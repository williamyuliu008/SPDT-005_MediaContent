#!/usr/bin/env python3
"""
SR-CH-003: AI 开源雷达日报生成器
──────────────────────────────────
数据源: Radar Pipeline ecosystem 信号
        + ModLib 外部扫描日报 (D:\9_infra\module_lib\docs\daily_reports\)
        + CI Engine 事件中开源/平台/生态相关条目
赛道:   A 快反（新发现速览 + 开源趋势信号 + 许可证警示）
        D 技术文档（重点项目深读）

输出: channels/oss/YYYY-MM-DD.md

用法: python build.py [--date YYYY-MM-DD] [--radar]
依赖: prompts.py（A/D 赛道 prompt 配置）
"""

import json
import os
import sys
import argparse
import glob
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# ─── 路径配置 ──────────────────────────────────────

CI_ENGINE_EVENTS_DIR = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events"
MODLIB_DAILY_DIR = r"D:\9_infra\module_lib\docs\daily_reports"
OUTPUT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─── 开源/生态关键词 ─────────────────────────────

ECOSYSTEM_KEYWORDS = [
    "开源", "open source", "open-source", "github", "hugging face",
    "repository", "repo", "license", "许可证", "mit", "apache", "gpl",
    "framework", "框架", "library", "库", "sdk", "api", "platform",
    "社区", "community", "contributor", "star", "fork", "developer",
    "模型开源", "model release", "权重", "weights", "checkpoint",
    "mcp", "agent", "plugin", "插件", "extension", "工具链", "toolchain",
    "llama", "mistral", "deepseek", "qwen", "stable diffusion",
    "finetune", "微调", "lora", "deploy", "部署", "推理", "inference",
    "ollama", "vllm", "langchain", "llamaindex",
]

PROJECT_KEYWORDS = [
    "项目", "project", "repo", "github.com", "发布", "release",
    "star", "⭐", "trending", "新发布", "launch", "首次发布",
]

LICENSE_KEYWORDS = [
    "许可证", "license", "mit", "apache", "gpl", "bsd", "cc",
    "变更", "change", "安全", "security", "漏洞", "vulnerability",
    "cve", "停维", "deprecated", "eol", "end of life",
]

# ─── 数据加载 ──────────────────────────────────────

def find_latest_events_file(target_date: str = None):
    """定位最新的 CI Engine 事件 JSON 文件"""
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        dt = datetime.now()
    for i in range(4):
        attempt = dt - timedelta(days=i)
        year_month = attempt.strftime("%Y-%m")
        date_mmdd = attempt.strftime("%m%d")
        filepath = os.path.join(CI_ENGINE_EVENTS_DIR, year_month, f"{date_mmdd}_extracted.json")
        if os.path.exists(filepath):
            return filepath, attempt
    return None, None


def load_events(filepath: str) -> list:
    """加载 CI Engine 事件 JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v:
                return v
    return []


def load_from_radar(date_str: str) -> tuple:
    """从 Radar Pipeline 获取开源频道信号"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from radar.pipeline import run_radar_pipeline
        result = run_radar_pipeline(date_str=date_str, filter_tracked=True, verbose=False)
        signals = result["dispatched"].get("oss", [])
        print(f"  Radar Pipeline → oss: {len(signals)} 条")
        return signals, date_str
    except Exception as e:
        print(f"  Radar Pipeline 不可用 ({e})")
        return None, None


