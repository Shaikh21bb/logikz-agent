from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .state import AgentState
from .prompts import PLANNER_PROMPT, DECISION_PROMPT, FINAL_ANSWER_PROMPT, EXECUTION_TRACES


class AgentGraph:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(api_key=api_key, model=model, temperature=0)
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

    def _planner_node(self, state: AgentState) -> AgentState:
        try:
            response = self.llm.invoke([
                SystemMessage(content=PLANNER_PROMPT),
                HumanMessage(content=state["user_query"])
            ])
            plan = self._parse_plan(response.content)
            return {**state, "plan": plan, "status": "planning"}
        except Exception:
            return {**state, "plan": [], "status": "error", "final_answer": "AI service unavailable"}

    def _decision_node(self, state: AgentState) -> AgentState:
        if state.get("status") == "error":
            return {**state, "status": "final"}

        completed = len(state.get("observations", []))
        plan = state.get("plan", [])

        if completed >= len(plan):
            return {**state, "status": "final"}

        try:
            response = self.llm.invoke([
                SystemMessage(content=DECISION_PROMPT.format(
                    plan=plan,
                    completed_steps=completed,
                    observations=state.get("observations", [])
                )),
                HumanMessage(content="Decide next action")
            ])
            decision = self._parse_decision(response.content)
            return {**state, "tool_calls": state.get("tool_calls", []) + [decision]}
        except Exception:
            return {**state, "status": "error", "final_answer": "AI service unavailable"}

    def _tool_call_node(self, state: AgentState) -> AgentState:
        from tools.manifest import TOOL_MANIFEST

        tool_call = state["tool_calls"][-1]
        tool_name = tool_call.get("tool")
        args = tool_call.get("args", {})

        trace = EXECUTION_TRACES.get(tool_name, f"Выполняю {tool_name}...")
        state["messages"].append(AIMessage(content=trace))

        if tool_name not in TOOL_MANIFEST:
            observation = {"tool": tool_name, "error": "Tool not found", "result": None}
            return {**state, "observations": state.get("observations", []) + [observation]}

        try:
            tool_func = TOOL_MANIFEST[tool_name]
            result = tool_func(**args)
            observation = {"tool": tool_name, "args": args, "result": result, "error": None}
        except Exception as e:
            observation = {"tool": tool_name, "args": args, "result": None, "error": str(e)}

        return {**state, "observations": state.get("observations", []) + [observation]}

    def _observation_node(self, state: AgentState) -> AgentState:
        return state

    def _final_answer_node(self, state: AgentState) -> AgentState:
        try:
            response = self.llm.invoke([
                SystemMessage(content=FINAL_ANSWER_PROMPT.format(
                    user_query=state["user_query"],
                    observations=state.get("observations", [])
                )),
                HumanMessage(content="Generate final answer")
            ])
            final_answer = response.content
        except Exception:
            final_answer = self._format_fallback_answer(state)

        return {**state, "final_answer": final_answer, "status": "completed"}

    def _parse_plan(self, content: str) -> List[str]:
        import json
        try:
            return json.loads(content.strip())
        except Exception:
            lines = [line.strip("- ") for line in content.strip().split("\n") if line.strip()]
            return lines

    def _parse_decision(self, content: str) -> Dict[str, Any]:
        import json
        try:
            return json.loads(content.strip())
        except Exception:
            return {"tool": "final_answer", "args": {}, "reason": "parse error"}

    def _route_decision(self, state: AgentState) -> str:
        if state.get("status") == "error":
            return "final_answer"
        if state.get("status") == "final":
            return "final_answer"
        tool_calls = state.get("tool_calls", [])
        if not tool_calls:
            return "planner"
        last_call = tool_calls[-1]
        if last_call.get("tool") == "final_answer":
            return "final_answer"
        return "tool_call"

    def _format_fallback_answer(self, state: AgentState) -> str:
        obs = state.get("observations", [])
        tn_ved = "Не определен"
        customs_value = "Не рассчитана"
        duty = "Не рассчитана"
        vat = "Не рассчитана"
        total = "Не рассчитан"
        logistics = "Не рассчитана"

        for o in obs:
            if o.get("tool") == "search_tn_ved_database" and o.get("result"):
                tn_ved = str(o["result"].get("tn_ved", "Не определен"))
            if o.get("tool") == "calculate_customs_duties" and o.get("result"):
                r = o["result"]
                customs_value = f"${r.get('customs_value', 0):,.2f}"
                duty = f"${r.get('duty', 0):,.2f}"
                vat = f"${r.get('vat', 0):,.2f}"
                total = f"${r.get('total', 0):,.2f}"
            if o.get("tool") == "calculate_logistics_cost" and o.get("result"):
                logistics = f"${o['result'].get('cost', 0):,.2f}"

        return f"""📦 Товар: {state['user_query'][:50]}
🏷 ТН ВЭД: {tn_ved}
💰 Стоимость товара: $50,000
🚚 Логистика: {logistics}
🧾 Таможенная стоимость: {customs_value}
📊 Пошлина: {duty}
🇰🇿 НДС: {vat}
💵 Итого: {total}
Источник данных: Demo / Mock"""

    def run(self, user_query: str) -> Dict[str, Any]:
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_query)],
            "user_query": user_query,
            "plan": [],
            "tool_calls": [],
            "observations": [],
            "final_answer": "",
            "status": "start",
        }
        result = self.graph.invoke(initial_state)
        return {
            "final_answer": result.get("final_answer", ""),
            "trace": [msg.content for msg in result.get("messages", []) if hasattr(msg, 'content')],
            "observations": result.get("observations", []),
        }