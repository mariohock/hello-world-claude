#!/usr/bin/env python3
"""Interactive 'Hello, World!' GTK4 application with mouse-following and dance animation."""

from dataclasses import dataclass

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

from motion import (
    DANCE_TICKS,
    TICK_INTERVAL_MS,
    clamp_turn,
    dance_offsets,
    desired_label_position,
    move_toward,
    rainbow_hue,
    target_angle_toward,
)

# ---------------------------------------------------------------------------
# Constants (GUI-specific)
# ---------------------------------------------------------------------------

DEFAULT_LABEL_WIDTH = 200
DEFAULT_LABEL_HEIGHT = 40
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400

CSS_CLASS = "title-1"


# ---------------------------------------------------------------------------
# CSS helpers
# ---------------------------------------------------------------------------


def _rotation_css(angle_deg: float) -> str:
    return (
        f".{CSS_CLASS} {{ transform-origin: center;"
        f" transform: rotate({angle_deg:.1f}deg); }}"
    )


def _rotation_color_css(angle_deg: float, hue: float) -> str:
    return (
        f".{CSS_CLASS} {{ transform-origin: center;"
        f" transform: rotate({angle_deg:.1f}deg);"
        f" color: hsl({hue:.0f}, 80%, 50%); }}"
    )


def _reset_css() -> str:
    return f".{CSS_CLASS} {{ transform-origin: center; transform: rotate(0deg); color: inherit; }}"


# ---------------------------------------------------------------------------
# Follow-state container
# ---------------------------------------------------------------------------


@dataclass
class FollowState:
    """Mutable state for the mouse-following behaviour."""

    current_x: float = 0.0
    current_y: float = 0.0
    current_angle: float = 0.0
    mouse_x: float = 0.0
    mouse_y: float = 0.0
    base_x: float = 0.0
    base_y: float = 0.0
    idle_tick: int = 0
    is_idle: bool = False


# ---------------------------------------------------------------------------
# GTK window
# ---------------------------------------------------------------------------


class HelloWindow(Gtk.ApplicationWindow):
    """Main application window with mouse-following label and dance animation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Hello World")
        self.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._state = FollowState()
        self._dance_tick = 0
        self._dance_timer = None
        self._follow_timer = None

        self._build_ui()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self):
        overlay = Gtk.Overlay()
        self.set_child(overlay)

        self._fixed = Gtk.Fixed()
        overlay.set_child(self._fixed)

        self._label = Gtk.Label(label="Hello, World!")
        self._label.add_css_class(CSS_CLASS)
        self._fixed.put(self._label, 0, 0)

        self._css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_mouse_move)
        self._fixed.add_controller(motion)

        button = Gtk.Button(label="Dance!")
        button.set_halign(Gtk.Align.CENTER)
        button.set_valign(Gtk.Align.END)
        button.set_margin_bottom(30)
        button.connect("clicked", self._on_dance_clicked)
        overlay.add_overlay(button)

        self.connect("notify::default-width", lambda *_: self._center_label())
        self.connect("notify::default-height", lambda *_: self._center_label())
        GLib.idle_add(self._center_label)

    # -- Label geometry helpers ---------------------------------------------

    def _label_size(self) -> tuple[float, float]:
        return (
            self._label.get_width() or DEFAULT_LABEL_WIDTH,
            self._label.get_height() or DEFAULT_LABEL_HEIGHT,
        )

    def _center_label(self):
        w = self.get_width()
        h = self.get_height()
        lw, lh = self._label_size()

        self._state.base_x = (w - lw) / 2
        self._state.base_y = (h - lh) / 2
        self._state.current_x = self._state.base_x
        self._state.current_y = self._state.base_y
        self._state.mouse_x = self._state.base_x
        self._state.mouse_y = self._state.base_y
        self._fixed.move(self._label, self._state.base_x, self._state.base_y)
        self._start_following()

    # -- Mouse tracking -----------------------------------------------------

    def _on_mouse_move(self, _controller, x, y):
        self._state.mouse_x = x
        self._state.mouse_y = y

    # -- Follow timer -------------------------------------------------------

    def _start_following(self):
        if not self._follow_timer:
            self._follow_timer = GLib.timeout_add(TICK_INTERVAL_MS, self._follow_mouse)

    def _stop_following(self):
        if self._follow_timer:
            GLib.source_remove(self._follow_timer)
            self._follow_timer = None

    def _follow_mouse(self) -> bool:
        if self._dance_timer:
            return True  # dance takes priority

        s = self._state
        lw, lh = self._label_size()

        center_x = s.current_x + lw / 2
        center_y = s.current_y + lh / 2

        # Turn toward mouse
        target = target_angle_toward(center_x, center_y, s.mouse_x, s.mouse_y)
        s.current_angle = clamp_turn(s.current_angle, target)

        # Desired resting position
        desired_x, desired_y = desired_label_position(
            s.mouse_x, s.mouse_y, s.current_angle, lw, lh,
        )

        # Move toward it
        new_x, new_y, idle = move_toward(s.current_x, s.current_y, desired_x, desired_y)
        s.current_x = new_x
        s.current_y = new_y

        if idle:
            if not s.is_idle:
                s.is_idle = True
                s.idle_tick = 0
            s.idle_tick += 1
            hue = rainbow_hue(s.idle_tick)
            self._css_provider.load_from_string(
                _rotation_color_css(s.current_angle, hue),
            )
        else:
            s.is_idle = False
            s.idle_tick = 0
            self._css_provider.load_from_string(
                _rotation_css(s.current_angle),
            )

        self._fixed.move(self._label, s.current_x, s.current_y)
        return True

    # -- Dance animation ----------------------------------------------------

    def _on_dance_clicked(self, _button):
        if self._dance_timer:
            return
        self._dance_tick = 0
        self._center_label()
        self._dance_timer = GLib.timeout_add(TICK_INTERVAL_MS, self._animate)

    def _animate(self) -> bool:
        self._dance_tick += 1
        offset_x, offset_y, angle = dance_offsets(self._dance_tick)

        self._fixed.move(
            self._label,
            self._state.base_x + offset_x,
            self._state.base_y + offset_y,
        )

        hue = rainbow_hue(self._dance_tick)
        self._css_provider.load_from_string(_rotation_color_css(angle, hue))

        if self._dance_tick >= DANCE_TICKS:
            self._css_provider.load_from_string(_reset_css())
            self._state.current_x = self._state.base_x
            self._state.current_y = self._state.base_y
            self._dance_timer = None
            return False
        return True


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------


def on_activate(app):
    window = HelloWindow(application=app)
    window.present()


def main():
    app = Gtk.Application(application_id="com.example.helloworld")
    app.connect("activate", on_activate)
    app.run()


if __name__ == "__main__":
    main()
