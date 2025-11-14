"""
Script to remove the old dashboard endpoint from server.py
"""

with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of the old dashboard endpoint (line 1688, index 1687 in 0-indexed)
# Find the end (before "# TRENDING SUGGESTIONS ENDPOINT")

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    # Find start: @app.get("/api/dashboard", response_model=UserDashboardResponse)
    if '@app.get("/api/dashboard", response_model=UserDashboardResponse)' in line:
        start_idx = i
        print(f"Found old dashboard start at line {i+1}")
    
    # Find end: # TRENDING SUGGESTIONS ENDPOINT (after the old dashboard)
    if start_idx is not None and end_idx is None:
        if '# TRENDING SUGGESTIONS ENDPOINT' in line and i > start_idx + 100:
            # Backtrack to find the empty line before this comment
            for j in range(i-1, start_idx, -1):
                if lines[j].strip() == '':
                    end_idx = j
                    break
            if end_idx is None:
                end_idx = i - 2  # Fallback
            print(f"Found old dashboard end at line {end_idx+1}")
            break

if start_idx is not None and end_idx is not None:
    print(f"\nRemoving lines {start_idx+1} to {end_idx+1}")
    print(f"Total lines to remove: {end_idx - start_idx + 1}")
    
    # Create new file without the old dashboard endpoint
    new_lines = lines[:start_idx] + lines[end_idx+1:]
    
    with open('server.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Successfully removed old dashboard endpoint!")
    print(f"Old file: {len(lines)} lines")
    print(f"New file: {len(new_lines)} lines")
    print(f"Removed: {len(lines) - len(new_lines)} lines")
else:
    print("❌ Could not find old dashboard endpoint")
    if start_idx is not None:
        print(f"Found start at {start_idx+1}")
    if end_idx is not None:
        print(f"Found end at {end_idx+1}")
