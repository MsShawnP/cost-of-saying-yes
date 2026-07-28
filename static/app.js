/* cost-of-saying-yes — main app JS (live model) */

'use strict';

// ── State ──────────────────────────────────────────────────────────────────
let currentData = null;        // all three scenario results from the API
let activeScenario = 'realistic';
let brokerProvided = true;     // did the user enter a broker figure, or is the left column the modeled gross?
let chartInitialized = false;       // tracks whether Plotly.newPlot has been called
let resizeListenerAttached = false; // ensures the resize listener is added exactly once
let calcSeq = 0;                    // monotonic id — drops stale /api/calculate responses

// The Cinderhaven worked example — the tool loads pre-filled with this so it is
// never an empty form. "Reset to example" restores it.
const EXAMPLE_INPUTS = {
  retailer: 'walmart',
  doors: '1200',
  skus: '4',
  unit_price_wholesale: '1.00',
  cogs_per_unit: '0.45',
  velocity: '2.0',
  broker_projection: '499200',
};

const LIVE_INPUT_IDS = [
  'retailer', 'doors', 'skus', 'unit_price_wholesale',
  'cogs_per_unit', 'velocity', 'broker_projection',
];

// ── Retailer context callout ───────────────────────────────────────────────
const RETAILER_CONTEXT = {
  walmart:        'Net-30 payment terms, 12% trade spend in months 1–3, and free fills (1 case/SKU/door) before any revenue arrives.',
  whole_foods:    'No new-store allowances, but $5,000 slotting per SKU is due at listing. UNFI\'s 30-day terms ease the cash cycle relative to Walmart.',
  costco:         'No slotting, low 6% trade spend, 30-day terms — but $3,500/mo operational overhead and 2-unit packs change the per-door economics significantly.',
  regional_chain: 'Lower volume, more forgiving terms: $1,500 slotting per SKU, 8% trade spend, and under 1% steady-state deductions.',
};

function updateRetailerContext(value) {
  const el = document.getElementById('retailer-context');
  if (el) el.textContent = RETAILER_CONTEXT[value] || '';
}

// ── Live-state flag ─────────────────────────────────────────────────────────
function setLive(state) {
  const el = document.getElementById('live-flag');
  if (!el) return;
  el.classList.remove('stale');
  if (state === 'calc') {
    el.textContent = 'Updating…';
  } else if (state === 'offline') {
    el.textContent = 'Couldn’t reach the server — showing last result';
    el.classList.add('stale');
  } else {
    el.textContent = 'Live · updates as you type';
  }
}

// ── Small utilities ─────────────────────────────────────────────────────────
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function setFieldError(fieldId, msg) {
  const el = document.getElementById(`${fieldId}-error`);
  if (el) el.textContent = msg;
}

function clearFieldErrors() {
  document.querySelectorAll('.field-error').forEach(el => { el.textContent = ''; });
}

// ── Fetch helpers (shared by calculate / compare / download) ────────────────
function buildPayload(v, { includeRetailer = true } = {}) {
  const payload = {
    doors: v.doors,
    skus: v.skus,
    unit_price_wholesale: v.price,
    cogs_per_unit: v.cogs,
    velocity_units_per_door_per_week: v.velocity,
  };
  if (includeRetailer) payload.retailer = v.retailer;
  if (v.broker !== null) payload.broker_projection_year1 = v.broker;
  return payload;
}

function parseErrorDetail(errBody, status) {
  return Array.isArray(errBody.detail)
    ? errBody.detail.map(d => d.msg).join('; ')
    : (errBody.detail || `Server error (${status})`);
}

// POST JSON with a 30s abort timeout. Returns { promise, done }; call done() in a
// finally block to clear the timer once the response body has been consumed.
function timedFetch(url, payload) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30_000);
  const promise = fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: controller.signal,
  });
  return { promise, done: () => clearTimeout(timeoutId) };
}

// ── Currency formatters ───────────────────────────────────────────────────
function formatCurrency(n) {
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) {
    const kVal = (abs / 1_000).toFixed(0);
    if (Number(kVal) >= 1000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
    return `${sign}$${kVal}K`;
  }
  return `${sign}$${abs.toFixed(0)}`;
}

