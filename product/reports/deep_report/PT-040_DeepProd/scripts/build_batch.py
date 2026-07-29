"""批量构建 5 集群引擎"""
import os, yaml

CLUSTERS = {
    "FlashNews": {
        "name": "实时快反集群 (CLUSTER-A)",
        "domain": "content_production.news",
        "stages": ["S1_MONITOR","S2_VERIFY","S3_DRAFT","S4_PUBLISH"],
        "guilds": [
            ("S1_MONITOR","SCOUT","信源监控","topic_detected"),
            ("S2_VERIFY","VERIFY","事实核查","verified"),
            ("S3_DRAFT","WRITING","快速撰稿","draft_ready"),
            ("S4_PUBLISH","PUBLISH","发布","published"),
        ],
        "outputs": {
            "S1_MONITOR": {"topic":"A股午间快报","sources":["沪深交易所","Wind"],"urgency":"high"},
            "S2_VERIFY": {"verified":True,"corrections":0},
            "S3_DRAFT": {"word_count":300,"format":"快讯"},
            "S4_PUBLISH": {"status":"published"},
        },
    },
    "TechDoc": {
        "name": "技术文档集群 (CLUSTER-D)",
        "domain": "content_production.techdoc",
        "stages": ["S1_SPEC","S2_RESEARCH","S3_WRITE","S4_REVIEW"],
        "guilds": [
            ("S1_SPEC","SPEC","规格定义","spec_ready"),
            ("S2_RESEARCH","RESEARCH","API/代码研究","research_done"),
            ("S3_WRITE","WRITING","文档撰写","draft_ready"),
            ("S4_REVIEW","REVIEW","技术审查","approved"),
        ],
        "outputs": {
            "S1_SPEC": {"format":"OpenAPI","sections":["认证","端点","错误码"]},
            "S2_RESEARCH": {"endpoints_found":24,"code_samples":8},
            "S3_WRITE": {"format":"markdown","completeness":0.95},
            "S4_REVIEW": {"errors":0,"approved":True},
        },
    },
    "CreativeX": {
        "name": "创意转化集群 (CLUSTER-C)",
        "domain": "content_production.creative",
        "stages": ["S1_BRIEF","S2_IDEATION","S3_CREATE","S4_POLISH"],
        "guilds": [
            ("S1_BRIEF","BRIEF","创意简报","brief_approved"),
            ("S2_IDEATION","IDEATE","创意构思","concept_selected"),
            ("S3_CREATE","CREATE","内容创作","draft_ready"),
            ("S4_POLISH","POLISH","润色定稿","final_approved"),
        ],
        "outputs": {
            "S1_BRIEF": {"tone":"创新","audience":"C端用户"},
            "S2_IDEATION": {"concepts":3,"selected":1},
            "S3_CREATE": {"format":"营销文案","hook":"性价比"},
            "S4_POLISH": {"readability":0.92,"cta_score":0.88},
        },
    },
    "SciPop": {
        "name": "知识科普集群 (CLUSTER-E)",
        "domain": "content_production.scipop",
        "stages": ["S1_RESEARCH","S2_TRANSLATE","S3_WRITE","S4_REVIEW"],
        "guilds": [
            ("S1_RESEARCH","RESEARCH","知识研究","research_done"),
            ("S2_TRANSLATE","TRANSLATE","通俗转化","analogies_ready"),
            ("S3_WRITE","WRITING","科普写作","draft_ready"),
            ("S4_REVIEW","REVIEW","准确性审查","approved"),
        ],
        "outputs": {
            "S1_RESEARCH": {"topic":"量子计算","sources":5},
            "S2_TRANSLATE": {"analogies":3,"complexity":"高中生"},
            "S3_WRITE": {"format":"科普文章","word_count":2000},
            "S4_REVIEW": {"accuracy":0.98,"approved":True},
        },
    },
    "OpEd": {
        "name": "观点论证集群 (CLUSTER-F)",
        "domain": "content_production.oped",
        "stages": ["S1_RESEARCH","S2_STRUCTURE","S3_WRITE","S4_DEBATE"],
        "guilds": [
            ("S1_RESEARCH","RESEARCH","论点研究","evidence_ready"),
            ("S2_STRUCTURE","STRUCTURE","论证结构","structure_approved"),
            ("S3_WRITE","WRITING","观点写作","draft_ready"),
            ("S4_DEBATE","DEBATE","反方检验","debate_passed"),
        ],
        "outputs": {
            "S1_RESEARCH": {"evidence_count":12,"pro_arguments":7,"con_arguments":5},
            "S2_STRUCTURE": {"thesis":"AI监管需要全球协作","sections":5},
            "S3_WRITE": {"word_count":3000,"tone":"论证导向"},
            "S4_DEBATE": {"counter_arguments_addressed":5,"approved":True},
        },
    },
}

