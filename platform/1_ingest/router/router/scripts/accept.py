f=r'D:\6_agent_project\.org\accepted_proposals\PP-20260615-001.yaml'
c=open(f,'r',encoding='utf-8').read()
c=c.replace('proposed','accepted')+'\n  accepted: "2026-06-15T19:10"'
open(f,'w',encoding='utf-8').write(c)
print('accepted')
