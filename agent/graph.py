import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .models import (
    AgentState, AgentStatus, Plan, Decision, ToolCall, Observation, 
    TraceEntry, ToolName, AgentConfig
)
from .prompts import (
    PLANNER_PROMPT, DECISION_PROMPT, FINAL_ANSWER_PROMPT, 
    EXECUTION_TRACES, format_plan_for_prompt, format_observations_for_prompt
)


class AgentGraph:
    def __init__(self, config: Optional[AgentConfig] = None, api_key: str = None):
        self.config = config or AgentConfig()
        self.llm = ChatOpenAI(
            api_key=api_key, 
            model=self.config.model, 
            temperature=self.config.temperature,
            timeout=self.config.timeout
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("planner", self._planner_node)
        workflow.add_node("decision", self._decision_node)
        workflow.add_node("tool_call", self._tool_call_node)
        workflow.add_node("observation", self._observation_node)
        workflow.add_node("final_answer", self._final_answer_node)

        workflow.set_entry_point("planner")

        workflow.add_edge("planner", "decision")
        workflow.add_conditional_edges(
            "decision",
            self._route_decision,
            {
                "tool_call": "tool_call",
                "final_answer": "final_answer",
                "planner": "planner",
            },
        )
        workflow.add_edge("tool_call", "observation")
        workflow.add_edge("observation", "decision")
        workflow.add_edge("final_answer", END)

        return workflow.compile()

    def _planner_node(self, state: AgentState) -> Dict[str, Any]:
        timestamp = datetime.now().isoformat()
        trace = TraceEntry(type="trace", content="🧠 Планирую выполнение запроса...", metadata={"node": "planner"})
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=PLANNER_PROMPT),
                HumanMessage(content=state.user_query)
            ])
            plan_data = self._parse_plan(response.content)
            plan = Plan(**plan_data)
            
            return {
                "plan": plan,
                "status": AgentStatus.PLANNING,
                "current_step": 0,
                "trace": state.trace + [trace],
            }
            
        except Exception as e:
            error_trace = TraceEntry(
                type="trace", 
                content="❌ Ошибка планирования", 
                metadata={"node": "planner", "error": str(e)}
            )
            return {
                "status": AgentStatus.ERROR,
                "error": f"Planning failed: {str(e)}",
                "final_answer": "AI service unavailable",
                "trace": state.trace + [trace, error_trace],
            }

    def _decision_node(self, state: AgentState) -> Dict[str, Any]:
        if state.status == AgentStatus.ERROR:
            return {"status": AgentStatus.FINALIZING}

        completed = len(state.observations)
        plan = state.plan
        
        if not plan or completed >= plan.total_steps:
            return {"status": AgentStatus.FINALIZING}

        timestamp = datetime.now().isoformat()
        trace = TraceEntry(
            type="trace", 
            content=f"🤔 Принимаю решение (шаг {completed + 1}/{plan.total_steps})", 
            metadata={"node": "decision", "step": completed}
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content=DECISION_PROMPT.format(
                    plan=format_plan_for_prompt(plan),
                    completed_steps=completed,
                    observations=format_observations_for_prompt(state.observations)
                )),
                HumanMessage(content="Decide next action")
            ])
            decision_data = self._parse_decision(response.content)
            decision = Decision(**decision_data)
            
            tool_call = ToolCall(
                tool=decision.tool,
                args=decision.args,
                reason=decision.reason,
                timestamp=timestamp
            )
            
            return {
                "tool_calls": state.tool_calls + [tool_call],
                "status": AgentStatus.DECIDING,
                "current_step": completed,
                "trace": state.trace + [trace],
            }
            
        except Exception as e:
            error_trace = TraceEntry(
                type="trace", 
                content="❌ Ошибка принятия решения", 
                metadata={"node": "decision", "error": str(e)}
            )
            return {
                "status": AgentStatus.ERROR,
                "error": f"Decision failed: {str(e)}",
                "final_answer": "AI service unavailable",
                "trace": state.trace + [trace, error_trace],
            }

    def _tool_call_node(self, state: AgentState) -> Dict[str, Any]:
        if not state.tool_calls:
            return {}

        tool_call = state.tool_calls[-1]
        tool_name = tool_call.tool
        args = tool_call.args

        trace_content = EXECUTION_TRACES.get(tool_name, f"Выполняю {tool_name.value}...")
        trace = TraceEntry(type="tool_call", content=trace_content, metadata={"tool": tool_name.value, "args": args})

        from tools.manifest import TOOL_MANIFEST

        if tool_name not in TOOL_MANIFEST:
            observation = Observation(
                tool=tool_name,
                args=args,
                result=None,
                error="Tool not found",
                success=False,
                timestamp=datetime.now().isoformat()
            )
            return {
                "observations": state.observations + [observation],
                "status": AgentStatus.OBSERVING,
                "trace": state.trace + [trace],
            }

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                tool_func = TOOL_MANIFEST[tool_name]
                result = tool_func(**args)
                
                observation = Observation(
                    tool=tool_name,
                    args=args,
                    result=result,
                    error=None,
                    success=True,
                    timestamp=datetime.now().isoformat()
                )
                
                return {
                    "observations": state.observations + [observation],
                    "status": AgentStatus.OBSERVING,
                    "trace": state.trace + [trace],
                }
                
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue

        observation = Observation(
            tool=tool_name,
            args=args,
            result=None,
            error=f"Tool execution failed after {self.config.max_retries} retries: {str(last_error)}",
            success=False,
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "observations": state.observations + [observation],
            "status": AgentStatus.OBSERVING,
            "trace": state.trace + [trace],
        }

    def _observation_node(self, state: AgentState) -> Dict[str, Any]:
        return {"status": AgentStatus.DECIDING}

    def _final_answer_node(self, state: AgentState) -> Dict[str, Any]:
        trace = TraceEntry(type="trace", content="✅ Формирую результат...", metadata={"node": "final_answer"})

        try:
            response = self.llm.invoke([
                SystemMessage(content=FINAL_ANSWER_PROMPT.format(
                    user_query=state.user_query,
                    observations=format_observations_for_prompt(state.observations)
                )),
                HumanMessage(content="Generate final answer")
            ])
            final_answer = response.content
        except Exception:
            final_answer = self._format_fallback_answer(state)

        trace_final = TraceEntry(type="final_answer", content=final_answer, metadata={"node": "final_answer"})
        
        return {
            "final_answer": final_answer,
            "status": AgentStatus.COMPLETED,
            "trace": state.trace + [trace, trace_final],
        }

    def _parse_plan(self, content: str) -> Dict[str, Any]:
        import json
        try:
            return json.loads(content.strip())
        except Exception:
            lines = [line.strip("- ") for line in content.strip().split("\n") if line.strip()]
            steps = []
            for i, line in enumerate(lines):
                if "final" in line.lower() or "compile" in line.lower() or "answer" in line.lower():
                    steps.append({"step": i+1, "description": line, "tool": "final_answer", "args": {}})
                elif "tn" in line.lower() or "hs" in line.lower() or "code" in line.lower():
                    steps.append({"step": i+1, "description": line, "tool": "search_tn_ved_database", "args": {"query": "товар"}})
                elif "customs" in line.lower() or "duty" in line.lower() or "пошлина" in line.lower():
                    steps.append({"step": i+1, "description": line, "tool": "calculate_customs_duties", "args": {"customs_value": 50000}})
                elif "logistics" in line.lower() or "shipping" in line.lower() or "логистик" in line.lower():
                    steps.append({"step": i+1, "description": line, "tool": "calculate_logistics_cost", "args": {"weight_kg": 10000}})
                else:
                    steps.append({"step": i+1, "description": line, "tool": "final_answer", "args": {}})
            return {"steps": steps, "reasoning": "Parsed from text"}

    def _parse_decision(self, content: str) -> Dict[str, Any]:
        import json
        try:
            return json.loads(content.strip())
        except Exception:
            return {"tool": "final_answer", "args": {}, "reason": "parse error", "step_index": 0}

    def _route_decision(self, state: AgentState) -> str:
        if state.status == AgentStatus.ERROR:
            return "final_answer"
        if state.status == AgentStatus.FINALIZING:
            return "final_answer"
        tool_calls = state.tool_calls
        if not tool_calls:
            return "planner"
        last_call = tool_calls[-1]
        if last_call.tool == ToolName.FINAL_ANSWER:
            return "final_answer"
        return "tool_call"

    def _format_fallback_answer(self, state: AgentState) -> str:
        tn_ved = "Не определен"
        customs_value = "Не рассчитана"
        duty = "Не рассчитана"
        vat = "Не рассчитана"
        total = "Не рассчитан"
        logistics = "Не рассчитана"

        for o in state.observations:
            if o.tool == ToolName.SEARCH_TN_VED and o.result:
                tn_ved = str(o.result.get("tn_ved", "Не определен"))
            if o.tool == ToolName.CALCULATE_CUSTOMS and o.result:
                r = o.result
                customs_value = f"${r.get('customs_value', 0):,.2f}"
                duty = f"${r.get('duty', 0):,.2f}"
                vat = f"${r.get('vat', 0):,.2f}"
                total = f"${r.get('total', 0):,.2f}"
            if o.tool == ToolName.CALCULATE_LOGISTICS and o.result:
                logistics = f"${o.result.get('cost', 0):,.2f}"

        return f"""📦 Товар: {state.user_query[:50]}
🏷 ТН ВЭД: {tn_ved}
💰 Стоимость товара: $50,000
🚚 Логистика: {logistics}
🧾 Таможенная стоимость: {customs_value}
📊 Пошлина: {duty}
🇰🇿 НДС: {vat}
💵 Итого: {total}
Источник данных: Demo / Mock"""

    def run(self, user_query: str) -> Dict[str, Any]:
        initial_state = AgentState(
            messages=[HumanMessage(content=user_query)],
            user_query=user_query,
            status=AgentStatus.START,
        )
        result = self.graph.invoke(initial_state)
        
        trace_contents = []
        for t in result.get("trace", []):
            if isinstance(t, TraceEntry):
                trace_contents.append(t.content)
            elif hasattr(t, 'content'):
                trace_contents.append(t.content)
        
        return {
            "final_answer": result.get("final_answer", ""),
            "trace": trace_contents,
            "observations": [
                {"tool": o.tool.value, "args": o.args, "result": o.result, "error": o.error, "success": o.success}
                for o in result.get("observations", [])
            ],
            "plan": [
                {"step": s.step, "description": s.description, "tool": s.tool.value if s.tool else None}
                for s in result.get("plan", Plan(steps=[])).steps
            ] if result.get("plan") else [],
        }