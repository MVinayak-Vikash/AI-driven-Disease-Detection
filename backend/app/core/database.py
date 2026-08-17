import logging
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings

logger = logging.getLogger("cardionav.database")

# In-memory storage for development, mock tests, and offline mode
class InMemoryDB:
    def __init__(self):
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.measurement_sessions: Dict[str, Dict[str, Any]] = {}
        self.sensor_readings: Dict[str, List[Dict[str, Any]]] = {}
        self.physiological_features: Dict[str, Dict[str, Any]] = {}
        self.ai_assessments: Dict[str, Dict[str, Any]] = {}

    def clear(self):
        self.profiles.clear()
        self.devices.clear()
        self.measurement_sessions.clear()
        self.sensor_readings.clear()
        self.physiological_features.clear()
        self.ai_assessments.clear()

db_memory = InMemoryDB()

_supabase_client = None

def is_valid_supabase_config() -> bool:
    url = (settings.SUPABASE_URL or "").lower()
    key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").lower()
    
    if not url or not key:
        return False
    
    dummy_patterns = ["placeholder", "your-project", "example.co", "...", "your-service-role-key"]
    for pattern in dummy_patterns:
        if pattern in url or pattern in key:
            return False
            
    return url.startswith("https://") or url.startswith("http://")

def get_supabase_client():
    """
    Initializes and returns the Supabase Client if valid credentials are provided.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if is_valid_supabase_config():
        try:
            from supabase import create_client
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.info("Supabase client initialized successfully.")
            return _supabase_client
        except Exception as e:
            logger.warning(f"Could not connect to live Supabase: {e}. Falling back to memory storage.")
            return None
    return None
