from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
)
from app.settings.hotkeys_config import load_hotkeys, save_hotkeys


class HotkeysTab(QWidget):
    """Вкладка настройки хоткеев."""

    LABELS = {
        "toggle_overlay": "Показать оверлей",
        "toggle_mixer": "Показать микшер",
        "toggle_settings": "Показать настройки",
        "play_pause": "Play / Pause",
        "next_track": "Следующий трек",
        "prev_track": "Предыдущий трек",
    }

    def __init__(self, on_save):
        super().__init__()
        self.on_save = on_save
        self.cfg = load_hotkeys()
        self.fields = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        for key, label in self.LABELS.items():
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(160)
            lbl.setStyleSheet("color: #ddd; font-size: 12px;")
            row.addWidget(lbl)

            field = QLineEdit(self.cfg.get(key, ""))
            field.setPlaceholderText("например: ctrl+alt+m")
            field.setStyleSheet("""
                background: #2a2a3a; color: white;
                border: 1px solid #3a3a4a; border-radius: 6px; padding: 6px;
            """)
            row.addWidget(field)
            self.fields[key] = field

            layout.addLayout(row)

        save_btn = QPushButton("💾 Сохранить хоткеи")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        hint = QLabel(
            "Синтаксис: ctrl+alt+m, shift+f1, ctrl+shift+right и т.д."
        )
        hint.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(hint)

    def _save(self):
        for key, field in self.fields.items():
            self.cfg[key] = field.text().strip()
        save_hotkeys(self.cfg)
        self.on_save()