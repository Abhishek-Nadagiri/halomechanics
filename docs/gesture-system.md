# Gesture Recognition & Stabilization System

## Core Gestures

| Gesture | Hand Configuration | Action Triggered |
|---|---|---|
| **Point** | Index extended, others flexed | Casts ray from eye through cursor to select 3D parts |
| **Pinch** | Thumb & Index tips in close proximity (`< 0.06` palm scale) | Grabs selected component and attaches it to spatial cursor |
| **Open Palm** | 4 or 5 fingers extended | Activates free interaction mode |
| **Fist** | Most or all fingers flexed | Pauses interaction |
| **Pull Apart** | Both hands open and separating (`> 0.035` delta) | Initiates Exploded View (requires 0.5s safety hold) |
| **Push Together** | Both hands open and converging | Initiates Reassembly sequence |
| **Two-Hand Rotate**| Both hands tracked, relative angular rotation | Rotates model around Y-axis |
| **Two-Hand Pinch** | Both hands pinching, distance modulated | Zooms / scales model (0.35x - 3.0x) |

## Stabilization & Safety Architecture (Phases 5 & 31)

### 1. Exponential Moving Average (EMA)
Spatial cursor position undergoes EMA filtering:
$$C_t = \alpha \cdot X_t + (1 - \alpha) \cdot C_{t-1}$$
with $\alpha = 0.65$ to eliminate optical high-frequency tremor while retaining low latency.

### 2. Gesture Hysteresis (150ms)
To avoid jitter between adjacent gesture classifications, a new candidate gesture must remain stable for at least 150 milliseconds before it is committed as the active command.

### 3. Explode Safety Hold (0.5s Hold Bar)
Major destructive operations (e.g. Exploding the entire motorcycle assembly) require the user to maintain the **Pull Apart** gesture continuously for 0.5 seconds. A HUD progress bar fills from 0% to 100% to prevent accidental trigger.
