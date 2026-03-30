import json
import time
from typing import Any, Dict
from utils.paths import resource_path
from dash import dcc, html

CONFIG: Dict[str, Dict[str, Any]] = json.load(open(resource_path("utils/config.json")))
SIDEBAR_STYLE: Dict[str, Any] = json.load(open(resource_path("utils/sidebar_style.json")))

# placeholder components:
data_preview_msg_placeholder = html.Div(
    id='output-div',
    style={"display" : "none"}
)

data_upload_timestamp_placeholder = dcc.Store(
    id="data-upload-timestamp",
    storage_type='session',
    data=None
)

drag_and_drop_placeholder = dcc.Upload(
    id='upload-data',
    children=html.Div(
        "Trascina qui il file o clicca per selezionare",
        style={"display": "none"}
    ), style={"display": "none"},  # Hidden
    contents=None,
)

home_page_placeholders = [
    data_preview_msg_placeholder,
    data_upload_timestamp_placeholder,
    drag_and_drop_placeholder,
]


# ============================================================================
# Heartbeat Tracking (instantiated by app.py and shared by launcher.py)
# ============================================================================
class HeartbeatTracker:
    """
    Thread-safe heartbeat tracker shared between server and launcher.
    Launcher monitors browser heartbeats without HTTP calls.
    
    This design is robust and scalable:
    - No hardcoded localhost addresses
    - Works with any deployment (local, Docker, remote)
    - Direct in-memory access (no network calls)
    - Simple to test and debug
    """
    def __init__(self):
        self.last_heartbeat = time.time()
    
    def record_heartbeat(self):
        """Server calls this when browser sends heartbeat."""
        self.last_heartbeat = time.time()
    
    def seconds_since_heartbeat(self) -> float:
        """Launcher calls this to check heartbeat freshness."""
        return time.time() - self.last_heartbeat
