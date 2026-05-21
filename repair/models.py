from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from diagnostics.models import FailureClass


class RepairAction(str, Enum):
    EDIT_SNIPPET = "edit_snippet"
    ADJUST_CONFIG = "adjust_config"
    REQUEST_PERMISSION = "request_permission"
    ABORT = "abort"


class RepairDirective(BaseModel):
    action: RepairAction
    target_file: str
    reason: str
    instructions: str
    failure_class: FailureClass


class RepairPlan(BaseModel):
    attempt: int = Field(ge=1)
    directives: list[RepairDirective]
    requires_recompile: bool
