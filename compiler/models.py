from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DiagnosticSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"


class SourceSpan(BaseModel):
    path: str
    line: int = Field(ge=1)
    column: int = Field(ge=1)


class CompilerDiagnostic(BaseModel):
    code: str
    message: str
    severity: DiagnosticSeverity
    span: SourceSpan


class CompileResult(BaseModel):
    success: bool
    diagnostics: list[CompilerDiagnostic]
    raw_stdout: str
    raw_stderr: str
