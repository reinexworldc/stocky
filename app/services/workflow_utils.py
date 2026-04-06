from __future__ import annotations


def make_tool_call(step: int, tool: str, status: str, result: dict) -> dict:
    return {
        "step": step,
        "tool": tool,
        "status": status,
        "result": result,
    }
