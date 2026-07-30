# -*- coding: utf-8 -*-
"""
pipeline_router.py — SPDT-005 弹性管线路由引擎
================================================

核心功能：
  1. 读取 ContentSpec.content_type
  2. 在 content_type_registry.yaml 中查找对应路由
  3. 按顺序执行 5 阶段管线的模块
  4. 在人类检查点（M1/M2/M4/M6）暂停，等待人工确认
  5. 处理灰区工单

规范参考：
  - governance/SPDT-005_SOP.md
  - platform/kb/content_type_registry.yaml
  - platform/5_deliver/checkpoint/signoff.py

使用方式：
  router = PipelineRouter()
  result = router.run(content_spec)
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]  # SPDT-005_MediaContent/
REGISTRY_PATH = REPO_ROOT / "platform" / "kb" / "content_type_registry.yaml"
SIGNOFF_PATH = REPO_ROOT / "platform" / "5_deliver" / "checkpoint" / "signoff.py"
CHECKPOINT_DIR = REPO_ROOT / "platform" / "5_deliver" / "checkpoint"
PRODUCT_DIR = REPO_ROOT / "platform" / "5_deliver" / "product"

# ─────────────────────────────────────────────────────────────────
# 内容类型 → 模块映射
# ─────────────────────────────────────────────────────────────────
# 格式：content_type → {"ingest": (module_path, class_name), ...}

CONTENT_TYPE_MODULES = {
    "breakdown_news": {
        "ingest":    ("platform.1_ingest.radar.radar_breaking",   "RadarBreaking"),
        "structure": ("platform.2_structure.article.article_breaking", "ArticleBreaking"),
        "render":    ("platform.3_render.engines.text.render_breaking", "RenderBreaking"),
        "adapt":     ("platform.4_adapt.scorecard.scorecard_breaking", "ScorecardBreaking"),
    },
}


# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

class CheckpointAction(Enum):
    SKIP = "skip"
    CONFIRM = "confirm"
    FAST_CONFIRM = "fast_confirm"
    STANDARD = "standard"
    CHIEF_SIGNOFF = "chief_signoff"
    THRESHOLD_70 = "threshold_70"
    THRESHOLD_75 = "threshold_75"
    THRESHOLD_80 = "threshold_80"
    THRESHOLD_85 = "threshold_85"


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    CHECKPOINT = "checkpoint"
    PASS = "pass"
    FAIL = "fail"
    GRAY_ZONE = "gray_zone"
    COMPLETE = "complete"


@dataclass
class ContentSpec:
    """内容规格说明（管线输入）"""
    content_type: str
    title: str = ""
    description: str = ""
    target_audience: str = ""
    channels: list[str] = field(default_factory=list)
    priority: int = 5
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "ContentSpec":
        return cls(
            content_type=data.get("content_type", "article"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            target_audience=data.get("target_audience", ""),
            channels=data.get("channels", []),
            priority=data.get("priority", 5),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict:
        return {
            "content_type": self.content_type,
            "title": self.title,
            "description": self.description,
            "target_audience": self.target_audience,
            "channels": self.channels,
            "priority": self.priority,
            "metadata": self.metadata,
        }


@dataclass
class StageResult:
    """单个阶段执行结果"""
    stage_name: str
    status: PipelineStatus
    artifact: dict = field(default_factory=dict)
    error: str = ""
    duration_seconds: float = 0.0
    checkpoint_result: dict = field(default_factory=dict)


@dataclass
class PipelineContext:
    """
    跨阶段上下文：存储中间 artifact，避免重复查询。

    Stage 3 生成的 article_v2 → 供 Stage 4 评分用
    Stage 4 生成的 scorecard + article_v2 → 供 Stage 5 产品化用
    """
    article_v2: dict = field(default_factory=dict)     # IF-P-3，Stage 3 产出
    scorecard: dict = field(default_factory=dict)     # IF-P-4，Stage 4 产出
    outline: dict = field(default_factory=dict)       # IF-P-2，Stage 2 产出
    brief: dict = field(default_factory=dict)         # IF-P-1，Stage 1 产出


@dataclass
class PipelineResult:
    """整条管线执行结果"""
    pipeline_id: str
    content_spec: ContentSpec
    content_type_label: str
    status: PipelineStatus
    stages: dict[str, StageResult] = field(default_factory=dict)
    scorecard: dict = field(default_factory=dict)
    gray_zone_tickets: list[dict] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    total_duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "content_spec": self.content_spec.to_dict(),
            "content_type_label": self.content_type_label,
            "status": self.status.value,
            "stages": {
                name: {
                    "status": s.status.value,
                    "artifact": s.artifact,
                    "error": s.error,
                    "duration_seconds": s.duration_seconds,
                    "checkpoint_result": s.checkpoint_result,
                }
                for name, s in self.stages.items()
            },
            "scorecard": self.scorecard,
            "gray_zone_tickets": self.gray_zone_tickets,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_seconds": self.total_duration_seconds,
        }


# ─────────────────────────────────────────────────────────────────
# 核心引擎
# ─────────────────────────────────────────────────────────────────

class PipelineRouter:
    """
    SPDT-005 弹性管线路由引擎

    执行流程：
      1. load_registry()       — 加载内容类型注册表
      2. get_route()           — 根据 content_type 查找路由
      3. run()                 — 执行完整管线
      4. _run_stage()          — 执行单个阶段（含 checkpoint）
      5. _run_checkpoint()     — 执行人类检查点
      6. _handle_gray_zone()  — 处理灰区工单
    """

    STAGES = ["ingest", "structure", "render", "adapt", "deliver"]

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self.registry: dict = {}
        self._module_cache: dict = {}
        self._signoff_manager = None
        self._load_registry()

    def _load_registry(self):
        """加载内容类型注册表"""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")
        data = yaml.safe_load(self.registry_path.read_text(encoding="utf-8"))
        self.registry = data

    def _get_module(self, content_type: str, stage_name: str):
        """
        动态加载内容类型对应阶段模块。

        module_path 格式：platform.1_ingest.radar.radar_breaking
        → 转换为文件系统路径：platform/1_ingest/radar/radar_breaking.py

        返回：(module, class_name) 或 None
        """
        cache_key = f"{content_type}:{stage_name}"
        if cache_key in self._module_cache:
            return self._module_cache[cache_key]

        if content_type not in CONTENT_TYPE_MODULES:
            return None

        stage_map = CONTENT_TYPE_MODULES[content_type]
        if stage_name not in stage_map:
            return None

        module_path, cls_name = stage_map[stage_name]
        # platform.1_ingest.radar.radar_breaking → platform/1_ingest/radar/radar_breaking.py
        relative = module_path.replace(".", "/") + ".py"
        file_path = REPO_ROOT / relative

        if not file_path.exists():
            return None

        # 使用 spec_from_file_location 避免命名冲突（platform 是 Python 内置模块）
        spec = importlib.util.spec_from_file_location(module_path, str(file_path))
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_path] = module
        spec.loader.exec_module(module)

        self._module_cache[cache_key] = (module, cls_name)
        return (module, cls_name)

    # ── 路由查找 ──────────────────────────────────────────────

    def get_route(self, content_type: str) -> dict:
        """
        根据 content_type 查找路由配置。

        若未找到，回退到 default_route。
        """
        routes = self.registry.get("content_types", {})
        if content_type in routes:
            return routes[content_type]
        # 回退到默认路由
        return self.registry.get("default_route", {
            "label": "默认路由",
            "description": "未识别的 content_type，使用标准路由",
            "stages": {
                s: {"module": f"platform/NOT_FOUND/{s}", "config": "standard"}
                for s in self.STAGES
            },
            "human_checkpoints": {
                "M1": "confirm", "M2": "confirm",
                "M4": "threshold_80", "M6": "standard"
            },
            "channels": ["web"],
        })

    # ── 主执行 ────────────────────────────────────────────────

    def run(self, content_spec: ContentSpec) -> PipelineResult:
        """
        执行完整管线。

        参数：
          content_spec: ContentSpec 对象或 dict

        返回：
          PipelineResult 对象
        """
        if isinstance(content_spec, dict):
            content_spec = ContentSpec.from_dict(content_spec)

        route = self.get_route(content_spec.content_type)
        pipeline_id = f"PL_{content_spec.content_type}_{uuid.uuid4().hex[:8]}"

        result = PipelineResult(
            pipeline_id=pipeline_id,
            content_spec=content_spec,
            content_type_label=route.get("label", content_spec.content_type),
            status=PipelineStatus.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # 跨阶段上下文：存储中间 artifact
        context = PipelineContext()

        start_time = time.time()
        gray_zone_tickets: list[dict] = []

        for stage_name in self.STAGES:
            stage_config = route.get("stages", {}).get(stage_name, {})
            checkpoint_action = route.get("human_checkpoints", {}).get(
                f"M{self.STAGES.index(stage_name) + 1}", "skip"
            )

            stage_result = self._run_stage(
                pipeline_id=pipeline_id,
                stage_name=stage_name,
                stage_config=stage_config,
                content_spec=content_spec,
                checkpoint_action=checkpoint_action,
                previous_artifact=result.stages.get(
                    self.STAGES[self.STAGES.index(stage_name) - 1]
                ).artifact if self.STAGES.index(stage_name) > 0 else {},
                context=context,
            )

            result.stages[stage_name] = stage_result

            # 处理灰区
            if stage_result.status == PipelineStatus.GRAY_ZONE:
                ticket = self._handle_gray_zone(
                    pipeline_id=pipeline_id,
                    stage_name=stage_name,
                    stage_result=stage_result,
                    gray_zone_rules=route.get("gray_zone_rules", [])
                        + self.registry.get("global_gray_zone_rules", []),
                    content_type=content_spec.content_type,
                )
                gray_zone_tickets.append(ticket)
                result.gray_zone_tickets = gray_zone_tickets

            if stage_result.status == PipelineStatus.FAIL:
                result.status = PipelineStatus.FAIL
                break

            # M4 质量阈值检查（adapt 阶段）
            if stage_name == "adapt":
                # stage_result.artifact["scorecard"] 结构（来自 ScorecardBreaking.run()）：
                #   {"header":{}, "scorecard":{"total_score":77.8,...}, "factual_claims_check":{}, ...}
                # 因此 total_score 路径：artifact["scorecard"]["scorecard"]["total_score"]
                artifact = stage_result.artifact
                result.scorecard = artifact       # 存完整 artifact
                inner_scorecard = artifact.get("scorecard", {})
                total_score = inner_scorecard.get("scorecard", {}).get("total_score", 0)
                threshold = self._parse_threshold(checkpoint_action)
                if total_score < threshold:
                    result.status = PipelineStatus.FAIL
                    break

        result.total_duration_seconds = time.time() - start_time
        result.completed_at = datetime.now(timezone.utc).isoformat()

        if result.status not in (PipelineStatus.FAIL, PipelineStatus.GRAY_ZONE):
            result.status = PipelineStatus.COMPLETE

        # 保存结果
        self._save_result(result)
        return result

    # ── 阶段执行 ──────────────────────────────────────────────

    def _run_stage(
        self,
        pipeline_id: str,
        stage_name: str,
        stage_config: dict,
        content_spec: ContentSpec,
        checkpoint_action: str,
        previous_artifact: dict,
        context: PipelineContext,
    ) -> StageResult:
        """
        执行单个管线阶段。

        流程：
          1. 加载模块
          2. 执行模块逻辑
          3. 人类 checkpoint（如果需要）
          4. 返回结果
        """
        start = time.time()
        status = PipelineStatus.PASS
        artifact: dict = {}
        error = ""
        checkpoint_result: dict = {}

        try:
            # ── 阶段 1: ingest ─────────────────────────────────
            if stage_name == "ingest":
                artifact = self._run_ingest(stage_config, content_spec, context)

            # ── 阶段 2: structure ──────────────────────────────
            elif stage_name == "structure":
                artifact = self._run_structure(stage_config, content_spec, previous_artifact, context)

            # ── 阶段 3: render ─────────────────────────────────
            elif stage_name == "render":
                artifact = self._run_render(stage_config, content_spec, previous_artifact, context)

            # ── 阶段 4: adapt ─────────────────────────────────
            elif stage_name == "adapt":
                artifact = self._run_adapt(stage_config, content_spec, previous_artifact, context)

            # ── 阶段 5: deliver ────────────────────────────────
            elif stage_name == "deliver":
                artifact = self._run_deliver(stage_config, content_spec, context)

            # ── checkpoint 检查 ───────────────────────────────
            checkpoint_result = self._run_checkpoint(
                action=checkpoint_action,
                stage_name=stage_name,
                artifact=artifact,
                content_spec=content_spec,
            )

            if checkpoint_result.get("status") == "hold":
                status = PipelineStatus.CHECKPOINT

        except Exception as e:
            status = PipelineStatus.FAIL
            error = str(e)

        return StageResult(
            stage_name=stage_name,
            status=status,
            artifact=artifact,
            error=error,
            duration_seconds=time.time() - start,
            checkpoint_result=checkpoint_result,
        )

    # ── 各阶段执行器 ──────────────────────────────────────────

    def _run_ingest(self, config: dict, content_spec: ContentSpec, context: PipelineContext) -> dict:
        """阶段 1：情报摄取（IF-P-1 → IntelligenceBrief）"""
        module_info = self._get_module(content_spec.content_type, "ingest")
        if module_info:
            module, cls_name = module_info
            # 动态构造 Request 并调用
            req = module.RadarBreakingRequest(
                topic=content_spec.title or "突发新闻",
                max_signals=5,
            )
            result = module.RadarBreaking().run(req)
            context.brief = result.brief
            return result.brief

        # fallback：骨架数据
        artifact = {
            "status": "ingested",
            "sources": [{"type": "radar", "config": config.get("config"), "count": 0}],
            "raw_data": [],
            "content_spec": content_spec.to_dict(),
        }
        context.brief = artifact
        return artifact

    def _run_structure(self, config: dict, content_spec: ContentSpec, prev: dict, context: PipelineContext) -> dict:
        """阶段 2：结构化（IF-P-2 → ArticleOutline）"""
        brief = prev  # prev = IntelligenceBrief
        module_info = self._get_module(content_spec.content_type, "structure")
        if module_info:
            module, cls_name = module_info
            result = getattr(module, cls_name)().run(brief)
            context.outline = result.outline
            return result.outline

        artifact = {
            "status": "structured",
            "structure_type": config.get("config"),
            "content_spec": content_spec.to_dict(),
            "outline": {},
            "knowledge_points": [],
        }
        context.outline = artifact
        return artifact

    def _run_render(self, config: dict, content_spec: ContentSpec, prev: dict, context: PipelineContext) -> dict:
        """阶段 3：内容生成（IF-P-3 → Article_v2）"""
        outline = prev  # prev = ArticleOutline
        module_info = self._get_module(content_spec.content_type, "render")
        if module_info:
            module, cls_name = module_info
            result = getattr(module, cls_name)().run(outline)
            context.article_v2 = result.article
            return result.article

        artifact = {
            "status": "rendered",
            "engine": config.get("config"),
            "draft_content": "",
            "word_count": 0,
        }
        context.article_v2 = artifact
        return artifact

    def _run_adapt(self, config: dict, content_spec: ContentSpec, prev: dict, context: PipelineContext) -> dict:
        """阶段 4：质量适配（IF-P-4 → QualityScorecard）"""
        article = prev  # prev = Article_v2
        module_info = self._get_module(content_spec.content_type, "adapt")
        if module_info:
            module, cls_name = module_info
            result = getattr(module, cls_name)().run(article)
            artifact = {
                "status": "adapted",
                "scorecard": result.scorecard,
                "passed": result.passed,
                "action": result.action,
                "gray_zones": result.gray_zones,
            }
            context.scorecard = result.scorecard
            return artifact

        scorecard_weights = self.registry.get("scorecard_weights", {}).get(
            content_spec.content_type,
            self.registry.get("scorecard_weights", {}).get("deep_industry_report", {})
        )
        artifact = {
            "status": "adapted",
            "scorecard": {
                "total_score": 0,
                "readability": 0,
                "factual": 0,
                "source": 0,
                "depth": 0,
                "timeliness": 0,
                "weights": scorecard_weights,
            }
        }
        context.scorecard = artifact["scorecard"]
        return artifact

    def _run_deliver(self, config: dict, content_spec: ContentSpec, context: PipelineContext) -> dict:
        """
        阶段 5：触达交付（IF-P-5 → ContentProduct）

        流程：
          1. 提取 article_v2（来自 context.article_v2）
          2. 提取 scorecard（来自 context.scorecard）
          3. 从注册表读取 pipeline_dimensions（accuracy / literary / professional_depth）
          4. 调用 MetadataGenerator 生成元数据（IF-P-5.metadata）
          5. 调用 ProductFormatter 生成排版格式（IF-P-5.formatting）
          6. 为每个目标渠道构建 ChannelPackage
          7. 输出完整 ContentProduct
        """
        article_v2 = context.article_v2
        scorecard = context.scorecard

        # 获取内容类型维度配置
        ct_config = self.registry.get("content_types", {}).get(content_spec.content_type, {})
        dims = ct_config.get("pipeline_dimensions", {})
        accuracy = dims.get("accuracy", 3)
        literary = dims.get("literary", 2)
        professional_depth = dims.get("professional_depth", 3)

        # 默认渠道
        channels = content_spec.channels or ct_config.get("channels", ["web"])

        # ── 1. 元数据生成 ──────────────────────────────────────
        mg_spec = importlib.util.spec_from_file_location(
            "metadata_generator",
            str(PRODUCT_DIR / "metadata_generator.py"),
        )
        mg_module = importlib.util.module_from_spec(mg_spec)
        sys.modules["metadata_generator"] = mg_module
        mg_spec.loader.exec_module(mg_module)

        mg_req = mg_module.MetadataRequest(
            article_v2=article_v2,
            content_type=content_spec.content_type,
            accuracy=accuracy,
            professional_depth=professional_depth,
            channels=channels,
            author_name="AI 媒体编辑",
            author_bio="由 SPDT-005 自动化管线生成",
        )
        metadata_result = mg_module.MetadataGenerator().generate(mg_req)

        # ── 2. 排版格式化 ─────────────────────────────────────
        pf_spec = importlib.util.spec_from_file_location(
            "product_formatter",
            str(PRODUCT_DIR / "product_formatter.py"),
        )
        pf_module = importlib.util.module_from_spec(pf_spec)
        sys.modules["product_formatter"] = pf_module
        pf_spec.loader.exec_module(pf_module)

        pf_req = pf_module.FormattingRequest(
            article_v2=article_v2,
            content_type=content_spec.content_type,
            literary=literary,
            professional_depth=professional_depth,
            target_channel="web",  # 主渠道先渲染，后续按需扩展
        )
        formatting_result = pf_module.ProductFormatter().format(pf_req)

        # ── 3. 渠道适配 ────────────────────────────────────────
        ca_spec = importlib.util.spec_from_file_location(
            "channel_adapter",
            str(PRODUCT_DIR / "channel_adapter.py"),
        )
        ca_module = importlib.util.module_from_spec(ca_spec)
        sys.modules["channel_adapter"] = ca_module
        ca_spec.loader.exec_module(ca_module)

        ca_req = ca_module.ChannelAdapterRequest(
            article_v2=article_v2,
            formatting=formatting_result.__dict__,
            metadata=metadata_result.__dict__,
            content_type=content_spec.content_type,
            target_channels=channels,
            literary=literary,
        )
        channel_packages_dict = ca_module.ChannelAdapter().adapt(ca_req)
        # adapt() returns dict[str, ChannelPackage] — convert to dict of dicts
        channel_packages = {
            ch: pkg.__dict__ for ch, pkg in channel_packages_dict.items()
        }

        # ── 4. 组装 ContentProduct（IF-P-5）──────────────────
        content_product = {
            "content_id": f"CP_{content_spec.content_type}_{uuid.uuid4().hex[:8]}",
            "article": article_v2,
            "metadata": metadata_result.__dict__,
            "formatting": formatting_result.__dict__,
            "channel_packages": channel_packages,
            "scorecard_summary": {
                "total_score": scorecard.get("total_score", 0),
                "passed": scorecard.get("total_score", 0) >= 70,
            },
            "published_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_id": "",  # 由调用方填充
        }

        return content_product

    # ── 人类检查点 ────────────────────────────────────────────

    def _run_checkpoint(
        self,
        action: str,
        stage_name: str,
        artifact: dict,
        content_spec: ContentSpec,
    ) -> dict:
        """
        执行人类检查点。

        checkpoint_action 映射：
          skip          → 直接通过
          confirm       → 人工确认（创建工单，等待批准）
          fast_confirm  → 值班编辑快速确认
          standard      → 标准确认流程
          chief_signoff → 主编签批
          threshold_N   → 阈值检查（仅 M4）
        """
        if action in ("skip", "SKIP"):
            return {"status": "pass", "action": action, "reviewer": "auto"}

        if action.startswith("threshold_"):
            threshold = int(action.split("_")[1])
            # artifact["scorecard"]["scorecard"]["total_score"]（ScorecardBreaking.run() 返回嵌套结构）
            score = artifact.get("scorecard", {}).get("scorecard", {}).get("total_score", 0)
            if score >= threshold:
                return {"status": "pass", "action": action, "threshold": threshold, "score": score}
            else:
                return {
                    "status": "fail",
                    "action": action,
                    "threshold": threshold,
                    "score": score,
                    "message": f"质量评分 {score} 低于阈值 {threshold}，需修改后重新提交"
                }

        # 需要人工确认
        if action in ("confirm", "fast_confirm", "standard", "chief_signoff"):
            ticket_id = f"CHK_{stage_name.upper()}_{uuid.uuid4().hex[:8]}"
            checkpoint_ticket = {
                "ticket_id": ticket_id,
                "stage": stage_name,
                "action": action,
                "content_type": content_spec.content_type,
                "content_spec": content_spec.to_dict(),
                "artifact_preview": self._summarize_artifact(artifact, stage_name),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending",
                "reviewer": self._reviewer_for_action(action),
            }
            self._save_checkpoint_ticket(checkpoint_ticket)
            return {
                "status": "hold",
                "action": action,
                "ticket_id": ticket_id,
                "message": f"检查点暂停：等待 {self._reviewer_for_action(action)} 确认"
            }

        return {"status": "pass", "action": action}

    def _reviewer_for_action(self, action: str) -> str:
        """根据 action 返回预期审核人"""
        mapping = {
            "skip": "auto",
            "confirm": "editor",
            "fast_confirm": "duty_editor",
            "standard": "editor",
            "chief_signoff": "chief_editor",
        }
        return mapping.get(action, "editor")

    def _parse_threshold(self, action: str) -> float:
        """从 action 中提取阈值"""
        if action.startswith("threshold_"):
            try:
                return float(action.split("_")[1])
            except (IndexError, ValueError):
                return 80.0
        return 80.0

    # ── 灰区处理 ─────────────────────────────────────────────

    def _handle_gray_zone(
        self,
        pipeline_id: str,
        stage_name: str,
        stage_result: StageResult,
        gray_zone_rules: list[dict],
        content_type: str,
    ) -> dict:
        """
        处理灰区工单。

        流程：
          1. 根据规则判断触发原因
          2. 创建灰区工单（调用 signoff.py）
          3. 暂停管线，等待人工处理
        """
        # 动态导入 signoff（避免循环依赖）
        signoff = self._load_signoff()

        ticket = signoff.SignoffManager(ticket_dir=CHECKPOINT_DIR / "tickets").create_ticket(
            content_id=pipeline_id,
            content_type=content_type,
            gray_zone_reasons=[
                f"{stage_name}: {stage_result.error or '灰区触发'}"
            ],
            checklist_results={"stage": stage_name, "status": "gray_zone"},
            scorecard=stage_result.artifact.get("scorecard", {}),
        )

        return ticket.to_dict()

    def _load_signoff(self):
        """动态加载 signoff 模块"""
        if not self._signoff_manager:
            spec = importlib.util.spec_from_file_location("signoff", SIGNOFF_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._signoff_manager = module
        return self._signoff_manager

    # ── 辅助 ─────────────────────────────────────────────────

    def _summarize_artifact(self, artifact: dict, stage_name: str) -> dict:
        """提取 artifact 的摘要（用于 checkpoint 工单展示）"""
        if stage_name == "ingest":
            return {"source_count": len(artifact.get("sources", []))}
        elif stage_name == "structure":
            return {
                "structure_type": artifact.get("structure_type"),
                "knowledge_points": len(artifact.get("knowledge_points", [])),
            }
        elif stage_name == "render":
            return {
                "word_count": artifact.get("word_count", 0),
                "engine": artifact.get("engine"),
            }
        elif stage_name == "adapt":
            scorecard = artifact.get("scorecard", {})
            return {
                "total_score": scorecard.get("total_score", 0),
                "breakdown": {k: v for k, v in scorecard.items() if k != "weights"},
            }
        elif stage_name == "deliver":
            return {
                "channels": artifact.get("channels", []),
                "status": artifact.get("status"),
            }
        return artifact

    def _save_result(self, result: PipelineResult):
        """保存管线执行结果"""
        out_dir = REPO_ROOT / "platform" / "5_deliver" / "checkpoint" / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{result.pipeline_id}.json"
        path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_checkpoint_ticket(self, ticket: dict):
        """保存 checkpoint 工单"""
        out_dir = CHECKPOINT_DIR / "checkpoints"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{ticket['ticket_id']}.json"
        path.write_text(json.dumps(ticket, ensure_ascii=False, indent=2), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="SPDT-005 弹性管线路由引擎")
    parser.add_argument("--content-type", default="deep_industry_report", help="内容类型")
    parser.add_argument("--title", default="测试稿件", help="标题")
    parser.add_argument("--dry-run", action="store_true", help="仅显示路由，不执行")
    args = parser.parse_args()

    router = PipelineRouter()

    # 显示路由
    route = router.get_route(args.content_type)
    print(f"Content Type: {args.content_type}")
    print(f"Label: {route.get('label')}")
    print(f"Priority: {route.get('priority')}")
    print(f"SLA: {route.get('sla_hours', route.get('sla_minutes'))} {'h' if 'sla_hours' in route else 'min'}")
    print(f"Channels: {route.get('channels')}")
    print(f"Human Checkpoints: {route.get('human_checkpoints')}")
    print(f"Stages: {list(route.get('stages', {}).keys())}")

    if not args.dry_run:
        print("\n执行管线...")
        spec = ContentSpec(
            content_type=args.content_type,
            title=args.title,
            channels=route.get("channels", ["web"]),
        )
        result = router.run(spec)
        print(f"\n状态: {result.status.value}")
        print(f"总耗时: {result.total_duration_seconds:.1f}s")
        if result.scorecard:
            print(f"质量评分: {result.scorecard.get('total_score')}")


if __name__ == "__main__":
    main()
