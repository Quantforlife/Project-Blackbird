window.BlackbirdMissionControls = (() => {
  let playbackMode = false;
  let playbackSpeed = 1;
  let onSeek = () => {};
  let onCommand = () => {};
  let onMode = () => {};
  let keyHandler = null;

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
      if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
        return;
      }
      if (event.code === 'Space') {
        event.preventDefault();
        if (playbackMode) {
          return;
        }
        await onCommand('pause');
      }
      if (event.key.toLowerCase() === 'r') {
        await onCommand('resume');
      }
      if (event.key.toLowerCase() === 's') {
        await onCommand('start');
      }
    };
    window.addEventListener('keydown', keyHandler, { passive: false });
  };

  const bind = (handlers) => {
    onSeek = handlers.onSeek || onSeek;
    onCommand = handlers.onCommand || onCommand;
    onMode = handlers.onMode || onMode;

    document.querySelectorAll('[data-live-command]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await onCommand(btn.dataset.liveCommand);
      });
    });

    document.querySelectorAll('[data-mode]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const isPlayback = btn.dataset.mode === 'playback';
        setPlaybackMode(isPlayback);
        await onMode(btn.dataset.mode);
      });
    });

    slider().addEventListener('input', async (event) => {
      const value = Number(event.target.value);
      timelineLabel().textContent = `t=${(value / playbackSpeed).toFixed(1)}s`;
      if (playbackMode) {
        await onSeek(value / playbackSpeed);
      }
    });

    document.getElementById('playback-speed').addEventListener('change', (event) => {
      playbackSpeed = Number(event.target.value);
    });

    installKeyboardHandler();
  };

  const teardown = () => {
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
