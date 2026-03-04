// Configuration for API endpoints
const API_BASE_URL = '/api';
const API_URLS = {
    kpis: `${API_BASE_URL}/kpis`,
    profitTrend: `${API_BASE_URL}/profit-trend`,
    deliveryTrend: `${API_BASE_URL}/delivery-trend`,
    gdpComparison: `${API_BASE_URL}/gdp-comparison`,
    analyze: `${API_BASE_URL}/analyze`,
    revenueHistory: `${API_BASE_URL}/revenue-history`,
    ordersOverview: `${API_BASE_URL}/orders-overview`,
    successPrediction: `${API_BASE_URL}/success-prediction`,
    salesTrend: `${API_BASE_URL}/sales-trend`,
    inventoryHealth: `/forecasting/inventory-health`,
    activeAlerts: `/alerts/active`,
    businessViability: `/ai/business-viability`,
    aiChat: `${API_BASE_URL}/ai/chat`,
    // Phase 1 endpoints
    searchOrders: `/sales/search/orders`,
    bulkStatus: `/sales/bulk-status`,
    exportSales: `/sales/export/csv`,
    inventoryList: `/inventory/`,
    exportInventory: `/inventory/export/csv`,
    // Phase 2 endpoints
    suppliersList: `/suppliers/`,
    exportSuppliers: `/suppliers/export/csv`,
    customersList: `/customers/`,
    exportCustomers: `/customers/export/csv`,
    teamMembers: `${API_BASE_URL}/team/members`,
    teamInvites: `${API_BASE_URL}/team/invites`,
    teamSendInvite: `${API_BASE_URL}/team/invites`,
    // Automation Phase
    requestOtp: `${API_BASE_URL}/automation/request-otp`,
    verifyOtp: `${API_BASE_URL}/automation/verify-otp`,
    listAutomations: `${API_BASE_URL}/automation/list`,
    deleteAutomation: `${API_BASE_URL}/automation`,
    // Phase 3 endpoints
    financeInvoices: `${API_BASE_URL}/finance/invoices`,
    logisticsShipments: `${API_BASE_URL}/logistics/shipments`,
    logisticsReturns: `${API_BASE_URL}/logistics/returns`,
    activityNotifications: `${API_BASE_URL}/activity/notifications`,
    activityLogs: `${API_BASE_URL}/activity/logs`
};

let charts = {};

/* ---------------- AUTH HELPERS ---------------- */

async function fetchWithAuth(url, options = {}) {
    const opts = { credentials: "include", ...options };
    opts.headers = { ...(options.headers || {}) };

    let response = await fetch(url, opts);
    if (response.status !== 401) return response;

    try {
        const refresh = await fetch("/api/refresh", { method: "POST", credentials: "include" });
        if (refresh.ok) {
            response = await fetch(url, opts);
            if (response.status !== 401) return response;
        }
    } catch (e) {
        console.error("Refresh failed", e);
    }

    window.location.href = "/";
    throw new Error("Unauthorized");
}

/* ---------------- SECTION HANDLING ---------------- */

function showSection(sectionName, event) {
    if (event) event.preventDefault();

    // Hide error banner safely
    const errorBanner = document.getElementById('error-banner');
    if (errorBanner) errorBanner.classList.add('hidden');

    // Hide all sections
    document.querySelectorAll('.dashboard-section')
        .forEach(s => s.classList.add('hidden'));

    // ✅ SAFETY CHECK
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (!targetSection) {
        // Fallback for ID mismatches
        if (sectionName === 'business-analysis-results') {
            const fallback = document.getElementById('business-analysis-results-section');
            if (fallback) { fallback.classList.remove('hidden'); return; }
        }
        console.error(`Section not found: ${sectionName}-section`);
        return;
    }

    targetSection.classList.remove('hidden');

    document.querySelectorAll('.nav-item')
        .forEach(item => item.classList.remove('active'));

    const activeNavItem = Array.from(document.querySelectorAll('.nav-item'))
        .find(item => item.getAttribute('onclick')?.includes(`'${sectionName}'`));
    if (activeNavItem) activeNavItem.classList.add('active');

    loadDataForSection(sectionName);
}


/* ---------------- ERROR HANDLING ---------------- */

function handleFetchError(error, context) {
    console.error(`Failed to ${context}:`, error);
    const errorBanner = document.getElementById('error-banner');
    if (errorBanner) {
        errorBanner.querySelector('#error-message').textContent =
            `Could not connect to backend to ${context}.`;
        errorBanner.classList.remove('hidden');
    }
}

/* ---------------- DASHBOARD DATA ---------------- */

async function loadDataForSection(sectionName) {
    if (sectionName === 'executive') {
        fetchKpis();
        fetchAndRenderChart('profitTrend', 'profitChart', initializeLineChart,
            { label: 'Profit Margin (%)', color: '#3b82f6' });
        fetchAndRenderChart('deliveryTrend', 'deliveryChart', initializeBarChart,
            { label: 'Delivery Performance (%)', color: '#10b981', yMin: 85, yMax: 100 });
        fetchOrderOverview();
        fetchSuccessPrediction();
    } else if (sectionName === 'comparison') {
        fetchAndRenderChart('gdpComparison', 'gdpChart', initializeBarChart,
            { label: 'Revenue by Country ($)', color: '#22c55e', indexAxis: 'y' });
        initGlobe();
    } else if (sectionName === 'sales') {
        fetchAndRenderChart('salesTrend', 'salesChart', initializeLineChart,
            { label: 'Monthly Sales ($)', color: '#8b5cf6' });
        loadOrders();
    } else if (sectionName === 'orders') {
        loadOrders();
    } else if (sectionName === 'inventory') {
        loadInventoryItems();
        fetchInventoryHealth();
        fetchAlerts();
    } else if (sectionName === 'suppliers') {
        loadSuppliers();
    } else if (sectionName === 'customers') {
        loadCustomers();
    } else if (sectionName === 'team') {
        loadTeamMembers();
        loadPendingInvites();
    } else if (sectionName === 'automation') {
        loadAutomations();
    } else if (sectionName === 'finance') {
        loadInvoices();
    } else if (sectionName === 'logistics') {
        loadLogistics();
    }
}

/* ---------------- KPI & CHART HELPERS ---------------- */

/* ---------------- GLOBE VISUALIZATION ---------------- */

let myGlobe = null;
const COUNTRY_COORDS = {
    'India': { lat: 20.5937, lng: 78.9629 },
    'United States': { lat: 37.0902, lng: -95.7129 },
    'United Kingdom': { lat: 55.3781, lng: -3.4360 },
    'Germany': { lat: 51.1657, lng: 10.4515 },
    'France': { lat: 46.2276, lng: 2.2137 },
    'Brazil': { lat: -14.2350, lng: -51.9253 },
    'Japan': { lat: 36.2048, lng: 138.2529 },
    'Australia': { lat: -25.2744, lng: 133.7751 },
    'Switzerland': { lat: 46.8182, lng: 8.2275 },
    'Ireland': { lat: 53.1424, lng: -7.6921 },
    'Canada': { lat: 56.1304, lng: -106.3468 }
};

