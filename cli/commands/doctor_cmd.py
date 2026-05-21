from __future__ import annotations

from pathlib import Path

from bindings import ensure_runtime_command_is_executable
from cli.context import CliContext


def execute(context: CliContext) -> dict[str, object]:
    warnings: list[str] = []

    runtime_command = context.settings.runtime.command
    if not runtime_command:
        warnings.append("runtime.command is empty")

    event_path = Path(context.settings.state.event_log_path)
    if not event_path.parent.exists():
        warnings.append(f"event log parent directory does not exist: {event_path.parent}")

    provider_names = context.providers.list_names()
    if not provider_names:
        warnings.append("no providers are registered")

    if not ensure_runtime_command_is_executable(runtime_command, Path.cwd()):
        warnings.append(
            "runtime executable was not found from runtime.command; build runtime crate before compile/repair execution"
        )

    return {
        "status": "ok" if not warnings else "warn",
        "provider_count": len(provider_names),
        "providers": provider_names,
        "runtime_command": runtime_command,
        "warnings": warnings,
    }
