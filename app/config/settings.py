from pathlib import Path
import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
MODELS_DIR = ASSETS_DIR / "models"
DATA_DIR = BASE_DIR / "data"

class Settings(BaseModel):
    # App info
    APP_NAME: str = "HoloMechanix"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Camera settings
    CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))
    CAMERA_WIDTH: int = int(os.getenv("CAMERA_WIDTH", "1280"))
    CAMERA_HEIGHT: int = int(os.getenv("CAMERA_HEIGHT", "720"))
    CAMERA_FPS: int = int(os.getenv("CAMERA_FPS", "30"))

    # Computer Vision (MediaPipe)
    MIN_DETECTION_CONFIDENCE: float = float(os.getenv("MIN_DETECTION_CONFIDENCE", "0.7"))
    MIN_TRACKING_CONFIDENCE: float = float(os.getenv("MIN_TRACKING_CONFIDENCE", "0.6"))
    MAX_NUM_HANDS: int = int(os.getenv("MAX_NUM_HANDS", "2"))

    # Spatial & Gesture thresholds
    PINCH_THRESHOLD: float = float(os.getenv("PINCH_THRESHOLD", "0.06"))
    GRAB_THRESHOLD: float = float(os.getenv("GRAB_THRESHOLD", "0.08"))
    GESTURE_HOLD_DURATION_SEC: float = float(os.getenv("GESTURE_HOLD_DURATION_SEC", "0.5"))
    GESTURE_HYSTERESIS_MS: int = int(os.getenv("GESTURE_HYSTERESIS_MS", "150"))

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WS_FPS_CAP: int = int(os.getenv("WS_FPS_CAP", "60"))

    # Paths
    BASE_DIR: Path = BASE_DIR
    ASSETS_DIR: Path = ASSETS_DIR
    MODELS_DIR: Path = MODELS_DIR
    DATA_DIR: Path = DATA_DIR

settings = Settings()
