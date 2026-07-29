f=r'D:\6_agent_project\.org\accepted_proposals\PP-20260615-001.yaml'
c=open(f,'r',encoding='utf-8').read()
c=c.replace('accepted','delivered')+'\n  delivered: "2026-06-15T19:14"'
open(f,'w',encoding='utf-8').write(c)
# metrics
m=open(r'D:\6_agent_project\.org\metrics.md','r',encoding='utf-8').read()
m=m.replace('delivered_this_month: 4','delivered_this_month: 5')
m=m.replace('delivered_total: 9','delivered_total: 10')
m=m.replace('T1: { total: 7, delivered: 2 }','T1: { total: 8, delivered: 3 }')
open(r'D:\6_agent_project\.org\metrics.md','w',encoding='utf-8').write(m)
print('status + metrics updated')
