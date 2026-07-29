"""
SmartTextPlatform — 集群文字创作能力基准测试
=================================================
6 集群 × 3 用例 = 18 个测试场景
每个用例评估：内容生成 + 质量评分 + 性能指标
支持 mock 模式和真实 LLM 模式
"""

import sys, os, json, time, yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
from shared.cluster_engine import ClusterEngine

# ═══════════════════════════════════════
# 18 个基准测试用例 — 覆盖 6 集群
# ═══════════════════════════════════════

TEST_CASES = [
    # ── CLUSTER-A 实时快反 (flashnews) ──
    {
        "id": "A1",
        "cluster": "flashnews",
        "label": "A股午间快讯",
        "spec": {
            "structured_spec": {
                "core_intent": "A股三大指数午间收盘快报",
                "product_type": "新闻/快讯",
                "depth": "快讯级 (≤500字)",
                "timeliness": "实时",
                "target_audience": "散户投资者",
                "style": "数据驱动",
                "domain_tags": ["金融", "证券"],
                "channel": "公众号",
            },
            "configuration": {"cluster": "A"},
        },
        "expect": {
            "min_chars": 50,
            "format_checks": ["包含涨跌幅数据", "覆盖三大指数", "≤300字"],
            "style": "简洁、数据密集、无评论",
        },
    },
    {
        "id": "A2",
        "cluster": "flashnews",
        "label": "科技行业收盘速递",
        "spec": {
            "structured_spec": {
                "core_intent": "今日科技板块收盘速递",
                "product_type": "新闻/快讯",
                "depth": "快讯级",
                "target_audience": "投资人群",
                "timeliness": "日内",
                "domain_tags": ["科技", "金融"],
            },
            "configuration": {"cluster": "A"},
        },
        "expect": {
            "min_chars": 50,
            "format_checks": ["聚焦科技板块", "≤300字"],
            "style": "信息密度高、快节奏",
        },
    },
    {
        "id": "A3",
        "cluster": "flashnews",
        "label": "突发事件快报",
        "spec": {
            "structured_spec": {
                "core_intent": "某科技公司发布重大产品，股价盘前大涨15%",
                "product_type": "新闻/快讯",
                "depth": "快讯级",
                "timeliness": "实时",
                "target_audience": "散户投资者",
                "domain_tags": ["科技", "金融", "突发事件"],
            },
            "configuration": {"cluster": "A"},
        },
        "expect": {
            "min_chars": 40,
            "format_checks": ["含事件要点", "含市场反应", "≤200字"],
            "style": "快速、关键点突出",
        },
    },

    # ── CLUSTER-B 深度生产 (deepprod) ──
    {
        "id": "B1",
        "cluster": "deepprod",
        "label": "半导体设备国产化深度分析",
        "spec": {
            "structured_spec": {
                "core_intent": "中国半导体设备国产化进程深度分析",
                "product_type": "分析/报告",
                "depth": "深度 (≥5000字)",
                "target_audience": "投资人群",
                "style": "数据驱动",
                "domain_tags": ["科技", "半导体", "制造"],
                "constraints": ["需引用来源", "需数据支撑"],
            },
            "configuration": {"cluster": "B", "config_name": "industry_analysis"},
        },
        "expect": {
            "min_chars": 800,
            "format_checks": ["含执行摘要", "含数据分析", "含投资建议", "结构化分段"],
            "style": "专业、深度、数据驱动",
        },
    },
    {
        "id": "B2",
        "cluster": "deepprod",
        "label": "新能源产业政策分析",
        "spec": {
            "structured_spec": {
                "core_intent": "2026年新能源汽车政策梳理与影响分析",
                "product_type": "分析/报告",
                "depth": "深度",
                "target_audience": "决策者",
                "style": "论证导向",
                "domain_tags": ["能源", "政策", "汽车"],
            },
            "configuration": {"cluster": "B", "config_name": "policy_analysis"},
        },
        "expect": {
            "min_chars": 800,
            "format_checks": ["含政策梳理", "含影响评估", "含建议"],
            "style": "严谨、论证充分",
        },
    },
    {
        "id": "B3",
        "cluster": "deepprod",
        "label": "AI大模型竞争格局报告",
        "spec": {
            "structured_spec": {
                "core_intent": "全球AI大模型竞争格局与趋势2026",
                "product_type": "行业研究",
                "depth": "深度",
                "target_audience": "投资人群+技术决策者",
                "style": "数据驱动+论证导向",
                "domain_tags": ["AI", "科技"],
                "constraints": ["需多维度对比", "需趋势预测"],
            },
            "configuration": {"cluster": "B", "config_name": "industry_analysis"},
        },
        "expect": {
            "min_chars": 800,
            "format_checks": ["含竞争格局分析", "含技术对比", "含趋势预测"],
            "style": "宏观视角、数据翔实",
        },
    },

    # ── CLUSTER-C 创意转化 (creativex) ──
    {
        "id": "C1",
        "cluster": "creativex",
        "label": "双十一促销文案",
        "spec": {
            "structured_spec": {
                "core_intent": "双十一大促活动营销文案",
                "product_type": "营销文案",
                "target_audience": "C端用户",
                "style": "情感共鸣+转化导向",
                "domain_tags": ["消费", "电商"],
                "channel": "社交媒体",
            },
            "configuration": {"cluster": "C"},
        },
        "expect": {
            "min_chars": 50,
            "format_checks": ["含痛点描述", "含行动号召", "有感染力"],
            "style": "生动、有吸引力、转化导向",
        },
    },
    {
        "id": "C2",
        "cluster": "creativex",
        "label": "品牌故事文案",
        "spec": {
            "structured_spec": {
                "core_intent": "新消费品牌创立故事",
                "product_type": "品牌文案",
                "target_audience": "25-35岁都市消费者",
                "style": "叙事为主",
                "domain_tags": ["消费", "品牌"],
                "channel": "公众号",
            },
            "configuration": {"cluster": "C"},
        },
        "expect": {
            "min_chars": 100,
            "format_checks": ["有故事性", "有情感共鸣", "有品牌价值表达"],
            "style": "叙事感、有温度",
        },
    },
    {
        "id": "C3",
        "cluster": "creativex",
        "label": "科技产品发布会文案",
        "spec": {
            "structured_spec": {
                "core_intent": "新款智能手表发布营销文案",
                "product_type": "营销文案",
                "target_audience": "科技爱好者",
                "style": "科技感+场景化",
                "domain_tags": ["科技", "消费电子"],
                "channel": "社交媒体",
            },
            "configuration": {"cluster": "C"},
        },
        "expect": {
            "min_chars": 50,
            "format_checks": ["含产品亮点", "含使用场景", "有科技感"],
            "style": "新颖、科技感强",
        },
    },

    # ── CLUSTER-D 技术文档 (techdoc) ──
    {
        "id": "D1",
        "cluster": "techdoc",
        "label": "REST API 接口文档",
        "spec": {
            "structured_spec": {
                "core_intent": "REST API 用户认证接口文档",
                "product_type": "技术文档",
                "target_audience": "技术人群",
                "depth": "中篇",
                "style": "技术准确",
                "domain_tags": ["技术", "软件"],
                "constraints": ["含代码示例", "含错误码"],
            },
            "configuration": {"cluster": "D"},
        },
        "expect": {
            "min_chars": 200,
            "format_checks": ["含认证流程", "含代码示例", "含错误码说明", "结构化(标题分层)"],
            "style": "精确、结构化、可执行",
        },
    },
    {
        "id": "D2",
        "cluster": "techdoc",
        "label": "Python SDK 安装指南",
        "spec": {
            "structured_spec": {
                "core_intent": "Python SDK 安装与快速上手指南",
                "product_type": "用户手册",
                "target_audience": "开发者",
                "style": "技术准确",
                "domain_tags": ["技术", "软件"],
                "constraints": ["含安装步骤", "含代码示例", "含FAQ"],
            },
            "configuration": {"cluster": "D"},
        },
        "expect": {
            "min_chars": 150,
            "format_checks": ["含安装步骤", "含代码示例", "含FAQ或常见问题"],
            "style": "清晰、可操作",
        },
    },
    {
        "id": "D3",
        "cluster": "techdoc",
        "label": "架构设计文档",
        "spec": {
            "structured_spec": {
                "core_intent": "微服务架构设计文档",
                "product_type": "架构文档",
                "target_audience": "技术决策者",
                "depth": "中篇",
                "style": "技术准确",
                "domain_tags": ["技术", "软件架构"],
                "constraints": ["含架构图描述", "含技术选型理由"],
            },
            "configuration": {"cluster": "D"},
        },
        "expect": {
            "min_chars": 200,
            "format_checks": ["含架构概要", "含技术选型说明", "含模块划分"],
            "style": "系统性强、逻辑清晰",
        },
    },

    # ── CLUSTER-E 知识科普 (scipop) ──
    {
        "id": "E1",
        "cluster": "scipop",
        "label": "量子计算科普",
        "spec": {
            "structured_spec": {
                "core_intent": "用通俗语言解释量子计算基本原理",
                "product_type": "科普/教程",
                "target_audience": "普通大众",
                "style": "通俗易懂+类比丰富",
                "domain_tags": ["科技", "量子"],
                "channel": "公众号",
            },
            "configuration": {"cluster": "E"},
        },
        "expect": {
            "min_chars": 200,
            "format_checks": ["含类比/比喻", "无过度专业术语", "有故事性"],
            "style": "轻松、有趣、易懂",
        },
    },
    {
        "id": "E2",
        "cluster": "scipop",
        "label": "AI工作原理科普",
        "spec": {
            "structured_spec": {
                "core_intent": "解释大语言模型如何工作",
                "product_type": "科普/教程",
                "target_audience": "学生",
                "depth": "短篇",
                "style": "通俗易懂",
                "domain_tags": ["AI", "科技"],
                "channel": "社交媒体",
            },
            "configuration": {"cluster": "E"},
        },
        "expect": {
            "min_chars": 150,
            "format_checks": ["含类比", "含简单示例", "面向非专业读者"],
            "style": "浅显、有趣",
        },
    },
    {
        "id": "E3",
        "cluster": "scipop",
        "label": "基因编辑科普",
        "spec": {
            "structured_spec": {
                "core_intent": "CRISPR基因编辑技术科普",
                "product_type": "科普/教程",
                "target_audience": "普通大众",
                "style": "通俗易懂",
                "domain_tags": ["生物", "医疗"],
                "constraints": ["需伦理讨论"],
            },
            "configuration": {"cluster": "E"},
        },
        "expect": {
            "min_chars": 200,
            "format_checks": ["含机制解释", "含应用案例", "含伦理讨论"],
            "style": "科学严谨但不晦涩",
        },
    },

    # ── CLUSTER-F 观点论证 (oped) ──
    {
        "id": "F1",
        "cluster": "oped",
        "label": "AI监管观点",
        "spec": {
            "structured_spec": {
                "core_intent": "AI监管需要全球协作而非各自为政",
                "product_type": "评论/观点",
                "target_audience": "决策者+专业人士",
                "style": "论证导向",
                "domain_tags": ["AI", "政策"],
            },
            "configuration": {"cluster": "F"},
        },
        "expect": {
            "min_chars": 200,
            "format_checks": ["含明确论点", "含论据支撑", "含反方观点回应"],
            "style": "有深度、论证严密",
        },
    },
    {
        "id": "F2",
        "cluster": "oped",
        "label": "远程办公利弊分析",
        "spec": {
            "structured_spec": {
                "core_intent": "远程办公对创新力的影响",
                "product_type": "评论/观点",
                "target_audience": "企业管理者",
                "style": "论证导向",
                "domain_tags": ["管理", "职场"],
            },
            "configuration": {"cluster": "F"},
        },
        "expect": {
            "min_chars": 200,
            "format_checks": ["含正反方分析", "含研究引用", "含结论判断"],
            "style": "客观、有深度",
        },
    },
    {
        "id": "F3",
        "cluster": "oped",
        "label": "开源vs闭源AI",
        "spec": {
            "structured_spec": {
                "core_intent": "开源AI模型vs闭源AI模型的未来博弈",
                "product_type": "评论/观点",
                "target_audience": "科技从业者",
                "style": "论证导向",
                "domain_tags": ["AI", "开源"],
            },
            "configuration": {"cluster": "F"},
        },
        "expect": {
            "min_chars": 200,
            "format_checks": ["含多角度分析", "含趋势判断", "含个人观点"],
            "style": "有深度、有立场",
        },
    },
]

