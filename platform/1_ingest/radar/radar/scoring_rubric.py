#!/usr/bin/env python3
"""
Radar 评分引擎 — Scoring Rubric
================================
按信号类型拆维评分：每种类型 2-3 个维度，加权聚合。
每条信号的分数有维度分解和简短理由。

6 种信号类型 × 维度矩阵:
  capability:   性能提升幅度(40%) + 竞品差距变化(30%) + 落地时间(30%)
  structural:   影响范围·公司数(40%) + 资本规模(30%) + 不可逆程度(30%)
  supply_chain: 产能变化%(50%) + 价格变化%(30%) + 替代方案可用性(20%)
  ecosystem:    采用速度(30%) + 网络效应潜力(40%) + 护城河深度(30%)
  paradigm:     新颖度(50%) + 可复制性(25%) + UX 改善幅度(25%)
  risk:         危害严重度(50%) + 发生概率(30%) + 可控性(20%)

用法:
  from radar.scoring_rubric import score_event, score_batch
"""

import json
from typing import Dict, Tuple

# ══════════════════════════════════════════════
# 维度定义
# ══════════════════════════════════════════════

DIMENSION_SCHEMA = {
    "capability": {
        "performance_leap": {
            "label": "性能提升幅度",
            "weight": 0.40,
            "description": "技术指标（参数量/上下文/推理速度/准确率）的提升程度",
        },
        "competitive_gap": {
            "label": "竞品差距变化",
            "weight": 0.30,
            "description": "与竞品的差距是拉大还是缩小",
        },
        "time_to_market": {
            "label": "落地时间",
            "weight": 0.30,
            "description": "从发布到实际可用的时间周期",
        },
    },
    "structural": {
        "impact_scope": {
            "label": "影响范围·公司数",
            "weight": 0.40,
            "description": "受影响的直接和间接公司数量",
        },
        "capital_scale": {
            "label": "资本规模",
            "weight": 0.30,
            "description": "涉及的资本量级（融资金额/市值影响）",
        },
        "irreversibility": {
            "label": "不可逆程度",
            "weight": 0.30,
            "description": "变化是否可逆（IPO/收购 > 合作/任命）",
        },
    },
    "supply_chain": {
        "capacity_change": {
            "label": "产能变化幅度",
            "weight": 0.50,
            "description": "产能/供应量的百分比变化",
        },
        "price_impact": {
            "label": "价格变化幅度",
            "weight": 0.30,
            "description": "价格变化的百分比和方向",
        },
        "alternatives": {
            "label": "替代方案可用性",
            "weight": 0.20,
            "description": "是否有可用的替代方案（越小=越重要）",
        },
    },
    "ecosystem": {
        "adoption_speed": {
            "label": "采用速度",
            "weight": 0.30,
            "description": "开发者/用户采纳的速度（下载量/forks/stars 增长）",
        },
        "network_effect": {
            "label": "网络效应潜力",
            "weight": 0.40,
            "description": "生态一旦建立能否形成自增强循环",
        },
        "moat_depth": {
            "label": "护城河深度",
            "weight": 0.30,
            "description": "生态壁垒有多深（数据/模型/平台锁定）",
        },
    },
    "paradigm": {
        "novelty": {
            "label": "新颖度",
            "weight": 0.50,
            "description": "交互模式/产品形态的创新程度（0=增量改进, 1=全新品类）",
        },
        "replicability": {
            "label": "可复制性",
            "weight": 0.25,
            "description": "被竞品复制的难度（越高=越有护城河）",
        },
        "ux_improvement": {
            "label": "UX 改善幅度",
            "weight": 0.25,
            "description": "用户体验的改善程度",
        },
    },
    "risk": {
        "severity": {
            "label": "危害严重度",
            "weight": 0.50,
            "description": "事件后果的严重程度",
        },
        "probability": {
            "label": "发生概率",
            "weight": 0.30,
            "description": "风险实际发生的概率",
        },
        "controllability": {
            "label": "可控性",
            "weight": 0.20,
            "description": "风险可被管理的程度（越低=越危险）",
        },
    },
}

