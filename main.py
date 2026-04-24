"""Ulauncher entry point for the Define extension."""

from __future__ import annotations

from textwrap import shorten, wrap
from urllib.parse import quote

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

from dictionary import lookup

ICON = "images/icon.png"
MAX_RESULTS = 8
DESC_WIDTH = 100
# Visible width of a result-item `name` field is ~32–34 chars in the default
# Ulauncher theme before GTK middle-ellipsis kicks in (themes can't override
# the ellipsize/max-width-chars attrs set in result_item.ui). Wrap well under
# that to guarantee no truncation in the drill-in view.
WRAP_WIDTH = 32
DICTIONARY_URL = "https://www.merriam-webster.com/dictionary/{word}"


def _single(name: str, description: str = "") -> RenderResultListAction:
    return RenderResultListAction(
        [ExtensionResultItem(icon=ICON, name=name, description=description)]
    )


def _browser_action(word: str) -> OpenUrlAction:
    return OpenUrlAction(DICTIONARY_URL.format(word=quote(word)))


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
                    on_alt_enter=_browser_action(word),
                )
            )
        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    """Drill-in view. Ulauncher's default result_item.ui hardcodes ellipsize=middle
    and max-width-chars=1 on item labels, so long text can't render inline on a
    single row. We wrap the full definition across multiple rows so it's readable
    without leaving Ulauncher.
    """

    def on_event(self, event, extension):
        data = event.get_data()
        word = data["word"]
        full = data["full"]
        copy = CopyToClipboardAction(full)
        browser = _browser_action(word)

        header = ExtensionResultItem(
            icon=ICON,
            name=f"{word} — {data['pos']}",
            description="Enter: copy · Alt+Enter: browser",
            on_enter=copy,
            on_alt_enter=browser,
        )
        body = [
            ExtensionResultItem(
                icon=ICON,
                name=line,
                description="",
                on_enter=copy,
                on_alt_enter=browser,
            )
            for line in wrap(full, width=WRAP_WIDTH)
        ]
        return RenderResultListAction([header] + body)


if __name__ == "__main__":
    DefineExtension().run()
