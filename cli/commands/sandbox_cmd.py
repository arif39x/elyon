from __future__ import annotations

from cli.context import CliContext
from sandbox import SandboxPolicy


def execute(context: CliContext, *, command: list[str] | None = None) -> dict[str, object]:
    policy = SandboxPolicy(context.settings.sandbox)
    allowed = None
    if command is not None:
        allowed = policy.command_allowed(command)

    return {
        "status": "ok",
        "allowed_command_prefixes": context.settings.sandbox.allowed_command_prefixes,
        "allowed_read_roots": context.settings.sandbox.allowed_read_roots,
        "allowed_write_roots": context.settings.sandbox.allowed_write_roots,
        "command": command,
        "command_allowed": allowed,
    }
