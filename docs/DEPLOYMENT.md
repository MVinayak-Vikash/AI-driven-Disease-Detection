# 🚀 CardioNav AI — Deployment & Supabase Setup Guide

## 1. Supabase Setup
1. Create a project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** in the Supabase Dashboard.
3. Execute the migration script: `supabase/migrations/20260817000001_create_schema_and_rls.sql`.
4. Copy your project URL, anon key, and service role key from **Project Settings ➔ API**.

---

## 2. Environment Configuration
Create a `.env` file in the root directory:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

AI_PROVIDER=mock
PORT=8000
```

---

## 3. Running Locally

### Backend:
```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger docs will be available at: `http://localhost:8000/docs`

### Frontend:
Open `frontend/index.html` directly in any web browser or serve with:
```bash
python frontend/server.py
```

### Running Tests:
```bash
pytest backend/tests/ -v
```
