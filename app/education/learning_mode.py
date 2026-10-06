from typing import List, Optional, Dict, Any
import logging
from ..models.metadata import LearningStep, ModelMetadata

logger = logging.getLogger("holomechanix.education.learning_mode")

class LearningModeManager:
    """Orchestrates step-by-step guided dismantling and assembly curricula."""

    def __init__(self, steps: List[LearningStep]):
        self.steps = steps
        self.current_step_index = 0
        self.completed_steps: List[int] = []

    @classmethod
    def from_model(cls, model_meta: ModelMetadata) -> 'LearningModeManager':
        return cls(model_meta.learning_steps)

    def get_current_step(self) -> Optional[Dict[str, Any]]:
        if self.current_step_index >= len(self.steps):
            return None
        step = self.steps[self.current_step_index]
        return {
            "step_number": step.step_number,
            "total_steps": len(self.steps),
            "component_id": step.component_id,
            "instruction": step.instruction,
            "required_gesture": step.required_gesture,
            "explanation": step.explanation,
            "is_completed": step.step_number in self.completed_steps
        }

    def validate_action(self, component_id: str, gesture_name: str) -> bool:
        """Validates if user executed the correct gesture on the target step component."""
        cur = self.get_current_step()
        if not cur:
            return False

        if cur["component_id"] == component_id and (cur["required_gesture"] in (gesture_name, "PINCH", "PULL_APART")):
            self.completed_steps.append(cur["step_number"])
            self.current_step_index += 1
            logger.info(f"Completed learning step {cur['step_number']} of {len(self.steps)}")
            return True

        return False

    def reset(self):
        self.current_step_index = 0
        self.completed_steps.clear()
