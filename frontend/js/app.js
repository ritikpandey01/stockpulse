// Core Application Logic & Routing

let currentChart = null;

// Routing
function navigate(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    document.getElementById(`page-${pageId}`).classList.add('active');
    const link = document.querySelector(`.nav-link[data-page="${pageId}"]`);
    if (link) link.classList.add('active');

    // Trigger page-specific loads
    if (pageId === 'home') loadRecommendations();
    if (pageId === 'admin') loadAdminDashboard();
}

function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');
}

// User Actions
function searchFromHero() {
    const symbol = document.getElementById('hero-search').value.trim();
    if (!symbol) return;

    document.getElementById('analyze-search').value = symbol;
    navigate('analyze');
    runAnalysis();
}

function analyzeSpecificStock(symbol) {
    document.getElementById('analyze-search').value = symbol;
    navigate('analyze');
    runAnalysis();
}

// === Data Fetching and Rendering ===

async function loadRecommendations() {
    const grid = document.getElementById('recommendations-grid');
    const sectors = document.getElementById('sector-movers');

    if (grid.children.length > 1) return; // Already loaded

    try {
        const data = await api.get('/recommendations');

        // Render Top Picks
        grid.innerHTML = data.top_picks.map(pick => `
            <div class="glass-card stock-card" onclick="analyzeSpecificStock('${pick.symbol}')">
                <div class="stock-card-header">
                    <h3>${pick.symbol}</h3>
                    <span class="stock-badge badge-${pick.signal.toLowerCase().replace(' ', '-')}">${pick.signal}</span>
                </div>
                <div class="stock-card-price">$${pick.price}</div>
                <div class="text-${pick.return_5d >= 0 ? 'success' : 'danger'} text-sm">
                    ${pick.return_5d >= 0 ? '▲' : '▼'} ${Math.abs(pick.return_5d)}% (5D)
                </div>
                <div class="metrics-row" style="margin-top:0.5rem; gap:0.5rem">
                    <div class="text-muted text-sm">Score: <span class="text-main font-mono">${pick.score}/100</span></div>
                    <div class="text-muted text-sm">Trend: <span class="text-main">${pick.trend}</span></div>
                </div>
            </div>
        `).join('');

        // Render Sectors
        sectors.innerHTML = data.sector_movers.map(s => `
            <div class="glass-card" style="padding:1rem">
                <div style="font-weight:600; margin-bottom:0.5rem">${s.sector} <span class="text-muted">(${s.etf})</span></div>
                <div class="text-${s.change >= 0 ? 'success' : 'danger'} font-mono font-bold">
                    ${s.change >= 0 ? '+' : ''}${s.change}%
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error(err);
        grid.innerHTML = `<p class="text-danger">Failed to load recommendations.</p>`;
    }
}


// ========== PROGRESSIVE ANALYSIS ==========

async function runAnalysis() {
    const symbol = document.getElementById('analyze-search').value.trim();
    if (!symbol) return;

    const period = document.getElementById('period-select').value;
    const interval = document.getElementById('interval-select').value;

    // UI states: show loading
    document.getElementById('analyze-results').classList.add('hidden');
    document.getElementById('analyze-loading').classList.remove('hidden');

    try {
        // ===== PHASE 1: Fast — chart, signals, indicators (instant) =====
        const res = await api.post('/analyze', { symbol, period, interval });

        // Hide loading, show results
        document.getElementById('analyze-loading').classList.add('hidden');
        document.getElementById('analyze-results').classList.remove('hidden');

        renderPhase1(res);

        // ===== PHASE 2: Heavy — ML prediction + risk (async in background) =====
        // Add spinners to the Prediction and Risk tabs
        addTabSpinner('prediction');
        addTabSpinner('risk');

        // Fire ML request in background
        const mlReq = { symbol, period, interval, timeframe: '1d' };
        loadMLResults(mlReq);

        // ===== PHASE 3: Sentiment (also async) =====
        loadSentiment(symbol);

        // Save search history in background
        api.post('/history', {
            symbol, analysis_type: 'Full',
            summary: { signals: res.signals?.overall }
        }).catch(e => console.log(e));

    } catch (err) {
        alert("Analysis failed: " + err.message);
        document.getElementById('analyze-loading').classList.add('hidden');
    }
}

// ========== PHASE 1 RENDER (instant) ==========

function renderPhase1(data) {
    // 1. Stock Header
    const colorClass = data.price_change >= 0 ? 'text-success' : 'text-danger';
    const sign = data.price_change >= 0 ? '+' : '';
    document.getElementById('stock-header').innerHTML = `
        <div>
            <h1>${data.symbol} <span class="text-muted text-lg">${data.info.name}</span></h1>
            <div class="text-muted">${data.info.sector} • ${data.info.industry}</div>
        </div>
        <div class="stock-price-main">
            <div class="price">$${data.current_price}</div>
            <div class="change ${colorClass}">${sign}${data.price_change}%</div>
        </div>
    `;

    // 2. Candlestick Chart
    if (window.renderChart) {
        window.renderChart('chart-container', data.chart_data);
    }

    // 3. Support/Resistance
    const sr = data.support_resistance;
    document.getElementById('support-resistance').innerHTML = `
        <div class="metric-box"><div class="label">Resistance (R1)</div><div class="value">$${sr.r1 || '-'}</div></div>
        <div class="metric-box"><div class="label">Pivot Point</div><div class="value">$${sr.pivot || '-'}</div></div>
        <div class="metric-box"><div class="label">Support (S1)</div><div class="value">$${sr.s1 || '-'}</div></div>
    `;

    // 4. Indicator mini-charts
    if (window.renderIndicatorCharts && data.indicator_data) {
        window.renderIndicatorCharts(data.indicator_data);
    }

    // 5. Trading Signals
    const sig = data.signals;
    const overallColor = sig.overall.includes('Buy') ? 'text-success' : (sig.overall.includes('Sell') ? 'text-danger' : 'text-warning');
    document.getElementById('signals-content').innerHTML = `
        <div class="glass-card">
            <h2 style="margin-bottom:1.5rem">Trading Signal Analysis</h2>
            <div class="metrics-row">
                <div class="metric-box"><div class="label">Overall Signal</div><div class="value ${overallColor}">${sig.overall}</div></div>
                <div class="metric-box"><div class="label">Strength Score</div><div class="value font-mono">${sig.score}</div></div>
            </div>
            <div class="metrics-row">
                <div class="metric-box"><div class="label">MACD</div><div class="value">${sig.macd}</div></div>
                <div class="metric-box"><div class="label">RSI</div><div class="value">${sig.rsi.value} <span class="text-sm">(${sig.rsi.signal})</span></div></div>
                <div class="metric-box"><div class="label">Bollinger Bands</div><div class="value">${sig.bollinger}</div></div>
                <div class="metric-box"><div class="label">Volume</div><div class="value">${sig.volume}</div></div>
                ${sig.mfi !== null ? `<div class="metric-box"><div class="label">Money Flow Index</div><div class="value">${sig.mfi}</div></div>` : ''}
            </div>
        </div>

        <div class="glass-card" style="margin-top:1.25rem">
            <h3>Expert Risk Assessment (Rule-Based)</h3>
            <div class="metrics-row">
                <div class="metric-box">
                    <div class="label">Risk Level</div>
                    <div class="value ${data.expert_risk.class === 'HIGH' ? 'text-danger' : (data.expert_risk.class === 'MEDIUM' ? 'text-warning' : 'text-success')}">${data.expert_risk.class}</div>
                </div>
                <div class="metric-box"><div class="label">Score</div><div class="value font-mono">${data.expert_risk.score}/100</div></div>
            </div>
            <ul style="margin-top:1rem; padding-left:1.5rem; color:var(--text-muted)">
                ${data.expert_risk.factors.map(f => `<li style="margin-bottom:0.5rem">${f}</li>`).join('')}
            </ul>
        </div>
    `;

    // 6. Performance Metrics
    const perf = data.performance;
    document.getElementById('performance-metrics').innerHTML = `
        <h3>Historical Performance Metrics</h3>
        <div class="metrics-row">
            <div class="metric-box"><div class="label">Volatility (Ann.)</div><div class="value">${perf.volatility}%</div></div>
            <div class="metric-box"><div class="label">Sharpe Ratio</div><div class="value">${perf.sharpe_ratio}</div></div>
            <div class="metric-box"><div class="label">Max Drawdown</div><div class="value text-danger">${perf.max_drawdown}%</div></div>
        </div>
    `;

    // Reset ML loading content (in case of re-analysis)
    resetMLTabs();
}


// ========== PHASE 2: ASYNC ML LOADING ==========

async function loadMLResults(req) {
    // Step animation
    setTimeout(() => animateStep('ml-step-1', 'done'), 400);
    setTimeout(() => animateStep('ml-step-2', 'active'), 600);

    try {
        const mlRes = await api.post('/analyze/ml', req);

        // Mark steps done
        animateStep('ml-step-2', 'done');
        animateStep('ml-step-3', 'done');

        // Remove spinners from tabs
        removeTabSpinner('prediction');
        removeTabSpinner('risk');

        // Render prediction
        renderPrediction(mlRes);

        // Render risk
        renderRisk(mlRes);

        // Update history with prediction data
        api.post('/history', {
            symbol: req.symbol, analysis_type: 'ML',
            summary: { prediction: mlRes.prediction?.direction, risk: mlRes.risk?.risk_class }
        }).catch(e => console.log(e));

    } catch (err) {
        console.error('ML analysis failed:', err);
        removeTabSpinner('prediction');
        removeTabSpinner('risk');
        document.getElementById('prediction-content').innerHTML = `
            <div class="glass-card"><p class="text-danger">⚠️ ML prediction failed: ${err.message}</p>
            <p class="text-muted" style="margin-top:0.5rem">The rule-based signals in the Signals tab are still available.</p></div>`;
        document.getElementById('risk-content').innerHTML = `
            <div class="glass-card"><p class="text-danger">⚠️ Risk analysis failed: ${err.message}</p></div>`;
    }
}

function renderPrediction(mlRes) {
    if (mlRes.prediction) {
        const p = mlRes.prediction;
        const color = p.direction === "UP" ? 'text-success' : 'text-danger';
        const arrow = p.direction === "UP" ? '↑' : '↓';
        const word = p.direction === "UP" ? 'Upside' : 'Downside';
        document.getElementById('prediction-content').innerHTML = `
            <div class="glass-card risk-gauge-container">
                <h2 style="margin-bottom:1rem">🤖 Machine Learning Prediction</h2>
                <div class="risk-class ${color}">${arrow} Projected ${word}</div>
                <div class="metrics-row">
                    <div class="metric-box"><div class="label">Predicted Price</div><div class="value">$${p.predicted_price}</div></div>
                    <div class="metric-box"><div class="label">Current Price</div><div class="value">$${p.current_price}</div></div>
                    <div class="metric-box"><div class="label">Expected Change</div><div class="value ${color}">${p.change_percent > 0 ? '+' : ''}${p.change_percent}%</div></div>
                </div>
                ${mlRes.prediction_logged ? `<div style="margin-top:1.5rem" class="text-success text-sm">✅ Prediction logged to Accuracy Tracker</div>` : ''}
            </div>
        `;
    } else {
        document.getElementById('prediction-content').innerHTML = `
            <div class="glass-card">
                <h3>🤖 ML Prediction</h3>
                <p class="text-muted" style="margin-top:1rem">Insufficient data for prediction modeling. Try selecting a longer historical period.</p>
            </div>`;
    }
}

function renderRisk(mlRes) {
    if (mlRes.risk) {
        const r = mlRes.risk;
        let cClass = r.risk_class === "HIGH" ? "text-danger" : (r.risk_class === "MEDIUM" ? "text-warning" : "text-success");
        let fillStyle = r.risk_class === "HIGH" ? "background:#EF4444" : (r.risk_class === "MEDIUM" ? "background:#F59E0B" : "background:#10B981");

        document.getElementById('risk-content').innerHTML = `
            <div class="glass-card risk-gauge-container" style="margin-bottom:1.5rem">
                <h2>Ensemble Risk Assessment</h2>
                <div class="risk-class ${cClass}">${r.risk_class} RISK</div>
                <div class="risk-score">Score: ${r.risk_score} / 100</div>
                <div class="risk-meter"><div class="risk-fill" style="width:${r.risk_score}%; ${fillStyle}"></div></div>
                <p>Downside Probability: <strong>${r.downside_prob}%</strong></p>
            </div>

            <div class="glass-card">
                <h3>ML Model Explanations</h3>
                <ul style="margin-top:1rem; padding-left:1.5rem">
                    ${r.explanation.map(f => `<li style="margin-bottom:0.5rem">${f}</li>`).join('')}
                </ul>
            </div>

            ${r.model_votes ? `
            <div class="glass-card" style="margin-top:1.25rem">
                <h3>Model Votes</h3>
                <div class="metrics-row" style="margin-top:1rem">
                    ${Object.entries(r.model_votes).map(([name, vote]) => `
                        <div class="metric-box">
                            <div class="label">${name}</div>
                            <div class="value text-sm ${vote === 'HIGH' ? 'text-danger' : (vote === 'MEDIUM' ? 'text-warning' : 'text-success')}">${vote}</div>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
        `;
    } else {
        document.getElementById('risk-content').innerHTML = `
            <div class="glass-card">
                <h3>⚠️ Ensemble Risk</h3>
                <p class="text-muted" style="margin-top:1rem">Insufficient data for risk modeling. Try a longer historical period.</p>
            </div>`;
    }
}


// ========== ML TAB HELPERS ==========

function resetMLTabs() {
    // Reset step loader for prediction
    document.querySelectorAll('#prediction-content .step-item').forEach(el => {
        el.className = 'step-item';
    });
    const s1 = document.getElementById('ml-step-1');
    if (s1) s1.classList.add('active');

    // Reset risk loading
    document.querySelectorAll('#risk-content .step-item').forEach(el => {
        el.className = 'step-item active';
    });
}

function animateStep(stepId, state) {
    const el = document.getElementById(stepId);
    if (!el) return;
    el.className = `step-item ${state}`;
}

function addTabSpinner(tabId) {
    const tab = document.querySelector(`.tab[data-tab="${tabId}"]`);
    if (tab && !tab.querySelector('.tab-spinner')) {
        const spinner = document.createElement('span');
        spinner.className = 'tab-spinner';
        tab.appendChild(spinner);
    }
}

function removeTabSpinner(tabId) {
    const tab = document.querySelector(`.tab[data-tab="${tabId}"]`);
    if (tab) {
        const spinner = tab.querySelector('.tab-spinner');
        if (spinner) spinner.remove();
    }
}


// ========== SENTIMENT (async) ==========

async function loadSentiment(symbol) {
    const loading = document.getElementById('sentiment-loading');
    const content = document.getElementById('sentiment-content');
    loading.classList.remove('hidden');
    content.classList.add('hidden');

    try {
        const data = await api.get(`/sentiment/${symbol}`);
        const sent = data.sentiment;

        let cClass = sent.score > 60 ? "text-success" : (sent.score < 40 ? "text-danger" : "text-warning");
        let fillStyle = sent.score > 60 ? "background:#10B981" : (sent.score < 40 ? "background:#EF4444" : "background:#F59E0B");

        content.innerHTML = `
            <div class="glass-card risk-gauge-container" style="margin-bottom:1.5rem">
                <h2>AI News Sentiment Analysis</h2>
                <div class="risk-class ${cClass}">${sent.mood}</div>
                <div class="risk-score">Greed/Fear Score: ${sent.score} / 100 <span class="text-sm">(${sent.confidence}% confidence)</span></div>
                <div class="risk-meter"><div class="risk-fill" style="width:${sent.score}%; ${fillStyle}"></div></div>
                <p class="text-muted" style="margin-top:1rem">${sent.summary}</p>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem;">
                <div class="glass-card">
                    <h3>Key Sentiment Factors</h3>
                    <ul style="margin-top:1rem; padding-left:1.5rem">
                        ${sent.key_factors.map(f => `<li style="margin-bottom:0.5rem">${f}</li>`).join('')}
                    </ul>
                </div>
                <div class="glass-card">
                    <h3>Recent Top Articles</h3>
                    <div style="margin-top:1rem; display:flex; flex-direction:column; gap:1rem;">
                        ${data.articles.map(a => `
                            <div>
                                <a href="${a.url}" target="_blank" style="color:var(--accent); text-decoration:none; font-weight:600">${a.title}</a>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        loading.classList.add('hidden');
        content.classList.remove('hidden');
    } catch (e) {
        loading.innerHTML = `<p class="text-danger">Failed to load sentiment: ${e.message}</p>`;
    }
}


// ========== INITIAL LOAD ==========

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    // Enter key triggers analyze
    document.getElementById('hero-search').addEventListener('keydown', e => {
        if (e.key === 'Enter') searchFromHero();
    });
    document.getElementById('analyze-search').addEventListener('keydown', e => {
        if (e.key === 'Enter') runAnalysis();
    });

    if (document.location.hash) {
        const p = document.location.hash.substring(1);
        navigate(p);
    } else {
        navigate('home');
    }
});