function formatTableCurrency(n) {
  const abs = Math.abs(n);
  const s = '$' + abs.toLocaleString('en-US', { maximumFractionDigits: 0 });
  return n < 0 ? '−' + s : s;
}

// ── HTML escaping ─────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ── Verdict hero (the live answer) ──────────────────────────────────────────
function buildVerdictLine(d) {
  const trough = d.trough_value;
  const net    = d.summary.net_cash_impact_year1;
  const broker = d.summary.broker_projection_year1;

  if (trough >= 0) {
    return `This launch never runs cash-negative — no working-capital gap in Year 1. ` +
           `Net Year 1 cash impact lands at <strong>${formatTableCurrency(net)}</strong>.`;
  }

  let s = `You'd need <strong>${formatTableCurrency(Math.abs(trough))}</strong> in working ` +
          `capital to fund this launch — deepest in Month ${d.trough_month}, before the ` +
          `payment terms catch up.`;
  s += d.break_even_month
    ? ` It turns cash-positive by Month ${d.break_even_month}.`
    : ` It does not turn cash-positive within Year 1.`;
  if (brokerProvided) {
    s += ` The ${formatTableCurrency(broker)} projection never shows it.`;
  }
  return s;
}

function updateVerdict(scenario) {
  const d = currentData[scenario];
  const summary = d.summary;

  const brokerLabelEl = document.getElementById('verdict-broker-label');
  const brokerValueEl = document.getElementById('verdict-broker-value');
  const brokerSubEl   = document.getElementById('verdict-broker-sub');
  const troughValueEl = document.getElementById('verdict-trough-value');
  const troughSubEl   = document.getElementById('verdict-trough-sub');
  const lineEl        = document.getElementById('verdict-line');

  // When no broker figure is entered, the left column is the model's OWN gross
  // revenue — label it as such so it is not passed off as an independent number.
  if (brokerProvided) {
    brokerLabelEl.textContent = "Broker's Projection";
    brokerSubEl.textContent = 'Year 1 gross revenue';
  } else {
    brokerLabelEl.textContent = 'Modeled Gross Revenue';
    brokerSubEl.textContent = 'No broker figure entered';
  }
  brokerValueEl.textContent = formatTableCurrency(summary.broker_projection_year1);

  const trough = d.trough_value;
  troughValueEl.textContent = formatTableCurrency(trough);
  troughValueEl.classList.toggle('verdict-value--red', trough < 0);
  troughSubEl.textContent = trough < 0
    ? `Working capital at the trough — Month ${d.trough_month}`
    : 'No working-capital gap in Year 1';

  lineEl.innerHTML = buildVerdictLine(d);
}

// ── Breakeven-velocity sensitivity note ─────────────────────────────────────
// Phrased against the current velocity input. breakeven_velocity is a top-level,
// model-computed figure for the realistic scenario (null if it never breaks even).
function updateSensitivity() {
  const el = document.getElementById('verdict-sensitivity');
  if (!el || !currentData) return;

  const breakeven = currentData.breakeven_velocity;   // number or null
  const current = parseFloat(document.getElementById('velocity').value);

  if (breakeven === null || breakeven === undefined) {
    el.textContent = "Doesn't reach Year-1 breakeven at any plausible velocity.";
    return;
  }

  // Two decimals, matching the API. The model rounds the crossover UP to the
  // nearest cent of velocity precisely so the reported figure itself nets >= 0 —
  // re-rounding to one decimal here throws that away (2.54 -> "2.5", which nets
  // -$2,104) and puts a velocity on screen that does not break even.
  const be = breakeven.toFixed(2);

  // If the velocity box is empty/non-numeric we can't compare against it — state
  // the requirement without a bogus "current" figure. (Guarding the comparison
  // matters: `breakeven > NaN` is always false, which would wrongly fall through
  // to the "stays cash-positive" branch.)
  if (!Number.isFinite(current)) {
    el.textContent = `Needs ~${be} units/door/week to break even in Year 1.`;
    return;
  }

  el.textContent = breakeven > current
    ? `Needs ~${be} units/door/week to break even in Year 1 — above the current ${current.toFixed(1)} assumption.`
    : `Stays cash-positive in Year 1 down to ~${be} units/door/week.`;
}

