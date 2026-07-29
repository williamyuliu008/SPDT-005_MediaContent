import sys; sys.path.insert(0, r'D:\_CEO\ceo')
from cabinet import list_cabinets
for c in list_cabinets():
    print(f"{c['org_id']:20s} | {c['short_name']:6s} | {c['name']}")
