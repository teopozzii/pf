import pytest


class TestConfig:
    def test_config_loads_successfully(self):
        from utils.config import CONFIG
        assert CONFIG is not None
        assert isinstance(CONFIG, dict)
        assert len(CONFIG) > 0

    def test_config_has_at_least_one_user(self):
        from utils.config import CONFIG
        assert len(CONFIG) >= 1

    def test_config_has_default_user(self):
        from utils.config import CONFIG
        assert "papà" in CONFIG

    def test_config_default_user_has_required_headers(self):
        from utils.config import CONFIG
        headers = CONFIG["papà"]["headers"]
        
        required_headers = ["loc_identif", "category", "date", "descript", "detail", "value"]
        for header in required_headers:
            assert header in headers, f"Missing required header: {header}"

    def test_config_default_user_categories_structure(self):
        import json
        from utils.paths import resource_path
        
        # Default categories are now stored in default_categories.json
        default_cat_path = resource_path("utils/default_categories.json")
        with open(default_cat_path) as f:
            default_categories = json.load(f)
        
        assert "papà" in default_categories
        categories = default_categories["papà"]
        
        assert isinstance(categories, dict)
        assert len(categories) > 0
        
        for category, keywords in categories.items():
            assert isinstance(category, str)
            assert isinstance(keywords, list)
            assert all(isinstance(kw, str) for kw in keywords)
