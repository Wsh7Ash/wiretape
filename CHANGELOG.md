# Changelog

All notable changes are documented here. This project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-29

### Added

- `RawRequest` / `RawResponse` with ordered header pairs, duplicate preservation
  and byte-exact serialization; `Host` is synthesized only when omitted.
- Socket sender with TLS support, `Content-Length` aware reads, elapsed time and
  SHA-256 digests of the sent and received octets. Redirects are not followed by
  default.
- Tape format (`schema` 1) with `request`, `shell` and `wait` steps, `{{var}}`
  substitution, `extract` (body regex, header, status) and `expect` (status,
  contains, absent, regex).
- Runner with a hard scope guard, an opt-in shell gate, fail-fast, dry run,
  raw capture files and a redacted run report.
- Exporters: runnable curl, HAR 1.2, markdown report and raw HTTP bundle, all
  redacted and all able to fill values a run extracted.
- Redaction for secret headers, query parameters, JSON fields, bearer tokens and
  JWTs, applied on every output path.
- `lint`, `steps`, `send`, `run`, `export` plus the shared corpus commands.
- 50 validated skills across capture, replay, extract, assert, execute and
  export phases, with a render/validate/build harness.
- 40 tests, including a real local HTTP server, the socket path, the runner,
  redaction and every exporter.
- A demo target and demo tape that run end to end against loopback.

### Fixed during the build

- Dry runs failed on variables produced by earlier steps; dry run now validates
  scope and routing only.
- HAR export did not redact secret query parameters by name.
- curl and markdown exports printed unresolved `{{variable}}` references from a
  completed run instead of the extracted values.
- A dry run with `--capture` failed because the capture directory was created
  only when a response was written.
