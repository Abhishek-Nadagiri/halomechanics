from typing import Dict, Optional, Tuple, Any
from ..vision.gesture_engine import GestureResult
from ..simulation.component import ComponentState
from ..models.hierarchy import ModelHierarchy
from .selection import RaycastSelector
from .grabbing import GrabController
from .rotation import RotationController
from .scaling import ScaleController
from .dismantling import DismantlingController

class ManipulationManager:
    """Central orchestrator coordinating gestures with 3D component manipulation."""

    def __init__(self, hierarchy: ModelHierarchy):
        self.hierarchy = hierarchy
        self.selector = RaycastSelector()
        self.grabber = GrabController()
        self.rotator = RotationController()
        self.scaler = ScaleController()
        self.dismantler = DismantlingController(hierarchy)

    def process_gesture(
        self,
        gesture: GestureResult,
        components: Dict[str, ComponentState],
        ray_origin: Tuple[float, float, float],
        ray_dir: Tuple[float, float, float],
        world_cursor: Tuple[float, float, float]
    ):
        """Dispatches gesture commands to appropriate interaction subsystems."""
        # 1. Update Continuous Explosions
        self.dismantler.update(components)

        # 2. Component Selection (when pointing or idle hovering)
        if gesture.primary_gesture in ("POINT", "OPEN_PALM", "IDLE"):
            hit_id = self.selector.find_intersected_component(ray_origin, ray_dir, components)
            if gesture.primary_gesture == "POINT" and hit_id:
                self.selector.select(hit_id)

        # 3. Component Grabbing & Dragging (Pinch)
        selected_id = self.selector.selected_component_id
        if gesture.primary_gesture in ("PINCH", "POINT_PINCH"):
            if not self.grabber.grabbed_component_id and selected_id:
                comp_state = components.get(selected_id)
                self.grabber.try_grab(selected_id, world_cursor, comp_state)
                self.dismantler.record_manual_dismantle(selected_id)
            elif self.grabber.grabbed_component_id:
                comp_state = components.get(self.grabber.grabbed_component_id)
                self.grabber.update_drag(world_cursor, comp_state)
        else:
            # Release grab on non-pinch
            if self.grabber.grabbed_component_id:
                comp_state = components.get(self.grabber.grabbed_component_id)
                self.grabber.release(comp_state)

        # 4. Two-Hand Rotation
        if gesture.two_hand_gesture == "TWO_HAND_ROTATE" and gesture.rotation_delta:
            self.rotator.apply_delta(gesture.rotation_delta)

        # 5. Two-Hand Scaling / Zoom
        if gesture.two_hand_gesture == "TWO_HAND_PINCH" and gesture.scale_delta != 1.0:
            self.scaler.apply_scale_multiplier(gesture.scale_delta)

        # 6. Exploded View (Pull Apart after hold completion)
        if gesture.two_hand_gesture == "PULL_APART":
            self.dismantler.trigger_exploded_view()

        # 7. Reassembly (Push Together)
        if gesture.two_hand_gesture == "PUSH_TOGETHER":
            self.dismantler.reassemble_all(components)

    def reset_all(self, components: Dict[str, ComponentState]):
        self.rotator.reset()
        self.scaler.reset()
        self.dismantler.reassemble_all(components)
        self.selector.select(None)
