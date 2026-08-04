# -*- coding: utf-8 -*-
"""
checkpoint_runner.py — SPDT-005 Checkpoint 执行层
================================================

功能：
  1. 读取 content_type 的 checkpoint 配置（来自 registry）
  2. 对 M1/M2/M3/M4/M5/M6 实施策略：
     - skip       → 自动通过，记录审计
     - threshold  → 分数阈值检查
     - confirm    → 创建工单，等待人工批准
     - fast_confirm → 值班编辑快速确认
     - chief_signoff → 主编签批
  3. 读取 deliver_checklist.yaml，执行 M6 三项确认
  4. 与 PolicyAuditLogger 集成，闭环所有决策

使用方式：
  # 检查待处理 checkpoint 工单
  runner = CheckpointRunner()
  pending = runner.list_pending()
  print(pending)

  # 执行 M6 交付检查
  runner.run_m6_delivery(pipeline_id="PL_xxx", scorecard={...})

  # 审批工单
  runner.approve_ticket(ticket_id, role="editor")
  runner.reject_ticket(ticket_id, role="chief_editor", reason="...")

  # 每日健康检查
  runner.daily_health_check()
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[4]
CHECKPOINT_DIR = REPO_ROOT / "platform" / "5_deliver" / "checkpoint"
CHECKLIST_PATH = CHECKPOINT_DIR / "deliver_checklist.yaml"
TICKET_DIR = CHECKPOINT_DIR / "tickets"
TICKET_DIR.mkdir(parents=True, exist_ok=True)


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


class TicketStatus(Enum):
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已批准
    REJECTED = "rejected"   # 已拒绝
    EXPIRED = "expired"     # 已过期


@dataclass
class CheckpointTicket:
    """Checkpoint 工单"""
    ticket_id: str
    pipeline_id: str
    content_type: str
    checkpoint_type: str         # "M1" / "M2" / "M3" / "M4" / "M5" / "M6"
    action: str                  # "confirm" / "chief_signoff" / "legal_review"
    status: str = TicketStatus.PENDING.value
    created_at: str = ""
    reviewer_role: str = ""      # "editor" / "chief_editor" / "compliance"
    review_comment: str = ""
    reviewed_at: str = ""
    content_summary: str = ""    # 人工可读的内容摘要
    scorecard_summary: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# CheckpointRunner
# ─────────────────────────────────────────────────────────────────

class CheckpointRunner:
    """
    Checkpoint 执行引擎

    设计原则：
      - checkpoint 策略由 registry 中 human_checkpoints 决定
      - 需要人工的 checkpoint → 创建工单 → 等待批准
      - 每日健康检查 → 自动清理过期工单 + 汇总统计
      - 所有决策写入 policy_audit.jsonl
    """

    # checkpoint_type → 序号映射
    STAGE_TO_M = {
        "ingest": "M1",
        "structure": "M2",
        "render": "M3",
        "adapt": "M4",
        "deliver": "M5",
        "publish": "M6",
    }

    def __init__(self, checklist_path: Optional[Path] = None):
        self.checklist_path = checklist_path or CHECKLIST_PATH
        self.checklist = self._load_checklist()

    def _load_checklist(self) -> dict:
        if not self.checklist_path.exists():
            return {}
        return yaml.safe_load(self.checklist_path.read_text(encoding="utf-8")) or {}

    # ── 策略执行 ──────────────────────────────────────────────

    def evaluate_action(
        self,
        action: str,
        pipeline_id: str,
        content_type: str,
        stage_name: str,
        artifact: dict,
        scorecard: Optional[dict] = None,
    ) -> dict:
        """
        评估 checkpoint action，返回执行结果。

        返回：
          {
            "proceed": bool,       # 是否继续管线
            "status": str,         # "auto_pass" / "ticket_created" / "threshold_fail"
            "ticket_id": str,      # 如果创建了工单
            "message": str,
            "audit_event": dict,    # 用于写入 policy_audit.jsonl
          }
        """
        m_id = self.STAGE_TO_M.get(stage_name, f"M?({stage_name})")
        scorecard = scorecard or {}

        # 解析阈值
        threshold = self._parse_threshold(action)

        if action in ("skip", "SKIP"):
            return {
                "proceed": True,
                "status": "auto_pass",
                "ticket_id": "",
                "message": f"{m_id}: skip，自动通过",
                "audit_event": self._make_audit_event(
                    "checkpoint_pass_auto", pipeline_id, content_type, m_id,
                    "skip", {"stage": stage_name}, gap=False,
                ),
            }

        if threshold is not None:
            total_score = self._get_total_score(scorecard)
            if total_score < threshold:
                return {
                    "proceed": False,
                    "status": "threshold_fail",
                    "ticket_id": "",
                    "message": f"{m_id}: 分数 {total_score} < 阈值 {threshold}，管线失败",
                    "audit_event": self._make_audit_event(
                        "quality_gate_failed", pipeline_id, content_type, m_id,
                        "break",
                        {"total_score": total_score, "threshold": threshold},
                        gap=True, severity="error",
                    ),
                }
            else:
                return {
                    "proceed": True,
                    "status": "threshold_pass",
                    "ticket_id": "",
                    "message": f"{m_id}: 分数 {total_score} >= {threshold}，通过",
                    "audit_event": self._make_audit_event(
                        "quality_gate_passed", pipeline_id, content_type, m_id,
                        "continue",
                        {"total_score": total_score, "threshold": threshold},
                        gap=False,
                    ),
                }

        if action in ("confirm", "fast_confirm", "standard"):
            ticket = self._create_ticket(
                pipeline_id=pipeline_id,
                content_type=content_type,
                checkpoint_type=m_id,
                action=action,
                artifact=artifact,
                scorecard=scorecard,
            )
            return {
                "proceed": False,
                "status": "ticket_created",
                "ticket_id": ticket.ticket_id,
                "message": f"{m_id}: 需要人工确认，工单 {ticket.ticket_id} 已创建",
                "audit_event": self._make_audit_event(
                    "checkpoint_hold", pipeline_id, content_type, m_id,
                    action, {"ticket_id": ticket.ticket_id}, gap=True, severity="warn",
                ),
            }

        if action == "chief_signoff":
            ticket = self._create_ticket(
                pipeline_id=pipeline_id,
                content_type=content_type,
                checkpoint_type=m_id,
                action=action,
                artifact=artifact,
                scorecard=scorecard,
            )
            return {
                "proceed": False,
                "status": "ticket_created",
                "ticket_id": ticket.ticket_id,
                "message": f"{m_id}: 需要主编签批，工单 {ticket.ticket_id} 已创建",
                "audit_event": self._make_audit_event(
                    "checkpoint_hold", pipeline_id, content_type, m_id,
                    action, {"ticket_id": ticket.ticket_id, "require": "chief_editor"},
                    gap=True, severity="warn",
                ),
            }

        # 未知 action → 默认自动通过
        return {
            "proceed": True,
            "status": "auto_pass_default",
            "ticket_id": "",
            "message": f"{m_id}: 未知 action '{action}'，默认通过",
            "audit_event": self._make_audit_event(
                "decision_unmatched", pipeline_id, content_type, m_id,
                action, {"fallback": "auto_pass"}, gap=True, severity="warn",
            ),
        }

    def _parse_threshold(self, action: str) -> Optional[float]:
        """从 action 字符串解析阈值，如 'threshold_70' → 70.0"""
        if not action.startswith("threshold_"):
            return None
        try:
            return float(action.split("_")[1])
        except (IndexError, ValueError):
            return None

    def _get_total_score(self, scorecard: dict) -> float:
        """从 scorecard 中提取总分"""
        if not scorecard:
            return 0.0
        inner = scorecard.get("scorecard", scorecard)
        if isinstance(inner, dict):
            return float(inner.get("total_score", 0))
        return float(inner.get("total_score", scorecard.get("total_score", 0)))

    # ── 工单管理 ────────────────────────────────────────────────

    def _create_ticket(
        self,
        pipeline_id: str,
        content_type: str,
        checkpoint_type: str,
        action: str,
        artifact: dict,
        scorecard: dict,
    ) -> CheckpointTicket:
        ticket_id = f"CHK_{checkpoint_type.replace('M','')}_{uuid.uuid4().hex[:8]}"
        score_summary = {
            "total_score": self._get_total_score(scorecard),
            "passed": self._get_total_score(scorecard) >= 70,
        }

        # 从 artifact 提取内容摘要
        if isinstance(artifact, dict):
            topic = artifact.get("topic", "")
            title = artifact.get("title", topic)
        else:
            title = str(artifact)[:100]

        ticket = CheckpointTicket(
            ticket_id=ticket_id,
            pipeline_id=pipeline_id,
            content_type=content_type,
            checkpoint_type=checkpoint_type,
            action=action,
            status=TicketStatus.PENDING.value,
            created_at=datetime.now(timezone.utc).isoformat(),
            content_summary=title[:80],
            scorecard_summary=score_summary,
        )

        # 持久化工单
        self._save_ticket(ticket)
        return ticket

    def _save_ticket(self, ticket: CheckpointTicket):
        path = TICKET_DIR / f"{ticket.ticket_id}.json"
        path.write_text(
            json.dumps(
                {
                    "ticket_id": ticket.ticket_id,
                    "pipeline_id": ticket.pipeline_id,
                    "content_type": ticket.content_type,
                    "checkpoint_type": ticket.checkpoint_type,
                    "action": ticket.action,
                    "status": ticket.status,
                    "created_at": ticket.created_at,
                    "reviewer_role": ticket.reviewer_role,
                    "review_comment": ticket.review_comment,
                    "reviewed_at": ticket.reviewed_at,
                    "content_summary": ticket.content_summary,
                    "scorecard_summary": ticket.scorecard_summary,
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )

    def load_ticket(self, ticket_id: str) -> Optional[CheckpointTicket]:
        path = TICKET_DIR / f"{ticket_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return CheckpointTicket(**data)

    def list_pending(self) -> list[CheckpointTicket]:
        """列出所有待处理工单"""
        tickets = []
        for f in TICKET_DIR.glob("CHK_*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            t = CheckpointTicket(**data)
            if t.status == TicketStatus.PENDING.value:
                tickets.append(t)
        tickets.sort(key=lambda t: t.created_at)
        return tickets

    def approve_ticket(
        self,
        ticket_id: str,
        reviewer_role: str = "editor",
        comment: str = "",
    ) -> dict:
        """批准工单"""
        ticket = self.load_ticket(ticket_id)
        if not ticket:
            return {"ok": False, "error": f"工单不存在: {ticket_id}"}
        if ticket.status != TicketStatus.PENDING.value:
            return {"ok": False, "error": f"工单状态非 pending: {ticket.status}"}

        ticket.status = TicketStatus.APPROVED.value
        ticket.reviewer_role = reviewer_role
        ticket.review_comment = comment
        ticket.reviewed_at = datetime.now(timezone.utc).isoformat()
        self._save_ticket(ticket)

        self._append_audit_event(self._make_audit_event(
            "checkpoint_pass", ticket.pipeline_id, ticket.content_type,
            ticket.checkpoint_type, "approved",
            {"reviewer_role": reviewer_role, "comment": comment[:100]},
            gap=False,
        ))

        return {"ok": True, "ticket_id": ticket_id, "action": "approved"}

    def reject_ticket(
        self,
        ticket_id: str,
        reviewer_role: str = "chief_editor",
        reason: str = "",
    ) -> dict:
        """拒绝工单"""
        ticket = self.load_ticket(ticket_id)
        if not ticket:
            return {"ok": False, "error": f"工单不存在: {ticket_id}"}

        ticket.status = TicketStatus.REJECTED.value
        ticket.reviewer_role = reviewer_role
        ticket.review_comment = reason
        ticket.reviewed_at = datetime.now(timezone.utc).isoformat()
        self._save_ticket(ticket)

        self._append_audit_event(self._make_audit_event(
            "checkpoint_rejected", ticket.pipeline_id, ticket.content_type,
            ticket.checkpoint_type, "rejected",
            {"reviewer_role": reviewer_role, "reason": reason[:100]},
            gap=False, severity="warn",
        ))

        return {"ok": True, "ticket_id": ticket_id, "action": "rejected", "reason": reason}

    # ── M6 交付检查 ───────────────────────────────────────────

    def run_m6_delivery(
        self,
        pipeline_id: str,
        scorecard: dict,
        content_type: str,
        content_spec: dict,
    ) -> dict:
        """
        执行 M6 交付检查（对应 deliver_checklist.yaml）。

        返回：
          {
            "passed": bool,
            "checklist_results": dict,
            "tickets": list[str],   # 需人工处理的工单 ID
            "message": str,
          }
        """
        total_score = self._get_total_score(scorecard)
        checklist = self.checklist.get("confirmation_items", [])
        media_extra = self.checklist.get("media_extra_checks", [])

        results = {}
        tickets = []
        all_passed = True

        # 基础三项确认
        for item in checklist:
            item_id = item["id"]
            threshold_score = 85 if item_id == "M6_SCORE_THRESHOLD" else 0

            if item_id == "M6_SCORE_THRESHOLD":
                passed = total_score >= threshold_score
                reason = f"总分 {total_score} {'>=' if passed else '<'} {threshold_score}"
            elif item_id == "M6_CONTENT_SPEC":
                # 内容规格匹配检查（基础版：检查 channels 是否非空）
                passed = bool(content_spec.get("channels"))
                reason = f"channels: {content_spec.get('channels', [])}"
            else:
                passed = True  # 其他项暂默认通过
                reason = "自动通过"

            results[item_id] = {"passed": passed, "reason": reason}
            if not passed:
                all_passed = False

        # 媒体额外检查（按类型过滤）
        for item in media_extra:
            apply_to = item.get("apply_to", [])
            if content_type not in apply_to:
                continue
            item_id = item["id"]
            results[item_id] = {"passed": True, "reason": "类型相关，自动通过"}
            # 如需人工检查 → 创建工单
            if item.get("pass_required"):
                ticket = self._create_ticket(
                    pipeline_id=pipeline_id,
                    content_type=content_type,
                    checkpoint_type="M6",
                    action="media_extra",
                    artifact=content_spec,
                    scorecard=scorecard,
                )
                tickets.append(ticket.ticket_id)
                results[item_id]["ticket_id"] = ticket.ticket_id
                all_passed = False

        return {
            "passed": all_passed,
            "checklist_results": results,
            "tickets": tickets,
            "total_score": total_score,
            "message": "M6 交付检查完成" if all_passed else "M6 需人工处理",
        }

    # ── 每日健康检查 ─────────────────────────────────────────

    def daily_health_check(self) -> dict:
        """
        每日健康检查：
          1. 清理过期工单（> 7 天未处理）
          2. 汇总待处理工单
          3. 统计 policy_audit.jsonl 最近的 gap_events
        """
        now = datetime.now(timezone.utc)
        expiry_days = 7
        tickets = self.list_pending()

        stats = {
            "pending_tickets": len(tickets),
            "expired_tickets": 0,
            "by_type": {},
            "oldest_pending": "",
            "gap_events_last_24h": 0,
        }

        # 清理过期 + 统计
        for t in tickets:
            created = datetime.fromisoformat(t.created_at.replace("Z", "+00:00"))
            age_days = (now - created).total_seconds() / 86400
            if age_days > expiry_days:
                t.status = TicketStatus.EXPIRED.value
                self._save_ticket(t)
                stats["expired_tickets"] += 1
                stats["pending_tickets"] -= 1

            key = f"{t.checkpoint_type}:{t.action}"
            stats["by_type"][key] = stats["by_type"].get(key, 0) + 1

        if tickets:
            stats["oldest_pending"] = tickets[0].created_at

        # policy_audit gap 统计（最近 24h）
        audit_path = CHECKPOINT_DIR / "policy_audit.jsonl"
        if audit_path.exists():
            lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
            cutoff = (now - timedelta(hours=24)).isoformat()
            stats["gap_events_last_24h"] = sum(
                1 for line in lines[-200:]  # 只看最近 200 条
                if cutoff <= json.loads(line).get("timestamp", "") <= now.isoformat()
                and json.loads(line).get("gap", False)
            )

        return stats

    # ── 审计工具 ───────────────────────────────────────────────

    def _make_audit_event(
        self,
        event_type: str,
        pipeline_id: str,
        content_type: str,
        stage: str,
        action_taken: str,
        details: dict,
        gap: bool = False,
        severity: str = "info",
    ) -> dict:
        return {
            "event_id": uuid.uuid4().hex[:12],
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline_id": pipeline_id,
            "content_type": content_type,
            "stage": stage,
            "action_taken": action_taken,
            "details": details,
            "matched_rule": stage,
            "gap": gap,
            "severity": severity,
        }

    def _append_audit_event(self, event: dict):
        log_path = CHECKPOINT_DIR / "policy_audit.jsonl"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys as _sys
    _sys.stdout = __import__('io').TextIOWrapper(_sys.stdout.buffer, encoding='utf-8', errors='replace')

    runner = CheckpointRunner()
    health = runner.daily_health_check()
    print("=== CheckpointRunner daily health check ===")
    print(f"  pending_tickets:   {health['pending_tickets']}")
    print(f"  expired_tickets:   {health['expired_tickets']}")
    print(f"  gap_events_24h:     {health['gap_events_last_24h']}")
    print(f"  by_type:           {health['by_type']}")

    pending = runner.list_pending()
    if pending:
        print(f"\n  Pending tickets:")
        for t in pending[:5]:
            print(f"    {t.ticket_id} | {t.checkpoint_type} | {t.content_summary[:40]} | {t.created_at[:10]}")
    else:
        print("\n  [OK] No pending tickets")
