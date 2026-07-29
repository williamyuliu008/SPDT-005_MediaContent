import os
base = r'D:\6_agent_project\.org\incoming_proposals'
acc = r'D:\6_agent_project\.org\accepted_proposals'
for i in range(2, 8):
    src = os.path.join(base, f'PP-20260615-{i:03d}.yaml')
    dst = os.path.join(acc, f'PP-20260615-{i:03d}.yaml')
    c = open(src, 'r', encoding='utf-8').read()
    c = c.replace('proposed', 'accepted')
    c = c + '\n  accepted: "2026-06-15T19:36"'
    open(dst, 'w', encoding='utf-8').write(c)
    os.remove(src)
    print(f'Accepted: PP-20260615-{i:03d}')
