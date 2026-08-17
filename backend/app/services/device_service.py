import uuid
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

from backend.app.core.database import db_memory, get_supabase_client
from backend.app.core.security import hash_device_token, verify_device_token
from backend.app.schemas.device import DeviceCreate, DeviceResponse

class DeviceService:
    @staticmethod
    def register_device(user_id: str, data: DeviceCreate) -> DeviceResponse:
        raw_token = data.device_token or f"dev_tok_{secrets.token_urlsafe(18)}"
        token_hash = hash_device_token(raw_token)
        device_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        supabase = get_supabase_client()
        if supabase:
            try:
                # Check for existing device_uid
                existing = supabase.table("devices").select("id").eq("device_uid", data.device_uid).execute()
                if existing.data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Device with UID '{data.device_uid}' is already registered."
                    )

                res = supabase.table("devices").insert({
                    "id": device_id,
                    "user_id": user_id,
                    "device_uid": data.device_uid,
                    "device_name": data.device_name,
                    "device_type": data.device_type or "ESP32_MAX30102",
                    "device_token_hash": token_hash,
                    "status": "active",
                    "created_at": now.isoformat()
                }).execute()
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error registering device: {str(e)}")
        else:
            # Memory store
            for d in db_memory.devices.values():
                if d["device_uid"] == data.device_uid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Device with UID '{data.device_uid}' is already registered."
                    )

            db_memory.devices[device_id] = {
                "id": device_id,
                "user_id": user_id,
                "device_uid": data.device_uid,
                "device_name": data.device_name,
                "device_type": data.device_type or "ESP32_MAX30102",
                "device_token_hash": token_hash,
                "status": "active",
                "last_seen": None,
                "created_at": now
            }

        return DeviceResponse(
            id=device_id,
            user_id=user_id,
            device_uid=data.device_uid,
            device_name=data.device_name,
            device_type=data.device_type or "ESP32_MAX30102",
            status="active",
            created_at=now,
            generated_token=raw_token
        )

    @staticmethod
    def list_devices(user_id: str) -> List[DeviceResponse]:
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("devices").select("*").eq("user_id", user_id).execute()
                return [DeviceResponse(**row) for row in (res.data or [])]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error listing devices: {str(e)}")
        
        user_devs = [
            DeviceResponse(**d) for d in db_memory.devices.values() if d["user_id"] == user_id
        ]
        return user_devs

    @staticmethod
    def get_device(user_id: str, device_id: str) -> Optional[DeviceResponse]:
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("devices").select("*").eq("id", device_id).eq("user_id", user_id).execute()
                if not res.data:
                    return None
                return DeviceResponse(**res.data[0])
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        dev = db_memory.devices.get(device_id)
        if dev and dev["user_id"] == user_id:
            return DeviceResponse(**dev)
        return None

    @staticmethod
    def delete_device(user_id: str, device_id: str) -> bool:
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("devices").delete().eq("id", device_id).eq("user_id", user_id).execute()
                return bool(res.data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error deleting device: {str(e)}")
        
        dev = db_memory.devices.get(device_id)
        if dev and dev["user_id"] == user_id:
            del db_memory.devices[device_id]
            return True
        return False

    @staticmethod
    def authenticate_device(device_uid: str, device_token: str) -> Optional[Dict[str, Any]]:
        """
        Validates device credentials for sensor ingestion.
        """
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("devices").select("*").eq("device_uid", device_uid).eq("status", "active").execute()
                if not res.data:
                    return None
                dev = res.data[0]
                if verify_device_token(device_token, dev["device_token_hash"]):
                    # Update last seen
                    supabase.table("devices").update({
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    }).eq("id", dev["id"]).execute()
                    return dev
                return None
            except Exception:
                return None
        
        for dev in db_memory.devices.values():
            if dev["device_uid"] == device_uid and dev["status"] == "active":
                if verify_device_token(device_token, dev["device_token_hash"]):
                    dev["last_seen"] = datetime.now(timezone.utc)
                    return dev
        return None
