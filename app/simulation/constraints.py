from typing import Tuple, List
import numpy as np

class Constraint:
    """Base class for kinematic constraints preventing random floating motion."""
    def apply_translation(self, current_pos: np.ndarray, delta: np.ndarray) -> np.ndarray:
        return current_pos + delta

    def apply_rotation(self, current_rot: np.ndarray, delta: np.ndarray) -> np.ndarray:
        return current_rot + delta


class FixedConstraint(Constraint):
    """Component cannot be moved or rotated relative to parent (structural mount)."""
    def apply_translation(self, current_pos: np.ndarray, delta: np.ndarray) -> np.ndarray:
        return current_pos

    def apply_rotation(self, current_rot: np.ndarray, delta: np.ndarray) -> np.ndarray:
        return current_rot


class HingeConstraint(Constraint):
    """Component rotates around a fixed axis within min and max angular bounds."""
    def __init__(self, axis: Tuple[float, float, float] = (0.0, 1.0, 0.0), min_deg: float = 0.0, max_deg: float = 90.0):
        self.axis = np.array(axis, dtype=float)
        self.axis /= (np.linalg.norm(self.axis) + 1e-6)
        self.min_rad = np.radians(min_deg)
        self.max_rad = np.radians(max_deg)
        self.current_rad = 0.0

    def apply_rotation(self, current_rot: np.ndarray, delta: np.ndarray) -> np.ndarray:
        rot_amount = float(np.dot(delta, self.axis))
        new_rad = np.clip(self.current_rad + rot_amount, self.min_rad, self.max_rad)
        actual_delta = new_rad - self.current_rad
        self.current_rad = new_rad
        return current_rot + (self.axis * actual_delta)


class SliderConstraint(Constraint):
    """Component translates linearly along a specific axis within stroke bounds (e.g. piston)."""
    def __init__(self, axis: Tuple[float, float, float] = (0.0, 1.0, 0.0), min_dist: float = -0.5, max_dist: float = 0.5):
        self.axis = np.array(axis, dtype=float)
        self.axis /= (np.linalg.norm(self.axis) + 1e-6)
        self.min_dist = min_dist
        self.max_dist = max_dist
        self.current_dist = 0.0

    def apply_translation(self, current_pos: np.ndarray, delta: np.ndarray) -> np.ndarray:
        proj = float(np.dot(delta, self.axis))
        new_dist = np.clip(self.current_dist + proj, self.min_dist, self.max_dist)
        actual_delta = new_dist - self.current_dist
        self.current_dist = new_dist
        return current_pos + (self.axis * actual_delta)


class RotationalConstraint(Constraint):
    """Continuous rotation around a shaft axle (e.g. crankshaft, wheel, gears)."""
    def __init__(self, axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)):
        self.axis = np.array(axis, dtype=float)
        self.axis /= (np.linalg.norm(self.axis) + 1e-6)

    def apply_rotation(self, current_rot: np.ndarray, delta: np.ndarray) -> np.ndarray:
        proj = float(np.dot(delta, self.axis))
        return current_rot + (self.axis * proj)
