window.BlackbirdTerminal = (() => {
  const classMap = {
    INFO: 'log-info',
    WARN: 'log-warn',
    ERROR: 'log-error',
    AI: 'log-ai',
    GPS: 'log-gps',
    NET: 'log-net',
    SYS: 'log-sys',
  };
  let terminal;
  const seen = new Set();

  const init = () => {
    terminal = document.getElementById('terminal');
  };

  const update = (payload) => {
    (payload.logs || []).forEach((line) => {
      const key = `${line.ts}-${line.level}-${line.message}`;
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      const row = document.createElement('div');
      row.className = `log-line ${classMap[line.level] || 'log-info'}`;
      row.textContent = `[${line.ts}] [${line.level}] ${line.message}`;
      terminal.appendChild(row);
    });
    terminal.scrollTop = terminal.scrollHeight;
  };

  return { init, update };
})();
