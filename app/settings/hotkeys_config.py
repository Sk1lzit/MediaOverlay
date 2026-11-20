import json
import os
from app.settings.config import get_appdata_dir


HOTKEYS_PATH = os.path.join(get_appdata_dir(), "hotkeys.json")

DEFAULT_HOTKEYS = {
    "toggle_overlay": "ctrl+alt+o",
    "toggle_mixer": "ctrl+alt+m",
    "toggle_settings": "ctrl+alt+s",
    "play_pause": "ctrl+alt+p",
    "next_track": "ctrl+alt+right",
    "prev_track": "ctrl+alt+left",
}


def load_hotkeys():
    if not os.path.exists(HOTKEYS_PATH):
        save_hotkeys(DEFAULT_HOTKEYS)
        return DEFAULT_HOTKEYS.copy()
    try:
        with open(HOTKEYS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_HOTKEYS.copy()
        merged.update(data)
        return merged
    except Exception as e:
        print(f"[Hotkeys] Ошибка загрузки: {e}")
        return DEFAULT_HOTKEYS.copy()


def save_hotkeys(cfg):
    os.makedirs(os.path.dirname(HOTKEYS_PATH), exist_ok=True)
    with open(HOTKEYS_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)