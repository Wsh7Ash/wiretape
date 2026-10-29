"""Raw HTTP exchanges: parse, serialize, send, capture.

The whole point of this module is that it never normalizes a message it was
asked to transmit. Header order, duplicate headers, header casing, the exact
request target and the body bytes all survive the round trip, because the bugs
worth finding usually live in the difference between what a normalizing proxy
sends and what the RFC allows you to send.

Only one header is ever synthesized: ``Host``, and only when the author left it
out, because a request without it cannot be routed at all. Everything else is
byte-for-byte the author's text.
"""

from __future__ import annotations

import socket
import ssl
import time
from dataclasses import dataclass, field
from typing import Iterable

CRLF = b"\r\n"


class ExchangeError(ValueError):
    """A message that cannot be parsed or a connection that cannot be made."""


def _split_head_body(data: bytes) -> tuple[list[str], bytes]:
    """Split at the first blank line, accepting CRLF or bare LF."""
    idx = data.find(b"\r\n\r\n")
    sep = 4
    if idx < 0:
        idx = data.find(b"\n\n")
        sep = 2
    if idx < 0:
        raise ExchangeError("message has no blank line separating head from body")
    head = data[:idx].decode("latin-1").replace("\r\n", "\n")
    return head.split("\n"), data[idx + sep :]


def _parse_headers(lines: Iterable[str]) -> tuple[tuple[str, str], ...]:
    headers: list[tuple[str, str]] = []
    for line in lines:
        if not line.strip():
            continue
        if line[0] in " \t" and headers:
            name, value = headers[-1]
            headers[-1] = (name, f"{value} {line.strip()}")
            continue
        if ":" not in line:
            raise ExchangeError(f"header line without colon: {line!r}")
        name, _, value = line.partition(":")
        headers.append((name.strip(), value.strip()))
    return tuple(headers)


@dataclass(frozen=True)
class RawRequest:
    """One request exactly as it will appear on the wire."""

    method: str
    target: str
    version: str
    headers: tuple[tuple[str, str], ...] = ()
    body: bytes = b""

    @classmethod
    def parse(cls, data: str | bytes) -> "RawRequest":
        raw = data.encode("latin-1") if isinstance(data, str) else data
        head, body = _split_head_body(raw)
        if not head:
            raise ExchangeError("empty request")
        parts = head[0].split()
        if len(parts) != 3:
            raise ExchangeError(f"bad request line: {head[0]!r}")
        method, target, version = parts
        if not version.upper().startswith("HTTP/"):
            raise ExchangeError(f"bad HTTP version: {version!r}")
        return cls(method, target, version, _parse_headers(head[1:]), body)

    def header(self, name: str) -> str | None:
        for key, value in self.headers:
            if key.lower() == name.lower():
                return value
        return None

    def with_headers(self, headers: tuple[tuple[str, str], ...]) -> "RawRequest":
        return RawRequest(self.method, self.target, self.version, headers, self.body)

    @property
    def path(self) -> str:
        target = self.target
        if target.startswith(("http://", "https://")):
            rest = target.split("://", 1)[1]
            target = "/" + rest.split("/", 1)[1] if "/" in rest else "/"
        return target.split("?", 1)[0]

    @property
    def query(self) -> str:
        return self.target.split("?", 1)[1] if "?" in self.target else ""

    def to_bytes(self, host_header: str | None = None) -> bytes:
        """Serialize, adding ``Host`` only if the author omitted it."""
        headers = list(self.headers)
        if host_header and not self.header("host"):
            headers.insert(0, ("Host", host_header))
        lines = [f"{self.method} {self.target} {self.version}"]
        lines += [f"{name}: {value}" for name, value in headers]
        head = "\r\n".join(lines).encode("latin-1") + CRLF + CRLF
        return head + self.body

    def render(self) -> str:
        lines = [f"{self.method} {self.target} {self.version}"]
        lines += [f"{name}: {value}" for name, value in self.headers]
        text = "\n".join(lines) + "\n\n"
        return text + self.body.decode("utf-8", "replace")


