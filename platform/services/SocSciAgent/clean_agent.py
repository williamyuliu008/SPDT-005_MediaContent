"""Clean LLM-generated Python files: remove markdown wrappers and trailing analysis."""
import sys, os

EMOJI_START = ord('\u2700')
EMOJI_END = ord('\U0010ffff')

def is_emoji_line(line):
    s = line.strip()
    if not s:
        return False
    for ch in s:
        cp = ord(ch)
        if EMOJI_START <= cp <= EMOJI_END:
            return True
    return False

def is_chinese_only(s):
    for ch in s:
        if not ('\u4e00' <= ch <= '\u9fff' or ch in ' \t\u3000-\u303f\uff00-\uffef，。！？；：""''（）【】'):
            return False
    return True

def clean_py_file(path):
    content = open(path, encoding='utf-8').read()
    lines = content.split('\n')
    result = []
    i = 0
    n = len(lines)

    # Skip leading ``` markers
    while i < n and '```' in lines[i].strip()[:4]:
        i += 1

    for line in lines[i:]:
        s = line.strip()
        # Skip pure emoji lines
        if is_emoji_line(s):
            continue
        # Skip markdown code block closers (```)
        if s == '```' or s.startswith('```'):
            continue
        # Skip pure Chinese lines (no code)
        if is_chinese_only(s):
            continue
        # Skip lines with only emoji and Chinese
        if is_emoji_line(line) and is_chinese_only(s):
            continue
        result.append(line)

    # Trim trailing empty lines
    while result and not result[-1].strip():
        result.pop()

    out = '\n'.join(result)
    if out and not out.endswith('\n'):
        out += '\n'
    open(path, 'w', encoding='utf-8').write(out)
    return len(out)

if __name__ == '__main__':
    p = sys.argv[1]
    sz = clean_py_file(p)
    actual = os.path.getsize(p)
    print(f'Cleaned: {sz} chars, {actual} bytes on disk')
