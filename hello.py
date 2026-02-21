#!/usr/bin/env python3

import math
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib


class HelloWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Hello World")
        self.set_default_size(600, 400)

        self._dance_tick = 0
        self._dance_timer = None
        self._follow_timer = None
        self._mouse_x = 0
        self._mouse_y = 0
        self._current_x = 0
        self._current_y = 0
        self._idle_tick = 0
        self._is_idle = False

        overlay = Gtk.Overlay()
        self.set_child(overlay)

        self._fixed = Gtk.Fixed()
        overlay.set_child(self._fixed)

        self._label = Gtk.Label(label="Hello, World!")
        self._label.add_css_class("title-1")
        self._fixed.put(self._label, 0, 0)

        css_provider = Gtk.CssProvider()
        self._css_provider = css_provider
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_mouse_move)
        self.add_controller(motion)

        button = Gtk.Button(label="Dance!")
        button.set_halign(Gtk.Align.CENTER)
        button.set_valign(Gtk.Align.END)
        button.set_margin_bottom(30)
        button.connect("clicked", self._on_dance_clicked)
        overlay.add_overlay(button)

        self.connect("notify::default-width", lambda *_: self._center_label())
        self.connect("notify::default-height", lambda *_: self._center_label())
        GLib.idle_add(self._center_label)

    def _center_label(self):
        w = self.get_width()
        h = self.get_height()
        lw = self._label.get_width() or 200
        lh = self._label.get_height() or 40
        self._base_x = (w - lw) / 2
        self._base_y = (h - lh) / 2
        self._current_x = self._base_x
        self._current_y = self._base_y
        self._mouse_x = self._base_x
        self._mouse_y = self._base_y
        self._fixed.move(self._label, self._base_x, self._base_y)
        self._start_following()

    def _on_mouse_move(self, _controller, x, y):
        lw = self._label.get_width() or 200
        lh = self._label.get_height() or 40
        self._mouse_x = x - lw / 2
        self._mouse_y = y - lh / 2

    def _start_following(self):
        if not self._follow_timer:
            self._follow_timer = GLib.timeout_add(50, self._follow_mouse)

    def _stop_following(self):
        if self._follow_timer:
            GLib.source_remove(self._follow_timer)
            self._follow_timer = None

    def _follow_mouse(self):
        if self._dance_timer:
            return True

        dx = self._mouse_x - self._current_x
        dy = self._mouse_y - self._current_y
        dist = math.hypot(dx, dy)

        # Rotate so the right side ("head") faces the cursor
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        # Move toward cursor at steady speed, stop when far enough away
        if dist > 80:
            speed = 2.5
            self._current_x += dx / dist * speed
            self._current_y += dy / dist * speed
            self._is_idle = False
            self._idle_tick = 0
            self._css_provider.load_from_string(
                f".title-1 {{ transform: rotate({angle_deg:.1f}deg); }}"
            )
        else:
            # Idle near cursor — cycle colors
            if not self._is_idle:
                self._is_idle = True
                self._idle_tick = 0
            self._idle_tick += 1
            hue = (self._idle_tick * 3.6) % 360
            self._css_provider.load_from_string(
                f".title-1 {{ transform: rotate({angle_deg:.1f}deg); color: hsl({hue:.0f}, 80%, 50%); }}"
            )

        self._fixed.move(self._label, self._current_x, self._current_y)
        return True

    def _on_dance_clicked(self, _button):
        if self._dance_timer:
            return
        self._dance_tick = 0
        self._center_label()
        self._dance_timer = GLib.timeout_add(50, self._animate)

    def _animate(self):
        self._dance_tick += 1
        t = self._dance_tick * 0.08

        offset_x = math.sin(t * 2.5) * 60
        offset_y = math.cos(t * 3.5) * 30 + math.sin(t * 1.5) * 15
        angle = math.sin(t * 2) * 12

        self._fixed.move(
            self._label,
            self._base_x + offset_x,
            self._base_y + offset_y,
        )

        hue = (self._dance_tick * 3.6) % 360
        self._css_provider.load_from_string(
            f".title-1 {{ transform: rotate({angle:.1f}deg); color: hsl({hue:.0f}, 80%, 50%); }}"
        )

        if self._dance_tick >= 100:
            self._css_provider.load_from_string(
                ".title-1 { transform: rotate(0deg); color: inherit; }"
            )
            self._current_x = self._base_x
            self._current_y = self._base_y
            self._dance_timer = None
            return False
        return True


def on_activate(app):
    window = HelloWindow(application=app)
    window.present()


def main():
    app = Gtk.Application(application_id="com.example.helloworld")
    app.connect("activate", on_activate)
    app.run()


if __name__ == "__main__":
    main()
