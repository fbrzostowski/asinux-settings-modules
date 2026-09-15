#!/usr/bin/env python3
"""Window Effects hub.

One place to reach the native preferences of the three GNOME Shell
extensions this module installs. Each extension ships its own settings UI
(Burn My Windows especially, with dozens of effect profiles) so this stays
a launcher rather than reimplementing them - it just opens the real thing.
"""
import subprocess
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk

APP_ID = "com.asinux.WindowEffectsHub"

EXTENSIONS = [
    {
        "uuid": "burn-my-windows@schneegans.github.com",
        "name": "Burn My Windows",
        "description": "Fire, glitch, portal and dozens of other open/close effects.",
        "icon": "bookmarks-organize",
    },
    {
        "uuid": "compiz-windows-effect@hermes83.github.com",
        "name": "Compiz Windows Effect",
        "description": "Classic Compiz-style wobbly windows.",
        "icon": "preferences-desktop-effects",
    },
    {
        "uuid": "compiz-alike-magic-lamp-effect@hermes83.github.com",
        "name": "Magic Lamp Effect",
        "description": "Compiz-style magic lamp minimize animation.",
        "icon": "view-restore-symbolic",
    },
]


def get_enabled_extensions():
    try:
        result = subprocess.run(
            ["gnome-extensions", "list", "--enabled"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


class WindowEffectsWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Window Effects")
        self.set_default_size(480, 360)

        self.toast_overlay = Adw.ToastOverlay()

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Window Effects", subtitle="Animated window effects"))
        toolbar_view.add_top_bar(header)

        list_box = Gtk.ListBox()
        list_box.add_css_class("boxed-list")
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)

        self.switch_handlers = {}
        enabled = get_enabled_extensions()

        for ext in EXTENSIONS:
            row = Adw.ActionRow(title=ext["name"], subtitle=ext["description"])

            icon = Gtk.Image.new_from_icon_name(ext["icon"])
            icon.set_pixel_size(28)
            row.add_prefix(icon)

            open_button = Gtk.Button(label="Settings")
            open_button.add_css_class("flat")
            open_button.set_valign(Gtk.Align.CENTER)
            open_button.connect("clicked", self.on_open_clicked, ext)
            row.add_suffix(open_button)
            row.set_activatable_widget(open_button)

            switch = Gtk.Switch()
            switch.set_valign(Gtk.Align.CENTER)
            switch.set_active(ext["uuid"] in enabled)
            handler_id = switch.connect("notify::active", self.on_toggle_extension, ext)
            self.switch_handlers[ext["uuid"]] = (switch, handler_id)
            row.add_suffix(switch)

            list_box.append(row)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(480)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)
        clamp.set_child(list_box)

        self.toast_overlay.set_child(clamp)
        toolbar_view.set_content(self.toast_overlay)
        self.set_content(toolbar_view)

    def on_toggle_extension(self, switch, _pspec, ext):
        enable = switch.get_active()
        try:
            result = subprocess.run(
                ["gnome-extensions", "enable" if enable else "disable", ext["uuid"]],
                capture_output=True, text=True, check=False,
            )
        except FileNotFoundError as err:
            self._revert_switch(ext, enable, str(err))
            return

        if result.returncode != 0:
            detail = result.stderr.strip() or f"exit code {result.returncode}"
            self._revert_switch(ext, enable, detail)

    def _revert_switch(self, ext, attempted_enable, detail):
        switch, handler_id = self.switch_handlers[ext["uuid"]]
        switch.handler_block(handler_id)
        switch.set_active(not attempted_enable)
        switch.handler_unblock(handler_id)
        verb = "enable" if attempted_enable else "disable"
        self.toast_overlay.add_toast(Adw.Toast.new(f"Couldn't {verb} {ext['name']}: {detail}"))

    def on_open_clicked(self, button, ext):
        try:
            proc = Gio.Subprocess.new(
                ["gnome-extensions", "prefs", ext["uuid"]],
                Gio.SubprocessFlags.STDERR_PIPE,
            )
        except GLib.Error as err:
            self.toast_overlay.add_toast(Adw.Toast.new(f"Couldn't open {ext['name']}: {err.message}"))
            return
        proc.communicate_utf8_async(None, None, self._on_prefs_finished, ext)

    def _on_prefs_finished(self, proc, result, ext):
        try:
            proc.communicate_utf8_finish(result)
        except GLib.Error:
            pass
        if not proc.get_successful():
            self.toast_overlay.add_toast(Adw.Toast.new(f'"{ext["name"]}" isn\'t installed yet.'))


class WindowEffectsApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = self.props.active_window
        if win is None:
            win = WindowEffectsWindow(self)
        win.present()


def main():
    app = WindowEffectsApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
