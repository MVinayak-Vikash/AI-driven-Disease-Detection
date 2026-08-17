import json
import logging
from typing import Dict, Set, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("cardionav.ws")

router = APIRouter(tags=["Real-Time Sensor WebSocket"])

class ConnectionManager:
    def __init__(self):
        # Maps session_id to set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket client connected to session: {session_id}")

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket client disconnected from session: {session_id}")

    async def broadcast(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.active_connections:
            dead_connections = set()
            payload = json.dumps(message)
            for ws in self.active_connections[session_id]:
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.warning(f"Error sending to WS client: {e}")
                    dead_connections.add(ws)
            for dead in dead_connections:
                self.active_connections[session_id].discard(dead)

manager = ConnectionManager()

async def broadcast_sensor_frame(session_id: str, data: Dict[str, Any]):
    """Helper used by ingestion routes to broadcast telemetry to live subscribers."""
    await manager.broadcast(session_id, data)

@router.websocket("/ws/sessions/{session_id}")
async def session_sensor_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time PPG waveform streaming and BPM telemetry.
    """
    await manager.connect(session_id, websocket)
    try:
        while True:
            # Keep connection alive; can receive client heartbeat pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    except Exception as e:
        logger.warning(f"WebSocket exception: {e}")
        manager.disconnect(session_id, websocket)
