import sys
from pathlib import Path
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import settings
from app.vision.camera import Camera
from app.vision.hand_tracker import HandTracker
from app.ui.overlays import CalibrationOverlay

def main():
    print("=" * 60)
    print("HoloMechanix Spatial Calibration Utility")
    print("=" * 60)
    print("Stand 1.0 - 2.0m from webcam. Extend all 10 fingers.")
    print("Press ESC to exit calibration.")

    cam = Camera(
        camera_index=settings.CAMERA_INDEX,
        width=settings.CAMERA_WIDTH,
        height=settings.CAMERA_HEIGHT,
        fps=settings.CAMERA_FPS
    )
    cam.start()
    tracker = HandTracker()

    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                continue

            hands = tracker.process_frame(frame)
            frame = tracker.draw_futuristic_skeleton(frame, hands)

            has_l = any(h.handedness.lower() == "left" for h in hands)
            has_r = any(h.handedness.lower() == "right" for h in hands)
            quality = 0.95 if (has_l and has_r) else (0.6 if (has_l or has_r) else 0.2)

            frame = CalibrationOverlay.draw(frame, tracking_quality=quality, has_left=has_l, has_right=has_r)

            cv2.imshow("HoloMechanix Calibration", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        cam.stop()
        tracker.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
