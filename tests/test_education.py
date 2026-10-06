import pytest
from app.models.registry import ModelRegistry
from app.education.learning_mode import LearningModeManager
from app.education.quiz import QuizManager
from app.education.explanations import EngineeringAIAssistant

def test_learning_mode_curriculum():
    registry = ModelRegistry()
    bike = registry.get_model("sports_bike")
    lm = LearningModeManager.from_model(bike)

    step1 = lm.get_current_step()
    assert step1 is not None
    assert step1["step_number"] == 1
    assert step1["component_id"] == "fuel_tank"

    # Validate step 1 execution
    success = lm.validate_action("fuel_tank", "PINCH")
    assert success is True
    step2 = lm.get_current_step()
    assert step2["step_number"] == 2

def test_quiz_manager():
    registry = ModelRegistry()
    bike = registry.get_model("sports_bike")
    qm = QuizManager.from_model(bike)

    q1 = qm.get_current_question()
    assert q1 is not None
    assert len(q1["options"]) >= 4

    # Submit correct answer (index 1 is spark plug)
    result = qm.submit_answer(1)
    assert result["correct"] is True
    assert qm.score == 1

def test_ai_assistant_grounding():
    registry = ModelRegistry()
    bike = registry.get_model("sports_bike")
    ai = EngineeringAIAssistant(bike)

    ans = ai.answer_query("what_does_it_do", "spark_plug")
    assert "known_data" in ans
    assert "educational_explanation" in ans
    assert "Spark Plug" in ans["known_data"]
    assert "ignite" in ans["educational_explanation"].lower()
