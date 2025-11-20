#!/usr/bin/env bash
# check_imports.sh
# Usage: run from Kudu Bash (or an ssh shell) in the App Service container.
# It will create /tmp/check_imports.py and run it using any found /tmp/*/antenv python.

set -o errexit
set -o nounset
set -o pipefail

PY_PATH="/tmp/check_imports.py"

echo "Writing Python import-check script to $PY_PATH ..."
cat > "$PY_PATH" <<'PY'
import traceback, importlib, sys
modules = ("streamlit","pandas","sqlalchemy","openpyxl","numpy")
for m in modules:
    try:
        mod = importlib.import_module(m)
        ver = getattr(mod, "__version__", getattr(mod, "version", ""))
        print(f"{m} OK {ver}")
    except Exception:
        print(f"ERROR importing {m}", file=sys.stderr)
        traceback.print_exc()
PY

echo
echo "Scanning /tmp for antenv virtualenvs and running the import test..."
found=0

for d in /tmp/*; do
  if [ -d "$d/antenv" ]; then
    found=1
    VENV_PY="$d/antenv/bin/python"
    echo
    echo "========================================="
    echo "VENV detected: $d/antenv"
    echo "Running: $VENV_PY $PY_PATH"
    if [ -x "$VENV_PY" ]; then
      "$VENV_PY" "$PY_PATH" || echo "Import tests returned non-zero for $d/antenv"
    else
      echo "Python executable not found or not executable at $VENV_PY"
    fi
    echo "========================================="
  fi
done

if [ "$found" -eq 0 ]; then
  echo
  echo "No antenv virtualenvs found under /tmp."
  echo "Listing /tmp directory for inspection:"
  ls -la /tmp || true
fi

echo
echo "Also testing the container's default 'python' in PATH (if present) ..."
if command -v python >/dev/null 2>&1; then
  python "$PY_PATH" || echo "Default python import test returned non-zero"
else
  echo "No 'python' in PATH"
fi

echo
echo "Done. If you see any lines that start with 'ERROR importing', copy the full traceback and paste it here so I can diagnose the failure."
exit 0