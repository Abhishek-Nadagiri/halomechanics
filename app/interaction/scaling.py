class ScaleController:
    """Handles model zoom and scale manipulation with smoothing and bounds clamping."""

    def __init__(self, min_scale: float = 0.35, max_scale: float = 3.0, initial_scale: float = 1.0):
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.current_scale = initial_scale
        self.target_scale = initial_scale

    def apply_scale_multiplier(self, multiplier: float):
        self.target_scale = max(self.min_scale, min(self.max_scale, self.target_scale * multiplier))

    def update(self, alpha: float = 0.2) -> float:
        self.current_scale += alpha * (self.target_scale - self.current_scale)
        return self.current_scale

    def reset(self):
        self.target_scale = 1.0
        self.current_scale = 1.0
