import os
import colorsys
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QPixmap, QMovie,
    QPen, QConicalGradient
)
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar,
    QPushButton, QMenu, QSlider
)
from app.media.smtc import SMTCListener, play_pause, next_track, prev_track
from app.media.video_bg import VideoBackground
from app.settings.config import load_config


class Overlay(QWidget):
    def __init__(self, on_open_settings=None, on_open_mixer=None, on_exit=None,
                 browser_bridge=None):
        super().__init__()
        self.on_open_settings = on_open_settings
        self.on_open_mixer = on_open_mixer
        self.on_exit = on_exit
        self.browser_bridge = browser_bridge
        self._browser_tab_id = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.cfg = load_config()["overlay"]
        self._bg_pixmap = None
        self._bg_movie = None
        self._video_bg = None
        self._video_frame = None
        self._is_playing = False

        self._rgb_phase = 0.0
        self._rgb_timer = QTimer()
        self._rgb_timer.timeout.connect(self._rgb_tick)

        self.resize(self.cfg["width"], self.cfg["height"])
        self._position_overlay()

        # ===== UI =====
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(8)

        top_layout = QHBoxLayout()

        self.cover = QLabel()
        self.cover.setFixedSize(64, 64)
        self.cover.setStyleSheet(
            "background: rgba(42,42,58,180); border-radius: 8px; color: #888;"
            "font-size: 24px; qproperty-alignment: AlignCenter;"
        )
        self.cover.setText("🎵")
        top_layout.addWidget(self.cover)

        text_layout = QVBoxLayout()
        self.title = QLabel("Сейчас ничего не играет")
        self.title.setWordWrap(True)

        self.artist = QLabel("—")
        text_layout.addWidget(self.title)
        text_layout.addWidget(self.artist)
        top_layout.addLayout(text_layout, stretch=1)

        self.btn_menu = QPushButton("⚙")
        self.btn_menu.setFixedSize(28, 28)
        self.btn_menu.setStyleSheet("""
            QPushButton {
                background: rgba(42,42,58,150);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(139,92,246,180);
            }
        """)
        self.btn_menu.clicked.connect(self._show_menu)
        top_layout.addWidget(self.btn_menu, alignment=Qt.AlignmentFlag.AlignTop)

        main_layout.addLayout(top_layout)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(
            "QProgressBar { background: rgba(42,42,58,180); border: none; border-radius: 2px; }"
            "QProgressBar::chunk { background: #8b5cf6; border-radius: 2px; }"
        )
        main_layout.addWidget(self.progress)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #888; font-size: 10px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.time_label)

        controls = QHBoxLayout()
        controls.setSpacing(12)
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_style = """
            QPushButton {
                background: rgba(42,42,58,150);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(139,92,246,180);
            }
        """

        self.btn_prev = QPushButton("⏮")
        self.btn_prev.setFixedSize(32, 32)
        self.btn_prev.setStyleSheet(btn_style)
        self.btn_prev.clicked.connect(self._on_prev)
        controls.addWidget(self.btn_prev)

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setStyleSheet(btn_style)
        self.btn_play.clicked.connect(self._on_play_pause)
        controls.addWidget(self.btn_play)

        self.btn_next = QPushButton("⏭")
        self.btn_next.setFixedSize(32, 32)
        self.btn_next.setStyleSheet(btn_style)
        self.btn_next.clicked.connect(self._on_next)
        controls.addWidget(self.btn_next)

        main_layout.addLayout(controls)

        vol_layout = QHBoxLayout()
        vol_layout.setSpacing(8)

        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet("color: #aaa; font-size: 14px;")
        vol_layout.addWidget(vol_icon)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px; background: rgba(42,42,58,180); border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #8b5cf6; width: 12px; margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #8b5cf6; border-radius: 2px;
            }
        """)
        vol_layout.addWidget(self.volume_slider, stretch=1)

        main_layout.addLayout(vol_layout)

        self._init_volume_slider()
        self.volume_slider.valueChanged.connect(self._on_volume_change)

        self._visible = True
        self._apply_text_styles()
        self._load_bg()

        self.smtc = SMTCListener(on_update=self._on_media_update)
        self.smtc.start()

        if self.browser_bridge:
            self.browser_bridge.tabs_updated.connect(
                self._on_browser_tabs,
                Qt.ConnectionType.QueuedConnection,
            )

    def showEvent(self, event):
        super().showEvent(event)
        if not self._rgb_timer.isActive():
            self._rgb_timer.start(50)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._rgb_timer.isActive():
            self._rgb_timer.stop()

    def _init_volume_slider(self):
        try:
            import pythoncom
            from pycaw.pycaw import AudioUtilities
            pythoncom.CoInitialize()
            try:
                device = AudioUtilities.GetSpeakers()
                volume = device.EndpointVolume
                current = volume.GetMasterVolumeLevelScalar()
                self.volume_slider.blockSignals(True)
                self.volume_slider.setValue(int(current * 100))
                self.volume_slider.blockSignals(False)
            finally:
                pythoncom.CoUninitialize()
        except Exception:
            pass

    def _on_volume_change(self, value):
        try:
            import pythoncom
            from pycaw.pycaw import AudioUtilities
            pythoncom.CoInitialize()
            try:
                device = AudioUtilities.GetSpeakers()
                volume = device.EndpointVolume
                volume.SetMasterVolumeLevelScalar(value / 100.0, None)
            finally:
                pythoncom.CoUninitialize()
        except Exception as e:
            print(f"[Overlay] Ошибка громкости: {e}")

    def _on_browser_tabs(self, tabs):
        active = [t for t in tabs if t.get("media_count", 0) > 0]
        if not active:
            self._browser_tab_id = None
            return

        playing = [t for t in active if t.get("playing")]

        if playing:
            chosen = max(
                playing,
                key=lambda t: (t.get("track") or {}).get("currentTime", 0),
            )
        else:
            if self._browser_tab_id:
                still_alive = next(
                    (t for t in active if t["id"] == self._browser_tab_id),
                    None,
                )
                chosen = still_alive or active[0]
            else:
                chosen = active[0]

        self._browser_tab_id = chosen["id"]
        self._update_from_browser(chosen)

    def _update_from_browser(self, tab):
        self.title.setText(tab.get("title", "—")[:60])
        self.artist.setText("🌐 Opera GX")
        track = tab.get("track") or {}
        dur = track.get("duration", 0)
        cur = track.get("currentTime", 0)
        if dur > 0:
            self.progress.setValue(int((cur / dur) * 100))
            self.time_label.setText(f"{self._fmt(cur)} / {self._fmt(dur)}")
        self.btn_play.setText("⏸" if not track.get("paused", True) else "▶")

    def _rgb_tick(self):
        mode = self.cfg.get("border_mode", "solid")
        if mode == "solid":
            return
        if not self.isVisible():
            return
        speed = float(self.cfg.get("border_rgb_speed", 1.0))
        self._rgb_phase = (self._rgb_phase + 0.015 * speed) % 1.0
        self.update()

    def _get_border_colors(self):
        mode = self.cfg.get("border_mode", "solid")
        if mode == "solid":
            return [QColor(*self.cfg["border_color"])]
        if mode == "rgb_cycle":
            h = self._rgb_phase
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            return [QColor(int(r * 255), int(g * 255), int(b * 255))]
        if mode == "gradient":
            c1 = QColor(*self.cfg.get("border_color_1", [139, 92, 246, 255]))
            c2 = QColor(*self.cfg.get("border_color_2", [239, 68, 68, 255]))
            return [c1, c2]
        return [QColor(*self.cfg["border_color"])]

    def _draw_border(self, painter, rect, radius):
        mode = self.cfg.get("border_mode", "solid")
        width = self.cfg["border_width"]
        if width <= 0:
            return
        colors = self._get_border_colors()
        if mode == "solid" or len(colors) == 1:
            pen = QPen(colors[0])
            pen.setWidth(width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)
        elif mode in ("gradient", "rgb_gradient") and len(colors) == 2:
            speed = float(self.cfg.get("border_rgb_speed", 1.0))
            angle = self._rgb_phase * 360 * speed
            grad = QConicalGradient(rect.center(), angle)
            grad.setColorAt(0.0, colors[0])
            grad.setColorAt(0.5, colors[1])
            grad.setColorAt(1.0, colors[0])
            pen = QPen()
            pen.setBrush(grad)
            pen.setWidth(width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

    def _apply_text_styles(self):
        self.title.setStyleSheet(
            f"color: {self.cfg['title_color']}; "
            f"font-size: {self.cfg['title_size']}px; font-weight: bold;"
        )
        self.artist.setStyleSheet(
            f"color: {self.cfg['artist_color']}; "
            f"font-size: {self.cfg['artist_size']}px;"
        )

    def _show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #1a1a2e; color: white;
                border: 1px solid #8b5cf6; border-radius: 8px; padding: 6px;
            }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #8b5cf6; }
        """)
        if self.on_open_settings:
            menu.addAction("⚙ Настройки", self.on_open_settings)
        if self.on_open_mixer:
            menu.addAction("🎚 Микшер", self.on_open_mixer)
        menu.addSeparator()
        if self.on_exit:
            menu.addAction("❌ Выход", self.on_exit)
        pos = self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft())
        menu.exec(pos)

    def _load_bg(self):
        self._cleanup_bg()
        path = self.cfg.get("bg_image")
        if not path or not os.path.exists(path):
            return
        ext = os.path.splitext(path)[1].lower()
        if ext in (".mp4", ".webm", ".mkv", ".avi", ".mov"):
            self._video_bg = VideoBackground(on_frame=self._on_video_frame)
            if not self._video_bg.load(path):
                self._video_bg = None
        elif ext == ".gif":
            self._bg_movie = QMovie(path)
            self._bg_movie.frameChanged.connect(self.update)
            self._bg_movie.start()
        else:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._bg_pixmap = pixmap

    def _on_video_frame(self, pixmap):
        if not self.isVisible():
            return
        self._video_frame = pixmap
        self.update()

    def _cleanup_bg(self):
        if self._video_bg:
            self._video_bg.stop()
            self._video_bg = None
        if self._bg_movie:
            self._bg_movie.stop()
            self._bg_movie = None
        self._video_frame = None

    def _position_overlay(self):
        screen = self.screen().availableGeometry()
        pos = self.cfg.get("position", "bottom-right")
        margin = 20
        if pos == "bottom-right":
            x = screen.width() - self.width() - margin
            y = screen.height() - self.height() - margin
        elif pos == "bottom-left":
            x, y = margin, screen.height() - self.height() - margin
        elif pos == "top-right":
            x, y = screen.width() - self.width() - margin, margin
        else:
            x, y = margin, margin
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
            radius = self.cfg["border_radius"]
            clip = QPainterPath()
            clip.addRoundedRect(rect, radius, radius)
            painter.setClipPath(clip)

            if self._video_frame is not None:
                painter.setOpacity(self.cfg["bg_image_opacity"])
                painter.drawPixmap(rect.toRect(), self._video_frame)
                painter.setOpacity(1.0)
                painter.fillRect(rect, QColor(10, 10, 20, 110))
            elif self._bg_movie is not None:
                painter.setOpacity(self.cfg["bg_image_opacity"])
                painter.drawPixmap(rect.toRect(), self._bg_movie.currentPixmap())
                painter.setOpacity(1.0)
            elif self._bg_pixmap is not None:
                painter.setOpacity(self.cfg["bg_image_opacity"])
                painter.drawPixmap(rect.toRect(), self._bg_pixmap)
                painter.setOpacity(1.0)
            else:
                painter.fillRect(rect, QColor(*self.cfg["bg_color"]))

            painter.setClipping(False)
            self._draw_border(painter, rect, radius)
        finally:
            painter.end()

    def _on_media_update(self, data):
        if self._browser_tab_id:
            return

        if data is None:
            self.title.setText("Сейчас ничего не играет")
            self.artist.setText("—")
            self.progress.setValue(0)
            self.time_label.setText("0:00 / 0:00")
            self.cover.setPixmap(QPixmap())
            self.cover.setText("🎵")
            self.btn_play.setText("▶")
            return

        self.title.setText(data["title"])
        self.artist.setText(data["artist"])

        duration = data["duration"]
        position = data["position"]
        if duration > 0:
            self.progress.setValue(int((position / duration) * 100))
        else:
            self.progress.setValue(0)

        self.time_label.setText(f"{self._fmt(position)} / {self._fmt(duration)}")

        if data["thumbnail"]:
            pixmap = QPixmap()
            pixmap.loadFromData(data["thumbnail"])
            self.cover.setPixmap(
                pixmap.scaled(
                    64, 64,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.cover.setText("")
        else:
            self.cover.setPixmap(QPixmap())
            self.cover.setText("🎵")

        self._is_playing = data.get("is_playing", False)
        self.btn_play.setText("⏸" if self._is_playing else "▶")

    @staticmethod
    def _fmt(seconds):
        seconds = int(seconds)
        return f"{seconds // 60}:{seconds % 60:02d}"

    def _on_play_pause(self):
        if self._browser_tab_id and self.browser_bridge:
            self.browser_bridge.send_command("play_pause", tab_id=self._browser_tab_id)
        else:
            play_pause()

    def _on_next(self):
        if self._browser_tab_id and self.browser_bridge:
            self.browser_bridge.send_command("next", tab_id=self._browser_tab_id)
        else:
            next_track()

    def _on_prev(self):
        if self._browser_tab_id and self.browser_bridge:
            self.browser_bridge.send_command("prev", tab_id=self._browser_tab_id)
        else:
            prev_track()

    def apply_live(self, key, value):
        self.cfg[key] = value
        if key in ("width", "height"):
            self.resize(int(self.cfg["width"]), int(self.cfg["height"]))
            self._position_overlay()
        elif key == "position":
            self._position_overlay()
        elif key in ("title_color", "title_size", "artist_color", "artist_size"):
            self._apply_text_styles()
        elif key == "bg_image":
            self._bg_pixmap = None
            self._load_bg()
        self.update()

    def reload_config(self):
        self.cfg = load_config()["overlay"]
        self.resize(self.cfg["width"], self.cfg["height"])
        self._position_overlay()
        self._apply_text_styles()
        self._bg_pixmap = None
        self._load_bg()
        self.update()

    def shutdown(self):
        """Останавливает все фоновые процессы оверлея."""
        try:
            if self._rgb_timer.isActive():
                self._rgb_timer.stop()
        except Exception:
            pass
        try:
            if self.smtc:
                self.smtc.stop()
        except Exception:
            pass
        try:
            if self._video_bg:
                self._video_bg.stop()
        except Exception:
            pass
        try:
            if self._bg_movie:
                self._bg_movie.stop()
        except Exception:
            pass

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()
            self._position_overlay()
        self._visible = not self._visible