from pynput import mouse


class HotkeyListener:
    def __init__(self, on_toggle):
        self.on_toggle = on_toggle
        self.listener = None

    def start(self):
        def on_click(x, y, button, pressed):
            if button == mouse.Button.middle and pressed:
                try:
                    self.on_toggle()
                except Exception as e:
                    print(f"[Hotkey] Ошибка: {e}")

        self.listener = mouse.Listener(on_click=on_click)
        self.listener.start()
        print("[Hotkey] Слушатель запущен. Средний клик = toggle оверлея.")