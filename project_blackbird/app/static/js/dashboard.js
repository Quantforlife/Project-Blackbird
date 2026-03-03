(() => {
  const kpi = {
    battery: document.getElementById('kpi-battery'),
    flightTime: document.getElementById('kpi-flight-time'),
    defects: document.getElementById('kpi-defects'),
    images: document.getElementById('kpi-images'),
    progress: document.getElementById('kpi-progress'),
    signal: document.getElementById('kpi-signal'),
  };
  const slider = document.getElementById('playback-slider');
  const tableBody = document.querySelector('#defect-table tbody');
  let trendData = [];
  let severityChart;
  let trendChart;

  const initCharts = () => {
    severityChart = new Chart(document.getElementById('severity-chart'), {
      type: 'bar',
      data: {
        labels: ['Critical', 'Warning', 'Minor'],
        datasets: [{
          data: [0, 0, 0],
          backgroundColor: ['#FF3B3B', '#FFB020', '#00E5FF'],
        }],
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    });

    trendChart = new Chart(document.getElementById('trend-chart'), {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Cumulative Defects',
          data: [],
          borderColor: '#00FFA3',
          tension: 0.25,
        }],
      },
      options: { plugins: { legend: { labels: { color: '#9CA3AF' } } } },
    });
  };

  const updateKPIs = (telemetry) => {
    kpi.battery.textContent = `${telemetry.battery}%`;
    kpi.flightTime.textContent = `${telemetry.flight_time}s`;
    kpi.defects.textContent = `${telemetry.active_defects}`;
    kpi.images.textContent = `${telemetry.images_captured}`;
    kpi.progress.textContent = `${telemetry.mission_progress}%`;
    kpi.signal.textContent = `${telemetry.signal_strength}%`;
    slider.value = telemetry.images_captured;
  };

  const updateTable = (defects) => {
    tableBody.innerHTML = '';
    defects.slice(-12).reverse().forEach((d) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${d.id}</td>
        <td>${d.type}</td>
        <td>${d.severity}</td>
        <td>${d.confidence}%</td>
        <td>${d.lat.toFixed(6)}</td>
        <td>${d.lon.toFixed(6)}</td>
      `;
      tableBody.appendChild(tr);
    });
  };

  const updateCharts = (analytics, telemetry) => {
    severityChart.data.datasets[0].data = [analytics.critical, analytics.warning, analytics.minor];
    severityChart.update('none');

    trendData.push({ t: telemetry.flight_time, value: analytics.total });
    trendData = trendData.slice(-40);
    trendChart.data.labels = trendData.map((x) => x.t);
    trendChart.data.datasets[0].data = trendData.map((x) => x.value);
    trendChart.update('none');
  };

  const applyPayload = (payload) => {
    updateKPIs(payload.telemetry);
    BlackbirdMap.update(payload);
    BlackbirdVideo.update(payload);
    BlackbirdTerminal.update(payload);
    updateTable(payload.defects || []);
    updateCharts(payload.analytics, payload.telemetry);
  };

  const wireControls = () => {
    document.querySelectorAll('[data-command]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await BlackbirdTelemetry.sendCommand(btn.dataset.command);
      });
    });

    document.querySelectorAll('[data-mode]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        document.querySelectorAll('[data-mode]').forEach((n) => n.classList.remove('active'));
        btn.classList.add('active');
        await BlackbirdTelemetry.setMode(btn.dataset.mode);
      });
    });

    slider.addEventListener('input', async () => {
      const playbackActive = document.querySelector('[data-mode="playback"]').classList.contains('active');
      if (playbackActive) {
        await BlackbirdTelemetry.setPlayback(slider.value);
      }
    });
  };

  const init = () => {
    BlackbirdMap.init();
    BlackbirdVideo.init();
    BlackbirdTerminal.init();
    initCharts();
    wireControls();

    BlackbirdTelemetry.onUpdate(applyPayload);
    BlackbirdTelemetry.connect();
  };

  window.addEventListener('DOMContentLoaded', init);
})();
