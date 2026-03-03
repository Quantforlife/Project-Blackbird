window.BlackbirdMapRenderer = (() => {
  const updateTelemetry = (payload) => {
    window.__blackbird_last_telemetry = payload;
  };

  const updateProgress = (payload) => {
    window.__blackbird_last_progress = payload;
  };

  return { updateTelemetry, updateProgress };
})();
