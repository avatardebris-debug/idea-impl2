"""
recorder.py — VCR-style HTTP record/replay for test fixtures.

Records real HTTP responses to disk during a "record" session, then replays
them from disk in "replay" mode — so tests never need a live network.

Why this matters for the pipeline
----------------------------------
Tests that use recorded real responses:
  - Catch real parsing bugs (real APIs return surprising fields, encodings,
    pagination shapes the code has never seen)
  - Are reproducible regardless of API availability / rate limits
  - Permanently pin the exact failure case when something breaks in production

Usage
-----
    # --- Record a real call once ---
    with VCRRecorder(cassette_dir=Path("tests/cassettes"), mode="record") as vcr:
        with vcr.intercept("GET", "https://api.example.com/users"):
            response = urllib.request.urlopen("https://api.example.com/users")

    # --- Replay in CI ---
    with VCRRecorder(cassette_dir=Path("tests/cassettes"), mode="replay") as vcr:
        with vcr.intercept("GET", "https://api.example.com/users"):
            response = urllib.request.urlopen("https://api.example.com/users")
            # returns the recorded bytes, no network call made

Implementation note
--------------------
Rather than monkey-patching urllib globally (fragile), the recorder provides
an explicit `fake_urlopen` context manager that patches at the call site.
This keeps the intercept scope narrow and avoids import-order surprises.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Cassette data model
# ---------------------------------------------------------------------------

@dataclass
class RecordedRequest:
    method: str
    url: str
    request_headers: Dict[str, str]
    recorded_at: float


@dataclass
class RecordedResponse:
    status: int
    headers: Dict[str, str]
    body: str           # always stored as UTF-8 text (base64 if binary)
    is_binary: bool = False


@dataclass
class Cassette:
    request: RecordedRequest
    response: RecordedResponse

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Cassette":
        return cls(
            request=RecordedRequest(**d["request"]),
            response=RecordedResponse(**d["response"]),
        )


# ---------------------------------------------------------------------------
# Cassette store (disk I/O)
# ---------------------------------------------------------------------------

def _cassette_path(cassette_dir: Path, method: str, url: str) -> Path:
    """Deterministic filename based on method + URL hash."""
    key = f"{method.upper()}::{url}"
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    safe_url = urllib.parse.urlparse(url).path.replace("/", "_").strip("_")[:40]
    return cassette_dir / f"{safe_url}__{h}.json"


def save_cassette(cassette_dir: Path, method: str, url: str, cassette: Cassette) -> Path:
    cassette_dir.mkdir(parents=True, exist_ok=True)
    path = _cassette_path(cassette_dir, method, url)
    path.write_text(json.dumps(cassette.to_dict(), indent=2), encoding="utf-8")
    return path


def load_cassette(cassette_dir: Path, method: str, url: str) -> Optional[Cassette]:
    path = _cassette_path(cassette_dir, method, url)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Cassette.from_dict(data)


# ---------------------------------------------------------------------------
# Fake HTTP response (returned during replay)
# ---------------------------------------------------------------------------

class _FakeHTTPResponse:
    """Mimics the interface of urllib.request.urlopen() responses."""

    def __init__(self, cassette: Cassette):
        self._cassette = cassette
        self._body = cassette.response.body.encode("utf-8")
        self._pos = 0
        self.status = cassette.response.status
        self.headers = cassette.response.headers

    def read(self, n: int = -1) -> bytes:
        if n == -1:
            data = self._body[self._pos:]
            self._pos = len(self._body)
        else:
            data = self._body[self._pos:self._pos + n]
            self._pos += n
        return data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def getcode(self) -> int:
        return self.status


# ---------------------------------------------------------------------------
# VCRRecorder
# ---------------------------------------------------------------------------

class VCRRecorder:
    """
    Lightweight VCR recorder/replayer for urllib-based HTTP calls.

    Modes
    -----
    "record"  — make the real network call and save the response
    "replay"  — return the saved response without any network call
    "passthrough" — do nothing (useful in integration environments)
    """

    def __init__(self, cassette_dir: Path, mode: str = "replay"):
        if mode not in ("record", "replay", "passthrough"):
            raise ValueError(f"Invalid mode: {mode!r}. Use 'record', 'replay', or 'passthrough'.")
        self.cassette_dir = Path(cassette_dir)
        self.mode = mode

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @contextmanager
    def intercept(self, method: str, url: str) -> Generator[None, None, None]:
        """
        Context manager that patches urllib.request.urlopen for a specific URL.

        In record mode: the real call is made and saved.
        In replay mode: the saved response is returned.
        In passthrough mode: does nothing.
        """
        if self.mode == "passthrough":
            yield
            return

        if self.mode == "replay":
            cassette = load_cassette(self.cassette_dir, method, url)
            if cassette is None:
                raise FileNotFoundError(
                    f"No cassette found for {method} {url}. "
                    f"Run with mode='record' first."
                )
            fake_response = _FakeHTTPResponse(cassette)

            def fake_urlopen(req_or_url, *args, **kwargs):
                return fake_response

            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                yield

        elif self.mode == "record":
            # Let the real call through, then save
            cassette_holder: List[Optional[Cassette]] = [None]

            original_urlopen = urllib.request.urlopen

            def recording_urlopen(req_or_url, *args, **kwargs):
                req_headers: Dict[str, str] = {}
                if isinstance(req_or_url, urllib.request.Request):
                    req_headers = dict(req_or_url.headers)

                resp = original_urlopen(req_or_url, *args, **kwargs)

                # Read and buffer the body
                body_bytes = resp.read()
                try:
                    body_text = body_bytes.decode("utf-8")
                    is_binary = False
                except UnicodeDecodeError:
                    import base64
                    body_text = base64.b64encode(body_bytes).decode("ascii")
                    is_binary = True

                cassette = Cassette(
                    request=RecordedRequest(
                        method=method.upper(),
                        url=url,
                        request_headers=req_headers,
                        recorded_at=time.time(),
                    ),
                    response=RecordedResponse(
                        status=getattr(resp, "status", 200),
                        headers=dict(getattr(resp, "headers", {})),
                        body=body_text,
                        is_binary=is_binary,
                    ),
                )
                cassette_holder[0] = cassette

                # Return a replay-able fake response so callers can still .read()
                return _FakeHTTPResponse(cassette)

            with patch("urllib.request.urlopen", side_effect=recording_urlopen):
                yield

            if cassette_holder[0]:
                save_cassette(self.cassette_dir, method, url, cassette_holder[0])
