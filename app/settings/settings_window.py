from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QSlider, QColorDialog, QFileDialog, QComboBox, QLineEdit,
    QScrollArea, QGridLayout
)
from app.settings.config import load_config, save_config
from app.settings.hotkeys_tab import HotkeysTab
from app.ui.theme import (
    get_mixer_stylesheet,
    get_bg_gradient_top,
    get_bg_gradient_bottom,
    get_panel_border,
    get_theme,
    reload_theme,
)
from app.ui.themes import (
    PRESETS, load_theme, save_theme, rgba, hex_color
)


class SettingsWindow(QWidget):
    def __init__(self, overlay, hotkeys_manager=None, on_theme_change=None):
        super().__init__()
        self.overlay = overlay
        self.hotkeys_manager = hotkeys_manager
        self.on_theme_change = on_theme_change
        self.cfg = load_config()

        self.setWindowTitle("Настройки")
        self.resize(560, 820)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)

        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._autosave)

        self._dragging = False
        self._drag_pos = None

        # ⚠️ Контент прямо в self
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(14)

        # ===== Хедер =====
        header = QHBoxLayout()
        t = get_theme()
        self.title_label = QLabel("⚙  Настройки")
        self.title_label.setStyleSheet(
            f"color: {hex_color(t['text'])}; font-size: 18px; font-weight: 600;"
        )
        header.addWidget(self.title_label)
        header.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.hide)
        header.addWidget(self.btn_close)

        main_layout.addLayout(header)

        # ===== Табы =====
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tabs.addTab(self._create_overlay_tab(), "🎨 Оверлей")
        hotkeys_tab = HotkeysTab(on_save=self._reload_hotkeys)
        self.tabs.addTab(hotkeys_tab, "⌨ Хоткеи")
        self.tabs.addTab(self._create_theme_tab(), "🌈 Тема")

        main_layout.addWidget(self.tabs, stretch=1)

        self.setStyleSheet(get_mixer_stylesheet())

    # ===== Overlay tab =====
    def _create_overlay_tab(self):
        overlay_tab = QWidget()
        layout = QVBoxLayout(overlay_tab)
        layout.setSpacing(8)

        layout.addWidget(self._label("Размер"))
        layout.addWidget(QLabel("Ширина"))
        self.width_slider = self._slider(200, 800, self.cfg["overlay"]["width"])
        self.width_slider.valueChanged.connect(lambda v: self._live("width", v))
        layout.addWidget(self.width_slider)

        layout.addWidget(QLabel("Высота"))
        self.height_slider = self._slider(150, 500, self.cfg["overlay"]["height"])
        self.height_slider.valueChanged.connect(lambda v: self._live("height", v))
        layout.addWidget(self.height_slider)

        layout.addWidget(self._label("Позиция"))
        self.position_combo = QComboBox()
        self.position_combo.addItems([
            "bottom-right", "bottom-left", "top-right", "top-left"
        ])
        self.position_combo.setCurrentText(self.cfg["overlay"]["position"])
        self.position_combo.currentTextChanged.connect(
            lambda v: self._live("position", v)
        )
        layout.addWidget(self.position_combo)

        layout.addWidget(self._label("Фон"))
        self.bg_image_path = QLineEdit(self.cfg["overlay"].get("bg_image") or "")
        self.bg_image_path.setReadOnly(True)
        layout.addWidget(self.bg_image_path)

        bg_btn = QPushButton("Выбрать фон (png/jpg/gif/mp4/webm)")
        bg_btn.clicked.connect(self._pick_bg_image)
        layout.addWidget(bg_btn)

        clear_bg = QPushButton("Убрать фон")
        clear_bg.clicked.connect(self._clear_bg)
        layout.addWidget(clear_bg)

        layout.addWidget(self._label("Цвета"))
        self.bg_color_btn = QPushButton("Цвет фона")
        self.bg_color_btn.clicked.connect(self._pick_bg_color)
        layout.addWidget(self.bg_color_btn)

        layout.addWidget(self._label("Обводка"))
        self.border_mode_combo = QComboBox()
        self.border_mode_combo.addItems(["solid", "rgb_cycle", "gradient"])
        self.border_mode_combo.setCurrentText(
            self.cfg["overlay"].get("border_mode", "solid")
        )
        self.border_mode_combo.currentTextChanged.connect(
            lambda v: self._live("border_mode", v)
        )
        layout.addWidget(self.border_mode_combo)

        self.color1_btn = QPushButton("🎨 Цвет 1 (для gradient)")
        self.color1_btn.clicked.connect(self._pick_color1)
        layout.addWidget(self.color1_btn)

        self.color2_btn = QPushButton("🎨 Цвет 2 (для gradient)")
        self.color2_btn.clicked.connect(self._pick_color2)
        layout.addWidget(self.color2_btn)

        swap_btn = QPushButton("⇄ Поменять цвета")
        swap_btn.clicked.connect(self._swap_colors)
        layout.addWidget(swap_btn)

        self.border_color_btn = QPushButton("Цвет обводки (для solid)")
        self.border_color_btn.clicked.connect(self._pick_border_color)
        layout.addWidget(self.border_color_btn)

        layout.addWidget(QLabel("Скорость анимации"))
        self.rgb_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.rgb_speed_slider.setRange(1, 50)
        self.rgb_speed_slider.setValue(
            int(self.cfg["overlay"].get("border_rgb_speed", 1.0) * 10)
        )
        self.rgb_speed_slider.valueChanged.connect(
            lambda v: self._live("border_rgb_speed", v / 10.0)
        )
        layout.addWidget(self.rgb_speed_slider)

        layout.addWidget(QLabel("Толщина обводки"))
        self.border_width_slider = self._slider(
            0, 10, self.cfg["overlay"]["border_width"]
        )
        self.border_width_slider.valueChanged.connect(
            lambda v: self._live("border_width", v)
        )
        layout.addWidget(self.border_width_slider)

        layout.addWidget(QLabel("Скругление"))
        self.radius_slider = self._slider(
            0, 40, self.cfg["overlay"]["border_radius"]
        )
        self.radius_slider.valueChanged.connect(
            lambda v: self._live("border_radius", v)
        )
        layout.addWidget(self.radius_slider)

        layout.addWidget(QLabel("Прозрачность картинки"))
        self.opacity_slider = self._slider(
            0, 100, int(self.cfg["overlay"]["bg_image_opacity"] * 100)
        )
        self.opacity_slider.valueChanged.connect(
            lambda v: self._live("bg_image_opacity", v / 100.0)
        )
        layout.addWidget(self.opacity_slider)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(overlay_tab)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        return scroll

    # ===== Theme tab =====
    def _create_theme_tab(self):
        theme_tab = QWidget()
        layout = QVBoxLayout(theme_tab)
        layout.setSpacing(12)

        layout.addWidget(self._label("Пресеты"))

        grid = QGridLayout()
        grid.setSpacing(8)

        self.preset_buttons = {}
        keys = list(PRESETS.keys())
        for i, key in enumerate(keys):
            btn = QPushButton(PRESETS[key]["name"])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda _, k=key: self._apply_preset(k))
            grid.addWidget(btn, i // 2, i % 2)
            self.preset_buttons[key] = btn

        layout.addLayout(grid)

        layout.addWidget(self._label("Кастомизация"))

        self.custom_bg_btn = QPushButton("🎨 Цвет фона окна")
        self.custom_bg_btn.clicked.connect(self._pick_custom_bg)
        layout.addWidget(self.custom_bg_btn)

        self.custom_accent_btn = QPushButton("🎨 Акцент (кнопки, слайдеры)")
        self.custom_accent_btn.clicked.connect(self._pick_custom_accent)
        layout.addWidget(self.custom_accent_btn)

        self.custom_text_btn = QPushButton("🎨 Цвет текста")
        self.custom_text_btn.clicked.connect(self._pick_custom_text)
        layout.addWidget(self.custom_text_btn)

        reset_btn = QPushButton("↺ Сбросить к пресету")
        reset_btn.clicked.connect(self._reset_to_preset)
        layout.addWidget(reset_btn)

        hint = QLabel(
            "💡 Изменения применяются сразу и сохраняются автоматически"
        )
        hint.setStyleSheet(
            f"color: {hex_color(get_theme()['text_muted'])}; font-size: 11px;"
        )
        layout.addWidget(hint)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(theme_tab)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        return scroll

    def _apply_preset(self, key):
        save_theme(preset_name=key, overrides={})
        reload_theme()
        self._refresh_all_themes()

    def _pick_custom_bg(self):
        theme = get_theme()
        current = QColor(*theme["bg_top"])
        color = QColorDialog.getColor(current, self, "Цвет фона окна")
        if color.isValid():
            overrides = self._get_current_overrides()
            overrides["bg_top"] = [color.red(), color.green(), color.blue(), 240]
            overrides["bg_bottom"] = [
                color.red() // 2, color.green() // 2, color.blue() // 2, 250
            ]
            save_theme(preset_name=self._current_preset(), overrides=overrides)
            reload_theme()
            self._refresh_all_themes()

    def _pick_custom_accent(self):
        theme = get_theme()
        current = QColor(*theme["accent"])
        color = QColorDialog.getColor(current, self, "Акцент")
        if color.isValid():
            overrides = self._get_current_overrides()
            r, g, b = color.red(), color.green(), color.blue()
            overrides["accent"] = [r, g, b, 255]
            overrides["accent_hover"] = [
                min(255, r + 30), min(255, g + 30), min(255, b + 30), 255
            ]
            overrides["accent_dim"] = [r, g, b, 80]
            overrides["icon_bg"] = [r, g, b, 90]
            overrides["icon_fg"] = [
                min(255, r + 40), min(255, g + 40), min(255, b + 40), 255
            ]
            save_theme(preset_name=self._current_preset(), overrides=overrides)
            reload_theme()
            self._refresh_all_themes()

    def _pick_custom_text(self):
        theme = get_theme()
        current = QColor(*theme["text"])
        color = QColorDialog.getColor(current, self, "Цвет текста")
        if color.isValid():
            overrides = self._get_current_overrides()
            overrides["text"] = [color.red(), color.green(), color.blue(), 255]
            save_theme(preset_name=self._current_preset(), overrides=overrides)
            reload_theme()
            self._refresh_all_themes()

    def _current_preset(self):
        import json
        import os
        from app.ui.themes import THEME_PATH
        if not os.path.exists(THEME_PATH):
            return "default"
        try:
            with open(THEME_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("preset", "default")
        except Exception:
            return "default"

    def _get_current_overrides(self):
        import json
        import os
        from app.ui.themes import THEME_PATH
        if not os.path.exists(THEME_PATH):
            return {}
        try:
            with open(THEME_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("overrides", {})
        except Exception:
            return {}

    def _reset_to_preset(self):
        current = self._current_preset()
        save_theme(preset_name=current, overrides={})
        reload_theme()
        self._refresh_all_themes()

    def _refresh_all_themes(self):
        self.setStyleSheet(get_mixer_stylesheet())
        t = get_theme()
        self.title_label.setStyleSheet(
            f"color: {hex_color(t['text'])}; font-size: 18px; font-weight: 600;"
        )
        self.update()

        if self.on_theme_change:
            self.on_theme_change()

    # ===== Фон по всему окну =====
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = 20

        top = get_bg_gradient_top()
        bottom = get_bg_gradient_bottom()

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(*top))
        grad.setColorAt(1.0, QColor(*bottom))

        path = QPainterPath()
        path.addRoundedRect(rect.toRectF(), radius, radius)
        painter.fillPath(path, grad)

        painter.setPen(QColor(*get_panel_border()))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)

    # ===== Перетаскивание =====
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    # ===== Helpers =====
    def _reload_hotkeys(self):
        if self.hotkeys_manager:
            self.hotkeys_manager.reload()

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {hex_color(get_theme()['text_dim'])}; font-size: 12px;"
            f"font-weight: 600; margin-top: 10px;"
        )
        return lbl

    def _slider(self, min_v, max_v, value):
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(min_v, max_v)
        s.setValue(value)
        return s

    def _live(self, key, value):
        self.cfg["overlay"][key] = value
        self.overlay.apply_live(key, value)
        self._save_timer.start(500)

    def _autosave(self):
        save_config(self.cfg)

    def _pick_bg_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбери фон", "",
            "Images & Videos (*.png *.jpg *.jpeg *.gif *.mp4 *.webm *.mkv *.mov)"
        )
        if path:
            self.cfg["overlay"]["bg_image"] = path
            self.bg_image_path.setText(path)
            self.overlay.apply_live("bg_image", path)
            self._save_timer.start(500)

    def _clear_bg(self):
        self.cfg["overlay"]["bg_image"] = None
        self.bg_image_path.setText("")
        self.overlay.apply_live("bg_image", None)
        self._save_timer.start(500)

    def _pick_bg_color(self):
        current = QColor(*self.cfg["overlay"]["bg_color"])
        color = QColorDialog.getColor(current, self, "Цвет фона")
        if color.isValid():
            value = [color.red(), color.green(), color.blue(), color.alpha()]
            self.cfg["overlay"]["bg_color"] = value
            self.overlay.apply_live("bg_color", value)
            self._save_timer.start(500)

    def _pick_border_color(self):
        current = QColor(*self.cfg["overlay"]["border_color"])
        color = QColorDialog.getColor(current, self, "Цвет обводки")
        if color.isValid():
            value = [color.red(), color.green(), color.blue(), color.alpha()]
            self.cfg["overlay"]["border_color"] = value
            self.overlay.apply_live("border_color", value)
            self._save_timer.start(500)

    def _pick_color1(self):
        current = QColor(*self.cfg["overlay"].get(
            "border_color_1", [139, 92, 246, 255]
        ))
        color = QColorDialog.getColor(current, self, "Цвет 1")
        if color.isValid():
            value = [color.red(), color.green(), color.blue(), color.alpha()]
            self.cfg["overlay"]["border_color_1"] = value
            self.overlay.apply_live("border_color_1", value)
            self._save_timer.start(500)

    def _pick_color2(self):
        current = QColor(*self.cfg["overlay"].get(
            "border_color_2", [239, 68, 68, 255]
        ))
        color = QColorDialog.getColor(current, self, "Цвет 2")
        if color.isValid():
            value = [color.red(), color.green(), color.blue(), color.alpha()]
            self.cfg["overlay"]["border_color_2"] = value
            self.overlay.apply_live("border_color_2", value)
            self._save_timer.start(500)

    def _swap_colors(self):
        c1 = self.cfg["overlay"].get("border_color_1", [139, 92, 246, 255])
        c2 = self.cfg["overlay"].get("border_color_2", [239, 68, 68, 255])
        self.cfg["overlay"]["border_color_1"] = c2
        self.cfg["overlay"]["border_color_2"] = c1
        self.overlay.apply_live("border_color_1", c2)
        self.overlay.apply_live("border_color_2", c1)
        self._save_timer.start(500)