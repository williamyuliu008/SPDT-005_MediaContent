# -*- coding: utf-8 -*-
import re

with open('gui_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open('_tmp_css_insert.py', 'r', encoding='utf-8') as f:
    tmp = f.read()

# Find new CSS block - look for _INK_GOLD_CSS = r""" and extract until next """
idx_new_start = tmp.find('_INK_GOLD_CSS = r"""')
if idx_new_start < 0:
    print('ERROR: _INK_GOLD_CSS start not found in tmp')
    exit(1)
search_from = idx_new_start + len('_INK_GOLD_CSS = r"""')
idx_new_close = tmp.find('"""', search_from)
if idx_new_close < 0:
    print('ERROR: closing """ not found in tmp')
    exit(1)
new_block = tmp[idx_new_start:idx_new_close+3]
print('New CSS length:', len(new_block))
print('New block preview:', repr(new_block[:80]))

# Find old CSS block - need to find the closing """ of the _INK_GOLD_CSS assignment
# The old block starts at '# ── 墨韵金韵主题注入' and ends after the closing """
idx_old_start = content.find('# ── 墨韵金韵主题注入')
# Find the opening r""" after _INK_GOLD_CSS =
idx_ink = content.find('_INK_GOLD_CSS = r"""', idx_old_start)
if idx_ink < 0:
    print('ERROR: _INK_GOLD_CSS start not found')
    exit(1)
# Find the closing """ - start after the opening """
search_from = idx_ink + len('_INK_GOLD_CSS = r"""')
idx_close = content.find('"""', search_from)
if idx_close < 0:
    print('ERROR: closing """ not found')
    exit(1)
# End of old block is after the closing """
idx_old_end = idx_close + len('"""')
old_block = content[idx_old_start:idx_old_end]
print('Old CSS length:', len(old_block))
print('Old block preview:', repr(old_block[:80]))

# Do replacement - new_block includes only the CSS, we need to add st.markdown after
new_content = content.replace(old_block, new_block + '\nst.markdown(_INK_GOLD_CSS, unsafe_allow_html=True)\n')
print('Replacement done, new length:', len(new_content))

with open('gui_app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('File written successfully')