# ══════════════════════════════════════════════
# 计分逻辑
# ══════════════════════════════════════════════

# CEILING 调整: 没有绝对天花板，保留极高影响力事件的可能性
# 但 0.95+ 的事件应该确实是"改写规则"级别的

def _score_capability(event: dict) -> Tuple[dict, dict]:
    """评分：capability 信号"""
    metrics = event.get("metrics", {})
    summary = event.get("summary", "").lower()
    tags = [t.lower() for t in event.get("tags", [])]
    text = summary + " " + " ".join(tags)
    title = event.get("title", "").lower()
    
    # 性能提升幅度
    perf_score = event.get("importance_score", 0.7)
    if "sota" in text or "benchmark" in text or "超越" in text:
        perf_score = max(perf_score, 0.90)
    if "首次" in title or "first" in title or "首个" in title:
        perf_score = max(perf_score, 0.85)
    
    perf_rationale = "综合多项基准指标判断"
    if "context_window" in text or "上下文" in text:
        perf_rationale = "上下文窗口/推理能力有显著扩展"
    if metrics:
        key_metrics = ", ".join(f"{k}={v}" for k, v in list(metrics.items())[:2])
        perf_rationale = f"关键指标: {key_metrics}"
    
    # 竞品差距变化
    gap_score = event.get("importance_score", 0.7) * 0.95
    gap_rationale = "基于与主要竞品的基准差距推断"
    if "frontier" in tags or "frontier" in text:
        gap_score = max(gap_score, 0.90)
        gap_rationale = "前沿能力突破，拉开与追赶者差距"
    if "open_source" in tags:
        gap_score = min(gap_score, 0.70)
        gap_rationale = "开源发布缩小了与闭源方案的差距"
    
    # 落地时间
    ttm_score = 0.75
    ttm_rationale = "预计未来 3-6 个月可用"
    if "量产" in text or "production" in text or "已上线" in text or "now available" in text:
        ttm_score = 0.95
        ttm_rationale = "已进入量产或已正式上线"
    if "preview" in text or "预览" in text or "demo" in text:
        ttm_score = 0.50
        ttm_rationale = "尚处于预览/演示阶段"
    if "今年" in text or "summer" in text or "秋季" in text:
        ttm_score = 0.80
        ttm_rationale = "年内有望落地"
    
    dims = {
        "performance_leap": {"score": round(perf_score, 2), "rationale": perf_rationale},
        "competitive_gap": {"score": round(gap_score, 2), "rationale": gap_rationale},
        "time_to_market": {"score": round(ttm_score, 2), "rationale": ttm_rationale},
    }
    
    weight = DIMENSION_SCHEMA["capability"]
    agg = round(
        dims["performance_leap"]["score"] * weight["performance_leap"]["weight"] +
        dims["competitive_gap"]["score"] * weight["competitive_gap"]["weight"] +
        dims["time_to_market"]["score"] * weight["time_to_market"]["weight"], 2
    )
    
    return dims, agg


