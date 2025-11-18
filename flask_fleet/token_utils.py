"""
token_utils.py

Create and verify HMAC tokens for one-click approval links.

Tokens are HMAC-SHA256 over "<trip_id>:<ts>" with a server-side secret. We include ts (UNIX seconds).
"""
import os
import hmac
import hashlib
import time

# Secret should be strong and kept out of source control. Put in .streamlit/secrets.toml or env:
# HMAC_SECRET = "very-secret-value"
HMAC_SECRET = os.getenv("HMAC_SECRET")

if not HMAC_SECRET:
    # try load from .streamlit/secrets.toml if present
    try:
        import tomllib as toml
    except Exception:
        try:
            import toml
        except Exception:
            toml = None
    if toml and os.path.exists(".streamlit/secrets.toml"):
        with open(".streamlit/secrets.toml", "rb") as f:
            data = toml.load(f)
            HMAC_SECRET = data.get("security", {}).get("hmac_secret")

def make_token(trip_id: int, ts: int = None):
    ts = ts or int(time.time())
    msg = f"{trip_id}:{ts}".encode("utf-8")
    sig = hmac.new(HMAC_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return sig, ts

def verify_token(trip_id: int, token: str, ts: str, max_age_seconds: int = 7*24*3600):
    try:
        ts_int = int(ts)
    except:
        return False, "invalid timestamp"
    # check age
    if abs(int(time.time()) - ts_int) > max_age_seconds:
        return False, "token expired"
    expected = hmac.new(HMAC_SECRET.encode("utf-8"), f"{trip_id}:{ts}".encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, token):
        return False, "signature mismatch"
    return True, "ok"