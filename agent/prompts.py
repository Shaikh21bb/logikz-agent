from typing import List
from .models import Plan, PlanStep, Decision, ToolName


PLANNER_PROMPT = """You are a logistics and customs calculation expert.
Given a user query about importing goods, create a step-by-step plan to answer it.

Available tools:
- search_tn_ved_database: Find HS codes (ТН ВЭД) for products
- calculate_customs_duties: Calculate customs duties and taxes
- calculate_logistics_cost: Calculate shipping/logistics costs

Analyze the user query and create a structured plan.
Return ONLY a JSON object matching this schema:
{{
  "steps": [
    {{"step": 1, "description": "Find HS code for servers", "tool": "search_tn_ved_database", "args": {{"query": "серверы"}}}},
    {{"step": 2, "description": "Calculate customs duties for $50,000", "tool": "calculate_customs_duties", "args": {{"customs_value": 50000, "tn_ved": "8471"}}}},
    {{"step": 3, "description": "Calculate logistics for 10 tons from China to Kazakhstan", "tool": "calculate_logistics_cost", "args": {{"weight_kg": 10000, "transport_type": "rail"}}}},
    {{"step": 4, "description": "Compile final answer", "tool": "final_answer", "args": {{}}}}
  ],
  "reasoning": "Brief reasoning for the plan"
}}"""


DECISION_PROMPT = """You are an agent that decides which tool to call next based on the current plan and observations.

Current plan: {plan}
Completed steps: {completed_steps}
Observations: {observations}

Decide the next tool to call. Return ONLY a JSON object matching this schema:
{{
  "tool": "search_tn_ved_database" | "calculate_customs_duties" | "calculate_logistics_cost" | "final_answer",
  "args": {{}},
  "reason": "brief reason for this choice",
  "step_index": 0
}}

If all plan steps are complete, return tool: "final_answer" with args containing the compiled answer."""


FINAL_ANSWER_PROMPT = """Compile a final answer for the user based on all observations.

User query: {user_query}
Observations: {observations}

Format the answer EXACTLY as:
📦 Товар: [product name]
🏷 ТН ВЭД: [HS code]
💰 Стоимость товара: [value]
🚚 Логистика: [logistics cost]
🧾 Таможенная стоимость: [customs value]
📊 Пошлина: [duty amount]
🇰🇿 НДС: [VAT amount]
💵 Итого: [total]
Источник данных: [Demo / Mock]"""


EXECUTION_TRACES = {
    ToolName.SEARCH_TN_VED: "🔎 Определяю категорию товара...\n📦 Проверяю ТН ВЭД...",
    ToolName.CALCULATE_CUSTOMS: "💰 Рассчитываю таможенные платежи...",
    ToolName.CALCULATE_LOGISTICS: "🚚 Рассчитываю логистику...",
    ToolName.FINAL_ANSWER: "✅ Формирую результат...",
}


def format_plan_for_prompt(plan: Plan) -> str:
    return "\n".join([f"{s.step}. {s.description} (tool: {s.tool.value if s.tool else 'none'})" for s in plan.steps])


def format_observations_for_prompt(observations: List) -> str:
    if not observations:
        return "No observations yet."
    lines = []
    for i, obs in enumerate(observations):
        status = "✅" if obs.success else "❌"
        lines.append(f"{i+1}. {status} {obs.tool.value}: {obs.result if obs.success else obs.error}")
    return "\n".join(lines)