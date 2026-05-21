from __future__ import annotations

from pathlib import Path

from orchestration.config import SandboxSettings


class SandboxPolicy:
    def __init__(self, settings: SandboxSettings) -> None:
        self._settings = settings

    def command_allowed(self, command: list[str]) -> bool:
        if not command:
            return False
        executable = command[0]
        return any(executable.startswith(prefix) for prefix in self._settings.allowed_command_prefixes)

    def read_allowed(self, path: Path) -> bool:
        resolved = path.resolve()
        return _is_in_roots(resolved, self._settings.allowed_read_roots)

    def write_allowed(self, path: Path) -> bool:
        resolved = path.resolve()
        return _is_in_roots(resolved, self._settings.allowed_write_roots)


def _is_in_roots(path: Path, roots: list[str]) -> bool:
    for root in roots:
        candidate = Path(root).resolve()
        if path == candidate or candidate in path.parents:
            return True
    return False
