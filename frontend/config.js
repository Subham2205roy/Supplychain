const CONFIG = {
    API_BASE: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? "http://127.0.0.1:8000"
        : "" // Empty string ensures requests go through Vercel proxy (e.g. /api/...)
};
