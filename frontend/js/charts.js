// ========== Main Chart ==========
window.renderChart = function(containerId, chartData) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (!chartData || chartData.length === 0) return;

    const chartProperties = {
        layout: {
            background: { type: 'solid', color: 'transparent' },
            textColor: '#94A3B8',
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
        },
        timeScale: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
            timeVisible: true,
        },
    };

    const chart = LightweightCharts.createChart(container, chartProperties);

    // Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
        upColor: '#10B981',
        downColor: '#EF4444',
        borderDownColor: '#EF4444',
        borderUpColor: '#10B981',
        wickDownColor: '#EF4444',
        wickUpColor: '#10B981',
    });

    candleSeries.setData(chartData);

    // Volume Series
    const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: '',
        scaleMargins: { top: 0.8, bottom: 0 },
    });

    const volumeData = chartData.map(d => ({
        time: d.time,
        value: d.volume,
        color: d.close >= d.open ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
    }));

    volumeSeries.setData(volumeData);

    // Resize handler
    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== container) return;
        const newRect = entries[0].contentRect;
        chart.applyOptions({ height: newRect.height, width: newRect.width });
    }).observe(container);

    chart.timeScale().fitContent();
};


// ========== Indicator Mini-Charts ==========
window.renderIndicatorCharts = function(indicatorData) {
    if (!indicatorData || indicatorData.length === 0) return;

    const miniChartOpts = {
        layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#64748B', fontSize: 10 },
        grid: { vertLines: { visible: false }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
        rightPriceScale: { borderVisible: false },
        timeScale: { borderVisible: false, timeVisible: true },
        crosshair: { mode: LightweightCharts.CrosshairMode.Magnet },
        handleScroll: false,
        handleScale: false,
    };

    // Filter out entries missing data
    const clean = indicatorData.filter(d => d.time);

    // ---- RSI Chart ----
    const rsiContainer = document.getElementById('rsi-chart');
    rsiContainer.innerHTML = '';
    const rsiChart = LightweightCharts.createChart(rsiContainer, miniChartOpts);

    const rsiData = clean.filter(d => d.RSI !== undefined).map(d => ({ time: d.time, value: d.RSI }));
    if (rsiData.length > 0) {
        const rsiSeries = rsiChart.addLineSeries({ color: '#A78BFA', lineWidth: 2 });
        rsiSeries.setData(rsiData);

        // Overbought/Oversold lines
        const ob = rsiChart.addLineSeries({ color: 'rgba(239,68,68,0.3)', lineWidth: 1, lineStyle: 2 });
        ob.setData(rsiData.map(d => ({ time: d.time, value: 70 })));
        const os = rsiChart.addLineSeries({ color: 'rgba(16,185,129,0.3)', lineWidth: 1, lineStyle: 2 });
        os.setData(rsiData.map(d => ({ time: d.time, value: 30 })));

        rsiChart.timeScale().fitContent();

        // Update badge
        const lastRsi = rsiData[rsiData.length - 1].value;
        const badge = document.getElementById('rsi-badge');
        badge.textContent = lastRsi.toFixed(1);
        if (lastRsi > 70) { badge.className = 'indicator-badge overbought'; }
        else if (lastRsi < 30) { badge.className = 'indicator-badge oversold'; }
        else { badge.className = 'indicator-badge neutral'; }
    }

    // ---- MACD Chart ----
    const macdContainer = document.getElementById('macd-chart');
    macdContainer.innerHTML = '';
    const macdChart = LightweightCharts.createChart(macdContainer, miniChartOpts);

    const macdData = clean.filter(d => d.MACD !== undefined).map(d => ({ time: d.time, value: d.MACD }));
    if (macdData.length > 0) {
        const macdHist = macdChart.addHistogramSeries({
            priceScaleId: '',
            scaleMargins: { top: 0.1, bottom: 0 },
        });
        macdHist.setData(macdData.map(d => ({
            time: d.time,
            value: d.value,
            color: d.value >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)',
        })));
        macdChart.timeScale().fitContent();
    }

    // ---- Bollinger Bands Chart ----
    const bbContainer = document.getElementById('bb-chart');
    bbContainer.innerHTML = '';
    const bbChart = LightweightCharts.createChart(bbContainer, miniChartOpts);

    const bbUpperData = clean.filter(d => d.BB_upper !== undefined).map(d => ({ time: d.time, value: d.BB_upper }));
    const bbMiddleData = clean.filter(d => d.BB_middle !== undefined).map(d => ({ time: d.time, value: d.BB_middle }));
    const bbLowerData = clean.filter(d => d.BB_lower !== undefined).map(d => ({ time: d.time, value: d.BB_lower }));

    if (bbUpperData.length > 0) {
        bbChart.addLineSeries({ color: 'rgba(239,68,68,0.5)', lineWidth: 1 }).setData(bbUpperData);
        bbChart.addLineSeries({ color: '#00D4FF', lineWidth: 2 }).setData(bbMiddleData);
        bbChart.addLineSeries({ color: 'rgba(16,185,129,0.5)', lineWidth: 1 }).setData(bbLowerData);
        bbChart.timeScale().fitContent();
    }

    // ---- OBV Chart ----
    const obvContainer = document.getElementById('obv-chart');
    obvContainer.innerHTML = '';
    const obvChart = LightweightCharts.createChart(obvContainer, miniChartOpts);

    const obvData = clean.filter(d => d.OBV !== undefined).map(d => ({ time: d.time, value: d.OBV }));
    if (obvData.length > 0) {
        const obvArea = obvChart.addAreaSeries({
            topColor: 'rgba(0, 212, 255, 0.3)',
            bottomColor: 'rgba(0, 212, 255, 0.02)',
            lineColor: '#00D4FF',
            lineWidth: 2,
        });
        obvArea.setData(obvData);
        obvChart.timeScale().fitContent();
    }
};