def _score_structural(event: dict) -> Tuple[dict, dict]:
    """评分：structural 信号"""
    event_type = event.get("event_type", "").lower()
    summary = event.get("summary", "").lower()
    tags = [t.lower() for t in event.get("tags", [])]
    text = summary + " " + " ".join(tags)
    
    # 影响范围
    scope_score = event.get("importance_score", 0.7)
    scope_rationale = "影响范围评估"
    if event_type in ("ipo",):
        scope_score = max(scope_score, 0.92)
        scope_rationale = "IPO 影响整个赛道的估值体系和资本流动"
    if event_type in ("funding",):
        scope_score = max(scope_score, 0.80)
        scope_rationale = "大规模融资改变行业竞争格局"
    if "ecosystem" in text or "生态" in text:
        scope_score += 0.05
    
    # 资本规模
    capital_score = event.get("importance_score", 0.7) * 0.9
    capital_rationale = "资本量级推断"
    if "ipo" in text or "s-1" in text:
        capital_score = 0.95
        capital_rationale = "IPO 规模预计数十亿至数百亿美元"
    if "billion" in text or "亿" in text:
        capital_score = max(capital_score, 0.85)
        capital_rationale = "涉及十亿美元级别资本运作"
    
    # 不可逆程度
    irrev_score = 0.70
    irrev_rationale = "中等不可逆"
    if event_type in ("ipo", "acquisition", "merger"):
        irrev_score = 0.95
        irrev_rationale = "IPO/并购一旦完成几乎不可逆"
    if event_type in ("funding",):
        irrev_score = 0.75
        irrev_rationale = "融资方向可调整但资本结构已改变"
    if event_type in ("partnership",):
        irrev_score = 0.60
        irrev_rationale = "合作关系可调整或终止"
    
    dims = {
        "impact_scope": {"score": round(scope_score, 2), "rationale": scope_rationale},
        "capital_scale": {"score": round(capital_score, 2), "rationale": capital_rationale},
        "irreversibility": {"score": round(irrev_score, 2), "rationale": irrev_rationale},
    }
    
    weight = DIMENSION_SCHEMA["structural"]
    agg = round(
        dims["impact_scope"]["score"] * weight["impact_scope"]["weight"] +
        dims["capital_scale"]["score"] * weight["capital_scale"]["weight"] +
        dims["irreversibility"]["score"] * weight["irreversibility"]["weight"], 2
    )
    
    return dims, agg


def _score_supply_chain(event: dict) -> Tuple[dict, dict]:
    """评分：supply_chain 信号"""
    metrics = event.get("metrics", {})
    summary = event.get("summary", "").lower()
    tags = [t.lower() for t in event.get("tags", [])]
    text = summary + " " + " ".join(tags)
    title = event.get("title", "").lower()
    
    # 产能变化
    cap_score = event.get("importance_score", 0.7)
    cap_rationale = "产能变化评估"
    if "量产" in title or "mass production" in text:
        cap_score = max(cap_score, 0.85)
        cap_rationale = "进入量产阶段，产能即将释放"
    if "shortage" in text or "供应不足" in text or "紧张" in text:
        cap_score = max(cap_score, 0.80)
        cap_rationale = "供应紧张，产能不足"
    if "中国" in title or "china" in text:
        cap_score = min(cap_score + 0.05, 1.0)
        cap_rationale = "中国市场定制产能释放"
    
    # 价格变化
    price_score = 0.65
    price_rationale = "价格变化待确认"
    if "降价" in title or "price" in text or "lower" in text:
        price_score = 0.80
        price_rationale = "显著降价，影响市场定价体系"
    if metrics.get("price_reduction_pct"):
        pct = metrics["price_reduction_pct"]
        price_score = min(0.60 + pct / 200, 1.0)
        price_rationale = f"价格下调 {pct}%"
    if "代际价格倒挂" in text or "price inversion" in text:
        price_score = 0.90
        price_rationale = "代际价格倒挂，市场信号异常"
    
    # 替代方案
    alt_score = 0.60
    alt_rationale = "存在部分替代方案"
    if "国产替代" in text or "alternative" in text:
        alt_score = 0.50
        alt_rationale = "国产替代方案正在形成"
    if "独家" in text or "exclusive" in text:
        alt_score = 0.30
        alt_rationale = "独家供应，替代方案有限"
    if "特供" in title:
        alt_score = 0.40
        alt_rationale = "特供产品，中国区替代方案有限"
    
    dims = {
        "capacity_change": {"score": round(cap_score, 2), "rationale": cap_rationale},
        "price_impact": {"score": round(price_score, 2), "rationale": price_rationale},
        "alternatives": {"score": round(alt_score, 2), "rationale": alt_rationale},
    }
    
    weight = DIMENSION_SCHEMA["supply_chain"]
    agg = round(
        dims["capacity_change"]["score"] * weight["capacity_change"]["weight"] +
        dims["price_impact"]["score"] * weight["price_impact"]["weight"] +
        dims["alternatives"]["score"] * weight["alternatives"]["weight"], 2
    )
    
    return dims, agg


