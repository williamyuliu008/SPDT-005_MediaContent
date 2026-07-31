# -*- coding: utf-8 -*-
"""验证 science_readability fix（infobox 注入）"""
import sys, importlib.util, time, re, json, os
from pathlib import Path

os.environ['DEEPSEEK_API_KEY'] = 'sk-91c9278a57b84e909c823c2acc4fae10'
ROOT = Path(r'D:\2_products\media\SPDT-005_MediaContent')
TS = str(int(time.time() * 1000))

def load(p, k):
    key = f'{TS}_{k}'
    if key in sys.modules:
        del sys.modules[key]
    for m in list(sys.modules.keys()):
        if m.startswith(('_m_', '_spdt')) or k in m:
            del sys.modules[m]
    s = importlib.util.spec_from_file_location(key, str(p))
    m = importlib.util.module_from_spec(s)
    sys.modules[key] = m
    s.loader.exec_module(m)
    return m

# Load fresh
RADAR  = load(ROOT / 'platform/1_ingest/radar/radar_science_fact.py',           'radar')
ARTICLE = load(ROOT / 'platform/2_structure/article/article_science_fact.py',    'article')
RENDER  = load(ROOT / 'platform/3_render/engines/text/render_science_fact.py',   'render')
SC      = load(ROOT / 'platform/4_adapt/scorecard/scorecard_science_fact.py',    'sc')

def to_dict(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    from dataclasses import asdict
    d = asdict(obj) if hasattr(obj, '__dataclass_fields__') else dict(obj) if obj else {}
    # ArticleScienceFactResult wraps in {"outline": ...}
    if "outline" in d and isinstance(d["outline"], dict):
        return d["outline"]
    return d

topic = '量子计算突破：Google Willow芯片的科学意义'
req = RADAR.RadarScienceFactRequest(topic=topic, max_signals=3)
brief = to_dict(RADAR.RadarScienceFact().run(req))
outline_dict = to_dict(ARTICLE.ArticleScienceFact().run(brief))
render_result = RENDER.RenderScienceFact().run(outline_dict)
article = render_result.article

# Check infoboxes
blocks = article.get('blocks', [])
infoboxes = [b for b in blocks if b.get('type') == 'infobox']
print(f'Infoboxes injected: {len(infoboxes)}')
for ib in infoboxes:
    txt = ib.get('content', {}).get('text', '')
    print(f'  > {txt}')

# Paragraph analysis
md = article.get('markdown', '')
body = re.sub(r'(?s)^---.*?---\n', '', md)
body = re.sub(r'(?m)^#.+$', '', body)
body = re.sub(r'(?m)^## .+$', '', body)
paras = [p.strip() for p in re.findall(r'(?m)^(.+)$', body) if len(p.strip()) > 20]
lens = [len(p) for p in paras]
long_paras = [p for p in paras if len(p) > 120]
sentences = len(re.findall(r'[。！？]', body))
print(f'\nParagraphs: {len(paras)}, avg: {sum(lens)//len(lens)}字, longest: {max(lens)}字')
print(f'Exceeding 120 chars: {len(long_paras)}/{len(paras)}')
print(f'Sentences: {sentences}, ratio: {sentences/len(paras):.1f}')

# Scorecard
score_result = SC.ScorecardScienceFact().run(article)
sc = score_result.scorecard
inner = sc.get('scorecard', sc)
dims = {k: round(v['score'], 1) for k, v in inner.get('dimensions', {}).items()}
print(f'\nTotal: {inner.get("total_score", "?")}')
print(f'Dims: {json.dumps(dims, ensure_ascii=False)}')
print(f'Readability: {dims.get("readability", "?")}  (target: >= 80)')
print(f'PASSED: {score_result.passed} | Action: {score_result.action}')
print(f'\n{"✅ PASS" if dims.get("readability", 0) >= 80 else "❌ FAIL"} readability >= 80')
