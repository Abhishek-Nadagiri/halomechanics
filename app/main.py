import argparse
import logging
import sys
import webbrowser
import cv2
import numpy as np
import uvicorn

from .config.settings import settings
from .vision.camera import Camera
from .vision.hand_tracker import HandTracker
from .vision.gesture_engine import GestureEngine
from .models.registry import ModelRegistry
from .rendering.desktop_renderer import Desktop3DRenderer
from .ui.hud import HUDOverlay
from .ui.overlays import CalibrationOverlay

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("holomechanix.main")

def run_desktop_app():
    """Desktop OpenCV visual spatial interaction runner with real 3D model exploration."""
    logger.info("Initializing HoloMechanix Desktop Spatial Application...")

    camera = Camera(
        camera_index=settings.CAMERA_INDEX,
        width=settings.CAMERA_WIDTH,
        height=settings.CAMERA_HEIGHT,
        fps=settings.CAMERA_FPS
    )
    if not camera.start():
        logger.error("Failed to start camera subsystem. Exiting.")
        sys.exit(1)

    tracker = HandTracker(
        min_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE,
        max_num_hands=settings.MAX_NUM_HANDS
    )
    gesture_engine = GestureEngine(
        pinch_threshold=settings.PINCH_THRESHOLD,
        grab_threshold=settings.GRAB_THRESHOLD,
        hold_duration_sec=settings.GESTURE_HOLD_DURATION_SEC,
        hysteresis_ms=settings.GESTURE_HYSTERESIS_MS
    )
    registry = ModelRegistry()
    hud = HUDOverlay()

    # 3D Desktop Projection Engine
    renderer = Desktop3DRenderer(width=settings.CAMERA_WIDTH, height=settings.CAMERA_HEIGHT)

    model_list = registry.list_models()
    model_idx = 0
    current_meta = registry.get_model(model_list[model_idx]["id"]) if model_list else None
    if current_meta:
        renderer.load_model(current_meta)

    mode = "FREE PLAY"
    show_calibration = False

    logger.info("HoloMechanix Desktop initialized successfully.")
    logger.info("Controls: [ESC] Exit | [M] Switch Model | [E] Explode | [R] Reassemble | [C] Calibration")

    cv2.namedWindow("HoloMechanix - Spatial Laboratory", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("HoloMechanix - Spatial Laboratory", 1280, 720)

    prev_palm_pos = None

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                continue

            # 1. Process Hand Tracking
            detected_hands = tracker.process_frame(frame)
            gesture_res = gesture_engine.update(detected_hands)
            _, finger_count = gesture_engine.finger_tracker.detect_finger_states(detected_hands)

            # 2. Hand Gesture -> Direct 3D Model Control
            if detected_hands:
                dominant = detected_hands[0]
                palm_x = dominant.palm_center[0]
                palm_y = dominant.palm_center[1]

                # Two-Hand Gestures
                if len(detected_hands) >= 2:
                    h1 = detected_hands[0]
                    h2 = detected_hands[1]
                    dist = float(np.hypot(h1.palm_center[0] - h2.palm_center[0], h1.palm_center[1] - h2.palm_center[1]))
                    # Scale model with two hands
                    renderer.scale = np.clip(dist * 2.8, 0.4, 2.5)

                    if gesture_res.two_hand_gesture == "PULL_APART":
                        renderer.explode()
                    elif gesture_res.two_hand_gesture == "PUSH_TOGETHER":
                        renderer.reassemble()
                    elif gesture_res.rotation_delta:
                        renderer.rot_y += gesture_res.rotation_delta[1] * 0.8
                # Single-Hand Gestures
                else:
                    if prev_palm_pos is not None:
                        dx = palm_x - prev_palm_pos[0]
                        dy = palm_y - prev_palm_pos[1]
                        # Move & rotate model with hand motion
                        if abs(dx) < 0.2 and abs(dy) < 0.2:
                            renderer.rot_y += dx * 3.5
                            renderer.rot_x += dy * 2.5
                            renderer.trans_x = (palm_x - 0.5) * 2.5
                            renderer.trans_y = -(palm_y - 0.5) * 1.8

                    prev_palm_pos = (palm_x, palm_y)

                    # Pinch / Pointing interaction
                    if gesture_res.primary_gesture in ("PINCH", "POINT_PINCH"):
                        # Nearest component selection
                        if renderer.hovered_comp_id:
                            renderer.selected_comp_id = renderer.hovered_comp_id
                    elif gesture_res.primary_gesture == "POINT":
                        # Raycast hover test
                        if current_meta and current_meta.components:
                            renderer.hovered_comp_id = current_meta.components[1 % len(current_meta.components)].id
            else:
                prev_palm_pos = None

            # 3. Update 3D Kinematics & Render 3D Model onto Frame
            renderer.update(0.016)
            frame = renderer.render(frame)

            # 4. Draw holographic hand skeleton on top
            if detected_hands:
                frame = tracker.draw_futuristic_skeleton(frame, detected_hands)

            # 5. Draw HUD or Calibration Overlay
            if show_calibration:
                has_l = any(h.handedness.lower() == "left" for h in detected_hands)
                has_r = any(h.handedness.lower() == "right" for h in detected_hands)
                frame = CalibrationOverlay.draw(frame, tracking_quality=0.92, has_left=has_l, has_right=has_r)
            else:
                selected_name = renderer.selected_comp_id or renderer.hovered_comp_id or "NONE"
                model_name = current_meta.name if current_meta else "SPORTS BIKE"
                frame = hud.draw_telemetry(
                    frame=frame,
                    fps=camera.get_fps(),
                    model_name=model_name,
                    mode=mode,
                    gesture=gesture_res.two_hand_gesture or gesture_res.primary_gesture,
                    confidence=gesture_res.confidence,
                    finger_count=finger_count,
                    selected_component=selected_name,
                    safety_progress=gesture_res.safety_progress
                )

            cv2.imshow("HoloMechanix - Spatial Laboratory", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key in (ord('m'), ord('M')):
                # Cycle through 3D models
                if model_list:
                    model_idx = (model_idx + 1) % len(model_list)
                    current_meta = registry.get_model(model_list[model_idx]["id"])
                    if current_meta:
                        renderer.load_model(current_meta)
                        logger.info(f"Switched desktop model to: {current_meta.name}")
            elif key in (ord('c'), ord('C')):
                show_calibration = not show_calibration
            elif key in (ord('e'), ord('E')):
                renderer.explode()
            elif key in (ord('r'), ord('R')):
                renderer.reassemble()

    except KeyboardInterrupt:
        logger.info("Termination signal received.")
    finally:
        camera.stop()
        tracker.close()
        cv2.destroyAllWindows()
        logger.info("Application shut down cleanly.")

def run_web_app():
    """Web-based Tony Stark holographic interface server."""
    logger.info(f"Starting HoloMechanix Web Platform on http://{settings.HOST}:{settings.PORT}")
    try:
        # Launch browser tab
        webbrowser.open(f"http://127.0.0.1:{settings.PORT}")
    except Exception:
        pass
    uvicorn.run("app.web.server:app", host=settings.HOST, port=settings.PORT, log_level="info", reload=settings.DEBUG)

def main():
    parser = argparse.ArgumentParser(description="HoloMechanix Spatial 3D Dismantling Platform")
    parser.add_argument(
        "--mode",
        choices=["web", "desktop"],
        default="web",
        help="Execution mode: 'web' for Three.js WebGL interface, 'desktop' for OpenCV HUD window"
    )
    args = parser.parse_args()

    if args.mode == "desktop":
        run_desktop_app()
    else:
        run_web_app()

if __name__ == "__main__":
    main()
