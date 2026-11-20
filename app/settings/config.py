import json
import os
import sys


def get_appdata_dir():
    """Конфиги в %APPDATA%\\MediaOverlay\\ — доступно откуда угодно."""
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "MediaOverlay")
    os.makedirs(path, exist_ok=True)
    return path


def get_resource_dir():
    """Ресурсы — рядом с .exe или в _MEIPASS (PyInstaller)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.abspath(".")


CONFIG_PATH = os.path.join(get_appdata_dir(), "config.json")
RESOURCE_DIR = get_resource_dir()


DEFAULT_CONFIG = {
    "overlay": {
        "width": 400,
        "height": 230,
        "position": "bottom-right",
        "bg_color": [20, 20, 30, 200],
        "border_color": [139, 92, 246, 255],
        "border_color_1": [139, 92, 246, 255],
        "border_color_2": [239, 68, 68, 255],
        "border_width": 2,
        "border_radius": 16,
        "border_mode": "solid",
        "border_rgb_speed": 1.0,
        "bg_image": None,
        "bg_image_opacity": 0.5,
        "title_color": "#ffffff",
        "artist_color": "#aaaaaa",
        "title_size": 15,
        "artist_size": 12,
    }
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        merged["overlay"].update(cfg.get("overlay", {}))
        return merged
    except Exception as e:
        print(f"[Config] Ошибка загрузки: {e}")
        return DEFAULT_CONFIG


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)