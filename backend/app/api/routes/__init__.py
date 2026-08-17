from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.profile import router as profile_router
from backend.app.api.routes.devices import router as devices_router
from backend.app.api.routes.sessions import router as sessions_router
from backend.app.api.routes.readings import router as readings_router
from backend.app.api.routes.signal import router as signal_router
from backend.app.api.routes.assessment import router as assessment_router
from backend.app.api.routes.history import router as history_router
from backend.app.api.routes.ws import router as ws_router

__all__ = [
    "auth_router",
    "profile_router",
    "devices_router",
    "sessions_router",
    "readings_router",
    "signal_router",
    "assessment_router",
    "history_router",
    "ws_router"
]
