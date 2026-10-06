from typing import Dict, Any, Optional
import cv2
import numpy as np

class HUDOverlay:
    """Draws high-tech Tony Stark-inspired holographic telemetry onto OpenCV frames."""

    def __init__(self):
        # Color palette: BGR
        self.CYAN = (255, 240, 0)
        self.AMBER = (0, 190, 255)
        self.WHITE = (240, 240, 240)
        self.GRAY = (140, 140, 140)
        self.DARK_BG = (15, 20, 28)
        self.RED = (50, 50, 255)
        self.GREEN = (50, 255, 100)

    def draw_telemetry(
        self,
        frame: np.ndarray,
        fps: float,
        model_name: str,
        mode: str,
        gesture: str,
        confidence: float,
        finger_count: int,
        selected_component: Optional[str],
        safety_progress: float = 0.0
    ) -> np.ndarray:
        h, w, _ = frame.shape
        overlay = frame.copy()

        # 1. Top HUD Bar
        cv2.rectangle(overlay, (15, 15), (w - 15, 65), self.DARK_BG, -1)
        cv2.rectangle(overlay, (15, 15), (w - 15, 65), self.CYAN, 1)

        # Title and System Health
        cv2.putText(overlay, "HOLOMECHANIX // SPATIAL LAB", (30, 48),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, self.CYAN, 2, cv2.LINE_AA)
        
        fps_text = f"FPS: {fps:.1f}"
        fps_color = self.GREEN if fps >= 30 else self.AMBER
        cv2.putText(overlay, fps_text, (w - 150, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, fps_color, 2, cv2.LINE_AA)

        # 2. Left Diagnostics Panel
        p_top, p_left, p_w, p_h = 80, 15, 320, 260
        cv2.rectangle(overlay, (p_left, p_top), (p_left + p_w, p_top + p_h), self.DARK_BG, -1)
        cv2.rectangle(overlay, (p_left, p_top), (p_left + p_w, p_top + p_h), self.CYAN, 1)

        entries = [
            ("ACTIVE MODEL", model_name[:20].upper()),
            ("INTERACTION MODE", mode.upper()),
            ("PRIMARY GESTURE", gesture.upper()),
            ("GESTURE CONF", f"{int(confidence * 100)}%"),
            ("TRACKED FINGERS", f"{finger_count} / 10"),
            ("SELECTED PART", (selected_component or "NONE").upper()),
        ]

        y_offset = p_top + 30
        for label, val in entries:
            cv2.putText(overlay, label, (p_left + 15, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.GRAY, 1, cv2.LINE_AA)
            cv2.putText(overlay, val, (p_left + 140, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.WHITE, 1, cv2.LINE_AA)
            y_offset += 34

        # 3. Safety Action Progress (Phase 31 Hold confirmation e.g. for PULL APART)
        if safety_progress > 0.0:
            bar_w = 260
            bar_h = 16
            bx = (w - bar_w) // 2
            by = h - 60
            cv2.rectangle(overlay, (bx - 10, by - 25), (bx + bar_w + 10, by + bar_h + 10), self.DARK_BG, -1)
            cv2.rectangle(overlay, (bx - 10, by - 25), (bx + bar_w + 10, by + bar_h + 10), self.AMBER, 1)
            cv2.putText(overlay, f"HOLD GESTURE TO EXPLODE: {int(safety_progress * 100)}%",
                        (bx, by - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.AMBER, 1, cv2.LINE_AA)
            filled = int(bar_w * min(1.0, safety_progress))
            cv2.rectangle(overlay, (bx, by), (bx + filled, by + bar_h), self.AMBER, -1)

        # Blend with opacity
        return cv2.addWeighted(overlay, 0.90, frame, 0.10, 0)