async function initGlobe() {
    const container = document.getElementById('globeContainer');
    if (!container || myGlobe) {
        if (myGlobe) loadGlobeData();
        return;
    }

    // Safety check for library loading
    if (typeof Globe === 'undefined') {
        console.warn("Globe.gl library not detected yet. Retrying in 1s...");
        setTimeout(initGlobe, 1000);
        return;
    }

    myGlobe = Globe()
        (container)
        .backgroundColor('rgba(0,0,0,0)') // Transparent background
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
        .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
        .atmosphereColor('#3b82f6')
        .atmosphereDaylightAlpha(0.2)
        .showAtmosphere(true)
        .pointResolution(24) // Balance between smoothness and detail
        .labelSize(1.6)
        .labelDotRadius(0.4)
        .labelColor(() => 'rgba(255, 255, 255, 0.9)')
        .labelResolution(3)
        .ringColor(() => d => d.color)
        .ringMaxRadius('maxR')
        .ringPropagationSpeed('speed')
        .ringRepeatPeriod('repeat');

    // Aesthetics for "Industrial Tactical"
    myGlobe.controls().autoRotate = true;
    myGlobe.controls().autoRotateSpeed = 0.5;
    myGlobe.controls().enableZoom = true;

    // Load data
    loadGlobeData();

    // Handle resize with debounce for smoothness
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (myGlobe) {
                const width = container.offsetWidth;
                const height = container.offsetHeight;
                myGlobe.width(width).height(height);
            }
        }, 200);
    });
}

async function loadGlobeData() {
    try {
        const res = await fetchWithAuth(API_URLS.gdpComparison);
        const result = await res.json();

        // Data format from backend is { labels: [], data: [] }
        const globeData = result.labels.map((country, index) => {
            const revenue = result.data[index] || 0;
            const coords = COUNTRY_COORDS[country];

            if (!coords) {
                console.warn(`No coords for: ${country}`);
                return null;
            }

            return {
                lat: coords.lat,
                lng: coords.lng,
                size: Math.max(0.1, Math.sqrt(revenue) / 500), // Scale up for better visibility
                color: revenue > 500000 ? '#22c55e' : '#3b82f6',
                label: `<b>${country}</b><br>Revenue: ${new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(revenue)}`,
                text: `${country}\n${new Intl.NumberFormat('en-IN', { notation: 'compact' }).format(revenue)}`
            };
        }).filter(d => d !== null);

        const ringData = globeData.map(d => ({
            lat: d.lat,
            lng: d.lng,
            maxR: d.size * 2,
            speed: 2,
            repeat: 1000,
            color: d.color
        }));

        myGlobe
            .pointsData(globeData)
            .pointAltitude('size')
            .pointColor('color')
            .pointLabel('label')
            .labelsData(globeData)
            .labelText('text')
            .labelAltitude(0.01)
            .ringsData(ringData)
            .pointsTransitionDuration(1000);

    } catch (e) { console.error("Failed to load globe data", e); }
}

async function fetchKpis() {
    try {
        const res = await fetchWithAuth(API_URLS.kpis);
        const data = await res.json();
        document.getElementById('kpiTotalCost').textContent =
            new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(data.total_cost);
        document.getElementById('kpiProfitMargin').textContent = `${data.profit_margin}%`;
        document.getElementById('kpiRiskScore').textContent = `${data.risk_score}/10`;
        document.getElementById('kpiDeliveryPerformance').textContent = `${data.delivery_performance}%`;
        document.getElementById('lastUpdated').textContent =
            `Last updated: ${new Date().toLocaleTimeString()}`;
    } catch (e) { handleFetchError(e, "fetch KPIs"); }
}

async function fetchOrderOverview() {
    try {
        const res = await fetchWithAuth(API_URLS.ordersOverview);
        const data = await res.json();
        document.getElementById('totalPendingOrders').textContent = data.total_pending;
        document.getElementById('shippedThisMonth').textContent = data.total_shipped_month;
    } catch (e) { handleFetchError(e, "fetch orders"); }
}

async function fetchSuccessPrediction() {
    try {
        const res = await fetchWithAuth(API_URLS.successPrediction);
        const data = await res.json();
        document.getElementById('predictionScore').textContent = `${data.prediction_score}/100`;
        document.getElementById('predictionConfidence').textContent =
            `Confidence: ${(data.confidence_level * 100).toFixed(1)}%`;
        document.getElementById('predictionFactors').textContent =
            `Key Factors: ${data.key_factors.join(', ')}`;
    } catch (e) { handleFetchError(e, "fetch prediction"); }
}

async function fetchInventoryHealth() {
    try {
        const res = await fetchWithAuth(API_URLS.inventoryHealth);
        const data = await res.json();
        const tbody = document.getElementById('inventory-table-body');
        if (!tbody) return;

        tbody.innerHTML = data.map(item => `
            <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#f8fafc'" onmouseout="this.style.backgroundColor='transparent'">
                <td style="padding: 12px; font-weight: 500;">${item.product_name}</td>
                <td style="padding: 12px;">${item.stock_level}</td>
                <td style="padding: 12px;">${item.burn_rate} / day</td>
                <td style="padding: 12px;">${item.days_left === 999 ? '∞' : item.days_left}</td>
                <td style="padding: 12px;">${item.stock_out_date || 'N/A'}</td>
                <td style="padding: 12px;">
                    <span class="badge" style="background-color: ${item.status === 'Critical' ? '#fee2e2' : item.status === 'At Risk' ? '#fef3c7' : '#dcfce7'
            }; color: ${item.status === 'Critical' ? '#b91c1c' : item.status === 'At Risk' ? '#b45309' : '#15803d'
            };">
                        ${item.status}
                    </span>
                </td>
            </tr>
        `).join('');
    } catch (e) { handleFetchError(e, "fetch inventory"); }
}

