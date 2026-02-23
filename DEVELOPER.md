# Hello World Claude — Developer Guide

## Overview

A GTK4 "Hello, World!" application written in Python that goes well beyond a static label. The text is alive: it **follows the mouse cursor**, **dances** on command, and **cycles through rainbow colors** when idle.

## Architecture

The app is a single file (`hello.py`) built on **GTK4** via PyGObject (`gi`). All logic lives in one class, `HelloWindow`, which extends `Gtk.ApplicationWindow`.

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

### 1. Mouse-Following (`_follow_mouse`)

The label "aims" its right edge at the cursor, then moves toward a target position that keeps a 15 px gap. The algorithm per tick:

1. **Compute label center** from current top-left position (`_current_x`, `_current_y`).
2. **Compute the rotated right-center** — the point at the middle of the label's right edge after rotation:
   ```
   right_center = center + (cos(angle), sin(angle)) * label_width / 2
   ```
3. **Compute target angle** from label center to mouse, then **clamp the turn** to ±3° per tick for smooth rotation.
4. **Compute desired position** — where the label's top-left must be so that its rotated right-center lands 15 px before the cursor:
   ```
   desired_center = cursor - direction * (label_width/2 + gap)
   desired_top_left = desired_center - (label_width/2, label_height/2)
   ```
5. **Move toward desired position** at a fixed speed of 2.5 px/tick. If within 5 px, consider the label "idle."

### 2. Idle Color Cycling

When the label is within 5 px of its target (idle), it cycles through HSL hues at 3.6° per tick, producing a smooth rainbow effect.

### 3. Dance Animation (`_animate`)

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

Tests live in `test_hello.py` and cover the pure calculation functions extracted from the GUI class. Run with:

```bash
python3 -m pytest test_hello.py -v
```
