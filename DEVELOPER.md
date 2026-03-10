# Hello World Claude — Developer Guide

## Overview

A GTK4 "Hello, World!" application written in Python that goes well beyond a static label. The text is alive: it **follows the mouse cursor**, **dances** on command, and **cycles through rainbow colors** when idle.

## Architecture

The app is split into two modules:

- **`hello.py`** — GTK4 GUI layer. Contains `HelloWindow` (the main window class), the `FollowState` dataclass for mutable animation state, and CSS helper functions.
- **`motion.py`** — Pure calculation helpers with **no GTK dependency**. All geometry, movement, dance, and color-cycling math lives here, making it fully unit-testable without a display server.

### Widget Hierarchy

```
Gtk.ApplicationWindow (HelloWindow)
└── Gtk.Overlay
    ├── Gtk.Fixed          ← positions the label freely on a canvas
    │   └── Gtk.Label      ← "Hello, World!" text
    └── Gtk.Button          ← "Dance!" button (overlay, bottom-center)
```

- **`Gtk.Fixed`** allows absolute pixel positioning of the label, which is essential for the smooth-follow and dance animations.
- **`Gtk.Overlay`** layers the button on top of the fixed canvas so it stays anchored at the bottom.

### Timer-Driven Animation

GTK4 has no built-in animation loop. Instead, the app uses **`GLib.timeout_add(50, callback)`** to create ~20 FPS timer ticks:

| Timer | Field | Purpose |
|-------|-------|---------|
| Follow timer | `_follow_timer` | Runs continuously. Each tick moves the label toward the cursor. |
| Dance timer | `_dance_timer` | Active only during dance. Overrides follow behavior for 100 ticks (~5 s). |

When the dance timer is active, the follow timer's callback exits early (`return True` without moving).

## Core Algorithms

### 1. Mouse-Following (`_follow_mouse` → helpers in `motion.py`)

The label "aims" its right edge at the cursor, then moves toward a target position that keeps a 15 px gap. The GUI method `_follow_mouse` in `hello.py` orchestrates the tick, calling pure functions from `motion.py` for each step:

1. **Compute label center** from current top-left position stored in `FollowState`.
2. **Compute target angle** via `target_angle_toward()`, then **clamp the turn** to ±3°/tick via `clamp_turn()` for smooth rotation.
3. **Compute desired position** via `desired_label_position()` — where the label's top-left must be so that its rotated right-center lands 15 px before the cursor:
   ```
   desired_center = cursor - direction * (label_width/2 + gap)
   desired_top_left = desired_center - (label_width/2, label_height/2)
   ```
   Note: both axes use `label_width/2` in the rotation term (the radius from center to right-edge is always half the width). The `label_height/2` only appears in the center-to-top-left conversion.
4. **Move toward desired position** via `move_toward()` at a fixed speed of 2.5 px/tick. If within 5 px, consider the label "idle."

### 2. Idle Color Cycling (`rainbow_hue()` in `motion.py`)

When the label is within 5 px of its target (idle), it cycles through HSL hues at 3.6° per tick via `rainbow_hue()`, producing a smooth rainbow effect.

### 3. Dance Animation (`_animate` → `dance_offsets()` in `motion.py`)

Triggered by clicking "Dance!". For 100 ticks:
- **X offset**: `sin(t * 2.5) * 60` — horizontal sway
- **Y offset**: `cos(t * 3.5) * 30 + sin(t * 1.5) * 15` — vertical bounce (two overlapping waves)
- **Rotation**: `sin(t * 2) * 12` degrees — gentle rocking
- **Color**: same rainbow HSL cycling as idle mode

After 100 ticks, the label resets to center with no rotation and default color.

## CSS Transforms

GTK4's CSS engine applies `transform: rotate(...)` and `color: hsl(...)` to the label. The app dynamically overwrites a `CssProvider` each tick with updated values. `transform-origin: center` ensures rotation pivots around the label center.

## Entry Point

```
main() → Gtk.Application → on_activate() → HelloWindow → window.present()
```

Standard GTK4 application lifecycle. No command-line arguments are processed.

## Dependencies

- **Python 3**
- **PyGObject** (`gi`) with GTK 4.0

## Running

```bash
./hello.py
# or
python3 hello.py
```

## Testing

Tests live in `test_hello.py` and cover the pure calculation functions in `motion.py`. Since `motion.py` has no GTK dependency, tests can run without a display server. Run with:

```bash
python3 -m pytest test_hello.py -v
```
