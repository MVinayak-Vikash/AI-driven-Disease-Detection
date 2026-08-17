/**
 * CardioNav AI - Patient Data & Clinical Taxonomy
 * Focused on 3 Diseases: Diabetes, Cardiac Disease / Arrest, and Anemia
 */

export const SYMPTOMS_LIST = [
  // Cardiac Symptoms
  { id: 'chest_pain', label: 'Chest Pain / Pressure / Tightness', category: 'cardiac', disease: 'cardiac' },
  { id: 'palpitations', label: 'Heart Palpitations / Rapid Fluttering', category: 'cardiac', disease: 'cardiac' },
  { id: 'dyspnea', label: 'Shortness of Breath (Dyspnea)', category: 'cardiac', disease: 'cardiac' },
  { id: 'cold_sweat', label: 'Sudden Cold Sweats / Clamminess', category: 'cardiac', disease: 'cardiac' },
  
  // Diabetes Symptoms
  { id: 'excessive_thirst', label: 'Excessive Thirst (Polydipsia)', category: 'diabetes', disease: 'diabetes' },
  { id: 'frequent_urination', label: 'Frequent Urination (Polyuria)', category: 'diabetes', disease: 'diabetes' },
  { id: 'slow_healing', label: 'Slow-Healing Wounds or Cuts', category: 'diabetes', disease: 'diabetes' },
  { id: 'blurred_vision', label: 'Blurred Vision & Eye Strain', category: 'diabetes', disease: 'diabetes' },

  // Anemia Symptoms
  { id: 'extreme_fatigue', label: 'Extreme Fatigue / Exhaustion', category: 'anemia', disease: 'anemia' },
  { id: 'dizziness', label: 'Dizziness / Lightheadedness', category: 'anemia', disease: 'anemia' },
  { id: 'pale_skin', label: 'Pale Skin, Gums or Nail Beds (Pallor)', category: 'anemia', disease: 'anemia' },
  { id: 'cold_extremities', label: 'Cold Hands and Feet', category: 'anemia', disease: 'anemia' }
];

export const MEDICAL_HISTORY_LIST = [
  { id: 'hypertension', label: 'Hypertension (High Blood Pressure)' },
  { id: 'family_diabetes', label: 'Family History of Diabetes' },
  { id: 'prior_cardiac_event', label: 'Prior Heart Attack / CAD History' },
  { id: 'iron_deficiency', label: 'History of Iron Deficiency / Anemia' },
  { id: 'smoking', label: 'Tobacco Smoker / Nicotine Use' },
  { id: 'kidney_disease', label: 'Chronic Kidney Disease' }
];

export const DEMO_SCENARIOS = {
  cardiac_alert: {
    id: 'cardiac_alert',
    title: '❤️ High Cardiac Arrest / Arrhythmia Risk Case',
    patient: {
      fullName: 'Vikram Sundaram',
      age: 54,
      sex: 'male',
      systolicBp: 154,
      diastolicBp: 96,
      glucose: 110,
      hemoglobin: 14.2,
      bmi: 28.1,
      symptoms: ['chest_pain', 'palpitations', 'dyspnea', 'cold_sweat'],
      history: ['hypertension', 'prior_cardiac_event', 'smoking']
    },
    sensorProfile: {
      type: 'arrhythmia',
      baseBpm: 112,
      bpmVariance: 16,
      hrv: 18.5,
      rhythmIrregularity: 0.78,
      signalQuality: 0.94,
      spo2: 95,
      abnormalBeatsRatio: 0.4
    }
  },

  diabetes_case: {
    id: 'diabetes_case',
    title: '🩺 High Diabetes & Metabolic Risk Case',
    patient: {
      fullName: 'Ramesh Patel',
      age: 48,
      sex: 'male',
      systolicBp: 134,
      diastolicBp: 86,
      glucose: 215,
      hemoglobin: 13.8,
      bmi: 31.2,
      symptoms: ['excessive_thirst', 'frequent_urination', 'slow_healing', 'blurred_vision'],
      history: ['family_diabetes', 'hypertension']
    },
    sensorProfile: {
      type: 'normal',
      baseBpm: 78,
      bpmVariance: 4,
      hrv: 42.0,
      rhythmIrregularity: 0.12,
      signalQuality: 0.96,
      spo2: 98,
      abnormalBeatsRatio: 0.0
    }
  },

  anemia_case: {
    id: 'anemia_case',
    title: '🩸 Moderate Anemia & Fatigue Case',
    patient: {
      fullName: 'Pooja Narayanan',
      age: 26,
      sex: 'female',
      systolicBp: 104,
      diastolicBp: 68,
      glucose: 92,
      hemoglobin: 8.6,
      bmi: 19.4,
      symptoms: ['extreme_fatigue', 'dizziness', 'pale_skin', 'cold_extremities'],
      history: ['iron_deficiency']
    },
    sensorProfile: {
      type: 'tachycardia',
      baseBpm: 94,
      bpmVariance: 5,
      hrv: 38.0,
      rhythmIrregularity: 0.18,
      signalQuality: 0.95,
      spo2: 96,
      abnormalBeatsRatio: 0.05
    }
  },

  normal_case: {
    id: 'normal_case',
    title: '🟢 Normal Healthy Baseline (Low Risk Across All 3)',
    patient: {
      fullName: 'Ananya Sharma',
      age: 27,
      sex: 'female',
      systolicBp: 116,
      diastolicBp: 76,
      glucose: 95,
      hemoglobin: 13.5,
      bmi: 21.5,
      symptoms: [],
      history: []
    },
    sensorProfile: {
      type: 'normal',
      baseBpm: 70,
      bpmVariance: 2,
      hrv: 68.0,
      rhythmIrregularity: 0.06,
      signalQuality: 0.98,
      spo2: 99,
      abnormalBeatsRatio: 0.0
    }
  }
};
