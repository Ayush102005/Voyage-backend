"""
Script: remove_duplicate_routes.py
Purpose: Read backend/server.py, remove duplicate FastAPI route functions (same function name), keep the first occurrence.
Behavior:
- Backs up original file to server.py.bak.TIMESTAMP
- Writes cleaned server.py (overwrites)
- This is a conservative text-based approach: it looks for decorators starting with @app. and the following def/async def; if a function name repeats, removes the entire decorator+function block for subsequent occurrences.
- It tries to preserve other code and formatting.

Run from backend/ directory: python scripts/remove_duplicate_routes.py
"""
import re
import shutil
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # backend/
SERVER = BASE / "server.py"
if not SERVER.exists():
    print(f"Error: {SERVER} not found")
    raise SystemExit(1)

with SERVER.open("r", encoding="utf-8") as f:
    lines = f.readlines()

# Helper to get indentation level (count of leading spaces; tabs converted to 4 spaces)
def leading_spaces(s: str) -> int:
    s_exp = s.replace('\t', '    ')
    return len(s_exp) - len(s_exp.lstrip(' '))

# Scan lines to find decorated functions that are FastAPI routes
# We'll collect blocks: (start_idx, end_idx, func_name)
blocks = []
idx = 0
n = len(lines)
route_decorator_pattern = re.compile(r'^\s*@app\.(get|post|put|delete|patch|options|head)\b')
def_line_pattern = re.compile(r'^\s*(async\s+def|def)\s+([a-zA-Z0-9_]+)\s*\(')

while idx < n:
    line = lines[idx]
    if route_decorator_pattern.match(line):
        # decorator block may have multiple decorators stacked; find top of decorator section
        start_idx = idx
        # Move forward to find the def line
        j = idx + 1
        # include other decorators (e.g., @some_other_decorator) until def line found
        while j < n and not def_line_pattern.match(lines[j]):
            j += 1
        if j >= n:
            # malformed - stop
            break
        # j is def line
        m = def_line_pattern.match(lines[j])
        if not m:
            idx = j + 1
            continue
        func_name = m.group(2)
        def_indent = leading_spaces(lines[j])
        # Determine end of function by scanning until we find a line with indentation <= def_indent that's not blank/comment
        k = j + 1
        while k < n:
            # stop when encountering another top-level decorator or a top-level def/class or EOF
            line_k = lines[k]
            if line_k.strip().startswith('@app.'):
                # next route decorator found at same or earlier level -> stop function at previous line
                break
            if line_k.strip().startswith('def ') or line_k.strip().startswith('async def ') or line_k.strip().startswith('class '):
                # If this def/class is at same or lesser indentation, it's a new top-level def/class
                if leading_spaces(line_k) <= def_indent:
                    break
            # If line indentation is <= def_indent and line not blank/comment, might be end of function
            if line_k.strip() and leading_spaces(line_k) <= def_indent:
                # It's likely a new top-level or sibling block
                break
            k += 1
        end_idx = k  # exclusive
        blocks.append((start_idx, end_idx, func_name))
        idx = end_idx
        continue
    idx += 1

# Now remove duplicate function blocks by function name, keep first occurrence
seen = set()
to_remove = [False] * n
for (s, e, name) in blocks:
    if name in seen:
        # mark lines s..e-1 for removal
        for i in range(s, e):
            to_remove[i] = True
        print(f"Marked duplicate function '{name}' (lines {s+1}-{e}) for removal")
    else:
        seen.add(name)

# If no duplicates, exit
if not any(to_remove):
    print("No duplicate route functions found. No changes made.")
    raise SystemExit(0)

# Backup original
bak = SERVER.with_suffix(SERVER.suffix + f".bak.{int(time.time())}")
shutil.copy2(SERVER, bak)
print(f"Backup written to: {bak}")

# Write cleaned file
new_lines = [lines[i] for i in range(n) if not to_remove[i]]
with SERVER.open('w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Wrote cleaned file: {SERVER}")
removed_count = sum(1 for x in to_remove if x)
print(f"Removed {removed_count} lines ({len(blocks) - len(seen)} duplicate function blocks removed)")
print("Done.")
