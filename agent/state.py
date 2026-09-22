from typing import TypedDict, List, Any


class AgentState(TypedDict):
    messages: List[Any]
    user_query: str
    plan: List[str]
    tool_calls: List[dict]
    observations: List[dict]
    final_answer: str
    status: str