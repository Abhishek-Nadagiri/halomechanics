from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import cv2
import numpy as np
import logging
from ..config.settings import settings

logger = logging.getLogger("holomechanix.vision.hand_tracker")

class HandLandmarkData:
    """Structured data container for a detected hand."""
    def __init__(self, handedness: str, confidence: float, landmarks: List[Tuple[float, float, float]]):
        self.handedness = handedness  # "Left" or "Right"
        self.confidence = confidence
        self.raw_landmarks = landmarks  # List of 21 (x, y, z) normalized coords

        # Specific landmark shortcuts
        self.wrist = landmarks[0]
        self.thumb_cmc = landmarks[1]
        self.thumb_mcp = landmarks[2]
        self.thumb_ip = landmarks[3]
        self.thumb_tip = landmarks[4]

        self.index_mcp = landmarks[5]
        self.index_pip = landmarks[6]
        self.index_dip = landmarks[7]
        self.index_tip = landmarks[8]

        self.middle_mcp = landmarks[9]
        self.middle_pip = landmarks[10]
        self.middle_dip = landmarks[11]
        self.middle_tip = landmarks[12]

        self.ring_mcp = landmarks[13]
        self.ring_pip = landmarks[14]
        self.ring_dip = landmarks[15]
        self.ring_tip = landmarks[16]

        self.pinky_mcp = landmarks[17]
        self.pinky_pip = landmarks[18]
        self.pinky_dip = landmarks[19]
        self.pinky_tip = landmarks[20]

        # Calculate palm center
        self.palm_center = (
            (self.wrist[0] + self.index_mcp[0] + self.middle_mcp[0] + self.pinky_mcp[0]) / 4.0,
            (self.wrist[1] + self.index_mcp[1] + self.middle_mcp[1] + self.pinky_mcp[1]) / 4.0,
            (self.wrist[2] + self.index_mcp[2] + self.middle_mcp[2] + self.pinky_mcp[2]) / 4.0,
        )

        # Approximate palm scale (wrist to middle MCP distance)
        dx = self.middle_mcp[0] - self.wrist[0]
        dy = self.middle_mcp[1] - self.wrist[1]
        dz = self.middle_mcp[2] - self.wrist[2]
        self.palm_scale = max(0.01, float(np.sqrt(dx*dx + dy*dy + dz*dz)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handedness": self.handedness,
            "confidence": round(self.confidence, 3),
            "palm_center": [round(c, 4) for c in self.palm_center],
            "palm_scale": round(self.palm_scale, 4),
            "landmarks": [[round(c, 4) for c in lm] for lm in self.raw_landmarks],
            "keypoints": {
                "wrist": [round(c, 4) for c in self.wrist],
                "thumb_tip": [round(c, 4) for c in self.thumb_tip],
                "index_tip": [round(c, 4) for c in self.index_tip],
                "middle_tip": [round(c, 4) for c in self.middle_tip],
                "ring_tip": [round(c, 4) for c in self.ring_tip],
                "pinky_tip": [round(c, 4) for c in self.pinky_tip],
            }
        }


class HandTracker:
    """Production MediaPipe Hand Tracker utilizing Google's official HandLandmarker task model."""

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),        # Index
        (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
        (9, 13), (13, 14), (14, 15), (15, 16), # Ring
        (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
        (0, 17)                                # Palm base
    ]

    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5, max_num_hands: int = 2):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.max_num_hands = max_num_hands

        self.detector = None
        self._init_mediapipe()

    def _init_mediapipe(self):
        # 1. Try modern MediaPipe HandLandmarker Tasks API with assets/hand_landmarker.task
        task_path = settings.BASE_DIR / "assets" / "hand_landmarker.task"
        if task_path.exists():
            try:
                import mediapipe as mp
                from mediapipe.tasks.python import vision
                from mediapipe.tasks.python import BaseOptions

                base_options = BaseOptions(model_asset_path=str(task_path))
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=self.max_num_hands,
                    min_hand_detection_confidence=self.min_detection_confidence,
                    min_hand_presence_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence
                )
                self.detector = vision.HandLandmarker.create_from_options(options)
                logger.info("HandTracker initialized with MediaPipe HandLandmarker Tasks model.")
                return
            except Exception as e:
                logger.warning(f"Could not initialize MediaPipe HandLandmarker: {e}")

        # 2. Try legacy mp.solutions.hands if available
        try:
            import mediapipe as mp
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=self.max_num_hands,
                    min_detection_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence
                )
                logger.info("HandTracker initialized with MediaPipe solutions backend.")
                return
        except Exception as e:
            logger.debug(f"MediaPipe solutions not available: {e}")

        logger.info("HandTracker using fallback tracking.")

    def process_frame(self, frame_bgr: np.ndarray) -> List[HandLandmarkData]:
        """Detect hands and produce 21 landmarks per hand."""
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # 1. Official MediaPipe Tasks detector
        if self.detector is not None:
            try:
                import mediapipe as mp
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                results = self.detector.detect(mp_image)
                detected_hands: List[HandLandmarkData] = []

                if results.hand_landmarks and results.handedness:
                    for lms, handedness_cat in zip(results.hand_landmarks, results.handedness):
                        cat = handedness_cat[0]
                        label = cat.category_name  # "Left" or "Right"
                        score = float(cat.score)
                        # Swapped label for mirror view
                        natural_label = "Right" if label == "Left" else "Left"
                        pts = [(float(lm.x), float(lm.y), float(lm.z)) for lm in lms]
                        detected_hands.append(HandLandmarkData(natural_label, score, pts))

                return detected_hands
            except Exception as e:
                logger.warning(f"Error in HandLandmarker inference: {e}")

        # 2. Legacy solutions
        if hasattr(self, "hands") and self.hands is not None:
            results = self.hands.process(frame_rgb)
            detected_hands = []
            if results.multi_hand_landmarks and results.multi_handedness:
                for landmarks, handedness_info in zip(results.multi_hand_landmarks, results.multi_handedness):
                    label = handedness_info.classification[0].label
                    score = handedness_info.classification[0].score
                    natural_label = "Right" if label == "Left" else "Left"
                    pts = [(lm.x, lm.y, lm.z) for lm in landmarks.landmark]
                    detected_hands.append(HandLandmarkData(natural_label, score, pts))
            return detected_hands

        return []

    def draw_futuristic_skeleton(self, frame: np.ndarray, detected_hands: List[HandLandmarkData]) -> np.ndarray:
        """Draws holographic cyan hand skeleton and glowing nodes."""
        h, w, _ = frame.shape
        overlay = frame.copy()
        cyan_color = (255, 240, 0)
        amber_color = (0, 190, 255)
        joint_color = (255, 255, 255)

        for hand in detected_hands:
            pts_px = [(int(np.clip(p[0] * w, 0, w - 1)), int(np.clip(p[1] * h, 0, h - 1))) for p in hand.raw_landmarks]
            for p1, p2 in self.HAND_CONNECTIONS:
                cv2.line(overlay, pts_px[p1], pts_px[p2], cyan_color, 2, cv2.LINE_AA)
            for i, pt in enumerate(pts_px):
                is_tip = i in [4, 8, 12, 16, 20]
                if is_tip:
                    cv2.circle(overlay, pt, 6, amber_color, -1, cv2.LINE_AA)
                    cv2.circle(overlay, pt, 3, joint_color, -1, cv2.LINE_AA)
                else:
                    cv2.circle(overlay, pt, 3, cyan_color, -1, cv2.LINE_AA)

            pc_x = int(np.clip(hand.palm_center[0] * w, 0, w - 1))
            pc_y = int(np.clip(hand.palm_center[1] * h, 0, h - 1))
            cv2.circle(overlay, (pc_x, pc_y), 10, amber_color, 1, cv2.LINE_AA)
            cv2.putText(overlay, f"{hand.handedness.upper()} HAND", (pc_x - 40, pc_y - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, cyan_color, 1, cv2.LINE_AA)

        return cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)

    def close(self):
        if self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass
