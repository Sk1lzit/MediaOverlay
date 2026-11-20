import threading
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item


def create_icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill=(139, 92, 246, 255))
    draw.ellipse((22, 36, 38, 52), fill=(255, 255, 255, 255))
    draw.rectangle((36, 16, 40, 46), fill=(255, 255, 255, 255))
    return img


class TrayIcon:
    def __init__(self, on_show_overlay, on_show_mixer,
                 on_show_settings, on_exit):
        self.on_show_overlay = on_show_overlay
        self.on_show_mixer = on_show_mixer
        self.on_show_settings = on_show_settings
        self.on_exit = on_exit
        self.icon = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        menu = pystray.Menu(
            item("🎵 Показать оверлей", self._overlay, default=True),
            item("🎚 Микшер громкости", self._mixer),
            item("⚙ Настройки", self._settings),
            pystray.Menu.SEPARATOR,
            item("❌ Выход", self._exit),
        )
        self.icon = pystray.Icon(
            "MediaOverlay",
            icon=create_icon_image(),
            title="Media Overlay",
            menu=menu,
        )
        self.icon.run()

    def _overlay(self, icon, item):
        self.on_show_overlay()

    def _mixer(self, icon, item):
        self.on_show_mixer()

    def _settings(self, icon, item):
        self.on_show_settings()

    def _exit(self, icon, item):
        if self.icon:
            self.icon.stop()
        self.on_exit()

    def stop(self):
        try:
            if self.icon:
                self.icon.stop()
        except Exception:
            pass