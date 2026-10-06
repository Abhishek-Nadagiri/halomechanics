import time
import pytest
import numpy as np
from app.vision.hand_tracker import HandLandmarkData
from app.vision.gesture_engine import GestureEngine

def test_gesture_engine_idle_and_pinch():
    engine = GestureEngine(pinch_threshold=0.08, hysteresis_ms=0)

    # Empty hands -> IDLE
    res = engine.update([])
    assert res.primary_gesture == "IDLE"

    # Create mock hand where thumb tip and index tip are very close (Pinch)
    lm = [(0.5, 0.5, 0.0)] * 21
    # Wrist
    lm[0] = (0.5, 0.8, 0.0)
    # Middle MCP for palm scale
    lm[9] = (0.5, 0.5, 0.0)
    # Thumb tip and index tip touching
    lm[4] = (0.5, 0.3, 0.0)
    lm[8] = (0.51, 0.3, 0.0)
    # Other tips folded back
    lm[12] = (0.5, 0.7, 0.0)
    lm[16] = (0.5, 0.7, 0.0)
    lm[20] = (0.5, 0.7, 0.0)

    hand = HandLandmarkData("Right", 0.98, lm)
    res = engine.update([hand])
    assert res.primary_gesture in ("PINCH", "POINT_PINCH")
    assert res.confidence >= 0.90
