// background.js — сервис-воркер, дублирует WS-канал для надёжности

let ws = null;

function connect() {
  try {
    ws = new WebSocket("ws://127.0.0.1:8765");
  } catch (e) {
    setTimeout(connect, 3000);
    return;
  }

  ws.onopen = () => console.log("[MediaOverlay BG] WS подключён");
  ws.onclose = () => {
    ws = null;
    setTimeout(connect, 3000);
  };
  ws.onerror = () => {};

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "command") {
        // Пересылаем во все вкладки
        chrome.tabs.query({}, (tabs) => {
          for (const tab of tabs) {
            chrome.tabs.sendMessage(tab.id, data).catch(() => {});
          }
        });
      }
    } catch (e) {}
  };
}

connect();