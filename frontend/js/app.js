// =========================================================
// StockPulse v3.0 — Unified Analysis Application Logic
// =========================================================

let currentChart = null;
let currentAnalyzeSymbol = '';

// ========== NAVIGATION ==========
function navigate(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));

    const page = document.getElementById(`page-${pageId}`);
    if (page) page.classList.add('active');

    const link = document.querySelector(`.nav-item[data-page="${pageId}"]`);
    if (link) link.classList.add('active');

    // Update header title
    const titles = {
        dashboard: '📊 Dashboard',
        analyze: '🔍 Analyze',
        screener: '🎯 Stock Screener',
        compare: '⚖️ Compare Stocks',
        admin: '👑 Admin Panel',
    };
    document.getElementById('page-title').textContent = titles[pageId] || 'StockPulse';

    // Trigger page-specific loads
    if (pageId === 'dashboard') loadDashboard();
    if (pageId === 'admin') loadAdminDashboard();
}

function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

    const tab = document.querySelector(`.tab[data-tab="${tabId}"]`);
    const panel = document.getElementById(`tab-${tabId}`);
    if (tab) tab.classList.add('active');
    if (panel) panel.classList.add('active');

    // Lazy load data for certain tabs
    if (tabId === 'fundamentals' && currentAnalyzeSymbol) {
        loadFundamentals(currentAnalyzeSymbol);
    }
    if (tabId === 'data' && currentAnalyzeSymbol) {
        loadDataStats(currentAnalyzeSymbol);
    }
}

// ========== USER ACTIONS ==========
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

// Global search
function handleGlobalSearch(e) {
    if (e.key === 'Enter') {
        const val = e.target.value.trim();
        if (val) {
            document.getElementById('analyze-search').value = val;
            navigate('analyze');
            runAnalysis();
            e.target.value = '';
        }
    }
}

// ========== DASHBOARD ==========
let dashboardLoaded = false;

function loadDashboard() {
    if (!dashboardLoaded) {
        loadMarketOverview();
        loadRecommendations();
        dashboardLoaded = true;
    }
}

async function loadMarketOverview() {
    try {
        const data = await api.get('/market/overview');

        // Indices
        const grid = document.getElementById('indices-grid');
        if (data.indices && data.indices.length > 0) {
            grid.innerHTML = data.indices.map(idx => `
                <div class="glass-card index-card">
                    <div class="index-name">${idx.name}</div>
                    <div class="index-value">${idx.value.toLocaleString()}</div>
                    <div class="index-change ${idx.change >= 0 ? 'text-success' : 'text-danger'}">
                        ${idx.change >= 0 ? '▲' : '▼'} ${Math.abs(idx.change)}%
                    </div>
                </div>
            `).join('');
        } else {
            grid.innerHTML = '<p class="text-muted">Market data loading...</p>';
        }

        // Fear & Greed
        const fgContainer = document.getElementById('fear-greed-container');
        if (data.fear_greed) {
            const fg = data.fear_greed;
            const fgColor = fg.score >= 55 ? 'text-success' : fg.score <= 45 ? 'text-danger' : 'text-warning';
            fgContainer.innerHTML = `
                <h3 style="margin-bottom:1rem;">Fear & Greed Index</h3>
                <div class="fg-score ${fgColor}">${fg.score}</div>
                <div class="fg-label ${fgColor}">${fg.label}</div>
                <div class="fg-meter"><div class="fg-needle" style="left:${fg.score}%;"></div></div>
                <div class="text-muted text-sm" style="margin-top:1rem; text-align:left;">
                    ${fg.factors.map(f => `<div style="margin-bottom:0.3rem;">• ${f}</div>`).join('')}
                </div>
            `;
        }

        // Sector Heatmap
        const heatmap = document.getElementById('sector-heatmap');
        if (data.sectors && data.sectors.length > 0) {
            heatmap.innerHTML = data.sectors.map(s => {
                const intensity = Math.min(Math.abs(s.change_1d) * 30, 100);
                const bg = s.change_1d >= 0
                    ? `rgba(0, 230, 138, ${intensity / 100 * 0.4})`
                    : `rgba(255, 77, 106, ${intensity / 100 * 0.4})`;
                return `
                    <div class="heatmap-cell" style="background:${bg};">
                        <div class="sector-name">${s.sector}</div>
                        <div class="sector-change">${s.change_1d >= 0 ? '+' : ''}${s.change_1d}%</div>
                    </div>
                `;
            }).join('');
        }
    } catch (err) {
        console.error('Market overview error:', err);
        document.getElementById('indices-grid').innerHTML = '<p class="text-muted">Unable to load market data.</p>';
    }
}

