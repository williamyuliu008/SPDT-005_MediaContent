import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r"C:\Users\willi\Desktop\我的视野\0615-组织级智能体集群设计\文字创作智能体集团军-设计需求"
files = sorted(os.listdir(base))
for i in range(7):
    path = os.path.join(base, files[i])
    content = open(path, 'r', encoding='utf-8').read()
    title = re.search(r'title:\s*(.+)', content)
    priority = re.search(r'priority:\s*(.+)', content)
    est = re.search(r'estimated_agents:\s*(.+)', content)
    cycle = re.search(r'estimated_cycle:\s*(.+)', content)
    name = title.group(1).strip() if title else "?"
    print(f"SR-TEXT-{i+1:03d}: {name}")
    if priority: print(f"  Priority: {priority.group(1)}")
    if est: print(f"  Agents: {est.group(1)}")
    if cycle: print(f"  Cycle: {cycle.group(1)}")
    print()
