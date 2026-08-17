-- =====================================================================
-- Migration: 20260817000001_create_schema_and_rls.sql
-- Description: Core schema, tables, foreign keys, indexes, and RLS
-- Platform: AI Early-Risk & Referral Navigator (Supabase PostgreSQL)
-- =====================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================================
-- 1. PROFILES TABLE
-- Extends auth.users with clinical and demographic profile data
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT,
    age INTEGER CHECK (age >= 0 AND age <= 125),
    gender TEXT,
    medical_history JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- 2. DEVICES TABLE
-- Multi-device ownership per user with hashed hardware tokens
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_uid TEXT UNIQUE NOT NULL,
    device_name TEXT NOT NULL,
    device_type TEXT DEFAULT 'ESP32_MAX30102',
    device_token_hash TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'revoked')),
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- 3. MEASUREMENT SESSIONS TABLE
-- Tracks individual screening recording sessions
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.measurement_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_id UUID REFERENCES public.devices(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'aborted', 'analyzed'))
);

-- =====================================================================
-- 4. SENSOR READINGS TABLE
-- High-frequency sensor samples (PPG, HR, SpO2, signal quality)
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.sensor_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.measurement_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    heart_rate FLOAT CHECK (heart_rate IS NULL OR (heart_rate >= 20.0 AND heart_rate <= 260.0)),
    spo2 FLOAT CHECK (spo2 IS NULL OR (spo2 >= 40.0 AND spo2 <= 100.0)),
    ppg_data JSONB,
    signal_quality FLOAT CHECK (signal_quality IS NULL OR (signal_quality >= 0.0 AND signal_quality <= 1.0))
);

-- =====================================================================
-- 5. PHYSIOLOGICAL FEATURES TABLE
-- Computed features from signal analysis and baseline comparisons
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.physiological_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES public.measurement_sessions(id) ON DELETE CASCADE,
    heart_rate_mean FLOAT,
    heart_rate_min FLOAT,
    heart_rate_max FLOAT,
    hrv FLOAT,
    rmssd FLOAT,
    rhythm_irregularity FLOAT,
    signal_quality FLOAT,
    baseline_delta JSONB DEFAULT '{}'::jsonb,
    trend_delta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- 6. AI ASSESSMENTS TABLE
-- Structured clinical decision-support output and reasoning evidence
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.ai_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES public.measurement_sessions(id) ON DELETE CASCADE,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MODERATE', 'HIGH')),
    risk_score FLOAT NOT NULL CHECK (risk_score >= 0.0 AND risk_score <= 100.0),
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    conditions_of_concern JSONB DEFAULT '[]'::jsonb,
    evidence JSONB DEFAULT '[]'::jsonb,
    trends JSONB DEFAULT '[]'::jsonb,
    recommended_action TEXT NOT NULL,
    specialist TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    raw_response JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_devices_user_id ON public.devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_device_uid ON public.devices(device_uid);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.measurement_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_device_id ON public.measurement_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON public.measurement_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_session_id ON public.sensor_readings(session_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON public.sensor_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_physio_features_session_id ON public.physiological_features(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_assessments_session_id ON public.ai_assessments(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_assessments_created_at ON public.ai_assessments(created_at DESC);

-- =====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Strict user boundary isolation using auth.uid()
-- =====================================================================

-- 1. Profiles RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- 2. Devices RLS
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own devices"
    ON public.devices FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own devices"
    ON public.devices FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own devices"
    ON public.devices FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own devices"
    ON public.devices FOR DELETE
    USING (auth.uid() = user_id);

-- 3. Measurement Sessions RLS
ALTER TABLE public.measurement_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sessions"
    ON public.measurement_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions"
    ON public.measurement_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions"
    ON public.measurement_sessions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions"
    ON public.measurement_sessions FOR DELETE
    USING (auth.uid() = user_id);

-- 4. Sensor Readings RLS (Through parent session ownership)
ALTER TABLE public.sensor_readings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sensor readings"
    ON public.sensor_readings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = sensor_readings.session_id
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own sensor readings"
    ON public.sensor_readings FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = sensor_readings.session_id
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own sensor readings"
    ON public.sensor_readings FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = sensor_readings.session_id
            AND s.user_id = auth.uid()
        )
    );

-- 5. Physiological Features RLS (Through parent session ownership)
ALTER TABLE public.physiological_features ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own physiological features"
    ON public.physiological_features FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = physiological_features.session_id
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own physiological features"
    ON public.physiological_features FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = physiological_features.session_id
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own physiological features"
    ON public.physiological_features FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = physiological_features.session_id
            AND s.user_id = auth.uid()
        )
    );

-- 6. AI Assessments RLS (Through parent session ownership)
ALTER TABLE public.ai_assessments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own AI assessments"
    ON public.ai_assessments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = ai_assessments.session_id
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own AI assessments"
    ON public.ai_assessments FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = ai_assessments.session_id
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own AI assessments"
    ON public.ai_assessments FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.measurement_sessions s
            WHERE s.id = ai_assessments.session_id
            AND s.user_id = auth.uid()
        )
    );

-- Trigger for updating timestamps on profiles
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_profiles_updated_at ON public.profiles;
CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();
