// content.js — работаем ТОЛЬКО в главном фрейме вкладки
(function () {
  if (window !== window.top) {
    return; // игнорируем iframe
  }

  const WS_URL = "ws://127.0.0.1:8765";
  let ws = null;
  let reconnectTimer = null;
  let observer = null;
  let lastSentJson = "";

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    try {
      ws = new WebSocket(WS_URL);
    } catch (e) {
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      console.log("[MediaOverlay] WS подключён");
      attachMediaListeners();
      startObserver();
      sendTabs(true);
    };

    ws.onclose = () => {
      ws = null;
      scheduleReconnect();
    };

    ws.onerror = () => {};

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "command") {
          if (!data.tab_id || data.tab_id === window.location.href) {
            handleCommand(data.command, data.payload || {});
          }
        }
      } catch (e) {}
    };
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, 5000);
  }

  function getMediaElements() {
    return Array.from(document.querySelectorAll("video, audio"));
  }

  function getTabInfo() {
    const all = getMediaElements();
    const activeMedia = all.find((m) => !m.paused) || all[0];

    let totalVol = 0, anyMuted = false, anyPlaying = false;
    for (const m of all) {
      totalVol += m.volume;
      if (m.muted) anyMuted = true;
      if (!m.paused) anyPlaying = true;
    }
    const avgVol = all.length ? totalVol / all.length : 1;

    return {
      id: window.location.href,
      url: window.location.href,
      title: document.title,
      playing: anyPlaying,
      muted: anyMuted,
      volume: avgVol,
      media_count: all.length,
      track: activeMedia
        ? {
            currentTime: activeMedia.currentTime,
            duration: activeMedia.duration || 0,
            paused: activeMedia.paused,
            volume: activeMedia.volume,
            muted: activeMedia.muted,
          }
        : null,
    };
  }

  function sendTabs(force = false) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const info = getTabInfo();
    const json = JSON.stringify(info);
    if (!force && json === lastSentJson) return;
    lastSentJson = json;
    ws.send(JSON.stringify({ type: "tabs_update", tabs: [info] }));
  }

  function handleCommand(command, payload) {
    const all = getMediaElements();
    if (all.length === 0) return;

    if (command === "set_volume") {
      const v = Math.max(0, Math.min(1, payload.volume));
      for (const m of all) m.volume = v;
    } else if (command === "set_mute") {
      for (const m of all) m.muted = !!payload.muted;
    } else if (command === "play_pause") {
      const anyPlaying = all.some((m) => !m.paused);
      for (const m of all) {
        if (anyPlaying) m.pause();
        else m.play().catch(() => {});
      }
    } else if (command === "next") {
      const btn = document.querySelector('.next-button, [aria-label*="Next" i]');
      if (btn) btn.click();
    } else if (command === "prev") {
      const btn = document.querySelector('.previous-button, [aria-label*="Previous" i]');
      if (btn) btn.click();
    }
  }

  function startObserver() {
    if (observer) return;
    observer = new MutationObserver(() => sendTabs());
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["src", "muted"],
    });
    setInterval(() => sendTabs(), 2000);
  }

  function attachMediaListeners() {
    const all = document.querySelectorAll("video, audio");
    for (const m of all) {
      if (m._mo_attached) continue;
      m._mo_attached = true;
      ["play", "pause", "volumechange", "timeupdate", "ended"].forEach((evt) => {
        m.addEventListener(evt, () => sendTabs());
      });
    }
  }

  connect();
  setInterval(() => {
    attachMediaListeners();
    if (!ws || ws.readyState === WebSocket.CLOSED) connect();
  }, 3000);
})();