# ═══════════════════════════════════════
# 质量评分器
# ═══════════════════════════════════════

def score_content(content: str, expected: dict, cluster_id: str) -> dict:
    """对生成内容进行多维度评分 (0-100)"""
    scores = {}
    
    # 1. 内容长度是否达标
    min_chars = expected.get("min_chars", 0)
    if len(content) >= min_chars:
        scores["length_adequate"] = 100
    elif len(content) > 0:
        scores["length_adequate"] = int(len(content) / min_chars * 100)
    else:
        scores["length_adequate"] = 0
    
    # 2. 格式检查 — 期望的关键元素是否出现
    format_checks = expected.get("format_checks", [])
    if format_checks:
        passed = 0
        for check in format_checks:
            # 模糊匹配：检查内容中是否包含相关关键词
            keywords = check.replace("含", "").replace("≤", "").replace("字", "").strip()
            # 对于"含X"类型的检查，做宽松匹配
            if any(kw in content for kw in keywords.split("、") if kw):
                passed += 1
        scores["format_completeness"] = int(passed / len(format_checks) * 100)
    else:
        scores["format_completeness"] = 100
    
    # 3. 内容非空/非模板化
    if content and len(content.strip()) > 10:
        scores["non_empty"] = 100
    else:
        scores["non_empty"] = 0
    
    # 4. 结构检查 — 是否有标题/分段等结构化元素
    has_structure = any(marker in content for marker in ["#", "##", "**", "1.", "- ", "\n\n"])
    scores["has_structure"] = 100 if has_structure else 50
    
    # 5. 原创性 — 是否含 mock 标记
    is_mock = "[mock]" in content.lower() or "Mock content" in content
    scores["is_real"] = 0 if is_mock else 100
    
    # 综合分
    weights = {
        "length_adequate": 0.20,
        "format_completeness": 0.30,
        "non_empty": 0.15,
        "has_structure": 0.15,
        "is_real": 0.20,
    }
    overall = sum(scores.get(k, 0) * w for k, w in weights.items())
    scores["overall"] = round(overall)
    
    return scores


