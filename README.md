# 🌐 HoloMechanix
### *Interactive Spatial 3D Dismantling & Engineering Learning Platform*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands_21_Landmarks-cyan.svg)](https://google.github.io/mediapipe/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async_WebSockets-009688.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL_3D_Engine-black.svg)](https://threejs.org/)
[![Tests](https://img.shields.io/badge/Tests-11_Passed-brightgreen.svg)]()

---

## ⚡ Overview
**HoloMechanix** is a futuristic, webcam-driven spatial engineering platform inspired by Tony Stark's holographic workshop interface. It allows engineers, mechanics, and students to stand in front of a standard camera, manipulate 3D engineering models with both hands and all 10 fingers in real time, explode assemblies into individual sub-components, inspect mechanical kinematics, and reassemble them seamlessly.

> [!NOTE]
> **Technical Reality Note (Section 56):** Standard 2D monocular webcams cannot project optical volumetric holograms into physical air. HoloMechanix creates an engineered **Spatial 3D Interaction Illusion** by fusing MediaPipe 21-landmark optical hand tracking, normalized palm perspective depth estimation, 3D raycasting, and high-performance WebGL graphics.

---

## 🛠️ Key Features

- **🤲 Optical 10-Finger Tracking**: Detects both left and right hands, all 10 fingers, 21 landmarks per hand, and palm orientation.
- **✨ Full Gesture Engine**:
  - `Point`: Raycast pointing to select parts.
  - `Pinch`: Grab and translate parts attached to cursor.
  - `Pull Apart`: Trigger exploded view (protected by 0.5s safety hold).
  - `Push Together`: Reassemble and collapse components.
  - `Two-Hand Rotation`: Freely rotate machine around 3D axes.
  - `Two-Hand Scale`: Zoom in and out smoothly.
- **💥 Kinematic Constraints & Simulation**:
  - Piston slider-crank linkages, meshing gear trains, and spinning wheels/brake discs.
  - Hinge, slider, rotational, and fixed kinematic constraints.
- **📚 Guided Learning & Quiz Modes**:
  - Step-by-step disassembly curricula with real-time gesture validation.
  - Interactive multiple-choice engineering quizzes assessing comprehension.
- **🤖 Grounded AI Diagnostics Assistant**:
  - Evaluates component function, connection rationale, failure consequences, and disassembly order without hallucinations.
- **🎙️ Voice Commands (Phase 28)**:
  - Hands-free control via Web Speech API: *"explode assembly"*, *"reassemble"*, *"engine"*, *"battery"*, *"rotate left"*, etc.
- **🎵 Synthesized Sci-Fi Sound FX**:
  - Real-time procedural audio synthesis via Web Audio API (tactile blips, grabs, swooshes).

---

## 🏗️ Project Architecture

```
HoloMechanix/
├── app/
│   ├── main.py                  # Main entrypoint (web & desktop modes)
│   ├── config/settings.py       # Configuration & environment variables
│   ├── vision/                  # Camera, MediaPipe Hand & Finger Trackers, Gesture Engine
│   ├── models/                  # Pydantic schemas, Hierarchy trees, Registry
│   ├── simulation/              # Constraints, Kinematic linkages, Animation eases
│   ├── interaction/             # Raycast selection, Pinch grabbing, Dismantling
│   ├── education/               # Learning curricula, Quizzes, AI Assistant
│   ├── ui/                      # OpenCV HUD & Calibration overlays
│   └── web/                     # FastAPI server, WebSockets, Three.js Frontend
├── assets/models/               # Extensible 3D model metadata catalogs
├── docs/                        # Detailed architectural specifications
├── tests/                       # Pytest automated test suites
├── scripts/                     # Standalone run & calibration scripts
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment defaults
├── Dockerfile                   # Container configuration
└── docker-compose.yml           # Multi-container orchestration
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- A standard USB or built-in monocular webcam

### 2. Installation
```bash
# Clone or navigate to the workspace
cd "c:\AJ Projects\holomechanix"

# Create a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
Copy the template configuration:
```bash
copy .env.example .env
```

---

## 🎮 Running HoloMechanix

### Option A: Web Mode (Futuristic Three.js Spatial Lab - Recommended)
```bash
python app/main.py --mode web
```
This boots the FastAPI WebSocket server and automatically opens your web browser to **`http://127.0.0.1:8000`**.

### Option B: Native Desktop OpenCV HUD Mode
```bash
python app/main.py --mode desktop
```
Opens a high-tech HUD OpenCV viewport with direct MediaPipe skeleton overlay and telemetry diagnostics.
- `ESC`: Exit
- `C`: Toggle Spatial Calibration Screen
- `E`: Trigger Exploded View
- `R`: Reassemble Model

### Option C: Standalone Scripts
```bash
python scripts/run_web.py      # Launch Web Platform
python scripts/run_desktop.py  # Launch Desktop Window
python scripts/calibrate.py    # Launch Calibration Setup
```

---

## 📦 Built-In 3D Model Catalog

1. **2025 Apex Sports Motorcycle** (`sports_bike`): Trellis frame, inline-4 engine, pressurized fuel tank, lithium battery, air filter, spark plug, titanium exhaust, wheels, radial brakes, USD forks.
2. **Four-Stroke Internal Combustion Engine** (`combustion_engine`): Crankcase block, cylinder head, spark plug, reciprocating piston, connecting rod, counterweighted crankshaft, and heavy flywheel.
3. **Constant-Mesh Mechanical Gearbox** (`mechanical_gearbox`): Split casing, input shaft with drive pinion, counter gear cluster, output shaft, and hardened selector fork.
4. **Quantum 16 Ultra Smartphone** (`smartphone`): Titanium chassis, flexible OLED panel, solid-state battery, logic motherboard, and periscope camera array.

### Adding New Custom Models (Phase 25)
Create a new directory in `assets/models/<model_id>/` containing a `metadata.json` matching the schema documented in [docs/model-system.md](docs/model-system.md). HoloMechanix will auto-discover and register it on startup without touching Python code!

---

## 🧪 Automated Testing

Run the full automated test suite:
```bash
python -m pytest
```

---

## 🐳 Docker Containerization

To run HoloMechanix in Docker:
```bash
docker compose up --build
```
Navigate to `http://localhost:8000`.

---

## 📄 License
MIT License. Built for spatial computing and educational engineering.
