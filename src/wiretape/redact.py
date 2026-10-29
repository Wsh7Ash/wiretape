"""Redaction for anything that leaves the process.

Captured traffic is full of live credentials: the session cookie you were given,
the bearer token in the replay, the API key in a query string. A tool that
exports exchanges has to assume the export will be pasted into a report, a
ticket or a chat, so redaction happens on the way out by default.
"""

from __future__ import annotations

import re

# Header names whose values are always replaced.
SECRET_HEADERS = (
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "x-auth-token",
    "x-csrf-token",
    "x-xsrf-token",
    "x-amz-security-token",
)

# Query and body parameters whose values are replaced.
SECRET_PARAMS = (
    "token",
    "access_token",
    "id_token",
    "refresh_token",
    "api_key",
    "apikey",
    "key",
    "secret",
    "password",
    "passwd",
    "session",
    "sessionid",
    "sig",
    "signature",
)

PLACEHOLDER = "<redacted>"

_HEADER_RE = re.compile(
    r"(?im)^(" + "|".join(re.escape(h) for h in SECRET_HEADERS) + r")\s*:\s*(.+)$"
)
_PARAM_RE = re.compile(
    r"(?i)\b(" + "|".join(re.escape(p) for p in SECRET_PARAMS) + r")=([^&\s\"'<>]+)"
)
_JSON_SECRET_RE = re.compile(
    r'(?i)"(' + "|".join(re.escape(p) for p in SECRET_PARAMS) + r')"\s*:\s*"([^"]*)"'
)
# Bearer/JWT-ish blobs that appear inline in prose rather than in a header.
_BEARER_RE = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9\-._~+/=]{8,}")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}\b")


def redact(text: str, placeholder: str = PLACEHOLDER) -> str:
    """Replace credentials in a message, header block or JSON body."""
    if not text:
        return text
    out = _HEADER_RE.sub(lambda m: f"{m.group(1)}: {placeholder}", text)
    out = _JSON_SECRET_RE.sub(lambda m: f'"{m.group(1)}": "{placeholder}"', out)
    out = _PARAM_RE.sub(lambda m: f"{m.group(1)}={placeholder}", out)
    out = _BEARER_RE.sub(lambda m: f"{m.group(1)} {placeholder}", out)
    out = _JWT_RE.sub(placeholder, out)
    return out


def redact_headers(headers: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    """Redact a header list while preserving order and duplicates."""
    out: list[tuple[str, str]] = []
    for name, value in headers:
        if name.lower() in SECRET_HEADERS:
            out.append((name, PLACEHOLDER))
        else:
            out.append((name, redact(value)))
    return tuple(out)


def contains_secret(text: str) -> bool:
    """Whether redaction would change this string (used by the leak guard)."""
    return redact(text) != text
