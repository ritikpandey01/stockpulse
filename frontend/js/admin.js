async function loadAdminDashboard() {
    const container = document.getElementById('admin-content');
    container.innerHTML = `<div class="loading-section"><div class="pulse-loader"></div><p>Aggregating validation data...</p></div>`;

    try {
        const data = await api.get('/admin/accuracy');
        
        if (data.error) {
            container.innerHTML = `
                <div class="glass-card">
                    <p class="text-danger">Failed to load: ${data.error}</p>
                    <p class="text-muted mt-2">Note: Supabase must be configured in <code>.env</code> with the proper tables created (<code>predictions</code> schema from the design doc).</p>
                </div>`;
            return;
        }

        let html = `
            <div class="metrics-row" style="margin-bottom: 2rem">
                <div class="glass-card metric-box text-center">
                    <div class="label">Overall Win Rate</div>
                    <div class="value ${data.win_rate > 50 ? 'text-success' : 'text-danger'}" style="font-size:3rem">
                        ${data.win_rate}%
                    </div>
                </div>
                <div class="glass-card metric-box text-center">
                    <div class="label">Validated Predictions</div>
                    <div class="value">${data.total_validated}</div>
                </div>
                <div class="glass-card metric-box text-center">
                    <div class="label">Successful (Wins)</div>
                    <div class="value text-success">${data.wins}</div>
                </div>
                <div class="glass-card metric-box text-center">
                    <div class="label">Pending Validation</div>
                    <div class="value text-warning">${data.pending}</div>
                </div>
            </div>
            
            <div style="display:grid; grid-template-columns: 1fr 2fr; gap:2rem;">
                <div class="glass-card">
                    <h3>Accuracy by Timeframe</h3>
                    <div style="margin-top:1rem">
                        ${Object.keys(data.by_timeframe).length === 0 ? '<p class="text-muted">No data yet</p>' : ''}
                        ${Object.entries(data.by_timeframe).map(([tf, stat]) => `
                            <div style="margin-bottom:1rem">
                                <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem">
                                    <strong>${tf} Model</strong>
                                    <span>${stat.accuracy}% (${stat.wins}/${stat.total})</span>
                                </div>
                                <div class="risk-meter" style="height:12px; margin:0"><div class="risk-fill" style="width:${stat.accuracy}%; background:${stat.accuracy > 50 ? '#10B981':'#EF4444'}"></div></div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="glass-card">
                    <h3>Recent Validations Log</h3>
                    <div style="margin-top:1rem; max-height:400px; overflow-y:auto;">
                        <table style="width:100%; text-align:left; border-collapse:collapse;">
                            <thead>
                                <tr style="border-bottom:1px solid var(--border)">
                                    <th style="padding:0.5rem">Time</th>
                                    <th style="padding:0.5rem">Symbol</th>
                                    <th style="padding:0.5rem">Prediction</th>
                                    <th style="padding:0.5rem">Actual</th>
                                    <th style="padding:0.5rem">Result</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.recent.length === 0 ? '<tr><td colspan="5" class="text-muted text-center" style="padding:1rem">No validated predictions yet</td></tr>' : ''}
                                ${data.recent.reverse().map(r => `
                                    <tr style="border-bottom:1px solid rgba(255,255,255,0.02)">
                                        <td style="padding:0.5rem; font-size:0.85rem" class="text-muted">${new Date(r.check_at).toLocaleString()}</td>
                                        <td style="padding:0.5rem" class="font-mono"><strong>${r.symbol}</strong> ${r.timeframe}</td>
                                        <td style="padding:0.5rem">$${r.predicted_price} (${r.predicted_direction})</td>
                                        <td style="padding:0.5rem">$${r.actual_price} (${r.actual_direction})</td>
                                        <td style="padding:0.5rem">
                                            <span class="stock-badge badge-${r.result === 'WIN' ? 'bullish' : 'bearish'}">${r.result}</span>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;

    } catch (e) {
        container.innerHTML = `<p class="text-danger">Admin dashboard error: ${e.message}</p>`;
    }
}
