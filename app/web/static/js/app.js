// HoloMechanix Master Application Bootstrap with Direct Client-Side MediaPipe Hands
document.addEventListener('DOMContentLoaded', () => {
  console.log('Bootstrapping HoloMechanix Spatial 3D Platform...');

  // 1. Initialize 3D Scene
  const scene = new HoloScene('canvas-container');
  window.holoScene = scene;

  // 2. Initialize HUD Controller
  const hud = new HUDController(scene);
  window.hudController = hud;

  // 3. Initialize Voice Controller
  const voice = new VoiceController(scene, hud);
  window.voiceController = voice;

  // 4. Initialize In-Browser MediaPipe Hand Tracking
  initInBrowserHandTracking(scene, hud);
});

// Toggle Webcam Monitor Display Size
window.toggleWebcamSize = function() {
  const panel = document.getElementById('webcam-monitor-panel');
  const btn = document.getElementById('webcam-size-btn');
  if (!panel || !btn) return;
  const isLarge = panel.classList.toggle('large');
  btn.textContent = isLarge ? '⤡ SHRINK' : '⤢ EXPAND';
  if (window.soundFX) window.soundFX.playBlip();
};

// 21-Landmark hand skeleton connections
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],        // Thumb
  [0, 5], [5, 6], [6, 7], [7, 8],        // Index
  [5, 9], [9, 10], [10, 11], [11, 12],   // Middle
  [9, 13], [13, 14], [14, 15], [15, 16], // Ring
  [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
  [0, 17]                                // Palm base
];

