# asinux-settings-modules

Downloadable extras for [Asinux System Configuration](https://github.com/fbrzostowski)'s
optional-module system (`asinux-settings/` in that project).

Each module there ships a small `module.json` + `install.sh` locally, but
keeps any heavier or rarely-used code (custom settings windows, etc.) out
of the base install. That code lives here instead, one folder per module,
and gets pulled down by the module's `install.sh` only when a user
actually opts in.

## Layout

- `window-effects/window.py` — the "Window Effects" hub window: launches
  the native preferences of the Burn My Windows, Compiz Windows Effect and
  Compiz Magic Lamp Effect GNOME Shell extensions from one place.
