from __future__ import annotations
import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID
from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .auth import CurrentUser, get_current_user, get_repository
from .config import Settings, get_settings
from .errors import api_error
from .repository import SupabaseRepository
from .schemas import AssessmentRequest, DeviceCreate, ProfileUpdate, ReadingCreate, SessionCreate
from .services import SignalAnalysisService, get_ai_service

app = FastAPI(title="AI Early-Risk & Referral Navigator", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Malformed or invalid request data.", "details": exc.errors()}})


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


def eq(**kwargs: object) -> dict[str, str]: return {key: f"eq.{value}" for key, value in kwargs.items()}
def now() -> str: return datetime.now(timezone.utc).isoformat()


@app.get("/health")
async def health(): return {"status": "ok"}


@app.get("/api/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    return {"data": {"id": user.id, "email": user.email}}


@app.get("/api/profile")
async def get_profile(user: CurrentUser = Depends(get_current_user), repo: SupabaseRepository = Depends(get_repository)):
    profile = await repo.one("profiles", eq(id=user.id))
    return {"data": profile}


@app.put("/api/profile")
async def put_profile(body: ProfileUpdate, user: CurrentUser = Depends(get_current_user), repo: SupabaseRepository = Depends(get_repository)):
    existing = await repo.one("profiles", eq(id=user.id))
    values = body.model_dump(exclude_unset=True)
    values["updated_at"] = now()
    profile = await repo.update("profiles", eq(id=user.id), values) if existing else await repo.insert("profiles", {"id": user.id, **values})
    return {"data": profile}


@app.post("/api/devices", status_code=201)
async def register_device(body: DeviceCreate, user: CurrentUser = Depends(get_current_user), repo: SupabaseRepository = Depends(get_repository)):
    credential = secrets.token_urlsafe(32)
    try:
        device = await repo.insert("devices", {**body.model_dump(), "user_id": user.id, "device_token_hash": hashlib.sha256(credential.encode()).hexdigest(), "status": "active"})
    except Exception:
        raise api_error(409, "DEVICE_UID_EXISTS", "This device UID is already registered.")
    # This is deliberately the only response that contains the device credential.
    return {"data": device, "device_credential": credential}


@app.get("/api/devices")
async def list_devices(repo: SupabaseRepository = Depends(get_repository)):
    return {"data": await repo.request("GET", "devices", params={"order": "created_at.desc"})}


@app.get("/api/devices/{device_id}")
async def get_device(device_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    device = await repo.one("devices", eq(id=device_id))
    if not device: raise api_error(404, "DEVICE_NOT_FOUND", "Device does not exist or is not accessible.")
    device.pop("device_token_hash", None)
    return {"data": device}


@app.delete("/api/devices/{device_id}", status_code=204)
async def delete_device(device_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    if not await repo.one("devices", eq(id=device_id)): raise api_error(404, "DEVICE_NOT_FOUND", "Device does not exist or is not accessible.")
    await repo.delete("devices", eq(id=device_id))


async def owned_session(session_id: UUID, repo: SupabaseRepository) -> dict:
    session = await repo.one("measurement_sessions", eq(id=session_id))
    if not session: raise api_error(404, "SESSION_NOT_FOUND", "Measurement session does not exist or is not accessible.")
    return session


@app.post("/api/sessions", status_code=201)
async def create_session(body: SessionCreate, user: CurrentUser = Depends(get_current_user), repo: SupabaseRepository = Depends(get_repository)):
    device = await repo.one("devices", eq(id=body.device_id))
    if not device: raise api_error(404, "DEVICE_NOT_FOUND", "Device does not exist or is not accessible.")
    return {"data": await repo.insert("measurement_sessions", {"user_id": user.id, "device_id": str(body.device_id), "status": "active"})}


@app.get("/api/sessions")
async def list_sessions(repo: SupabaseRepository = Depends(get_repository)):
    return {"data": await repo.request("GET", "measurement_sessions", params={"order": "started_at.desc"})}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    return {"data": await owned_session(session_id, repo)}


@app.post("/api/sessions/{session_id}/finish")
async def finish_session(session_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    await owned_session(session_id, repo)
    return {"data": await repo.update("measurement_sessions", eq(id=session_id), {"status": "finished", "ended_at": now()})}


async def save_reading(session: dict, body: ReadingCreate, repo: SupabaseRepository) -> dict:
    if not body.has_measurement(): raise api_error(422, "EMPTY_READING", "At least one measurement field is required.")
    if session["status"] != "active": raise api_error(409, "SESSION_NOT_ACTIVE", "Measurements may only be added to an active session.")
    timestamp = body.timestamp
    if isinstance(timestamp, (int, float)): timestamp = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
    elif isinstance(timestamp, datetime): timestamp = timestamp.isoformat()
    return await repo.insert("sensor_readings", {"session_id": session["id"], "timestamp": timestamp or now(), "heart_rate": body.heart_rate, "spo2": body.spo2, "signal_quality": body.signal_quality, "ppg_data": body.ppg})


@app.post("/api/sessions/{session_id}/readings", status_code=201)
async def session_reading(session_id: UUID, body: ReadingCreate, repo: SupabaseRepository = Depends(get_repository)):
    session = await owned_session(session_id, repo)
    if body.session_id and body.session_id != session_id: raise api_error(422, "SESSION_MISMATCH", "Payload session_id does not match request path.")
    return {"data": await save_reading(session, body, repo)}


@app.get("/api/sessions/{session_id}/readings")
async def list_readings(session_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    await owned_session(session_id, repo)
    return {"data": await repo.request("GET", "sensor_readings", params={**eq(session_id=session_id), "order": "timestamp.asc"})}


def system_repository(settings: Settings) -> SupabaseRepository:
    # This key stays only on FastAPI; it is never sent to the ESP32 or frontend.
    if not settings.supabase_service_role_key: raise api_error(503, "DEVICE_INGEST_UNAVAILABLE", "Device ingestion is not configured.")
    return SupabaseRepository(settings, settings.supabase_service_role_key)


@app.post("/api/devices/{device_id}/readings", status_code=201)
async def device_reading(device_id: UUID, body: ReadingCreate, x_device_token: str | None = Header(None), settings: Settings = Depends(get_settings)):
    if not x_device_token: raise api_error(401, "DEVICE_UNAUTHORIZED", "A device credential is required.")
    repo = system_repository(settings)
    device = await repo.one("devices", eq(id=device_id))
    if not device or not secrets.compare_digest(device["device_token_hash"], hashlib.sha256(x_device_token.encode()).hexdigest()): raise api_error(401, "DEVICE_UNAUTHORIZED", "Invalid device credential.")
    session_id = body.session_id
    if not session_id: raise api_error(422, "SESSION_REQUIRED", "Device ingestion requires session_id in the payload.")
    session = await repo.one("measurement_sessions", eq(id=session_id))
    if not session or str(session["device_id"]) != str(device_id): raise api_error(403, "INVALID_DEVICE_SESSION", "The device is not authorized for this session.")
    if body.device_id and body.device_id != device["device_uid"]: raise api_error(422, "DEVICE_MISMATCH", "Payload device_id does not match registered device UID.")
    reading = await save_reading(session, body, repo)
    await repo.update("devices", eq(id=device_id), {"last_seen": now(), "status": "active"})
    return {"data": reading}


@app.post("/api/sessions/{session_id}/analyze-signal")
async def analyze_signal(session_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    await owned_session(session_id, repo)
    readings = await repo.request("GET", "sensor_readings", params={**eq(session_id=session_id), "order": "timestamp.asc"})
    # RLS on the join protects prior user sessions; only completed feature rows are consumed.
    historical = await repo.request("GET", "physiological_features", params={"select": "*,measurement_sessions!inner(user_id)", "measurement_sessions.user_id": "eq." + (await owned_session(session_id, repo))["user_id"], "order": "created_at.asc"})
    try: feature = SignalAnalysisService().analyze(readings, [x for x in historical if x.get("session_id") != str(session_id)])
    except ValueError as exc: raise api_error(422, "INSUFFICIENT_SIGNAL_DATA", str(exc))
    feature["session_id"] = str(session_id)
    return {"data": await repo.insert("physiological_features", feature)}


@app.get("/api/sessions/{session_id}/features")
async def get_features(session_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    await owned_session(session_id, repo)
    return {"data": await repo.one("physiological_features", eq(session_id=session_id))}


@app.post("/api/sessions/{session_id}/assess-risk")
async def assess_risk(session_id: UUID, body: AssessmentRequest, user: CurrentUser = Depends(get_current_user), repo: SupabaseRepository = Depends(get_repository), settings: Settings = Depends(get_settings)):
    await owned_session(session_id, repo)
    feature = await repo.one("physiological_features", eq(session_id=session_id))
    if not feature: raise api_error(409, "FEATURES_REQUIRED", "Analyze the session before requesting an assessment.")
    profile = await repo.one("profiles", eq(id=user.id)) or {}
    payload = {"patient": {"age": profile.get("age"), "gender": profile.get("gender"), "medical_history": profile.get("medical_history", [])}, "symptoms": body.symptoms, "current_sensor": {"heart_rate": feature["heart_rate_mean"], "hrv": feature.get("hrv"), "rhythm_irregularity": feature.get("rhythm_irregularity"), "signal_quality": feature.get("signal_quality")}, "baseline": feature.get("baseline_delta"), "trend": feature.get("trend_delta")}
    try: result = await get_ai_service(settings.ai_provider).assess(payload)
    except ValueError as exc: raise api_error(500, "AI_PROVIDER_INVALID", str(exc))
    record = {"session_id": str(session_id), **result.model_dump(), "model_name": settings.ai_provider if settings.ai_provider == "mock" else settings.model_name or settings.ai_provider, "model_version": "development" if settings.ai_provider == "mock" else "configured", "raw_response": result.model_dump()}
    return {"data": await repo.insert("ai_assessments", record)}


@app.get("/api/sessions/{session_id}/assessment")
async def get_assessment(session_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    await owned_session(session_id, repo)
    return {"data": await repo.one("ai_assessments", eq(session_id=session_id))}


@app.get("/api/history")
async def history(repo: SupabaseRepository = Depends(get_repository)):
    return {"data": await repo.request("GET", "measurement_sessions", params={"select": "*,physiological_features(*),ai_assessments(*)", "order": "started_at.desc"})}


@app.get("/api/history/{session_id}")
async def session_history(session_id: UUID, repo: SupabaseRepository = Depends(get_repository)):
    return {"data": await owned_session(session_id, repo)}


@app.websocket("/ws/sessions/{session_id}")
async def session_ws(websocket: WebSocket, session_id: UUID):
    # Browser passes a Supabase JWT in Authorization; REST ingestion remains the durable data path.
    try:
        user = await get_current_user(websocket.headers.get("authorization"), get_settings())
        repo = SupabaseRepository(get_settings(), user.token)
        await owned_session(session_id, repo)
    except Exception:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    await websocket.send_json({"type": "connected", "session_id": str(session_id), "message": "Use REST ingestion as the durable data path."})
    try:
        while True:
            message = await websocket.receive_json()
            try:
                reading = ReadingCreate.model_validate(message)
                if not reading.has_measurement(): raise ValueError
            except Exception:
                await websocket.send_json({"error": {"code": "VALIDATION_ERROR", "message": "Invalid reading message."}})
                continue
            await websocket.send_json({"type": "reading", "data": reading.model_dump(mode="json")})
    except WebSocketDisconnect: pass
