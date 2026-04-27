# ulauncher-define

Ulauncher extension: type `def <word>` to look up English definitions inline. ~150 ms per lookup.

## Keys

**First view (definitions list):**

- `Enter` on a meaning → drill in (full definition wrapped across rows so you can read it without leaving Ulauncher)
- `Alt+Enter` → open the word's [Merriam-Webster](https://www.merriam-webster.com/) entry in your default browser

**Drill-in view:**

- `Enter` (any row) → open the word in Merriam-Webster
- `Alt+Enter` (any row) → copy the full definition to the clipboard

## Install

```bash
git clone https://github.com/anentree/ulauncher-define \
    ~/.local/share/ulauncher/extensions/ulauncher-define
# restart Ulauncher
```

Or declaratively on NixOS via home-manager — see `examples/nixos.nix` in this repo (or copy the snippet below):

```nix
{ pkgs, ... }:
let
  ulauncher-define = pkgs.fetchFromGitHub {
    owner = "anentree";
    repo = "ulauncher-define";
    rev = "v0.2.0";
    hash = "sha256-...";  # nix-prefetch-github anentree ulauncher-define --rev v0.2.0
  };
in {
  home.file.".local/share/ulauncher/extensions/ulauncher-define".source = ulauncher-define;
}
```

## Implementation notes

- Definitions powered by [Datamuse](https://www.datamuse.com/api/) (sourced from Wiktionary, ~150 ms p50, no API key, free).
- Python standard library only — no `pip install` required.
- Ulauncher's default `result_item.ui` hardcodes `ellipsize=middle` and `max-width-chars=1` on result rows; that's why long definitions can't render inline on a single row, and why the drill-in view exists.
