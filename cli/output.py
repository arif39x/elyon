from __future__ import annotations

import json
import shutil
from typing import Any


def _table(rows: list[dict[str, Any]], columns: list[dict[str, str]]) -> str:
    col_count = len(columns)
    headers = [c["label"] for c in columns]
    col_keys = [c["key"] for c in columns]

    hard_min_widths = {"status": 13, "name": 10, "role": 8}
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, key in enumerate(col_keys):
            val = str(row.get(key, ""))
            col_widths[i] = max(col_widths[i], len(val), hard_min_widths.get(key, 6))

    term_width = shutil.get_terminal_size().columns
    gap = 3
    available = term_width - (gap * (col_count - 1)) - 1
    total_width = sum(col_widths)
    if total_width > available:
        shrinkable = [i for i in range(col_count) if col_keys[i] not in ("status",)]
        if not shrinkable:
            shrinkable = list(range(col_count))
        shrink_total = sum(col_widths[i] for i in shrinkable)
        needed = total_width - available
        for i in shrinkable:
            ratio = col_widths[i] / shrink_total
            reduction = min(int(needed * ratio) + 1, col_widths[i] - 6)
            col_widths[i] -= reduction
        diff = available - sum(col_widths)
        if diff > 0:
            col_widths[shrinkable[-1]] += diff

    lines: list[str] = []
    fmt = " {:{}} " * col_count
    header_line = fmt.format(*[h for pair in zip(headers, col_widths) for h in pair])
    lines.append(header_line)
    lines.append(" " + "─" * (sum(col_widths) + (col_count - 1) * gap))
    for row in rows:
        vals = []
        for i, key in enumerate(col_keys):
            v = str(row.get(key, ""))
            vals.append(v[:col_widths[i]].ljust(col_widths[i]))
        lines.append(fmt.format(*[v for pair in zip(vals, col_widths) for v in pair]))
    return "\n".join(lines)


def render(payload: dict[str, Any], *, as_json: bool) -> str:
    if as_json:
        return json.dumps(payload, separators=(",", ":"))

    col_map: dict[str, str] = {
        "name": "Name",
        "task_id": "Task",
        "agent": "Agent",
        "status": "Status",
        "success": "Success",
        "path": "Path",
        "signature": "Signature",
        "role": "Role",
        "provider": "Provider",
        "model": "Model",
        "description": "Description",
        "output_preview": "Output",
        "token_estimate": "Tokens",
        "error": "Error",
    }

    lines: list[str] = []
    for key, value in payload.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            header = key.replace("_", " ").title()
            lines.append(f"\n{header}")
            keys_in_order = [k for k in col_map if k in value[0]]
            columns = [{"key": k, "label": col_map[k]} for k in keys_in_order]
            lines.append(_table(value, columns))
        elif key == "status":
            continue
        elif key not in ("agents", "config_agents", "system_agents", "tasks"):
            lines.append(f"{key}: {value}")
    return "\n".join(lines)
