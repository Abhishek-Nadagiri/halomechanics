from typing import Dict, Any, Optional
import cv2
import numpy as np

class CalibrationOverlay:
    """Renders the Phase 35 Spatial Calibration and Setup Screen."""

    @staticmethod
    def draw(frame: np.ndarray, tracking_quality: float = 0.92, has_left: bool = True, has_right: bool = True) -> np.ndarray:
        h, w, _ = frame.shape
        overlay = frame.copy()

        # Dark overlay
        cv2.rectangle(overlay, (50, 50), (w - 50, h - 50), (12, 16, 24), -1)
        cv2.rectangle(overlay, (50, 50), (w - 50, h - 50), (255, 240, 0), 2)

        cv2.putText(overlay, "SPATIAL CALIBRATION // SYSTEM SETUP", (80, 100),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 240, 0), 2, cv2.LINE_AA)

        instructions = [
            "1. Stand 1.0 - 2.0 meters from the camera",
            "2. Ensure good ambient lighting without harsh backlighting",
            "3. Raise BOTH hands with open palms towards the camera",
            "4. Gently articulate fingers to verify full 10-finger detection"
        ]

        y = 150
        for inst in instructions:
            cv2.putText(overlay, inst, (80, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
            y += 35

        # Progress bars
        y += 20
        metrics = [
            ("CAMERA RESOLUTION", 1.0),
            ("LEFT HAND TRACKING", 0.95 if has_left else 0.1),
            ("RIGHT HAND TRACKING", 0.95 if has_right else 0.1),
            ("DEPTH RECONSTRUCTION", 0.85),
            ("OVERALL SYSTEM CONFIDENCE", tracking_quality),
        ]

        for label, val in metrics:
            cv2.putText(overlay, label, (80, y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)
            bx, by, bw, bh = 340, y, 300, 20
            cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (40, 50, 65), -1)
            cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (255, 240, 0), 1)
            fill_w = int(bw * val)
            cv2.rectangle(overlay, (bx, by), (bx + fill_w, by + bh), (0, 220, 255), -1)
            cv2.putText(overlay, f"{int(val * 100)}%", (bx + bw + 15, y + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            y += 35

        cv2.putText(overlay, "Press 'C' to exit calibration mode and enter laboratory",
                    (80, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 120), 2, cv2.LINE_AA)

        return cv2.addWeighted(overlay, 0.92, frame, 0.08, 0)
