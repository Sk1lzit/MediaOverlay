from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QAction
from PyQt6.QtWidgets import QWidget, QMenu


class TrayButton(QWidget):
    """Маленькая иконка в углу экрана с меню по клику."""

    def __init__(self, on_show_overlay, on_show_mixer,
                 on_show_settings, on_exit):
        super().__init__()

        self.on_show_overlay = on_show_overlay
        self.on_show_mixer = on_show_mixer
        self.on_show_settings = on_show_settings
        self.on_exit = on_exit

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(48, 48)

        # Позиция — правый верхний угол
        screen = self.screen().availableGeometry()
        self.move(screen.width() - 60, 10)

        self.setToolTip("Media Overlay")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Круг
        painter.setBrush(QColor(139, 92, 246, 220))
        painter.setPen(QColor(255, 255, 255, 100))
        painter.drawEllipse(4, 4, 40, 40)

        # Нота (символ)
        painter.setPen(QColor(255, 255, 255, 255))
        font = painter.font()
        font.setPointSize(18)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎵")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_menu(event.globalPosition().toPoint())
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_menu(event.globalPosition().toPoint())

    def _show_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #1a1a2e;
                color: white;
                border: 1px solid #8b5cf6;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #8b5cf6;
            }
        """)

        menu.addAction("🎵 Показать оверлей", self.on_show_overlay)
        menu.addAction("🎚 Микшер громкости", self.on_show_mixer)
        menu.addAction("⚙ Настройки", self.on_show_settings)
        menu.addSeparator()
        menu.addAction("❌ Выход", self.on_exit)

        menu.exec(pos)