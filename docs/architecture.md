# HoloMechanix System Architecture

## Overview
HoloMechanix is a spatial 3D dismantling and engineering learning platform inspired by futuristic spatial interfaces (such as Tony Stark's holographic engineering workshop). It couples real-time optical hand tracking with interactive 3D WebGL computer-aided engineering visualization.

## Critical Technical Reality (Section 56)
A standard 2D monocular webcam does not emit volumetric holographic light waves. HoloMechanix instead produces a high-fidelity **Spatial 3D Interaction Illusion** by combining:
1. MediaPipe 21-landmark 3D hand tracking
2. Real-time normalized palm scale and depth approximation
3. Perspective 3D raycasting and bounding-volume intersection
4. Cyberpunk laboratory aesthetics, glowing shader outlines, and minimal technical HUD overlays.

## Subsystem Architecture

```
                          ┌─────────────────────┐
                          │   Monocular Webcam  │
                          │   (or Synthetic)    │
                          └──────────┬──────────┘
                                     │ (BGR Frame)
                                     ▼
                          ┌─────────────────────┐
                          │     OpenCV Host     │
                          │  (app/vision/cam)   │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │  MediaPipe Tracker  │
                          │  (21 3D landmarks)  │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │   10-Finger Matrix  │
                          │   & Gesture Engine  │
                          └──────────┬──────────┘
                                     │
                                     ▼
            ┌────────────────────────┴────────────────────────┐
            │                                                 │
            ▼                                                 ▼
┌─────────────────────────┐                       ┌─────────────────────────┐
│     Desktop Runner      │                       │     FastAPI Backend     │
│   (OpenCV HUD Window)   │                       │   (WebSocket Telemetry) │
└─────────────────────────┘                       └────────────┬────────────┘
                                                               │
                                                               ▼
                                                  ┌─────────────────────────┐
                                                  │    Three.js Frontend    │
                                                  │   (WebGL Engineering    │
                                                  │       Laboratory)       │
                                                  └─────────────────────────┘
```

## Modular Directory Layout
- **`app/vision/`**: Camera capture, MediaPipe tracking, 10-finger detection, gesture engine with hysteresis, and spatial coordinate mapping.
- **`app/models/`**: Semantic component hierarchy, Pydantic metadata schema, and dynamic model discovery.
- **`app/simulation/`**: Kinematic constraints (fixed, hinge, slider, rotational), slider-crank engine kinematics, and easing animation controllers.
- **`app/interaction/`**: 3D raycast selection, pinch-to-grab dragging, two-hand rotation/scaling, and exploded view dismantling.
- **`app/education/`**: Guided step-by-step curricula, engineering quiz engine, and grounded AI diagnostics assistant.
- **`app/ui/`**: Futuristic OpenCV HUD telemetry renderer and calibration overlays.
- **`app/web/`**: FastAPI REST API, WebSocket streaming pipeline, and Three.js frontend.
