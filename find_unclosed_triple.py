import io
s = io.open('server.py', encoding='utf-8').read().splitlines()
open_stack = []
for i, l in enumerate(s,1):
    if '"""' in l:
        # count occurrences in the line
        cnt = l.count('"""')
        for _ in range(cnt):
            if open_stack and open_stack[-1][0] == '"""':
                open_stack.pop()
            else:
                open_stack.append(('"""', i))
    if "'''" in l:
        cnt = l.count("'''")
        for _ in range(cnt):
            if open_stack and open_stack[-1][0] == "'''":
                open_stack.pop()
            else:
                open_stack.append(("'''", i))

print('Open triple-quote stack (top is last):')
for kind, line in open_stack[-10:]:
    print(kind, line)

if open_stack:
    kind, start = open_stack[-1]
    print('\nFirst unclosed triple-quote appears at line', start)
    start_context = max(1, start-3)
    end_context = min(len(s), start+10)
    print('\nContext around the opener:')
    for i in range(start_context, end_context+1):
        print(i, s[i-1])
else:
    print('\nNo unclosed triple-quote found (parity balanced).')