async function fetchAlerts() {
    try {
        const res = await fetchWithAuth(API_URLS.activeAlerts);
        const data = await res.json();
        const container = document.getElementById('alerts-container');
        if (!container) return;

        if (data.length === 0) {
            container.innerHTML = `
                <div class="card" style="border: 1px solid #dcfce7; background: #f0fdf4;">
                    <div class="card-header-padded" style="display: flex; align-items: center; gap: 12px;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        <p style="color: #15803d; font-weight: 500; margin: 0;">No active alerts. Your supply chain is running smoothly!</p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = data.map(alert => {
            let iconSvg = '';
            if (alert.type === 'Low Stock') {
                iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>`;
            } else if (alert.type === 'Late Shipment') {
                iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>`;
            } else {
                iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
            }

            return `
                <div class="card" style="border-left: 4px solid ${alert.severity === 'High' ? '#ef4444' : '#f59e0b'}; margin-bottom: 12px;">
                    <div class="card-header-padded" style="padding: 16px 24px; display: flex; align-items: center; gap: 16px;">
                        <div style="color: ${alert.severity === 'High' ? '#ef4444' : '#f59e0b'}; display: flex;">${iconSvg}</div>
                        <div style="flex: 1;">
                            <h4 style="font-size: 14px; font-weight: 700; color: #1e293b; margin: 0;">${alert.type}</h4>
                            <p style="font-size: 13px; color: #64748b; margin: 4px 0 0 0;">${alert.message}</p>
                        </div>
                        <span class="badge" style="background: ${alert.severity === 'High' ? '#fee2e2' : '#fef3c7'}; color: ${alert.severity === 'High' ? '#b91c1c' : '#b45309'}">
                            ${alert.severity} Priority
                        </span>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) { handleFetchError(e, "fetch alerts"); }
}

/* ---------------- CHART UTILS ---------------- */

function fetchAndRenderChart(urlKey, chartId, initFn, options) {
    fetchWithAuth(API_URLS[urlKey])
        .then(res => res.json())
        .then(data => initFn(chartId, data, options))
        .catch(e => handleFetchError(e, `chart ${chartId}`));
}

function createOrUpdateChart(chartId, config) {
    const ctx = document.getElementById(chartId)?.getContext('2d');
    if (!ctx) return;
    if (charts[chartId]) charts[chartId].destroy();
    charts[chartId] = new Chart(ctx, config);
}

function initializeLineChart(id, data, opt) {
    createOrUpdateChart(id, {
        type: 'line',
        data: { labels: data.labels, datasets: [{ label: opt.label, data: data.data, borderColor: opt.color, backgroundColor: opt.color, fill: false }] }
    });
}

function initializeBarChart(id, data, opt) {
    createOrUpdateChart(id, {
        type: 'bar',
        data: { labels: data.labels, datasets: [{ label: opt.label, data: data.data, backgroundColor: opt.color }] },
        options: { indexAxis: opt.indexAxis || 'x' }
    });
}

/* ---------------- BUSINESS ANALYSIS LOGIC ---------------- */

async function generateAnalysis() {
    const generateBtn = document.getElementById('generate-btn');
    const industry = document.getElementById('industry').value;
    const marketDemand = document.getElementById('market_demand').value;
    const competition = document.getElementById('competition').value;
    const capitalRange = document.getElementById('capital_range').value;
    const experience = document.getElementById('experience').value;
    const ideaText = document.getElementById('business_idea').value;

    if (!ideaText) {
        alert("Please describe the business idea.");
        return;
    }

    const originalText = generateBtn.innerText;
    generateBtn.innerText = "Analyzing...";
    generateBtn.disabled = true;

    const payload = {
        industry: industry,
        market_demand: parseInt(marketDemand) || 0,
        competition: parseInt(competition) || 0,
        capital_range: capitalRange,
        experience: parseInt(experience) || 0,
        idea: ideaText
    };

    try {
        const response = await fetchWithAuth(API_URLS.businessViability, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({ detail: "Invalid request" }));
            alert(errData.detail || "Invalid input. Please refine your description.");
            return;
        }

        const data = await response.json();
        displayResults(data, ideaText);

    } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to AI backend.");
    } finally {
        generateBtn.innerText = originalText;
        generateBtn.disabled = false;
    }
}

function displayResults(data, ideaName) {
    showSection('business-analysis-results');

    document.getElementById('ideaName').innerText = ideaName.length > 30 ? ideaName.substring(0, 30) + "..." : ideaName;
    document.getElementById('score-display').innerText = data.viability_score + "/100";
    document.getElementById('recommendation-text').innerText = data.breakdown || "Analysis Complete";

    if (data.projections) {
        document.getElementById('investment-est').innerText = data.projections.estimated_cost;
        document.getElementById('analysisTimeline').innerText = "12-18 Months";
    }

    const riskBadge = document.getElementById('risk-badge');
    if (riskBadge) {
        riskBadge.innerText = data.risk_level;
        riskBadge.style.color = '#fff';
        riskBadge.style.padding = '4px 8px';
        riskBadge.style.borderRadius = '4px';

        if (data.risk_level === 'High') riskBadge.style.backgroundColor = '#dc3545';
        else if (data.risk_level === 'Medium') riskBadge.style.backgroundColor = '#ffc107';
        else riskBadge.style.backgroundColor = '#28a745';
    }

    updateAnalysisCharts(data);
}

let viabilityChartInstance = null;
let marketChartInstance = null;

function updateAnalysisCharts(data) {
    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

    let revLabels = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'];
    let revData = (data.projections && data.projections.revenue_curve) ? data.projections.revenue_curve : [0, 0, 0, 0, 0];

    const ctx1 = document.getElementById('viabilityChart')?.getContext('2d');
    if (ctx1) {
        if (viabilityChartInstance) viabilityChartInstance.destroy();
        viabilityChartInstance = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: revLabels,
                datasets: [{
                    label: 'Revenue ($)',
                    data: revData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    fill: true
                }]
            },
            options: { responsive: true }
        });
    }

    const demandScore = clamp((data.market_demand || 5), 0, 10);
    const competitionScore = clamp(10 - (data.competition || 5), 0, 10);
    const innovationScore = clamp(data.viability_score / 10, 0, 10);
    const scalabilityScore = clamp((data.experience || 5) * 2, 0, 10);
    const riskScore = (() => {
        const rl = (data.risk_level || "").toLowerCase();
        if (rl === 'high') return 3;
        if (rl === 'medium') return 6;
        return 9;
    })();

    const ctx2 = document.getElementById('marketChart')?.getContext('2d');
    if (ctx2) {
        if (marketChartInstance) marketChartInstance.destroy();
        marketChartInstance = new Chart(ctx2, {
            type: 'radar',
            data: {
                labels: ['Demand', 'Competition', 'Innovation', 'Scalability', 'Risk'],
                datasets: [{
                    label: 'Market Fit',
                    data: [demandScore, competitionScore, innovationScore, scalabilityScore, riskScore],
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: '#10b981'
                }]
            },
            options: { responsive: true }
        });
    }
}

/* ---------------- AI CHAT WIDGET ---------------- */

function setupAIChat() {
    const toggleBtn = document.getElementById('ai-chat-toggle');
    const closeBtn = document.getElementById('ai-chat-close');
    const header = document.getElementById('ai-chat-header');
    const panel = document.getElementById('ai-chat-panel');
    const sendBtn = document.getElementById('ai-chat-send');
    const input = document.getElementById('ai-chat-input');
    const messages = document.getElementById('ai-chat-messages');

    if (!toggleBtn || !panel || !sendBtn || !input || !messages) return;

    const openPanel = () => {
        panel.classList.remove('hidden');
        input.focus();
    };

    const closePanel = () => {
        panel.classList.add('hidden');
    };

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (panel.classList.contains('hidden')) openPanel();
        else closePanel();
    });

    if (closeBtn) closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closePanel();
    });

    if (header) header.addEventListener('click', (e) => {
        if (e.target === closeBtn) return;
        closePanel();
    });

    document.addEventListener('click', (e) => {
        if (panel.classList.contains('hidden')) return;
        if (panel.contains(e.target) || toggleBtn.contains(e.target)) return;
        closePanel();
    });

    sendBtn.addEventListener('click', () => sendAIMessage(input, messages));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendAIMessage(input, messages);
        }
    });
}

function appendChatBubble(messages, role, text, highlight) {
    const bubble = document.createElement('div');
    bubble.className = `ai-chat-bubble ${role === 'user' ? 'ai-chat-bubble-user' : 'ai-chat-bubble-bot'}`;

    if (highlight && text.includes(highlight)) {
        const parts = text.split(highlight);
        bubble.append(document.createTextNode(parts[0]));
        const highlightSpan = document.createElement('span');
        highlightSpan.className = 'ai-chat-highlight';
        highlightSpan.textContent = highlight;
        bubble.append(highlightSpan);
        bubble.append(document.createTextNode(parts.slice(1).join(highlight)));
    } else {
        bubble.textContent = text;
    }

    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
}

function appendTypingBubble(messages) {
    const bubble = document.createElement('div');
    bubble.className = 'ai-chat-bubble ai-chat-bubble-bot ai-chat-typing';
    const dots = document.createElement('div');
    dots.className = 'ai-chat-dots';
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        dots.appendChild(dot);
    }
    bubble.appendChild(dots);
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
}

