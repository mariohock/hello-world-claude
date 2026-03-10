"""Unit tests for the pure calculation helpers in hello.py.

These tests exercise the math extracted from the GUI class and can run
without a display server or GTK installation.
"""

import math

import pytest

from motion import (
    CURSOR_GAP_PX,
    DANCE_AMPLITUDE_X,
    DANCE_AMPLITUDE_Y1,
    DANCE_AMPLITUDE_Y2,
    DANCE_ROTATION_AMPLITUDE,
    DANCE_TIME_SCALE,
    HUE_RATE,
    IDLE_THRESHOLD,
    MAX_TURN_DEG,
    MOVE_SPEED,
    clamp_turn,
    dance_offsets,
    desired_label_position,
    move_toward,
    rainbow_hue,
    rotated_right_center,
    target_angle_toward,
)


# ---------------------------------------------------------------------------
# rotated_right_center
# ---------------------------------------------------------------------------


class TestRotatedRightCenter:
    def test_zero_angle(self):
        """At 0° the right-center is directly to the right of the center."""
        rx, ry = rotated_right_center(100, 100, 0, 50)
        assert rx == pytest.approx(150)
        assert ry == pytest.approx(100)

    def test_90_degrees(self):
        """At 90° the right-center is directly below the center."""
        rx, ry = rotated_right_center(100, 100, 90, 50)
        assert rx == pytest.approx(100, abs=1e-10)
        assert ry == pytest.approx(150)

    def test_180_degrees(self):
        """At 180° the right-center is directly to the left."""
        rx, ry = rotated_right_center(100, 100, 180, 50)
        assert rx == pytest.approx(50)
        assert ry == pytest.approx(100, abs=1e-10)

    def test_arbitrary_angle(self):
        """Sanity-check: result lies on a circle of radius half_width."""
        cx, cy, hw = 200, 150, 60
        for angle in [30, 45, 135, 270, -45]:
            rx, ry = rotated_right_center(cx, cy, angle, hw)
            dist = math.hypot(rx - cx, ry - cy)
            assert dist == pytest.approx(hw)


# ---------------------------------------------------------------------------
# target_angle_toward
# ---------------------------------------------------------------------------


class TestTargetAngleToward:
    def test_right(self):
        assert target_angle_toward(0, 0, 10, 0) == pytest.approx(0)

    def test_down(self):
        assert target_angle_toward(0, 0, 0, 10) == pytest.approx(90)

    def test_left(self):
        assert target_angle_toward(0, 0, -10, 0) == pytest.approx(180)

    def test_up(self):
        assert target_angle_toward(0, 0, 0, -10) == pytest.approx(-90)


# ---------------------------------------------------------------------------
# clamp_turn
# ---------------------------------------------------------------------------


class TestClampTurn:
    def test_within_limit(self):
        """Small turns are applied exactly."""
        assert clamp_turn(10, 12) == pytest.approx(12)

    def test_clamped_positive(self):
        """Large positive turns are clamped to MAX_TURN_DEG."""
        result = clamp_turn(0, 90)
        assert result == pytest.approx(MAX_TURN_DEG)

    def test_clamped_negative(self):
        """Large negative turns are clamped to -MAX_TURN_DEG."""
        result = clamp_turn(0, -90)
        assert result == pytest.approx(-MAX_TURN_DEG)

    def test_wrap_around(self):
        """Handles the 360°→0° boundary correctly."""
        # From 359° toward 1°: shortest path is +2°, within limit.
        result = clamp_turn(359, 1)
        assert result == pytest.approx(361)  # 359 + 2

    def test_wrap_around_negative(self):
        """From 1° toward 359°: shortest path is -2°."""
        result = clamp_turn(1, 359)
        assert result == pytest.approx(-1)


# ---------------------------------------------------------------------------
# desired_label_position — the "where text stops" calculation
# ---------------------------------------------------------------------------


