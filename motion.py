"""Pure calculation helpers for label motion, dance animation, and color cycling.

This module has **no GTK dependency** and is fully unit-testable.
"""

import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TICK_INTERVAL_MS = 50  # ~20 FPS
CURSOR_GAP_PX = 15  # space between label right-edge and cursor
MAX_TURN_DEG = 3.0  # max rotation per tick
MOVE_SPEED = 2.5  # pixels per tick
IDLE_THRESHOLD = 5.0  # distance below which the label is considered idle
HUE_RATE = 3.6  # degrees of hue shift per tick
DANCE_TICKS = 100  # duration of dance in ticks
DANCE_TIME_SCALE = 0.08
DANCE_AMPLITUDE_X = 60
DANCE_AMPLITUDE_Y1 = 30
DANCE_AMPLITUDE_Y2 = 15
DANCE_ROTATION_AMPLITUDE = 12


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def rotated_right_center(center_x: float, center_y: float,
                         angle_deg: float, half_width: float) -> tuple[float, float]:
    """Return the world-space position of the label's right-center after rotation."""
    rad = math.radians(angle_deg)
    return (
        center_x + math.cos(rad) * half_width,
        center_y + math.sin(rad) * half_width,
    )


def target_angle_toward(center_x: float, center_y: float,
                        mouse_x: float, mouse_y: float) -> float:
    """Return the angle (in degrees) from the label center toward the mouse."""
    return math.degrees(math.atan2(mouse_y - center_y, mouse_x - center_x))


def clamp_turn(current_angle: float, target_angle: float,
               max_turn: float = MAX_TURN_DEG) -> float:
    """Return a new angle that moves *current_angle* toward *target_angle*
    by at most *max_turn* degrees."""
    diff = (target_angle - current_angle + 180) % 360 - 180
    if abs(diff) > max_turn:
        diff = max_turn if diff > 0 else -max_turn
    return current_angle + diff


def desired_label_position(mouse_x: float, mouse_y: float,
                           angle_deg: float,
                           label_width: float, label_height: float,
                           gap: float = CURSOR_GAP_PX) -> tuple[float, float]:
    """Compute the top-left position where the label's rotated right-center
    is *gap* px before the cursor.

    This is the resting position the label converges to — the point where
    ``move_toward`` reports idle because the remaining distance is below the
    threshold.
    """
    rad = math.radians(angle_deg)
    desired_x = (mouse_x - math.cos(rad) * (label_width / 2 + gap)) - label_width / 2
    desired_y = (mouse_y - math.sin(rad) * (label_width / 2 + gap)) - label_height / 2
    return desired_x, desired_y


def move_toward(current_x: float, current_y: float,
                desired_x: float, desired_y: float,
                speed: float = MOVE_SPEED,
                threshold: float = IDLE_THRESHOLD) -> tuple[float, float, bool]:
    """Move from (current) toward (desired) at a fixed *speed*.

    Returns ``(new_x, new_y, is_idle)``.  When the remaining distance is
    within *threshold*, the position is unchanged and *is_idle* is ``True``.
    """
    dx = desired_x - current_x
    dy = desired_y - current_y
    dist = math.hypot(dx, dy)
    if dist <= threshold:
        return current_x, current_y, True
    return (
        current_x + dx / dist * speed,
        current_y + dy / dist * speed,
        False,
    )


# ---------------------------------------------------------------------------
# Dance animation
# ---------------------------------------------------------------------------


def dance_offsets(tick: int) -> tuple[float, float, float]:
    """Return ``(offset_x, offset_y, rotation_deg)`` for the given dance *tick*."""
    t = tick * DANCE_TIME_SCALE
    offset_x = math.sin(t * 2.5) * DANCE_AMPLITUDE_X
    offset_y = math.cos(t * 3.5) * DANCE_AMPLITUDE_Y1 + math.sin(t * 1.5) * DANCE_AMPLITUDE_Y2
    angle = math.sin(t * 2) * DANCE_ROTATION_AMPLITUDE
    return offset_x, offset_y, angle


# ---------------------------------------------------------------------------
# Color cycling
# ---------------------------------------------------------------------------


def rainbow_hue(tick: int, rate: float = HUE_RATE) -> float:
    """Return a hue value (0–360) cycling at *rate* degrees per tick."""
    return (tick * rate) % 360
