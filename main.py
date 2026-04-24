"""Ulauncher entry point for the Define extension."""

from __future__ import annotations

from textwrap import shorten, wrap

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

from dictionary import lookup

ICON = "images/icon.png"
MAX_RESULTS = 8
DESC_WIDTH = 100  # first-view description width
WRAP_WIDTH = 60  # chars per line in the drill-in view


def _single(name: str, description: str = "") -> RenderResultListAction:
    return RenderResultListAction(
        [ExtensionResultItem(icon=ICON, name=name, description=description)]
    )


class DefineExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


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
                    on_enter=ExtensionCustomAction(
                        {
                            "word": word,
                            "pos": d.part_of_speech,
                            "text": d.text,
                            "full": full,
                        },
                        keep_app_open=True,
                    ),
                )
            )
        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    """Drill-in view: Ulauncher's default theme ellipsizes each row to one line,
    so long definitions can't be shown inline. On Enter, replace the list with
    a wrapped multi-line view; Enter on any row copies the full definition.
    """

    def on_event(self, event, extension):
        data = event.get_data()
        full = data["full"]
        copy_action = CopyToClipboardAction(full)

        header = ExtensionResultItem(
            icon=ICON,
            name=f"{data['word']} — {data['pos']}",
            description="Press Enter to copy full definition",
            on_enter=copy_action,
        )
        body = [
            ExtensionResultItem(
                icon=ICON,
                name=line,
                description="",
                on_enter=copy_action,
            )
            for line in wrap(data["text"], width=WRAP_WIDTH)
        ]
        return RenderResultListAction([header] + body)


if __name__ == "__main__":
    DefineExtension().run()
