import json
from utils.paths import resource_path

CONFIG = json.load(open(resource_path("utils/config.json")))
SIDEBAR_STYLE = json.load(open(resource_path("utils/sidebar_style.json")))
