"""Fix chief_editor: convert from standalone .py to package with __init__.py"""
import os

base = r"D:\92_products\SPDT-005_MediaContent\PT-047_SocSciAgent\agents\chief_editor"
src = os.path.join(base, "chief_editor.py")
dst = os.path.join(base, "agent.py")
init = '__init__.py'

if os.path.exists(src):
    os.rename(src, dst)
    print(f"Renamed: chief_editor.py -> agent.py")

init_path = os.path.join(base, init)
with open(init_path, 'w', encoding='utf-8') as f:
    f.write('"""chief_editor package."""\n')
    f.write('from .agent import ChiefEditorAgent, ChiefEditorInput, ChiefEditorOutput\n')
    f.write('from .tension_curve import TensionCurve\n')
    f.write('from .three_stage_funnel import ThreeStageFunnel\n')
print(f"Created: {init_path}")

for fname in os.listdir(base):
    print(f"  {fname}")
