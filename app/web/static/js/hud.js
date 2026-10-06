// HoloMechanix HUD Controller & Real-Time WebSocket Telemetry
class HUDController {
  constructor(scene) {
    this.scene = scene;
    this.ws = null;
    this.models = [];
    this.currentModelMeta = null;
    this.cursorEl = document.getElementById('spatial-cursor');
    this.safetyBarEl = document.getElementById('safety-hold-bar');
    this.safetyFillEl = document.getElementById('safety-hold-fill');
    this.safetyTextEl = document.getElementById('safety-hold-text');

    this.currentMode = 'FREE PLAY';
    this.init();
  }

  async init() {
    this._setupUIListeners();
    await this._fetchModels();
    this._connectWebSocket();
  }

  async _fetchModels() {
    try {
      const res = await fetch('/api/models');
      this.models = await res.json();
      this._renderModelList();
      if (this.models.length > 0) {
        await this.loadModel(this.models[0].id);
      }
    } catch (e) {
      console.error('Failed to fetch models:', e);
    }
  }

  _renderModelList() {
    const listEl = document.getElementById('model-list-container');
    if (!listEl) return;
    listEl.innerHTML = '';
    this.models.forEach((m) => {
      const item = document.createElement('div');
      item.className = `model-list-item ${m.id === this.scene.currentModelId ? 'selected' : ''}`;
      item.innerHTML = `
        <span class="model-item-name">${m.name}</span>
        <span class="model-item-cat">${m.category}</span>
      `;
      item.onclick = () => this.loadModel(m.id);
      listEl.appendChild(item);
    });
  }

  async loadModel(modelId) {
    try {
      const res = await fetch(`/api/models/${modelId}`);
      this.currentModelMeta = await res.json();
      this.scene.loadModel(this.currentModelMeta);
      document.getElementById('hud-model-name').textContent = this.currentModelMeta.name.toUpperCase();
      this._renderModelList();
      this.displayComponentCard(null);
    } catch (e) {
      console.error('Failed to load model:', e);
    }
  }

