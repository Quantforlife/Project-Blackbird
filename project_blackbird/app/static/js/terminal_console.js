window.BlackbirdTerminalConsole = (() => {
  let terminal;
  const seen = new Set();
  const seenQueue = [];
  const levelClass = {
    SYSTEM: 'terminal-system',
    AI: 'terminal-ai',
    GPS: 'terminal-gps',
    WARN: 'terminal-warn',
    ERROR: 'terminal-error',
  };

  const init = () => {
    terminal = document.getElementById('terminal-console');
  };

  const pushEvent = (payload) => {
    if (!terminal) {
      return;
    }
    const timestamp = payload.timestamp !== undefined ? Number(payload.timestamp).toFixed(2) : '0.00';
    const type = String(payload.type || 'SYSTEM').toUpperCase();
    const message = String(payload.message || '');
    const key = `${timestamp}:${type}:${message}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    seenQueue.push(key);

    const line = document.createElement('div');
    line.className = `terminal-line ${levelClass[type] || 'terminal-system'}`;
    line.textContent = `[${timestamp}] [${type}] ${message}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;

    const maxLines = 300;
    while (terminal.children.length > maxLines) {
      terminal.removeChild(terminal.firstChild);
    }
    while (seenQueue.length > maxLines * 2) {
      const oldest = seenQueue.shift();
      seen.delete(oldest);
    }
  };

  const clear = () => {
    if (terminal) {
      terminal.innerHTML = '';
    }
    seen.clear();
    seenQueue.length = 0;
  };

  return { init, pushEvent, clear };
})();
