import io
s = io.open('server.py', encoding='utf-8').read()
# Simple scanner to find unclosed string literal
state = 'code'
quote_char = None
quote_start = None
i = 0
line = 1
last_open = None
while i < len(s):
    ch = s[i]
    # handle newlines
    if ch == '\n':
        line += 1
    if state == 'code':
        # detect triple quotes first
        if s.startswith('"""', i):
            state = 'string'
            quote_char = '"""'
            quote_start = line
            i += 3
            continue
        if s.startswith("'''", i):
            state = 'string'
            quote_char = "'''"
            quote_start = line
            i += 3
            continue
        if ch == '"' or ch == "'":
            state = 'string'
            quote_char = ch
            quote_start = line
            i += 1
            continue
    elif state == 'string':
        if quote_char in ('"""', "'''"):
            if s.startswith(quote_char, i):
                state = 'code'
                quote_char = None
                quote_start = None
                i += 3
                continue
        else:
            if ch == '\\':
                i += 2
                continue
            if ch == quote_char:
                state = 'code'
                quote_char = None
                quote_start = None
                i += 1
                continue
    i += 1

if state != 'code':
    print('Unclosed string starting at line', quote_start, 'quote:', quote_char)
    # print context
    lines = s.splitlines()
    start = max(1, quote_start-5)
    end = min(len(lines), quote_start+20)
    for ln in range(start, end+1):
        print(ln, lines[ln-1])
else:
    print('No unclosed string found')
