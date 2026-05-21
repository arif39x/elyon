from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AgentRole(StrEnum):
    PLANNER = "planner"
    REPAIRER = "repairer"
    VERIFIER = "verifier"
    OPTIMIZER = "optimizer"
    SECURITY_AUDITOR = "security_auditor"
    TEST_GENERATOR = "test_generator"


class AgentSettings(BaseModel):
    name: str
    role: AgentRole
    provider: str
    model: str | None = None
    description: str = ""
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)


class AgentTask(BaseModel):
    role: AgentRole
    objective: str
    trace_id: str
