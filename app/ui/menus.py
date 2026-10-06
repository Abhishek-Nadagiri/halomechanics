from typing import List, Dict, Any

class MenuController:
    """Manages active mode selection and model browser states."""

    MODES = ["FREE PLAY", "LEARNING MODE", "QUIZ MODE", "CALIBRATION"]

    def __init__(self, available_models: List[str]):
        self.available_models = available_models
        self.active_model_index = 0
        self.active_mode_index = 0

    @property
    def current_model(self) -> str:
        if not self.available_models:
            return "None"
        return self.available_models[self.active_model_index % len(self.available_models)]

    @property
    def current_mode(self) -> str:
        return self.MODES[self.active_mode_index % len(self.MODES)]

    def next_model(self) -> str:
        if self.available_models:
            self.active_model_index = (self.active_model_index + 1) % len(self.available_models)
        return self.current_model

    def prev_model(self) -> str:
        if self.available_models:
            self.active_model_index = (self.active_model_index - 1) % len(self.available_models)
        return self.current_model

    def next_mode(self) -> str:
        self.active_mode_index = (self.active_mode_index + 1) % len(self.MODES)
        return self.current_mode
