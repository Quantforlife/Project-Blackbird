window.BlackbirdSocketClient = (() => {
  let socket = null;
  const handlers = {};

  const init = () => {
    if (!window.io || socket) {
      return;
    }
    socket = window.io({ transports: ['websocket'], reconnection: true });
    Object.entries(handlers).forEach(([eventName, callbacks]) => {
      callbacks.forEach((callback) => socket.on(eventName, callback));
    });
  };

  const on = (eventName, callback) => {
    handlers[eventName] = handlers[eventName] || [];
    if (!handlers[eventName].includes(callback)) {
      handlers[eventName].push(callback);
    }
    if (socket) {
      socket.on(eventName, callback);
    }
  };

  const off = (eventName, callback) => {
    handlers[eventName] = (handlers[eventName] || []).filter((cb) => cb !== callback);
    if (socket) {
      socket.off(eventName, callback);
    }
  };

  return { init, on, off };
})();
