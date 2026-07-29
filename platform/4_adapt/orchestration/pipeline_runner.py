"""
PT-047 Pipeline Runner — 全链路编排入口
从选材 → 编排 → 生成 → 审稿 → 反思 → 输出的完整流水线
用法: python pipeline_runner.py --input <cog_config.json>
"""
from __future__ import annotations
import sys, os, json, argparse, logging, asyncio
from datetime import datetime
from typing import Any, Dict, Union
import inspect

# ── Python path ──────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PT047.Pipeline")


# ── Agent 延迟加载（避免启动时全部下载模型）───────────────
def _load_agents():
    from agents.chief_editor import ChiefEditorAgent
    from agents.orchestration.orchestration import OrchestrationAgent
    from agents.material_scout.material_scout import MaterialScoutAgent
    from agents.generation.controlled_generation import ControlledGenerationAgent
    from agents.review.adversarial_review import AdversarialReviewAgent
    from agents.reflection.reflection import ReflectionAgent
    from agents.output.output_renderer import OutputRendererAgent
    return {
        "chief_editor": ChiefEditorAgent,
        "orchestration": OrchestrationAgent,
        "material_scout": MaterialScoutAgent,
        "controlled_generation": ControlledGenerationAgent,
        "adversarial_review": AdversarialReviewAgent,
        "reflection": ReflectionAgent,
        "output_renderer": OutputRendererAgent,
    }


# ── Pipeline 阶段定义 ──────────────────────────────────
STAGES = [
    ("chief_editor",       "主编协调（上下文快照+路由决策）"),
    ("material_scout",     "选材（意图解析+知识库召回）"),
    ("orchestration",      "编排（COG脚本+三层漏斗）"),
    ("controlled_generation","生成（LLM填槽+四层注入）"),
    ("adversarial_review", "审稿（双模型对抗+合规检查）"),
    ("reflection",         "反思（张力曲线+修订循环）"),
    ("output_renderer",     "输出（格式渲染+持久化）"),
]

STAGE_NAMES = {name for name, _ in STAGES}


