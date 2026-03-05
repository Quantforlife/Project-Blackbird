window.BlackbirdMissionControls = (() => {
  let playbackMode = false;
  let playbackSpeed = 1;
  let onSeek = () => {};
  let onCommand = () => {};
  let onMode = () => {};
  let keyHandler = null;
  let cleanupFns = [];
  let diagnostics = false;

  const debug = (...args) => {
    if (diagnostics) {
      console.debug('[BlackbirdMissionControls]', ...args);
    }
  };

  const slider = () => document.getElementById('timeline-slider');
  const timelineLabel = () => document.getElementById('timeline-time');

  const setPlaybackMode = (enabled) => {
    playbackMode = enabled;
    document.querySelectorAll('[data-live-command]').forEach((btn) => {
      btn.disabled = playbackMode;
    });
    document.querySelectorAll('[data-mode]').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.mode === (enabled ? 'playback' : 'live'));
    });
  };

  const installKeyboardHandler = () => {
    if (keyHandler) {
      window.removeEventListener('keydown', keyHandler);
    }
    keyHandler = async (event) => {
      const tagName = (event.target?.tagName || '').toLowerCase();
      if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') return;
      if (event.code === 'Space') {
        event.preventDefault();
        if (!playbackMode) await onCommand('pause');
      }
      if (event.key.toLowerCase() === 'r') await onCommand('resume');
      if (event.key.toLowerCase() === 's') await onCommand('start');
    };
    window.addEventListener('keydown', keyHandler, { passive: false });
  };

  const addCleanup = (fn) => cleanupFns.push(fn);

  const bind = (handlers) => {
    teardown();
    diagnostics = Boolean(handlers?.diagnostics);
    onSeek = handlers.onSeek || onSeek;
    onCommand = handlers.onCommand || onCommand;
    onMode = handlers.onMode || onMode;

    document.querySelectorAll('[data-live-command]').forEach((btn) => {
      const handler = async () => {
        debug('click', btn.dataset.liveCommand);
        await onCommand(btn.dataset.liveCommand);
      };
      btn.addEventListener('click', handler);
      addCleanup(() => btn.removeEventListener('click', handler));
    });

    document.querySelectorAll('[data-mode]').forEach((btn) => {
      const handler = async () => {
        const isPlayback = btn.dataset.mode === 'playback';
        setPlaybackMode(isPlayback);
        await onMode(btn.dataset.mode);
      };
      btn.addEventListener('click', handler);
      addCleanup(() => btn.removeEventListener('click', handler));
    });

    const sliderNode = slider();
    const sliderHandler = async (event) => {
      const value = Number(event.target.value);
      timelineLabel().textContent = `t=${(value / playbackSpeed).toFixed(1)}s`;
      if (playbackMode) await onSeek(value / playbackSpeed);
    };
    sliderNode.addEventListener('input', sliderHandler);
    addCleanup(() => sliderNode.removeEventListener('input', sliderHandler));

    const speedNode = document.getElementById('playback-speed');
    const speedHandler = (event) => {
      playbackSpeed = Number(event.target.value);
    };
    speedNode.addEventListener('change', speedHandler);
    addCleanup(() => speedNode.removeEventListener('change', speedHandler));

    installKeyboardHandler();
  };

  const teardown = () => {
    cleanupFns.forEach((fn) => fn());
    cleanupFns = [];
    if (keyHandler) {
      window.removeEventListener('keydown', keyHandler);
      keyHandler = null;
    }
  };

  const updateTimeline = (timestamp, maxValue = 120) => {
    const val = Math.min(maxValue, Math.max(0, timestamp));
    slider().value = String(val);
    timelineLabel().textContent = `t=${Number(val).toFixed(1)}s`;
  };

  return { bind, setPlaybackMode, updateTimeline, teardown };
})();
