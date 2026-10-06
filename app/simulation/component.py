from typing import List, Optional
import numpy as np
from ..models.metadata import ComponentMetadata

class ComponentState:
    """Runtime simulation state of an individual component in 3D world space."""

    def __init__(self, metadata: ComponentMetadata):
        self.metadata = metadata
        self.id = metadata.id
        self.name = metadata.name

        # Initial baseline transforms
        self.base_position = np.array(metadata.local_position, dtype=float)
        self.base_rotation = np.array(metadata.local_rotation, dtype=float)

        # Dynamic runtime transforms
        self.current_position = self.base_position.copy()
        self.current_rotation = self.base_rotation.copy()
        self.target_position = self.base_position.copy()
        self.target_rotation = self.base_rotation.copy()

        # Interaction flags
        self.is_selected = False
        self.is_grabbed = False
        self.is_dismantled = False
        self.highlight_glow = 0.0  # 0.0 to 1.0

    def update_lerp(self, alpha: float = 0.15):
        """Smoothly interpolates current transforms towards target transforms."""
        self.current_position += alpha * (self.target_position - self.current_position)
        self.current_rotation += alpha * (self.target_rotation - self.current_rotation)

    def reset_transform(self):
        """Restores component to its original factory position."""
        self.target_position = self.base_position.copy()
        self.target_rotation = self.base_rotation.copy()
        self.is_dismantled = False
        self.is_grabbed = False
        self.is_selected = False
