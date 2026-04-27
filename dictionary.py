"""Dictionary API client — stdlib only, no external deps.

Uses Datamuse (api.datamuse.com): ~150ms p50, sourced from Wiktionary,
~25x faster than the previous api.dictionaryapi.dev which was Cloudflare-
fronted and slow.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://api.datamuse.com/words"
TIMEOUT_SECONDS = 4
USER_AGENT = "ulauncher-define/0.2 (+https://github.com/anentree/ulauncher-define)"

# Datamuse encodes part-of-speech as a single-letter prefix on each definition.
POS_NAMES = {
    "n": "noun",
    "v": "verb",
    "adj": "adjective",
    "adv": "adverb",
    "u": "unknown",
}


@dataclass(frozen=True)
class Definition:
    part_of_speech: str
    text: str


def lookup(word: str) -> list[Definition] | str:
    """Returns a list of Definitions on success, or an error message string on failure."""
    clean = word.strip().lower()
    if not clean:
        return "Type a word"

    qs = urlencode({"sp": clean, "md": "d", "max": "1"})
    url = f"{API_URL}?{qs}"
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as e:
        return f"Dictionary returned HTTP {e.code}"
    except (URLError, socket.timeout, TimeoutError):
        return "Couldn't reach dictionary (offline?)"

    try:
        payload = json.loads(raw)
        if not payload:
            return f"No definition found for '{word}'"

        entry = payload[0]
        # Datamuse `sp=` is fuzzy; reject if it didn't return our exact word.
        if entry.get("word", "").lower() != clean:
            return f"No definition found for '{word}'"

        defs_raw = entry.get("defs") or []
        if not defs_raw:
            return f"No definition found for '{word}'"

        out: list[Definition] = []
        seen: set[tuple[str, str]] = set()
        for d in defs_raw:
            pos_abbr, sep, text = d.partition("\t")
            if not sep or not text:
                continue
            pos = POS_NAMES.get(pos_abbr, pos_abbr)
            key = (pos, text)
            if key in seen:
                continue
            seen.add(key)
            out.append(Definition(part_of_speech=pos, text=text))

        if not out:
            return "Dictionary returned unexpected data"
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return "Dictionary returned unexpected data"

    return out
