from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ZERO_EXT = ".zero"


@dataclass(frozen=True)
class ZeroDirective:
    kind: str
    content: str
    token_count: int
    line: int


@dataclass(frozen=True)
class ZeroModule:
    path: str
    directives: list[ZeroDirective]
    raw_token_count: int
    optimized_token_count: int


_TOKEN_PATTERN = re.compile(r"\S+")


def _starts_with_any(text: str, prefixes: tuple[str, ...]) -> bool:
    return any(text.startswith(p) for p in prefixes)


def _count_tokens(text: str) -> int:
    return len(_TOKEN_PATTERN.findall(text))


def parse_zero_file(path: Path) -> ZeroModule:
    raw = path.read_text(encoding="utf-8")
    raw_tokens = _count_tokens(raw)

    directives: list[ZeroDirective] = []
    for i, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("#"):
            continue

        kind = "directive"
        content = stripped

        if _starts_with_any(stripped, ("task ", 'task "', "task '")):
            kind = "task"
        elif _starts_with_any(stripped, ("prompt ", 'prompt "', "prompt '")):
            kind = "prompt"
        elif _starts_with_any(stripped, ("agent ", 'agent "', "agent '")):
            kind = "agent"

        directives.append(
            ZeroDirective(
                kind=kind,
                content=content,
                token_count=_count_tokens(content),
                line=i,
            )
        )

    optimized = optimize_module(raw, directives)

    return ZeroModule(
        path=str(path),
        directives=directives,
        raw_token_count=raw_tokens,
        optimized_token_count=_count_tokens(optimized),
    )


def optimize_module(raw: str, directives: list[ZeroDirective]) -> str:
    lines = raw.splitlines()
    optimized: list[str] = []

    for line in lines:
        commentary_patterns = [
            r"^\s*//",
            r"^\s*#",
            r"(?i)basically\s",
            r"(?i)essentially\s",
            r"(?i)simply\s",
            r"(?i)in other words",
            r"(?i)you need to",
            r"(?i)please\s",
        ]
        is_commentary = False
        for pat in commentary_patterns:
            if re.search(pat, line):
                is_commentary = True
                break

        if is_commentary:
            continue

        optimized.append(line)

    return "\n".join(optimized)


def estimate_token_reduction(module: ZeroModule) -> dict[str, Any]:
    if module.raw_token_count == 0:
        return {"savings_pct": 0, "savings_tokens": 0}

    savings = module.raw_token_count - module.optimized_token_count
    pct = round((savings / module.raw_token_count) * 100, 1)

    return {
        "raw_tokens": module.raw_token_count,
        "optimized_tokens": module.optimized_token_count,
        "savings_tokens": savings,
        "savings_pct": pct,
    }


def compile_zero(path: Path) -> dict[str, Any]:
    module = parse_zero_file(path)
    reduction = estimate_token_reduction(module)

    return {
        "status": "ok",
        "path": module.path,
        "directives": len(module.directives),
        "raw_token_count": module.raw_token_count,
        "optimized_token_count": module.optimized_token_count,
        "savings_tokens": reduction["savings_tokens"],
        "savings_pct": reduction["savings_pct"],
        "can_optimize": reduction["savings_tokens"] > 0,
    }
