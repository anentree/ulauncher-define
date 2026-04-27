import json
from unittest.mock import patch, MagicMock
from urllib.error import URLError

from dictionary import Definition, lookup


# Datamuse format: list of one entry with `defs` array of "POS\tText" strings.
PEACE_RESPONSE = [
    {
        "word": "peace",
        "score": 100,
        "defs": [
            "n\tFreedom from disturbance; tranquility.",
            "n\tA state of mutual harmony between people.",
            "v\tTo make peaceful; to put at peace; to be at peace.",
        ],
    }
]

# Datamuse merges homographs into one entry's defs array.
BASS_RESPONSE = [
    {
        "word": "bass",
        "defs": [
            "n\tA fish.",
            "n\tLow-pitched sound.",
        ],
    }
]

# An entry with a malformed def (no tab separator) — should skip without raising.
MALFORMED_DEF_RESPONSE = [
    {
        "word": "x",
        "defs": [
            "no_tab_separator_here",
            "v\tReal def.",
        ],
    }
]


def _mock_urlopen(payload):
    m = MagicMock()
    m.read.return_value = json.dumps(payload).encode("utf-8")
    m.__enter__.return_value = m
    m.__exit__.return_value = False
    return m


def test_lookup_returns_one_definition_per_def_string():
    with patch("dictionary.urlopen", return_value=_mock_urlopen(PEACE_RESPONSE)):
        result = lookup("peace")
    assert result == [
        Definition(
            part_of_speech="noun", text="Freedom from disturbance; tranquility."
        ),
        Definition(
            part_of_speech="noun", text="A state of mutual harmony between people."
        ),
        Definition(
            part_of_speech="verb",
            text="To make peaceful; to put at peace; to be at peace.",
        ),
    ]


def test_lookup_handles_homograph_in_defs():
    with patch("dictionary.urlopen", return_value=_mock_urlopen(BASS_RESPONSE)):
        result = lookup("bass")
    assert len(result) == 2
    assert {d.text for d in result} == {"A fish.", "Low-pitched sound."}


def test_lookup_skips_malformed_defs():
    with patch(
        "dictionary.urlopen", return_value=_mock_urlopen(MALFORMED_DEF_RESPONSE)
    ):
        result = lookup("x")
    assert result == [Definition(part_of_speech="verb", text="Real def.")]


def test_lookup_returns_error_on_empty_response():
    with patch("dictionary.urlopen", return_value=_mock_urlopen([])):
        result = lookup("asdfqwerty")
    assert isinstance(result, str)
    assert "no definition found" in result.lower()


def test_lookup_returns_error_on_word_mismatch():
    # Datamuse fuzzy match: user typed 'xyzzy', got back a related word.
    response = [{"word": "different", "defs": ["n\tSome def."]}]
    with patch("dictionary.urlopen", return_value=_mock_urlopen(response)):
        result = lookup("xyzzy")
    assert isinstance(result, str)
    assert "no definition found" in result.lower()


def test_lookup_returns_error_when_entry_has_no_defs():
    # Datamuse can return a word entry with no `defs` field (just a spelling match).
    response = [{"word": "peace", "score": 100}]
    with patch("dictionary.urlopen", return_value=_mock_urlopen(response)):
        result = lookup("peace")
    assert isinstance(result, str)
    assert "no definition found" in result.lower()


def test_lookup_returns_error_on_network_error():
    with patch("dictionary.urlopen", side_effect=URLError("no internet")):
        result = lookup("peace")
    assert isinstance(result, str)
    assert "reach" in result.lower() or "offline" in result.lower()


def test_lookup_returns_error_on_bad_json():
    bad = MagicMock()
    bad.read.return_value = b"not json"
    bad.__enter__.return_value = bad
    bad.__exit__.return_value = False
    with patch("dictionary.urlopen", return_value=bad):
        result = lookup("peace")
    assert isinstance(result, str)
    assert "unexpected" in result.lower()


def test_lookup_url_encodes_multi_word_query():
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        return _mock_urlopen([{"word": "ice cream", "defs": ["n\tFrozen dessert."]}])

    with patch("dictionary.urlopen", side_effect=fake_urlopen):
        lookup("ice cream")

    # urlencode default uses + for spaces in query strings.
    assert "ice+cream" in captured["url"] or "ice%20cream" in captured["url"]
