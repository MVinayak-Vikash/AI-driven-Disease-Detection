/**
 * CardioNav AI - Tri-Disease Clinical AI Reasoning Engine
 * Specialized Risk Prediction Models for:
 * 1. Diabetes Mellitus
 * 2. Cardiac Disease & Cardiac Arrest Warning
 * 3. Anemia (Hemoglobin & Oxygenation Deficiency)
 */

export class AIClinicalReasoner {
  constructor() {}

  /**
   * Evaluates patient data + real-time sensor stream
   * Generates discrete predictions for Diabetes, Cardiac Arrest, and Anemia
   */
  async assessRisk(patientData, sensorFeatures) {
    // Slight simulated inference latency
    await new Promise((r) => setTimeout(r, 200));

    const diabetesResult = this.predictDiabetes(patientData);
    const cardiacResult = this.predictCardiac(patientData, sensorFeatures);
    const anemiaResult = this.predictAnemia(patientData, sensorFeatures);

    // Highest severity determines triage urgency
    const maxScore = Math.max(diabetesResult.score, cardiacResult.score, anemiaResult.score);
    let overallRiskLevel = 'LOW';
    let urgencyBadge = 'Routine Health Maintenance';
    let isEmergency = false;

    if (cardiacResult.score >= 75 || cardiacResult.isImminentArrestWarning) {
      overallRiskLevel = 'HIGH';
      urgencyBadge = 'EMERGENCY: Immediate Cardiac Triage';
      isEmergency = true;
    } else if (maxScore >= 65) {
      overallRiskLevel = 'HIGH';
      urgencyBadge = 'Urgent: Specialist Evaluation within 24-48h';
    } else if (maxScore >= 35) {
      overallRiskLevel = 'MODERATE';
      urgencyBadge = 'Priority: Primary Care Review within 1-2 Weeks';
    }

    return {
      timestamp: new Date().toISOString(),
      patient: {
        name: patientData.fullName || 'Anonymous Patient',
        age: Number(patientData.age) || 40,
        sex: patientData.sex || 'male',
        bp: `${patientData.systolicBp || 120}/${patientData.diastolicBp || 80} mmHg`,
        glucose: Number(patientData.glucose) || 95,
        hemoglobin: Number(patientData.hemoglobin) || 13.5
      },
      sensor: {
        heartRate: sensorFeatures.heartRate || 72,
        hrv: sensorFeatures.hrv || 45,
        rhythmIrregularity: sensorFeatures.rhythmIrregularity || 0.1,
        spo2: sensorFeatures.spo2 || 98
      },
      overall_risk_level: overallRiskLevel,
      urgency_badge: urgencyBadge,
      is_emergency: isEmergency,
      predictions: {
        diabetes: diabetesResult,
        cardiac: cardiacResult,
        anemia: anemiaResult
      }
    };
  }

