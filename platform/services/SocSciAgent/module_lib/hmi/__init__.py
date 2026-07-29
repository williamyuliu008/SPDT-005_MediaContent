"""
module_lib.hmi — PT-047 人机界面模块（CLI标准输出）
-stub: 所有CLI渲染器类，满足agents导入要求
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json, sys
from datetime import datetime

__all__ = [
    "CLIOutput", "CLIOutputRenderer", "CLIOutputFormatter",
    "CLIInterface", "CLIStructuredOutput", "StructuredOutput",
    "CLIInput", "CLIMenu", "MenuItem", "OutputFormatter",
]


# ── 基础输出 ─────────────────────────────────────────────
class CLIOutput:
    """CLI 文本输出渲染器。"""

    def __init__(self, stream=None):
        self.stream = stream or sys.stdout

    def print(self, msg: str, level: str = "info"):
        prefix = {"info": "[INFO]", "warn": "[WARN]", "error": "[ERROR]", "debug": "[DEBUG]"}.get(level, "[MSG]")
        self.stream.write(f"{prefix} {msg}\n")
        self.stream.flush()

    def log(self, msg: str):
        """Alias for print — used by agents."""
        self.print(msg, "info")

    def render(self, data: Any):
        if isinstance(data, dict):
            self.stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        else:
            self.stream.write(str(data) + "\n")
        self.stream.flush()


class CLIOutputRenderer(CLIOutput):
    """CLIOutputRenderer = CLIOutput（向后兼容别名）。"""
    pass


# ── 格式化输出 ───────────────────────────────────────────
class CLIOutputFormatter:
    """结构化输出格式化器。"""

    def __init__(self):
        self._indent = 2

    def format_structured(self, data: Dict[str, Any], title: str = "") -> str:
        lines = []
        if title:
            lines.append(f"=== {title} ===")
        lines.append(json.dumps(data, ensure_ascii=False, indent=self._indent))
        return "\n".join(lines)

    def format_table(self, rows: List[Dict[str, Any]], headers: List[str] = None) -> str:
        if not rows:
            return "(empty)"
        headers = headers or list(rows[0].keys())
        col_widths = {h: max(len(str(r.get(h, ""))) for r in rows + [dict(zip(headers, headers))]) for h in headers}
        sep = " | ".join("-" * col_widths[h] for h in headers)
        header_row = " | ".join(str(h).ljust(col_widths[h]) for h in headers)
        lines = [header_row, sep]
        for row in rows:
            lines.append(" | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers))
        return "\n".join(lines)

    def render(self, data: Any):
        print(self.format_structured(data) if isinstance(data, dict) else str(data))


# ── 高级结构化输出 ───────────────────────────────────────
class CLIStructuredOutput:
    """带时间戳和格式的结构化输出。"""

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []

    def add(self, key: str, value: Any):
        self._entries.append({"ts": datetime.now().isoformat(), "key": key, "value": value})

    def output(self) -> Dict[str, Any]:
        return {"entries": self._entries, "count": len(self._entries)}


class StructuredOutput(CLIStructuredOutput):
    """StructuredOutput = CLIStructuredOutput（别名）。"""
    pass


class OutputFormatter(CLIOutputFormatter):
    """OutputFormatter = CLIOutputFormatter（别名）。"""
    pass


# ── CLI 接口 ─────────────────────────────────────────────
class CLIInterface:
    """CLI 交互接口：输入/输出/菜单。"""

    def __init__(self):
        self.output = CLIOutput()
        self.formatter = CLIOutputFormatter()

    def read_line(self, prompt: str = "") -> str:
        return input(prompt).strip()

    def menu(self, items: List[str], title: str = "Menu") -> int:
        print(f"\n=== {title} ===")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
        choice = self.read_line("Choice: ")
        try:
            return int(choice) - 1
        except ValueError:
            return -1

    def confirm(self, question: str) -> bool:
        resp = self.read_line(f"{question} (y/n): ").lower().strip()
        return resp in ("y", "yes")


# ── 菜单与输入 ───────────────────────────────────────────
@dataclass
class MenuItem:
    label: str
    action: str = ""
    shortcut: str = ""


class CLIMenu:
    """CLI 菜单渲染器。"""

    def __init__(self, title: str = ""):
        self.title = title
        self.items: List[MenuItem] = []

    def add(self, label: str, action: str = "", shortcut: str = "") -> "CLIMenu":
        self.items.append(MenuItem(label=label, action=action, shortcut=shortcut))
        return self

    def show(self) -> int:
        if self.title:
            print(f"\n### {self.title} ###")
        for i, item in enumerate(self.items, 1):
            shortcut = f" ({item.shortcut})" if item.shortcut else ""
            print(f"  {i}. {item.label}{shortcut}")
        return -1


class CLIInput:
    """CLI 输入读取器（stub）。"""

    def read(self, prompt: str = "") -> str:
        return input(prompt).strip()

    def read_int(self, prompt: str = "") -> Optional[int]:
        try:
            return int(self.read(prompt))
        except (ValueError, EOFError):
            return None