# ── Pipeline 执行器 ─────────────────────────────────────
class PipelineRunner:
    """PT-047 全链路执行器。"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agents: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {
            "pipeline_started": datetime.now().isoformat(),
            "stages": [],
        }
        self._agent_classes = None

    def _init_agents(self):
        if self._agent_classes is None:
            logger.info("Loading agents...")
            self._agent_classes = _load_agents()
            logger.info(f"Loaded {len(self._agent_classes)} agents")

    def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        self._init_agents()
        self.context["initial_input"] = initial_input
        result = initial_input

        for stage_name, stage_desc in STAGES:
            logger.info(f"\n{'='*60}\n  Stage: {stage_name} — {stage_desc}\n{'='*60}")
            try:
                result = self._run_stage(stage_name, result)
                self.context["stages"].append({
                    "stage": stage_name,
                    "status": "success",
                    "result_preview": str(result)[:200],
                })
            except Exception as ex:
                logger.error(f"Stage {stage_name} failed: {ex}")
                self.context["stages"].append({
                    "stage": stage_name,
                    "status": "error",
                    "error": str(ex),
                })
                # 决策：继续还是中断
                if not self.config.get("continue_on_error", False):
                    logger.warning("Pipeline aborted due to stage failure.")
                    break

        self.context["pipeline_finished"] = datetime.now().isoformat()
        return {"context": self.context, "final_result": result}

    def _run_stage(self, stage_name: str, input_data: Any) -> Any:
        """执行单个阶段。"""
        agent_cls = self._agent_classes.get(stage_name)
        if agent_cls is None:
            logger.warning(f"No agent for stage: {stage_name}")
            return input_data

        # 实例化 agent（支持多种 __init__ 签名）
        try:
            agent = agent_cls()
        except TypeError:
            try:
                agent = agent_cls(agent_id=stage_name)
            except TypeError:
                try:
                    agent = agent_cls(agent_id=stage_name, config=None)
                except TypeError:
                    # 兜底：不传参数
                    agent = agent_cls(None, None)

        self.agents[stage_name] = agent

        # 适配各 agent 的输入格式
        adapted_input = self._adapt_input(stage_name, input_data)

        # 通用调用约定：优先 execute，其次 handoff，最后 BaseAgent 兜底
        if hasattr(agent, "execute"):
            execute_method = getattr(agent, "execute")
            is_coro = inspect.iscoroutinefunction(execute_method)
            if is_coro:
                # async agent: 在事件循环中执行
                try:
                    loop = asyncio.get_running_loop()
                    # 已在运行循环中，创建 Task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(asyncio.run, execute_method(adapted_input))
                        return result.result()
                except RuntimeError:
                    # 没有运行中的循环
                    return asyncio.run(execute_method(adapted_input))
            else:
                return execute_method(adapted_input)
        elif hasattr(agent, "handoff"):
            return agent.handoff(type("Req", (), {
                "target_agent": stage_name,
                "payload": adapted_input,
                "to_dict": lambda s: {"target_agent": s.target_agent, "payload": s.payload}
            })())
        else:
            logger.warning(f"Agent {stage_name} has no execute/handoff method, using BaseAgent stub")
            return {"status": "ok", "agent": stage_name, "stub": True}

    def _adapt_input(self, stage_name: str, input_data: Any) -> Any:
        """适配各阶段 agent 的输入格式。"""
        # 兼容 Pydantic 模型 → dict
        if hasattr(input_data, "model_dump"):
            input_data = input_data.model_dump()
        elif hasattr(input_data, "dict"):
            input_data = input_data.dict()

        if stage_name == "chief_editor":
            # ChiefEditorAgent 需要 ChiefEditorInput(content=..., metadata=...)
            if isinstance(input_data, dict) and "content" not in input_data:
                return {"content": json.dumps(input_data, ensure_ascii=False), "metadata": input_data}
            return input_data
        elif stage_name == "material_scout":
            # MaterialScoutAgent 需要 MaterialScoutInput(query=..., domain=...)
            from agents.material_scout.material_scout import MaterialScoutInput
            if isinstance(input_data, dict):
                if "query" not in input_data:
                    # 从 chief_editor 输出提取 query
                    content = input_data.get("final_edited_content", json.dumps(input_data, ensure_ascii=False))
                    input_data["query"] = content
                if "domain" not in input_data:
                    input_data["domain"] = input_data.get("metadata", {}).get("domain", "general")
            return MaterialScoutInput(**input_data)
        elif stage_name == "orchestration":
            # OrchestrationAgent 需要 dict
            if not isinstance(input_data, dict):
                return {"raw_input": str(input_data)}
        elif stage_name == "controlled_generation":
            # 需要 COG script
            if isinstance(input_data, dict) and "cog_script" not in input_data:
                input_data["cog_script"] = input_data.get("result", {})
        elif stage_name == "adversarial_review":
            if isinstance(input_data, dict) and "content_text" not in input_data:
                # 从 generation 结果提取文本
                input_data["content_text"] = input_data.get("generated_text",
                    input_data.get("text", json.dumps(input_data, ensure_ascii=False)))
                input_data["content_id"] = input_data.get("content_id", f"content_{stage_name}")
        elif stage_name == "reflection":
            if isinstance(input_data, dict) and "insights" not in input_data:
                input_data["insights"] = input_data.get("review_findings",
                    input_data.get("adversarial_findings", []))
        elif stage_name == "output_renderer":
            # 需要 GeneratedText
            if isinstance(input_data, dict) and "text" not in input_data:
                input_data["text"] = input_data.get("generated_text",
                    input_data.get("refined_content",
                    json.dumps(input_data, ensure_ascii=False)))
        # 其他阶段：直接传递 dict
        return input_data


# ── CLI ─────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="PT-047 Pipeline Runner")
    parser.add_argument("--input", "-i", default="",
                        help="Input JSON file (COG config)")
    parser.add_argument("--output", "-o", default="pipeline_output.json",
                        help="Output JSON file")
    parser.add_argument("--continue", dest="continue_on_err", action="store_true",
                        help="Continue pipeline on stage failure")
    args = parser.parse_args()

    if args.input and os.path.exists(args.input):
        with open(args.input, encoding="utf-8") as f:
            initial_input = json.load(f)
    else:
        # 默认测试输入
        initial_input = {
            "intent": "epic",
            "chapter_title": "乾元元年·蒲州的墨与血",
            "characters": ["颜真卿", "安禄山"],
            "themes": ["忠义", "家国", "书法"],
            "target_length": 2000,
        }
        logger.info("No input file, using default test input")

    runner = PipelineRunner({"continue_on_error": args.continue_on_err})
    result = runner.run(initial_input)

    output_path = args.output
    def _pydantic_dumper(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return str(obj)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=_pydantic_dumper)
    logger.info(f"\nPipeline complete. Output: {output_path}")

    # 打印摘要
    for stage in result["context"]["stages"]:
        status_icon = "OK" if stage["status"] == "success" else "FAIL"
        print(f"  [{status_icon}] {stage['stage']}")

if __name__ == "__main__":
    main()
