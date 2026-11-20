import sys
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from app.overlay import Overlay
from app.hotkey import HotkeyListener
from app.ui.mixer_widget import MixerWidget
from app.settings.settings_window import SettingsWindow
from app.hotkeys import GlobalHotkeys
from app.browser.ws_server import BrowserBridge
from app.tray import TrayIcon


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    bridge = BrowserBridge()
    bridge.start()

    mixer = MixerWidget()
    mixer.set_browser_bridge(bridge)
    mixer.hide()

    settings = None

    def open_settings():
        settings.show()
        settings.raise_()
        settings.activateWindow()

    def open_mixer():
        mixer.show()
        mixer.raise_()
        mixer.activateWindow()

    overlay = Overlay(
        on_open_settings=open_settings,
        on_open_mixer=open_mixer,
        on_exit=app.quit,
        browser_bridge=bridge,
    )
    overlay.show()

    settings = SettingsWindow(
        overlay=overlay,
        on_theme_change=lambda: mixer.refresh_theme(),
    )
    settings.hide()

    hotkey = HotkeyListener(on_toggle=overlay.toggle)
    hotkey.start()

    hotkeys = GlobalHotkeys(overlay=overlay, mixer=mixer, settings=settings)
    hotkeys.register()

    settings.hotkeys_manager = hotkeys

    tray = TrayIcon(
        on_show_overlay=overlay.toggle,
        on_show_mixer=open_mixer,
        on_show_settings=open_settings,
        on_exit=app.quit,
    )
    tray.start()

    def shutdown():
        print("[App] Завершение...")
        try:
            tray.stop()
        except Exception:
            pass
        try:
            hotkeys.unregister()
        except Exception:
            pass
        try:
            overlay.shutdown()
        except Exception:
            pass
        try:
            bridge.stop()
        except Exception:
            pass
        print("[App] Готово")

    app.aboutToQuit.connect(shutdown)

    signal.signal(signal.SIGINT, lambda *args: app.quit())

    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()