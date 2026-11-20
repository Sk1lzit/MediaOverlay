import keyboard
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from app.settings.hotkeys_config import load_hotkeys


class HotkeySignals(QObject):
    toggle_overlay = pyqtSignal()
    toggle_mixer = pyqtSignal()
    toggle_settings = pyqtSignal()
    play_pause = pyqtSignal()
    next_track = pyqtSignal()
    prev_track = pyqtSignal()


class GlobalHotkeys:
    """Глобальные хоткеи с безопасной доставкой в главный поток Qt."""

    def __init__(self, overlay, mixer, settings):
        self.overlay = overlay
        self.mixer = mixer
        self.settings = settings

        self.signals = HotkeySignals()

        self.signals.toggle_overlay.connect(
            self._toggle_overlay, Qt.ConnectionType.QueuedConnection
        )
        self.signals.toggle_mixer.connect(
            self._toggle_mixer, Qt.ConnectionType.QueuedConnection
        )
        self.signals.toggle_settings.connect(
            self._toggle_settings, Qt.ConnectionType.QueuedConnection
        )
        self.signals.play_pause.connect(
            self._play_pause, Qt.ConnectionType.QueuedConnection
        )
        self.signals.next_track.connect(
            self._next_track, Qt.ConnectionType.QueuedConnection
        )
        self.signals.prev_track.connect(
            self._prev_track, Qt.ConnectionType.QueuedConnection
        )

    def _toggle_overlay(self):
        self.overlay.toggle()

    def _toggle_mixer(self):
        if self.mixer.isVisible():
            self.mixer.hide()
        else:
            self.mixer.show()
            self.mixer.raise_()
            self.mixer.activateWindow()

    def _toggle_settings(self):
        if self.settings.isVisible():
            self.settings.hide()
        else:
            self.settings.show()
            self.settings.raise_()
            self.settings.activateWindow()

    def _play_pause(self):
        from app.media.smtc import play_pause
        play_pause()

    def _next_track(self):
        from app.media.smtc import next_track
        next_track()

    def _prev_track(self):
        from app.media.smtc import prev_track
        prev_track()

    def register(self):
        actions = {
            "toggle_overlay": self.signals.toggle_overlay.emit,
            "toggle_mixer": self.signals.toggle_mixer.emit,
            "toggle_settings": self.signals.toggle_settings.emit,
            "play_pause": self.signals.play_pause.emit,
            "next_track": self.signals.next_track.emit,
            "prev_track": self.signals.prev_track.emit,
        }

        cfg = load_hotkeys()

        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        for key, combo in cfg.items():
            if key in actions and combo:
                try:
                    keyboard.add_hotkey(combo, actions[key])
                    print(f"[Hotkeys] {key} → {combo}")
                except Exception as e:
                    print(f"[Hotkeys] Ошибка {combo}: {e}")

    def reload(self):
        self.register()

    def unregister(self):
        """Снимает все хуки клавиатуры — устраняет фризы при выходе."""
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        try:
            keyboard.unhook_all()
        except Exception:
            pass