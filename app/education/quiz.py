from typing import List, Optional, Dict, Any
from ..models.metadata import QuizQuestion, ModelMetadata

class QuizManager:
    """Evaluates post-dismantling comprehension questions."""

    def __init__(self, questions: List[QuizQuestion]):
        self.questions = questions
        self.current_index = 0
        self.score = 0
        self.user_answers: Dict[str, int] = {}

    @classmethod
    def from_model(cls, model_meta: ModelMetadata) -> 'QuizManager':
        return cls(model_meta.quiz_questions)

    def get_current_question(self) -> Optional[Dict[str, Any]]:
        if self.current_index >= len(self.questions):
            return None
        q = self.questions[self.current_index]
        return {
            "id": q.id,
            "index": self.current_index,
            "total": len(self.questions),
            "question": q.question,
            "options": q.options,
            "current_score": self.score
        }

    def submit_answer(self, option_index: int) -> Dict[str, Any]:
        cur = self.get_current_question()
        if not cur:
            return {"finished": True, "score": self.score, "total": len(self.questions)}

        q = self.questions[self.current_index]
        is_correct = (option_index == q.correct_index)
        if is_correct:
            self.score += 1

        self.user_answers[q.id] = option_index
        self.current_index += 1

        return {
            "correct": is_correct,
            "explanation": q.explanation,
            "correct_option": q.options[q.correct_index],
            "is_last": self.current_index >= len(self.questions),
            "total_score": self.score,
            "total_questions": len(self.questions)
        }

    def reset(self):
        self.current_index = 0
        self.score = 0
        self.user_answers.clear()
