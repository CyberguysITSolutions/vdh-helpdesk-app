#!/usr/bin/env bash
# Robust startup script for Streamlit on App Service
# Enables pipefail only when running under bash so it is safe if invoked by /bin/sh.

set -e
set -u
# Enable pipefail only when running under bash (dash/sh don't support it)
if [ -n "${BASH_VERSION:-}" ]; then
  set -o pipefail
fi

# Path to app main file
APP="/home/site/wwwroot/helpdesk_app.py"

# Streamlit options
ST_PORT=8000
ST_ADDR="0.0.0.0"
ST_BASE="/login"
ST_FLAGS="--server.port ${ST_PORT} --server.address ${ST_ADDR} --server.headless true --server.baseUrlPath ${ST_BASE} --server.enableCORS false --server.enableXsrfProtection false --logger.level info"

# Prefer the home venv if present
HOME_VENV_PY="/home/site/wwwroot/antenv/bin/python"
TMP_VENV_PY=""
for d in /tmp/*/antenv/bin/python ; do
  if [ -x "$d" ]; then
    TMP_VENV_PY="$d"
    break
  fi
done

if [ -x "${HOME_VENV_PY}" ]; then
  PYTHON="${HOME_VENV_PY}"
elif [ -n "${TMP_VENV_PY}" ] && [ -x "${TMP_VENV_PY}" ]; then
  PYTHON="${TMP_VENV_PY}"
  export PYTHONPATH="$(dirname "$(dirname "${TMP_VENV_PY}")")/lib/$( "${TMP_VENV_PY}" -c "import sys; print('python{}.{}'.format(sys.version_info.major,sys.version_info.minor))" 2>/dev/null || echo '')/site-packages:${PYTHONPATH:-}"
else
  PYTHON="/usr/bin/python3"
fi

echo "Using python: ${PYTHON}"
echo "Starting Streamlit with flags: ${ST_FLAGS}"

exec "${PYTHON}" -m streamlit run "${APP}" ${ST_FLAGS}
