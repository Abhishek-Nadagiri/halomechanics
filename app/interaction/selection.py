from typing import List, Optional, Tuple, Dict
import numpy as np
from ..simulation.component import ComponentState

class RaycastSelector:
    """Detects component selection via 3D raycasting and cursor proximity."""

    def __init__(self, hit_radius: float = 0.45):
        self.hit_radius = hit_radius
        self.hovered_component_id: Optional[str] = None
        self.selected_component_id: Optional[str] = None

    def find_intersected_component(
        self,
        ray_origin: Tuple[float, float, float],
        ray_dir: Tuple[float, float, float],
        components: Dict[str, ComponentState]
    ) -> Optional[str]:
        """Calculates distance from ray to bounding sphere of each component."""
        o = np.array(ray_origin, dtype=float)
        d = np.array(ray_dir, dtype=float)
        d /= (np.linalg.norm(d) + 1e-6)

        closest_id = None
        min_dist_along_ray = float("inf")

        for comp_id, state in components.items():
            pos = state.current_position
            # Vector from ray origin to component center
            oc = pos - o
            # Projection along ray
            t = np.dot(oc, d)
            if t < 0:
                continue  # Behind camera

            # Perpendicular distance from ray to component center
            closest_pt_on_ray = o + (t * d)
            perp_dist = np.linalg.norm(pos - closest_pt_on_ray)

            if perp_dist <= self.hit_radius and t < min_dist_along_ray:
                min_dist_along_ray = t
                closest_id = comp_id

        self.hovered_component_id = closest_id
        return closest_id

    def select(self, comp_id: Optional[str]):
        """Sets active selection and updates highlight glow on components."""
        self.selected_component_id = comp_id
