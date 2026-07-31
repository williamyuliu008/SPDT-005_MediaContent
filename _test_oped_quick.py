# -*- coding: utf-8 -*-
"""Quick oped test after banned fix"""
import sys, os, time, json, re
from pathlib import Path
os.environ['DEEPSEEK_API_KEY'] = 'sk-91c9278a57b84e909c823c2acc4fae10'
ROOT = Path(r'D:\2_products\media\SPDT-005_MediaContent')
TS = str(int(time.time() * 1000))

def load(p, k):
    key = f'{TS}_{k}'
    for m in list(sys.modules.keys()):
        if m.startswith(('_m_', '_spdt')):
            del sys.modules[m]
    import importlib.util
    spec = importlib.util.spec_from_file_location(key, str(p))
    m = importlib.util.module_from_spec(spec)
    sys.modules[key] = m
    spec.loader.exec_module(m)
    return m

RADAR  = load(ROOT / 'platform/1_ingest/radar/radar_opinion.py', 'op1')
ARTCL  = load(ROOT / 'platform/2_structure/article/article_opinion.py', 'op2')
REND   = load(ROOT / 'platform/3_render/engines/text/render_opinion.py', 'op3')
SCARD  = load(ROOT / 'platform/4_adapt/scorecard/scorecard_opinion.py', 'op4')

topic = 'AI监管：必要的刹车而非倒车'
req = RADAR.RadarOpinionRequest(topic=topic, perspective='支持', industry_focus='科技行业', max_signals=4)
brief = RADAR.RadarOpinion().run(req)
res2 = ARTCL.ArticleOpinion().run(brief, title=topic)
res3 = REND.RenderOpinion().run(res2, brand_voice='assertive')
res4 = SCARD.ScorecardOpinion().run(res3)
render_dict = res3.to_dict()
sc = res4.to_dict()
dims = sc['scorecard']['dimensions']
print(f'tone_ok={render_dict["tone_check"]["passed"]}')
print(f'violations={render_dict["tone_check"]["violations"]}')
print(f'brand={dims["brand"]} factual={dims["factual"]} logic={dims["logic"]}')
print(f'score={sc["scorecard"]["total_score"]} action={sc["action"]}')

md = render_dict['markdown']
body = re.sub(r'(?s)^---.*?---\n', '', md)
paras = [p.strip() for p in re.findall(r'(?m)^(.+)$', body) if len(p.strip()) > 20]
long = len([p for p in paras if len(p) > 120])
print(f'paras={len(paras)} avg={sum(len(p) for p in paras)//len(paras)} max={max(len(p) for p in paras)} long={long}')