function initInBrowserHandTracking(scene, hud) {
  const videoEl = document.getElementById('webcam-video');
  const canvasEl = document.getElementById('webcam-canvas');
  if (!videoEl || !canvasEl) return;

  const ctx = canvasEl.getContext('2d');

  if (typeof Hands === 'undefined') {
    console.warn('MediaPipe Hands JS loading from CDN... retrying in 800ms');
    setTimeout(() => initInBrowserHandTracking(scene, hud), 800);
    return;
  }

  console.log('Activating MediaPipe Hands in browser...');
  const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
  });

  hands.setOptions({
    maxNumHands: 2,
    modelComplexity: 1,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
  });

  let prevHandDistance = null;
  let prevHandAngle = null;
  let prevSinglePalm = null;
  let pullApartHoldStart = 0;
  let isGrabbingPart = false;

  hands.onResults((results) => {
    // Flag client tracking as active to protect against idle server packets
    window.isClientTrackingActive = true;

    // Synchronize canvas dimensions
    if (canvasEl.width !== videoEl.videoWidth || canvasEl.height !== videoEl.videoHeight) {
      canvasEl.width = videoEl.videoWidth || 640;
      canvasEl.height = videoEl.videoHeight || 480;
    }

    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

    const hasHands = results.multiHandLandmarks && results.multiHandLandmarks.length > 0;
    const trackingStatusEl = document.getElementById('tracking-status-val');

    if (!hasHands) {
      prevHandDistance = null;
      prevHandAngle = null;
      prevSinglePalm = null;
      pullApartHoldStart = 0;
      isGrabbingPart = false;

      if (trackingStatusEl) {
        trackingStatusEl.textContent = 'RAISE HANDS IN FRONT OF CAMERA';
        trackingStatusEl.style.color = 'var(--amber-primary)';
      }
      const activeGEl = document.getElementById('active-gesture-name');
      if (activeGEl) activeGEl.textContent = 'STANDBY';
      const confEl = document.getElementById('gesture-conf-val');
      if (confEl) confEl.textContent = '0%';
      const cursorEl = document.getElementById('spatial-cursor');
      if (cursorEl) cursorEl.style.display = 'none';

      document.querySelectorAll('.finger-dot').forEach(d => d.classList.remove('active'));
      return;
    }

    if (trackingStatusEl) {
      trackingStatusEl.textContent = `OPTICAL TRACKING (${results.multiHandLandmarks.length} HAND${results.multiHandLandmarks.length > 1 ? 'S' : ''})`;
      trackingStatusEl.style.color = 'var(--accent-green)';
    }

    // 1. Draw glowing neon skeleton on camera monitor
    results.multiHandLandmarks.forEach((landmarks) => {
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 3;
      HAND_CONNECTIONS.forEach(([i1, i2]) => {
        const p1 = landmarks[i1];
        const p2 = landmarks[i2];
        ctx.beginPath();
        ctx.moveTo(p1.x * canvasEl.width, p1.y * canvasEl.height);
        ctx.lineTo(p2.x * canvasEl.width, p2.y * canvasEl.height);
        ctx.stroke();
      });

      landmarks.forEach((lm, idx) => {
        const isTip = [4, 8, 12, 16, 20].includes(idx);
        ctx.beginPath();
        ctx.arc(lm.x * canvasEl.width, lm.y * canvasEl.height, isTip ? 6 : 3, 0, 2 * Math.PI);
        ctx.fillStyle = isTip ? '#ffaa00' : '#ffffff';
        ctx.fill();
      });
    });

    // 2. Evaluate 10-Finger Matrix
    let totalFingersCount = 0;
    results.multiHandLandmarks.forEach((landmarks, hIdx) => {
      const handednessInfo = results.multiHandedness && results.multiHandedness[hIdx];
      const rawSide = handednessInfo ? handednessInfo.label : (hIdx === 0 ? 'Right' : 'Left');
      const side = (rawSide === 'Right' ? 'left' : 'right'); // Mirrored for user intuition

      const fingers = {
        thumb: Math.hypot(landmarks[4].x - landmarks[17].x, landmarks[4].y - landmarks[17].y) > 0.16,
        index: landmarks[8].y < landmarks[6].y,
        middle: landmarks[12].y < landmarks[10].y,
        ring: landmarks[16].y < landmarks[14].y,
        pinky: landmarks[20].y < landmarks[18].y
      };

      Object.entries(fingers).forEach(([fName, isOpen]) => {
        const dot = document.getElementById(`f-${side}-${fName}`);
        if (dot) dot.classList.toggle('active', isOpen);
        if (isOpen) totalFingersCount++;
      });
    });

    const fingerCountEl = document.getElementById('tracked-fingers-val');
    if (fingerCountEl) fingerCountEl.textContent = `${totalFingersCount} / 10`;

    // 3. Dominant Hand Mapping
    const dominantHand = results.multiHandLandmarks[0];
    const indexTip = dominantHand[8];
    const thumbTip = dominantHand[4];
    const wrist = dominantHand[0];
    const middleMcp = dominantHand[9];

    // Compute mirrored coordinates
    const palmX = 1.0 - middleMcp.x;
    const palmY = middleMcp.y;

    // Cursor reticle follows index tip
    const cursorEl = document.getElementById('spatial-cursor');
    const screenX = (1.0 - indexTip.x) * window.innerWidth;
    const screenY = indexTip.y * window.innerHeight;
    if (cursorEl) {
      cursorEl.style.display = 'block';
      cursorEl.style.left = `${screenX}px`;
      cursorEl.style.top = `${screenY}px`;
    }

    // Raycast hit-test in 3D scene
    scene.mouse.x = ((1.0 - indexTip.x) * 2) - 1;
    scene.mouse.y = -(indexTip.y * 2) + 1;
    scene._checkRaycast();

    // Check Pinch gesture
    const pinchDist = Math.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y);
    const isPinching = pinchDist < 0.06;

    let activeGesture = 'HAND TRACKED';
    let gestureConfidence = 0.96;

    // A. TWO-HAND INTERACTION (When user raises both hands)
    if (results.multiHandLandmarks.length >= 2) {
      const h1 = results.multiHandLandmarks[0][9];
      const h2 = results.multiHandLandmarks[1][9];

      const currentDist = Math.hypot(h1.x - h2.x, h1.y - h2.y);
      const currentAngle = Math.atan2(h1.y - h2.y, h1.x - h2.x);

      // Average center of both hands moves the model in 3D
      const avgX = 1.0 - ((h1.x + h2.x) / 2.0);
      const avgY = (h1.y + h2.y) / 2.0;
      scene.targetPosition.x = (avgX - 0.5) * 3.0;
      scene.targetPosition.y = (0.5 - avgY) * 2.2;

      if (prevHandDistance !== null) {
        const distDelta = currentDist - prevHandDistance;
        const angleDelta = currentAngle - prevHandAngle;

        // Two-Hand Scaling (Zoom)
        if (Math.abs(distDelta) > 0.01) {
          const scaleChange = 1.0 + (distDelta * 3.5);
          scene.targetScale = Math.max(0.35, Math.min(3.5, scene.targetScale * scaleChange));
          activeGesture = distDelta > 0 ? 'ZOOM IN (HANDS SPREAD)' : 'ZOOM OUT (HANDS PINCH)';
        }

        // Two-Hand Steering/Rotation
        if (Math.abs(angleDelta) > 0.02) {
          scene.targetRotation.y += angleDelta * 2.0;
          activeGesture = 'ROTATE MODEL (TWO HANDS)';
        }

        // Explode / Reassemble by Pull Apart / Push Together
        if (distDelta > 0.038) {
          activeGesture = 'PULL APART (EXPLODE)';
          const now = Date.now();
          if (!pullApartHoldStart) pullApartHoldStart = now;
          const elapsed = (now - pullApartHoldStart) / 1000.0;
          const safetyPct = Math.min(1.0, elapsed / 0.35);

          const safetyBar = document.getElementById('safety-hold-bar');
          const safetyFill = document.getElementById('safety-hold-fill');
          const safetyText = document.getElementById('safety-hold-text');
          if (safetyBar) {
            safetyBar.style.display = 'block';
            safetyFill.style.width = `${Math.round(safetyPct * 100)}%`;
            safetyText.textContent = `PULL APART: ${Math.round(safetyPct * 100)}%`;
          }

          if (safetyPct >= 1.0) {
            scene.explode();
            pullApartHoldStart = 0;
            if (safetyBar) safetyBar.style.display = 'none';
          }
        } else if (distDelta < -0.038) {
          activeGesture = 'PUSH TOGETHER (REASSEMBLE)';
          scene.reassemble();
          pullApartHoldStart = 0;
          const safetyBar = document.getElementById('safety-hold-bar');
          if (safetyBar) safetyBar.style.display = 'none';
        } else {
          pullApartHoldStart = 0;
          const safetyBar = document.getElementById('safety-hold-bar');
          if (safetyBar) safetyBar.style.display = 'none';
        }
      }

      prevHandDistance = currentDist;
      prevHandAngle = currentAngle;
      prevSinglePalm = null;
    }
    // B. SINGLE HAND DIRECT MANIPULATION (Entire model works on hand movement!)
    else {
      prevHandDistance = null;
      prevHandAngle = null;

      // Direct Spatial Parallax: Model follows hand position in 3D!
      scene.targetPosition.x = (palmX - 0.5) * 2.6;
      scene.targetPosition.y = (0.5 - palmY) * 1.8;

      if (prevSinglePalm) {
        const dx = palmX - prevSinglePalm.x;
        const dy = palmY - prevSinglePalm.y;

        // 1. PINCH -> GRAB & DETACH PART DIRECTLY WITH HAND
        if (isPinching) {
          activeGesture = 'PINCH (GRAB PART)';
          if (scene.hoveredComponentId && !scene.selectedComponentId) {
            scene.selectComponent(scene.hoveredComponentId);
            if (window.soundFX) window.soundFX.playGrab();
          }

          if (scene.selectedComponentId) {
            const compMesh = scene.componentMeshes.get(scene.selectedComponentId);
            if (compMesh) {
              compMesh.position.x += dx * 5.0;
              compMesh.position.y -= dy * 5.0;
              compMesh.userData.manualOffset = true;
              activeGesture = `MOVING: ${scene.selectedComponentId.toUpperCase()}`;
            }
          }
        }
        // 2. OPEN PALM / MOVING HAND -> ROTATE MODEL SMOOTHLY IN 3D
        else {
          if (Math.hypot(dx, dy) < 0.25) {
            scene.targetRotation.y += dx * 4.5;
            scene.targetRotation.x += dy * 3.5;
            activeGesture = 'HAND MOTION (ROTATE MODEL)';
          }

          // Point to highlight
          if (indexTip.y < middleMcp.y) {
            if (scene.hoveredComponentId && scene.hoveredComponentId !== scene.selectedComponentId) {
              scene.selectComponent(scene.hoveredComponentId);
              if (window.soundFX) window.soundFX.playBlip();
            }
          }
        }
      }

      prevSinglePalm = { x: palmX, y: palmY };
    }

    // Update HUD telemetry
    const activeGEl = document.getElementById('active-gesture-name');
    if (activeGEl) activeGEl.textContent = activeGesture;
    const confEl = document.getElementById('gesture-conf-val');
    if (confEl) confEl.textContent = `${Math.round(gestureConfidence * 100)}%`;
  });

  // Start Camera
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user'
      }
    }).then((stream) => {
      videoEl.srcObject = stream;
      videoEl.play();

      if (typeof Camera !== 'undefined') {
        const camera = new Camera(videoEl, {
          onFrame: async () => {
            await hands.send({ image: videoEl });
          },
          width: 640,
          height: 480
        });
        camera.start();
        console.log('MediaPipe Camera loop started.');
      } else {
        async function processFrame() {
          if (videoEl.readyState >= 2) {
            await hands.send({ image: videoEl });
          }
          requestAnimationFrame(processFrame);
        }
        requestAnimationFrame(processFrame);
      }
    }).catch((err) => {
      console.error('Camera access error:', err);
      if (trackingStatusEl) {
        trackingStatusEl.textContent = 'CAMERA BLOCKED / PERMISSION DENIED';
        trackingStatusEl.style.color = 'var(--accent-red)';
      }
    });
  }
}
