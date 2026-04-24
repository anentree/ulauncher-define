# ulauncher-define

Ulauncher extension: type `def <word>` to see English definitions inline.

- **Enter** on a result drills into that meaning — the full definition is wrapped across multiple rows so you can read it inline (Ulauncher's default theme ellipsizes each row to one line, so this is the only way to surface long definitions inside Ulauncher itself).
- **Alt+Enter** opens the word's [Merriam-Webster](https://www.merriam-webster.com/) entry in your default browser.
- In the drill-in view, **Enter** copies the full definition to the clipboard; **Alt+Enter** also opens Merriam-Webster.

## Install

```bash
git clone https://github.com/anentree/ulauncher-define ~/.local/share/ulauncher/extensions/ulauncher-define
# restart ulauncher
```

Definitions powered by the free [Dictionary API](https://dictionaryapi.dev/). The extension uses only the Python standard library — no `pip install` required.
