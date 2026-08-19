/**
 * CardioNav AI - High Precision 60 FPS PPG & ECG Waveform Engine
 * Photoplethysmogram Synthesizer & Real-Time Hardware Buffer Renderer
 */

export class PPGCanvasEngine {
  constructor(canvasElement, options = {}) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.onBeat = options.onBeat || null;
    this.onMetricsUpdate = options.onMetricsUpdate || null;

    // Dimensions
    this.width = canvasElement.width || 800;
    this.height = canvasElement.height || 260;

    // Simulation state
    this.isRunning = false;
    this.profile = {
      type: 'arrhythmia',
      baseBpm: 108,
      bpmVariance: 18,
      hrv: 21.4,
      rhythmIrregularity: 0.76,
      signalQuality: 0.93,
      spo2: 96,
      abnormalBeatsRatio: 0.38
    };

    // Live mode vs Simulation
    this.isLiveStream = false;
    this.liveBuffer = [];

    // Waveform rendering variables
    this.points = [];
    this.maxPoints = 400; // Visible history on screen
    this.scanX = 0;
    this.lastTimestamp = 0;

    // Heartbeat cycle generators
    this.phase = 0; // 0 to 1 for beat progression
    this.currentBpm = 72;
    this.currentHrv = 45;
    this.currentIrregularity = 0.1;
    this.currentSpo2 = 98;
    this.currentSqi = 96;

    // Beat timing state
    this.timeToNextBeat = 0;
    this.beatIntervalMs = 800;
    this.isAbnormalBeat = false;
    this.lastBeatTime = performance.now();

    // Audio synthesizer
    this.audioCtx = null;
    this.audioEnabled = false;

