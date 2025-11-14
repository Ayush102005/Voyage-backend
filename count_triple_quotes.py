import io
s = io.open('server.py', encoding='utf-8').read()
count_double = s.count('"""')
count_single = s.count("'''")
print('""" count =', count_double)
print("''' count =", count_single)
# Print lines where a triple quote occurs with context
lines = s.splitlines()
for i,l in enumerate(lines,1):
    if '"""' in l or "'''" in l:
        print(i, l)
