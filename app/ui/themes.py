"""Готовые пресеты тем + загрузка/сохранение кастомной.

ВАЖНО: этот файл НЕ импортирует app.ui.theme — только данные и утилиты.
"""

import json
import os


def get_theme_dir():
    """Тема хранится в %APPDATA%\\MediaOverlay\\."""
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "MediaOverlay")
    os.makedirs(path, exist_ok=True)
    return path


THEME_PATH = os.path.join(get_theme_dir(), "theme.json")


# ===== Пресеты =====

PRESETS = {
    "default": {
        "name": "По умолчанию",
        "bg_top": [15, 23, 42, 240],
        "bg_bottom": [5, 8, 16, 245],
        "panel": [30, 41, 59, 100],
        "panel_border": [148, 163, 184, 40],
        "card": [30, 41, 59, 100],
        "card_border": [148, 163, 184, 20],
        "browser_card": [139, 92, 246, 20],
        "browser_border": [139, 92, 246, 50],
        "accent": [139, 92, 246, 255],
        "accent_hover": [167, 139, 250, 255],
        "accent_dim": [139, 92, 246, 76],
        "text": [226, 232, 240, 255],
        "text_dim": [148, 163, 184, 255],
        "text_muted": [100, 116, 139, 255],
        "border": [148, 163, 184, 38],
        "icon_bg": [139, 92, 246, 76],
        "icon_fg": [167, 139, 250, 255],
    },
    "sunset": {
        "name": "🌆 Закат",
        "bg_top": [45, 20, 15, 245],
        "bg_bottom": [20, 8, 5, 250],
        "panel": [60, 30, 20, 110],
        "panel_border": [255, 140, 90, 50],
        "card": [60, 30, 20, 110],
        "card_border": [255, 140, 90, 30],
        "browser_card": [255, 100, 50, 25],
        "browser_border": [255, 140, 90, 60],
        "accent": [255, 130, 60, 255],
        "accent_hover": [255, 160, 100, 255],
        "accent_dim": [255, 130, 60, 90],
        "text": [255, 235, 220, 255],
        "text_dim": [230, 180, 150, 255],
        "text_muted": [180, 130, 100, 255],
        "border": [255, 140, 90, 50],
        "icon_bg": [255, 130, 60, 90],
        "icon_fg": [255, 200, 160, 255],
    },
    "cyberpunk": {
        "name": "🌃 Киберпанк",
        "bg_top": [10, 5, 25, 245],
        "bg_bottom": [5, 0, 15, 250],
        "panel": [25, 10, 50, 120],
        "panel_border": [255, 0, 200, 60],
        "card": [25, 10, 50, 120],
        "card_border": [0, 255, 255, 40],
        "browser_card": [255, 0, 200, 30],
        "browser_border": [0, 255, 255, 60],
        "accent": [0, 255, 255, 255],
        "accent_hover": [255, 0, 200, 255],
        "accent_dim": [0, 255, 255, 76],
        "text": [240, 240, 255, 255],
        "text_dim": [180, 180, 220, 255],
        "text_muted": [120, 120, 160, 255],
        "border": [255, 0, 200, 50],
        "icon_bg": [255, 255, 0, 90],
        "icon_fg": [255, 255, 0, 255],
    },
    "lagoon": {
        "name": "💜 Фиолетовая лагуна",
        "bg_top": [30, 15, 50, 245],
        "bg_bottom": [10, 5, 25, 250],
        "panel": [45, 25, 70, 110],
        "panel_border": [180, 100, 220, 50],
        "card": [45, 25, 70, 110],
        "card_border": [150, 200, 255, 30],
        "browser_card": [180, 100, 220, 25],
        "browser_border": [150, 200, 255, 60],
        "accent": [200, 100, 255, 255],
        "accent_hover": [150, 200, 255, 255],
        "accent_dim": [200, 100, 255, 80],
        "text": [235, 220, 255, 255],
        "text_dim": [190, 170, 230, 255],
        "text_muted": [140, 120, 180, 255],
        "border": [180, 100, 220, 50],
        "icon_bg": [200, 100, 255, 90],
        "icon_fg": [150, 200, 255, 255],
    },
    "blue_glass": {
        "name": "🔷 Синее стекло",
        "bg_top": [15, 25, 45, 230],
        "bg_bottom": [5, 12, 25, 245],
        "panel": [30, 55, 85, 100],
        "panel_border": [100, 180, 255, 40],
        "card": [30, 55, 85, 100],
        "card_border": [100, 180, 255, 25],
        "browser_card": [60, 130, 220, 25],
        "browser_border": [100, 180, 255, 60],
        "accent": [70, 150, 255, 255],
        "accent_hover": [100, 180, 255, 255],
        "accent_dim": [70, 150, 255, 76],
        "text": [220, 240, 255, 255],
        "text_dim": [150, 190, 220, 255],
        "text_muted": [100, 140, 180, 255],
        "border": [100, 180, 255, 40],
        "icon_bg": [70, 150, 255, 76],
        "icon_fg": [150, 200, 255, 255],
    },
    "glass": {
        "name": "⬜ Стекло",
        "bg_top": [45, 48, 56, 200],
        "bg_bottom": [25, 28, 35, 220],
        "panel": [70, 75, 85, 100],
        "panel_border": [200, 200, 220, 50],
        "card": [70, 75, 85, 100],
        "card_border": [200, 200, 220, 30],
        "browser_card": [140, 140, 160, 25],
        "browser_border": [200, 200, 220, 60],
        "accent": [200, 200, 220, 255],
        "accent_hover": [230, 230, 245, 255],
        "accent_dim": [200, 200, 220, 76],
        "text": [245, 245, 255, 255],
        "text_dim": [200, 200, 215, 255],
        "text_muted": [150, 150, 170, 255],
        "border": [200, 200, 220, 50],
        "icon_bg": [200, 200, 220, 70],
        "icon_fg": [255, 255, 255, 255],
    },
}


# ===== Загрузка / сохранение =====

def load_theme():
    if not os.path.exists(THEME_PATH):
        return PRESETS["default"].copy()
    try:
        with open(THEME_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "preset" in data and data["preset"] in PRESETS:
            theme = PRESETS[data["preset"]].copy()
            theme.update(data.get("overrides", {}))
            return theme
        base = PRESETS["default"].copy()
        base.update(data)
        return base
    except Exception as e:
        print(f"[Theme] Ошибка загрузки: {e}")
        return PRESETS["default"].copy()


def save_theme(preset_name=None, overrides=None, custom=None):
    os.makedirs(os.path.dirname(THEME_PATH), exist_ok=True)
    data = {}
    if preset_name:
        data["preset"] = preset_name
    if overrides:
        data["overrides"] = overrides
    if custom:
        data = custom
    with open(THEME_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def rgba(c, alpha_override=None):
    if isinstance(c, (list, tuple)):
        r, g, b = c[:3]
        a = alpha_override if alpha_override is not None else (c[3] if len(c) > 3 else 255)
        return f"rgba({r}, {g}, {b}, {a / 255:.3f})"
    return str(c)


def hex_color(c):
    if isinstance(c, (list, tuple)):
        return "#{:02x}{:02x}{:02x}".format(c[0], c[1], c[2])
    return str(c)