// ── Dynamic line-item table ───────────────────────────────────────────────
function renderLineItems(scenario) {
  const data = currentData[scenario];
  if (!data || !data.line_items) return;

  const container = document.getElementById('line-items-table');
  const items = data.line_items;
  const net = data.summary.net_cash_impact_year1;

  let html = '<table class="cs-table"><thead><tr>';
  html += '<th>Line Item</th><th class="cs-table-amount">Amount</th>';
  html += '</tr></thead><tbody>';

  items.forEach(item => {
    const cls = item.amount < 0 ? 'cs-negative' : 'cs-positive';
    html += '<tr><td>' + escapeHtml(item.label) + '</td>';
    html += '<td class="cs-table-amount ' + cls + '">' + formatTableCurrency(item.amount) + '</td></tr>';
  });

  const netCls = net < 0 ? 'cs-negative' : 'cs-positive';
  html += '<tr class="cs-table-total"><td><strong>Net Year 1 Cash Impact</strong></td>';
  html += '<td class="cs-table-amount ' + netCls + '"><strong>' + formatTableCurrency(net) + '</strong></td></tr>';

  if (data.trough_value < 0) {
    html += '<tr class="cs-table-total"><td><strong>Peak Cash Trough (Month ' + data.trough_month + ')</strong></td>';
    html += '<td class="cs-table-amount cs-negative"><strong>' + formatTableCurrency(data.trough_value) + '</strong></td></tr>';
  }

  html += '</tbody></table>';
  container.innerHTML = html;
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

  const hasTroughNote = troughValue !== undefined && troughMonth !== undefined && troughValue < 0;

  if (hasTroughNote) {
    annotations.push({
      x: troughMonth, y: troughValue, xref: 'x', yref: 'y',
      text: `Peak trough<br>${formatCurrency(troughValue)}`,
      // Sits BELOW the trough point. Above it is where the point's own data label
      // goes, and the area under the minimum is always empty.
      showarrow: true, arrowhead: 2, arrowsize: 1, arrowwidth: 1.5,
      arrowcolor: '#ffffff', ax: 40, ay: 56,
      bgcolor: '#1a1a1a', bordercolor: 'rgba(255,255,255,0.12)',
      font: { family: 'Source Sans 3, sans-serif', size: 12, color: '#ffffff' },
      borderpad: 6
    });
  }

  return {
    paper_bgcolor: '#f5f3ee',
    plot_bgcolor:  '#f5f3ee',
    // Top margin clears the data labels, which sit above each point. Bottom margin
    // widens when the trough callout is present — it hangs below the lowest point,
    // so 48px of axis area isn't enough to hold it inside the chart.
    margin: { t: 40, r: 24, b: hasTroughNote ? 96 : 48, l: 80 },
    // NO `transition` here. A layout transition makes Plotly.react animate the
    // existing DOM instead of re-rendering it, and it silently skips structural
    // updates: annotations keep their old text (the trough callout would show a
    // stale figure next to fresh point labels) and point labels that were blank
    // at a narrower width are never created. Correct numbers beat a 350ms ease.
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

// Every data point gets a text label — Lailara chart rule. Below ~560px of chart
// width there is not room for twelve of them and they collide into an unreadable
// smear, so label every third month plus the last one. The shape stays readable,
// the endpoints stay exact, and hover still gives every month in full.
function buildPointLabels(values) {
  const el = document.getElementById('cashflow-chart');
  const stride = (el && el.clientWidth >= 560) ? 1 : 3;
  const last = values.length - 1;
  return values.map((v, i) => (i % stride === 0 || i === last) ? formatCurrency(v) : '');
}

function renderChart(scenario) {
  const data = currentData[scenario];
  const trace = {
    x: data.months,
    y: [...data.cumulative_cash_position],
    customdata: data.months.map((_, i) => [
      data.gross_revenue[i],
      data.deductions[i],
      data.cash_received[i],
    ]),
    type: 'scatter',
    // Every data point gets a text label — Lailara chart rule, non-negotiable.
    mode: 'lines+markers+text',
    text: buildPointLabels(data.cumulative_cash_position),
    textposition: 'top center',
    textfont: { family: 'Source Sans 3, sans-serif', size: 11, color: '#333333' },
    cliponaxis: false,
    fill: 'tozeroy',
    fillcolor: 'rgba(31, 46, 122, 0.08)',
    marker: { color: '#1f2e7a', size: 5 },
    line: { color: '#1f2e7a', width: 2.5 },
    hovertemplate:
      'Month %{x}<br>' +
      'Gross revenue: %{customdata[0]:$,.0f}<br>' +
      'Deductions: %{customdata[1]:$,.0f}<br>' +
      'Cash received: %{customdata[2]:$,.0f}<br>' +
      'Cumulative: %{y:$,.0f}' +
      '<extra></extra>',
  };

  const layout = buildLayout(data.break_even_month, data.trough_month, data.trough_value);
  const config = { responsive: true, displaylogo: false, displayModeBar: false };

  let plotPromise;
  if (!chartInitialized) {
    plotPromise = Plotly.newPlot('cashflow-chart', [trace], layout, config);
    chartInitialized = true;
    if (!resizeListenerAttached) {
      // Re-render before resizing: the label stride depends on chart width, and
      // Plotly.Plots.resize alone reuses the trace text computed at the old width.
      window.addEventListener('resize', debounce(() => {
        if (!currentData) return;
        renderChart(activeScenario).then(() => Plotly.Plots.resize('cashflow-chart'));
      }, 150));
      resizeListenerAttached = true;
    }
  } else {
    plotPromise = Plotly.react('cashflow-chart', [trace], layout, config);
  }
  return plotPromise;
}

// ── Scenario switch ────────────────────────────────────────────────────────
function renderScenario(scenario) {
  activeScenario = scenario;
  const chartPromise = renderChart(scenario);
  updateVerdict(scenario);
  updateSensitivity();
  renderLineItems(scenario);

  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.scenario === scenario);
  });

  return chartPromise;
}

