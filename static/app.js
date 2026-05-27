/* cost-of-saying-yes — main app JS */

'use strict';

// ── State ──────────────────────────────────────────────────────────────────
let currentData = null;        // all three scenario results from the API
let activeScenario = 'realistic';

// ── Currency formatter ─────────────────────────────────────────────────────
function formatCurrency(n) {
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000)     return `${sign}$${(abs / 1_000).toFixed(0)}K`;
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

  if (troughValue !== undefined && troughMonth !== undefined) {
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

  if (!currentData._chartInitialized) {
    Plotly.newPlot('cashflow-chart', [trace], layout, config);
    currentData._chartInitialized = true;
    window.addEventListener('resize', () => Plotly.Plots.resize('cashflow-chart'));
  } else {
    Plotly.react('cashflow-chart', [trace], layout, config);
  }
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
  renderChart(scenario);
  updateComparisonPanel(scenario);

  // Update toggle button states
  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.scenario === scenario);
  });
}

// ── Form submission ────────────────────────────────────────────────────────
document.getElementById('input-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('calculate-btn');
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

  try {
    const res = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      errorEl.textContent = err.detail?.[0]?.msg || `Server error (${res.status})`;
      return;
    }

    currentData = await res.json();
    currentData._chartInitialized = false;

    // Show results panel
    const panel = document.getElementById('results-panel');
    panel.classList.add('visible');

    // Enable scenario buttons
    document.querySelectorAll('.btn-scenario').forEach(b => b.disabled = false);

    // Render default scenario
    renderScenario('realistic');

    // Smooth scroll to results
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    errorEl.textContent = 'Network error — is the server running?';
  } finally {
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
