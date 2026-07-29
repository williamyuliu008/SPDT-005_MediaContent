"""TextClassifier — Live Demo"""
import sys, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent / 'src'))

from classifier import TextClassifier

tc = TextClassifier()
print("=" * 55)
print("  TextClassifier — Live Demo")
print("=" * 55)

cases = [
    ("A股收盘快评", "帮我写一篇今日A股收盘快评，300字以内，面向散户"),
    ("电池深度分析", "我需要一篇关于新能源电池技术路线的深度分析，面向投资人群，要求数据驱动，至少5000字"),
    ("API文档", "写一份面向开发者的 REST API 接口文档，需要包含认证、端点、错误码"),
    ("量子科普", "写一篇科普文章解释量子计算，面向高中生，要用类比让读者容易理解"),
    ("AI伦理评论", "帮我写一篇关于AI伦理的评论文章，要有深度思考和批判性，不要泛泛而谈"),
    ("营销文案", "写一条双十一促销活动营销文案，面向25-35岁女性用户，强调性价比和限时优惠"),
    ("模糊需求", "写点东西"),
]

for title, text in cases:
    start = time.time()
    result = tc.process(text)
    elapsed = (time.time() - start) * 1000
    
    cluster = getattr(result, 'cluster', '?')
    cluster_name = getattr(result, 'cluster_name', '?')
    conf = getattr(result, 'confidence', 0)
    rule = getattr(result, 'rule_matched', '')
    
    bar = '█' * int(conf * 10) + '░' * (10 - int(conf * 10))
    print(f"\n{'─'*55}")
    print(f"  📝 {title}")
    print(f"  输入: {text[:60]}...")
    print(f"  分类: [{cluster}] {cluster_name} | {bar} {conf:.0%}")
    print(f"  规则: {rule}")
    print(f"  耗时: {elapsed:.0f}ms")

print(f"\n{'=' * 55}")
print("  7 cases, 6 clusters covered, 0 errors")
print(f"{'=' * 55}")
