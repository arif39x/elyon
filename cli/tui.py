from __future__ import annotations

import curses
import os
import subprocess
import threading
from pathlib import Path

from orchestration.agent_detector import KNOWN_SIGNATURES, detect_agents

BANNER_PATH = Path(__file__).parent.parent / "assets" / "ascii.txt"


def _read_logo() -> list[str]:
    if BANNER_PATH.exists():
        return BANNER_PATH.read_text(encoding="utf-8").splitlines()
    return ["MONAD v0.1.0"]


def _run_agent(agent_binary: str, prompt: str, signature: tuple[str, ...]) -> str:
    cmd = [agent_binary]
    for part in signature:
        if "{prompt}" in part:
            cmd.append(prompt)
        elif "{model}" in part:
            cmd.append("default")
        else:
            cmd.append(part)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.getcwd(),
        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\n[stderr] {result.stderr.strip()}"
        if result.returncode != 0:
            output = f"Exit code {result.returncode}\n{output}"
        return output if output else "(no output)"
    except FileNotFoundError:
        return f"Error: agent binary '{agent_binary}' not found on PATH"
    except subprocess.TimeoutExpired:
        return "Error: task timed out after 300 seconds"
    except Exception as e:
        return f"Error: {e}"


def _detect_agents_with_status() -> list[dict]:
    agents = detect_agents()
    result = []
    for a in agents:
        sig = KNOWN_SIGNATURES.get(a.binary, ("{prompt}",))
        result.append({
            "name": a.name,
            "binary": a.binary,
            "path": a.path,
            "description": a.description,
            "signature": sig,
            "available": True,
        })
    if not result:
        result.append({
            "name": "(no agents detected)",
            "binary": "",
            "path": "",
            "description": "Install an AI CLI agent like opencode, aider, or claude",
            "signature": ("{prompt}",),
            "available": False,
        })
    return result


def run_tui() -> None:
    curses.wrapper(_main_loop)


