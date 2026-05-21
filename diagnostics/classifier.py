from __future__ import annotations

from compiler.models import CompilerDiagnostic
from diagnostics.models import ClassifiedDiagnostic, FailureClass


def classify_diagnostic(diagnostic: CompilerDiagnostic) -> ClassifiedDiagnostic:
    code = diagnostic.code.lower()
    message = diagnostic.message.lower()

    if "syntax" in code or "parse" in message:
        failure_class = FailureClass.SYNTAX
    elif "type" in code or "mismatch" in message:
        failure_class = FailureClass.TYPE
    elif "capability" in message or "permission" in message:
        failure_class = FailureClass.CAPABILITY
    elif "sandbox" in message:
        failure_class = FailureClass.SANDBOX
    elif "timeout" in message:
        failure_class = FailureClass.TIMEOUT
    else:
        failure_class = FailureClass.UNKNOWN

    return ClassifiedDiagnostic(
        code=diagnostic.code,
        message=diagnostic.message,
        failure_class=failure_class,
    )