async function sendAIMessage(input, messages) {
    const query = input.value.trim();
    if (!query) return;

    appendChatBubble(messages, 'user', query);
    input.value = '';

    const typingBubble = appendTypingBubble(messages);

    try {
        const response = await fetchWithAuth(API_URLS.aiChat, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) throw new Error('AI request failed');
        const data = await response.json();

        typingBubble.remove();
        appendChatBubble(messages, 'bot', data.text || 'No response available.', data.highlight);
    } catch (error) {
        console.error("AI Chat Error:", error);
        typingBubble.remove();
        appendChatBubble(messages, 'bot', 'Sorry, I could not process that request right now.');
    }
}

/* ---------------- CSV UPLOAD ---------------- */

async function uploadCSV() {
    const fileInput = document.getElementById('csvFile');
    const replaceCheckbox = document.getElementById('replaceData');
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a CSV file first.");
        return;
    }

    const mode = replaceCheckbox && replaceCheckbox.checked ? "replace" : "upsert";

    // Warning for replacement
    if (mode === "replace") {
        if (!confirm("WARNING: This will DELETE all existing sales records before uploading. Continue?")) {
            return;
        }
    }

    const formData = new FormData();
    formData.append("file", file);

    const uploadBtn = document.querySelector('button[onclick="uploadCSV()"]');
    if (uploadBtn) {
        uploadBtn.innerText = "Uploading...";
        uploadBtn.disabled = true;
    }

    try {
        const response = await fetchWithAuth(`/upload/csv?mode=${mode}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }

        const result = await response.json();
        alert(result.message);
        window.location.reload();

    } catch (error) {
        console.error("Upload Error:", error);
        alert("Error: " + error.message);
    } finally {
        if (uploadBtn) {
            uploadBtn.innerText = "Upload & Refresh";
            uploadBtn.disabled = false;
        }
        fileInput.value = "";
    }
}

/* ---------------- THEME TOGGLE ---------------- */

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
}

function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

/* ====================================================================
   PHASE 1: ORDER MANAGEMENT
   ==================================================================== */

let currentOrderPage = 1;
let selectedOrderIds = new Set();
let orderSearchTimer = null;

function debounceOrderSearch() {
    clearTimeout(orderSearchTimer);
    orderSearchTimer = setTimeout(() => loadOrders(), 350);
}

async function loadOrders(page) {
    if (page) currentOrderPage = page;
    const search = document.getElementById('orderSearch')?.value || '';
    const status = document.getElementById('orderStatusFilter')?.value || '';
    const dateFrom = document.getElementById('orderDateFrom')?.value || '';
    const dateTo = document.getElementById('orderDateTo')?.value || '';

    const params = new URLSearchParams({
        page: currentOrderPage,
        page_size: 20,
        sort_by: 'order_date',
        sort_dir: 'desc'
    });
    if (search) params.set('search', search);
    if (status) params.set('status', status);
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);

    try {
        const res = await fetchWithAuth(`${API_URLS.searchOrders}?${params}`);
        const data = await res.json();
        renderOrdersTable(data);
        renderPagination(data);
    } catch (e) {
        handleFetchError(e, 'load orders');
    }
}

function renderOrdersTable(data) {
    const tbody = document.getElementById('ordersTableBody');
    if (!tbody) return;

    if (!data.orders || data.orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="padding:24px;text-align:center;color:#64748b;">No orders found</td></tr>';
        return;
    }

    const statusClass = (s) => {
        const map = { 'Pending': 'status-pending', 'Shipped': 'status-shipped', 'Delivered': 'status-delivered', 'Cancelled': 'status-cancelled' };
        return map[s] || 'status-pending';
    };

    tbody.innerHTML = data.orders.map(o => `
        <tr>
            <td><input type="checkbox" class="order-checkbox" data-id="${o.id}" ${selectedOrderIds.has(o.id) ? 'checked' : ''} onchange="toggleOrderSelect(${o.id}, this.checked)"></td>
            <td class="order-id-cell">${o.order_id}</td>
            <td>${o.product_name}</td>
            <td>${o.category || '-'}</td>
            <td>${o.quantity}</td>
            <td>$${Number(o.unit_price).toFixed(2)}</td>
            <td>${o.order_date || '-'}</td>
            <td>
                <select class="inline-status-select" onchange="updateSingleOrderStatus(${o.id}, this.value)">
                    ${['Pending', 'Shipped', 'Delivered', 'Cancelled'].map(s => `<option value="${s}" ${o.delivery_status === s ? 'selected' : ''}>${s}</option>`).join('')}
                </select>
            </td>
            <td>${o.country || '-'}</td>
            <td class="actions-cell">
                <div style="display: flex; gap: 4px;">
                    <button class="btn btn-outline btn-sm" onclick="generateInvoiceForOrder('${o.order_id}', ${o.unit_price * o.quantity}, '${o.country}')" title="Generate Invoice">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="createShipmentForOrder('${o.order_id}')" title="Ship Product">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>
                    </button>
                    <button class="btn-icon danger" title="Delete" onclick="deleteOrder(${o.id})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderPagination(data) {
    const info = document.getElementById('paginationInfo');
    const controls = document.getElementById('paginationControls');
    if (!info || !controls) return;

    const start = (data.page - 1) * data.page_size + 1;
    const end = Math.min(data.page * data.page_size, data.total);
    info.textContent = data.total > 0 ? `Showing ${start}–${end} of ${data.total} orders` : 'No orders';

    let html = '';
    html += `<button class="pagination-btn" ${data.page <= 1 ? 'disabled' : ''} onclick="loadOrders(${data.page - 1})">← Prev</button>`;

    const maxButtons = 5;
    let startPage = Math.max(1, data.page - Math.floor(maxButtons / 2));
    let endPage = Math.min(data.total_pages, startPage + maxButtons - 1);
    if (endPage - startPage < maxButtons - 1) startPage = Math.max(1, endPage - maxButtons + 1);

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="pagination-btn ${i === data.page ? 'active' : ''}" onclick="loadOrders(${i})">${i}</button>`;
    }

    html += `<button class="pagination-btn" ${data.page >= data.total_pages ? 'disabled' : ''} onclick="loadOrders(${data.page + 1})">Next →</button>`;
    controls.innerHTML = html;
}

function toggleOrderSelect(id, checked) {
    if (checked) selectedOrderIds.add(id);
    else selectedOrderIds.delete(id);
    updateBulkBar();
}

function toggleSelectAll(checkbox) {
    document.querySelectorAll('#ordersTableBody .order-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
        const id = parseInt(cb.dataset.id);
        if (checkbox.checked) selectedOrderIds.add(id);
        else selectedOrderIds.delete(id);
    });
    updateBulkBar();
}

function updateBulkBar() {
    const bar = document.getElementById('bulkActionsBar');
    const count = document.getElementById('selectedCount');
    if (selectedOrderIds.size > 0) {
        bar.classList.add('visible');
        count.textContent = `${selectedOrderIds.size} selected`;
    } else {
        bar.classList.remove('visible');
    }
}

function clearSelection() {
    selectedOrderIds.clear();
    document.querySelectorAll('#ordersTableBody .order-checkbox').forEach(cb => cb.checked = false);
    const selectAll = document.getElementById('selectAllOrders');
    if (selectAll) selectAll.checked = false;
    updateBulkBar();
}

async function updateSingleOrderStatus(orderId, newStatus) {
    try {
        await fetchWithAuth(`/sales/${orderId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ delivery_status: newStatus })
        });
    } catch (e) {
        alert('Failed to update status');
        loadOrders();
    }
}

