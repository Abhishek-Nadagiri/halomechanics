from typing import Tuple
import numpy as np

class RotationController:
    """Handles 3D model rotation from two-hand spatial vectors."""

    def __init__(self):
        # Euler angles (roll, pitch, yaw) in radians
        self.angles = np.array([0.0, 0.0, 0.0], dtype=float)
        self.angular_velocity = np.array([0.0, 0.0, 0.0], dtype=float)

    def apply_delta(self, delta_rot: Tuple[float, float, float], smoothing: float = 0.8):
        d = np.array(delta_rot, dtype=float)
        self.angular_velocity = (smoothing * self.angular_velocity) + ((1.0 - smoothing) * d)
        self.angles += self.angular_velocity

    def get_angles_deg(self) -> Tuple[float, float, float]:
        deg = np.degrees(self.angles)
        return (float(deg[0]), float(deg[1]), float(deg[2]))

    def reset(self):
        self.angles = np.array([0.0, 0.0, 0.0], dtype=float)
        self.angular_velocity = np.array([0.0, 0.0, 0.0], dtype=float)
