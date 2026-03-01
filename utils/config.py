import json
from typing import Any, Dict, List
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
