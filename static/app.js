/* cost-of-saying-yes — main app JS */

'use strict';

// ── State ──────────────────────────────────────────────────────────────────
let currentData = null;        // all three scenario results from the API
let activeScenario = 'realistic';
let chartInitialized = false;       // tracks whether Plotly.newPlot has been called
let resizeListenerAttached = false; // ensures the resize listener is added exactly once

// ── Currency formatter ─────────────────────────────────────────────────────
function formatCurrency(n) {
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) {
    const kVal = (abs / 1_000).toFixed(0);
    // Guard against rounding up to 1000 (e.g. $999,500 → "$1000K")
    if (Number(kVal) >= 1000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
    return `${sign}$${kVal}K`;
  }
  return `${sign}$${abs.toFixed(0)}`;
}

// ── Chart rendering ────────────────────────────────────────────────────────
function buildLayout(breakEvenMonth, troughMonth, troughValue) {
  const shapes = [];
  const annotations = [];

  if (breakEvenMonth !== null && breakEvenMonth !== undefined) {
    shapes.push({
      type: 'line', xref: 'x', yref: 'paper',
      x0: breakEvenMonth, x1: breakEvenMonth, y0: 0, y1: 1,
      line: { color: '#cc100a', width: 1.5, dash: 'dash' }
    });
    annotations.push({
      x: breakEvenMonth, y: 1, xref: 'x', yref: 'paper',
      text: `Break-even: Month ${breakEvenMonth}`,
      showarrow: false, xanchor: 'left',
      font: { family: 'Source Sans 3, sans-serif', size: 12, color: '#cc100a' }
    });
  }

  // Only annotate the trough when the position is negative — a positive
  // minimum is not a meaningful trough for this tool's audience.
  if (troughValue !== undefined && troughMonth !== undefined && troughValue < 0) {
    annotations.push({
      x: troughMonth, y: troughValue, xref: 'x', yref: 'y',
      text: `Peak trough<br>${formatCurrency(troughValue)}`,
      showarrow: true, arrowhead: 2, arrowsize: 1, arrowwidth: 1.5,
      arrowcolor: '#ffffff', ax: 40, ay: -40,
      bgcolor: '#1a1a1a', bordercolor: 'rgba(255,255,255,0.12)',
      font: { family: 'Source Sans 3, sans-serif', size: 12, color: '#ffffff' },
      borderpad: 6
    });
  }

  return {
    paper_bgcolor: '#f5f3ee',
    plot_bgcolor:  '#f5f3ee',
    margin: { t: 24, r: 24, b: 48, l: 80 },
    xaxis: {
      title: { text: 'Month', font: { family: 'Source Sans 3, sans-serif', size: 12 } },
      tickfont: { family: 'Source Sans 3, sans-serif', size: 12 },
      showgrid: false,
      zeroline: false,
      dtick: 1
    },
    yaxis: {
      tickfont: { family: 'Source Sans 3, sans-serif', size: 12 },
      tickformat: '$.3s',
      gridcolor: '#d9d9d9',
      showgrid: true,
      zeroline: true,
      zerolinecolor: '#666666',
      zerolinewidth: 2
    },
    shapes,
    annotations,
    showlegend: false
  };
}

function renderChart(scenario) {
  const data = currentData[scenario];
  const trace = {
    x: data.months,
    y: [...data.cumulative_cash_position],
    type: 'scatter',
    mode: 'lines',
    fill: 'tozeroy',
    fillcolor: 'rgba(31, 46, 122, 0.08)',
    line: { color: '#1f2e7a', width: 2.5 },
    hovertemplate: 'Month %{x}<br>%{y:$,.0f}<extra></extra>'
  };

  const layout = buildLayout(data.break_even_month, data.trough_month, data.trough_value);
  const config = { responsive: true, displaylogo: false, displayModeBar: false };

  let plotPromise;
  if (!chartInitialized) {
    plotPromise = Plotly.newPlot('cashflow-chart', [trace], layout, config);
    chartInitialized = true;
    if (!resizeListenerAttached) {
      window.addEventListener('resize', () => Plotly.Plots.resize('cashflow-chart'));
      resizeListenerAttached = true;
    }
  } else {
    plotPromise = Plotly.react('cashflow-chart', [trace], layout, config);
  }
  return plotPromise;
}

