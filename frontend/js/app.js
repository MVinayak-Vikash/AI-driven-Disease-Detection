/**
 * CardioNav AI - Clean Responsive Application Controller
 * Handles real-time telemetry, 3 disease predictions, history storage, and mobile drawer navigation
 */

import { SYMPTOMS_LIST, MEDICAL_HISTORY_LIST, DEMO_SCENARIOS } from './patient-data.js';
import { PPGCanvasEngine } from './ppg-canvas.js';
import { AIClinicalReasoner } from './ai-reasoner.js';
import { APIClient } from './api-client.js';

class CardioNavApp {
  constructor() {
    this.selectedSymptoms = new Set(['chest_pain', 'palpitations', 'dyspnea', 'cold_sweat']);
    this.selectedHistory = new Set(['hypertension', 'prior_cardiac_event', 'smoking']);
    this.currentAssessment = null;
    this.currentScenarioId = 'cardiac_alert';
    this.reasoner = new AIClinicalReasoner();

    this.apiClient = new APIClient({
      httpBaseUrl: 'http://localhost:8000',
      onConnectionStatusChanged: (status) => this.handleBackendStatus(status)
    });

    this.initDOM();
    this.initTheme();
    this.initCanvasEngine();
    this.renderTaxonomy();
    this.bindEvents();
    this.updateHistoryBadge();

    // Run initial scenario
    this.loadScenario('cardiac_alert');

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  handleBackendStatus(status) {
    const dot = document.getElementById('backendStatusDot');
    const text = document.getElementById('backendStatusText');
    const badge = document.getElementById('backendStatusBadge');
    if (!badge || !dot || !text) return;

    if (status.backendOnline) {
      badge.style.background = 'rgba(16, 185, 129, 0.12)';
      badge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      badge.style.color = 'var(--accent-emerald)';
      dot.style.background = 'var(--accent-emerald)';
      text.textContent = '🟢 Backend: Online (FastAPI)';
    } else {
      badge.style.background = 'rgba(245, 158, 11, 0.12)';
      badge.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      badge.style.color = 'var(--accent-amber)';
      dot.style.background = 'var(--accent-amber)';
      text.textContent = '⚡ Client Engine (Local)';
    }
  }

  initDOM() {
    // Sidebar & Mobile Drawer DOM
    this.appSidebar = document.getElementById('appSidebar');
    this.sidebarBackdrop = document.getElementById('sidebarBackdrop');
    this.btnMobileMenu = document.getElementById('btnMobileMenu');
    this.btnCloseSidebar = document.getElementById('btnCloseSidebar');

    // Waveform & Telemetry
    this.canvas = document.getElementById('ppgCanvas');
    this.heartBeater = document.getElementById('heartBeater');
    this.metricBpm = document.getElementById('metricBpm');
    this.metricHrv = document.getElementById('metricHrv');
    this.metricIrregularity = document.getElementById('metricIrregularity');
    this.metricSpo2 = document.getElementById('metricSpo2');

    // Intake form inputs
    this.intakeForm = document.getElementById('intakeForm');
    this.inputName = document.getElementById('inputName');
    this.inputAge = document.getElementById('inputAge');
    this.inputSex = document.getElementById('inputSex');
    this.inputSys = document.getElementById('inputSys');
    this.inputDia = document.getElementById('inputDia');
    this.inputGlucose = document.getElementById('inputGlucose');
    this.inputHemoglobin = document.getElementById('inputHemoglobin');
    this.symptomsList = document.getElementById('symptomsList');
    this.historyList = document.getElementById('historyList');

    // Disease Prediction Elements
    this.diabetesCard = document.getElementById('diabetesCard');
    this.diabetesPill = document.getElementById('diabetesPill');
    this.diabetesBar = document.getElementById('diabetesBar');
    this.diabetesScore = document.getElementById('diabetesScore');
    this.diabetesEvidence = document.getElementById('diabetesEvidence');
    this.diabetesRec = document.getElementById('diabetesRec');

    this.cardiacCard = document.getElementById('cardiacCard');
    this.cardiacPill = document.getElementById('cardiacPill');
    this.cardiacBar = document.getElementById('cardiacBar');
    this.cardiacScore = document.getElementById('cardiacScore');
    this.cardiacEvidence = document.getElementById('cardiacEvidence');
    this.cardiacRec = document.getElementById('cardiacRec');

    this.anemiaCard = document.getElementById('anemiaCard');
    this.anemiaPill = document.getElementById('anemiaPill');
    this.anemiaBar = document.getElementById('anemiaBar');
    this.anemiaScore = document.getElementById('anemiaScore');
    this.anemiaEvidence = document.getElementById('anemiaEvidence');
    this.anemiaRec = document.getElementById('anemiaRec');

    this.referralTitle = document.getElementById('referralTitle');
    this.referralSubtitle = document.getElementById('referralSubtitle');

    // Theme & Badges
    this.btnThemeToggle = document.getElementById('btnThemeToggle');
    this.themeIcon = document.getElementById('themeIcon');
    this.themeText = document.getElementById('themeText');
    this.historyBadge = document.getElementById('historyBadge');
    this.historyTableBody = document.getElementById('historyTableBody');
  }

  initTheme() {
    const savedTheme = localStorage.getItem('cardionav_theme') || 'light';
    if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
      this.updateThemeButton(true);
    } else {
      document.body.classList.remove('dark-theme');
      this.updateThemeButton(false);
    }
  }