  /**
   * 1. DIABETES RISK PREDICTION
   */
  predictDiabetes(patient) {
    const glucose = Number(patient.glucose) || 95;
    const bmi = Number(patient.bmi) || 23;
    const symptoms = patient.symptoms || [];
    const history = patient.history || [];

    let score = 0;
    const evidence = [];

    // Blood Glucose Evaluation (mg/dL)
    if (glucose >= 200) {
      score += 55;
      evidence.push(`Random blood glucose is severely elevated (${glucose} mg/dL ≥ 200 mg/dL diagnostic threshold)`);
    } else if (glucose >= 140) {
      score += 40;
      evidence.push(`Elevated blood glucose indicating impaired glucose tolerance (${glucose} mg/dL)`);
    } else if (glucose >= 100) {
      score += 20;
      evidence.push(`Borderline fasting glucose in pre-diabetic window (${glucose} mg/dL)`);
    } else {
      evidence.push(`Normoglycemic blood glucose reading (${glucose} mg/dL)`);
    }

    // Classic Symptoms (Polydipsia, Polyuria, Slow Healing, Vision)
    if (symptoms.includes('excessive_thirst')) {
      score += 15;
      evidence.push('Reported polydipsia (abnormal excessive thirst)');
    }
    if (symptoms.includes('frequent_urination')) {
      score += 15;
      evidence.push('Reported polyuria (frequent osmotic diuresis)');
    }
    if (symptoms.includes('slow_healing')) {
      score += 10;
      evidence.push('Slow-healing wounds indicating microvascular delay');
    }
    if (symptoms.includes('blurred_vision')) {
      score += 10;
      evidence.push('Transient refractive blurring associated with glycemic shifts');
    }

    // Comorbidities
    if (history.includes('family_diabetes')) {
      score += 12;
      evidence.push('Positive first-degree genetic predisposition for Type 2 Diabetes');
    }
    if (bmi >= 30) {
      score += 10;
      evidence.push(`Obesity-level BMI (${bmi}) contributing to insulin resistance`);
    }

    score = Math.min(100, Math.max(5, score));

    let status = 'Low Risk (Normoglycemic)';
    let level = 'LOW';
    let recommendation = 'Maintain healthy diet and regular physical activity.';

    if (score >= 65 || glucose >= 180) {
      status = 'High Diabetes Risk';
      level = 'HIGH';
      recommendation = 'Order formal Fasting Plasma Glucose (FPG) & HbA1c lab tests. Refer to Endocrinology.';
    } else if (score >= 35 || glucose >= 115) {
      status = 'Pre-Diabetes / Moderate Risk';
      level = 'MODERATE';
      recommendation = 'Recommend Oral Glucose Tolerance Test (OGTT) and lifestyle glycemic management.';
    }

    return {
      name: 'Diabetes Mellitus Risk',
      score,
      level,
      status,
      evidence,
      recommendation
    };
  }

  /**
   * 2. CARDIAC DISEASE & CARDIAC ARREST RISK PREDICTION
   */
  predictCardiac(patient, sensor) {
    const hr = Number(sensor.heartRate) || 75;
    const hrv = Number(sensor.hrv) || 40;
    const irregularity = Number(sensor.rhythmIrregularity) || 0.1;
    const systolic = Number(patient.systolicBp) || 120;
    const diastolic = Number(patient.diastolicBp) || 80;
    const symptoms = patient.symptoms || [];
    const history = patient.history || [];

    let score = 0;
    let isImminentWarning = false;
    const evidence = [];

    // Real-Time Sensor Arrhythmia & Irregularity
    if (irregularity >= 0.65) {
      score += 45;
      evidence.push(`Marked pulse rhythm irregularity index (${(irregularity * 100).toFixed(0)}%) pointing to chaotic atrial/ventricular depolarization`);
    } else if (irregularity >= 0.25) {
      score += 20;
      evidence.push(`Mild pulse interval variance detected (${(irregularity * 100).toFixed(0)}%)`);
    } else {
      evidence.push(`Stable, rhythmic pulse waveform (${(irregularity * 100).toFixed(0)}% irregularity)`);
    }

    // Heart Rate & HRV
    if (hr > 110) {
      score += 20;
      evidence.push(`Significant resting tachycardia (${hr} BPM > 100 BPM threshold)`);
    } else if (hr < 50) {
      score += 18;
      evidence.push(`Severe bradycardia (${hr} BPM < 50 BPM)`);
    }

    if (hrv < 22) {
      score += 15;
      evidence.push(`Depressed HRV RMSSD (${hrv} ms) reflecting severe autonomic strain`);
    }

    // Blood Pressure
    if (systolic >= 150 || diastolic >= 95) {
      score += 20;
      evidence.push(`Hypertensive crisis stage BP profile (${systolic}/${diastolic} mmHg)`);
    } else if (systolic >= 135 || diastolic >= 85) {
      score += 10;
      evidence.push(`Elevated vascular resistance (${systolic}/${diastolic} mmHg)`);
    }

    // Acute Symptoms (Chest pain, cold sweat, palpitations, dyspnea)
    if (symptoms.includes('chest_pain')) {
      score += 35;
      isImminentWarning = true;
      evidence.push('CRITICAL: Active chest discomfort / pressure reported');
    }
    if (symptoms.includes('cold_sweat')) {
      score += 15;
      evidence.push('Diaphoresis (sudden cold clammy sweats)');
    }
    if (symptoms.includes('palpitations')) {
      score += 12;
      evidence.push('Reported rapid cardiac fluttering / palpitations');
    }
    if (symptoms.includes('dyspnea')) {
      score += 12;
      evidence.push('Acute exertional dyspnea / shortness of breath');
    }

    // Past History
    if (history.includes('prior_cardiac_event')) {
      score += 20;
      evidence.push('Known clinical history of prior myocardial infarction or CAD');
    }

    score = Math.min(100, Math.max(5, score));

    let status = 'Low Cardiac Risk (Stable)';
    let level = 'LOW';
    let recommendation = 'Normal cardiovascular rhythm. Periodic annual checkup recommended.';

    if (score >= 65 || isImminentWarning) {
      status = 'High Cardiac Arrest & Arrhythmia Risk';
      level = 'HIGH';
      recommendation = 'Immediate 12-lead ECG telemetry. Urgent evaluation by Cardiology / Emergency Ward.';
    } else if (score >= 35) {
      status = 'Moderate Cardiovascular Stress';
      level = 'MODERATE';
      recommendation = 'Schedule outpatient ECG and 24h Holter monitoring. Cardiology consult recommended.';
    }

    return {
      name: 'Cardiac Disease & Arrest Warning',
      score,
      level,
      status,
      isImminentArrestWarning: isImminentWarning,
      evidence,
      recommendation
    };
  }