def load_modlib_report(date_str: str = None) -> str:
    """加载 ModLib 外部扫描日报"""
    if not os.path.exists(MODLIB_DAILY_DIR):
        print(f"  ⚠️  ModLib 日报目录不存在: {MODLIB_DAILY_DIR}")
        return ""
    
    if date_str:
        filename = f"external_scan_{date_str}.md"
    else:
        filename = f"external_scan_{datetime.now().strftime('%Y-%m-%d')}.md"
    
    filepath = os.path.join(MODLIB_DAILY_DIR, filename)
    if os.path.exists(filepath):
        print(f"  📄 ModLib 日报: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 找最新的日报
    files = sorted(glob.glob(os.path.join(MODLIB_DAILY_DIR, "external_scan_*.md")))
    if files:
        latest = files[-1]
        print(f"  📄 使用最新 ModLib 日报: {os.path.basename(latest)}")
        with open(latest, 'r', encoding='utf-8') as f:
            return f.read()
    
    print(f"  ⚠️  未找到 ModLib 日报")
    return ""


def extract_modlib_projects(modlib_text: str) -> list:
    """从 ModLib 日报中提取开源项目信息"""
    projects = []
    
    # 提取 navigator 报告引用
    nav_pattern = re.compile(r'navigator_[\d-]+_(.+?)\.md')
    nav_matches = nav_pattern.findall(modlib_text)
    
    # 提取 Profile 领域
    profile_pattern = re.compile(r'\*\*Profile 列表\*\*:\s*(.+?)(?:\n\n|\Z)', re.DOTALL)
    profile_match = profile_pattern.search(modlib_text)
    profiles = []
    if profile_match:
        profiles = [p.strip() for p in profile_match.group(1).split(',')]
    
    # 提取关键信息
    for match in nav_matches:
        projects.append({
            "name": match,
            "source": "ModLib Navigator",
            "profile": "discovery",
        })
    
    return projects, profiles


# ─── 开源信号过滤 ──────────────────────────────────

def filter_ecosystem_events(events: list) -> list:
    """从 CI Engine 事件中筛选开源/生态相关条目"""
    eco_events = []
    for e in events:
        title = e.get("title", "")
        summary = e.get("summary", "")
        tags = " ".join(e.get("tags", []))
        event_type = e.get("event_type", "")
        signal_type = e.get("signal_type", "")
        combined = f"{title} {summary} {tags} {event_type} {signal_type}".lower()
        
        if any(kw.lower() in combined for kw in ECOSYSTEM_KEYWORDS):
            eco_events.append(e)
        elif event_type in ("open_source_release", "platform_launch"):
            eco_events.append(e)
        elif signal_type == "ecosystem":
            eco_events.append(e)
    
    eco_events.sort(key=lambda e: e.get("importance_score", 0), reverse=True)
    return eco_events


# ─── 差异度计算 ────────────────────────────────────

def diversity_score(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 1.0
    return 1.0 - SequenceMatcher(None, text_a, text_b).ratio()


# ─── 模块生成 ──────────────────────────────────────

def generate_new_discoveries(events: list, modlib_text: str) -> str:
    """模块 1：昨日新发现（A 快反赛道）"""
    section = "## 昨日新发现（A 快反赛道）\n\n"
    section += "Top 5 新开源项目，每项含简介、⭐趋势、主要语言：\n\n"
    
    eco_events = filter_ecosystem_events(events)
    
    # 从 ModLib 日报提取项目信息
    modlib_projects, profiles = extract_modlib_projects(modlib_text)
    
    if not eco_events and not modlib_projects:
        section += "> 今日无显著的新开源项目发现。开源 AI 生态处于常规迭代节奏中。\n\n"
        section += "**持续关注领域：**\n\n"
        section += "- AI Agent 框架（LangChain / CrewAI / AutoGen / Coze）\n"
        section += "- 模型部署与推理（Ollama / vLLM / TensorRT-LLM）\n"
        section += "- 多模态与 AIGC（Stable Diffusion / ComfyUI / Diffusers）\n"
        section += "- MCP 与工具生态（Model Context Protocol 相关工具链）\n"
        section += "- 前端与 UI 工程（Vercel AI SDK / CopilotKit）\n\n"
        return section
    
    item_num = 1
    
    # ModLib 项目
    for proj in modlib_projects[:3]:
        section += f"### {item_num}. 📦 {proj['name']}\n\n"
        section += f"来源：{proj['source']} | 领域：{proj.get('profile', 'discovery')}\n\n"
        section += f"> ModLib 自动发现，详情见 Navigator 报告。\n\n"
        item_num += 1
    
    # CI Engine 事件
    for e in eco_events[:5 - len(modlib_projects[:3])]:
        title = e.get("title", "无标题")
        summary = e.get("summary", "")
        company = e.get("company", "?")
        score = e.get("importance_score", 0)
        
        section += f"### {item_num}. {title}\n\n"
        section += f"{summary[:200]}\n\n"
        section += f"> 公司：{company} | 影响力：{score:.2f} | 类型：{e.get('event_type', '?')}\n\n"
        item_num += 1
    
    return section


def generate_deep_project(events: list, modlib_text: str) -> str:
    """模块 2：重点项目深读（D 技术文档赛道）"""
    section = "## 重点项目深读（D 技术文档赛道）\n\n"
    
    eco_events = filter_ecosystem_events(events)
    high_score = [e for e in eco_events if e.get("importance_score", 0) >= 0.70]
    
    if not high_score and not modlib_text:
        section += "> 今日无需要深读的重点项目。\n\n"
        section += "**本周关注项目池：**\n\n"
        section += "1. **LangChain v0.4** — 多 Agent 编排成为核心能力\n"
        section += "2. **Ollama** — 本地模型部署持续降低门槛\n"
        section += "3. **MCP (Model Context Protocol)** — Anthropic 推动的工具调用标准\n"
        section += "4. **vLLM** — 推理引擎性能竞赛，FP8 量化成为标配\n"
        section += "5. **ComfyUI** — 节点式 AI 工作流成为设计新范式\n\n"
        return section
    
    if high_score:
        e = high_score[0]
        title = e.get("title", "")
        summary = e.get("summary", "")
        
        section += f"### {title}\n\n"
        section += "**技术栈分析：**\n\n"
        section += f"{summary}\n\n"
        
        section += "**架构洞察：**\n\n"
        tags = e.get("tags", [])
        if any("agent" in t.lower() for t in tags):
            section += "- 采用 Agent 架构，多步骤推理与工具调用\n"
        if any("open" in t.lower() or "开源" in t for t in tags):
            section += "- 开源策略：社区驱动开发，降低企业采用门槛\n"
        if any("model" in t.lower() for t in tags):
            section += "- 模型选型：关注其底层模型选择和微调策略\n"
        
        section += "\n**应用场景：**\n\n"
        dims = e.get("affected_dimensions", [])
        if dims:
            for d in dims:
                section += f"- {d}\n"
        else:
            section += "- AI 应用开发加速\n"
            section += "- 企业级 AI 部署\n"
        
        section += f"\n> 公司：{e.get('company', '?')} | 影响力：{e.get('importance_score', 0):.2f} | 信号类型：{e.get('signal_type', '?')}\n\n"
    else:
        section += "基于 ModLib 扫描数据，以下项目值得深读：\n\n"
        modlib_projects, _ = extract_modlib_projects(modlib_text)
        if modlib_projects:
            section += f"**{modlib_projects[0]['name']}**\n\n"
            section += f"来源：{modlib_projects[0]['source']}\n\n"
            section += "> 该项目在 ModLib 每日扫描中被自动发现，属于探索发现 Profile。建议使用 Navigator 报告获取详细信息。\n\n"
    
    return section


def generate_trend_signals(events: list) -> str:
    """模块 3：开源趋势信号（A 快反赛道）"""
    section = "## 开源趋势信号（A 快反赛道）\n\n"
    section += "本周出现的新方向/范式转变：\n\n"
    
    eco_events = filter_ecosystem_events(events)
    
    if not eco_events:
        section += "**当前开源 AI 生态主要趋势：**\n\n"
        section += "1. **Agent 框架竞争加剧** — LangChain / CrewAI / AutoGen / Coze 争夺开发者心智\n"
        section += "2. **MCP 协议标准化** — Model Context Protocol 正成为 AI 工具调用的事实标准\n"
        section += "3. **模型推理优化** — FP8/INT4 量化 + vLLM/TensorRT 推理加速成为标配\n"
        section += "4. **多模态开源爆发** — 从文本→图像→视频→3D，开源模型全模态覆盖\n"
        section += "5. **本地优先（Local-First）** — Ollama/LM Studio 推动模型本地化部署\n\n"
        return section
    
    for i, e in enumerate(eco_events[:3], 1):
        title = e.get("title", "")
        direction = e.get("delta", {}).get("direction", "neutral")
        icon = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(direction, "➡️")
        section += f"- {icon} **{title}** — {e.get('summary', '')[:120]}\n"
    
    section += "\n"
    return section


def generate_license_alert(events: list) -> str:
    """模块 4：许可证与合规警示（A 快反赛道）"""
    section = "## 许可证与合规警示（A 快反赛道）\n\n"
    
    license_events = []
    for e in events:
        title = e.get("title", "")
        summary = e.get("summary", "")
        combined = f"{title} {summary}".lower()
        if any(kw.lower() in combined for kw in LICENSE_KEYWORDS):
            license_events.append(e)
    
    if not license_events:
        section += "> ✅ 今日无许可证变更、安全漏洞或停维通知。\n\n"
        section += "**持续监控清单：**\n\n"
        section += "| 项目 | 许可证 | 风险等级 |\n"
        section += "|------|--------|----------|\n"
        section += "| Llama 4 | Llama 4 Community License | 🟡 中等（商用限制） |\n"
        section += "| Mistral Large | Apache 2.0（研究）/ 商用许可 | 🟢 低 |\n"
        section += "| DeepSeek V3 | MIT | 🟢 低 |\n"
        section += "| Qwen 3 | Apache 2.0 | 🟢 低 |\n\n"
        return section
    
    for e in license_events[:3]:
        title = e.get("title", "")
        summary = e.get("summary", "")
        section += f"### ⚠️ {title}\n\n"
        section += f"{summary}\n\n"
    
    section += "\n"
    return section


def build_oss_daily(events: list, modlib_text: str, report_date: str) -> str:
    """组装完整开源雷达日报"""
    eco_events = filter_ecosystem_events(events)
    
    discoveries = generate_new_discoveries(events, modlib_text)
    deep_project = generate_deep_project(events, modlib_text)
    trends = generate_trend_signals(events)
    license_alert = generate_license_alert(events)
    
    # Stage 差异度
    a_text = discoveries + trends + license_alert
    d_text = deep_project
    diversity = diversity_score(a_text, d_text)
    
    modlib_note = ""
    if modlib_text:
        modlib_note = " | 含 ModLib 外部扫描数据"
    
    report = f"""# AI 开源雷达日报 — {report_date}

> 🎯 A 快反赛道 + D 技术文档赛道 | Stage 差异度 {diversity:.2f} | {len(eco_events)} 条生态信号{modlib_note}

{discoveries}
---

{deep_project}
---

{trends}
---

{license_alert}
---

*📋 报告由 SmartTextPlatform SR-CH-003 自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')} Asia/Shanghai*
*📊 数据源：CI Engine + ModLib 外部扫描 + Radar Pipeline*
"""
    return report


# ─── 入口 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SR-CH-003 AI 开源雷达日报生成")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD")
    parser.add_argument("--radar", action="store_true", help="优先使用 Radar Pipeline")
    parser.add_argument("--no-modlib", action="store_true", help="不使用 ModLib 数据")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  SR-CH-003: AI 开源雷达日报生成器")
    print("=" * 60)
    
    events = []
    report_date = args.date or datetime.now().strftime("%Y-%m-%d")
    
    # ── Radar Pipeline 模式 ──
    if args.radar:
        print(f"\n🛰️  数据源: Radar Pipeline")
        radar_signals, _ = load_from_radar(args.date)
        if radar_signals:
            events = radar_signals
        else:
            print("  Radar 未返回生态信号，回退 CI Engine 模式")
    
    # ── CI Engine 模式 ──
    if not events:
        print(f"\n📂 数据源: CI Engine + 关键词过滤")
        filepath, actual_date = find_latest_events_file(args.date)
        if not filepath:
            print("⚠️  未找到 CI Engine 事件文件，将仅使用 ModLib 数据")
        else:
            report_date = actual_date.strftime("%Y-%m-%d")
            print(f"📂 数据文件: {filepath}")
            events = load_events(filepath)
    
    print(f"📊 原始事件: {len(events)} 条")
    
    # 过滤生态事件
    eco_events = filter_ecosystem_events(events)
    print(f"🔬 开源/生态相关事件: {len(eco_events)} 条")
    
    # 加载 ModLib 日报
    modlib_text = ""
    if not args.no_modlib:
        modlib_text = load_modlib_report(args.date)
        if modlib_text:
            print(f"📄 ModLib 日报长度: {len(modlib_text):,} 字符")
    
    # 生成报告
    print(f"\n📝 生成开源雷达日报...")
    report = build_oss_daily(events, modlib_text, report_date)
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{report_date}.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 开源雷达日报已生成: {output_path}")
    print(f"   字符数: {len(report):,}")
    print(f"   行数: {report.count(chr(10))}")
    
    # 信号覆盖
    covered = set()
    for e in eco_events:
        for kw in ECOSYSTEM_KEYWORDS[:10]:
            if kw.lower() in f"{e.get('title','')} {e.get('summary','')}".lower():
                covered.add(kw)
    if modlib_text:
        covered.add("ModLib")
    print(f"   覆盖信号维度: {len(covered)}")
    print("=" * 60)
    
    return output_path


if __name__ == "__main__":
    main()
