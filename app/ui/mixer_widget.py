from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QScrollArea, QCheckBox
)
from app.media.mixer import AudioMixer
from app.ui.theme import (
    get_mixer_stylesheet,
    get_bg_gradient_top,
    get_bg_gradient_bottom,
    get_panel_border,
    get_theme,
)
from app.ui.themes import hex_color


class MixerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Микшер громкости")
        self.resize(460, 620)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)

        self.mixer = AudioMixer()
        self._rows = {}
        self._browser_rows = {}
        self._bridge = None
        self._dragging = False
        self._drag_pos = None

        # ⚠️ Контент прямо в self — без card-обёртки
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(14)

        # ===== Хедер =====
        header = QHBoxLayout()

        t = get_theme()
        self.title_label = QLabel("🎚  Микшер громкости")
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

        self.hide_system_check = QCheckBox("Скрыть системные процессы")
        self.hide_system_check.setChecked(True)
        self.hide_system_check.stateChanged.connect(lambda _: self.refresh())
        main_layout.addWidget(self.hide_system_check)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(6)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll, stretch=1)

        self.setStyleSheet(get_mixer_stylesheet())

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(5000)
        self.refresh()

    # ===== Фон по всему окну =====
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Весь прямоугольник окна, с минимальным внутренним зазором для обводки
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

        # Обводка
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

    # ===== Тема =====
    def refresh_theme(self):
        self.setStyleSheet(get_mixer_stylesheet())
        t = get_theme()
        self.title_label.setStyleSheet(
            f"color: {hex_color(t['text'])}; font-size: 18px; font-weight: 600;"
        )

        for row in self._rows.values():
            row["widget"].deleteLater()
        self._rows.clear()

        for row in self._browser_rows.values():
            row["widget"].deleteLater()
        self._browser_rows.clear()

        self.refresh()
        self.update()

    # ===== Логика =====
    def set_browser_bridge(self, bridge):
        self._bridge = bridge
        bridge.tabs_updated.connect(
            self._on_browser_tabs,
            Qt.ConnectionType.QueuedConnection,
        )

    def _tick(self):
        if self.isVisible():
            self.refresh()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def refresh(self):
        try:
            hide_sys = self.hide_system_check.isChecked()
            sessions = self.mixer.get_sessions(hide_system=hide_sys)
        except Exception as e:
            print(f"[Mixer] Ошибка refresh: {e}")
            return

        current_pids = {s["pid"] for s in sessions}

        for pid in list(self._rows.keys()):
            if pid not in current_pids:
                row = self._rows.pop(pid)
                row["widget"].deleteLater()

        for s in sessions:
            pid = s["pid"]
            if pid in self._rows:
                row = self._rows[pid]
                row["session"] = s["session"]
                current_val = int(s["volume"] * 100)
                if abs(row["slider"].value() - current_val) > 2:
                    row["slider"].blockSignals(True)
                    row["slider"].setValue(current_val)
                    row["slider"].blockSignals(False)
                continue

            row_widget = self._create_row(s)
            self.container_layout.addWidget(row_widget)

    def _create_row(self, session_data):
        pid = session_data["pid"]
        name = session_data["name"]

        widget = QWidget()
        widget.setObjectName("appRow")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        icon_label = QLabel("🎵")
        icon_label.setObjectName("appIcon")
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        t = get_theme()
        label = QLabel(self._pretty_name(name))
        label.setFixedWidth(120)
        label.setStyleSheet(
            f"color: {hex_color(t['text'])}; font-size: 13px; font-weight: 500;"
        )
        layout.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(int(session_data["volume"] * 100))
        slider.valueChanged.connect(
            lambda v, p=pid: self._on_volume_change(p, v)
        )
        layout.addWidget(slider, stretch=1)

        mute_btn = QPushButton("🔊" if not session_data["muted"] else "🔇")
        mute_btn.setFixedSize(36, 36)
        mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mute_btn.clicked.connect(lambda _, p=pid: self._toggle_mute(p))
        layout.addWidget(mute_btn)

        self._rows[pid] = {
            "widget": widget,
            "slider": slider,
            "mute": mute_btn,
            "session": session_data["session"],
            "muted": session_data["muted"],
        }

        return widget

    @staticmethod
    def _pretty_name(name):
        base = name.replace(".exe", "")
        return base[:1].upper() + base[1:]

    def _on_volume_change(self, pid, value):
        row = self._rows.get(pid)
        if not row:
            return
        self.mixer.set_volume(row["session"], value / 100.0)

    def _toggle_mute(self, pid):
        row = self._rows.get(pid)
        if not row:
            return
        new_muted = not row["muted"]
        self.mixer.set_mute(row["session"], new_muted)
        row["muted"] = new_muted
        row["mute"].setText("🔇" if new_muted else "🔊")

    def _on_browser_tabs(self, tabs):
        active = [t for t in tabs if t.get("media_count", 0) > 0]
        current_ids = {t["id"] for t in active}

        for tab_id in list(self._browser_rows.keys()):
            if tab_id not in current_ids:
                row = self._browser_rows.pop(tab_id)
                row["widget"].deleteLater()

        for t in active:
            tab_id = t["id"]
            if tab_id in self._browser_rows:
                row = self._browser_rows[tab_id]
                current_val = int(t.get("volume", 1.0) * 100)
                if abs(row["slider"].value() - current_val) > 2:
                    row["slider"].blockSignals(True)
                    row["slider"].setValue(current_val)
                    row["slider"].blockSignals(False)
                row["muted"] = t.get("muted", False)
                row["mute"].setText("🔇" if row["muted"] else "🔊")
                row["label"].setText(self._short_title(t.get("title", "Вкладка")))
                continue

            row_widget = self._create_browser_row(t)
            self.container_layout.addWidget(row_widget)

    @staticmethod
    def _short_title(title):
        if not title:
            return "Вкладка"
        title = title.strip()
        return title[:26] + ("…" if len(title) > 26 else "")

    def _create_browser_row(self, tab):
        tab_id = tab["id"]

        widget = QWidget()
        widget.setObjectName("browserRow")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        icon = QLabel("🌐")
        icon.setObjectName("browserIcon")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        t = get_theme()
        label = QLabel(self._short_title(tab.get("title", "Вкладка")))
        label.setFixedWidth(120)
        label.setStyleSheet(
            f"color: {hex_color(t['text'])}; font-size: 13px; font-weight: 500;"
        )
        label.setToolTip(tab.get("url", ""))
        layout.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(int(tab.get("volume", 1.0) * 100))
        slider.valueChanged.connect(
            lambda v, t_id=tab_id: self._on_browser_volume(t_id, v)
        )
        layout.addWidget(slider, stretch=1)

        mute_btn = QPushButton("🔇" if tab.get("muted") else "🔊")
        mute_btn.setFixedSize(36, 36)
        mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mute_btn.clicked.connect(lambda _, t_id=tab_id: self._toggle_browser_mute(t_id))
        layout.addWidget(mute_btn)

        self._browser_rows[tab_id] = {
            "widget": widget,
            "slider": slider,
            "mute": mute_btn,
            "label": label,
            "muted": tab.get("muted", False),
        }

        return widget

    def _on_browser_volume(self, tab_id, value):
        if self._bridge:
            self._bridge.send_command(
                "set_volume",
                tab_id=tab_id,
                payload={"volume": value / 100.0},
            )

    def _toggle_browser_mute(self, tab_id):
        row = self._browser_rows.get(tab_id)
        if not row:
            return
        new_muted = not row["muted"]
        row["muted"] = new_muted
        row["mute"].setText("🔇" if new_muted else "🔊")
        if self._bridge:
            self._bridge.send_command(
                "set_mute",
                tab_id=tab_id,
                payload={"muted": new_muted},
            )