async function bulkUpdateStatus() {
    if (selectedOrderIds.size === 0) return;
    const newStatus = document.getElementById('bulkStatusSelect').value;
    try {
        const res = await fetchWithAuth(API_URLS.bulkStatus, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_ids: Array.from(selectedOrderIds), new_status: newStatus })
        });
        const data = await res.json();
        alert(data.message);
        clearSelection();
        loadOrders();
    } catch (e) {
        alert('Failed to bulk update');
    }
}

async function deleteOrder(orderId) {
    if (!confirm('Are you sure you want to delete this order?')) return;
    try {
        await fetchWithAuth(`/sales/${orderId}`, { method: 'DELETE' });
        loadOrders();
    } catch (e) {
        alert('Failed to delete order');
    }
}

function openCreateOrderModal() {
    document.getElementById('newOrderDate').value = new Date().toISOString().split('T')[0];
    openModal('createOrderModal');
}

async function submitCreateOrder() {
    const payload = {
        order_id: document.getElementById('newOrderId').value.trim(),
        product_name: document.getElementById('newProductName').value.trim(),
        category: document.getElementById('newCategory').value.trim() || 'General',
        quantity: parseInt(document.getElementById('newQuantity').value) || 1,
        unit_price: parseFloat(document.getElementById('newUnitPrice').value) || 0,
        unit_cost: parseFloat(document.getElementById('newUnitCost').value) || 0,
        order_date: document.getElementById('newOrderDate').value || null,
        country: document.getElementById('newCountry').value.trim() || 'Global',
        region_risk_score: parseFloat(document.getElementById('newRiskScore').value) || 5,
    };

    if (!payload.order_id || !payload.product_name) {
        alert('Order ID and Product Name are required.');
        return;
    }

    try {
        const res = await fetchWithAuth('/sales/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const err = await res.json();
            alert('Error: ' + (err.detail || 'Failed to create order'));
            return;
        }
        alert('Order created!');
        closeModal('createOrderModal');
        loadOrders();
    } catch (e) {
        alert('Failed to create order');
    }
}

function exportOrders() {
    fetchWithAuth(API_URLS.exportSales)
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `orders_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        })
        .catch(e => alert('Export failed'));
}

/* ====================================================================
   PHASE 1: INVENTORY MANAGEMENT
   ==================================================================== */

async function loadInventoryItems() {
    try {
        const res = await fetchWithAuth(API_URLS.inventoryList);
        const data = await res.json();
        const tbody = document.getElementById('inventoryManageBody');
        if (!tbody) return;

        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="padding:24px;text-align:center;color:#64748b;">No inventory items. Click "Add Item" to get started.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(item => `
            <tr>
                <td style="font-weight:500;">${item.product_name}</td>
                <td>
                    <span class="status-badge ${item.stock_level <= 0 ? 'status-cancelled' : item.stock_level <= 10 ? 'status-pending' : 'status-delivered'}">
                        ${item.stock_level}
                    </span>
                </td>
                <td>${item.reorder_point}</td>
                <td>${item.last_updated ? new Date(item.last_updated).toLocaleDateString() : 'N/A'}</td>
                <td class="actions-cell">
                    <button class="btn-icon" title="Adjust Stock" onclick="openAdjustStockModal(${item.id}, '${item.product_name.replace(/'/g, '\\&#39;')}', ${item.stock_level})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10"></path><path d="M18 20V4"></path><path d="M6 20v-4"></path></svg>
                    </button>
                    <button class="btn-icon" title="Edit" onclick="openEditInventoryModal(${item.id}, '${item.product_name.replace(/'/g, '\\&#39;')}', ${item.stock_level}, ${item.reorder_point})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button class="btn-icon danger" title="Delete" onclick="deleteInventoryItem(${item.id}, '${item.product_name.replace(/'/g, '\\&#39;')}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        handleFetchError(e, 'load inventory items');
    }
}

function openAddInventoryModal() {
    document.getElementById('invProductName').value = '';
    document.getElementById('invStockLevel').value = '0';
    document.getElementById('invReorderPoint').value = '10';
    openModal('addInventoryModal');
}

async function submitAddInventory() {
    const payload = {
        product_name: document.getElementById('invProductName').value.trim(),
        stock_level: parseInt(document.getElementById('invStockLevel').value) || 0,
        reorder_point: parseInt(document.getElementById('invReorderPoint').value) || 10,
    };
    if (!payload.product_name) { alert('Product name is required.'); return; }

    try {
        const res = await fetchWithAuth(API_URLS.inventoryList, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const err = await res.json();
            alert('❌ ' + (err.detail || 'Failed'));
            return;
        }
        alert('Inventory item added!');
        closeModal('addInventoryModal');
        loadInventoryItems();
        fetchInventoryHealth();
    } catch (e) {
        alert('Failed to add item');
    }
}

function openEditInventoryModal(id, name, stock, reorder) {
    document.getElementById('editInvId').value = id;
    document.getElementById('editInvProductName').value = name;
    document.getElementById('editInvStockLevel').value = stock;
    document.getElementById('editInvReorderPoint').value = reorder;
    openModal('editInventoryModal');
}

async function submitEditInventory() {
    const id = document.getElementById('editInvId').value;
    const payload = {
        stock_level: parseInt(document.getElementById('editInvStockLevel').value),
        reorder_point: parseInt(document.getElementById('editInvReorderPoint').value),
    };
    try {
        const res = await fetchWithAuth(`/inventory/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) { alert('Failed to update'); return; }
        alert('Item updated!');
        closeModal('editInventoryModal');
        loadInventoryItems();
        fetchInventoryHealth();
    } catch (e) {
        alert('Failed to update');
    }
}

async function deleteInventoryItem(id, name) {
    if (!confirm(`Delete "${name}" from inventory?`)) return;
    try {
        await fetchWithAuth(`/inventory/${id}`, { method: 'DELETE' });
        loadInventoryItems();
        fetchInventoryHealth();
    } catch (e) {
        alert('Failed to delete');
    }
}

function openAdjustStockModal(id, name, currentStock) {
    document.getElementById('adjustInvId').value = id;
    document.getElementById('adjustProductName').textContent = name;
    document.getElementById('adjustCurrentStock').textContent = currentStock;
    document.getElementById('adjustAmount').value = '';
    document.getElementById('adjustReason').value = 'Restock';
    openModal('adjustStockModal');
}

async function submitStockAdjustment() {
    const id = document.getElementById('adjustInvId').value;
    const adjustment = parseInt(document.getElementById('adjustAmount').value);
    const reason = document.getElementById('adjustReason').value;

    if (isNaN(adjustment) || adjustment === 0) { alert('Enter a valid non-zero adjustment.'); return; }

    try {
        const res = await fetchWithAuth(`/inventory/${id}/adjust`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ adjustment, reason })
        });
        if (!res.ok) {
            const err = await res.json();
            alert('❌ ' + (err.detail || 'Failed'));
            return;
        }
        const data = await res.json();
        alert(data.message);
        closeModal('adjustStockModal');
        loadInventoryItems();
        fetchInventoryHealth();
    } catch (e) {
        alert('Adjustment failed');
    }
}

function exportInventory() {
    fetchWithAuth(API_URLS.exportInventory)
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `inventory_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        })
        .catch(e => alert('Export failed'));
}

/* ====================================================================
   MODAL HELPERS
   ==================================================================== */

