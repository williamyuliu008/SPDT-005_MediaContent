"""
DLV Common Bridge — 为新项目自动注入 _common/ 和 _agent_os 依赖

用法:
    import sys
    sys.path.insert(0, r"D:\6_agent_project")
    from _templates._common.dlv_common_bridge import setup_project

    setup_project(agent_count=3)
    # 之后可以直接 from _common.base_engine import BaseEngine
"""

from pathlib import Path
import sys

# ── 路径解析 ────────────────────────────────────────────────────
DLV_ROOT = Path(r"D:\6_agent_project")
AGENT_OS_ROOT = DLV_ROOT / "_agent_os"
COMMON_ROOT = DLV_ROOT / "_common"

# ── _common/ 注入 ────────────────────────────────────────────────
if str(COMMON_ROOT) not in sys.path and COMMON_ROOT.exists():
    sys.path.insert(0, str(DLV_ROOT))

# ── _agent_os 注入 ───────────────────────────────────────────────
AGENT_OS_PATHS = [
    str(AGENT_OS_ROOT / "01_agent_os_v1" / "src"),
    str(AGENT_OS_ROOT / "02_agent_os_agno" / "src"),
    str(AGENT_OS_ROOT / "03_a2a_comm"),
]

for p in AGENT_OS_PATHS:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

# ── 可复用模块清单 ──────────────────────────────────────────────

DLV_COMMON_MODULES = {
    "base_engine":    "_common/base_engine.py",
    "base_api":       "_common/base_api.py",
    "config_loader":  "_common/config_loader.py",
}

AGENT_OS_MODULES = {
    "runner":          "01_agent_os_v1/src/runner",
    "session_manager": "01_agent_os_v1/src/session_manager",
    "health_monitor":  "01_agent_os_v1/src/health_monitor",
    "observability":   "01_agent_os_v1/src/observability",
    "a2a_comm":        "03_a2a_comm",
}

def setup_project(agent_count: int = 1):
    """为新项目设置所有依赖路径"""
    # DLV Common
    if str(COMMON_ROOT) not in sys.path and COMMON_ROOT.exists():
        sys.path.insert(0, str(DLV_ROOT))
    
    # Agent OS
    for p in AGENT_OS_PATHS:
        if Path(p).exists() and p not in sys.path:
            sys.path.insert(0, p)
    
    deps = get_recommended_deps(agent_count)
    return deps


def get_recommended_deps(agent_count: int) -> dict:
    """根据 Agent 数量返回推荐依赖"""
    deps = {
        "dlv_common": ["base_engine", "config_loader"],
        "agent_os": ["runner", "session_manager"],
    }
    if agent_count > 1:
        deps["agent_os"].append("a2a_comm")
    deps["agent_os"].extend(["health_monitor", "observability"])
    return deps