def _main_loop(stdscr: curses.window) -> None:
    curses.curs_set(1)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)

    logo_lines = _read_logo()
    agents = _detect_agents_with_status()
    selected_idx = 0
    idea_lines: list[str] = [""]
    idea_row = 0
    idea_col = 0
    status_msg = "Ready — F2: Run  |  F10: Exit"
    running = False
    result_text = ""
    show_result = False
    focus: str = "idea"

    while True:
        rows, cols = stdscr.getmaxyx()
        stdscr.clear()

        # --- Logo ---
        logo_h = min(len(logo_lines), 4)
        for i in range(logo_h):
            line = logo_lines[i].rstrip()
            if line:
                try:
                    stdscr.addstr(i, 2, line[:cols - 4], curses.color_pair(1))
                except curses.error:
                    pass

        y = logo_h + 1

        # --- Layout ---
        avail_h = rows - y - 2
        panel_w = (cols - 5) // 2
        left_x = 2
        right_x = left_x + panel_w + 3

        if avail_h < 6:
            try:
                stdscr.addstr(y, 2, "Terminal too small — resize to at least 80x24")
            except curses.error:
                pass
            stdscr.refresh()
            stdscr.getch()
            break

        # --- Left panel: Idea ---
        title_left = " IDEA (describe your task) "
        _draw_panel(stdscr, y, left_x, avail_h, panel_w, title_left,
                     curses.color_pair(2) if focus == "idea" else curses.color_pair(5))

        content_h = avail_h - 2
        visible_lines = idea_lines[-(content_h - 1):] if content_h > 1 else idea_lines[-1:]
        for i, line in enumerate(visible_lines):
            if i >= content_h - 1:
                break
            display = line[:panel_w - 4]
            try:
                stdscr.addstr(y + 1 + i, left_x + 2, display)
            except curses.error:
                pass

        if focus == "idea":
            cursor_screen_row = y + 1 + min(idea_row, content_h - 2)
            cursor_screen_col = left_x + 2 + min(idea_col, panel_w - 4)
            try:
                stdscr.move(cursor_screen_row, cursor_screen_col)
            except curses.error:
                pass

        # --- Right panel: Agent & Tasks ---
        title_right = " AGENT & TASKS "
        _draw_panel(stdscr, y, right_x, avail_h, panel_w, title_right,
                     curses.color_pair(2) if focus == "agent" else curses.color_pair(5))

        _draw_agent_panel(stdscr, y, right_x, avail_h, panel_w, agents,
                          selected_idx, running, show_result, result_text)

        # --- Status bar ---
        try:
            stdscr.addstr(rows - 1, 0, " " * (cols - 1), curses.color_pair(6))
            if running:
                status = " Running... "
            else:
                status = f" {status_msg} "
            stdscr.addstr(rows - 1, 2, status[:cols - 4],
                          curses.color_pair(6) | curses.A_BOLD)
        except curses.error:
            pass

        stdscr.refresh()

        # --- Input ---
        key = stdscr.getch()

        if key == curses.KEY_F10 or (key == ord('q') and not running):
            break

        if key == curses.KEY_F2 and not running and focus == "agent":
            if agents and agents[selected_idx]["available"] and idea_lines and any(l.strip() for l in idea_lines):
                running = True
                show_result = False
                result_text = ""
                status_msg = "Running..."

                def run_async():
                    nonlocal result_text, running, status_msg
                    agent = agents[selected_idx]
                    prompt = "\n".join(idea_lines).strip()
                    sig = agent["signature"]
                    try:
                        output = _run_agent(agent["binary"], prompt, tuple(sig))
                        result_text = output
                        status_msg = f"Done — agent: {agent['name']}"
                    except Exception as e:
                        result_text = f"Error: {e}"
                        status_msg = "Task failed"
                    running = False

                threading.Thread(target=run_async, daemon=True).start()
            continue

        if running:
            continue

        # --- Tab / F6 to switch focus ---
        if key == 9 or key == curses.KEY_F6:
            focus = "agent" if focus == "idea" else "idea"
            curses.curs_set(1 if focus == "idea" else 0)
            continue

        if focus == "agent":
            if key == curses.KEY_UP and selected_idx > 0:
                selected_idx -= 1
            elif key == curses.KEY_DOWN and selected_idx < len(agents) - 1:
                selected_idx += 1
            elif key == 10 and show_result:
                show_result = False
        elif focus == "idea":
            if key == curses.KEY_UP:
                if idea_row > 0:
                    idea_row -= 1
                    idea_col = min(idea_col, len(idea_lines[idea_row]))
            elif key == curses.KEY_DOWN:
                if idea_row < len(idea_lines) - 1:
                    idea_row += 1
                    idea_col = min(idea_col, len(idea_lines[idea_row]))
            elif key == curses.KEY_LEFT:
                if idea_col > 0:
                    idea_col -= 1
            elif key == curses.KEY_RIGHT:
                if idea_col < len(idea_lines[idea_row]):
                    idea_col += 1
            elif key == curses.KEY_HOME:
                idea_col = 0
            elif key == curses.KEY_END:
                idea_col = len(idea_lines[idea_row])
            elif key == 10:
                newline = idea_lines[idea_row][idea_col:]
                idea_lines[idea_row] = idea_lines[idea_row][:idea_col]
                idea_lines.insert(idea_row + 1, newline)
                idea_row += 1
                idea_col = 0
            elif key in (curses.KEY_BACKSPACE, 127):
                if idea_col > 0:
                    idea_lines[idea_row] = idea_lines[idea_row][:idea_col - 1] + idea_lines[idea_row][idea_col:]
                    idea_col -= 1
                elif idea_row > 0:
                    prev_len = len(idea_lines[idea_row - 1])
                    idea_lines[idea_row - 1] += idea_lines[idea_row]
                    del idea_lines[idea_row]
                    idea_row -= 1
                    idea_col = prev_len
            elif key == curses.KEY_DC:
                if idea_col < len(idea_lines[idea_row]):
                    idea_lines[idea_row] = idea_lines[idea_row][:idea_col] + idea_lines[idea_row][idea_col + 1:]
                elif idea_row < len(idea_lines) - 1:
                    idea_lines[idea_row] += idea_lines[idea_row + 1]
                    del idea_lines[idea_row + 1]
            elif 32 <= key <= 126:
                ch = chr(key)
                idea_lines[idea_row] = idea_lines[idea_row][:idea_col] + ch + idea_lines[idea_row][idea_col:]
                idea_col += 1

        # --- Ctrl+L to toggle result view ---
        if key == 12 and result_text:
            show_result = not show_result