  toggleTheme() {
    const isDark = document.body.classList.toggle('dark-theme');
    localStorage.setItem('cardionav_theme', isDark ? 'dark' : 'light');
    this.updateThemeButton(isDark);
  }

  setTheme(theme) {
    if (theme === 'dark') {
      document.body.classList.add('dark-theme');
      localStorage.setItem('cardionav_theme', 'dark');
      this.updateThemeButton(true);
    } else {
      document.body.classList.remove('dark-theme');
      localStorage.setItem('cardionav_theme', 'light');
      this.updateThemeButton(false);
    }
  }

  updateThemeButton(isDark) {
    if (this.themeIcon) {
      this.themeIcon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
    }
    if (this.themeText) {
      this.themeText.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    }
    if (window.lucide) window.lucide.createIcons();
  }

  initCanvasEngine() {
    this.ppgEngine = new PPGCanvasEngine(this.canvas, {
      onBeat: () => {
        if (this.heartBeater) {
          this.heartBeater.classList.add('beating');
          setTimeout(() => this.heartBeater.classList.remove('beating'), 250);
        }
      },
      onMetricsUpdate: (metrics) => {
        if (this.metricBpm) this.metricBpm.textContent = metrics.bpm;
        if (this.metricHrv) this.metricHrv.textContent = metrics.hrv;
        if (this.metricIrregularity) this.metricIrregularity.textContent = metrics.irregularity;
        if (this.metricSpo2) this.metricSpo2.textContent = metrics.spo2;
      }
    });

    this.ppgEngine.start();
  }

  renderTaxonomy() {
    // 1. Symptoms Chips
    this.symptomsList.innerHTML = '';
    SYMPTOMS_LIST.forEach((s) => {
      const chip = document.createElement('div');
      chip.className = `tag-chip ${this.selectedSymptoms.has(s.id) ? 'selected' : ''}`;
      chip.textContent = s.label;
      chip.addEventListener('click', () => {
        if (this.selectedSymptoms.has(s.id)) {
          this.selectedSymptoms.delete(s.id);
          chip.classList.remove('selected');
        } else {
          this.selectedSymptoms.add(s.id);
          chip.classList.add('selected');
        }
      });
      this.symptomsList.appendChild(chip);
    });

    // 2. Medical History Chips
    this.historyList.innerHTML = '';
    MEDICAL_HISTORY_LIST.forEach((h) => {
      const chip = document.createElement('div');
      chip.className = `tag-chip ${this.selectedHistory.has(h.id) ? 'selected' : ''}`;
      chip.textContent = h.label;
      chip.addEventListener('click', () => {
        if (this.selectedHistory.has(h.id)) {
          this.selectedHistory.delete(h.id);
          chip.classList.remove('selected');
        } else {
          this.selectedHistory.add(h.id);
          chip.classList.add('selected');
        }
      });
      this.historyList.appendChild(chip);
    });
  }

  loadScenario(scenarioId) {
    const sc = DEMO_SCENARIOS[scenarioId];
    if (!sc) return;
    this.currentScenarioId = scenarioId;

    // Update active chip
    document.querySelectorAll('.demo-chip').forEach((chip) => {
      chip.classList.toggle('active', chip.dataset.scenario === scenarioId);
    });

    // Populate inputs
    this.inputName.value = sc.patient.fullName;
    this.inputAge.value = sc.patient.age;
    this.inputSex.value = sc.patient.sex;
    this.inputSys.value = sc.patient.systolicBp;
    this.inputDia.value = sc.patient.diastolicBp;
    this.inputGlucose.value = sc.patient.glucose;
    this.inputHemoglobin.value = sc.patient.hemoglobin;

    this.selectedSymptoms = new Set(sc.patient.symptoms);
    this.selectedHistory = new Set(sc.patient.history);
    this.renderTaxonomy();

    // Set PPG Profile
    this.ppgEngine.setProfile(sc.sensorProfile);

    // Run prediction
    setTimeout(() => this.runPrediction(false), 50);
  }

