import json
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

from dictionary import Definition, lookup


PEACE_RESPONSE = [
    {
        "word": "peace",
        "meanings": [
            {
                "partOfSpeech": "noun",
                "definitions": [
                    {"definition": "Freedom from disturbance; tranquility."},
                    {"definition": "A state of mutual harmony between people."},
                ],
            },
            {
                "partOfSpeech": "verb",
                "definitions": [{"definition": "To make peaceful."}],
            },
        ],
    }
]

# Homograph: API returns multiple top-level entries.
BASS_RESPONSE = [
    {
        "word": "bass",
        "meanings": [
            {"partOfSpeech": "noun", "definitions": [{"definition": "A fish."}]}
        ],
    },
    {
        "word": "bass",
        "meanings": [
            {
                "partOfSpeech": "noun",
                "definitions": [{"definition": "Low-pitched sound."}],
            }
        ],
    },
]

# Edge case: an entry with an empty definitions list should be skipped, not raise.
EMPTY_MEANING_RESPONSE = [
    {
        "word": "x",
        "meanings": [
            {"partOfSpeech": "noun", "definitions": []},
            {"partOfSpeech": "verb", "definitions": [{"definition": "Real def."}]},
        ],
    }
]


def _mock_urlopen(payload):
    m = MagicMock()
    m.read.return_value = json.dumps(payload).encode("utf-8")
    m.__enter__.return_value = m
    m.__exit__.return_value = False
    return m


def test_lookup_returns_one_definition_per_meaning():
    with patch("dictionary.urlopen", return_value=_mock_urlopen(PEACE_RESPONSE)):
        result = lookup("peace")
    assert result == [
        Definition(
            part_of_speech="noun", text="Freedom from disturbance; tranquility."
        ),
        Definition(part_of_speech="verb", text="To make peaceful."),
    ]


def test_lookup_flattens_homograph_entries():
    with patch("dictionary.urlopen", return_value=_mock_urlopen(BASS_RESPONSE)):
        result = lookup("bass")
    assert len(result) == 2
    assert {d.text for d in result} == {"A fish.", "Low-pitched sound."}


def test_lookup_skips_meanings_with_no_definitions():
    with patch(
        "dictionary.urlopen", return_value=_mock_urlopen(EMPTY_MEANING_RESPONSE)
    ):
        result = lookup("x")
    assert result == [Definition(part_of_speech="verb", text="Real def.")]


def test_lookup_returns_error_string_on_404():
    err = HTTPError(url="x", code=404, msg="Not Found", hdrs=None, fp=None)
    with patch("dictionary.urlopen", side_effect=err):
        result = lookup("asdfqwerty")
    assert isinstance(result, str)
    assert "no definition found" in result.lower()


def test_lookup_returns_error_string_on_network_error():
    with patch("dictionary.urlopen", side_effect=URLError("no internet")):
        result = lookup("peace")
    assert isinstance(result, str)
    assert "reach" in result.lower() or "offline" in result.lower()


def test_lookup_returns_error_string_on_bad_json():
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
        return _mock_urlopen(PEACE_RESPONSE)

    with patch("dictionary.urlopen", side_effect=fake_urlopen):
        lookup("ice cream")

    assert "ice%20cream" in captured["url"]
