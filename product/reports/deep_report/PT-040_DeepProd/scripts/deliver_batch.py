import os
acc = r'D:\6_agent_project\.org\accepted_proposals'
for i in range(2, 8):
    p = os.path.join(acc, f'PP-20260615-{i:03d}.yaml')
    c = open(p, 'r', encoding='utf-8').read()
    c = c.replace('accepted', 'delivered')
    c += '\n  delivered: "2026-06-15T19:45"'
    open(p, 'w', encoding='utf-8').write(c)
# metrics
m = open(r'D:\6_agent_project\.org\metrics.md', 'r', encoding='utf-8').read()
m = m.replace('delivered_this_month: 5', 'delivered_this_month: 11')
m = m.replace('delivered_total: 10', 'delivered_total: 16')
m = m.replace('T2: { total: 4, delivered: 2 }', 'T2: { total: 9, delivered: 7 }')
open(r'D:\6_agent_project\.org\metrics.md', 'w', encoding='utf-8').write(m)
print('All 6 clusters + metrics updated')
