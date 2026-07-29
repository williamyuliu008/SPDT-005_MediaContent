# -*- coding: utf-8 -*-
"""
signoff.py — M6 人类签批工作流
==========================================
SOP v4.0 M6 人类检查点 · SPDT-005 媒体领域实现

功能：
  1. 从 4_adapt 质量记分卡接收交付请求
  2. 生成灰区工单（Gray Zone Ticket）
  3. 管理签批流程（APPROVED / REJECTED / MODIFIED）
  4. 触发 autopublish 发布或回退

规范参考：
  - 内容制造管线执行规范 v1.0 §2.5
  - quality_gate_schema.json（gray_zone_ticket 格式）
  - deliver_checklist.yaml（M6 检查清单）

使用方式：
  signoff = SignoffManager()
  ticket = signoff.create_ticket(content_id, gray_zone_reasons)
  signoff.submit_for_review(ticket)
  result = signoff.get_result(ticket_id)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────

class SignoffResult(Enum):
    APPROVED = "APPROVED"       # 通过，直接发布
    REJECTED = "REJECTED"       # 拒绝，退回 2_structure
    MODIFIED = "MODIFIED"       # 修订后重新提交
    PENDING = "PENDING"         # 待审核


class SignoffRole(Enum):
    EDITOR = "editor"
    CHIEF_EDITOR = "chief_editor"
    COMPLIANCE = "compliance"


@dataclass
class GrayZoneTicket:
    """灰区工单（M6 人类检查点）"""
    ticket_id: str
    content_id: str
    content_type: str                    # article_v2 content_type
    gray_zone_reasons: list[str]         # 灰区触发原因
    checklist_results: dict              # M6 三项确认结果
    scorecard: dict                     # 质量记分卡结果
    created_at: str
    submitted_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    result: str = "PENDING"
    notes: str = ""
    escalation_level: int = 0           # 0=编辑，1=主编，2=主编+合规

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "gray_zone_reasons": self.gray_zone_reasons,
            "checklist_results": self.checklist_results,
            "scorecard": self.scorecard,
            "created_at": self.created_at,
            "submitted_at": self.submitted_at,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "result": self.result,
            "notes": self.notes,
            "escalation_level": self.escalation_level,
        }


@dataclass
class DeliveryPackage:
    """交付包（通过所有检查，准备发布）"""
    package_id: str
    content_id: str
    article_path: Path                  # article_v2 JSON 路径
    content_type: str
    target_channels: list[str]           # 发布渠道列表
    signoff_ticket: Optional[GrayZoneTicket]
    approved_at: str
    metadata: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# 签批管理器
# ─────────────────────────────────────────────────────────────────

class SignoffManager:
    """
    M6 人类签批管理器

    签批流程：
      1. create_ticket()     — 灰区触发时创建工单
      2. submit_for_review() — 提交人工审核
      3. approve() / reject() / request_modification() — 审核动作
      4. get_result()        — 查询审核结果
      5. trigger_publish()  — 触发 autopublish 发布
    """

    def __init__(self, ticket_dir: Optional[Path] = None):
        self.ticket_dir = ticket_dir or Path("D:/2_products/media/SPDT-005_MediaContent/platform/5_deliver/checkpoint/tickets")
        self.ticket_dir.mkdir(parents=True, exist_ok=True)
        self._tickets: dict[str, GrayZoneTicket] = {}
        self._load_existing_tickets()

    # ── 核心 API ────────────────────────────────────────────────

    def create_ticket(
        self,
        content_id: str,
        content_type: str,
        gray_zone_reasons: list[str],
        checklist_results: dict,
        scorecard: dict,
    ) -> GrayZoneTicket:
        """
        创建灰区工单。

        调用时机：
          - 4_adapt 质量记分卡发现灰区触发时
          - 任意 G-SOURCE / G-TIMELINESS / G-FACTUAL 灰区时
        """
        ticket_id = f"GRAY_{content_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        ticket = GrayZoneTicket(
            ticket_id=ticket_id,
            content_id=content_id,
            content_type=content_type,
            gray_zone_reasons=gray_zone_reasons,
            checklist_results=checklist_results,
            scorecard=scorecard,
            created_at=datetime.now(timezone.utc).isoformat(),
            escalation_level=self._compute_escalation(content_type, gray_zone_reasons),
        )
        self._tickets[ticket_id] = ticket
        self._save_ticket(ticket)
        return ticket

    def submit_for_review(self, ticket_id: str) -> GrayZoneTicket:
        """提交工单供人工审核"""
        ticket = self._get_ticket(ticket_id)
        ticket.submitted_at = datetime.now(timezone.utc).isoformat()
        self._save_ticket(ticket)
        return ticket

    def approve(
        self,
        ticket_id: str,
        reviewer: str,
        notes: str = ""
    ) -> GrayZoneTicket:
        """人工审核：批准"""
        ticket = self._get_ticket(ticket_id)
        ticket.result = SignoffResult.APPROVED.value
        ticket.reviewed_by = reviewer
        ticket.reviewed_at = datetime.now(timezone.utc).isoformat()
        ticket.notes = notes
        self._save_ticket(ticket)
        return ticket

    def reject(
        self,
        ticket_id: str,
        reviewer: str,
        reason: str
    ) -> GrayZoneTicket:
        """人工审核：拒绝（退回 2_structure）"""
        ticket = self._get_ticket(ticket_id)
        ticket.result = SignoffResult.REJECTED.value
        ticket.reviewed_by = reviewer
        ticket.reviewed_at = datetime.now(timezone.utc).isoformat()
        ticket.notes = reason
        self._save_ticket(ticket)
        return ticket

    def request_modification(
        self,
        ticket_id: str,
        reviewer: str,
        modification_notes: str
    ) -> GrayZoneTicket:
        """人工审核：要求修改"""
        ticket = self._get_ticket(ticket_id)
        ticket.result = SignoffResult.MODIFIED.value
        ticket.reviewed_by = reviewer
        ticket.reviewed_at = datetime.now(timezone.utc).isoformat()
        ticket.notes = modification_notes
        self._save_ticket(ticket)
        return ticket

    def get_result(self, ticket_id: str) -> GrayZoneTicket:
        """查询工单审核结果"""
        return self._get_ticket(ticket_id)

    def trigger_publish(
        self,
        package: DeliveryPackage,
        autopublish_config: Optional[dict] = None
    ) -> dict:
        """
        触发 autopublish 发布。

        调用条件：
          - signoff_ticket.result == APPROVED
          - checklist_results 全部 PASS

        返回：
          autopublish 任务状态
        """
        ticket = package.signoff_ticket
        if ticket and ticket.result != SignoffResult.APPROVED.value:
            raise ValueError(f"Cannot publish: ticket {ticket.ticket_id} not approved (result={ticket.result})")

        # 构建 autopublish 任务
        publish_task = {
            "task_id": f"PUBLISH_{package.package_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content_id": package.content_id,
            "article_path": str(package.article_path),
            "channels": package.target_channels,
            "approved_at": package.approved_at,
            "ticket_id": ticket.ticket_id if ticket else None,
            "config": autopublish_config or {},
        }

        return {
            "status": "QUEUED",
            "task": publish_task,
            "message": f"发布任务已排队：{publish_task['task_id']}，目标渠道：{package.target_channels}"
        }

    # ── 辅助方法 ────────────────────────────────────────────────

    def _compute_escalation(self, content_type: str, reasons: list[str]) -> int:
        """根据内容类型和原因计算升级级别"""
        # 涉及敏感话题 → 强制升级
        sensitive_keywords = ["政治", "领导人", "领土", "主权", "宗教"]
        for reason in reasons:
            for kw in sensitive_keywords:
                if kw in reason:
                    return 2

        # 深度报告/评论 → 主编审核
        if content_type in ("deep_industry_report", "oped_argument"):
            return 1

        # 快讯/科普 → 普通编辑
        return 0

    def _get_ticket(self, ticket_id: str) -> GrayZoneTicket:
        if ticket_id not in self._tickets:
            path = self.ticket_dir / f"{ticket_id}.json"
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                self._tickets[ticket_id] = GrayZoneTicket(**data)
            else:
                raise ValueError(f"Ticket not found: {ticket_id}")
        return self._tickets[ticket_id]

    def _save_ticket(self, ticket: GrayZoneTicket):
        path = self.ticket_dir / f"{ticket.ticket_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ticket.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_existing_tickets(self):
        """加载已有的工单"""
        for path in self.ticket_dir.glob("GRAY_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._tickets[data["ticket_id"]] = GrayZoneTicket(**data)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────
# 便捷入口
# ─────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="M6 签批工作流")
    parser.add_argument("action", choices=["create", "submit", "approve", "reject", "result", "publish"])
    parser.add_argument("--ticket-id", help="工单ID")
    parser.add_argument("--content-id", help="内容ID")
    parser.add_argument("--content-type", help="内容类型")
    parser.add_argument("--reviewer", help="审核人")
    parser.add_argument("--notes", help="审核备注")
    args = parser.parse_args()

    manager = SignoffManager()

    if args.action == "create":
        ticket = manager.create_ticket(
            content_id=args.content_id or "ARTICLE_001",
            content_type=args.content_type or "deep_industry_report",
            gray_zone_reasons=["部分引用来源为 C 级"],
            checklist_results={"M6_CONTENT_SPEC": "PASS", "M6_GENRE_GAPS": "PASS"},
            scorecard={"total_score": 82, "G-SOURCE": "review_required"},
        )
        print(f"Created: {ticket.ticket_id}")

    elif args.action == "approve":
        ticket = manager.approve(args.ticket_id, args.reviewer or "EDITOR", args.notes or "")
        print(f"Approved: {ticket.ticket_id} → {ticket.result}")

    elif args.action == "reject":
        ticket = manager.reject(args.ticket_id, args.reviewer or "EDITOR", args.notes or "内容不合格")
        print(f"Rejected: {ticket.ticket_id} → {ticket.result}")

    elif args.action == "result":
        ticket = manager.get_result(args.ticket_id)
        print(json.dumps(ticket.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
