// HoloMechanix Phase 28 Voice Command Assistant
class VoiceController {
  constructor(scene, hud) {
    this.scene = scene;
    this.hud = hud;
    this.recognition = null;
    this.isListening = false;
    this._init();
  }

  _init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Web Speech API not supported in this browser.');
      document.getElementById('voice-status-text').textContent = 'UNSUPPORTED';
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';

    this.recognition.onstart = () => {
      this.isListening = true;
      document.getElementById('voice-status-text').textContent = 'VOICE ACTIVE';
      document.getElementById('voice-status-indicator').style.display = 'flex';
    };

    this.recognition.onresult = (event) => {
      const last = event.results.length - 1;
      const cmd = event.results[last][0].transcript.trim().toLowerCase();
      console.log('Voice Command Received:', cmd);
      this._executeCommand(cmd);
    };

    this.recognition.onerror = (e) => {
      console.warn('Voice error:', e.error);
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        try { this.recognition.start(); } catch (err) {}
      }
    };

    // Auto-start listening on first user interaction
    window.addEventListener('click', () => {
      if (!this.isListening && this.recognition) {
        try {
          this.recognition.start();
        } catch (e) {}
      }
    }, { once: true });
  }

  _executeCommand(cmd) {
    const feedbackEl = document.getElementById('voice-status-text');
    feedbackEl.textContent = `CMD: "${cmd.toUpperCase()}"`;
    setTimeout(() => {
      if (this.isListening) feedbackEl.textContent = 'VOICE ACTIVE';
    }, 2500);

    if (cmd.includes('explode')) {
      this.scene.explode();
    } else if (cmd.includes('reassemble') || cmd.includes('assemble')) {
      this.scene.reassemble();
    } else if (cmd.includes('engine')) {
      this.scene.selectComponent('engine');
    } else if (cmd.includes('battery')) {
      this.scene.selectComponent('battery');
    } else if (cmd.includes('spark plug')) {
      this.scene.selectComponent('spark_plug');
    } else if (cmd.includes('rotate left')) {
      this.scene.targetRotation.y += 0.8;
    } else if (cmd.includes('rotate right')) {
      this.scene.targetRotation.y -= 0.8;
    } else if (cmd.includes('zoom in')) {
      this.scene.targetScale = Math.min(2.5, this.scene.targetScale + 0.3);
    } else if (cmd.includes('zoom out')) {
      this.scene.targetScale = Math.max(0.5, this.scene.targetScale - 0.3);
    } else if (cmd.includes('learning')) {
      this.hud.openLearningModal();
    } else if (cmd.includes('quiz')) {
      this.hud.openQuizModal();
    } else if (cmd.includes('free play') || cmd.includes('close')) {
      this.hud.closeModals();
    }
  }
}

window.VoiceController = VoiceController;