  async runPrediction(saveToHistory = true) {
    const patientData = {
      fullName: this.inputName.value || 'Anonymous Patient',
      age: Number(this.inputAge.value) || 40,
      sex: this.inputSex.value,
      systolicBp: Number(this.inputSys.value) || 120,
      diastolicBp: Number(this.inputDia.value) || 80,
      glucose: Number(this.inputGlucose.value) || 95,
      hemoglobin: Number(this.inputHemoglobin.value) || 13.5,
      bmi: 24.0,
      symptoms: Array.from(this.selectedSymptoms),
      history: Array.from(this.selectedHistory)
    };

    const sensorFeatures = {
      heartRate: this.ppgEngine.currentBpm,
      hrv: this.ppgEngine.currentHrv,
      rhythmIrregularity: this.ppgEngine.currentIrregularity,
      spo2: this.ppgEngine.currentSpo2
    };

    const assessmentOutcome = await this.apiClient.runAssessment(patientData, sensorFeatures);
    const result = assessmentOutcome.data;
    this.currentAssessment = result;
    this.renderPredictionResults(result);

    if (saveToHistory) {
      this.saveRecordToHistory(result);
    }
  }

  renderPredictionResults(result) {
    const { diabetes, cardiac, anemia } = result.predictions;

    // 1. DIABETES CARD
    this.diabetesCard.className = `disease-card risk-${diabetes.level}`;
    this.diabetesPill.className = `risk-pill ${diabetes.level}`;
    this.diabetesPill.textContent = `${diabetes.level} RISK`;
    this.diabetesScore.textContent = `${diabetes.score}%`;
    this.diabetesBar.style.width = `${diabetes.score}%`;
    this.diabetesBar.style.background = diabetes.level === 'HIGH' ? 'var(--accent-red)' : diabetes.level === 'MODERATE' ? 'var(--accent-amber)' : 'var(--accent-emerald)';
    this.diabetesEvidence.innerHTML = diabetes.evidence.map((e) => `<li>${e}</li>`).join('');
    this.diabetesRec.innerHTML = `<strong>Clinical Recommendation:</strong> ${diabetes.recommendation}`;

    // 2. CARDIAC CARD
    this.cardiacCard.className = `disease-card risk-${cardiac.level}`;
    this.cardiacPill.className = `risk-pill ${cardiac.level}`;
    this.cardiacPill.textContent = cardiac.isImminentArrestWarning ? 'CRITICAL / ARREST ALERT' : `${cardiac.level} RISK`;
    this.cardiacScore.textContent = `${cardiac.score}%`;
    this.cardiacBar.style.width = `${cardiac.score}%`;
    this.cardiacBar.style.background = cardiac.level === 'HIGH' ? 'var(--accent-red)' : cardiac.level === 'MODERATE' ? 'var(--accent-amber)' : 'var(--accent-emerald)';
    this.cardiacEvidence.innerHTML = cardiac.evidence.map((e) => `<li>${e}</li>`).join('');
    this.cardiacRec.innerHTML = `<strong>Clinical Recommendation:</strong> ${cardiac.recommendation}`;

    // 3. ANEMIA CARD
    this.anemiaCard.className = `disease-card risk-${anemia.level}`;
    this.anemiaPill.className = `risk-pill ${anemia.level}`;
    this.anemiaPill.textContent = `${anemia.level} RISK`;
    this.anemiaScore.textContent = `${anemia.score}%`;
    this.anemiaBar.style.width = `${anemia.score}%`;
    this.anemiaBar.style.background = anemia.level === 'HIGH' ? 'var(--accent-red)' : anemia.level === 'MODERATE' ? 'var(--accent-amber)' : 'var(--accent-emerald)';
    this.anemiaEvidence.innerHTML = anemia.evidence.map((e) => `<li>${e}</li>`).join('');
    this.anemiaRec.innerHTML = `<strong>Clinical Recommendation:</strong> ${anemia.recommendation}`;

    // 4. HOSPITAL REFERRAL BANNER
    if (cardiac.score >= 65 || result.is_emergency) {
      this.referralTitle.textContent = '🚨 Emergency Hospital Referral Required';
      this.referralSubtitle.textContent = 'High cardiac risk or arrhythmia pattern detected. Direct patient to Department of Cardiology immediately.';
    } else if (diabetes.score >= 65) {
      this.referralTitle.textContent = '⚠️ Priority Specialist Referral: Endocrinology';
      this.referralSubtitle.textContent = 'Marked glycemic deviation. Refer patient for formal fasting glucose & HbA1c diagnostic panel.';
    } else if (anemia.score >= 65) {
      this.referralTitle.textContent = '🩸 Clinical Referral: Hematology & Internal Medicine';
      this.referralSubtitle.textContent = 'Significant hemoglobin depletion. Order Complete Blood Count (CBC) and iron profile.';
    } else {
      this.referralTitle.textContent = '✅ Stable Clinical Profile';
      this.referralSubtitle.textContent = 'All 3 disease risk indicators within normative baseline. Routine periodic wellness check advised.';
    }

    if (window.lucide) window.lucide.createIcons();
  }

