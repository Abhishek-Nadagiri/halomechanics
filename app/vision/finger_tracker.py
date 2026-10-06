from typing import Dict, List, Tuple
import numpy as np
import logging
from .hand_tracker import HandLandmarkData

logger = logging.getLogger("holomechanix.vision.finger_tracker")

class FingerTracker:
    """Robust 10-finger detection system invariant to rotation, perspective, and scale."""

    FINGER_JOINTS = {
        "index": (5, 6, 7, 8),     # MCP, PIP, DIP, TIP
        "middle": (9, 10, 11, 12),
        "ring": (13, 14, 15, 16),
        "pinky": (17, 18, 19, 20),
    }

    def __init__(self):
        pass

    def detect_finger_states(self, detected_hands: List[HandLandmarkData]) -> Tuple[Dict[str, Dict[str, bool]], int]:
        """Calculates boolean states for all 10 fingers across both hands and total count."""
        states = {
            "left": {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False},
            "right": {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}
        }
        total_open = 0

        for hand in detected_hands:
            side = hand.handedness.lower()
            hand_states = self._evaluate_hand_fingers(hand)
            states[side] = hand_states
            total_open += sum(1 for v in hand_states.values() if v)

        return states, total_open

    def _evaluate_hand_fingers(self, hand: HandLandmarkData) -> Dict[str, bool]:
        """Evaluates finger extension states using angular flexion and projection on palm plane."""
        lm = np.array(hand.raw_landmarks)  # shape (21, 3)
        wrist = lm[0]
        middle_mcp = lm[9]
        index_mcp = lm[5]
        pinky_mcp = lm[17]

        # Define palm coordinate system:
        # v_long: from wrist to middle MCP (longitudinal axis of palm)
        v_long = middle_mcp - wrist
        len_long = np.linalg.norm(v_long) + 1e-6
        v_long_norm = v_long / len_long

        # v_trans: from index MCP to pinky MCP (transverse axis across palm)
        v_trans = pinky_mcp - index_mcp
        len_trans = np.linalg.norm(v_trans) + 1e-6
        v_trans_norm = v_trans / len_trans

        # Palm normal vector
        v_norm = np.cross(v_long_norm, v_trans_norm)
        v_norm /= (np.linalg.norm(v_norm) + 1e-6)

        results = {}

        # 1. Non-thumb fingers (Index, Middle, Ring, Pinky)
        for finger_name, (mcp_idx, pip_idx, dip_idx, tip_idx) in self.FINGER_JOINTS.items():
            mcp = lm[mcp_idx]
            pip = lm[pip_idx]
            tip = lm[tip_idx]

            # Vector from MCP to TIP
            v_finger = tip - mcp
            # Projection along palm longitudinal axis
            long_proj = np.dot(v_finger, v_long_norm)

            # Distance ratio relative to palm scale
            dist_wrist_tip = np.linalg.norm(tip - wrist)
            dist_wrist_pip = np.linalg.norm(pip - wrist)

            # A finger is open if tip extends further away from wrist than PIP
            # and projects positively along longitudinal vector
            is_extended = (dist_wrist_tip > dist_wrist_pip * 1.15) and (long_proj > 0.02)
            results[finger_name] = bool(is_extended)

        # 2. Thumb detection (Thumb articulates sideways away from palm)
        thumb_cmc = lm[1]
        thumb_mcp = lm[2]
        thumb_ip = lm[3]
        thumb_tip = lm[4]

        # Vector from wrist to thumb tip
        v_thumb = thumb_tip - thumb_cmc
        # Normal distance from index MCP
        dist_thumb_index_mcp = np.linalg.norm(thumb_tip - index_mcp)
        dist_thumb_mcp_index = np.linalg.norm(thumb_mcp - index_mcp)

        # Compare tip extension vs IP joint
        dist_wrist_thumb_tip = np.linalg.norm(thumb_tip - wrist)
        dist_wrist_thumb_ip = np.linalg.norm(thumb_ip - wrist)

        thumb_extended = (dist_wrist_thumb_tip > dist_wrist_thumb_ip * 1.08) and (dist_thumb_index_mcp > dist_thumb_mcp_index * 1.1)
        results["thumb"] = bool(thumb_extended)

        return results