def _score_ecosystem(event: dict) -> Tuple[dict, dict]:
    """评分：ecosystem 信号"""
    metrics = event.get("metrics", {})
    summary = event.get("summary", "").lower()
    tags = [t.lower() for t in event.get("tags", [])]
    text = summary + " " + " ".join(tags)
    
    # 采用速度
    adoption_score = event.get("importance_score", 0.7) * 0.9
    adoption_rationale = "采用速度推断"
    if metrics.get("derived_models"):
        count = metrics["derived_models"]
        if count >= 100000:
            adoption_score = 0.95
            adoption_rationale = f"衍生模型 {count//1000}K+，生态爆发式增长"
        elif count >= 10000:
            adoption_score = 0.85
            adoption_rationale = f"衍生模型 {count//1000}K+，生态快速增长"
    if metrics.get("downloads"):
        dl = metrics["downloads"]
        if dl >= 1_000_000_000:
            adoption_score = 0.95
            adoption_rationale = f"下载量 {dl//1_000_000_000}B+，全球最大开源生态"
    
    # 网络效应
    network_score = event.get("importance_score", 0.7)
    network_rationale = "网络效应评估"
    if "platform" in tags or "ecosystem" in tags:
        network_score = max(network_score, 0.85)
        network_rationale = "平台化构筑网络效应壁垒"
    if "agent_platform" in tags or "智能体平台" in text:
        network_score = max(network_score, 0.82)
        network_rationale = "Agent 平台形成双边网络效应"
    if "open_source" in tags:
        network_score = max(network_score, 0.80)
        network_rationale = "开源生态天然具有网络效应"
    
    # 护城河深度
    moat_score = 0.65
    moat_rationale = "护城河正在形成"
    if "下载量" in text and ("亿" in text or "billion" in text):
        moat_score = 0.90
        moat_rationale = "下载量级已构成强大生态护城河"
    if "独占" in text or "独家" in text:
        moat_score = 0.85
    if "ecosystem" in tags:
        moat_score = max(moat_score, 0.80)
        moat_rationale = "生态壁垒成型"
    
    dims = {
        "adoption_speed": {"score": round(adoption_score, 2), "rationale": adoption_rationale},
        "network_effect": {"score": round(network_score, 2), "rationale": network_rationale},
        "moat_depth": {"score": round(moat_score, 2), "rationale": moat_rationale},
    }
    
    weight = DIMENSION_SCHEMA["ecosystem"]
    agg = round(
        dims["adoption_speed"]["score"] * weight["adoption_speed"]["weight"] +
        dims["network_effect"]["score"] * weight["network_effect"]["weight"] +
        dims["moat_depth"]["score"] * weight["moat_depth"]["weight"], 2
    )
    
    return dims, agg


