from typing import Tuple
import numpy as np

class SpatialMapper:
    """Maps 2D camera space into 3D world space.
    
    CRITICAL TECHNICAL NOTE (Prompt Sec. 56):
    A standard monocular webcam does not provide millimeter-accurate depth sensor data.
    This mapper produces an engineered 'Spatial 3D Interaction Illusion' by fusing:
    1. MediaPipe relative z-landmarks
    2. Normalized inverse palm bounding size (apparent hand size in camera frustum)
    3. Normalized viewport aspect mapping to 3D world plane [-2.0, 2.0]
    """

    def __init__(self, viewport_w: float = 4.0, viewport_h: float = 2.25, base_depth: float = 0.0):
        self.viewport_w = viewport_w
        self.viewport_h = viewport_h
        self.base_depth = base_depth

        # Reference palm scale at standard calibrated distance (~0.6m from webcam)
        self.calibrated_palm_scale = 0.18

    def screen_to_world(self, norm_x: float, norm_y: float, norm_z: float = 0.0, palm_scale: float = 0.18) -> Tuple[float, float, float]:
        """Maps normalized camera coordinates [0, 1] into 3D world coordinates.
        norm_x: 0 (left) to 1 (right)
        norm_y: 0 (top) to 1 (bottom)
        norm_z: MediaPipe raw depth relative to wrist
        palm_scale: Euclidean distance between wrist and middle MCP
        """
        # Center coordinates to origin [-0.5, 0.5]
        cx = norm_x - 0.5
        cy = 0.5 - norm_y  # Invert Y so up is +Y

        # World X and Y
        world_x = float(cx * self.viewport_w)
        world_y = float(cy * self.viewport_h)

        # Approximate World Z from palm scale and MediaPipe z
        scale_ratio = palm_scale / max(0.02, self.calibrated_palm_scale)
        # Closer hands have scale_ratio > 1.0 (towards user, +Z)
        # Farther hands have scale_ratio < 1.0 (into screen, -Z)
        depth_offset = (scale_ratio - 1.0) * 1.5 - (norm_z * 0.8)
        world_z = float(self.base_depth + depth_offset)

        return (world_x, world_y, world_z)

    def compute_ray(self, norm_x: float, norm_y: float, camera_pos: Tuple[float, float, float] = (0.0, 0.0, 3.0)) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Computes a 3D ray from the camera origin through the 2D cursor point on the near plane.
        Returns: (ray_origin, ray_direction_normalized)
        """
        target_pt = self.screen_to_world(norm_x, norm_y, 0.0)
        origin = np.array(camera_pos, dtype=float)
        target = np.array(target_pt, dtype=float)

        direction = target - origin
        norm = np.linalg.norm(direction) + 1e-6
        unit_dir = direction / norm

        return (
            (float(origin[0]), float(origin[1]), float(origin[2])),
            (float(unit_dir[0]), float(unit_dir[1]), float(unit_dir[2]))
        )
