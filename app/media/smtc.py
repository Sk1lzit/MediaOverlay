import asyncio
import threading
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)
from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions


class SMTCListener:
    """Слушает Windows SMTC и отдаёт данные о текущем треке."""

    def __init__(self, on_update):
        self.on_update = on_update
        self._stop = False
        self._session = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop = True

    def _run(self):
        asyncio.run(self._loop())

    async def _loop(self):
        while not self._stop:
            try:
                manager = await MediaManager.request_async()
                session = manager.get_current_session()
                self._session = session

                if session is None:
                    self.on_update(None)
                else:
                    info = await session.try_get_media_properties_async()
                    timeline = session.get_timeline_properties()
                    playback_info = session.get_playback_info()

                    title = info.title or "Неизвестно"
                    artist = info.artist or "—"
                    position = timeline.position.total_seconds()
                    duration = timeline.end_time.total_seconds()
                    # 4 = PLAYING
                    is_playing = playback_info.playback_status == 4

                    thumbnail = None
                    if info.thumbnail is not None:
                        thumbnail = await self._read_thumbnail(info.thumbnail)

                    self.on_update({
                        "title": title,
                        "artist": artist,
                        "position": position,
                        "duration": duration,
                        "thumbnail": thumbnail,
                        "is_playing": is_playing,
                    })
            except Exception as e:
                print(f"[SMTC] Ошибка: {e}")

            await asyncio.sleep(2)

    async def _read_thumbnail(self, stream_ref):
        try:
            stream = await stream_ref.open_read_async()
            size = stream.size
            if size == 0:
                return None
            buffer = Buffer(size)
            await stream.read_async(buffer, size, InputStreamOptions.READ_AHEAD)
            reader = DataReader.from_buffer(buffer)
            data = bytearray(size)
            reader.read_bytes(data)
            return bytes(data)
        except Exception as e:
            print(f"[SMTC] Ошибка чтения обложки: {e}")
            return None


# ===== Управление плеером =====

def _run_async(coro):
    """Запускает корутину в отдельном потоке с event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_session():
    manager = await MediaManager.request_async()
    return manager.get_current_session()


def play_pause():
    async def _do():
        s = await _get_session()
        if s:
            await s.try_toggle_play_pause_async()
    threading.Thread(target=_run_async, args=(_do(),), daemon=True).start()


def next_track():
    async def _do():
        s = await _get_session()
        if s:
            await s.try_skip_next_async()
    threading.Thread(target=_run_async, args=(_do(),), daemon=True).start()


def prev_track():
    async def _do():
        s = await _get_session()
        if s:
            await s.try_skip_previous_async()
    threading.Thread(target=_run_async, args=(_do(),), daemon=True).start()