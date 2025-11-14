import io
s = io.open('server.py', encoding='utf-8').read().splitlines()
for i, l in enumerate(s, 1):
    if '"""' in l or "'''" in l:
        print(i, repr(l))
# Print nearby context around the reported last triple-quote before the error line
error_line = 4480
start = max(1, error_line-20)
end = min(len(s), error_line+5)
print('\nContext around line', error_line)
for i in range(start, end+1):
    print(i, s[i-1])