async function loadRecommendations(force = false) {
    const grid = document.getElementById('recommendations-grid');
    if (!force && grid.children.length > 1) return;

    try {
        const data = await api.get('/recommendations');

        grid.innerHTML = data.top_picks.map(pick => `
            <div class="glass-card interactive stock-card" onclick="analyzeSpecificStock('${pick.symbol}')">
                <div class="stock-card-header">
                    <div>
                        <div class="stock-card-symbol">${pick.symbol}</div>
                    </div>
                    <span class="stock-badge badge-${pick.signal.toLowerCase().replace(' ', '-')}">${pick.signal}</span>
                </div>
                <div class="stock-card-price">$${pick.price}</div>
                <div class="text-${pick.return_5d >= 0 ? 'success' : 'danger'} text-sm">
                    ${pick.return_5d >= 0 ? '▲' : '▼'} ${Math.abs(pick.return_5d)}% (5D)
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--text-muted);">
                    <span>Score: <span class="font-mono text-main">${pick.score}</span></span>
                    <span>RSI: <span class="font-mono text-main">${pick.rsi}</span></span>
                    <span>${pick.trend}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
        grid.innerHTML = '<p class="text-danger">Failed to load recommendations.</p>';
    }
}

// ========== PROGRESSIVE ANALYSIS ==========
async function runAnalysis() {
    const symbol = document.getElementById('analyze-search').value.trim().toUpperCase();
    if (!symbol) return;
    currentAnalyzeSymbol = symbol;

    const period = document.getElementById('period-select').value;
    const interval = document.getElementById('interval-select').value;

    document.getElementById('analyze-results').classList.add('hidden');
    document.getElementById('analyze-loading').classList.remove('hidden');

    // Reset lazy-load flags
    window._fundamentalsLoaded = false;
    window._dataStatsLoaded = false;

    try {
        // PHASE 1: Fast (rule-based)
        const res = await api.post('/analyze', { symbol, period, interval });

        document.getElementById('analyze-loading').classList.add('hidden');
        document.getElementById('analyze-results').classList.remove('hidden');

        renderPhase1(res);

        // PHASE 2: ML (async — updates verdict when done)
        addTabSpinner('prediction');
        loadMLResults({ symbol, period, interval, timeframe: '1d' });

        // PHASE 3: Sentiment (async — feeds into verdict)
        loadSentimentForVerdict(symbol);

        // Save history
        api.post('/history', {
            symbol, analysis_type: 'Full',
            summary: { verdict: res.unified_verdict?.verdict_label }
        }).catch(() => {});

    } catch (err) {
        alert('Analysis failed: ' + err.message);
        document.getElementById('analyze-loading').classList.add('hidden');
    }
}

// ========== PHASE 1 RENDER ==========
function renderPhase1(data) {
    const colorClass = data.price_change >= 0 ? 'text-success' : 'text-danger';
    const sign = data.price_change >= 0 ? '+' : '';

    document.getElementById('stock-header').innerHTML = `
        <div>
            <h1>${data.symbol} <span class="text-muted text-lg">${data.info.name}</span></h1>
            <div class="text-muted text-sm">${data.info.sector} • ${data.info.industry}</div>
        </div>
        <div class="stock-price-main">
            <div class="price">$${data.current_price}</div>
            <div class="change ${colorClass}">${sign}${data.price_change}%</div>
        </div>
    `;

    // Unified Verdict (Phase 1 — rule-based only, will update when ML arrives)
    renderUnifiedVerdict(data.unified_verdict, false);

    // Chart
    try {
        if (window.renderChart) window.renderChart('chart-container', data.chart_data);
    } catch (e) {
        console.error("Chart render error:", e);
    }

    // Support / Resistance
    try {
        const sr = data.support_resistance;
        document.getElementById('support-resistance').innerHTML = `
            <div class="metric-box"><div class="label">Resistance (R1)</div><div class="value">$${sr.r1 || '-'}</div></div>
            <div class="metric-box"><div class="label">Pivot Point</div><div class="value">$${sr.pivot || '-'}</div></div>
            <div class="metric-box"><div class="label">Support (S1)</div><div class="value">$${sr.s1 || '-'}</div></div>
        `;
    } catch (e) {
        console.error("Support/Resistance error:", e);
    }

    // Indicators
    try {
        if (window.renderIndicatorCharts && data.indicator_data) {
            window.renderIndicatorCharts(data.indicator_data);
        }
    } catch (e) {
        console.error("Indicators render error:", e);
    }

    // Signals detail (in Technical tab)
    try {
        const sig = data.signals;
        const overallColor = sig.overall.includes('Buy') ? 'text-success' : (sig.overall.includes('Sell') ? 'text-danger' : 'text-warning');
        document.getElementById('signals-detail').innerHTML = `
        <div class="glass-card">
            <h2 style="margin-bottom:1.5rem">Signal Breakdown</h2>
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
            <h3>Risk Factors (Rule-Based)</h3>
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
    } catch (e) {
        console.error("Signals render error:", e);
    }

    // Performance
    try {
        const perf = data.performance;
        document.getElementById('performance-metrics').innerHTML = `
            <h3>Historical Performance Metrics</h3>
            <div class="metrics-row">
                <div class="metric-box"><div class="label">Volatility (Ann.)</div><div class="value">${perf.volatility}%</div></div>
                <div class="metric-box"><div class="label">Sharpe Ratio</div><div class="value">${perf.sharpe_ratio}</div></div>
                <div class="metric-box"><div class="label">Max Drawdown</div><div class="value text-danger">${perf.max_drawdown}%</div></div>
            </div>
        `;
    } catch (e) {
        console.error("Performance render error:", e);
    }

    resetMLTabs();
}


// ========== UNIFIED VERDICT RENDERER ==========
function renderUnifiedVerdict(verdict, isFinal = false) {
    if (!verdict) return;

    const section = document.getElementById('unified-verdict-section');

    // Determine colors based on direction
    const directionColors = {
        'Strong Bullish': { color: '#00E68A', bg: 'rgba(0, 230, 138, 0.08)', glow: 'rgba(0, 230, 138, 0.3)' },
        'Bullish': { color: '#00E68A', bg: 'rgba(0, 230, 138, 0.06)', glow: 'rgba(0, 230, 138, 0.2)' },
        'Slightly Bullish': { color: '#7DEFA5', bg: 'rgba(0, 230, 138, 0.04)', glow: 'rgba(0, 230, 138, 0.15)' },
        'Neutral': { color: '#FFB020', bg: 'rgba(255, 176, 32, 0.06)', glow: 'rgba(255, 176, 32, 0.2)' },
        'Slightly Bearish': { color: '#FF8A9B', bg: 'rgba(255, 77, 106, 0.04)', glow: 'rgba(255, 77, 106, 0.15)' },
        'Bearish': { color: '#FF4D6A', bg: 'rgba(255, 77, 106, 0.06)', glow: 'rgba(255, 77, 106, 0.2)' },
        'Strong Bearish': { color: '#FF4D6A', bg: 'rgba(255, 77, 106, 0.08)', glow: 'rgba(255, 77, 106, 0.3)' },
    };

    const colors = directionColors[verdict.verdict_label] || directionColors['Neutral'];
    const verdictEmoji = verdict.score > 20 ? '🟢' : (verdict.score < -20 ? '🔴' : '🟡');

    // Gauge position: score -100..+100 => 0%..100%
    const gaugePercent = Math.max(0, Math.min(100, (verdict.score + 100) / 2));

    // Component breakdown
    let componentsHTML = '';
    if (verdict.components && Object.keys(verdict.components).length > 0) {
        const componentNames = {
            'technical': '📊 Technical',
            'ml_prediction': '🤖 ML Prediction',
            'ensemble_risk': '⚠️ Risk Assessment',
            'sentiment': '📰 Sentiment',
        };
        componentsHTML = Object.entries(verdict.components).map(([key, comp]) => {
            const dirColor = comp.direction === 'Bullish' ? 'var(--success)' : (comp.direction === 'Bearish' ? 'var(--danger)' : 'var(--warning)');
            const barWidth = Math.abs(comp.score);
            const barLeft = comp.score >= 0;
            return `
                <div class="verdict-component">
                    <div class="verdict-comp-header">
                        <span class="verdict-comp-name">${componentNames[key] || key}</span>
                        <span class="verdict-comp-dir" style="color:${dirColor}">${comp.direction} <span class="font-mono text-sm">(${comp.score > 0 ? '+' : ''}${comp.score})</span></span>
                    </div>
                    <div class="verdict-comp-bar-track">
                        <div class="verdict-comp-bar-center"></div>
                        <div class="verdict-comp-bar ${barLeft ? 'bar-right' : 'bar-left'}" style="width:${barWidth * 0.5}%; background:${dirColor};"></div>
                    </div>
                    <div class="verdict-comp-weight">Weight: ${comp.weight}%</div>
                </div>
            `;
        }).join('');
    }

    // Risk summary
    let riskHTML = '';
    if (verdict.risk_summary) {
        const rs = verdict.risk_summary;
        const riskColor = rs.class === 'HIGH' ? 'var(--danger)' : (rs.class === 'MEDIUM' ? 'var(--warning)' : 'var(--success)');
        riskHTML = `
            <div class="verdict-risk-card">
                <div class="verdict-risk-header">
                    <span>Risk Level</span>
                    <span class="verdict-risk-badge" style="background:${riskColor}20; color:${riskColor}">${rs.class}</span>
                </div>
                <div class="risk-meter"><div class="risk-fill" style="width:${rs.score}%; background:${riskColor}"></div></div>
                <div class="verdict-risk-factors">
                    ${rs.factors.slice(0, 4).map(f => `<div class="verdict-risk-factor">• ${f}</div>`).join('')}
                </div>
            </div>
        `;
    }

    // Explanation
    const explanationHTML = verdict.explanation.map(e =>
        `<div class="verdict-explanation-item">${e}</div>`
    ).join('');

    section.innerHTML = `
        <div class="verdict-card" style="border-color:${colors.color}30; background:${colors.bg}">
            <div class="verdict-main">
                <div class="verdict-gauge-area">
                    <div class="verdict-gauge">
                        <svg viewBox="0 0 200 120" class="verdict-gauge-svg">
                            <defs>
                                <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" style="stop-color:#FF4D6A" />
                                    <stop offset="35%" style="stop-color:#FFB020" />
                                    <stop offset="65%" style="stop-color:#FFB020" />
                                    <stop offset="100%" style="stop-color:#00E68A" />
                                </linearGradient>
                            </defs>
                            <path d="M 20 110 A 80 80 0 0 1 180 110" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="12" stroke-linecap="round"/>
                            <path d="M 20 110 A 80 80 0 0 1 180 110" fill="none" stroke="url(#gaugeGrad)" stroke-width="12" stroke-linecap="round" stroke-dasharray="251" stroke-dashoffset="${251 - (gaugePercent / 100 * 251)}" class="verdict-gauge-fill"/>
                            <circle cx="${20 + (160 * gaugePercent / 100)}" cy="${110 - Math.sin(Math.PI * gaugePercent / 100) * 80}" r="8" fill="${colors.color}" class="verdict-gauge-dot">
                                <animate attributeName="r" values="8;10;8" dur="2s" repeatCount="indefinite"/>
                            </circle>
                        </svg>
                    </div>
                    <div class="verdict-score-display">
                        <div class="verdict-label" style="color:${colors.color}">${verdictEmoji} ${verdict.verdict_label}</div>
                        <div class="verdict-score-num font-mono">${verdict.score > 0 ? '+' : ''}${verdict.score}</div>
                    </div>
                </div>
                <div class="verdict-meta">
                    <div class="verdict-confidence">
                        <span class="verdict-confidence-label">Confidence</span>
                        <div class="verdict-confidence-bar">
                            <div class="verdict-confidence-fill" style="width:${verdict.confidence}%; background:${colors.color}"></div>
                        </div>
                        <span class="verdict-confidence-val font-mono">${verdict.confidence}%</span>
                    </div>
                    ${!isFinal ? '<div class="verdict-updating"><span class="tab-spinner"></span> ML models loading — verdict will update...</div>' : '<div class="verdict-final">✅ Full analysis complete</div>'}
                </div>
            </div>
            <div class="verdict-body">
                <div class="verdict-components">
                    <h4>Component Breakdown</h4>
                    ${componentsHTML || '<div class="text-muted text-sm">Awaiting ML analysis...</div>'}
                </div>
                <div class="verdict-details">
                    ${riskHTML}
                    <div class="verdict-explanations">
                        <h4>Analysis Summary</h4>
                        ${explanationHTML}
                    </div>
                </div>
            </div>
        </div>
    `;
}


// ========== PHASE 2: ML ==========
async function loadMLResults(req) {
    setTimeout(() => animateStep('ml-step-1', 'done'), 400);
    setTimeout(() => animateStep('ml-step-2', 'active'), 600);

    try {
        const mlRes = await api.post('/analyze/ml', req);
        animateStep('ml-step-2', 'done');
        animateStep('ml-step-3', 'done');
        removeTabSpinner('prediction');
        renderPrediction(mlRes);

        // UPDATE the unified verdict with ML data
        if (mlRes.unified_verdict) {
            renderUnifiedVerdict(mlRes.unified_verdict, true);
        }
    } catch (err) {
        console.error('ML failed:', err);
        removeTabSpinner('prediction');
        document.getElementById('prediction-content').innerHTML = `
            <div class="glass-card"><p class="text-danger">⚠️ ML prediction failed: ${err.message}</p>
            <p class="text-muted" style="margin-top:0.5rem">Rule-based signals are still available in the Technical tab.</p></div>`;
        // Mark verdict as final even without ML
        const existingVerdict = document.querySelector('.verdict-updating');
        if (existingVerdict) {
            existingVerdict.innerHTML = '⚠️ ML unavailable — showing rule-based verdict only';
            existingVerdict.className = 'verdict-partial';
        }
    }
}

function renderPrediction(mlRes) {
    let predHTML = '';

    if (mlRes.prediction) {
        const p = mlRes.prediction;
        const color = p.direction === "UP" ? 'text-success' : 'text-danger';
        const arrow = p.direction === "UP" ? '↑' : '↓';
        const word = p.direction === "UP" ? 'Upside' : 'Downside';
        predHTML += `
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
        predHTML += `
            <div class="glass-card"><h3>🤖 ML Prediction</h3>
            <p class="text-muted" style="margin-top:1rem">Insufficient data for prediction. Try a longer period.</p></div>`;
    }

    // Ensemble Risk details (moved from separate Risk tab)
    if (mlRes.risk) {
        const r = mlRes.risk;
        const cClass = r.risk_class === "HIGH" ? "text-danger" : (r.risk_class === "MEDIUM" ? "text-warning" : "text-success");
        const fillBg = r.risk_class === "HIGH" ? "var(--danger)" : (r.risk_class === "MEDIUM" ? "var(--warning)" : "var(--success)");
        predHTML += `
            <div class="glass-card" style="margin-top:1.5rem">
                <h3>Ensemble Model Risk Assessment</h3>
                <div class="metrics-row" style="margin-top:1rem">
                    <div class="metric-box">
                        <div class="label">Risk Level</div>
                        <div class="value ${cClass}">${r.risk_class}</div>
                    </div>
                    <div class="metric-box"><div class="label">Risk Score</div><div class="value font-mono">${r.risk_score}/100</div></div>
                    <div class="metric-box"><div class="label">Downside Prob.</div><div class="value font-mono">${r.downside_prob}%</div></div>
                </div>
                <div class="risk-meter" style="margin-top:1rem"><div class="risk-fill" style="width:${r.risk_score}%; background:${fillBg}"></div></div>
                <ul style="margin-top:1rem; padding-left:1.5rem; color:var(--text-muted)">
                    ${r.explanation.map(f => `<li style="margin-bottom:0.5rem">${f}</li>`).join('')}
                </ul>
            </div>
        `;

        // Model votes
        if (r.model_votes) {
            predHTML += `
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
            </div>`;
        }
    }

    document.getElementById('prediction-content').innerHTML = predHTML;
}


// ========== SENTIMENT (feeds into verdict) ==========
async function loadSentimentForVerdict(symbol) {
    try {
        const data = await api.get(`/sentiment/${symbol}`);
        if (data.sentiment) {
            // Store for reference — sentiment data is now part of the unified verdict flow
            window._lastSentiment = data;
        }
    } catch (e) {
        console.warn('Sentiment loading skipped:', e.message);
    }
}


// ========== FUNDAMENTALS (lazy) ==========
async function loadFundamentals(symbol) {
    if (window._fundamentalsLoaded === symbol) return;

    const loading = document.getElementById('fundamentals-loading');
    const content = document.getElementById('fundamentals-content');
    loading.classList.remove('hidden');
    content.classList.add('hidden');

    try {
        const data = await api.get(`/fundamentals/${symbol}`);
        window._fundamentalsLoaded = symbol;

        if (data.error) {
            content.innerHTML = `<div class="glass-card"><p class="text-danger">${data.error}</p></div>`;
        } else {
            content.innerHTML = buildFundamentalsHTML(data);
        }

        loading.classList.add('hidden');
        content.classList.remove('hidden');
    } catch (e) {
        loading.innerHTML = `<p class="text-danger">Failed to load fundamentals: ${e.message}</p>`;
    }
}

function buildFundamentalsHTML(d) {
    const fmt = (v, prefix = '', suffix = '') => v !== null && v !== undefined ? `${prefix}${typeof v === 'number' ? v.toLocaleString() : v}${suffix}` : '—';
    const fmtMcap = (v) => {
        if (!v) return '—';
        if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
        if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
        if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
        return `$${v.toLocaleString()}`;
    };

    return `
        <div class="fundamentals-grid">
            <div class="glass-card fundamentals-section">
                <h3>📊 Valuation</h3>
                ${fRow('Market Cap', fmtMcap(d.valuation?.market_cap))}
                ${fRow('P/E (Trailing)', fmt(d.valuation?.pe_trailing))}
                ${fRow('P/E (Forward)', fmt(d.valuation?.pe_forward))}
                ${fRow('PEG Ratio', fmt(d.valuation?.peg_ratio))}
                ${fRow('P/S Ratio', fmt(d.valuation?.ps_ratio))}
                ${fRow('P/B Ratio', fmt(d.valuation?.pb_ratio))}
                ${fRow('EV/EBITDA', fmt(d.valuation?.ev_ebitda))}
            </div>
            <div class="glass-card fundamentals-section">
                <h3>💰 Profitability</h3>
                ${fRow('Revenue', fmtMcap(d.profitability?.revenue))}
                ${fRow('Revenue Growth', fmt(d.profitability?.revenue_growth, '', '%'))}
                ${fRow('Gross Margin', fmt(d.profitability?.gross_margins, '', '%'))}
                ${fRow('Operating Margin', fmt(d.profitability?.operating_margins, '', '%'))}
                ${fRow('Profit Margin', fmt(d.profitability?.profit_margins, '', '%'))}
                ${fRow('EPS (Trailing)', fmt(d.profitability?.eps_trailing, '$'))}
                ${fRow('ROE', fmt(d.profitability?.roe, '', '%'))}
            </div>
            <div class="glass-card fundamentals-section">
                <h3>🎯 Analyst Targets</h3>
                ${fRow('Recommendation', `<span class="stock-badge badge-${(d.targets?.recommendation || '').includes('buy') ? 'buy' : 'neutral'}">${d.targets?.recommendation || '—'}</span>`)}
                ${fRow('Target High', fmt(d.targets?.target_high, '$'))}
                ${fRow('Target Mean', fmt(d.targets?.target_mean, '$'))}
                ${fRow('Target Low', fmt(d.targets?.target_low, '$'))}
                ${fRow('# Analysts', fmt(d.targets?.num_analysts))}
            </div>
            <div class="glass-card fundamentals-section">
                <h3>🏦 Financial Health</h3>
                ${fRow('Total Cash', fmtMcap(d.financial_health?.total_cash))}
                ${fRow('Total Debt', fmtMcap(d.financial_health?.total_debt))}
                ${fRow('Debt/Equity', fmt(d.financial_health?.debt_to_equity))}
                ${fRow('Current Ratio', fmt(d.financial_health?.current_ratio))}
                ${fRow('Free Cash Flow', fmtMcap(d.financial_health?.free_cashflow))}
            </div>
            <div class="glass-card fundamentals-section">
                <h3>💵 Dividends</h3>
                ${fRow('Dividend Rate', fmt(d.dividends?.dividend_rate, '$'))}
                ${fRow('Dividend Yield', fmt(d.dividends?.dividend_yield, '', '%'))}
                ${fRow('Payout Ratio', fmt(d.dividends?.payout_ratio, '', '%'))}
            </div>
            <div class="glass-card fundamentals-section">
                <h3>📈 Price Info</h3>
                ${fRow('52W High', fmt(d.price_info?.['52w_high'], '$'))}
                ${fRow('52W Low', fmt(d.price_info?.['52w_low'], '$'))}
                ${fRow('50D Average', fmt(d.price_info?.['50d_avg'], '$'))}
                ${fRow('200D Average', fmt(d.price_info?.['200d_avg'], '$'))}
                ${fRow('Avg Volume', d.price_info?.avg_volume ? d.price_info.avg_volume.toLocaleString() : '—')}
            </div>
        </div>
        ${d.core?.description ? `<div class="glass-card" style="margin-top:1.25rem"><h3>About ${d.core.name}</h3><p class="text-muted" style="margin-top:0.5rem; line-height:1.7;">${d.core.description}</p></div>` : ''}
    `;
}

function fRow(label, value) {
    return `<div class="fundamentals-row"><span class="f-label">${label}</span><span class="f-value">${value}</span></div>`;
}

// ========== DATA & STATS (lazy) ==========
async function loadDataStats(symbol) {
    if (window._dataStatsLoaded === symbol) return;

    const loading = document.getElementById('data-loading');
    const content = document.getElementById('data-content');
    loading.classList.remove('hidden');
    content.classList.add('hidden');

    const period = document.getElementById('period-select').value;
    const interval = document.getElementById('interval-select').value;

    try {
        const data = await api.post('/analyze/data', { symbol, period, interval });
        window._dataStatsLoaded = symbol;

        let html = '';

        // Descriptive Stats Cards
        if (data.stats) {
            const s = data.stats;
            html += `
                <h3 style="margin-bottom:1rem;">📊 Descriptive Statistics</h3>
                <div class="metrics-grid" style="margin-bottom:2rem;">
                    ${statCard('Current Price', `$${s.price.current}`, '')}
                    ${statCard('Mean Price', `$${s.price.mean}`, `Median: $${s.price.median}`)}
                    ${statCard('Std Deviation', `$${s.price.std}`, `Range: $${s.price.range}`)}
                    ${statCard('Daily Return (Avg)', `${s.returns.mean_daily}%`, `Std: ${s.returns.std_daily}%`)}
                    ${statCard('Best Day', `${s.returns.best_day}%`, 'text-success')}
                    ${statCard('Worst Day', `${s.returns.worst_day}%`, 'text-danger')}
                    ${statCard('Win Rate', `${s.returns.win_rate}%`, `${s.returns.positive_days}↑ / ${s.returns.negative_days}↓`)}
                    ${statCard('Data Points', s.data_points, `${s.date_range.start} → ${s.date_range.end}`)}
                </div>
            `;
        }

        // Returns Distribution
        if (data.distribution && data.distribution.bins.length > 0) {
            html += `
                <h3 style="margin-bottom:1rem;">📈 Returns Distribution</h3>
                <div class="glass-card" style="margin-bottom:2rem;">
                    <div id="distribution-chart" style="height:250px;"></div>
                    <div class="metrics-row" style="margin-top:1rem;">
                        <div class="metric-box"><div class="label">Skewness</div><div class="value font-mono">${data.distribution.skewness}</div></div>
                        <div class="metric-box"><div class="label">Kurtosis</div><div class="value font-mono">${data.distribution.kurtosis}</div></div>
                        <div class="metric-box"><div class="label">Range</div><div class="value font-mono">${data.distribution.min}% to ${data.distribution.max}%</div></div>
                    </div>
                </div>
            `;
        }

        // Advanced Risk Metrics
        if (data.advanced_risk && !data.advanced_risk.error) {
            const ar = data.advanced_risk;
            html += `
                <h3 style="margin-bottom:1rem;">⚠️ Advanced Risk Metrics</h3>
                <div class="metrics-grid" style="margin-bottom:2rem;">
                    ${statCard('VaR (95%)', `${ar.var_95}%`, 'Daily worst-case loss')}
                    ${statCard('VaR (99%)', `${ar.var_99}%`, 'Extreme scenario')}
                    ${statCard('Sortino Ratio', ar.sortino_ratio, 'Downside risk-adjusted')}
                    ${statCard('Calmar Ratio', ar.calmar_ratio, 'Return / Max Drawdown')}
                    ${statCard('Beta (vs S&P)', ar.beta !== null ? ar.beta : '—', 'Market sensitivity')}
                    ${statCard('Ann. Return', `${ar.ann_return_pct}%`, 'Annualized')}
                </div>
            `;

            // Volatility cone
            if (ar.volatility_cone && Object.keys(ar.volatility_cone).length > 0) {
                html += `
                    <div class="glass-card" style="margin-bottom:2rem;">
                        <h3 style="margin-bottom:1rem;">🌊 Volatility Cone</h3>
                        <div class="data-table-wrapper">
                            <table class="data-table">
                                <thead><tr><th>Window</th><th>Current</th><th>Mean</th><th>Min</th><th>Max</th></tr></thead>
                                <tbody>
                                    ${Object.entries(ar.volatility_cone).map(([w, v]) => `
                                        <tr><td>${w}</td><td>${v.current ?? '—'}%</td><td>${v.mean}%</td><td>${v.min}%</td><td>${v.max}%</td></tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }
        }

        // Drawdown chart
        if (data.drawdown && data.drawdown.length > 0) {
            html += `
                <h3 style="margin-bottom:1rem;">📉 Drawdown Series</h3>
                <div class="glass-card" style="margin-bottom:2rem;">
                    <div id="drawdown-chart" style="height:220px;"></div>
                </div>
            `;
        }

        // OHLCV Data Table
        if (data.table_data && data.table_data.length > 0) {
            html += `
                <h3 style="margin-bottom:1rem;">📋 OHLCV Data (${data.table_data.length} rows)</h3>
                <div class="data-table-wrapper glass-card" style="max-height:400px; overflow-y:auto; padding:0;">
                    <table class="data-table">
                        <thead>
                            <tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th><th>Change %</th></tr>
                        </thead>
                        <tbody>
                            ${data.table_data.reverse().map(r => `
                                <tr>
                                    <td>${r.date}</td>
                                    <td>$${r.open}</td>
                                    <td>$${r.high}</td>
                                    <td>$${r.low}</td>
                                    <td>$${r.close}</td>
                                    <td>${r.volume.toLocaleString()}</td>
                                    <td class="${r.change_pct >= 0 ? 'text-success' : 'text-danger'}">${r.change_pct > 0 ? '+' : ''}${r.change_pct}%</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        content.innerHTML = html;
        loading.classList.add('hidden');
        content.classList.remove('hidden');

        // Render charts after DOM update
        setTimeout(() => {
            if (data.distribution && data.distribution.bins.length > 0) {
                renderDistributionChart('distribution-chart', data.distribution);
            }
            if (data.drawdown && data.drawdown.length > 0) {
                renderDrawdownChart('drawdown-chart', data.drawdown);
            }
        }, 100);

    } catch (e) {
        loading.innerHTML = `<p class="text-danger">Failed to load data: ${e.message}</p>`;
    }
}

function statCard(label, value, sub) {
    const isColorClass = sub === 'text-success' || sub === 'text-danger';
    return `
        <div class="glass-card stat-card">
            <div class="stat-label">${label}</div>
            <div class="stat-value ${isColorClass ? sub : ''}">${value}</div>
            ${sub && !isColorClass ? `<div class="stat-sub">${sub}</div>` : ''}
        </div>
    `;
}

// ========== DISTRIBUTION CHART ==========
function renderDistributionChart(containerId, dist) {
    const container = document.getElementById(containerId);
    if (!container || !dist.bins.length) return;
    container.innerHTML = '';

    const chart = LightweightCharts.createChart(container, {
        layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#7B8CA8', fontSize: 10 },
        grid: { vertLines: { visible: false }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
        rightPriceScale: { borderVisible: false },
        timeScale: { borderVisible: false },
        handleScroll: false,
        handleScale: false,
    });

    const histSeries = chart.addHistogramSeries({
        priceScaleId: '',
        scaleMargins: { top: 0.05, bottom: 0 },
    });

    const histData = dist.bins.map((bin, i) => ({
        time: i + 1,
        value: dist.counts[i],
        color: bin[0] >= 0 ? 'rgba(0, 230, 138, 0.6)' : 'rgba(255, 77, 106, 0.6)',
    }));

    histSeries.setData(histData);
    chart.timeScale().fitContent();
}

// ========== DRAWDOWN CHART ==========
function renderDrawdownChart(containerId, drawdownData) {
    const container = document.getElementById(containerId);
    if (!container || !drawdownData.length) return;
    container.innerHTML = '';

    const chart = LightweightCharts.createChart(container, {
        layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#7B8CA8', fontSize: 10 },
        grid: { vertLines: { visible: false }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
        rightPriceScale: { borderVisible: false },
        timeScale: { borderVisible: false, timeVisible: true },
        handleScroll: false,
        handleScale: false,
    });

    const areaSeries = chart.addAreaSeries({
        topColor: 'rgba(255, 77, 106, 0.01)',
        bottomColor: 'rgba(255, 77, 106, 0.25)',
        lineColor: '#FF4D6A',
        lineWidth: 2,
    });

    areaSeries.setData(drawdownData);
    chart.timeScale().fitContent();
}

// ========== SCREENER ==========
async function runScreener() {
    const container = document.getElementById('screener-results');
    container.innerHTML = '<div class="loading-section"><div class="pulse-loader"></div><p class="loading-text">Scanning stocks... this may take a minute.</p></div>';

    const params = new URLSearchParams();
    const sector = document.getElementById('scr-sector').value;
    const minPrice = document.getElementById('scr-min-price').value;
    const maxPrice = document.getElementById('scr-max-price').value;
    const minRsi = document.getElementById('scr-min-rsi').value;
    const maxRsi = document.getElementById('scr-max-rsi').value;
    const signal = document.getElementById('scr-signal').value;
    const sortBy = document.getElementById('scr-sort').value;

    if (sector) params.append('sector', sector);
    if (minPrice) params.append('min_price', minPrice);
    if (maxPrice) params.append('max_price', maxPrice);
    if (minRsi) params.append('min_rsi', minRsi);
    if (maxRsi) params.append('max_rsi', maxRsi);
    if (signal) params.append('signal', signal);
    params.append('sort_by', sortBy);
    params.append('limit', '25');

    try {
        const data = await api.get(`/screener?${params.toString()}`);

        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<div class="glass-card text-center"><p class="text-muted" style="padding:2rem;">No stocks match your filters. Try broadening your criteria.</p></div>';
            return;
        }

        const fmtMcap = (v) => {
            if (!v) return '—';
            if (v >= 1e12) return `${(v / 1e12).toFixed(1)}T`;
            if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
            if (v >= 1e6) return `${(v / 1e6).toFixed(0)}M`;
            return v.toLocaleString();
        };

        container.innerHTML = `
            <div class="glass-card" style="padding:0;">
                <div style="padding:1rem 1.5rem; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
                    <span class="text-muted text-sm">${data.results.length} stocks found</span>
                </div>
                <div class="data-table-wrapper">
                    <table class="data-table">
                        <thead>
                            <tr><th>Symbol</th><th>Price</th><th>5D Return</th><th>Signal</th><th>RSI</th><th>Score</th><th>Market Cap</th><th>P/E</th><th>Sector</th></tr>
                        </thead>
                        <tbody>
                            ${data.results.map(r => `
                                <tr style="cursor:pointer;" onclick="analyzeSpecificStock('${r.symbol}')">
                                    <td><strong>${r.symbol}</strong> <span style="font-family:Inter; color:var(--text-dim); font-size:0.75rem;">${r.name}</span></td>
                                    <td>$${r.price}</td>
                                    <td class="${r.return_5d >= 0 ? 'text-success' : 'text-danger'}">${r.return_5d > 0 ? '+' : ''}${r.return_5d}%</td>
                                    <td><span class="stock-badge badge-${r.signal.toLowerCase().replace(' ', '-')}">${r.signal}</span></td>
                                    <td>${r.rsi ?? '—'}</td>
                                    <td>${r.score}</td>
                                    <td style="font-family:Inter;">$${fmtMcap(r.market_cap)}</td>
                                    <td>${r.pe_ratio ?? '—'}</td>
                                    <td style="font-family:Inter; font-size:0.8rem;">${r.sector}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    } catch (e) {
        container.innerHTML = `<p class="text-danger">Screener error: ${e.message}</p>`;
    }
}

// ========== COMPARISON ==========
async function runComparison() {
    const container = document.getElementById('compare-results');
    const symbols = [
        document.getElementById('cmp-sym1').value.trim(),
        document.getElementById('cmp-sym2').value.trim(),
        document.getElementById('cmp-sym3').value.trim(),
    ].filter(s => s);

    if (symbols.length < 2) {
        container.innerHTML = '<p class="text-danger">Enter at least 2 symbols to compare.</p>';
        return;
    }

    container.innerHTML = '<div class="loading-section"><div class="pulse-loader"></div><p class="loading-text">Comparing stocks...</p></div>';

    const period = document.getElementById('cmp-period').value;

    try {
        const data = await api.post('/compare', { symbols, period });

        if (data.error) {
            container.innerHTML = `<p class="text-danger">${data.error}</p>`;
            return;
        }

        let html = '';

        // Normalized chart
        if (data.normalized_series && Object.keys(data.normalized_series).length > 0) {
            html += `
                <div class="glass-card" style="margin-bottom:1.5rem;">
                    <h3 style="margin-bottom:0.75rem;">📈 Normalized Returns (Base 100)</h3>
                    <div id="comparison-chart" style="height:400px;"></div>
                </div>
            `;
        }

        // Comparison table
        if (data.comparison && data.comparison.length > 0) {
            html += `
                <div class="glass-card" style="margin-bottom:1.5rem; padding:0;">
                    <div class="data-table-wrapper">
                        <table class="data-table">
                            <thead>
                                <tr><th>Symbol</th><th>Price</th><th>Total Return</th><th>Signal</th><th>RSI</th><th>Volatility</th><th>Sharpe</th><th>Max DD</th></tr>
                            </thead>
                            <tbody>
                                ${data.comparison.map(c => `
                                    <tr style="cursor:pointer;" onclick="analyzeSpecificStock('${c.symbol}')">
                                        <td><strong>${c.symbol}</strong> <span style="font-family:Inter; color:var(--text-dim); font-size:0.75rem;">${c.name}</span></td>
                                        <td>$${c.price}</td>
                                        <td class="${c.total_return >= 0 ? 'text-success' : 'text-danger'}">${c.total_return > 0 ? '+' : ''}${c.total_return}%</td>
                                        <td><span class="stock-badge badge-${c.signal.toLowerCase().replace(' ', '-')}">${c.signal}</span></td>
                                        <td>${c.rsi}</td>
                                        <td>${c.volatility}%</td>
                                        <td>${c.sharpe}</td>
                                        <td class="text-danger">${c.max_drawdown}%</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        // Correlation matrix
        if (data.correlation && Object.keys(data.correlation).length > 0) {
            const syms = Object.keys(data.correlation);
            html += `
                <div class="glass-card">
                    <h3 style="margin-bottom:1rem;">🔗 Correlation Matrix</h3>
                    <div class="correlation-matrix">
                        <table>
                            <thead><tr><th></th>${syms.map(s => `<th>${s}</th>`).join('')}</tr></thead>
                            <tbody>
                                ${syms.map(s1 => `
                                    <tr><td style="font-weight:700;">${s1}</td>
                                    ${syms.map(s2 => {
                                        const val = data.correlation[s1]?.[s2];
                                        const bg = val !== null ? getCorrColor(val) : 'transparent';
                                        return `<td style="background:${bg}">${val !== null ? val.toFixed(2) : '—'}</td>`;
                                    }).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;

        // Render comparison chart
        setTimeout(() => {
            if (data.normalized_series) {
                renderComparisonChart('comparison-chart', data.normalized_series);
            }
        }, 100);

    } catch (e) {
        container.innerHTML = `<p class="text-danger">Comparison error: ${e.message}</p>`;
    }
}

function getCorrColor(val) {
    if (val >= 0.7) return 'rgba(0, 230, 138, 0.2)';
    if (val >= 0.3) return 'rgba(0, 230, 138, 0.1)';
    if (val <= -0.3) return 'rgba(255, 77, 106, 0.1)';
    if (val <= -0.7) return 'rgba(255, 77, 106, 0.2)';
    return 'rgba(255,255,255,0.02)';
}

function renderComparisonChart(containerId, series) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth || 800,
        height: container.clientHeight || 400,
        layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#7B8CA8' },
        grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
        rightPriceScale: { borderVisible: false },
        timeScale: { borderVisible: false, timeVisible: true },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    });

    const colors = ['#00D4FF', '#00E68A', '#A78BFA', '#FFB020', '#FF4D6A'];
    let i = 0;
    for (const [symbol, data] of Object.entries(series)) {
        const line = chart.addLineSeries({
            color: colors[i % colors.length],
            lineWidth: 2,
            title: symbol,
        });
        line.setData(data);
        i++;
    }

    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== container) return;
        const newRect = entries[0].contentRect;
        const w = container.clientWidth || newRect.width;
        const h = container.clientHeight || newRect.height;
        if (w > 0 && h > 0) {
            chart.applyOptions({ height: h, width: w });
            chart.timeScale().fitContent();
        }
    }).observe(container);

    chart.timeScale().fitContent();
}


// ========== ML TAB HELPERS ==========
function resetMLTabs() {
    document.querySelectorAll('#prediction-content .step-item').forEach(el => el.className = 'step-item');
    const s1 = document.getElementById('ml-step-1');
    if (s1) s1.classList.add('active');
}

function animateStep(stepId, state) {
    const el = document.getElementById(stepId);
    if (el) el.className = `step-item ${state}`;
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

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    // Check if backend is awake (Render cold-start)
    const connectBanner = document.getElementById('global-loading-banner');
    if (connectBanner) {
        api.get('/market/overview')
            .then(() => {
                connectBanner.classList.add('banner-hidden');
                setTimeout(() => connectBanner.style.display = 'none', 300);
            })
            .catch(() => {
                const textEl = connectBanner.querySelector('.global-loading-text');
                if (textEl) textEl.textContent = '⚠️ Backend connection failed. Retrying...';
                // Try once more after 5s
                setTimeout(() => {
                    api.get('/market/overview').then(() => {
                        connectBanner.classList.add('banner-hidden');
                        setTimeout(() => connectBanner.style.display = 'none', 300);
                    }).catch(() => {
                        if (textEl) textEl.textContent = '⚠️ Backend offline.';
                        setTimeout(() => {
                            connectBanner.classList.add('banner-hidden');
                            setTimeout(() => connectBanner.style.display = 'none', 300);
                        }, 3000);
                    });
                }, 5000);
            });
    }

    // Enter keys
    document.getElementById('hero-search').addEventListener('keydown', e => {
        if (e.key === 'Enter') searchFromHero();
    });
    document.getElementById('analyze-search').addEventListener('keydown', e => {
        if (e.key === 'Enter') runAnalysis();
    });
    document.getElementById('global-search').addEventListener('keydown', handleGlobalSearch);

    // Initial navigation
    if (document.location.hash) {
        navigate(document.location.hash.substring(1));
    } else {
        navigate('dashboard');
    }
});
