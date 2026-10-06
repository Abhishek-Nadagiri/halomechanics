import pytest
import numpy as np
from app.vision.camera import Camera
from app.vision.hand_tracker import HandLandmarkData

def test_camera_synthetic_generation():
    cam = Camera(camera_index=-999, width=640, height=360, fps=30)
    assert cam.start() is True
    assert cam.is_synthetic is True

    ret, frame = cam.read()
    assert ret is True
    assert frame is not None
    assert frame.shape == (360, 640, 3)
    assert cam.get_fps() > 0.0
    cam.stop()
    assert cam.is_running is False

def test_hand_landmark_data_calculations():
    # Mock 21 normalized landmarks
    raw_lm = [(0.5, 0.5 + i * 0.01, 0.0) for i in range(21)]
    hand = HandLandmarkData(handedness="Right", confidence=0.95, landmarks=raw_lm)

    assert hand.handedness == "Right"
    assert hand.confidence == 0.95
    assert len(hand.palm_center) == 3
    assert hand.palm_scale > 0.0
    data = hand.to_dict()
    assert "landmarks" in data
    assert "keypoints" in data
    assert data["confidence"] == 0.95
