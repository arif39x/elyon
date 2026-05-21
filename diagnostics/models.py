from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class FailureClass(str, Enum):
    SYNTAX = "syntax"
    TYPE = "type"
    CAPABILITY = "capability"
    SANDBOX = "sandbox"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ClassifiedDiagnostic(BaseModel):
    code: str
    message: str
    failure_class: FailureClass
