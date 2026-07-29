"""
SmartTextPlatform — SmartText Engine
======================================
文字创作引擎主入口。

将 Signal Bundle JSON 转化为 Content Bundle JSON。
Prompt 配置从 YAML 加载，不再是硬编码。
内容形态由 formats/ 目录中的模板定义。

用法:
    from smartext import SmartTextEngine
    engine = SmartTextEngine()
    content = engine.generate(signal_bundle, "daily_report")
"""

import sys, os, json, yaml, logging, time
from pathlib import Path
from datetime import datetime
from typing import Optional

SMARTEXT_DIR = Path(__file__).parent

# 确保可以引用现有 shared/ 模块（兼容旧路径）
PROJECT_ROOT = SMARTEXT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.cluster_engine_v3 import ClusterEngineV3, StageContext, STAGE_SYSTEM_PROMPTS, STAGE_TOKEN_LIMITS
from .llm_gateway import LLMGateway, LLMResponse, ClusterLLMWriter

logger = logging.getLogger("smartext.engine")


class SmartTextEngine:
    """
    文字创作引擎 — 将 Signal Bundle 转化为 Content Bundle。
    
    Prompt 配置从 smartext/prompts/*.yaml 加载，不再硬编码。
    内容形态由 smartext/formats/*.py 定义。
    """
    
    # 内置 mock bundle（用于独立测试，无需 Radar 信号）
    MOCK_SIGNAL_BUNDLE = {
        "bundle_id": "mock_20260622",
        "domain": "ai_tech",
        "date": "2026-06-22",
        "meta": {"signals_count": 8, "companies_covered": 6, "avg_confidence": 0.85},
        "signals": [
            {
                "id": "sig_001", "type": "capability", "company": "nvidia",
                "title": "NVIDIA 发布下一代 GX200 GPU 架构",
                "summary": "NVIDIA 正式发布 GX200 架构，FP32 算力较上代提升 3.2x，采用全新 3nm 工艺与 HBM4 显存。首批产品预计 2026 Q3 量产出货。",
                "importance_score": 0.95, "confidence": 0.98, "verifiability": "L4",
                "source_url": "https://nvidia.com/blog/gx200",
                "tags": ["hardware", "GPU", "edge_ai"],
            },
            {
                "id": "sig_002", "type": "structural", "company": "openai",
                "title": "OpenAI 宣布 GPT-6 架构全面开放 API",
                "summary": "OpenAI 宣布 GPT-6 系列模型全面开放 API 访问，支持 256K 上下文窗口与多模态输入。企业版定价下调 40%。",
                "importance_score": 0.92, "confidence": 0.96, "verifiability": "L3",
                "source_url": "https://openai.com/blog/gpt6-api",
                "tags": ["大模型", "API", "多模态"],
            },
            {
                "id": "sig_003", "type": "supply_chain", "company": "tsmc",
                "title": "台积电 N2 工艺良率突破 85%",
                "summary": "台积电宣布 2nm 工艺良率已达 85%，预计 2026 Q4 量产。客户包括苹果、NVIDIA、AMD。",
                "importance_score": 0.88, "confidence": 0.95, "verifiability": "L4",
                "source_url": "https://tsmc.com/news/n2-yield",
                "tags": ["芯片", "制程", "供应链"],
            },
            {
                "id": "sig_004", "type": "ecosystem", "company": "microsoft",
                "title": "Microsoft Copilot 集成 DeepSeek 推理引擎",
                "summary": "Microsoft 宣布 Copilot 将集成 DeepSeek 推理引擎作为辅助推理后端，提升复杂任务的推理能力。",
                "importance_score": 0.91, "confidence": 0.94, "verifiability": "L3",
                "source_url": "https://microsoft.com/blog/copilot-deepseek",
                "tags": ["大模型", "Copilot", "生态"],
            },
            {
                "id": "sig_005", "type": "capability", "company": "google",
                "title": "Google Gemini 3 Ultra 在 MMLU-Pro 突破 93%",
                "summary": "Google DeepMind 发布 Gemini 3 Ultra，在 MMLU-Pro 基准上达到 93.1%，超越人类专家平均水平。TPU v6 同步发布。",
                "importance_score": 0.90, "confidence": 0.97, "verifiability": "L3",
                "source_url": "https://deepmind.google/blog/gemini-3",
                "tags": ["大模型", "基准测试", "TPU"],
            },
            {
                "id": "sig_006", "type": "structural", "company": "bytedance",
                "title": "字节跳动豆包大模型日活突破 2 亿",
                "summary": "字节跳动旗下豆包大模型宣布日活跃用户突破 2 亿，成为全球第二大大模型应用。超级入口战略初见成效。",
                "importance_score": 0.87, "confidence": 0.93, "verifiability": "L2",
                "source_url": "https://bytedance.com/news/doubao",
                "tags": ["大模型", "应用", "日活"],
            },
        ],
    }
    
    # 格式注册表：format name → module path
    _FORMAT_REGISTRY = {}
    
    # Prompt 缓存
    _PROMPT_CACHE = {}
    
    def __init__(self, api_key: str = None):
        """
        初始化引擎，加载所有 prompt 配置和格式模板。
        
        Args:
            api_key: DeepSeek API key。默认从环境变量 DEEPSEEK_API_KEY 读取。
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.llm = LLMGateway(api_key=api_key)
        self.mock_mode = not self.api_key
        
        # 加载所有 prompt 配置
        self._load_prompts()
        
        # 注册所有内容形态模板
        self._register_formats()
        
        logger.info(f"SmartTextEngine 初始化完成 (mock={self.mock_mode}, "
                   f"clusters={len(self._PROMPT_CACHE)}, formats={len(self._FORMAT_REGISTRY)})")
    
    def _load_prompts(self):
        """从 prompts/*.yaml 加载所有集群 Prompt 配置"""
        prompts_dir = SMARTEXT_DIR / "prompts"
        
        for yaml_file in sorted(prompts_dir.glob("*.yaml")):
            cluster_id = yaml_file.stem
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                self._PROMPT_CACHE[cluster_id] = config
                logger.debug(f"加载 Prompt: {cluster_id} ({len(config.get('stages', {}))} stages)")
            except Exception as e:
                logger.warning(f"加载 Prompt 失败 {yaml_file}: {e}")
        
        logger.info(f"加载 {len(self._PROMPT_CACHE)} 个集群 Prompt 配置")
    
    def _register_formats(self):
        """扫描 smartext/formats/ 注册所有内容形态模板"""
        formats_dir = SMARTEXT_DIR / "formats"
        
        for py_file in sorted(formats_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            
            format_name = py_file.stem
            try:
                # 动态导入格式模块
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    f"smartext.formats.{format_name}", py_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "FORMAT_SPEC"):
                    self._FORMAT_REGISTRY[format_name] = module
                    logger.debug(f"注册格式: {format_name} → {module.FORMAT_SPEC.get('name', format_name)}")
            except Exception as e:
                logger.warning(f"注册格式失败 {format_name}: {e}")
        
        logger.info(f"注册 {len(self._FORMAT_REGISTRY)} 个内容形态模板: {list(self._FORMAT_REGISTRY.keys())}")
    
    def get_prompt_config(self, cluster_id: str) -> Optional[dict]:
        """获取指定集群的 Prompt 配置"""
        return self._PROMPT_CACHE.get(cluster_id)
    
    def list_formats(self) -> list:
        """列出所有可用的内容形态"""
        return [
            {"id": name, "name": mod.FORMAT_SPEC.get("name", name)}
            for name, mod in self._FORMAT_REGISTRY.items()
        ]
    
    def list_clusters(self) -> list:
        """列出所有可用的集群"""
        return [
            {"id": cid, "name": cfg.get("cluster", {}).get("name", cid)}
            for cid, cfg in self._PROMPT_CACHE.items()
        ]
    
    def generate(self, signal_bundle: dict, format: str, **options) -> dict:
        """
        核心接口：将 Signal Bundle 转化为 Content Bundle。
        
        Args:
            signal_bundle: Signal Bundle JSON（来自 Radar 或 Mock）
            format: 内容形态名称，如 'daily_report' | 'wechat_article'
            **options: 额外选项（如 --date, --mock 等）
        
        Returns:
            Content Bundle JSON:
            {
                "bundle_id": "content_20260622_daily_report",
                "format": "daily_report",
                "generated_at": "2026-06-22T06:50:00",
                "sections": [...],
                "meta": {...},
            }
        """
        t0 = time.time()
        
        # 查找格式模板
        if format not in self._FORMAT_REGISTRY:
            available = list(self._FORMAT_REGISTRY.keys())
            return {
                "error": f"未知格式 '{format}'，可用: {available}",
                "bundle_id": "",
                "format": format,
                "sections": [],
                "meta": {"status": "error"},
            }
        
        format_module = self._FORMAT_REGISTRY[format]
        format_spec = format_module.FORMAT_SPEC
        
        logger.info(f"生成内容: format={format} ({format_spec.get('name')}), "
                   f"signals={signal_bundle.get('meta', {}).get('signals_count', len(signal_bundle.get('signals', [])))}")
        
        # 提取格式参数
        date_str = options.get("date", signal_bundle.get("date", datetime.now().strftime("%Y-%m-%d")))
        
        # 按 section 分组信号
        sections = []
        signals = signal_bundle.get("signals", [])
        
        for section_spec in format_spec.get("sections", []):
            section_content = self._generate_section(
                signals, section_spec, format_spec, signal_bundle, options
            )
            sections.append(section_content)
        
        # 生成热度统计
        heat_data = self._build_heat_data(signals)
        
        # 组装 Content Bundle
        total_words = sum(s.get("word_count", 0) for s in sections)
        total_latency = (time.time() - t0) * 1000
        
        content_bundle = {
            "bundle_id": f"content_{date_str.replace('-', '')}_{format}",
            "format": format,
            "format_name": format_spec.get("name", format),
            "generated_at": datetime.now().isoformat(),
            "source_bundle_id": signal_bundle.get("bundle_id", ""),
            "date": date_str,
            "sections": sections,
            "heat": heat_data,
            "meta": {
                "signals_processed": len(signals),
                "sections_generated": len(sections),
                "total_words": total_words,
                "total_latency_ms": round(total_latency, 1),
                "mock_mode": self.mock_mode,
                "output_format": format_spec.get("output_format", "markdown"),
            },
        }
        
        # 如果格式模块提供了 render 函数，生成完整 Markdown
        if hasattr(format_module, "render"):
            content_bundle["rendered"] = format_module.render(content_bundle, **options)
        
        logger.info(f"生成完成: {len(sections)} sections, {total_words} words, {total_latency:.0f}ms")
        
        return content_bundle
    
    def _generate_section(self, signals: list, section_spec: dict,
                          format_spec: dict, signal_bundle: dict, options: dict) -> dict:
        """为单个板块生成内容"""
        section_id = section_spec["id"]
        section_label = section_spec.get("label", section_id)
        cluster_id = section_spec.get("cluster", "flashnews")
        signal_type = section_spec.get("signal_type", None)
        max_items = section_spec.get("max_items", 3)
        
        # 筛选该板块的信号
        if signal_type:
            section_signals = [s for s in signals if s.get("type") == signal_type]
        else:
            section_signals = signals
        
        # 按重要性排序取 top N
        section_signals = sorted(
            section_signals,
            key=lambda s: s.get("importance_score", 0),
            reverse=True
        )[:max_items]
        
        # 构建该板块的 structured_spec
        signal_summaries = [
            f"{s.get('company','')}: {s.get('title','')} — {s.get('summary','')[:100]}"
            for s in section_signals
        ]
        
        structured_spec = {
            "core_intent": f"{section_label} - {format_spec.get('name', '')}板块",
            "section_id": section_id,
            "section_label": section_label,
            "product_type": "分析/摘要",
            "depth": "短篇",
            "signals": signal_summaries,
            "num_signals": len(section_signals),
        }
        
        router_output = {
            "structured_spec": structured_spec,
            "configuration": {"cluster": cluster_id},
        }
        
        # 使用集群引擎生成
        llm_content = ""
        stage_results = {}
        
        prompt_config = self._PROMPT_CACHE.get(cluster_id, {})
        
        if self.mock_mode or options.get("mock", False):
            # Mock 模式：直接格式化信号
            llm_content = self._mock_section_content(section_id, section_label, section_signals)
        else:
            try:
                engine = ClusterEngineV3(cluster_id)
                stage_results = engine.run_full_pipeline(router_output)
                
                # 提取最终 stage 的内容
                stages_list = prompt_config.get("stages", {})
                for sid in sorted(stage_results.keys()):
                    content = stage_results[sid].get("output", {}).get("content", "")
                    if content and len(content) > len(llm_content):
                        llm_content = content
            except Exception as e:
                logger.error(f"生成板块失败 {section_id}: {e}")
                llm_content = self._mock_section_content(section_id, section_label, section_signals)
        
        word_count = len(llm_content) if llm_content else 0
        
        return {
            "section_id": section_id,
            "label": section_label,
            "cluster": cluster_id,
            "signals_count": len(section_signals),
            "content": llm_content,
            "word_count": word_count,
            "signals": [s.get("id", "") for s in section_signals],
            "stage_results": {sid: r.get("status") for sid, r in stage_results.items()},
        }
    
    def _mock_section_content(self, section_id: str, label: str, signals: list) -> str:
        """生成 Mock 板块内容（无 API key 时）"""
        lines = [f"## {label}\n"]
        
        for i, s in enumerate(signals):
            title = s.get("title", "N/A")
            summary = s.get("summary", "")
            company = s.get("company", "")
            score = s.get("importance_score", 0.0)
            lines.append(f"### {i+1}. {title}")
            lines.append(f"\n{summary[:200]}\n")
            lines.append(f"> 来源: {company} | 影响力: {score:.2f}\n")
        
        return "\n".join(lines)
    
    def _build_heat_data(self, signals: list) -> dict:
        """构建信号热度统计"""
        tags = {}
        companies = {}
        
        for s in signals:
            for tag in s.get("tags", []):
                tags[tag] = tags.get(tag, 0) + 1
            company = s.get("company", "")
            if company:
                companies[company] = companies.get(company, 0) + 1
        
        top_tags = sorted(tags.items(), key=lambda x: -x[1])[:10]
        top_companies = sorted(companies.items(), key=lambda x: -x[1])[:10]
        
        return {
            "total_signals": len(signals),
            "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
            "top_companies": [{"company": c, "count": n} for c, n in top_companies],
        }


# ═══════════════════════════════════════
# CLI / 独立测试
# ═══════════════════════════════════════

def main():
    """CLI 入口 — 独立测试 SmartTextEngine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartText Engine — 文字创作引擎")
    parser.add_argument("--format", default="daily_report", help="内容形态")
    parser.add_argument("--mock", action="store_true", default=True, help="使用 Mock 模式")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="日期")
    parser.add_argument("--list-formats", action="store_true", help="列出所有格式")
    parser.add_argument("--list-clusters", action="store_true", help="列出所有集群")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  SmartText Engine — 文字创作引擎")
    print(f"  API Key{' ✅' if os.environ.get('DEEPSEEK_API_KEY') else ' ❌ 未设置 (Mock 模式)'}")
    print("=" * 60)
    
    engine = SmartTextEngine()
    
    if args.list_formats:
        print("\n  可用内容形态:")
        for fmt in engine.list_formats():
            print(f"    {fmt['id']:20s} → {fmt['name']}")
        return
    
    if args.list_clusters:
        print("\n  可用文字创作集群:")
        for cl in engine.list_clusters():
            prompt = engine.get_prompt_config(cl["id"])
            stages = len(prompt.get("stages", {})) if prompt else 0
            print(f"    {cl['id']:15s} → {cl['name']} ({stages} stages)")
        return
    
    print(f"\n  格式: {args.format}")
    print(f"  日期: {args.date}")
    print(f"  模式: {'Mock' if args.mock else 'Real LLM'}\n")
    
    # 使用内置 Mock Signal Bundle 测试
    bundle = SmartTextEngine.MOCK_SIGNAL_BUNDLE
    result = engine.generate(bundle, args.format, date=args.date, mock=args.mock)
    
    if "error" in result:
        print(f"  ❌ 错误: {result['error']}")
        return
    
    print(f"  生成完成: {len(result['sections'])} 板块")
    print(f"  总词数: {result['meta']['total_words']}")
    print(f"  耗时: {result['meta']['total_latency_ms']}ms\n")
    
    for section in result["sections"]:
        print(f"  [{section['section_id']}] {section['label']}")
        print(f"    集群: {section['cluster']} | 信号: {section['signals_count']} | 词数: {section['word_count']}")
        preview = section['content'][:120].replace('\n', ' ')
        print(f"    预览: {preview}...\n")
    
    # 输出渲染版
    if "rendered" in result:
        print("  " + "-" * 56)
        print(f"  渲染 Markdown ({len(result['rendered'])} chars):")
        print("  " + "-" * 56)
        for line in result['rendered'].split('\n')[:20]:
            print(f"  {line}")
    
    print(f"\n{'=' * 60}")
    print(f"  SmartText Engine 就绪 ✓")
    print(f"  {'=' * 60}")


if __name__ == "__main__":
    main()