// ── Read + validate inputs ──────────────────────────────────────────────────
function readInputs() {
  const retailer  = document.getElementById('retailer').value;
  const doors     = parseInt(document.getElementById('doors').value, 10);
  const skus      = parseInt(document.getElementById('skus').value, 10);
  const price     = parseFloat(document.getElementById('unit_price_wholesale').value);
  const cogs      = parseFloat(document.getElementById('cogs_per_unit').value);
  const velocity  = parseFloat(document.getElementById('velocity').value);
  const brokerRaw = document.getElementById('broker_projection').value;
  const broker    = brokerRaw ? parseFloat(brokerRaw) : null;
  return { retailer, doors, skus, price, cogs, velocity, broker };
}

function validateInputs(v) {
  const errs = [];
  if (!Number.isFinite(v.doors))    errs.push(['doors', 'Required']);
  if (!Number.isFinite(v.skus))     errs.push(['skus', 'Required']);
  if (!Number.isFinite(v.price))    errs.push(['unit_price_wholesale', 'Required']);
  if (!Number.isFinite(v.cogs))     errs.push(['cogs_per_unit', 'Required']);
  if (!Number.isFinite(v.velocity)) errs.push(['velocity', 'Required']);
  if (errs.length) return errs;
  if (v.cogs >= v.price) return [['cogs_per_unit', 'COGS must be less than wholesale price.']];
  return null;
}

// ── Core: run the model and render everything ───────────────────────────────
async function runCalculation({ source }) {
  const silent = source === 'live' || source === 'load';
  const errorEl = document.getElementById('form-error');
  clearFieldErrors();
  errorEl.textContent = '';

  const inputs = readInputs();
  const errs = validateInputs(inputs);
  if (errs) {
    errs.forEach(([field, msg]) => setFieldError(field, msg));
    if (!silent) errorEl.textContent = 'Please fix the highlighted fields.';
    setLive('live');
    return;   // keep the last good chart/verdict on screen
  }

  brokerProvided = inputs.broker !== null;
  setLive('calc');

  const payload = buildPayload(inputs);
  const seq = ++calcSeq;                 // this call's ticket
  const req = timedFetch('/api/calculate', payload);

  try {
    const res = await req.promise;
    if (seq !== calcSeq) return;         // a newer request superseded this one

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      if (seq !== calcSeq) return;
      const detail = parseErrorDetail(err, res.status);
      if (res.status === 422) {          // input out of range — show it, stay live
        errorEl.textContent = detail;
        setLive('live');
      } else if (silent) {
        setLive('offline');
      } else {
        errorEl.textContent = detail;
        setLive('live');
      }
      return;
    }

    const data = await res.json();
    if (seq !== calcSeq) return;         // don't let a stale reply overwrite fresh state
    currentData = data;
    document.getElementById('results-panel').classList.add('visible');
    await renderScenario(activeScenario);
    setLive('live');

  } catch (err) {
    if (seq !== calcSeq) return;         // stale failure — a newer request owns the UI
    if (silent) {
      setLive('offline');
    } else {
      errorEl.textContent = (err.name === 'AbortError')
        ? 'Request timed out — the server may be starting up. Please try again.'
        : 'Network error — is the server running?';
      setLive('live');
    }
  } finally {
    req.done();
  }
}

