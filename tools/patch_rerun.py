#!/usr/bin/env python3
"""
Patch helpdesk_app.py:

- Insert a safe_rerun() helper (if missing) after the marker '# --- end replacement ---'
  (falls back to inserting after the last import block if the marker is not found)
- Replace st.experimental_rerun() and st.rerun() with safe_rerun()

Run:
  .venv\Scripts\python.exe tools\patch_rerun.py
"""
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime
from typing import Optional

ROOT = Path(".")
TARGET = ROOT / "helpdesk_app.py"
if not TARGET.exists():
    print("ERROR: helpdesk_app.py not found in repo root.")
    sys.exit(1)

# Create a timestamped backup filename next to the original
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
bak_name = TARGET.with_name(f"{TARGET.stem}.py.bak.{timestamp}")

try:
    content = TARGET.read_text(encoding="utf-8")
except Exception as e:
    print(f"ERROR reading {TARGET}: {e}")
    sys.exit(1)

# safe_rerun helper code to insert
safe_rerun_code = (
    "\n# --- safe rerun helper (inserted automatically) -------------------------\n"
    "def safe_rerun():\n"
    "    \"\"\"\n"
    "    Cross-version safe replacement for st.experimental_rerun()/st.rerun().\n"
    "    Call safe_rerun() instead of st.experimental_rerun() or st.rerun().\n"
    "    \"\"\"\n"
    "    try:\n"
    "        # Preferred newer API\n"
    "        return st.experimental_rerun()\n"
    "    except Exception:\n"
    "        try:\n"
    "            # Streamlit newer internal location\n"
    "            from streamlit.runtime.scriptrunner import RerunException\n"
    "            raise RerunException()\n"
    "        except Exception:\n"
    "            try:\n"
    "                # Older Streamlit internal path\n"
    "                from streamlit.report_thread import RerunException as _OldRerunException  # type: ignore\n"
    "                raise _OldRerunException()\n"
    "            except Exception:\n"
    "                # Final fallback: stop the script (prevents AttributeError)\n"
    "                st.stop()\n"
    "# ------------------------------------------------------------------------\n\n"
)

# 1) Insert safe_rerun if missing
if "def safe_rerun" in content:
    print("safe_rerun already present, skipping insertion.")
    insert_made = False
else:
    marker = "# --- end replacement ---"
    insert_pos: Optional[int] = None
    idx = content.find(marker)
    if idx != -1:
        # insert after the end of the marker line (preserve newline)
        nl_after = content.find("\n", idx + len(marker))
        if nl_after != -1:
            insert_pos = nl_after + 1
        else:
            insert_pos = idx + len(marker)
    else:
        # fallback: insert after the last import statement block
        import_matches = list(
            re.finditer(r'^(?:import\s.+|from\s.+\simport\s.+)$', content, flags=re.MULTILINE)
        )
        if import_matches:
            last_imp = import_matches[-1]
            # insert after that line
            nl_after = content.find("\n", last_imp.end())
            if nl_after != -1:
                insert_pos = nl_after + 1
            else:
                insert_pos = last_imp.end()
        else:
            # fallback to top of file
            insert_pos = 0

    if insert_pos is None:
        insert_pos = 0

    content = content[:insert_pos] + safe_rerun_code + content[insert_pos:]
    insert_made = True
    print("Inserted safe_rerun helper into helpdesk_app.py")

# 2) Replace st.experimental_rerun() and st.rerun() calls
# Use patterns that tolerate whitespace between tokens
re_exp = re.compile(r'(?<!\w)st\.experimental_rerun\s*\(\s*\)', flags=re.MULTILINE)
re_rerun = re.compile(r'(?<!\w)st\.rerun\s*\(\s*\)', flags=re.MULTILINE)

# Count occurrences before replacement (for reporting)
count_exp_before = len(re_exp.findall(content))
count_rerun_before = len(re_rerun.findall(content))

content, n1 = re_exp.subn('safe_rerun()', content)
content, n2 = re_rerun.subn('safe_rerun()', content)

total_replaced = n1 + n2

# 3) Write backup then overwrite file
try:
    shutil.copy2(TARGET, bak_name)
    TARGET.write_text(content, encoding="utf-8")
except Exception as e:
    print(f"ERROR writing changes: {e}")
    sys.exit(1)

print(f"Backup written to: {bak_name.name}")
print(
    f"Replacements made: experimental_rerun (before={count_exp_before}) -> replaced={n1}, "
    f"st.rerun (before={count_rerun_before}) -> replaced={n2} (total replaced={total_replaced})"
)
if insert_made:
    print("safe_rerun was inserted.")
else:
    print("safe_rerun was already present; no insertion was made.")

# 4) show remaining occurrences (for verification)
remaining_exp = re_exp.search(content)
remaining_rerun = re_rerun.search(content)
if not remaining_exp and not remaining_rerun:
    print("No remaining st.experimental_rerun() or st.rerun() occurrences found.")
else:
    print("Warning: some occurrences remain. Please inspect helpdesk_app.py manually.")