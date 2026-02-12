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
    businessViability: `/ai/business-viability`, // Matches Backend
    aiChat: `${API_BASE_URL}/ai/chat`
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

/* ---------------- SECTION HANDLING (Preserved) ---------------- */

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
        if(sectionName === 'business-analysis-results') {
             const fallback = document.getElementById('business-analysis-results-section');
             if(fallback) { fallback.classList.remove('hidden'); return; }
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

    if (typeof loadDataForSection === 'function') {
        loadDataForSection(sectionName);
    }
}


/* ---------------- ERROR HANDLING (Preserved) ---------------- */

function handleFetchError(error, context) {
    console.error(`Failed to ${context}:`, error);
    const errorBanner = document.getElementById('error-banner');
    if(errorBanner) {
        errorBanner.querySelector('#error-message').textContent =
            `Could not connect to backend to ${context}.`;
        errorBanner.classList.remove('hidden');
    }
}

/* ---------------- DASHBOARD DATA (Preserved) ---------------- */

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
    } else if (sectionName === 'sales') {
        fetchAndRenderChart('salesTrend', 'salesChart', initializeLineChart,
            { label: 'Monthly Sales ($)', color: '#8b5cf6' });
    }
}

/* ---------------- KPI & CHART HELPERS (Preserved) ---------------- */

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

/* ---------------- CHART UTILS (Preserved) ---------------- */

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

/* ---------------- FIXED BUSINESS ANALYSIS LOGIC ---------------- */
/* This replaces the old event listener with the function your HTML expects */

async function generateAnalysis() {
    const generateBtn = document.getElementById('generate-btn');
    
    // 1. Correctly get values using IDs that match your HTML
    const industry = document.getElementById('industry').value;
    const marketDemand = document.getElementById('market_demand') ? document.getElementById('market_demand').value : document.getElementById('marketDemand').value; // Handle both ID possibilities safely
    const competition = document.getElementById('competition').value;
    const capitalRange = document.getElementById('capital_range') ? document.getElementById('capital_range').value : document.getElementById('capitalRange').value;
    const experience = document.getElementById('experience').value;
    const ideaText = document.getElementById('business_idea') ? document.getElementById('business_idea').value : document.getElementById('businessIdeaText').value;

    // 2. Validate
    if (!ideaText) {
        alert("Please describe the business idea.");
        return;
    }

    // 3. UI Loading State
    const originalText = generateBtn.innerText;
    generateBtn.innerText = "Analyzing...";
    generateBtn.disabled = true;

    // 4. Construct Payload for Backend
    const payload = {
        industry: industry,
        market_demand: parseInt(marketDemand) || 0,
        competition: parseInt(competition) || 0,
        capital_range: capitalRange,
        experience: parseInt(experience) || 0,
        idea: ideaText
    };

    try {
        // 5. Send Request to FastAPI Backend
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

        // 6. Update UI
        await displayResults(data, ideaText);

    } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to AI backend. Ensure main.py is running!");
    } finally {
        generateBtn.innerText = originalText;
        generateBtn.disabled = false;
    }
}

// Helper to update the Results UI
async function displayResults(data, ideaName) {
    showSection('business-analysis-results');

    document.getElementById('ideaName').innerText = ideaName.length > 30 ? ideaName.substring(0, 30) + "..." : ideaName;
    document.getElementById('score-display').innerText = data.viability_score + "/100";
    document.getElementById('recommendation-text').innerText = data.breakdown || "Analysis Complete";
    
    // Only access projections if they exist
    if (data.projections) {
        document.getElementById('investment-est').innerText = data.projections.estimated_cost;
        document.getElementById('analysisTimeline').innerText = "12-18 Months"; 
    }

    // Risk Badge Color Logic
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

    await updateAnalysisCharts(data);
}

// Helper to Update Charts
let viabilityChartInstance = null;
let marketChartInstance = null;

async function updateAnalysisCharts(data) {
    const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

    // Use model-based projections first; no sales DB dependency
    let revLabels = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'];
    let revData = (data.projections && data.projections.revenue_curve) ? data.projections.revenue_curve : [0,0,0,0,0];

    // Revenue Chart
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

    // Radar Chart
    const ctx2 = document.getElementById('marketChart')?.getContext('2d');
    if (ctx2) {
        if (marketChartInstance) marketChartInstance.destroy();
        marketChartInstance = new Chart(ctx2, {
            type: 'radar',
            data: {
                labels: ['Demand', 'Competition', 'Innovation', 'Scalability', 'Risk'],
                datasets: [{
                    label: 'Market Fit',
                    data: [
                        demandScore,
                        competitionScore,
                        innovationScore,
                        scalabilityScore,
                        riskScore
                    ],
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
        toggleBtn.setAttribute('aria-expanded', 'true');
        panel.setAttribute('aria-hidden', 'false');
        input.focus();
    };

    const closePanel = () => {
        panel.classList.add('hidden');
        toggleBtn.setAttribute('aria-expanded', 'false');
        panel.setAttribute('aria-hidden', 'true');
    };

    toggleBtn.setAttribute('aria-expanded', 'false');
    panel.setAttribute('aria-hidden', 'true');

    toggleBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        if (panel.classList.contains('hidden')) openPanel();
        else closePanel();
    });

    if (closeBtn) closeBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        closePanel();
    });

    if (header) header.addEventListener('click', (event) => {
        if (event.target === closeBtn) return;
        closePanel();
    });

    document.addEventListener('click', (event) => {
        if (panel.classList.contains('hidden')) return;
        if (panel.contains(event.target) || toggleBtn.contains(event.target)) return;
        closePanel();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !panel.classList.contains('hidden')) {
            closePanel();
        }
    });

    sendBtn.addEventListener('click', () => {
        sendAIMessage(input, messages);
    });

    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
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
    for (let i = 0; i < 3; i += 1) {
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

/* ---------------- INIT (Preserved) ---------------- */

document.addEventListener('DOMContentLoaded', () => {
    showSection('executive', { preventDefault() {} });
    setInterval(() => loadDataForSection('executive'), 15000);
    setupAIChat();
});
/* ---------------- UPLOAD LOGIC (Add this to script.js) ---------------- */

async function uploadCSV() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];

    // 1. Safety Check: Did they select a file?
    if (!file) {
        alert("Please select a CSV file first.");
        return;
    }

    // 2. Prepare the Upload
    const formData = new FormData();
    formData.append("file", file);

    const uploadBtn = document.querySelector('button[onclick="uploadCSV()"]');
    if (uploadBtn) {
        uploadBtn.innerText = "Uploading...";
        uploadBtn.disabled = true;
    }

    try {
        // 3. Send to Backend
        // Note: Matches the Python @router.post("/csv") inside prefix="/upload"
        const response = await fetchWithAuth('/upload/csv', { 
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }

        const result = await response.json();
        
        // 4. Success Message
        alert("✅ Success! " + result.message);

        // 5. THE FIX: Reload page to show new data
        window.location.reload();

    } catch (error) {
        console.error("Upload Error:", error);
        alert("❌ Error: " + error.message);
    } finally {
        // Reset Button
        if (uploadBtn) {
            uploadBtn.innerText = "Upload Data";
            uploadBtn.disabled = false;
        }
        // Clear input so they can upload again if needed
        fileInput.value = "";
    }
}