    // Initialize display buffer
    this.initBuffer();
    this.bindEvents();
  }

  bindEvents() {
    window.addEventListener('resize', () => this.resize());
    setTimeout(() => this.resize(), 100);
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    if (rect.width > 0 && rect.height > 0) {
      this.canvas.width = rect.width * dpr;
      this.canvas.height = rect.height * dpr;
      this.ctx.scale(dpr, dpr);
      this.width = rect.width;
      this.height = rect.height;
      this.maxPoints = Math.floor(this.width / 2);
    }
  }

  initBuffer() {
    this.points = [];
    const baseline = this.height * 0.55;
    for (let i = 0; i < this.maxPoints; i++) {
      this.points.push({
        y: baseline,
        isPeak: false,
        sqi: 95
      });
    }
  }

  setProfile(newProfile) {
    this.profile = { ...this.profile, ...newProfile };
    this.currentBpm = this.profile.baseBpm || 75;
    this.currentHrv = this.profile.hrv || 35;
    this.currentIrregularity = this.profile.rhythmIrregularity || 0.1;
    this.currentSpo2 = this.profile.spo2 || 98;
    this.currentSqi = Math.round((this.profile.signalQuality || 0.95) * 100);
    this.beatIntervalMs = (60 / this.currentBpm) * 1000;
  }

  enableLiveStream(enabled = true) {
    this.isLiveStream = enabled;
    if (enabled) {
      this.liveBuffer = [];
    }
  }

  pushLiveValues(bpm, spo2, rawSignalArray = []) {
    if (bpm) this.currentBpm = bpm;
    if (spo2) this.currentSpo2 = spo2;
    if (Array.isArray(rawSignalArray) && rawSignalArray.length > 0) {
      for (const val of rawSignalArray) {
        this.liveBuffer.push(val);
      }
      if (this.liveBuffer.length > 1000) {
        this.liveBuffer = this.liveBuffer.slice(-500);
      }
    }
  }

  toggleAudio(force) {
    this.audioEnabled = force !== undefined ? force : !this.audioEnabled;
    if (this.audioEnabled && !this.audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.audioCtx = new AudioContextClass();
      }
    }
    return this.audioEnabled;
  }

  playBeep(frequency = 880, duration = 0.06) {
    if (!this.audioEnabled || !this.audioCtx) return;
    try {
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(frequency, this.audioCtx.currentTime);
      gain.gain.setValueAtTime(0.04, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {
      // Audio autoplay policy catch
    }
  }

  /**
   * Generates a realistic photoplethysmogram (PPG) sample
   * Phase is [0, 1) through the cardiac cycle
   */
  synthesizePPGSample(phase, isAbnormal) {
    let y = 0;
    // Respiration baseline wander (0.2 Hz slow oscillation)
    const respiration = Math.sin(performance.now() * 0.0012) * 6;

    if (isAbnormal) {
      // Arrhythmia: chaotic diastolic decay, blurred dicrotic notch, irregular rise
      if (phase < 0.18) {
        // Fast steep upstroke (systolic)
        const t = phase / 0.18;
        y = Math.sin(t * Math.PI * 0.5) * 75;
      } else if (phase < 0.35) {
        // Partial drop
        const t = (phase - 0.18) / 0.17;
        y = 75 - t * 45;
      } else if (phase < 0.55) {
        // Distorted secondary wave
        const t = (phase - 0.35) / 0.20;
        y = 30 + Math.sin(t * Math.PI) * 18;
      } else {
        // Irregular baseline return with tremor
        const t = (phase - 0.55) / 0.45;
        y = 30 * (1 - t) + (Math.random() - 0.5) * 3;
      }
    } else {
      // Normal healthy PPG: Crisp systolic peak + defined dicrotic notch + diastolic wave
      if (phase < 0.15) {
        // Anacrotic phase (rapid systolic upstroke)
        const t = phase / 0.15;
        y = Math.sin(t * Math.PI * 0.5) * 78;
      } else if (phase < 0.30) {
        // Systolic decline to dicrotic notch
        const t = (phase - 0.15) / 0.15;
        y = 78 - Math.sin(t * Math.PI * 0.5) * 38; // Drops to ~40
      } else if (phase < 0.48) {
        // Dicrotic peak (diastolic rebound from aortic valve closure)
        const t = (phase - 0.30) / 0.18;
        y = 40 + Math.sin(t * Math.PI) * 16; // Peaks at ~56
      } else {
        // Diastolic runoff (catacrotic runoff back to baseline)
        const t = (phase - 0.48) / 0.52;
        y = 40 * Math.exp(-t * 3.5);
      }
    }

    // Baseline centering
    const baseline = this.height * 0.60;
    return baseline - y + respiration;
  }

  start() {
    if (this.isRunning) return;
    this.isRunning = true;
    this.lastTimestamp = performance.now();
    this.lastBeatTime = performance.now();
    this.renderLoop();
  }

  stop() {
    this.isRunning = false;
  }

  renderLoop() {
    if (!this.isRunning) return;

    const now = performance.now();
    const dt = Math.min((now - this.lastTimestamp), 100); // delta time capped
    this.lastTimestamp = now;

    this.updatePhysics(dt, now);
    this.draw();

    requestAnimationFrame(() => this.renderLoop());
  }

  updatePhysics(dt, now) {
    if (this.isLiveStream && this.liveBuffer.length > 0) {
      // Ingest live values from ESP32 buffer
      const samplesToPull = Math.max(1, Math.floor(this.liveBuffer.length / 10));
      for (let i = 0; i < samplesToPull; i++) {
        const rawVal = this.liveBuffer.shift();
        if (rawVal !== undefined) {
          // Normalize to screen
          const normalizedY = this.height * 0.55 - (rawVal - 50) * 1.5;
          this.points.push({ y: normalizedY, isPeak: false, sqi: this.currentSqi });
        }
      }
    } else {
      // Synthetic cardiac cycle simulation
      const elapsedSinceBeat = now - this.lastBeatTime;
      const progress = elapsedSinceBeat / this.beatIntervalMs;

      let isPeakFrame = false;

      if (progress >= 1.0) {
        // A cardiac cycle completed! Trigger new beat
        this.lastBeatTime = now;
        this.phase = 0;

        // Calculate next beat interval with realistic physiological jitter
        const isArrhythmia = this.profile.type === 'arrhythmia';
        const randomJitter = (Math.random() - 0.5) * (this.profile.bpmVariance || 4);
        
        let targetBpm = this.profile.baseBpm + randomJitter;
        if (isArrhythmia && Math.random() < this.profile.abnormalBeatsRatio) {
          this.isAbnormalBeat = true;
          // Premature or delayed beat
          targetBpm += (Math.random() > 0.5 ? 28 : -22);
        } else {
          this.isAbnormalBeat = false;
        }

        this.currentBpm = Math.round(Math.max(40, Math.min(180, targetBpm)));
        this.beatIntervalMs = (60 / this.currentBpm) * 1000;

        // Slight metric wander
        this.currentHrv = +(this.profile.hrv + (Math.random() - 0.5) * 2.5).toFixed(1);
        this.currentIrregularity = +(this.profile.rhythmIrregularity + (Math.random() - 0.5) * 0.04).toFixed(2);
        this.currentIrregularity = Math.max(0.02, Math.min(0.98, this.currentIrregularity));

        // Beat events
        isPeakFrame = true;
        this.playBeep(this.isAbnormalBeat ? 720 : 880);
        if (this.onBeat) {
          this.onBeat({
            bpm: this.currentBpm,
            hrv: this.currentHrv,
            isAbnormal: this.isAbnormalBeat
          });
        }
        if (this.onMetricsUpdate) {
          this.onMetricsUpdate({
            bpm: this.currentBpm,
            hrv: this.currentHrv,
            irregularity: this.currentIrregularity,
            sqi: this.currentSqi,
            spo2: this.currentSpo2
          });
        }
      } else {
        this.phase = progress;
      }

      // Generate continuous sample point
      const yVal = this.synthesizePPGSample(this.phase, this.isAbnormalBeat);
      this.points.push({
        y: yVal,
        isPeak: isPeakFrame,
        sqi: this.currentSqi
      });
    }

    // Keep buffer sized
    while (this.points.length > this.maxPoints) {
      this.points.shift();
    }
  }

  draw() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    // 1. Clear background
    ctx.fillStyle = '#0a0f1d';
    ctx.fillRect(0, 0, w, h);

    // 2. Draw Clinical Medical ECG Grid Lines
    this.drawGrid(ctx, w, h);

    // 3. Draw Waveform Trace
    if (this.points.length > 2) {
      ctx.save();
      const stepX = w / (this.maxPoints - 1);

      // Primary glowing path
      ctx.beginPath();
      ctx.lineWidth = 2.4;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';

      // Neon Emerald / Cyan Gradient
      const grad = ctx.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, 'rgba(16, 185, 129, 0.2)');
      grad.addColorStop(0.7, 'rgba(16, 185, 129, 0.85)');
      grad.addColorStop(1, '#10b981');

      if (this.profile.type === 'arrhythmia') {
        grad.addColorStop(0, 'rgba(239, 68, 68, 0.2)');
        grad.addColorStop(0.7, 'rgba(239, 68, 68, 0.85)');
        grad.addColorStop(1, '#ef4444');
      }

      ctx.strokeStyle = grad;
      ctx.shadowColor = this.profile.type === 'arrhythmia' ? '#ef4444' : '#10b981';
      ctx.shadowBlur = 8;

      for (let i = 0; i < this.points.length; i++) {
        const pt = this.points[i];
        const x = i * stepX;
        if (i === 0) {
          ctx.moveTo(x, pt.y);
        } else {
          ctx.lineTo(x, pt.y);
        }
      }
      ctx.stroke();

      // Lead cursor / Phosphor scan head glow
      const headIdx = this.points.length - 1;
      const headX = headIdx * stepX;
      const headY = this.points[headIdx].y;

      ctx.shadowBlur = 14;
      ctx.shadowColor = '#ffffff';
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(headX, headY, 3.5, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    // 4. On-screen telemetry watermark
    this.drawWatermark(ctx, w, h);
  }

  drawGrid(ctx, w, h) {
    const majorSize = 40;
    const minorSize = 8;

    ctx.save();
    // Minor grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let x = 0; x < w; x += minorSize) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
    }
    for (let y = 0; y < h; y += minorSize) {
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
    }
    ctx.stroke();

    // Major grid
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.08)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x < w; x += majorSize) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
    }
    for (let y = 0; y < h; y += majorSize) {
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
    }
    ctx.stroke();
    ctx.restore();
  }

  drawWatermark(ctx, w, h) {
    ctx.save();
    ctx.font = '10px "JetBrains Mono", monospace';

    // Top-Left: Lead Title
    ctx.textAlign = 'left';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
    ctx.fillText('LEAD I • PPG (940nm)', 12, 18);

    // Top-Right: Stream Status (Properly right-aligned with safety margin)
    ctx.textAlign = 'right';
    const isNarrow = w < 420;
    const statusText = this.isLiveStream 
      ? (isNarrow ? '● LIVE (ESP32)' : '● LIVE STREAM (ESP32)') 
      : (isNarrow ? '● SIMULATOR' : '● SYNTHETIC ENGINE');
    const statusColor = this.isLiveStream ? '#38bdf8' : '#34d399';
    ctx.fillStyle = statusColor;
    ctx.fillText(statusText, w - 12, 18);

    // Bottom-Left: Filter Telemetry (Placed at the bottom so it never overlaps top headers)
    if (w > 320) {
      ctx.textAlign = 'left';
      ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.fillText('100 Hz | BANDPASS 0.5-5.0 Hz', 12, h - 10);
    }

    ctx.restore();
  }
}