@dataclass(frozen=True)
class RawResponse:
    """One response, including the exact octets it arrived as."""

    version: str
    status: int
    reason: str
    headers: tuple[tuple[str, str], ...] = ()
    body: bytes = b""
    raw: bytes = b""

    @classmethod
    def parse(cls, data: str | bytes) -> "RawResponse":
        raw = data.encode("latin-1") if isinstance(data, str) else data
        head, body = _split_head_body(raw)
        if not head:
            raise ExchangeError("empty response")
        parts = head[0].split(None, 2)
        if len(parts) < 2:
            raise ExchangeError(f"bad status line: {head[0]!r}")
        version, status_text = parts[0], parts[1]
        reason = parts[2] if len(parts) > 2 else ""
        try:
            status = int(status_text)
        except ValueError as exc:
            raise ExchangeError(f"bad status code: {status_text!r}") from exc
        return cls(version, status, reason, _parse_headers(head[1:]), body, raw)

    def header(self, name: str) -> str | None:
        for key, value in self.headers:
            if key.lower() == name.lower():
                return value
        return None

    def header_values(self, name: str) -> tuple[str, ...]:
        return tuple(v for k, v in self.headers if k.lower() == name.lower())

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")

    @property
    def content_type(self) -> str:
        return (self.header("content-type") or "").split(";")[0].strip().lower()

    def render(self) -> str:
        lines = [f"{self.version} {self.status} {self.reason}".rstrip()]
        lines += [f"{name}: {value}" for name, value in self.headers]
        return "\n".join(lines) + "\n\n" + self.body.decode("utf-8", "replace")


@dataclass
class Exchange:
    """A request, the response it produced, and when that happened."""

    request: RawRequest
    response: RawResponse | None = None
    elapsed_ms: float = 0.0
    error: str | None = None
    sent_bytes: bytes = b""
    received_bytes: bytes = b""

    @property
    def ok(self) -> bool:
        return self.error is None and self.response is not None


def _read_response(sock: socket.socket, timeout: float) -> bytes:
    """Read until headers plus a complete body, according to Content-Length."""
    sock.settimeout(timeout)
    chunks: list[bytes] = []
    total = 0
    head_end = -1
    length: int | None = None
    deadline = time.monotonic() + timeout
    while True:
        if time.monotonic() > deadline:
            break
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            break
        except OSError as exc:  # connection reset mid-body
            raise ExchangeError(f"connection error while reading: {exc}") from exc
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        data = b"".join(chunks)
        if head_end < 0:
            for sep in (b"\r\n\r\n", b"\n\n"):
                pos = data.find(sep)
                if pos >= 0:
                    head_end = pos + len(sep)
                    head = data[:pos].decode("latin-1").replace("\r\n", "\n")
                    for line in head.split("\n")[1:]:
                        name, _, value = line.partition(":")
                        if name.strip().lower() == "content-length":
                            try:
                                length = int(value.strip())
                            except ValueError:
                                length = None
                    break
            if head_end < 0:
                continue
        if length is not None and total - head_end >= length:
            break
        if length is None and head_end >= 0:
            # No length: the only honest signal left is connection close.
            continue
    return b"".join(chunks)


def send(
    request: RawRequest,
    *,
    host: str,
    port: int,
    scheme: str = "https",
    timeout: float = 15.0,
    follow_redirects: bool = False,
    verify_tls: bool = True,
) -> Exchange:
    """Transmit one request and capture the response octets.

    Redirects are never followed by default: a 302 is evidence, not a detour.
    """
    sent = request.to_bytes(host_header=f"{host}:{port}" if port not in (80, 443) else host)
    started = time.monotonic()
    exchange = Exchange(request=request, sent_bytes=sent)
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        exchange.error = f"connect failed: {exc}"
        return exchange
    try:
        if scheme == "https":
            context = ssl.create_default_context()
            if not verify_tls:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=host)
        sock.sendall(sent)
        received = _read_response(sock, timeout)
    except (OSError, ssl.SSLError, ExchangeError) as exc:
        exchange.error = f"send failed: {exc}"
        return exchange
    finally:
        try:
            sock.close()
        except OSError:
            pass
    exchange.elapsed_ms = (time.monotonic() - started) * 1000.0
    exchange.received_bytes = received
    if not received:
        exchange.error = "empty response"
        return exchange
    try:
        exchange.response = RawResponse.parse(received)
    except ExchangeError as exc:
        exchange.error = str(exc)
        return exchange
    if follow_redirects and exchange.response.status in (301, 302, 303, 307, 308):
        location = exchange.response.header("location")
        if location and location.startswith(("http://", "https://")):
            from urllib.parse import urlsplit

            parts = urlsplit(location)
            followed = RawRequest("GET", parts.path + (f"?{parts.query}" if parts.query else ""), "HTTP/1.1", ())
            return send(
                followed,
                host=parts.hostname or host,
                port=parts.port or (443 if parts.scheme == "https" else 80),
                scheme=parts.scheme,
                timeout=timeout,
                follow_redirects=False,
                verify_tls=verify_tls,
            )
    return exchange
