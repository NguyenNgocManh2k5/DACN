import json
from pathlib import Path

CONFIG_FILE = Path("app_config.json")

def save_remembered_username(username):
    """Lưu tên đăng nhập vào file JSON cục bộ"""
    try:
        data = {"last_username": username}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def load_remembered_username():
    """Đọc tên đăng nhập đã lưu trước đó"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_username", "")
    except Exception:
        pass
    return ""