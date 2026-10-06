from typing import Dict, List, Optional, Tuple, Any
import time
import numpy as np
import logging
from .hand_tracker import HandLandmarkData
from .finger_tracker import FingerTracker

logger = logging.getLogger("holomechanix.vision.gesture_engine")

class GestureResult:
    """Detailed result of evaluated spatial gestures."""
    def __init__(
        self,
        primary_gesture: str = "IDLE",
        confidence: float = 0.0,
        two_hand_gesture: Optional[str] = None,
        safety_progress: float = 0.0,
        cursor_pos: Optional[Tuple[float, float, float]] = None,
        rotation_delta: Optional[Tuple[float, float, float]] = None,
        scale_delta: float = 1.0,
        active_hand: str = "right"
    ):
        self.primary_gesture = primary_gesture
        self.confidence = confidence
        self.two_hand_gesture = two_hand_gesture
        self.safety_progress = safety_progress  # 0.0 to 1.0 for actions requiring hold
        self.cursor_pos = cursor_pos
        self.rotation_delta = rotation_delta
        self.scale_delta = scale_delta
        self.active_hand = active_hand

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_gesture": self.primary_gesture,
            "confidence": round(self.confidence, 3),
            "two_hand_gesture": self.two_hand_gesture,
            "safety_progress": round(self.safety_progress, 2),
            "cursor_pos": [round(c, 4) for c in self.cursor_pos] if self.cursor_pos else None,
            "rotation_delta": [round(r, 4) for r in self.rotation_delta] if self.rotation_delta else None,
            "scale_delta": round(self.scale_delta, 4),
            "active_hand": self.active_hand
        }