  _connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/spatial`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      document.getElementById('tracking-status-val').textContent = 'CONNECTED';
      document.getElementById('tracking-status-val').style.color = 'var(--accent-green)';
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this._handleTelemetry(data);
      } catch (err) {
        console.error('Telemetry parse error:', err);
      }
    };

    this.ws.onclose = () => {
      document.getElementById('tracking-status-val').textContent = 'OFFLINE (RETRY)';
      document.getElementById('tracking-status-val').style.color = 'var(--accent-red)';
      setTimeout(() => this._connectWebSocket(), 2000);
    };
  }

  _handleTelemetry(data) {
    // 1. Telemetry connection indicators
    if (data.fps && !window.isClientTrackingActive) {
      document.getElementById('fps-counter').textContent = data.fps.toFixed(1);
    }

    // If client-side browser tracking is active, do not overwrite real hand telemetry with idle server packets!
    if (window.isClientTrackingActive) {
      return;
    }

    if (data.synthetic_camera) {
      document.getElementById('tracking-status-val').textContent = 'SIMULATED (LAB)';
      document.getElementById('tracking-status-val').style.color = 'var(--amber-primary)';
    } else {
      document.getElementById('tracking-status-val').textContent = 'HARDWARE OPTICAL';
      document.getElementById('tracking-status-val').style.color = 'var(--accent-green)';
    }

    // 2. Gesture Telemetry (fallback when client tracking is inactive)
    if (data.gesture) {
      const g = data.gesture;
      const gName = g.two_hand_gesture || g.primary_gesture || 'IDLE';
      document.getElementById('active-gesture-name').textContent = gName;
      document.getElementById('gesture-conf-val').textContent = `${Math.round((g.confidence || 0) * 100)}%`;

      // Two-Hand Rotation
      if (g.rotation_delta) {
        this.scene.targetRotation.y += g.rotation_delta[1] * 0.15;
      }

      // Two-Hand Scale
      if (g.scale_delta && g.scale_delta !== 1.0) {
        this.scene.targetScale = Math.max(0.4, Math.min(2.8, this.scene.targetScale * g.scale_delta));
      }

      // Exploded View Safety Hold
      if (g.safety_progress && g.safety_progress > 0.0) {
        this.safetyBarEl.style.display = 'block';
        const pct = Math.round(g.safety_progress * 100);
        this.safetyFillEl.style.width = `${pct}%`;
        this.safetyTextEl.textContent = `PULL APART DETECTED: ${pct}%`;
      } else {
        this.safetyBarEl.style.display = 'none';
      }

      // Two-Hand Explode & Reassemble triggers
      if (g.two_hand_gesture === 'PULL_APART') {
        this.scene.explode();
      } else if (g.two_hand_gesture === 'PUSH_TOGETHER') {
        this.scene.reassemble();
      }
    }

    // 3. 10-Finger Matrix Visualizer
    if (data.finger_states) {
      const fs = data.finger_states;
      const fingers = ['thumb', 'index', 'middle', 'ring', 'pinky'];
      fingers.forEach((f) => {
        const leftDot = document.getElementById(`f-left-${f}`);
        if (leftDot) leftDot.classList.toggle('active', !!fs.left[f]);
        const rightDot = document.getElementById(`f-right-${f}`);
        if (rightDot) rightDot.classList.toggle('active', !!fs.right[f]);
      });
    }

    if (data.finger_count !== undefined) {
      document.getElementById('tracked-fingers-val').textContent = `${data.finger_count} / 10`;
    }

    // 4. Spatial 3D Cursor Positioning
    if (data.gesture && data.gesture.cursor_pos) {
      const [nx, ny] = data.gesture.cursor_pos;
      const screenX = nx * window.innerWidth;
      const screenY = ny * window.innerHeight;
      this.cursorEl.style.display = 'block';
      this.cursorEl.style.left = `${screenX}px`;
      this.cursorEl.style.top = `${screenY}px`;

      this.scene.mouse.x = (nx * 2) - 1;
      this.scene.mouse.y = -(ny * 2) + 1;
      this.scene._checkRaycast();

      if (data.gesture.primary_gesture === 'PINCH' && this.scene.hoveredComponentId) {
        this.scene.selectComponent(this.scene.hoveredComponentId);
      }
    } else {
      this.cursorEl.style.display = 'none';
    }
  }

  displayComponentCard(compData) {
    const card = document.getElementById('component-card-body');
    if (!compData) {
      card.innerHTML = `
        <div class="card-row">
          <span class="card-label">SELECTION</span>
          <span class="card-value highlight">NONE // POINT TO SELECT</span>
        </div>
        <div class="card-row">
          <span class="card-label">MANIPULATION GUIDE</span>
          <span class="card-value" style="font-size:11px; color:var(--text-dim);">
            • Point index finger to highlight part<br>
            • Pinch (Thumb + Index) to grab / inspect<br>
            • Pull apart hands to explode view<br>
            • Push hands together to reassemble
          </span>
        </div>
      `;
      document.getElementById('ai-btn-container').style.display = 'none';
      return;
    }

    card.innerHTML = `
      <div class="card-row">
        <span class="card-label">COMPONENT NAME</span>
        <span class="card-value highlight">${compData.name.toUpperCase()}</span>
      </div>
      <div class="card-row">
        <span class="card-label">SUBSYSTEM CATEGORY</span>
        <span class="card-value">${compData.category}</span>
      </div>
      <div class="card-row">
        <span class="card-label">ENGINEERING FUNCTION</span>
        <span class="card-value" style="font-size:12px;">${compData.function}</span>
      </div>
      <div class="card-row">
        <span class="card-label">MATERIAL COMPOSITION</span>
        <span class="card-value" style="font-size:12px;">${compData.material}</span>
      </div>
      <div class="card-row">
        <span class="card-label">PRIMARY FAILURE MECHANISM</span>
        <span class="card-value" style="font-size:12px; color:var(--accent-red);">${compData.common_failure}</span>
      </div>
    `;
    document.getElementById('ai-btn-container').style.display = 'grid';
  }

  async queryAI(queryType) {
    if (!this.currentModelMeta) return;
    const compId = this.scene.selectedComponentId;
    const resBox = document.getElementById('ai-response-box');
    resBox.textContent = 'Processing engineering diagnostics query...';

    try {
      const res = await fetch(`/api/ai/${this.currentModelMeta.id}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_type: queryType, component_id: compId })
      });
      const data = await res.json();
      resBox.innerHTML = `<strong>${data.known_data}</strong><br><br>${data.educational_explanation.replace(/\n/g, '<br>')}`;
    } catch (e) {
      resBox.textContent = 'Failed to fetch AI diagnostics.';
    }
  }

  _setupUIListeners() {
    // Mode toggles
    document.getElementById('btn-free-play').onclick = () => this.setMode('FREE PLAY');
    document.getElementById('btn-learning-mode').onclick = () => this.openLearningModal();
    document.getElementById('btn-quiz-mode').onclick = () => this.openQuizModal();
    document.getElementById('btn-calibration').onclick = () => this.openCalibrationModal();

    // Center dock buttons
    document.getElementById('dock-explode-btn').onclick = () => {
      if (this.scene.explosionFactor > 0.5) {
        this.scene.reassemble();
        document.getElementById('dock-explode-btn').classList.remove('active-explode');
        document.getElementById('dock-explode-btn').innerHTML = '<span>💥</span> EXPLODE ASSEMBLY';
      } else {
        this.scene.explode();
        document.getElementById('dock-explode-btn').classList.add('active-explode');
        document.getElementById('dock-explode-btn').innerHTML = '<span>🔄</span> REASSEMBLE';
      }
    };

    document.getElementById('dock-reset-btn').onclick = () => {
      this.scene.reassemble();
      this.scene.targetRotation.set(0, 0, 0);
      this.scene.targetScale = 1.0;
    };

    // Component selected callback hook
    window.onComponentSelected = async (compId) => {
      if (!compId || !this.currentModelMeta) {
        this.displayComponentCard(null);
        return;
      }
      try {
        const res = await fetch(`/api/components/${this.currentModelMeta.id}/${compId}`);
        const data = await res.json();
        this.displayComponentCard(data);
      } catch (e) {
        console.error('Failed to get component card:', e);
      }
    };
  }

  setMode(mode) {
    this.currentMode = mode;
    document.getElementById('hud-mode-name').textContent = mode;
    document.querySelectorAll('.nav-btn').forEach((b) => b.classList.remove('active'));
    if (mode === 'FREE PLAY') document.getElementById('btn-free-play').classList.add('active');
  }

  // Phase 21: Learning Mode Modal
  async openLearningModal() {
    this.setMode('LEARNING MODE');
    const modal = document.getElementById('learning-modal');
    modal.style.display = 'flex';
    this.fetchLearningStep();
  }

  async fetchLearningStep() {
    if (!this.currentModelMeta) return;
    try {
      const res = await fetch(`/api/learning/${this.currentModelMeta.id}`);
      const data = await res.json();
      const content = document.getElementById('learning-modal-body');
      if (data.completed) {
        content.innerHTML = `<h3 style="color:var(--accent-green);">Curriculum Complete!</h3><p>${data.message}</p>`;
        return;
      }
      content.innerHTML = `
        <div style="font-family:var(--font-mono); color:var(--cyan-primary); font-size:13px; margin-bottom:8px;">
          STEP ${data.step_number} OF ${data.total_steps}
        </div>
        <h4 style="font-size:16px; margin-bottom:6px;">Target Component: ${data.component_id.toUpperCase()}</h4>
        <p style="color:var(--text-primary); margin-bottom:12px;"><strong>Instruction:</strong> ${data.instruction}</p>
        <div style="background:rgba(0,240,255,0.06); padding:10px; border-left:2px solid var(--cyan-primary); font-size:12px; margin-bottom:15px;">
          ${data.explanation}
        </div>
        <button class="nav-btn active" id="validate-step-btn" style="width:100%;">EXECUTE STEP (SIMULATE GESTURE)</button>
      `;
      // Auto highlight target component in 3D scene
      this.scene.selectComponent(data.component_id);

      document.getElementById('validate-step-btn').onclick = async () => {
        await fetch(`/api/learning/${this.currentModelMeta.id}/validate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ component_id: data.component_id, gesture: data.required_gesture })
        });
        if (window.soundFX) window.soundFX.playSuccess();
        this.fetchLearningStep();
      };
    } catch (e) {
      console.error(e);
    }
  }

  // Phase 40: Quiz Mode Modal
  async openQuizModal() {
    this.setMode('QUIZ MODE');
    const modal = document.getElementById('quiz-modal');
    modal.style.display = 'flex';
    this.fetchQuizQuestion();
  }

  async fetchQuizQuestion() {
    if (!this.currentModelMeta) return;
    try {
      const res = await fetch(`/api/quiz/${this.currentModelMeta.id}`);
      const data = await res.json();
      const body = document.getElementById('quiz-modal-body');
      if (data.finished) {
        body.innerHTML = `
          <h3 style="color:var(--accent-green); margin-bottom:10px;">QUIZ COMPLETE!</h3>
          <p>Your Engineering Proficiency Score: <strong>${data.final_score} Points</strong></p>
          <button class="nav-btn active" onclick="hudController.closeModals()" style="margin-top:15px;">RETURN TO LABORATORY</button>
        `;
        return;
      }
      body.innerHTML = `
        <div style="font-family:var(--font-mono); color:var(--cyan-primary); font-size:12px; margin-bottom:6px;">
          QUESTION ${data.index + 1} OF ${data.total} | CURRENT SCORE: ${data.current_score}
        </div>
        <p style="font-size:15px; font-weight:600; margin-bottom:14px;">${data.question}</p>
        <div class="quiz-options">
          ${data.options.map((opt, idx) => `
            <button class="quiz-opt-btn" onclick="hudController.submitAnswer(${idx})">${String.fromCharCode(65 + idx)}. ${opt}</button>
          `).join('')}
        </div>
        <div id="quiz-feedback" class="quiz-feedback"></div>
      `;
    } catch (e) {
      console.error(e);
    }
  }

  async submitAnswer(optionIndex) {
    try {
      const res = await fetch(`/api/quiz/${this.currentModelMeta.id}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ option_index: optionIndex })
      });
      const data = await res.json();
      const fb = document.getElementById('quiz-feedback');
      fb.style.display = 'block';
      if (data.correct) {
        fb.className = 'quiz-feedback correct';
        fb.innerHTML = `<strong>CORRECT!</strong> ${data.explanation}`;
        if (window.soundFX) window.soundFX.playSuccess();
      } else {
        fb.className = 'quiz-feedback incorrect';
        fb.innerHTML = `<strong>INCORRECT.</strong> Correct answer: ${data.correct_option}.<br>${data.explanation}`;
        if (window.soundFX) window.soundFX.playBlip();
      }
      setTimeout(() => this.fetchQuizQuestion(), 2000);
    } catch (e) {
      console.error(e);
    }
  }

  // Phase 35: Calibration Screen
  openCalibrationModal() {
    this.setMode('CALIBRATION');
    document.getElementById('calibration-modal').style.display = 'flex';
  }

  closeModals() {
    document.querySelectorAll('.modal-overlay').forEach((m) => (m.style.display = 'none'));
    this.setMode('FREE PLAY');
  }
}

window.HUDController = HUDController;