def _draw_panel(stdscr: curses.window, top: int, left: int, height: int, width: int,
                title: str, border_color: int) -> None:
    try:
        stdscr.addstr(top, left, "┌" + "─" * (width - 2) + "┐", border_color)
        title_disp = f" {title} " if len(title) < width - 4 else title[:width - 4]
        stdscr.addstr(top, left + 2, title_disp, curses.color_pair(2) | curses.A_BOLD)
        for i in range(1, height - 1):
            stdscr.addstr(top + i, left, "│", border_color)
            stdscr.addstr(top + i, left + width - 1, "│", border_color)
        stdscr.addstr(top + height - 1, left, "└" + "─" * (width - 2) + "┘", border_color)
    except curses.error:
        pass


def _draw_agent_panel(stdscr: curses.window, top: int, left: int, height: int, width: int,
                      agents: list[dict], selected_idx: int, running: bool,
                      show_result: bool, result_text: str) -> None:
    x = left + 2
    y = top + 1

    if show_result and result_text:
        try:
            stdscr.addstr(y, x, "--- Task Result ---", curses.color_pair(2) | curses.A_BOLD)
            y += 1
            for line in result_text.split("\n")[:height - 4]:
                if y >= top + height - 1:
                    break
                try:
                    stdscr.addstr(y, x, line[:width - 4])
                except curses.error:
                    pass
                y += 1
            try:
                stdscr.addstr(y, x, "(Ctrl+L to go back)", curses.color_pair(3))
            except curses.error:
                pass
        except curses.error:
            pass
        return

    try:
        stdscr.addstr(y, x, "Available Agents:", curses.A_BOLD)
        y += 1
    except curses.error:
        return

    for i, agent in enumerate(agents):
        if y >= top + height - 4:
            break
        prefix = ">" if i == selected_idx else " "
        color = curses.color_pair(2) if i == selected_idx else curses.color_pair(5)
        display = f"{prefix} {agent['name']}"
        try:
            stdscr.addstr(y, x, display[:width - 6], color)
            if i == selected_idx and agent["available"]:
                desc = agent["description"][:width - 10]
                try:
                    stdscr.addstr(y + 1, x + 2, desc[:width - 10], curses.color_pair(3))
                except curses.error:
                    pass
                y += 1
        except curses.error:
            pass
        y += 1

    y += 1
    sep = "─" * (width - 6)
    try:
        stdscr.addstr(y, x, sep, curses.color_pair(5))
        y += 1
    except curses.error:
        return

    if running:
        try:
            stdscr.addstr(y, x, "Running task...", curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass
    elif agents and any(a["available"] for a in agents):
        try:
            stdscr.addstr(y, x, "F2: Run with selected agent", curses.color_pair(2) | curses.A_BOLD)
            y += 1
            stdscr.addstr(y, x, "Tab: Switch panel", curses.color_pair(3))
            y += 1
            stdscr.addstr(y, x, "Ctrl+L: View result", curses.color_pair(3))
        except curses.error:
            pass
    else:
        try:
            stdscr.addstr(y, x, "No agents detected on PATH", curses.color_pair(4))
        except curses.error:
            pass
