import os
import threading
import pythoncom
import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
from pycaw.pycaw import AudioUtilities


SYSTEM_PROCESSES = {
    "svchost.exe",
    "audiodg.exe",
    "System",
    "Registry",
    "Idle",
    "wallpaper64.exe",
    "wallpaper32.exe",
    "backgroundTaskHost.exe",
    "RuntimeBroker.exe",
    "SearchApp.exe",
    "StartMenuExperienceHost.exe",
    "TextInputHost.exe",
    "ShellExperienceHost.exe",
}


class AudioMixer:
    def __init__(self):
        self._icon_cache = {}
        self._path_cache = {}
        self._lock = threading.Lock()

    def get_sessions(self, hide_system=True):
        """Безопасный обход сессий с COM-инициализацией."""
        result = []
        try:
            pythoncom.CoInitialize()
            sessions = AudioUtilities.GetAllSessions()

            for session in sessions:
                if session.Process is None:
                    continue
                try:
                    name = session.Process.name()
                    pid = session.Process.pid

                    if hide_system and name in SYSTEM_PROCESSES:
                        continue

                    volume = session.SimpleAudioVolume

                    result.append({
                        "name": name,
                        "pid": pid,
                        "volume": volume.GetMasterVolume(),
                        "muted": volume.GetMute(),
                        "session": session,
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"[Mixer] get_sessions ошибка: {e}")
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        seen = set()
        unique = []
        for item in result:
            if item["pid"] in seen:
                continue
            seen.add(item["pid"])
            unique.append(item)

        unique.sort(key=lambda x: x["name"].lower())
        return unique

    def get_icon(self, exe_name):
        if exe_name in self._icon_cache:
            return self._icon_cache[exe_name]
        exe_path = self._find_exe_path(exe_name)
        if not exe_path:
            self._icon_cache[exe_name] = None
            return None
        icon = self._extract_icon(exe_path)
        self._icon_cache[exe_name] = icon
        return icon

    def _find_exe_path(self, exe_name):
        if exe_name in self._path_cache:
            return self._path_cache[exe_name]
        try:
            import psutil
            exe_path = None
            for proc in psutil.process_iter(["name", "exe"]):
                try:
                    info = proc.info
                    if info.get("name") == exe_name and info.get("exe"):
                        exe_path = info["exe"]
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            self._path_cache[exe_name] = exe_path
            return exe_path
        except Exception:
            self._path_cache[exe_name] = None
            return None

    @staticmethod
    def _extract_icon(exe_path):
        try:
            if not os.path.exists(exe_path):
                return None
            ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
            ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
            large, small = win32gui.ExtractIconEx(exe_path, 0)
            if not large:
                return None
            hicon = large[0]
            if not hicon:
                return None
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
            hdc_mem = hdc.CreateCompatibleDC()
            hdc_mem.SelectObject(hbmp)
            hdc_mem.DrawIcon((0, 0), hicon)
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                "RGBA", (ico_x, ico_y), bmpstr, "raw", "BGRA", 0, 1
            )
            win32gui.DestroyIcon(hicon)
            win32gui.DeleteObject(hbmp.GetHandle())
            hdc_mem.DeleteDC()
            return img
        except Exception:
            return None

    @staticmethod
    def set_volume(session, value):
        try:
            pythoncom.CoInitialize()
            session.SimpleAudioVolume.SetMasterVolume(float(value), None)
        except Exception:
            pass
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    @staticmethod
    def set_mute(session, muted: bool):
        try:
            pythoncom.CoInitialize()
            session.SimpleAudioVolume.SetMute(bool(muted), None)
        except Exception:
            pass
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass