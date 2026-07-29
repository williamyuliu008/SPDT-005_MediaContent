"""
DeepProd — 深度生产集群引擎 (CLUSTER-B)
==========================================
DESIGN SOP T2 生成创作型 | 6 Guild | 12 Agent
接收 SR-TEXT-001 TextClassifier 输出
"""

import json, yaml, os, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

BASE = Path(__file__).parent.parent
CONFIG_DIR = BASE / "config"
OUTPUT_DIR = BASE / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
logger = logging.getLogger("deepprod")

class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Artifact:
    """Guild 间传递的产物"""
    artifact_id: str
    guild_from: str
    guild_to: str
    content: dict
    status: str = "pending"
    timestamp: str = ""

@dataclass
class DecisionLog:
    """FR: 所有工具调用记录"""
    agent_id: str
    action: str
    input_summary: str
    output_summary: str
    timestamp: str = ""
    tools_used: list = field(default_factory=list)

class DeepProdEngine:
    """深度生产集群主引擎"""
    
    def __init__(self):
        self.cluster_config = yaml.safe_load(
            open(CONFIG_DIR / "cluster.yaml", 'r', encoding='utf-8'))
        self._artifacts: list[Artifact] = []
        self._decision_log: list[DecisionLog] = []
        self._stage_status: dict = {}
        self._init_stages()
    
    def _init_stages(self):
        for s in self.cluster_config["stages"]:
            self._stage_status[s["id"]] = StageStatus.PENDING.value
    
    def log_decision(self, agent_id: str, action: str, 
                     input_s: str, output_s: str, tools: list = None):
        entry = DecisionLog(
            agent_id=agent_id, action=action,
            input_summary=input_s, output_summary=output_s,
            timestamp=datetime.now().isoformat(),
            tools_used=tools or [],
        )
        self._decision_log.append(entry)
        return entry
    
    def submit_artifact(self, guild_from: str, guild_to: str, 
                        content: dict) -> Artifact:
        artifact = Artifact(
            artifact_id=f"ART-{guild_from}-{guild_to}-{datetime.now().strftime('%H%M%S')}",
            guild_from=guild_from, guild_to=guild_to,
            content=content, status="submitted",
            timestamp=datetime.now().isoformat(),
        )
        self._artifacts.append(artifact)
        self.log_decision(guild_from, "submit_artifact",
                         f"Artifact to {guild_to}", 
                         f"Keys: {list(content.keys())[:5]}")
        return artifact
    
    def run_stage(self, stage_id: str, input_data: dict = None) -> dict:
        """执行单个 Stage"""
        stage = next(s for s in self.cluster_config["stages"] 
                    if s["id"] == stage_id)
        self._stage_status[stage_id] = StageStatus.RUNNING.value
        
        guild = stage["guild"]
        
        # 模拟 Guild 执行
        result = {
            "stage_id": stage_id,
            "guild": guild,
            "status": "completed",
            "output": self._simulate_guild_output(stage_id, guild, input_data),
            "gate": stage["gate"],
            "gate_passed": True,
        }
        
        self._stage_status[stage_id] = StageStatus.COMPLETED.value
        self.log_decision("operator", f"stage_{stage_id}_complete",
                         f"Stage {stage_id} input", 
                         f"Gate {stage['gate']}: PASS")
        
        return result
    
    def _simulate_guild_output(self, stage_id: str, guild: str, 
                               input_data: dict = None) -> dict:
        """模拟 Guild 产出"""
        outputs = {
            "S1_TOPIC": {
                "topic": "中国半导体设备国产化进程深度分析",
                "angle": "技术路线对比 + 政策驱动 + 主要玩家评估",
                "value_score": 8.5,
                "sources": ["SEMI报告", "大基金二期投资清单", "SMIC/华虹年报", "北方华创/中微公司技术路线"],
            },
            "S2_RESEARCH": {
                "data_collected": True,
                "key_findings": [
                    "国产化率从15%→35%，刻蚀/薄膜设备突破最快",
                    "光刻机仍是最大瓶颈，国产化率<5%",
                    "政策驱动：大基金二期+设备采购税收优惠",
                ],
                "models": {"market_size_2026": "$45B", "cagr": "22%"},
            },
            "S3_WRITING": {
                "draft_version": "v1",
                "word_count": 18500,
                "structure": ["执行摘要", "产业链全景", "技术路线对比", "政策环境", "竞争格局", "投资建议"],
            },
            "S4_REVIEW": {
                "factcheck_errors": 0,
                "consistency_score": 0.95,
                "approval": "approved",
            },
            "S5_VISUAL": {
                "charts": ["产业链全景图", "国产化率趋势图", "竞争格局矩阵"],
                "tables": ["主要玩家对比表", "政策时间线"],
            },
            "S6_DELIVER": {
                "final_doc": "中国半导体设备国产化进程深度分析_v1.md",
                "word_count": 18500,
                "delivery_time": datetime.now().isoformat(),
            },
        }
        return outputs.get(stage_id, {"status": "completed"})
    
    def run_full_pipeline(self, input_data: dict = None) -> dict:
        """完整 6 Stage 管道"""
        results = {}
        stage_list = self.cluster_config["stages"]
        for i, stage in enumerate(stage_list):
            sid = stage["id"]
            prev = results[stage_list[i-1]["id"]] if i > 0 else {}
            prev_data = prev.get("output", {}) if prev else input_data
            
            result = self.run_stage(sid, prev_data)
            results[sid] = result
            logger.info(f"{sid}: {result['status']} (gate: {result['gate']})")
        
        return results
    
    def report(self) -> dict:
        return {
            "cluster": self.cluster_config["cluster_id"],
            "stages_completed": sum(
                1 for s in self._stage_status.values() 
                if s == StageStatus.COMPLETED.value
            ),
            "total_stages": len(self._stage_status),
            "artifacts": len(self._artifacts),
            "decision_log_entries": len(self._decision_log),
        }


def main():
    print("=" * 60)
    print("  DeepProd — 深度生产集群 (CLUSTER-B)")
    print("  DESIGN SOP T2 | 6 Guild | 12 Agent")
    print("=" * 60)
    
    engine = DeepProdEngine()
    
    # 模拟接收 TextClassifier 输出
    router_output = {
        "structured_spec": {
            "core_intent": "中国半导体设备国产化进程深度分析",
            "product_type": "分析/报告",
            "target_audience": "投资人群",
            "depth": "深度 (>=5000字)",
            "domain_tags": ["科技", "金融"],
        },
        "configuration": {
            "config_name": "industry_analysis",
            "cluster": "B",
        },
    }
    
    print("\n  Input: TextClassifier → Cluster B")
    print(f"  Topic: {router_output['structured_spec']['core_intent']}")
    
    results = engine.run_full_pipeline(router_output)
    
    print("\n  Pipeline Results:")
    for sid, result in results.items():
        stage = next(s for s in engine.cluster_config["stages"] if s["id"] == sid)
        icon = "[OK]" if result["gate_passed"] else "[FAIL]"
        print(f"    {icon} {sid}: {stage['name']} → {result['gate']}")
    
    report = engine.report()
    print(f"\n  Report: {report}")
    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
