from __future__ import annotations

import json
from typing import Any

from compiler.models import CompilerDiagnostic, DiagnosticSeverity, SourceSpan


def parse_structured_diagnostics(raw: str) -> list[CompilerDiagnostic]:
    diagnostics: list[CompilerDiagnostic] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            diagnostics.append(_malformed_diagnostic(stripped))
            continue

        diagnostics.append(_from_payload(payload))

    return diagnostics


def _from_payload(payload: dict[str, Any]) -> CompilerDiagnostic:
    severity = _normalize_severity(payload.get("severity"))
    span_payload = payload.get("span") if isinstance(payload.get("span"), dict) else {}

    return CompilerDiagnostic(
        code=str(payload.get("code", "UNKNOWN")),
        message=str(payload.get("message", "Missing compiler message")),
        severity=severity,
        span=SourceSpan(
            path=str(span_payload.get("path", "unknown")),
            line=int(span_payload.get("line", 1)),
            column=int(span_payload.get("column", 1)),
        ),
    )


def _normalize_severity(value: Any) -> DiagnosticSeverity:
    if isinstance(value, str):
        candidate = value.lower()
        if candidate in {"error", "warning", "note"}:
            return DiagnosticSeverity(candidate)
    return DiagnosticSeverity.ERROR


def _malformed_diagnostic(raw_line: str) -> CompilerDiagnostic:
    return CompilerDiagnostic(
        code="MALFORMED_DIAGNOSTIC",
        message=f"Unable to parse diagnostic payload: {raw_line}",
        severity=DiagnosticSeverity.ERROR,
        span=SourceSpan(path="unknown", line=1, column=1),
    )