function openModal(id) {
    document.getElementById(id).style.display = 'flex';
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

/* ====================================================================
   PHASE 2: SUPPLIER MANAGEMENT
   ==================================================================== */

let supplierSearchTimer = null;

function debounceSupplierSearch() {
    clearTimeout(supplierSearchTimer);
    supplierSearchTimer = setTimeout(() => loadSuppliers(), 400);
}

async function loadSuppliers() {
    try {
        const search = document.getElementById('supplierSearch')?.value || '';
        let url = API_URLS.suppliersList;
        if (search) url += `?search=${encodeURIComponent(search)}`;
        const res = await fetchWithAuth(url);
        if (!res.ok) throw new Error('Failed to load suppliers');
        const data = await res.json();
        renderSuppliersTable(data);
    } catch (err) { handleFetchError(err, 'loadSuppliers'); }
}

function renderSuppliersTable(items) {
    const tbody = document.getElementById('suppliersTableBody');
    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="padding:24px;text-align:center;color:#64748b;">No suppliers found. Click "Add Supplier" to get started.</td></tr>';
        return;
    }
    tbody.innerHTML = items.map(s => {
        const reliPct = (s.reliability_score / 10 * 100).toFixed(0);
        const reliColor = s.reliability_score >= 7 ? '#10b981' : s.reliability_score >= 4 ? '#f59e0b' : '#ef4444';
        return `<tr>
            <td><strong>${s.name}</strong></td>
            <td>${s.contact_name || '—'}</td>
            <td>${s.email || '—'}</td>
            <td>${s.country || '—'}</td>
            <td>${s.lead_time_days} days</td>
            <td>
                <div class="reliability-bar">
                    <div class="reliability-fill" style="width:${reliPct}%;background:${reliColor};"></div>
                </div>
                <span style="font-size:11px;color:#64748b;">${s.reliability_score}/10</span>
            </td>
            <td>
                <button class="btn-action btn-edit" onclick='openEditSupplierModal(${JSON.stringify(s)})' title="Edit">✏️</button>
                <button class="btn-action btn-delete" onclick="deleteSupplier(${s.id})" title="Delete">🗑️</button>
            </td>
        </tr>`;
    }).join('');
}

function openAddSupplierModal() {
    ['supName', 'supContact', 'supEmail', 'supPhone', 'supCountry', 'supNotes'].forEach(id => {
        const el = document.getElementById(id); if (el) el.value = '';
    });
    document.getElementById('supLeadTime').value = '7';
    document.getElementById('supReliability').value = '5';
    openModal('addSupplierModal');
}

