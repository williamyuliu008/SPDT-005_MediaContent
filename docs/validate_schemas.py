import json
from pathlib import Path

schemas = [
    r'D:\1_omas\MODLIB\schemas\article_v2.schema.json',
    r'D:\1_omas\MODLIB\schemas\intelligence_brief.schema.json',
    r'D:\1_omas\MODLIB\schemas\article_outline.schema.json',
    r'D:\1_omas\MODLIB\schemas\quality_scorecard.schema.json',
    r'D:\1_omas\MODLIB\schemas\content_product.schema.json',
]
for path in schemas:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    name = Path(path).name
    print(f'OK: {name} | version={data["version"]} | frozen={data.get("frozen", "N/A")}')
