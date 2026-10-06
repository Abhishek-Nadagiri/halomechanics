from typing import List, Dict, Optional, Tuple
import logging
from ..models.hierarchy import ModelHierarchy
from ..simulation.component import ComponentState
from ..simulation.animation import AnimationController

logger = logging.getLogger("holomechanix.interaction.dismantling")

class DismantlingController:
    """Orchestrates assembly explosion, manual part detachment, and sequential reassembly."""

    def __init__(self, hierarchy: ModelHierarchy):
        self.hierarchy = hierarchy
        self.dismantled_history: List[str] = []
        self.animator = AnimationController(duration_sec=1.0)
        self.is_exploded = False

    def trigger_exploded_view(self):
        """Smoothly drives all components outward along their explosion vectors."""
        self.is_exploded = True
        self.animator.animate_to(1.0)
        logger.info("Exploded view animation initiated.")

    def trigger_collapse(self):
        """Smoothly collapses components back to assembled pose."""
        self.is_exploded = False
        self.animator.animate_to(0.0)
        logger.info("Assembly collapse animation initiated.")

    def record_manual_dismantle(self, comp_id: str):
        """Records manually extracted component into disassembly log."""
        if comp_id not in self.dismantled_history:
            self.dismantled_history.append(comp_id)
            logger.info(f"Recorded manual component detachment: {comp_id} (Total: {len(self.dismantled_history)})")

    def reassemble_all(self, components: Dict[str, ComponentState]) -> Dict[str, bool]:
        """Validates and restores all components to original nominal geometry."""
        validation_results = {}
        for comp_id in self.dismantled_history:
            state = components.get(comp_id)
            if state:
                state.reset_transform()
                # Phase 20 validation checks:
                valid = (state.metadata.parent is None or state.metadata.parent in components)
                validation_results[comp_id] = valid
        
        self.dismantled_history.clear()
        self.trigger_collapse()
        return validation_results

    def update(self, components: Dict[str, ComponentState]):
        """Updates continuous exploded view interpolation."""
        explosion_factor = self.animator.update()
        offsets = self.hierarchy.compute_explosion_offsets(explosion_factor)

        for comp_id, offset in offsets.items():
            state = components.get(comp_id)
            if state and not state.is_grabbed and not state.is_dismantled:
                state.target_position = state.base_position + offset
