import io, re
src = 'server.py'
text = io.open(src, encoding='utf-8').read()
lines = text.splitlines()
seen = set()
out_lines = []
i = 0
n = len(lines)

def is_top_decorator(line):
    return line.startswith('@app.') or line.startswith('@router.') or line.startswith('@app')

while i < n:
    line = lines[i]
    if line.lstrip().startswith('@app.'):
        # capture consecutive decorators (could be multiple)
        dec_start = i
        dec_lines = []
        while i < n and lines[i].lstrip().startswith('@'):
            dec_lines.append(lines[i])
            i += 1
        # next non-decorator line should be def
        if i < n and re.match(r'^\s*def\s', lines[i]):
            def_line = lines[i]
            m = re.match(r'^\s*def\s+([a-zA-Z_][\w_]*)\s*\(', def_line)
            func_name = m.group(1) if m else None
            if func_name and func_name in seen:
                # skip this entire function block until next top-level decorator or EOF
                print(f"Skipping duplicate route function: {func_name} at line {dec_start+1}")
                i += 1
                # skip function body (indented) until next decorator at column 0 or next EOF
                while i < n:
                    # if a top-level decorator (starts at col 0 with @app.) found, stop skipping
                    if lines[i].startswith('@app.'):
                        break
                    # also stop if we see a top-level def (unlikely) or end of file
                    if re.match(r'^@', lines[i]) and not lines[i].startswith('    '):
                        break
                    i += 1
                continue
            else:
                # keep it
                if func_name:
                    seen.add(func_name)
                # write decorators and def line
                for l in dec_lines:
                    out_lines.append(l)
                out_lines.append(lines[i])
                i += 1
                # write function body
                while i < n:
                    # stop before next top-level decorator
                    if lines[i].startswith('@app.'):
                        break
                    out_lines.append(lines[i])
                    i += 1
                continue
        else:
            # decorator not followed by def? keep as-is
            for l in dec_lines:
                out_lines.append(l)
            continue
    else:
        out_lines.append(line)
        i += 1

# write backup and overwrite
import shutil
shutil.copyfile(src, src + '.bak_duplicates')
io.open(src, 'w', encoding='utf-8').write('\n'.join(out_lines) + '\n')
print('Wrote cleaned server.py, backup at', src + '.bak_duplicates')
print('Original lines:', n, 'New lines:', len(out_lines))
