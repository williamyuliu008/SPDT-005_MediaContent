# _agent_os 桥接模块
# ============================================================================
# 功能：为新项目注入 _agent_os 基础设施依赖
#       确保每个项目能使用 Agent OS 的运行时/通信/部署能力
#
# 使用方式：Assembler 生成项目时自动引用本文件
# ============================================================================

from pathlib import Path
import sys

# ── _agent_os 路径解析 ────────────────────────────────────────────────────
AGENT_OS_ROOT = Path(r"D:\6_agent_project\_agent_os")

# ── 注入路径确保 import ───────────────────────────────────────────────────
_AGENT_OS_PATHS = [
    str(AGENT_OS_ROOT / "01_agent_os_v1" / "src"),       # V1 核心
    str(AGENT_OS_ROOT / "02_agent_os_agno" / "src"),     # V2 核心
    str(AGENT_OS_ROOT / "03_a2a_comm"),                  # A2A 通信桥
    str(AGENT_OS_ROOT / "agent_os_sw_elite"),            # 生产级版本
]

for _p in _AGENT_OS_PATHS:
    if Path(_p).exists() and _p not in sys.path:
        sys.path.insert(0, _p)

# ── 可复用的基础设施模块 ──────────────────────────────────────────────────
# 这些是 _agent_os 中可被新项目直接复用的模块

REUSABLE_MODULES = {
    # V1 基础设施
    "approval_engine":    "01_agent_os_v1/src/approval_engine",
    "governance":         "01_agent_os_v1/src/governance",
    "guards":             "01_agent_os_v1/src/guards",
    "health_monitor":     "01_agent_os_v1/src/health_monitor",
    "runner":             "01_agent_os_v1/src/runner",
    "scheduler":          "01_agent_os_v1/src/scheduler_subsystem",
    "session_manager":    "01_agent_os_v1/src/session_manager",
    "observability":      "01_agent_os_v1/src/observability",

    # V2 基础设施
    "agno_core":          "02_agent_os_agno/src",

    # 通信桥
    "a2a_comm":           "03_a2a_comm",

    # 项目模板
    "templates":          "01_agent_os_v1/templates",
}

# ── 项目脚手架注入指导 ────────────────────────────────────────────────────
# 新项目应包含以下 _agent_os 能力：

REQUIRED_INFRA = [
    "runner",           # Agent 运行时（必需）
    "session_manager",  # 会话管理（必需）
    "health_monitor",   # 健康检查（推荐）
    "observability",    # 可观测性（推荐）
    "a2a_comm",         # 跨 Agent 通信（如有多个 Agent → 必需）
]


def get_infrastructure_deps(agent_count: int) -> list:
    """根据 Agent 数量，返回推荐的 _agent_os 依赖清单。"""
    deps = ["runner", "session_manager"]
    if agent_count > 1:
        deps.append("a2a_comm")
    deps.append("health_monitor")
    deps.append("observability")
    return deps
