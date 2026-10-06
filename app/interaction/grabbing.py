from typing import Optional, Tuple
import numpy as np
from ..simulation.component import ComponentState

class GrabController:
    """Manages pinch-to-grab attachment, translation, and release of components."""

    def __init__(self):
        self.grabbed_component_id: Optional[str] = None
        self._initial_grab_offset: Optional[np.ndarray] = None

    def try_grab(self, comp_id: Optional[str], cursor_pos_3d: Tuple[float, float, float], comp_state: Optional[ComponentState]):
        if not comp_id or not comp_state or not comp_state.metadata.removable:
            return

        self.grabbed_component_id = comp_id
        comp_state.is_grabbed = True
        cursor = np.array(cursor_pos_3d, dtype=float)
        self._initial_grab_offset = comp_state.current_position - cursor

    def update_drag(self, cursor_pos_3d: Tuple[float, float, float], comp_state: Optional[ComponentState]):
        if not self.grabbed_component_id or not comp_state or self._initial_grab_offset is None:
            return

        cursor = np.array(cursor_pos_3d, dtype=float)
        new_target = cursor + self._initial_grab_offset
        comp_state.target_position = new_target
        comp_state.is_dismantled = True

    def release(self, comp_state: Optional[ComponentState]):
        if comp_state:
            comp_state.is_grabbed = False
        self.grabbed_component_id = None
        self._initial_grab_offset = None
