from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field

class ConstraintConfig(BaseModel):
    """Kinematic constraint parameters for a component."""
    type: str = "fixed"  # "fixed", "hinge", "slider", "rotational", "translational"
    axis: List[float] = Field(default_factory=lambda: [0.0, 1.0, 0.0])
    limits: Tuple[float, float] = (-180.0, 180.0)
    current_value: float = 0.0

class ComponentMetadata(BaseModel):
    """Semantic engineering metadata for an individual component."""
    id: str
    name: str
    category: str
    description: str
    function: str
    parent: Optional[str] = None
    removable: bool = True
    movement_axis: List[float] = Field(default_factory=lambda: [0.0, 1.0, 0.0])
    explosion_vector: Optional[List[float]] = None
    explosion_distance: float = 1.5
    material: str = "Aluminum Alloy"
    common_failure: str = "Mechanical wear / thermal fatigue"
    educational_level: str = "Beginner"
    connected_components: List[str] = Field(default_factory=list)
    constraint: Optional[ConstraintConfig] = None
    
    # 3D bounding & position offsets
    local_position: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    local_rotation: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    color_hex: str = "#00e5ff"

class LearningStep(BaseModel):
    step_number: int
    component_id: str
    instruction: str
    required_gesture: str = "PINCH"
    explanation: str

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_index: int
    explanation: str

class ModelMetadata(BaseModel):
    """Complete metadata for an inspectable 3D machine or system."""
    id: str
    name: str
    category: str  # "Automotive", "Mechanical", "Electronics"
    description: str
    root_component_id: str
    components: List[ComponentMetadata]
    learning_steps: List[LearningStep] = Field(default_factory=list)
    quiz_questions: List[QuizQuestion] = Field(default_factory=list)