const debouncedRun = debounce(() => runCalculation({ source: 'live' }), 350);

// ── Tab switching ────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.page-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  const pane = document.getElementById('tab-' + name);
  if (pane) pane.classList.add('active');
  if (name === 'model' && chartInitialized && window.Plotly) {
    Plotly.Plots.resize('cashflow-chart');
  }
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  updateRetailerContext(document.getElementById('retailer').value);

  document.querySelectorAll('.page-tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  const csRun = document.getElementById('cs-run-btn');
  if (csRun) csRun.addEventListener('click', () => {
    switchTab('model');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // Reactive inputs — recompute live on any change
  LIVE_INPUT_IDS.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const evt = el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(evt, () => {
      if (id === 'retailer') updateRetailerContext(el.value);
      debouncedRun();
    });
  });

  // Reset to the Cinderhaven example
  const resetBtn = document.getElementById('reset-btn');
  if (resetBtn) resetBtn.addEventListener('click', () => {
    Object.entries(EXAMPLE_INPUTS).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el) el.value = val;
    });
    updateRetailerContext(document.getElementById('retailer').value);
    clearFieldErrors();
    document.getElementById('form-error').textContent = '';
    activeScenario = 'realistic';   // the canonical example is the realistic case
    runCalculation({ source: 'live' });
  });

  // Enter key inside the form triggers an explicit recompute
  document.getElementById('input-form').addEventListener('submit', (e) => {
    e.preventDefault();
    runCalculation({ source: 'submit' });
  });

  // Scenario toggle
  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.addEventListener('click', () => {
      if (currentData) renderScenario(btn.dataset.scenario);
    });
  });

  // Hydrate on load — the verdict card already shows the example numbers, so a
  // slow/cold server never leaves the user staring at nothing.
  runCalculation({ source: 'load' });
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
  document.getElementById('compare-section').classList.add('visible');
}

document.getElementById('compare-btn').addEventListener('click', async () => {
  const btn = document.getElementById('compare-btn');
  if (btn.disabled) return;

  const errorEl = document.getElementById('form-error');
  errorEl.textContent = '';

  const v = readInputs();
  if (validateInputs(v)) {
    errorEl.textContent = 'Please fill in all required fields before comparing.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Comparing…';
  const coldStartId = setTimeout(() => {
    if (btn.disabled) btn.textContent = 'Comparing… (first load may take a moment)';
  }, 2_000);

  const payload = buildPayload(v, { includeRetailer: false });
  const req = timedFetch('/api/compare', payload);

  try {
    const res = await req.promise;
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      errorEl.textContent = parseErrorDetail(err, res.status);
      return;
    }
    renderCompareTable(await res.json());

  } catch (err) {
    errorEl.textContent = (err.name === 'AbortError')
      ? 'Request timed out — please try again.'
      : 'Network error — is the server running?';
  } finally {
    req.done();
    clearTimeout(coldStartId);
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
  clearFieldErrors();

  const v = readInputs();
  const errs = validateInputs(v);
  if (errs) {
    errs.forEach(([field, msg]) => setFieldError(field, msg));
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Generating…';

  const payload = buildPayload(v);
  const req = timedFetch('/api/download/excel', payload);

  try {
    const res = await req.promise;
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      errorEl.textContent = parseErrorDetail(err, res.status);
      return;
    }

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'retailer-launch-model.xlsx';
    a.click();
    URL.revokeObjectURL(url);

  } catch (err) {
    errorEl.textContent = (err.name === 'AbortError')
      ? 'Request timed out — please try again.'
      : 'Download failed — please try again.';
  } finally {
    req.done();
    btn.disabled = false;
    btn.textContent = 'Download Excel Model';
  }
});
