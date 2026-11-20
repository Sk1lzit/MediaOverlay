import asyncio
import json
import threading
import time
import websockets
from PyQt6.QtCore import QObject, pyqtSignal


class BrowserBridge(QObject):
    tabs_updated = pyqtSignal(list)
    command_done = pyqtSignal(str)

    def __init__(self, host="127.0.0.1", port=8765):
        super().__init__()
        self.host = host
        self.port = port
        self.clients = {}  # websocket -> tab_id
        self._tabs = {}
        self._last_emit = ""
        self._loop = None
        self._server = None
        self._thread = None
        self._cleanup_thread = None
        self._running = True

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, daemon=True
        )
        self._cleanup_thread.start()

    def stop(self):
        """Корректно останавливает WebSocket-сервер."""
        self._running = False
        try:
            if self._loop and self._server:
                asyncio.run_coroutine_threadsafe(
                    self._server.close(), self._loop
                )
        except Exception:
            pass
        try:
            if self._loop:
                self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception:
            pass

    async def _serve(self):
        async def handler(websocket):
            self.clients[websocket] = None
            print(f"[WS] Клиент подключён (всего: {len(self.clients)})")
            try:
                async for message in websocket:
                    await self._on_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                pass
            except Exception:
                pass
            finally:
                self.clients.pop(websocket, None)
                print(f"[WS] Клиент отключён (осталось: {len(self.clients)})")

        self._server = await websockets.serve(
            handler, self.host, self.port,
            ping_interval=20, ping_timeout=20,
        )
        print(f"[WS] Сервер запущен на ws://{self.host}:{self.port}")
        await self._server.wait_closed()

    async def _on_message(self, websocket, raw):
        try:
            data = json.loads(raw)
        except Exception:
            return

        msg_type = data.get("type")

        if msg_type == "tabs_update":
            tabs = data.get("tabs", [])
            now = time.time()
            for t in tabs:
                tab_id = t.get("id")
                if not tab_id:
                    continue
                t["_last_seen"] = now
                self._tabs[tab_id] = t
                self.clients[websocket] = tab_id

            dead = [
                tid for tid, t in self._tabs.items()
                if now - t.get("_last_seen", 0) > 15
            ]
            for tid in dead:
                self._tabs.pop(tid, None)

            self._emit(list(self._tabs.values()))

        elif msg_type == "command_done":
            self.command_done.emit(data.get("command", ""))

    def _emit(self, tabs):
        json_key = json.dumps(tabs, sort_keys=True, default=str)
        if json_key == self._last_emit:
            return
        self._last_emit = json_key
        self.tabs_updated.emit(tabs)

    def _cleanup_loop(self):
        while self._running:
            time.sleep(5)
            if not self._running:
                break
            now = time.time()
            dead = [
                tid for tid, t in self._tabs.items()
                if now - t.get("_last_seen", 0) > 15
            ]
            if dead:
                for tid in dead:
                    self._tabs.pop(tid, None)
                self._emit(list(self._tabs.values()))

    def send_command(self, command: str, tab_id: str = None, payload: dict = None):
        if not self.clients or not self._loop:
            return
        message = json.dumps({
            "type": "command",
            "command": command,
            "tab_id": tab_id,
            "payload": payload or {},
        })
        try:
            asyncio.run_coroutine_threadsafe(
                self._send_to_tab(message, tab_id),
                self._loop,
            )
        except Exception:
            pass

    async def _send_to_tab(self, message, tab_id):
        for ws, client_tab_id in list(self.clients.items()):
            try:
                if tab_id is None or client_tab_id == tab_id:
                    await ws.send(message)
            except Exception:
                pass