# ═══════════════════════════════════════
# 主测试运行器
# ═══════════════════════════════════════

def run_benchmark(cluster_id: str = None, verbose: bool = True):
    """运行基准测试"""
    cases = TEST_CASES
    if cluster_id:
        cases = [c for c in cases if c["cluster"] == cluster_id]
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "platform_version": "1.0.0",
        "total_cases": len(cases),
        "passed": 0,
        "failed": 0,
        "cases": [],
        "summary": {},
    }
    
    cluster_stats = {}
    
    for case in cases:
        cid = case["id"]
        cluster = case["cluster"]
        label = case["label"]
        
        if verbose:
            print(f"\n{'─'*50}")
            print(f"  [{cid}] {label}  ({cluster})")
        
        t0 = time.time()
        
        try:
            engine = ClusterEngine(cluster)
            pipeline_result = engine.run_full_pipeline(case["spec"])
            latency = (time.time() - t0) * 1000
            
            # 收集所有 stage 输出
            all_content = ""
            stages_passed = 0
            stages_total = len(pipeline_result)
            
            for sid, r in pipeline_result.items():
                content = r.get("output", {}).get("content", "")
                all_content += content
                if r.get("gate_passed"):
                    stages_passed += 1
            
            # 评分
            quality = score_content(all_content, case["expect"], cluster)
            
            # 判断通过
            passed = (
                stages_passed == stages_total
                and quality["overall"] >= 50
                and len(all_content) > 0
            )
            
            case_result = {
                "id": cid,
                "cluster": cluster,
                "label": label,
                "passed": passed,
                "mock_mode": engine.mock_mode,
                "stages": f"{stages_passed}/{stages_total}",
                "total_chars": len(all_content),
                "latency_ms": round(latency),
                "quality": quality,
                "content_preview": all_content[:200] + ("..." if len(all_content) > 200 else ""),
            }
            
            if verbose:
                status = "✅" if passed else "❌"
                mock_tag = " [MOCK]" if engine.mock_mode else ""
                print(f"  {status} stages={stages_passed}/{stages_total} "
                      f"chars={len(all_content)} latency={latency:.0f}ms "
                      f"quality={quality['overall']}{mock_tag}")
                if not passed:
                    print(f"     └─ quality: {json.dumps(quality, ensure_ascii=False)}")
            
            results["cases"].append(case_result)
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            # 集群统计
            if cluster not in cluster_stats:
                cluster_stats[cluster] = {"total": 0, "passed": 0, "total_chars": 0, "total_latency": 0}
            cluster_stats[cluster]["total"] += 1
            if passed:
                cluster_stats[cluster]["passed"] += 1
            cluster_stats[cluster]["total_chars"] += len(all_content)
            cluster_stats[cluster]["total_latency"] += latency
            
        except Exception as e:
            if verbose:
                print(f"  ❌ ERROR: {str(e)[:100]}")
            results["cases"].append({
                "id": cid, "cluster": cluster, "label": label,
                "passed": False, "error": str(e),
            })
            results["failed"] += 1
    
    # 汇总
    results["summary"] = {
        "per_cluster": {
            k: {
                "pass_rate": f"{v['passed']}/{v['total']}",
                "avg_chars": round(v["total_chars"] / v["total"]) if v["total"] else 0,
                "avg_latency_ms": round(v["total_latency"] / v["total"]) if v["total"] else 0,
            }
            for k, v in cluster_stats.items()
        },
        "overall_pass_rate": f"{results['passed']}/{results['total_cases']}",
        "mock_mode": engine.mock_mode if 'engine' in dir() else True,
    }
    
    return results


def main():
    print("=" * 60)
    print("  SmartTextPlatform — 集群文字创作能力基准测试")
    print("=" * 60)
    
    results = run_benchmark()
    
    # 保存结果
    results_dir = BASE / "tests" / "continuous" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = results_dir / f"benchmark_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 汇总报告
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total: {results['total_cases']} cases")
    print(f"  Passed: {results['passed']} ✅")
    print(f"  Failed: {results['failed']} ❌")
    print(f"  Mock mode: {results['summary']['mock_mode']}")
    
    print(f"\n  Per Cluster:")
    for cluster, stats in sorted(results["summary"]["per_cluster"].items()):
        print(f"    {cluster}: {stats['pass_rate']} pass | "
              f"avg {stats['avg_chars']} chars | {stats['avg_latency_ms']}ms")
    
    print(f"\n  Results saved: {result_file}")
    print(f"{'='*60}")
    
    return results


if __name__ == "__main__":
    main()