class TestDesiredLabelPosition:
    """Tests for the resting position calculation.

    When the label reaches this position, ``move_toward`` reports idle and
    the label stops moving.  The invariant is:

        The rotated right-center of the label at the desired position
        should be exactly ``gap`` pixels away from the cursor, measured
        along the label's aiming direction.
    """

    LABEL_W = 200
    LABEL_H = 40

    def _verify_gap(self, mouse_x, mouse_y, angle_deg, gap=CURSOR_GAP_PX):
        """Assert that the right-center of the label at the desired position
        is exactly *gap* px from the cursor along the aiming direction."""
        dx, dy = desired_label_position(
            mouse_x, mouse_y, angle_deg,
            self.LABEL_W, self.LABEL_H, gap,
        )
        # Reconstruct label center from top-left
        cx = dx + self.LABEL_W / 2
        cy = dy + self.LABEL_H / 2

        # Rotated right-center
        rx, ry = rotated_right_center(cx, cy, angle_deg, self.LABEL_W / 2)

        # The vector from right-center to cursor should have length == gap
        dist = math.hypot(mouse_x - rx, mouse_y - ry)
        assert dist == pytest.approx(gap), (
            f"Expected gap={gap}, got {dist:.4f} "
            f"(mouse=({mouse_x},{mouse_y}), angle={angle_deg}°)"
        )

    def test_straight_right(self):
        """Cursor directly to the right; angle 0°."""
        self._verify_gap(400, 200, 0)

    def test_straight_down(self):
        """Cursor directly below; angle 90°."""
        self._verify_gap(300, 400, 90)

    def test_diagonal(self):
        """Cursor at 45°."""
        self._verify_gap(500, 500, 45)

    def test_negative_angle(self):
        """Cursor above and to the right; angle -30°."""
        self._verify_gap(400, 100, -30)

    def test_various_angles(self):
        """Sweep through many angles to verify the gap invariant."""
        for angle in range(0, 360, 15):
            self._verify_gap(300, 300, angle)

    def test_custom_gap(self):
        """The gap parameter is respected."""
        self._verify_gap(400, 200, 0, gap=30)

    def test_label_stops_at_desired_position(self):
        """Simulate convergence: run move_toward until idle, then check
        that the resting position matches desired_label_position."""
        mouse_x, mouse_y = 400, 250
        angle_deg = 20.0
        lw, lh = self.LABEL_W, self.LABEL_H

        desired_x, desired_y = desired_label_position(
            mouse_x, mouse_y, angle_deg, lw, lh,
        )

        # Start far away and iterate
        cx, cy = 50.0, 50.0
        for _ in range(10_000):
            cx, cy, idle = move_toward(cx, cy, desired_x, desired_y)
            if idle:
                break

        # After convergence, verify the gap to cursor
        label_cx = cx + lw / 2
        label_cy = cy + lh / 2
        rx, ry = rotated_right_center(label_cx, label_cy, angle_deg, lw / 2)
        dist = math.hypot(mouse_x - rx, mouse_y - ry)
        assert dist == pytest.approx(CURSOR_GAP_PX, abs=IDLE_THRESHOLD)


# ---------------------------------------------------------------------------
# move_toward
# ---------------------------------------------------------------------------


class TestMoveToward:
    def test_idle_when_close(self):
        """Returns idle=True when already within threshold."""
        nx, ny, idle = move_toward(100, 100, 103, 100)
        assert idle is True
        assert nx == 100
        assert ny == 100

    def test_moves_at_fixed_speed(self):
        """Moves exactly MOVE_SPEED pixels per call."""
        nx, ny, idle = move_toward(0, 0, 100, 0)
        assert idle is False
        assert nx == pytest.approx(MOVE_SPEED)
        assert ny == pytest.approx(0)

    def test_diagonal_speed(self):
        """Speed is constant regardless of direction."""
        nx, ny, idle = move_toward(0, 0, 100, 100)
        dist = math.hypot(nx, ny)
        assert dist == pytest.approx(MOVE_SPEED)

    def test_exact_threshold_is_idle(self):
        """At exactly the threshold distance, the label is idle."""
        _, _, idle = move_toward(0, 0, IDLE_THRESHOLD, 0)
        assert idle is True

    def test_converges(self):
        """Repeated calls converge to within threshold of the target."""
        x, y = 0.0, 0.0
        target_x, target_y = 200.0, 150.0
        for _ in range(10_000):
            x, y, idle = move_toward(x, y, target_x, target_y)
            if idle:
                break
        assert math.hypot(target_x - x, target_y - y) <= IDLE_THRESHOLD


# ---------------------------------------------------------------------------
# dance_offsets
# ---------------------------------------------------------------------------


class TestDanceOffsets:
    def test_tick_zero_gives_zero(self):
        """At tick 0 all offsets are zero (sin(0) = 0, cos(0) = 1 for Y)."""
        ox, oy, angle = dance_offsets(0)
        assert ox == pytest.approx(0)
        # oy = cos(0)*30 + sin(0)*15 = 30
        assert oy == pytest.approx(DANCE_AMPLITUDE_Y1)
        assert angle == pytest.approx(0)

    def test_offsets_bounded(self):
        """Offsets never exceed their amplitude constants."""
        for tick in range(1, 200):
            ox, oy, angle = dance_offsets(tick)
            assert abs(ox) <= DANCE_AMPLITUDE_X + 0.01
            assert abs(oy) <= DANCE_AMPLITUDE_Y1 + DANCE_AMPLITUDE_Y2 + 0.01
            assert abs(angle) <= DANCE_ROTATION_AMPLITUDE + 0.01

    def test_deterministic(self):
        """Same tick always produces the same result."""
        assert dance_offsets(42) == dance_offsets(42)


# ---------------------------------------------------------------------------
# rainbow_hue
# ---------------------------------------------------------------------------


class TestRainbowHue:
    def test_zero(self):
        assert rainbow_hue(0) == 0

    def test_wraps(self):
        assert rainbow_hue(100) == pytest.approx((100 * HUE_RATE) % 360)

    def test_always_in_range(self):
        for tick in range(500):
            assert 0 <= rainbow_hue(tick) < 360
