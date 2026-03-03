window.BlackbirdTerminalConsole = (() => {
  const pushEvent = (payload) => {
    window.__blackbird_terminal_events = window.__blackbird_terminal_events || [];
    window.__blackbird_terminal_events.push(payload);
  };

  return { pushEvent };
})();