async function submitAddSupplier() {
    const name = document.getElementById('supName').value.trim();
    if (!name) return alert('Supplier name is required.');
    const body = {
        name,
        contact_name: document.getElementById('supContact').value.trim() || null,
        email: document.getElementById('supEmail').value.trim() || null,
        phone: document.getElementById('supPhone').value.trim() || null,
        country: document.getElementById('supCountry').value.trim() || null,
        lead_time_days: parseInt(document.getElementById('supLeadTime').value) || 7,
        reliability_score: parseFloat(document.getElementById('supReliability').value) || 5,
        notes: document.getElementById('supNotes').value.trim() || null,
    };
    try {
        const res = await fetchWithAuth(API_URLS.suppliersList, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Failed'); }
        closeModal('addSupplierModal');
        loadSuppliers();
    } catch (err) { alert('Error: ' + err.message); }
}

function openEditSupplierModal(s) {
    document.getElementById('editSupId').value = s.id;
    document.getElementById('editSupName').value = s.name || '';
    document.getElementById('editSupContact').value = s.contact_name || '';
    document.getElementById('editSupEmail').value = s.email || '';
    document.getElementById('editSupPhone').value = s.phone || '';
    document.getElementById('editSupCountry').value = s.country || '';
    document.getElementById('editSupLeadTime').value = s.lead_time_days || 7;
    document.getElementById('editSupReliability').value = s.reliability_score || 5;
    document.getElementById('editSupNotes').value = s.notes || '';
    openModal('editSupplierModal');
}

async function submitEditSupplier() {
    const id = document.getElementById('editSupId').value;
    const body = {
        name: document.getElementById('editSupName').value.trim() || null,
        contact_name: document.getElementById('editSupContact').value.trim() || null,
        email: document.getElementById('editSupEmail').value.trim() || null,
        phone: document.getElementById('editSupPhone').value.trim() || null,
        country: document.getElementById('editSupCountry').value.trim() || null,
        lead_time_days: parseInt(document.getElementById('editSupLeadTime').value) || null,
        reliability_score: parseFloat(document.getElementById('editSupReliability').value) || null,
        notes: document.getElementById('editSupNotes').value.trim() || null,
    };
    try {
        const res = await fetchWithAuth(`${API_URLS.suppliersList}${id}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Failed'); }
        closeModal('editSupplierModal');
        loadSuppliers();
    } catch (err) { alert('Error: ' + err.message); }
}

async function deleteSupplier(id) {
    if (!confirm('Delete this supplier?')) return;
    try {
        const res = await fetchWithAuth(`${API_URLS.suppliersList}${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        loadSuppliers();
    } catch (err) { alert('Error: ' + err.message); }
}

async function exportSuppliers() {
    try {
        const res = await fetchWithAuth(API_URLS.exportSuppliers);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'suppliers.csv'; a.click();
        URL.revokeObjectURL(url);
    } catch (err) { alert('Export failed: ' + err.message); }
}

/* ====================================================================
   PHASE 2: CUSTOMER MANAGEMENT
   ==================================================================== */

let customerSearchTimer = null;

function debounceCustomerSearch() {
    clearTimeout(customerSearchTimer);
    customerSearchTimer = setTimeout(() => loadCustomers(), 400);
}

async function loadCustomers() {
    try {
        const search = document.getElementById('customerSearch')?.value || '';
        const segment = document.getElementById('customerSegmentFilter')?.value || '';
        let url = API_URLS.customersList;
        const params = new URLSearchParams();
        if (search) params.set('search', search);
        if (segment) params.set('segment', segment);
        const qs = params.toString();
        if (qs) url += `?${qs}`;
        const res = await fetchWithAuth(url);
        if (!res.ok) throw new Error('Failed to load customers');
        const data = await res.json();
        renderCustomersTable(data);
    } catch (err) { handleFetchError(err, 'loadCustomers'); }
}

function renderCustomersTable(items) {
    const tbody = document.getElementById('customersTableBody');
    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="padding:24px;text-align:center;color:#64748b;">No customers found. Click "Add Customer" to get started.</td></tr>';
        return;
    }
    const segColor = s => s === 'VIP' ? '#8b5cf6' : s === 'Regular' ? '#3b82f6' : '#10b981';
    tbody.innerHTML = items.map(c => `<tr>
        <td><strong>${c.name}</strong></td>
        <td>${c.email || '—'}</td>
        <td>${c.phone || '—'}</td>
        <td><span class="segment-badge" style="background:${segColor(c.segment)}20;color:${segColor(c.segment)};border:1px solid ${segColor(c.segment)}40;">${c.segment}</span></td>
        <td>${c.total_orders}</td>
        <td>$${(c.total_revenue || 0).toLocaleString()}</td>
        <td>
            <button class="btn-action btn-edit" onclick='openEditCustomerModal(${JSON.stringify(c)})' title="Edit">✏️</button>
            <button class="btn-action btn-delete" onclick="deleteCustomer(${c.id})" title="Delete">🗑️</button>
        </td>
    </tr>`).join('');
}

function openAddCustomerModal() {
    ['custName', 'custEmail', 'custPhone', 'custAddress', 'custNotes'].forEach(id => {
        const el = document.getElementById(id); if (el) el.value = '';
    });
    document.getElementById('custSegment').value = 'Regular';
    openModal('addCustomerModal');
}

async function submitAddCustomer() {
    const name = document.getElementById('custName').value.trim();
    if (!name) return alert('Customer name is required.');
    const body = {
        name,
        email: document.getElementById('custEmail').value.trim() || null,
        phone: document.getElementById('custPhone').value.trim() || null,
        segment: document.getElementById('custSegment').value,
        address: document.getElementById('custAddress').value.trim() || null,
        notes: document.getElementById('custNotes').value.trim() || null,
    };
    try {
        const res = await fetchWithAuth(API_URLS.customersList, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Failed'); }
        closeModal('addCustomerModal');
        loadCustomers();
    } catch (err) { alert('Error: ' + err.message); }
}

function openEditCustomerModal(c) {
    document.getElementById('editCustId').value = c.id;
    document.getElementById('editCustName').value = c.name || '';
    document.getElementById('editCustEmail').value = c.email || '';
    document.getElementById('editCustPhone').value = c.phone || '';
    document.getElementById('editCustSegment').value = c.segment || 'Regular';
    document.getElementById('editCustAddress').value = c.address || '';
    document.getElementById('editCustNotes').value = c.notes || '';
    openModal('editCustomerModal');
}

async function submitEditCustomer() {
    const id = document.getElementById('editCustId').value;
    const body = {
        name: document.getElementById('editCustName').value.trim() || null,
        email: document.getElementById('editCustEmail').value.trim() || null,
        phone: document.getElementById('editCustPhone').value.trim() || null,
        segment: document.getElementById('editCustSegment').value || null,
        address: document.getElementById('editCustAddress').value.trim() || null,
        notes: document.getElementById('editCustNotes').value.trim() || null,
    };
    try {
        const res = await fetchWithAuth(`${API_URLS.customersList}${id}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Failed'); }
        closeModal('editCustomerModal');
        loadCustomers();
    } catch (err) { alert('Error: ' + err.message); }
}

async function deleteCustomer(id) {
    if (!confirm('Delete this customer?')) return;
    try {
        const res = await fetchWithAuth(`${API_URLS.customersList}${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        loadCustomers();
    } catch (err) { alert('Error: ' + err.message); }
}

async function exportCustomers() {
    try {
        const res = await fetchWithAuth(API_URLS.exportCustomers);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'customers.csv'; a.click();
        URL.revokeObjectURL(url);
    } catch (err) { alert('Export failed: ' + err.message); }
}

/* ====================================================================
   PHASE 2: TEAM MANAGEMENT
   ==================================================================== */

async function loadTeamMembers() {
    try {
        const res = await fetchWithAuth(API_URLS.teamMembers);
        if (!res.ok) throw new Error('Failed to load team');
        const data = await res.json();
        const tbody = document.getElementById('teamMembersBody');
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="3" style="padding:24px;text-align:center;color:#64748b;">No team members found.</td></tr>';
            return;
        }
        tbody.innerHTML = data.map(m => `<tr>
            <td><strong>${m.username}</strong></td>
            <td>${m.email}</td>
            <td><span class="segment-badge" style="background:${m.role === 'Owner' ? '#8b5cf620' : '#3b82f620'};color:${m.role === 'Owner' ? '#8b5cf6' : '#3b82f6'};border:1px solid ${m.role === 'Owner' ? '#8b5cf640' : '#3b82f640'};">${m.role}</span></td>
        </tr>`).join('');
    } catch (err) { handleFetchError(err, 'loadTeamMembers'); }
}

async function loadPendingInvites() {
    try {
        const res = await fetchWithAuth(API_URLS.teamInvites);
        const tbody = document.getElementById('pendingInvitesBody');
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="4" style="padding:24px;text-align:center;color:#64748b;">Could not load invites (owner access required).</td></tr>';
            return;
        }
        const data = await res.json();
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="4" style="padding:24px;text-align:center;color:#64748b;">No pending invitations.</td></tr>';
            return;
        }
        tbody.innerHTML = data.map(inv => `<tr>
            <td>${inv.invited_email}</td>
            <td><span class="status-badge status-pending">${inv.status}</span></td>
            <td>${inv.created_at ? new Date(inv.created_at).toLocaleDateString() : '—'}</td>
            <td>${inv.expires_at ? new Date(inv.expires_at).toLocaleDateString() : '—'}</td>
        </tr>`).join('');
    } catch (err) { handleFetchError(err, 'loadPendingInvites'); }
}

async function sendTeamInvite() {
    const email = document.getElementById('inviteEmail').value.trim();
    if (!email) return alert('Please enter an email address.');
    try {
        const res = await fetchWithAuth(API_URLS.teamSendInvite, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ invited_email: email })
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Failed to send invite'); }
        document.getElementById('inviteEmail').value = '';
        alert('Invitation sent successfully!');
        loadPendingInvites();
    } catch (err) { alert('Error: ' + err.message); }
}

/* ---------------- INIT ---------------- */

initializeTheme();

document.addEventListener('DOMContentLoaded', () => {
    showSection('executive');
    setInterval(() => {
        const activeSection = Array.from(document.querySelectorAll('.dashboard-section'))
            .find(s => !s.classList.contains('hidden'))?.id.replace('-section', '');
        if (activeSection === 'executive') loadDataForSection('executive');
        if (activeSection === 'automation') loadDataForSection('automation');
    }, 30000);
    setupAIChat();
    setupThemeToggle();
});
/* ---------------- EMAIL AUTOMATION HANDLING ---------------- */

async function loadAutomations() {
    try {
        const response = await fetchWithAuth(API_URLS.listAutomations);
        if (!response.ok) throw new Error("Failed to fetch automations");
        const data = await response.json();

        const tbody = document.getElementById('automationTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px;">No active automations. Setup one to automate CSV uploads!</td></tr>';
            return;
        }

        data.forEach(item => {
            const tr = document.createElement('tr');
            const statusClass = item.is_verified ? 'status-pill status-active' : 'status-pill status-pending';
            const statusText = item.is_verified ? 'Active' : 'Pending Verification';

            // Calculate time remaining if applicable
            let durationInfo = '-';
            if (item.expires_at) {
                const now = new Date();
                const exp = new Date(item.expires_at);
                const diffTime = exp - now;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                durationInfo = diffDays > 0 ? `${diffDays} days left` : 'Expired';
            }

            tr.innerHTML = `
                <td>${item.sender_email}</td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td>${durationInfo}</td>
                <td>${item.expires_at || 'Never'}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="handleDeleteAutomation(${item.id})">Remove</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        handleFetchError(e, "load automations");
    }
}

function openAddAutomationModal() {
    resetAutomationModal();
    openModal('addAutomationModal');
}

function resetAutomationModal() {
    document.getElementById('automation-step-1').classList.remove('hidden');
    document.getElementById('automation-step-2').classList.add('hidden');
    document.getElementById('requestOtpForm').reset();
    document.getElementById('verifyOtpForm').reset();
}

async function submitRequestOTP() {
    const email = document.getElementById('autoSenderEmail').value;
    try {
        const response = await fetchWithAuth(API_URLS.requestOtp, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender_email: email })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to request OTP");
        }

        // Show next step
        document.getElementById('automation-step-1').classList.add('hidden');
        document.getElementById('automation-step-2').classList.remove('hidden');
        alert(`A verification code has been sent to ${email}. Please check your inbox (including spam).`);
    } catch (e) {
        alert(e.message);
    }
}

async function submitVerifyOTP() {
    const email = document.getElementById('autoSenderEmail').value;
    const otp = document.getElementById('autoOtpCode').value;
    const duration = parseInt(document.getElementById('autoDuration').value);

    try {
        const response = await fetchWithAuth(API_URLS.verifyOtp, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender_email: email,
                otp_code: otp,
                duration_days: duration
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Verification failed");
        }

        alert("Automation activated successfully!");
        closeModal('addAutomationModal');
        loadAutomations();
    } catch (e) {
        alert(e.message);
    }
}

async function handleDeleteAutomation(id) {
    if (!confirm("Are you sure you want to remove this automation? The sender will no longer be able to upload files automatically.")) return;

    try {
        const response = await fetchWithAuth(`${API_URLS.deleteAutomation}/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error("Delete failed");

        alert("Automation removed.");
        loadAutomations();
    } catch (e) {
        alert(e.message);
    }
}
/* ---------------- FINANCE & LOGISTICS ---------------- */

async function loadInvoices() {
    try {
        const res = await fetchWithAuth(API_URLS.financeInvoices);
        const invoices = await res.json();
        const tbody = document.querySelector('#invoicesTable tbody');
        tbody.innerHTML = invoices.map(inv => `
            <tr>
                <td class="font-bold">${inv.invoice_number}</td>
                <td>${inv.order_id}</td>
                <td>${inv.customer_name || 'N/A'}</td>
                <td>${new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(inv.amount)}</td>
                <td>${inv.due_date}</td>
                <td><span class="badge ${getStatusBadgeClass(inv.status)}">${inv.status}</span></td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="alert('PDF Generation Coming Soon')">
                        Download
                    </button>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="7" class="text-center">No invoices found.</td></tr>';
        loadActivityLogs('Finance', '#financeLogsTable tbody');
    } catch (e) { console.error("Failed to load invoices", e); }
}

async function loadLogistics() {
    try {
        const [shipRes, retRes] = await Promise.all([
            fetchWithAuth(API_URLS.logisticsShipments),
            fetchWithAuth(API_URLS.logisticsReturns)
        ]);
        const shipments = await shipRes.json();
        const returns = await retRes.json();

        const shipTbody = document.querySelector('#shipmentsTable tbody');
        shipTbody.innerHTML = shipments.map(s => `
            <tr>
                <td><code>${s.tracking_number}</code></td>
                <td>${s.order_id}</td>
                <td>${s.carrier}</td>
                <td><span class="badge ${getStatusBadgeClass(s.status)}">${s.status}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="4" class="text-center">No active shipments.</td></tr>';

        const retTbody = document.querySelector('#returnsTable tbody');
        retTbody.innerHTML = returns.map(r => `
            <tr>
                <td>${r.order_id}</td>
                <td>${r.reason}</td>
                <td><span class="badge badge-outline">${r.refund_status}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="3" class="text-center">No returns processed.</td></tr>';
        loadActivityLogs('Logistics', '#logisticsLogsTable tbody');
    } catch (e) { console.error("Failed to load logistics", e); }
}

function getStatusBadgeClass(status) {
    const s = status.toLowerCase();
    if (s.includes('paid') || s.includes('delivered') || s.includes('success')) return 'badge-success';
    if (s.includes('unpaid') || s.includes('pending')) return 'badge-warning';
    if (s.includes('overdue') || s.includes('exception')) return 'badge-error';
    return 'badge-outline';
}

async function generateInvoiceForOrder(orderId, amount, customer) {
    if (!confirm(`Generate invoice for Order ${orderId} in the amount of $${amount.toFixed(2)}?`)) return;

    try {
        const payload = {
            order_id: orderId,
            customer_name: customer || "Standard Customer",
            amount: amount,
            status: "Unpaid",
            due_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // 2 weeks from now
        };

        const res = await fetchWithAuth(API_URLS.financeInvoices, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Failed to generate invoice");

        alert("Invoice generated successfully! View it in the Finance section.");
        showSection('finance');
    } catch (e) { alert(e.message); }
}

async function createShipmentForOrder(orderId) {
    if (!confirm(`Initialize shipment for Order ${orderId}?`)) return;

    try {
        const payload = {
            order_id: orderId,
            carrier: "BlueDart Global",
            estimated_delivery: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            status: "Pending"
        };

        const res = await fetchWithAuth(API_URLS.logisticsShipments, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Failed to create shipment");

        alert("Shipment tracking initialized! View it in the Logistics section.");
        showSection('logistics');
    } catch (e) { alert(e.message); }
}

/* ---------------- NOTIFICATIONS & ACTIVITY ---------------- */

function toggleNotifications() {
    const panel = document.getElementById('notificationPanel');
    panel.classList.toggle('hidden');
    if (!panel.classList.contains('hidden')) {
        fetchNotifications();
    }
}

async function fetchNotifications() {
    try {
        const res = await fetchWithAuth(API_URLS.activityNotifications);
        const notifications = await res.json();
        const list = document.getElementById('notificationList');
        const count = document.getElementById('notificationCount');

        const unread = notifications.filter(n => !n.is_read);
        if (unread.length > 0) {
            count.innerText = unread.length;
            count.classList.remove('hidden');
        } else {
            count.classList.add('hidden');
        }

        if (notifications.length === 0) {
            list.innerHTML = '<p class="empty-msg">No notifications.</p>';
            return;
        }

        list.innerHTML = notifications.map(n => `
            <div class="notification-item ${n.is_read ? 'read' : 'unread'}" onclick="markAsRead(${n.id})">
                <div class="notif-content">
                    <h4>${n.title}</h4>
                    <p>${n.message}</p>
                    <span class="notif-time">${new Date(n.created_at || Date.now()).toLocaleTimeString()}</span>
                </div>
            </div>
        `).join('');
    } catch (e) { console.error("Failed to fetch notifications", e); }
}

async function markAsRead(id) {
    try {
        await fetchWithAuth(`${API_URLS.activityNotifications}/read/${id}`, { method: 'POST' });
        fetchNotifications();
    } catch (e) { console.error("Fail", e); }
}

async function markAllNotificationsAsRead() {
    // Basic implementation: fetch current notifications and mark each
    const list = document.getElementById('notificationList');
    const items = list.querySelectorAll('.notification-item.unread');
    if (items.length === 0) return;

    alert("Marking all as read...");
    // Ideally a backend endpoint for this, but we can iterate for now
    fetchNotifications(); // Refresh list
}

async function loadActivityLogs(type, selector) {
    try {
        const res = await fetchWithAuth(`${API_URLS.activityLogs}?entity_type=${type}`);
        const logs = await res.json();
        const tbody = document.querySelector(selector);
        if (!tbody) return;

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td><strong>${l.action}</strong></td>
                <td>${l.entity_type} (#${l.entity_id})</td>
                <td class="text-sm">${l.details || '-'}</td>
                <td><span class="text-xs text-slate-500">${new Date(l.created_at).toLocaleString()}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="4" class="text-center">No recent activity.</td></tr>';
    } catch (e) { console.error("Failed to load logs", e); }
}
