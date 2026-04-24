"""Ulauncher entry point for the Define extension."""

from __future__ import annotations

from textwrap import shorten

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

from dictionary import lookup

ICON = "images/icon.png"
MAX_RESULTS = 8
DESC_WIDTH = 100  # Ulauncher visually truncates around here depending on theme


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

        items = []
        for d in result[:MAX_RESULTS]:
            full = f"{word} ({d.part_of_speech}): {d.text}"
            items.append(
                ExtensionResultItem(
                    icon=ICON,
                    name=f"{word} — {d.part_of_speech}",
                    description=shorten(d.text, width=DESC_WIDTH, placeholder="…"),
                    on_enter=CopyToClipboardAction(full),
                )
            )
        return RenderResultListAction(items)


if __name__ == "__main__":
    DefineExtension().run()