// ── Comparison panel ───────────────────────────────────────────────────────
function updateComparisonPanel(scenario) {
  const summary = currentData[scenario].summary;
  const brokerEl  = document.getElementById('broker-projection-value');
  const cashEl    = document.getElementById('net-cash-value');

  brokerEl.textContent = formatCurrency(summary.broker_projection_year1);
  brokerEl.classList.remove('negative');

  const netCash = summary.net_cash_impact_year1;
  cashEl.textContent = formatCurrency(netCash);
  cashEl.classList.toggle('negative', netCash < 0);
}

// ── Scenario switch ────────────────────────────────────────────────────────
function renderScenario(scenario) {
  activeScenario = scenario;
  const chartPromise = renderChart(scenario);
  updateComparisonPanel(scenario);

  // Update toggle button states
  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.scenario === scenario);
  });

  return chartPromise;
}

// ── Form submission ────────────────────────────────────────────────────────
document.getElementById('input-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('calculate-btn');

  // Guard against Enter-key re-entry while a fetch is already in flight
  if (btn.disabled) return;

  const errorEl = document.getElementById('form-error');
  errorEl.textContent = '';

  // Collect form values
  const retailer   = document.getElementById('retailer').value;
  const doors      = parseInt(document.getElementById('doors').value, 10);
  const skus       = parseInt(document.getElementById('skus').value, 10);
  const price      = parseFloat(document.getElementById('unit_price_wholesale').value);
  const cogs       = parseFloat(document.getElementById('cogs_per_unit').value);
  const velocity   = parseFloat(document.getElementById('velocity').value);
  const brokerRaw  = document.getElementById('broker_projection').value;
  const broker     = brokerRaw ? parseFloat(brokerRaw) : null;

  // Client-side guard (server validates too, but this gives instant feedback)
  if (!doors || !skus || !price || !cogs || !velocity) {
    errorEl.textContent = 'Please fill in all required fields.';
    return;
  }
  if (cogs >= price) {
    errorEl.textContent = 'COGS must be less than wholesale price.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Calculating…';

  const payload = {
    retailer, doors, skus,
    unit_price_wholesale: price,
    cogs_per_unit: cogs,
    velocity_units_per_door_per_week: velocity,
  };
  if (broker !== null) payload.broker_projection_year1 = broker;

  const controller = new AbortController();
  const timeoutId  = setTimeout(() => controller.abort(), 30_000);
  // Show cold-start hint after 2s — Fly.io auto-start can take a moment
  const coldStartId = setTimeout(() => {
    if (btn.disabled) btn.textContent = 'Calculating… (first load may take a moment)';
  }, 2_000);

  try {
    const res = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = Array.isArray(err.detail)
        ? err.detail.map(d => d.msg).join('; ')
        : (err.detail || `Server error (${res.status})`);
      errorEl.textContent = detail;
      return;
    }

    currentData = await res.json();
    chartInitialized = false;  // next renderChart will call Plotly.newPlot for fresh layout

    // Show results panel
    const panel = document.getElementById('results-panel');
    panel.classList.add('visible');

    // Enable scenario and compare buttons
    document.querySelectorAll('.btn-scenario').forEach(b => b.disabled = false);
    document.getElementById('compare-btn').disabled = false;

    // Render scenario, then scroll after Plotly draw completes
    await renderScenario(activeScenario);

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    panel.scrollIntoView({ behavior: prefersReduced ? 'auto' : 'smooth', block: 'start' });

  } catch (err) {
    if (err.name === 'AbortError') {
      errorEl.textContent = 'Request timed out — the server may be starting up. Please try again.';
    } else {
      errorEl.textContent = 'Network error — is the server running?';
    }
  } finally {
    clearTimeout(timeoutId);
    clearTimeout(coldStartId);
    btn.disabled = false;
    btn.textContent = 'Calculate';
  }
});

// ── Scenario toggle ────────────────────────────────────────────────────────
document.querySelectorAll('.btn-scenario').forEach(btn => {
  btn.addEventListener('click', () => {
    if (currentData) renderScenario(btn.dataset.scenario);
  });
});

