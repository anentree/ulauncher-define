"""Ulauncher entry point for the Define extension."""

from __future__ import annotations

from textwrap import shorten
from urllib.parse import quote

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

from dictionary import lookup

ICON = "images/icon.png"
MAX_RESULTS = 8
DESC_WIDTH = 100
WIKTIONARY_URL = "https://en.wiktionary.org/wiki/{word}"


def _single(name: str, description: str = "") -> RenderResultListAction:
    return RenderResultListAction(
        [ExtensionResultItem(icon=ICON, name=name, description=description)]
    )


class DefineExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        word = (event.get_argument() or "").strip()
        if not word:
            return _single("Type a word after the keyword…")

        result = lookup(word)
        if isinstance(result, str):
            return _single(result)

        # Ulauncher's default theme forces every row to one line (ellipsize=middle,
        # max-width-chars=1), so long definitions get truncated inline. Enter opens
        # the word in Wiktionary for the full entry; Alt+Enter copies the short
        # definition to clipboard for power-users who just want the text.
        url = WIKTIONARY_URL.format(word=quote(word))
        open_wiktionary = OpenUrlAction(url)

        items = []
        for d in result[:MAX_RESULTS]:
            full = f"{word} ({d.part_of_speech}): {d.text}"
            items.append(
                ExtensionResultItem(
                    icon=ICON,
                    name=f"{word} — {d.part_of_speech}",
                    description=shorten(d.text, width=DESC_WIDTH, placeholder="…"),
                    on_enter=open_wiktionary,
                    on_alt_enter=CopyToClipboardAction(full),
                )
            )
        return RenderResultListAction(items)


if __name__ == "__main__":
    DefineExtension().run()
