-- =====================================================================
-- Migration: 20260817000002_seed_demo_data.sql
-- Description: Seed fixtures for testing baseline deviations & AI referral
-- =====================================================================

-- Note: In production or real environments, users are created via Supabase Auth signup.
-- This script contains template fixtures demonstrating historical longitudinal trends.

-- Commented template query for reference when setting up demo accounts:
/*
-- 1. Example Profile
INSERT INTO public.profiles (id, name, age, gender, medical_history)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Vikram Sundaram (Demo Patient)',
    54,
    'male',
    '["hypertension", "smoking"]'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- 2. Example Device
INSERT INTO public.devices (id, user_id, device_uid, device_name, device_token_hash, status)
VALUES (
    '10000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'ESP32-A8F31',
    'CardioNav ESP32 Sensor 01',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'active'
) ON CONFLICT (device_uid) DO NOTHING;
*/