def _score_paradigm(event: dict) -> Tuple[dict, dict]:
    """评分：paradigm 信号"""
    summary = event.get("summary", "").lower()
    tags = [t.lower() for t in event.get("tags", [])]
    title = event.get("title", "").lower()
    text = summary + " " + " ".join(tags) + " " + title
    
    # 新颖度
    novelty_score = event.get("importance_score", 0.7)
    novelty_rationale = "增量改进"
    if "首次" in title or "首个" in title or "first" in title:
        novelty_score = max(novelty_score, 0.90)
        novelty_rationale = "首创性产品/交互形态"
    if "超级应用" in text or "super app" in text:
        novelty_score = max(novelty_score, 0.85)
        novelty_rationale = "超级应用形态代表新的交互范式"
    if "重新定义" in text or "重塑" in text or "新品类" in text:
        novelty_score = max(novelty_score, 0.88)
        novelty_rationale = "产品形态有重塑行业格局的潜力"
    
    # 可复制性（越高=越难复制）
    replicability_score = 0.60
    replicability_rationale = "中等可复制性"
    if "硬件" in text or "hardware" in text or "chip" in text:
        replicability_score = 0.85
        replicability_rationale = "硬件创新难以快速复制"
    if "platform" in tags or "平台" in text:
        replicability_score = 0.75
        replicability_rationale = "平台网络效应使得复制困难"
    if "copilot" in tags or "assistant" in text:
        replicability_score = 0.50
        replicability_rationale = "软件助理功能可被竞品快速跟进"
    
    # UX 改善幅度
    ux_score = 0.70
    ux_rationale = "UX 有显著改善"
    if "整合" in text or "integration" in text or "统一" in text:
        ux_score = 0.80
        ux_rationale = "统一入口大幅简化用户体验"
    if "agent" in text or "智能体" in text:
        ux_score = max(ux_score, 0.78)
        ux_rationale = "Agent 形态改变用户与 AI 的交互方式"
    if "混合" in text or "hybrid" in text:
        ux_score = 0.75
        ux_rationale = "混合推理改变延迟和隐私体验"
    
    dims = {
        "novelty": {"score": round(novelty_score, 2), "rationale": novelty_rationale},
        "replicability": {"score": round(replicability_score, 2), "rationale": replicability_rationale},
        "ux_improvement": {"score": round(ux_score, 2), "rationale": ux_rationale},
    }
    
    weight = DIMENSION_SCHEMA["paradigm"]
    agg = round(
        dims["novelty"]["score"] * weight["novelty"]["weight"] +
        dims["replicability"]["score"] * weight["replicability"]["weight"] +
        dims["ux_improvement"]["score"] * weight["ux_improvement"]["weight"], 2
    )
    
    return dims, agg


def _score_risk(event: dict) -> Tuple[dict, dict]:
    """评分：risk 信号"""
    summary = event.get("summary", "").lower()
    tags = [t.lower() for t in event.get("tags", [])]
    text = summary + " " + " ".join(tags)
    
    # 危害严重度
    severity_score = event.get("importance_score", 0.7)
    severity_rationale = "潜在危害评估"
    if "regulation" in tags or "监管" in text:
        severity_score = max(severity_score, 0.80)
        severity_rationale = "监管变化可能导致市场准入变化"
    if "safety" in tags or "安全" in text:
        severity_score = max(severity_score, 0.85)
        severity_rationale = "安全问题直接威胁用户信任和商业可行"
    if "consciousness" in tags or "意识" in text:
        severity_score = 0.75
        severity_rationale = "意识争议影响公众舆论和监管方向"
    
    # 发生概率
    prob_score = 0.60
    prob_rationale = "中等发生概率"
    if "已" in text or "已经" in text or "已发生" in text:
        prob_score = 0.90
        prob_rationale = "事件已经发生"
    if "可能" in text or "potential" in text:
        prob_score = 0.50
        prob_rationale = "潜在风险，尚未实际发生"
    
    # 可控性
    control_score = 0.50
    control_rationale = "部分可控"
    if "debate" in tags or "争议" in text:
        control_score = 0.60
        control_rationale = "通过行业讨论可能达成共识"
    if "regulation" in tags:
        control_score = 0.40
        control_rationale = "监管方向不完全由行业控制"
    
    dims = {
        "severity": {"score": round(severity_score, 2), "rationale": severity_rationale},
        "probability": {"score": round(prob_score, 2), "rationale": prob_rationale},
        "controllability": {"score": round(control_score, 2), "rationale": control_rationale},
    }
    
    weight = DIMENSION_SCHEMA["risk"]
    agg = round(
        dims["severity"]["score"] * weight["severity"]["weight"] +
        dims["probability"]["score"] * weight["probability"]["weight"] +
        dims["controllability"]["score"] * weight["controllability"]["weight"], 2
    )
    
    return dims, agg


