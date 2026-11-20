"""Динамическая тема — берётся из themes.load_theme()."""
from app.ui.themes import load_theme, rgba, hex_color


_current_theme = None


def get_theme():
    global _current_theme
    if _current_theme is None:
        _current_theme = load_theme()
    return _current_theme


def reload_theme():
    global _current_theme
    _current_theme = load_theme()
    return _current_theme


def apply_theme(theme_dict):
    global _current_theme
    _current_theme = theme_dict


def get_mixer_stylesheet():
    t = get_theme()

    accent = hex_color(t["accent"])
    accent_hover = hex_color(t["accent_hover"])
    accent_dim = rgba(t["accent_dim"])
    text = hex_color(t["text"])
    text_dim = hex_color(t["text_dim"])
    text_muted = hex_color(t["text_muted"])
    border = rgba(t["border"])
    card = rgba(t["card"])
    card_border = rgba(t["card_border"])
    input_bg = rgba(t["panel"])

    return f"""
        QWidget {{
            background: transparent;
            color: {text};
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }}
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}

        QLabel {{
            background: transparent;
        }}

        /* Слайдеры */
        QSlider::groove:horizontal {{
            height: 6px;
            background: {card};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {accent};
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }}
        QSlider::handle:horizontal:hover {{
            background: {accent_hover};
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent}, stop:1 {accent_hover}
            );
            border-radius: 3px;
        }}

        /* Кнопки */
        QPushButton {{
            background: {card};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background: {accent_dim};
            border: 1px solid {accent};
        }}
        QPushButton:pressed {{
            background: {accent_dim};
        }}

        /* Чекбокс */
        QCheckBox {{
            spacing: 8px;
            color: {text_dim};
            font-size: 12px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid {border};
            background: {card};
        }}
        QCheckBox::indicator:checked {{
            background: {accent};
            border: 1px solid {accent};
        }}

        /* Скроллбар */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {card};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {accent_dim};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}

        /* Вкладки */
        QTabWidget::pane {{
            border: none;
            background: transparent;
        }}
        QTabBar::tab {{
            background: transparent;
            color: {text_muted};
            padding: 10px 18px;
            margin-right: 4px;
            border: none;
            border-radius: 8px;
            font-size: 13px;
        }}
        QTabBar::tab:hover {{
            background: {card};
            color: {text_dim};
        }}
        QTabBar::tab:selected {{
            background: {accent_dim};
            color: {text};
        }}

        /* Input */
        QLineEdit {{
            background: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {accent};
        }}

        QComboBox {{
            background: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 8px 12px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background: #0f172a;
            color: {text};
            selection-background-color: {accent};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 4px;
        }}

        /* Карточки приложений */
        QWidget#appRow {{
            background: {card};
            border-radius: 12px;
            border: 1px solid {card_border};
        }}

        QWidget#browserRow {{
            background: {rgba(t['browser_card'])};
            border-radius: 12px;
            border: 1px solid {rgba(t['browser_border'])};
        }}

        QLabel#appIcon {{
            background: {rgba(t['icon_bg'])};
            color: {hex_color(t['icon_fg'])};
            border-radius: 10px;
            font-size: 18px;
        }}

        QLabel#browserIcon {{
            background: {rgba(t['icon_bg'])};
            color: {hex_color(t['icon_fg'])};
            border-radius: 10px;
            font-size: 16px;
        }}
    """


def get_bg_gradient_top():
    return get_theme()["bg_top"]


def get_bg_gradient_bottom():
    return get_theme()["bg_bottom"]


def get_panel_border():
    return get_theme()["panel_border"]