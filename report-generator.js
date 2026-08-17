/**
 * CardioNav AI - Clinical Decision Support Report Generator
 * Generates printable & exportable clinical referral briefs with QR verification
 */

export class ReportGenerator {
  static generateReportHtml(assessmentData, ppgSnapshotDataUrl = null) {
    const {
      patient = {},
      sensor_features = {},
      risk_level = 'LOW',
      risk_score_numeric = 15,
      conditions_of_concern = [],
      evidence = [],
      confidence = 0.85,
      specialist = 'cardiology',
      urgency_tier = 'Routine',
      clinical_summary = '',
      timestamp = new Date().toISOString()
    } = assessmentData;

    const formattedDate = new Date(timestamp).toLocaleString('en-US', {
      dateStyle: 'full',
      timeStyle: 'medium'
    });

    const reportId = `CRN-${Math.random().toString(36).substring(2, 8).toUpperCase()}-${Date.now().toString().slice(-4)}`;

    const riskColor = risk_level === 'HIGH' ? '#ef4444' : risk_level === 'MODERATE' ? '#f59e0b' : '#10b981';
    const riskBg = risk_level === 'HIGH' ? '#fef2f2' : risk_level === 'MODERATE' ? '#fffbeb' : '#f0fdf4';

    return `
      <div class="clinical-report-sheet" id="printReportArea">
        <div class="report-header">
          <div class="header-left">
            <div class="logo-mark">
              <span class="cross">+</span>
              <span class="brand-title">CardioNav AI</span>
            </div>
            <div class="report-subtitle">Clinical Decision Support & Early-Risk Screening Referral Brief</div>
            <div class="report-meta-line">VITSIH-26 Multi-Modal Diagnostic Decision-Support Framework</div>
          </div>
          <div class="header-right text-right">
            <div class="badge-report-id">REPORT ID: <strong>${reportId}</strong></div>
            <div class="report-timestamp">${formattedDate}</div>
            <div class="screening-mode">Sensor Device: ESP32_PPG (940nm)</div>
          </div>
        </div>

        <hr class="report-divider"/>

        <div class="report-grid-2col">
          <div class="report-card">
            <h4 class="card-title">1. Patient Demographic & Baseline Profile</h4>
            <div class="data-table">
              <div class="data-row"><span>Patient Name:</span> <strong>${patient.name || 'Anonymous Patient'}</strong></div>
              <div class="data-row"><span>Age / Biological Sex:</span> <strong>${patient.age} Yrs / ${patient.sex?.toUpperCase()}</strong></div>
              <div class="data-row"><span>Baseline Blood Pressure:</span> <strong>${patient.bp || '120/80'} mmHg</strong></div>
              <div class="data-row"><span>Screening Channel:</span> <strong>Edge ESP32 PPG + Clinical AI Reasoner</strong></div>
            </div>
          </div>

          <div class="report-card">
            <h4 class="card-title">2. Edge Physiological Signal Telemetry</h4>
            <div class="data-table">
              <div class="data-row"><span>Heart Rate (BPM):</span> <strong>${sensor_features.heart_rate} BPM</strong></div>
              <div class="data-row"><span>Heart Rate Variability (HRV RMSSD):</span> <strong>${sensor_features.hrv} ms</strong></div>
              <div class="data-row"><span>Rhythm Irregularity Index:</span> <strong>${(sensor_features.rhythm_irregularity * 100).toFixed(0)}%</strong></div>
              <div class="data-row"><span>Peripheral SpO2 / SQI:</span> <strong>${sensor_features.spo2}% / ${(sensor_features.signal_quality * 100).toFixed(0)}% SQI</strong></div>
            </div>
          </div>
        </div>

        ${ppgSnapshotDataUrl ? `
          <div class="report-card ppg-snapshot-card">
            <h4 class="card-title">3. Real-Time PPG Waveform Morphological Strip</h4>
            <img src="${ppgSnapshotDataUrl}" alt="PPG Waveform Strip" class="ppg-strip-img" />
          </div>
        ` : ''}

        <div class="report-card risk-summary-card" style="background-color: ${riskBg}; border-left: 6px solid ${riskColor};">
          <div class="risk-flex-header">
            <div>
              <span class="risk-caption">TRIAGE RISK CATEGORY</span>
              <h2 class="risk-level-title" style="color: ${riskColor};">${risk_level} RISK (Score: ${risk_score_numeric}/100)</h2>
            </div>
            <div class="risk-confidence">
              <div class="confidence-val">AI Confidence: <strong>${(confidence * 100).toFixed(0)}%</strong></div>
              <div class="urgency-tag" style="background-color: ${riskColor}; color: #fff;">${urgency_tier}</div>
            </div>
          </div>
        </div>

        <div class="report-card">
          <h4 class="card-title">4. Differential Conditions of Concern</h4>
          <table class="conditions-table">
            <thead>
              <tr>
                <th>Suspected Clinical Pattern</th>
                <th>ICD-10 Mapping</th>
                <th>Estimated Likelihood</th>
              </tr>
            </thead>
            <tbody>
              ${conditions_of_concern.map(c => `
                <tr>
                  <td><strong>${c.label}</strong></td>
                  <td><code>${c.icdCode || 'N/A'}</code></td>
                  <td>
                    <div class="progress-bar-wrap">
                      <div class="progress-bar-fill" style="width: ${(c.risk * 100)}%; background-color: ${riskColor};"></div>
                      <span class="progress-bar-text">${(c.risk * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <div class="report-card">
          <h4 class="card-title">5. Multi-Modal Evidence Chain</h4>
          <ul class="evidence-list">
            ${evidence.map(item => `<li><span class="bullet-tag">▶</span> ${item}</li>`).join('')}
          </ul>
        </div>

        <div class="report-card">
          <h4 class="card-title">6. Specialist Referral & Clinical Action Order</h4>
          <div class="action-box">
            <div class="action-row"><strong>Recommended Action:</strong> ${assessmentData.recommended_action?.replace(/_/g, ' ').toUpperCase()}</div>
            <div class="action-row"><strong>Specialist Consultation:</strong> Department of ${specialist.toUpperCase()}</div>
            <div class="action-row"><strong>Referral Priority:</strong> ${urgency_tier}</div>
            <div class="clinical-note-box">
              <strong>Clinical Narrative:</strong>
              <p>${clinical_summary}</p>
            </div>
          </div>
        </div>

        <div class="report-footer">
          <div class="footer-disclaimer">
            <strong>IMPORTANT CLINICAL NOTICE:</strong> This document is generated by an AI-assisted screening and decision-support prototype (CardioNav AI). It does NOT constitute a definitive medical diagnosis. All findings must be validated with formal 12-lead ECG, clinical examination, and physician oversight.
          </div>
          <div class="sign-off-grid">
            <div class="sign-box">
              <div class="sign-line"></div>
              <span>Evaluating Clinician / Triage Officer</span>
            </div>
            <div class="sign-box text-right">
              <div class="sign-line"></div>
              <span>Hospital Department Stamp & Date</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}
