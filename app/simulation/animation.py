import time
import numpy as np

def ease_out_cubic(x: float) -> float:
    """Cubic ease-out curve for smooth deceleration."""
    x = max(0.0, min(1.0, x))
    return 1.0 - pow(1.0 - x, 3)

def ease_in_out_quad(x: float) -> float:
    """Quadratic ease-in-out curve."""
    x = max(0.0, min(1.0, x))
    return 2.0 * x * x if x < 0.5 else 1.0 - pow(-2.0 * x + 2.0, 2) / 2.0

class AnimationController:
    """Controls time-based state transitions like explosion and reassembly."""

    def __init__(self, duration_sec: float = 1.2):
        self.duration_sec = duration_sec
        self.start_time = 0.0
        self.start_value = 0.0
        self.target_value = 0.0
        self.current_value = 0.0
        self.is_animating = False

    def animate_to(self, target: float):
        self.start_time = time.time()
        self.start_value = self.current_value
        self.target_value = target
        self.is_animating = True

    def update(self) -> float:
        if not self.is_animating:
            return self.current_value

        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / max(1e-4, self.duration_sec))
        eased = ease_out_cubic(progress)

        self.current_value = self.start_value + (self.target_value - self.start_value) * eased

        if progress >= 1.0:
            self.current_value = self.target_value
            self.is_animating = False

        return self.current_value
