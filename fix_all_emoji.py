"""
fix_all_emoji.py
Replaces all non-ASCII emoji characters in print() and log statements
across all project Python files with ASCII-safe equivalents.
Safe to run multiple times (idempotent).
"""
import os
import re

# Map common emoji to ASCII labels
EMOJI_MAP = {
    '\u2705': '[OK]',       # [OK]
    '\u274c': '[FAIL]',     # [FAIL]
    '\u26a0\ufe0f': '[WARN]',  # [WARN] (with variation selector)
    '\u26a0': '[WARN]',     # [WARN]
    '\u23f3': '[WAIT]',     # [WAIT]
    '\U0001f504': '[RETRY]',# [RETRY]
    '\U0001f4e2': '[NOTIFY]',# [NOTIFY]
    '\U0001f4bb': '[CODE]', # [CODE]
    '\U0001f50d': '[SEARCH]',# [SEARCH]
    '\U0001f9ea': '[TEST]', # [TEST]
    '\U0001f4dd': '[PR]',   # [PR]
    '\u2728': '[NEW]',      # [NEW]
    '\U0001f680': '[RUN]',  # [RUN]
    '\U0001f4be': '[SAVE]', # [SAVE]
    '\u2139\ufe0f': '[INFO]',# [INFO]
    '\u2139': '[INFO]',     # [INFO]
    '\U0001f916': '[BOT]',  # [BOT]
    '\U0001f4f1': '[PHONE]',# [PHONE]
    '\u2714': '[OK]',       # [OK]
    '\u2716': '[FAIL]',     # [FAIL]
    '\U0001f525': '[HOT]',  # [HOT]
    '\U0001f4a1': '[IDEA]', # [IDEA]
    '\U0001f4ca': '[STATS]',# [STATS]
}

PROJECT_ROOT = r"d:\Jira-Agentic-Development-System"
SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules"}

def replace_emoji(content: str) -> str:
    for emoji, replacement in EMOJI_MAP.items():
        content = content.replace(emoji, replacement)
    return content

fixed_files = []
skipped_files = []

for root, dirs, files in os.walk(PROJECT_ROOT):
    # Prune skip dirs
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for filename in files:
        if not filename.endswith('.py'):
            continue

        filepath = os.path.join(root, filename)

        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                original = f.read()

            fixed = replace_emoji(original)

            if fixed != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed)
                rel = os.path.relpath(filepath, PROJECT_ROOT)
                fixed_files.append(rel)
                print(f"[FIXED] {rel}")
        except Exception as e:
            skipped_files.append((filepath, str(e)))
            print(f"[SKIP]  {filepath}: {e}")

print()
print("=" * 60)
print(f"  Fixed {len(fixed_files)} file(s)")
if skipped_files:
    print(f"  Skipped {len(skipped_files)} file(s) (errors)")
print("=" * 60)
