"""Dictionary API client — stdlib only, no external deps."""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
TIMEOUT_SECONDS = 6  # live-probe median latency ~3.8s, p95 ~3.87s
USER_AGENT = "ulauncher-define/0.1 (+https://github.com/neo/ulauncher-define)"


@dataclass(frozen=True)
class Definition:
    part_of_speech: str
    text: str


def lookup(word: str) -> list[Definition] | str:
    """Returns a list of Definitions on success, or an error message string on failure.

    The error-as-string return makes the caller (`main.py`) a trivial isinstance check
    and avoids a custom exception class that would shadow stdlib `LookupError`.
    """
    clean = word.strip().lower()
    url = API_URL.format(word=quote(clean, safe=""))
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as e:
        # HTTPError must come before URLError — it's a subclass.
        if e.code == 404:
            return f"No definition found for '{word}'"
        return f"Dictionary returned HTTP {e.code}"
    except (URLError, socket.timeout, TimeoutError):
        return "Couldn't reach dictionary (offline?)"

    try:
        payload = json.loads(raw)
        out: list[Definition] = []
        seen: set[tuple[str, str]] = set()
        for entry in payload:
            for meaning in entry["meanings"]:
                pos = meaning["partOfSpeech"]
                defs = meaning.get("definitions") or []
                if not defs:
                    continue
                text = defs[0]["definition"]
                key = (pos, text)
                if key in seen:
                    continue
                seen.add(key)
                out.append(Definition(part_of_speech=pos, text=text))
        if not out:
            raise ValueError("no meanings in any entry")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        # Catches: not JSON, payload not a list, entry missing keys, empty result.
        return "Dictionary returned unexpected data"

    return out
