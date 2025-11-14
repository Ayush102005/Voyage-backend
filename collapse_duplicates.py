import io, shutil
src = 'server.py'
bak = 'server.py.bak'
shutil.copyfile(src, bak)
lines = io.open(src, encoding='utf-8').read().splitlines()
out = []
prev = None
for l in lines:
    if l == prev:
        # collapse consecutive identical lines into one
        continue
    out.append(l)
    prev = l
# write back
io.open(src, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('Collapsed consecutive duplicate lines. Backup at', bak)
print('Original lines:', len(lines), 'New lines:', len(out))
