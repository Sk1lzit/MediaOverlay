import cv2
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap


class VideoBackground:
    def __init__(self, on_frame):
        self.on_frame = on_frame
        self.cap = None
        self.timer = None
        self.fps = 24
        self._error_logged = False

    def load(self, path):
        self.stop()
        try:
            self.cap = cv2.VideoCapture(path)
            if not self.cap.isOpened():
                print(f"[Video] Не удалось открыть: {path}")
                self.cap = None
                return False

            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = fps if fps and fps > 0 else 24

            self.timer = QTimer()
            self.timer.timeout.connect(self._next_frame)
            self.timer.start(int(1000 / self.fps))
            return True
        except Exception as e:
            print(f"[Video] Ошибка загрузки: {e}")
            self.cap = None
            return False

    def _next_frame(self):
        if self.cap is None:
            return
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                # Зацикливаем
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg.copy())

            self.on_frame(pixmap)
        except Exception as e:
            if not self._error_logged:
                print(f"[Video] Ошибка кадра: {e}")
                self._error_logged = True

    def stop(self):
        if self.timer:
            self.timer.stop()
            self.timer = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self._error_logged = False