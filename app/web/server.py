import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..config.settings import settings
from ..vision.camera import Camera
from ..vision.hand_tracker import HandTracker
from ..vision.finger_tracker import FingerTracker
from ..vision.gesture_engine import GestureEngine
from ..vision.spatial_mapper import SpatialMapper
from ..models.registry import ModelRegistry
from ..models.metadata import ModelMetadata
from ..simulation.mechanisms import MechanicalSimulator
from ..education.component_info import ComponentInfoService
from ..education.learning_mode import LearningModeManager
from ..education.quiz import QuizManager
from ..education.explanations import EngineeringAIAssistant

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("holomechanix.web.server")

app = FastAPI(
    title="HoloMechanix API",
    description="Spatial 3D Dismantling & Engineering Learning Platform Backend",
    version=settings.VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
registry = ModelRegistry()
simulator = MechanicalSimulator()
camera = Camera(
    camera_index=settings.CAMERA_INDEX,
    width=settings.CAMERA_WIDTH,
    height=settings.CAMERA_HEIGHT,
    fps=settings.CAMERA_FPS
)
hand_tracker = HandTracker(
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
spatial_mapper = SpatialMapper()

# Dynamic curriculum managers
learning_managers: Dict[str, LearningModeManager] = {}
quiz_managers: Dict[str, QuizManager] = {}
ai_assistants: Dict[str, EngineeringAIAssistant] = {}

for model_id in [m["id"] for m in registry.list_models()]:
    meta = registry.get_model(model_id)
    if meta:
        learning_managers[model_id] = LearningModeManager.from_model(meta)
        quiz_managers[model_id] = QuizManager.from_model(meta)
        ai_assistants[model_id] = EngineeringAIAssistant(meta)

# REST APIs (Phase 45)
@app.get("/api/health")
def get_health():
    return {
        "status": "operational",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "camera_active": camera.is_running,
        "synthetic_mode": camera.is_synthetic,
        "models_available": len(registry.list_models())
    }

@app.get("/api/models")
def get_models():
    return registry.list_models()

@app.get("/api/models/{model_id}")
def get_model(model_id: str):
    m = registry.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return m

@app.get("/api/models/{model_id}/components")
def get_model_components(model_id: str):
    m = registry.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return m.components

@app.get("/api/components/{model_id}/{comp_id}")
def get_component_info(model_id: str, comp_id: str):
    m = registry.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    comp = next((c for c in m.components if c.id == comp_id), None)
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")
    return ComponentInfoService.format_card(comp)

@app.get("/api/learning/{model_id}")
def get_learning_step(model_id: str):
    mgr = learning_managers.get(model_id)
    if not mgr:
        raise HTTPException(status_code=404, detail="Learning curriculum not found")
    return mgr.get_current_step() or {"completed": True, "message": "All disassembly steps completed."}

class ActionValidateReq(BaseModel):
    component_id: str
    gesture: str

@app.post("/api/learning/{model_id}/validate")
def validate_learning_action(model_id: str, req: ActionValidateReq):
    mgr = learning_managers.get(model_id)
    if not mgr:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    success = mgr.validate_action(req.component_id, req.gesture)
    return {"success": success, "next_step": mgr.get_current_step()}

@app.get("/api/quiz/{model_id}")
def get_quiz_question(model_id: str):
    qmgr = quiz_managers.get(model_id)
    if not qmgr:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return qmgr.get_current_question() or {"finished": True, "final_score": qmgr.score}

class QuizAnswerReq(BaseModel):
    option_index: int

@app.post("/api/quiz/{model_id}/answer")
def submit_quiz_answer(model_id: str, req: QuizAnswerReq):
    qmgr = quiz_managers.get(model_id)
    if not qmgr:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return qmgr.submit_answer(req.option_index)

class AIQueryReq(BaseModel):
    query_type: str  # what_does_it_do, why_connected_here, what_happens_if_fails, what_should_i_remove_next
    component_id: Optional[str] = None

@app.post("/api/ai/{model_id}/ask")
def ask_ai(model_id: str, req: AIQueryReq):
    ai = ai_assistants.get(model_id)
    if not ai:
        raise HTTPException(status_code=404, detail="AI Assistant context not found")
    return ai.answer_query(req.query_type, req.component_id)

# WebSocket Real-Time Spatial Interaction Pipeline (Phase 44)
@app.websocket("/ws/spatial")
async def websocket_spatial_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket spatial client connected.")
    
    # Ensure camera is active
    if not camera.is_running:
        camera.start()

    prev_time = time.time()
    try:
        while True:
            # Throttle to capped frame rate
            await asyncio.sleep(1.0 / settings.WS_FPS_CAP)
            now = time.time()
            dt = now - prev_time
            prev_time = now

            # 1. Grab camera frame
            ret, frame = camera.read()
            if not ret or frame is None:
                continue

            # 2. Hand tracking
            detected_hands = hand_tracker.process_frame(frame)

            # 3. Gesture Engine evaluation
            gesture_res = gesture_engine.update(detected_hands)

            # 4. Mechanical simulation step
            mech_data = simulator.step(dt)

            # 5. Finger detection states
            finger_states, finger_count = gesture_engine.finger_tracker.detect_finger_states(detected_hands)

            # 6. Raycast / cursor mapping
            norm_cursor = gesture_res.cursor_pos or (0.5, 0.5, 0.0)
            ray_origin, ray_dir = spatial_mapper.compute_ray(norm_cursor[0], norm_cursor[1])

            # Package holographic telemetry packet
            packet = {
                "timestamp": now,
                "fps": round(camera.get_fps(), 1),
                "hands": [h.to_dict() for h in detected_hands],
                "finger_count": finger_count,
                "finger_states": finger_states,
                "gesture": gesture_res.to_dict(),
                "ray": {
                    "origin": [round(c, 4) for c in ray_origin],
                    "direction": [round(c, 4) for c in ray_dir]
                },
                "mechanisms": mech_data,
                "synthetic_camera": camera.is_synthetic
            }

            await websocket.send_text(json.dumps(packet))

    except WebSocketDisconnect:
        logger.info("WebSocket spatial client disconnected.")
    except Exception as e:
        logger.error(f"Error in spatial WebSocket stream: {e}")

# Static files mounting
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "HoloMechanix Web Server Running. Please compile frontend assets."}