class GestureEngine:
    """Evaluates spatial gestures with temporal smoothing, hysteresis, and safety confirmation."""

    def __init__(
        self,
        pinch_threshold: float = 0.06,
        grab_threshold: float = 0.08,
        hold_duration_sec: float = 0.5,
        hysteresis_ms: int = 150
    ):
        self.pinch_threshold = pinch_threshold
        self.grab_threshold = grab_threshold
        self.hold_duration_sec = hold_duration_sec
        self.hysteresis_sec = hysteresis_ms / 1000.0

        self.finger_tracker = FingerTracker()

        # State tracking & smoothing
        self._current_gesture = "IDLE"
        self._candidate_gesture = "IDLE"
        self._candidate_start_time = 0.0
        self._last_gesture_change_time = 0.0

        # Safety hold tracking (e.g., Pull Apart / Explode)
        self._safety_gesture_start = 0.0
        self._safety_target = ""

        # Multi-frame tracking for 2-hand gestures
        self._prev_hand_distance = None
        self._prev_hand_angle = None
        self._prev_positions = {"left": None, "right": None}
        self._prev_timestamp = time.time()

        # EMA smoothed cursor
        self._smoothed_cursor = None
        self._alpha = 0.65  # EMA weight for current sample

    def update(self, detected_hands: List[HandLandmarkData]) -> GestureResult:
        """Main update function: evaluates hand states, runs gesture rules, applies smoothing."""
        now = time.time()
        dt = max(1e-4, now - self._prev_timestamp)
        self._prev_timestamp = now

        finger_states, total_fingers = self.finger_tracker.detect_finger_states(detected_hands)

        # Default result
        result = GestureResult(primary_gesture="IDLE", confidence=0.0)

        if not detected_hands:
            self._reset_transient_states()
            return result

        # Determine dominant hand (default right, or single detected hand)
        right_hand = next((h for h in detected_hands if h.handedness.lower() == "right"), None)
        left_hand = next((h for h in detected_hands if h.handedness.lower() == "left"), None)
        dominant_hand = right_hand if right_hand is not None else left_hand

        # 1. Update smoothed spatial cursor (Index tip of dominant hand)
        raw_cursor = dominant_hand.index_tip
        if self._smoothed_cursor is None:
            self._smoothed_cursor = np.array(raw_cursor, dtype=float)
        else:
            self._smoothed_cursor = (self._alpha * np.array(raw_cursor)) + ((1.0 - self._alpha) * self._smoothed_cursor)
        result.cursor_pos = (float(self._smoothed_cursor[0]), float(self._smoothed_cursor[1]), float(self._smoothed_cursor[2]))
        result.active_hand = dominant_hand.handedness.lower()

        # 2. Single hand gesture classification
        detected_gesture, gesture_conf = self._classify_single_hand(dominant_hand, finger_states[dominant_hand.handedness.lower()])

        # 3. Two-hand gesture classification (Rotation, Scaling, Explode, Reassemble)
        if len(detected_hands) >= 2 and right_hand and left_hand:
            two_hand_action, r_delta, s_delta, safety_pct = self._evaluate_bimanual_interaction(right_hand, left_hand, finger_states, now, dt)
            if two_hand_action:
                result.two_hand_gesture = two_hand_action
                result.rotation_delta = r_delta
                result.scale_delta = s_delta
                result.safety_progress = safety_pct

                # In bimanual mode, prioritize the two-hand gesture
                detected_gesture = two_hand_action
                gesture_conf = 0.95

        # 4. Temporal hysteresis and stabilization
        stable_gesture = self._apply_hysteresis(detected_gesture, now)
        result.primary_gesture = stable_gesture
        result.confidence = gesture_conf

        return result

    def _classify_single_hand(self, hand: HandLandmarkData, fingers: Dict[str, bool]) -> Tuple[str, float]:
        """Classify single hand gestures: Open Palm, Fist, Point, Pinch, Point+Pinch."""
        # Calculate pinch distance (Thumb tip to Index tip normalized by palm scale)
        p_thumb = np.array(hand.thumb_tip)
        p_index = np.array(hand.index_tip)
        pinch_dist = np.linalg.norm(p_thumb - p_index) / max(0.01, hand.palm_scale)

        num_open = sum(1 for v in fingers.values() if v)

        # A. Pinch / Point+Pinch
        if pinch_dist < (self.pinch_threshold * 1.5):
            # If middle/ring/pinky are closed, it's a precision Pinch / Grab
            if not fingers["middle"] and not fingers["pinky"]:
                return "PINCH", 0.94
            return "POINT_PINCH", 0.90

        # B. Point: Index is open, middle/ring/pinky are closed
        if fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            return "POINT", 0.96

        # C. Fist: All or almost all fingers closed
        if num_open <= 1 and not fingers["index"] and not fingers["middle"]:
            return "FIST", 0.92

        # D. Open Palm: 4 or 5 fingers extended
        if num_open >= 4:
            return "OPEN_PALM", 0.95

        return "IDLE", 0.50

    def _evaluate_bimanual_interaction(
        self,
        r_hand: HandLandmarkData,
        l_hand: HandLandmarkData,
        finger_states: Dict[str, Dict[str, bool]],
        now: float,
        dt: float
    ) -> Tuple[Optional[str], Optional[Tuple[float, float, float]], float, float]:
        """Evaluates two-hand gestures: Rotation, Scaling, Explode (Pull Apart), Reassemble (Push Together)."""
        r_palm = np.array(r_hand.palm_center)
        l_palm = np.array(l_hand.palm_center)

        current_dist = float(np.linalg.norm(r_palm - l_palm))
        current_dx = r_palm[0] - l_palm[0]
        current_dy = r_palm[1] - l_palm[1]
        current_angle = float(np.arctan2(current_dy, current_dx))

        r_open = sum(1 for v in finger_states["right"].values() if v) >= 4
        l_open = sum(1 for v in finger_states["left"].values() if v) >= 4

        gesture_name = None
        rot_delta = None
        scale_delta = 1.0
        safety_progress = 0.0

        if self._prev_hand_distance is not None:
            dist_change = current_dist - self._prev_hand_distance
            angle_change = current_angle - self._prev_hand_angle

            # Normalise angular jump [-pi, pi]
            if angle_change > np.pi: angle_change -= 2 * np.pi
            elif angle_change < -np.pi: angle_change += 2 * np.pi

            # Check for PULL APART (Explosion) / PUSH TOGETHER (Reassembly)
            if r_open and l_open:
                # Hands moving apart significantly
                if dist_change > 0.035:
                    if self._safety_target != "PULL_APART":
                        self._safety_target = "PULL_APART"
                        self._safety_gesture_start = now
                    
                    elapsed = now - self._safety_gesture_start
                    safety_progress = min(1.0, elapsed / self.hold_duration_sec)
                    if safety_progress >= 1.0:
                        gesture_name = "PULL_APART"  # Explode triggered
                    else:
                        gesture_name = "ARMING_EXPLODE"

                # Hands moving together significantly
                elif dist_change < -0.035:
                    gesture_name = "PUSH_TOGETHER"
                    self._safety_target = ""
                else:
                    self._safety_target = ""

            # Check for Two-Finger / Two-Hand Rotation
            if abs(angle_change) > 0.04 and not gesture_name:
                gesture_name = "TWO_HAND_ROTATE"
                rot_delta = (0.0, float(angle_change * 1.5), 0.0)

            # Two-Hand Pinch / Scale
            r_pinching = np.linalg.norm(np.array(r_hand.thumb_tip) - np.array(r_hand.index_tip)) < 0.08
            l_pinching = np.linalg.norm(np.array(l_hand.thumb_tip) - np.array(l_hand.index_tip)) < 0.08
            if r_pinching and l_pinching:
                gesture_name = "TWO_HAND_PINCH"
                scale_factor = 1.0 + (dist_change * 2.0)
                scale_delta = max(0.5, min(2.0, scale_factor))

        self._prev_hand_distance = current_dist
        self._prev_hand_angle = current_angle
        return gesture_name, rot_delta, scale_delta, safety_progress

    def _apply_hysteresis(self, new_gesture: str, now: float) -> str:
        """Prevents rapid jitter by requiring a gesture to be held for hysteresis_sec."""
        if new_gesture != self._candidate_gesture:
            self._candidate_gesture = new_gesture
            self._candidate_start_time = now

        if (now - self._candidate_start_time) >= self.hysteresis_sec:
            self._current_gesture = self._candidate_gesture
            self._last_gesture_change_time = now

        return self._current_gesture

    def _reset_transient_states(self):
        self._prev_hand_distance = None
        self._prev_hand_angle = None
        self._safety_target = ""
        self._safety_gesture_start = 0.0