  /**
   * 3. ANEMIA RISK PREDICTION
   */
  predictAnemia(patient, sensor) {
    const hb = Number(patient.hemoglobin) || 13.5;
    const isFemale = patient.sex === 'female';
    const spo2 = Number(sensor.spo2) || 98;
    const symptoms = patient.symptoms || [];
    const history = patient.history || [];

    let score = 0;
    const evidence = [];

    // Hemoglobin Cutoffs (g/dL)
    const normalMin = isFemale ? 12.0 : 13.5;

    if (hb < 8.0) {
      score += 65;
      evidence.push(`Severe hemoglobin depletion (${hb} g/dL < 8.0 g/dL critical cutoff)`);
    } else if (hb < 10.0) {
      score += 45;
      evidence.push(`Moderate anemia detected (${hb} g/dL)`);
    } else if (hb < normalMin) {
      score += 25;
      evidence.push(`Mild hemoglobin reduction below normative threshold (${hb} g/dL < ${normalMin} g/dL)`);
    } else {
      evidence.push(`Normal physiological hemoglobin concentration (${hb} g/dL)`);
    }

    // Symptoms (Fatigue, Dizziness, Pale skin, Cold extremities)
    if (symptoms.includes('pale_skin')) {
      score += 20;
      evidence.push('Visible pallor in skin, conjunctiva, or nail beds');
    }
    if (symptoms.includes('extreme_fatigue')) {
      score += 15;
      evidence.push('Persistent chronic fatigue from reduced cellular oxygen delivery');
    }
    if (symptoms.includes('dizziness')) {
      score += 10;
      evidence.push('Postural dizziness / lightheadedness');
    }
    if (symptoms.includes('cold_extremities')) {
      score += 8;
      evidence.push('Peripheral vasoconstriction (cold hands and feet)');
    }

    // Oxygenation & History
    if (spo2 < 95) {
      score += 12;
      evidence.push(`Sub-optimal pulse oximetry saturation (${spo2}% SpO2)`);
    }
    if (history.includes('iron_deficiency')) {
      score += 15;
      evidence.push('Clinical history of chronic iron deficiency / nutritional anemia');
    }

    score = Math.min(100, Math.max(5, score));

    let status = 'Normal Blood Profile';
    let level = 'LOW';
    let recommendation = 'Hemoglobin levels within normal reference range.';

    if (score >= 65 || hb < 9.0) {
      status = 'Severe / Moderate Anemia';
      level = 'HIGH';
      recommendation = 'Order Complete Blood Count (CBC), Serum Ferritin, and Iron Profile. Consult Hematology.';
    } else if (score >= 35 || hb < normalMin) {
      status = 'Mild Anemia / Deficiency Risk';
      level = 'MODERATE';
      recommendation = 'Recommend dietary iron optimization and follow-up CBC screening in 4 weeks.';
    }

    return {
      name: 'Anemia & Hemoglobin Profile',
      score,
      level,
      status,
      evidence,
      recommendation
    };
  }
}