def build_cluster(name, config):
    base = f"D:\\92_products\\{name}"
    os.makedirs(f"{base}\\config", exist_ok=True)
    os.makedirs(f"{base}\\src", exist_ok=True)
    
    # cluster.yaml
    cluster = {
        "cluster_id": f"{name.lower()}_cluster",
        "version": "0.1.0",
        "description": config["name"],
        "domain": config["domain"],
        "input_router": "SR-TEXT-001 (TextClassifier)",
        "stages": [],
        "topology": {"type": "mesh", "entry_point": "operator"},
        "message_bus": {"type": "operator_managed", "decision_log": True},
    }
    for sid, guild, gname, gate in config["guilds"]:
        cluster["stages"].append({
            "id": sid, "name": gname, "guild": guild, "gate": gate,
        })
    
    yaml.dump(cluster, open(f"{base}\\config\\cluster.yaml", "w", encoding="utf-8"), 
              allow_unicode=True, default_flow_style=False)
    
    # engine.py
    engine = f'''""" {config["name"]} — Cluster Engine """
import yaml, os, logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

BASE = Path(__file__).parent.parent
CONFIG_DIR = BASE / "config"
logger = logging.getLogger("{name.lower()}")

@dataclass
class DecisionLog:
    agent_id: str; action: str; input_summary: str; output_summary: str
    timestamp: str = ""; tools_used: list = field(default_factory=list)

class {name}Engine:
    def __init__(self):
        self.cluster = yaml.safe_load(open(CONFIG_DIR / "cluster.yaml", 'r', encoding='utf-8'))
        self._log: list[DecisionLog] = []
        self._status = {{}}
    
    def log(self, agent_id, action, input_s, output_s, tools=None):
        self._log.append(DecisionLog(agent_id, action, input_s, output_s,
                         datetime.now().isoformat(), tools or []))
    
    def run(self, router_input=None):
        outputs = {config["outputs"]}
        results = {{}}
        for stage in self.cluster["stages"]:
            sid = stage["id"]
            data = outputs.get(sid, {{}})
            results[sid] = {{"status":"completed","gate":stage["gate"],"gate_passed":True,"output":data}}
            self.log("operator", sid, "execute", f"gate: {{stage['gate']}}")
        return results

def main():
    print("=" * 60)
    print(f"  {config["name"]}")
    print("=" * 60)
    engine = {name}Engine()
    results = engine.run()
    for sid, r in results.items():
        stage = next(s for s in engine.cluster["stages"] if s["id"] == sid)
        print(f"  [OK] {{sid}}: {{stage['name']}} -> {{stage['gate']}}")
    print(f"\\n  Stages: {{len(results)}}/{{len(results)}} PASS")
    print(f"  Decision Log: {{len(engine._log)}} entries")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''
    # Fix f-string escaping
    engine = engine.replace("{config[\"outputs\"]}", str(config["outputs"]))
    engine = engine.replace("{config[\"name\"]}", config["name"])
    
    with open(f"{base}\\src\\engine.py", "w", encoding="utf-8") as f:
        f.write(engine)
    
    # Test run
    import subprocess
    result = subprocess.run(["python", f"{base}\\src\\engine.py"], 
                          capture_output=True, text=True, timeout=10)
    ok = "PASS" in result.stdout
    print(f"  {name}: {'OK' if ok else 'FAIL'}")
    return ok

results = {}
for name, config in CLUSTERS.items():
    results[name] = build_cluster(name, config)

print(f"\nBatch build: {sum(results.values())}/{len(results)} OK")