# ══════════════════════════════════════════════
# Scorer Dispatcher
# ══════════════════════════════════════════════

_SCORER_MAP = {
    "capability": _score_capability,
    "structural": _score_structural,
    "supply_chain": _score_supply_chain,
    "ecosystem": _score_ecosystem,
    "paradigm": _score_paradigm,
    "risk": _score_risk,
}


def score_event(event: dict) -> dict:
    """
    对单条事件按类型拆维评分。
    
    要求事件已有 signal_type 字段（由 signal_taxonomy.classify 产出）。
    返回更新后的事件 dict，含 dimension_scores 和 aggregated importance_score。
    """
    signal_type = event.get("signal_type", "capability")
    
    if signal_type not in _SCORER_MAP:
        signal_type = "capability"  # fallback
    
    scorer = _SCORER_MAP[signal_type]
    dims, agg = scorer(event)
    
    event["dimension_scores"] = dims
    event["importance_score"] = agg  # 覆盖 CI Engine 原始分数
    
    return event


def score_batch(events: list) -> list:
    """批量评分，返回带评分的事件列表"""
    return [score_event(e) for e in events]


# ══════════════════════════════════════════════
# 格式化输出
# ══════════════════════════════════════════════

def format_score_detail(event: dict) -> str:
    """格式化单条信号的评分详情"""
    st = event.get("signal_type", "?")
    dims = event.get("dimension_scores", {})
    agg = event.get("importance_score", 0)
    
    lines = [
        f"信号: [{st}] {event.get('title', '')[:60]}",
        f"综合分: {agg:.2f}",
    ]
    
    schema = DIMENSION_SCHEMA.get(st, {})
    for dim_key, dim_info in schema.items():
        dim_data = dims.get(dim_key, {})
        score = dim_data.get("score", 0)
        rationale = dim_data.get("rationale", "")
        label = dim_info.get("label", dim_key)
        weight = dim_info.get("weight", 0)
        lines.append(f"  {label} ({weight*100:.0f}%): {score:.2f} — {rationale}")
    
    return "\n".join(lines)


# ══════════════════════════════════════════════
# CLI 测试
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    from radar.signal_taxonomy import classify_batch
    
    events_path = r"C:\Users\willi\.openclaw-autoclaw\agents\mkt\workspace\ci-engine\events\2026-06\0617_extracted.json"
    if os.path.exists(events_path):
        with open(events_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        # 先分类
        events = classify_batch(events)
        # 再评分
        scored = score_batch(events)
        
        print("=" * 60)
        print("  Radar 评分引擎 — 结果")
        print("=" * 60)
        
        # 按综合分排序
        scored.sort(key=lambda e: e.get("importance_score", 0), reverse=True)
        
        for i, e in enumerate(scored[:5], 1):
            print(f"\n── Top {i} ──")
            print(format_score_detail(e))
        
        # 统计
        print(f"\n{'='*60}")
        print("评分统计:")
        scores_list = [e.get("importance_score", 0) for e in scored]
        print(f"  事件数: {len(scored)}")
        print(f"  最高分: {max(scores_list):.2f}")
        print(f"  最低分: {min(scores_list):.2f}")
        print(f"  平均分: {sum(scores_list)/len(scores_list):.2f}")
        print(f"  ≥ 0.80 高分: {sum(1 for s in scores_list if s >= 0.80)} 条")
        print(f"  ≥ 0.60 中分: {sum(1 for s in scores_list if 0.60 <= s < 0.80)} 条")
        print(f"  < 0.60 低分: {sum(1 for s in scores_list if s < 0.60)} 条")