// ── Retailer comparison table ──────────────────────────────────────────────
function renderCompareTable(data) {
  const tbody = document.getElementById('compare-tbody');
  tbody.innerHTML = '';
  data.retailers.forEach(r => {
    const tr = document.createElement('tr');
    const breakEven = r.break_even_month !== null ? `Month ${r.break_even_month}` : '—';
    const troughClass = r.trough_value < 0 ? ' class="negative"' : '';
    const netClass = r.net_cash_impact_year1 < 0 ? ' class="negative"' : '';
    tr.innerHTML = `
      <td>${r.label}</td>
      <td${troughClass}>${formatCurrency(r.trough_value)}</td>
      <td>Month ${r.trough_month}</td>
      <td>${breakEven}</td>
      <td${netClass}>${formatCurrency(r.net_cash_impact_year1)}</td>
    `;
    tbody.appendChild(tr);
  });
  document.getElementById('compare-section').style.display = '';
}

document.getElementById('compare-btn').addEventListener('click', async () => {
  const btn = document.getElementById('compare-btn');
  if (btn.disabled) return;

  const errorEl = document.getElementById('form-error');
  errorEl.textContent = '';

  const doors    = parseInt(document.getElementById('doors').value, 10);
  const skus     = parseInt(document.getElementById('skus').value, 10);
  const price    = parseFloat(document.getElementById('unit_price_wholesale').value);
  const cogs     = parseFloat(document.getElementById('cogs_per_unit').value);
  const velocity = parseFloat(document.getElementById('velocity').value);
  const brokerRaw = document.getElementById('broker_projection').value;
  const broker   = brokerRaw ? parseFloat(brokerRaw) : null;

  if (!doors || !skus || !price || !cogs || !velocity) {
    errorEl.textContent = 'Please fill in all required fields before comparing.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Comparing…';

  const payload = {
    doors, skus,
    unit_price_wholesale: price,
    cogs_per_unit: cogs,
    velocity_units_per_door_per_week: velocity,
  };
  if (broker !== null) payload.broker_projection_year1 = broker;

  const controller = new AbortController();
  const timeoutId  = setTimeout(() => controller.abort(), 30_000);

  try {
    const res = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = Array.isArray(err.detail)
        ? err.detail.map(d => d.msg).join('; ')
        : (err.detail || `Server error (${res.status})`);
      errorEl.textContent = detail;
      return;
    }

    renderCompareTable(await res.json());

  } catch (err) {
    if (err.name === 'AbortError') {
      errorEl.textContent = 'Request timed out — please try again.';
    } else {
      errorEl.textContent = 'Network error — is the server running?';
    }
  } finally {
    clearTimeout(timeoutId);
    btn.disabled = false;
    btn.textContent = 'Compare Retailers';
  }
});

// ── Excel download ─────────────────────────────────────────────────────────
document.getElementById('download-btn').addEventListener('click', async () => {
  const btn = document.getElementById('download-btn');
  if (btn.disabled) return;

  const errorEl = document.getElementById('form-error');
  errorEl.textContent = '';

  const retailer  = document.getElementById('retailer').value;
  const doors     = parseInt(document.getElementById('doors').value, 10);
  const skus      = parseInt(document.getElementById('skus').value, 10);
  const price     = parseFloat(document.getElementById('unit_price_wholesale').value);
  const cogs      = parseFloat(document.getElementById('cogs_per_unit').value);
  const velocity  = parseFloat(document.getElementById('velocity').value);
  const brokerRaw = document.getElementById('broker_projection').value;
  const broker    = brokerRaw ? parseFloat(brokerRaw) : null;

  if (!doors || !skus || !price || !cogs || !velocity) {
    errorEl.textContent = 'Please fill in all required fields before downloading.';
    return;
  }
  if (cogs >= price) {
    errorEl.textContent = 'COGS must be less than wholesale price.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Generating…';

  const payload = {
    retailer, doors, skus,
    unit_price_wholesale: price,
    cogs_per_unit: cogs,
    velocity_units_per_door_per_week: velocity,
  };
  if (broker !== null) payload.broker_projection_year1 = broker;

  try {
    const res = await fetch('/api/download/excel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = Array.isArray(err.detail)
        ? err.detail.map(d => d.msg).join('; ')
        : (err.detail || `Server error (${res.status})`);
      errorEl.textContent = detail;
      return;
    }

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'retailer-launch-model.xlsx';
    a.click();
    URL.revokeObjectURL(url);

  } catch {
    errorEl.textContent = 'Download failed — please try again.';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Download Excel Model';
  }
});
