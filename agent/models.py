from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ToolName(str, Enum):
    SEARCH_TN_VED = "search_tn_ved_database"
    CALCULATE_CUSTOMS = "calculate_customs_duties"
    CALCULATE_LOGISTICS = "calculate_logistics_cost"
    FINAL_ANSWER = "final_answer"


class AgentStatus(str, Enum):
    START = "start"
    PLANNING = "planning"
    DECIDING = "deciding"
    EXECUTING = "executing"
    OBSERVING = "observing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    ERROR = "error"


class PlanStep(BaseModel):
    step: int
    description: str
    tool: Optional[ToolName] = None
    args: Dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    steps: List[PlanStep]
    reasoning: str = ""

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def pending_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if s.tool != ToolName.FINAL_ANSWER]


class Decision(BaseModel):
    tool: ToolName
    args: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    step_index: int = 0

    @field_validator("tool", mode="before")
    @classmethod
    def validate_tool(cls, v):
        if isinstance(v, str):
            try:
                return ToolName(v)
            except ValueError:
                return ToolName.FINAL_ANSWER
        return v


class ToolCall(BaseModel):
    tool: ToolName
    args: Dict[str, Any]
    reason: str
    timestamp: str = ""
    retry_count: int = 0


class Observation(BaseModel):
    tool: ToolName
    args: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    success: bool = True
    timestamp: str = ""

    @property
    def is_error(self) -> bool:
        return self.error is not None or not self.success


class TraceEntry(BaseModel):
    type: Literal["trace", "tool_call", "observation", "final_answer"]
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    messages: List[Any] = Field(default_factory=list)
    user_query: str = ""
    plan: Optional[Plan] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    observations: List[Observation] = Field(default_factory=list)
    final_answer: str = ""
    status: AgentStatus = AgentStatus.START
    current_step: int = 0
    error: Optional[str] = None
    trace: List[TraceEntry] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class AgentConfig(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    max_steps: int = 10