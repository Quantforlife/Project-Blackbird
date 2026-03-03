window.BlackbirdVideoOverlay = (() => {
  const updateFrame = (payload) => {
    window.__blackbird_last_frame = payload;
  };

  return { updateFrame };
})();
