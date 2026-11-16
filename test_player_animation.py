"""Testes da interpolação de movimento dos avatares."""

import unittest

from player_animation import PlayerAnimator


class PlayerAnimatorTests(unittest.TestCase):
    def test_stationary_player_uses_logical_position(self):
        animator = PlayerAnimator()
        self.assertEqual(animator.visual_state(0, (2, 3), 100), (2.0, 3.0, 0.0, 0.0))

    def test_midpoint_uses_smooth_interpolation(self):
        animator = PlayerAnimator(duration_ms=400)
        animator.start_move(0, (0, 0), (0, 1), 1000)
        row, col, angle, swing = animator.visual_state(0, (0, 1), 1200)
        self.assertAlmostEqual(row, 0.0)
        self.assertAlmostEqual(col, 0.5)
        self.assertAlmostEqual(angle, 90.0)
        self.assertAlmostEqual(swing, 0.0, places=6)

    def test_animation_finishes_at_destination(self):
        animator = PlayerAnimator(duration_ms=300)
        animator.start_move(1, (5, 5), (4, 5), 200)
        state = animator.visual_state(1, (4, 5), 500)
        self.assertEqual(state[:3], (4.0, 5.0, 180.0))
        self.assertEqual(state[3], 0.0)
        self.assertFalse(animator.is_active(500))

    def test_each_direction_sets_expected_facing_angle(self):
        cases = {
            (-1, 0): 180.0,
            (1, 0): 0.0,
            (0, -1): -90.0,
            (0, 1): 90.0,
        }
        for destination_delta, expected_angle in cases.items():
            animator = PlayerAnimator()
            destination = destination_delta
            animator.start_move(0, (0, 0), destination, 0)
            state = animator.visual_state(0, destination, 1)
            self.assertEqual(state[2], expected_angle)


if __name__ == "__main__":
    unittest.main(verbosity=2)