  saveRecordToHistory(result) {
    const history = JSON.parse(localStorage.getItem('cardionav_history') || '[]');
    const newEntry = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      date: new Date().toLocaleDateString(),
      name: result.patient.name,
      ageSex: `${result.patient.age} / ${result.patient.sex.toUpperCase()}`,
      diabetesScore: `${result.predictions.diabetes.score}% (${result.predictions.diabetes.level})`,
      cardiacScore: `${result.predictions.cardiac.score}% (${result.predictions.cardiac.level})`,
      anemiaScore: `${result.predictions.anemia.score}% (${result.predictions.anemia.level})`,
      action: result.urgency_badge
    };

    history.unshift(newEntry);
    if (history.length > 25) history.pop();
    localStorage.setItem('cardionav_history', JSON.stringify(history));
    this.updateHistoryBadge();
  }

  updateHistoryBadge() {
    const history = JSON.parse(localStorage.getItem('cardionav_history') || '[]');
    if (this.historyBadge) {
      this.historyBadge.textContent = history.length;
    }
  }

  renderHistoryTable() {
    const history = JSON.parse(localStorage.getItem('cardionav_history') || '[]');
    if (!this.historyTableBody) return;

    if (history.length === 0) {
      this.historyTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No previous screening records found. Click "Analyze" on any patient to record.</td></tr>`;
      return;
    }

    this.historyTableBody.innerHTML = history
      .map(
        (h) => `
        <tr>
          <td><span style="font-family: var(--font-mono); font-size: 0.75rem;">${h.date} ${h.timestamp}</span></td>
          <td><strong>${h.name}</strong></td>
          <td>${h.ageSex}</td>
          <td><span style="font-weight: 700;">${h.diabetesScore}</span></td>
          <td><span style="font-weight: 700; color: ${h.cardiacScore.includes('HIGH') ? 'var(--accent-red)' : 'inherit'};">${h.cardiacScore}</span></td>
          <td><span style="font-weight: 700;">${h.anemiaScore}</span></td>
          <td><span style="font-size: 0.75rem; color: var(--accent-cyan); font-weight: 600;">${h.action}</span></td>
        </tr>
      `
      )
      .join('');
  }

  // Mobile Drawer Controls
  openMobileSidebar() {
    if (this.appSidebar) this.appSidebar.classList.add('open');
    if (this.sidebarBackdrop) this.sidebarBackdrop.classList.add('active');
  }

  closeMobileSidebar() {
    if (this.appSidebar) this.appSidebar.classList.remove('open');
    if (this.sidebarBackdrop) this.sidebarBackdrop.classList.remove('active');
  }

  bindEvents() {
    // Mobile Hamburger Menu Click
    if (this.btnMobileMenu) {
      this.btnMobileMenu.addEventListener('click', () => this.openMobileSidebar());
    }

    // Mobile Close Button Click
    if (this.btnCloseSidebar) {
      this.btnCloseSidebar.addEventListener('click', () => this.closeMobileSidebar());
    }

    // Backdrop Click
    if (this.sidebarBackdrop) {
      this.sidebarBackdrop.addEventListener('click', () => this.closeMobileSidebar());
    }

    // Theme Toggle on top bar
    this.btnThemeToggle.addEventListener('click', () => this.toggleTheme());

    // Preset buttons
    document.querySelectorAll('.demo-chip').forEach((chip) => {
      chip.addEventListener('click', (e) => {
        const sc = e.target.dataset.scenario;
        if (sc) this.loadScenario(sc);
      });
    });

    // Form submit
    this.intakeForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.runPrediction(true);
    });

    // Clear form
    const btnReset = document.getElementById('btnResetForm');
    if (btnReset) {
      btnReset.addEventListener('click', () => {
        this.inputName.value = '';
        this.inputAge.value = '30';
        this.inputSys.value = '120';
        this.inputDia.value = '80';
        this.inputGlucose.value = '90';
        this.inputHemoglobin.value = '13.0';
        this.selectedSymptoms.clear();
        this.selectedHistory.clear();
        this.renderTaxonomy();
      });
    }

    // Audio toggle
    const btnAudio = document.getElementById('btnToggleAudio');
    if (btnAudio) {
      btnAudio.addEventListener('click', () => {
        const isEnabled = this.ppgEngine.toggleAudio();
        const icon = document.getElementById('audioIcon');
        if (icon) {
          icon.setAttribute('data-lucide', isEnabled ? 'volume-2' : 'volume-x');
          if (window.lucide) window.lucide.createIcons();
        }
      });
    }

    // Stream Pause/Resume
    const btnStream = document.getElementById('btnToggleStream');
    if (btnStream) {
      btnStream.addEventListener('click', () => {
        if (this.ppgEngine.isRunning) {
          this.ppgEngine.stop();
          document.getElementById('streamText').textContent = 'Resume';
          document.getElementById('streamIcon').setAttribute('data-lucide', 'play');
        } else {
          this.ppgEngine.start();
          document.getElementById('streamText').textContent = 'Pause';
          document.getElementById('streamIcon').setAttribute('data-lucide', 'pause');
        }
        if (window.lucide) window.lucide.createIcons();
      });
    }

    // Print summary report
    const btnPrint = document.getElementById('btnExportSummary');
    if (btnPrint) {
      btnPrint.addEventListener('click', () => window.print());
    }

    // SIDEBAR NAVIGATION & MODALS
    document.querySelectorAll('.nav-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        const targetView = item.dataset.view;
        document.querySelectorAll('.nav-item').forEach((n) => n.classList.remove('active'));
        item.classList.add('active');

        // Close mobile drawer on item tap
        this.closeMobileSidebar();

        if (targetView === 'history') {
          this.renderHistoryTable();
          this.openModal('historyModal');
        } else if (targetView === 'hospital') {
          this.openModal('hospitalModal');
        } else if (targetView === 'settings') {
          this.openModal('settingsModal');
        } else if (targetView === 'about') {
          this.openModal('aboutModal');
        } else if (targetView === 'contact') {
          this.openModal('contactModal');
        }
      });
    });

    // Quick hospital dispatch button
    const btnOpenHosp = document.getElementById('btnOpenHospitalModal');
    if (btnOpenHosp) {
      btnOpenHosp.addEventListener('click', () => this.openModal('hospitalModal'));
    }

    // Modal close buttons
    document.querySelectorAll('[data-close]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const modalId = btn.dataset.close;
        this.closeModal(modalId);
      });
    });

    // Close on backdrop click
    document.querySelectorAll('.modal-overlay').forEach((modal) => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('open');
        }
      });
    });

    // Hospital Form Submission
    const hospForm = document.getElementById('hospitalIntegrationForm');
    if (hospForm) {
      hospForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const hospName = document.getElementById('hospName').value;
        const ward = document.getElementById('hospWard').value;
        alert(`✅ Patient referral successfully dispatched to ${hospName} (${ward.toUpperCase()})!\nEmergency notification sent to Doctor ID: ${document.getElementById('hospDocId').value}`);
        this.closeModal('hospitalModal');
      });
    }

    // Settings Theme Buttons
    const btnSetLight = document.getElementById('btnSetLight');
    const btnSetDark = document.getElementById('btnSetDark');
    if (btnSetLight) btnSetLight.addEventListener('click', () => this.setTheme('light'));
    if (btnSetDark) btnSetDark.addEventListener('click', () => this.setTheme('dark'));

    // Contact Form Submission
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
      contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const sender = document.getElementById('contactName').value;
        alert(`✅ Thank you, ${sender}! Your message has been dispatched to Team Really Unique. We will get back to your email shortly.`);
        contactForm.reset();
        this.closeModal('contactModal');
      });
    }

    // Clear History Button
    const btnClearHist = document.getElementById('btnClearHistory');
    if (btnClearHist) {
      btnClearHist.addEventListener('click', () => {
        if (confirm('Clear all stored patient records from browser?')) {
          localStorage.removeItem('cardionav_history');
          this.renderHistoryTable();
          this.updateHistoryBadge();
        }
      });
    }
  }

  openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('open');
  }

  closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('open');
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  window.app = new CardioNavApp();
});
