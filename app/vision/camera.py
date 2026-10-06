import time
import logging
from typing import Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger("holomechanix.vision.camera")

class Camera:
    """Camera abstraction for HoloMechanix.
    Provides robust frame capture, FPS tracking, and synthetic fallback when physical camera is unavailable.
    """

    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720, fps: int = 30):
        self.camera_index = camera_index
        self.target_width = width
        self.target_height = height
        self.target_fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.is_synthetic = False

        # FPS calculation
        self._prev_frame_time = 0.0
        self._current_fps = 0.0
        self._frame_count = 0
        self._synthetic_phase = 0.0

    def start(self) -> bool:
        """Start the camera stream. Falls back to synthetic simulation if camera is unavailable."""
        logger.info(f"Attempting to open camera index {self.camera_index}...")
        try:
            # Use CAP_DSHOW on Windows for fast and conflict-free camera access
            import platform
            backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
            self.cap = cv2.VideoCapture(self.camera_index, backend)
            if self.cap is not None and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                self.is_running = True
                self.is_synthetic = False
                actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                logger.info(f"Physical camera initialized successfully at {actual_w}x{actual_h}")
                return True
        except Exception as e:
            logger.warning(f"Failed to open hardware camera {self.camera_index}: {e}")

        # Fallback to synthetic camera feed (virtual hand simulation for testing and headless servers)
        logger.info("Initializing synthetic laboratory camera fallback stream...")
        self.is_synthetic = True
        self.is_running = True
        return True

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame. Returns (success, frame_bgr)."""
        if not self.is_running:
            return False, None

        current_time = time.time()
        delta = current_time - self._prev_frame_time
        if delta > 0:
            self._current_fps = 0.9 * self._current_fps + 0.1 * (1.0 / delta)
        self._prev_frame_time = current_time

        if not self.is_synthetic and self.cap is not None:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Mirror horizontal for natural spatial mirror interaction
                frame = cv2.flip(frame, 1)
                return True, frame
            else:
                logger.warning("Hardware camera frame drop. Switching to synthetic fallback.")
                self.is_synthetic = True

        # Generate synthetic futuristic laboratory feed
        frame = self._generate_synthetic_frame()
        return True, frame

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Generates a high-tech laboratory camera canvas for demonstration and testing."""
        frame = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
        # Deep dark blue laboratory background
        frame[:] = (12, 16, 24)

        # Subtle cyber grid
        grid_spacing = 40
        for x in range(0, self.target_width, grid_spacing):
            cv2.line(frame, (x, 0), (x, self.target_height), (20, 30, 42), 1)
        for y in range(0, self.target_height, grid_spacing):
            cv2.line(frame, (0, y), (self.target_width, y), (20, 30, 42), 1)

        self._synthetic_phase += 0.05
        # Draw animated holographic calibration reticle
        cx, cy = self.target_width // 2, self.target_height // 2
        radius = int(80 + 10 * np.sin(self._synthetic_phase))
        cv2.circle(frame, (cx, cy), radius, (255, 240, 0), 1, cv2.LINE_AA)
        cv2.drawMarker(frame, (cx, cy), (0, 240, 255), cv2.MARKER_CROSS, 30, 1)

        cv2.putText(frame, "HOLOMECHANIX SYNTHETIC TEST FEED [SIMULATED WEBCAM]", 
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 240, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"FPS: {self.get_fps():.1f} | Hardware camera fallback active", 
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1, cv2.LINE_AA)

        return frame

    def get_fps(self) -> float:
        """Get smoothed FPS."""
        return max(1.0, self._current_fps)

    def stop(self):
        """Release camera resources."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info("Camera resources released successfully.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
