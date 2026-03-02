window.BlackbirdTelemetry = (() => {
  let source = null;
  const handlers = new Set();
  const reconnectDelayMs = 2000;
  let reconnectTimer = null;

  const connect = () => {
    if (source) {
      source.close();
    }
    source = new EventSource('/realtime/stream');
    source.addEventListener('telemetry', (event) => {
      const payload = JSON.parse(event.data);
      handlers.forEach((handler) => handler(payload));
    });
    source.onerror = () => {
      if (source) {
        source.close();
      }
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          connect();
        }, reconnectDelayMs);
      }
    };
  };

  const onUpdate = (handler) => {
    handlers.add(handler);
  };

  const sendCommand = async (action) => {
    await fetch(`/realtime/command/${action}`, { method: 'POST' });
  };

  const setMode = async (mode) => {
    await fetch(`/realtime/mode/${mode}`, { method: 'POST' });
  };

  const setPlayback = async (index) => {
    await fetch(`/realtime/playback/${index}`, { method: 'POST' });
  };

  return {
    connect,
    onUpdate,
    sendCommand,
    setMode,
    setPlayback,
  };
})();
