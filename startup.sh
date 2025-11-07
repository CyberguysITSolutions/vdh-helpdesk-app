#!/usr/bin/env bash
set -e
set -u
if [ -n "${BASH_VERSION:-}" ]; then
  set -o pipefail
fi

APP="/home/site/wwwroot/helpdesk_app.py"

ST_PORT=8000
ST_ADDR="0.0.0.0"
ST_BASE="/login"
ST_FLAGS="--server.port ${ST_PORT} --server.address ${ST_ADDR} --server.headless true --server.baseUrlPath ${ST_BASE} --server.enableCORS false --server.enableXsrfProtection false --logger.level debug"

# Helper: validate a python binary by trying to run a trivial import
validate_python() {
  local py="$1"
  if [ -x "$py" ]; then
    if "$py" -c "import sys" >/dev/null 2>&1; then
      echo "$py"
      return 0
    fi
  fi
  return 1
}

PYTHON=""

# 1) Prefer the persistent venv under /home if it contains a working python
HOME_PY="/home/site/wwwroot/antenv/bin/python"
HOME_PY3="/home/site/wwwroot/antenv/bin/python3"
if validate_python "$HOME_PY" >/dev/null 2>&1; then
  PYTHON="$HOME_PY"
elif validate_python "$HOME_PY3" >/dev/null 2>&1; then
  PYTHON="$HOME_PY3"
fi

# 2) If persistent venv didn't work, search for an Oryx-extracted tmp venv
if [ -z "${PYTHON}" ]; then
  for d in /tmp/*/antenv/bin/python /tmp/*/antenv/bin/python3; do
    if validate_python "$d" >/dev/null 2>&1; then
      PYTHON="$d"
      VENV_ROOT="$(dirname "$(dirname "${d}")")"
      PYVER="$("$d" -c "import sys; print('python{}.{}'.format(sys.version_info.major, sys.version_info.minor))" 2>/dev/null || echo '')"
      if [ -n "$PYVER" ]; then
        export PYTHONPATH="${VENV_ROOT}/lib/${PYVER}/site-packages:${PYTHONPATH:-}"
      fi
      break
    fi
  done
fi

# 3) As last-resort, try system python3, but only if it actually runs
if [ -z "${PYTHON}" ]; then
  if command -v python3 >/dev/null 2>&1 && validate_python "$(command -v python3)" >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  fi
fi

if [ -z "${PYTHON}" ]; then
  echo "ERROR: No usable python found. Checked persistent venv, tmp venvs under /tmp, and system python3."
  echo "Please ensure /home/site/wwwroot/antenv contains a working python or re-deploy so Oryx provides a tmp venv."
  exit 1
fi

echo "Using python: ${PYTHON}"
echo "Starting Streamlit with flags: ${ST_FLAGS}"

exec "${PYTHON}" -m streamlit run "${APP}" ${ST_FLAGS}
