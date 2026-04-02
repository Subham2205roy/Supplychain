const CONFIG = {
    // Auto-detect: empty for local dev, your Hugging Face backend URL for production
    API_BASE: window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? ""
        : "https://subham2205-supplychain-app.hf.space"  // Hugging Face Backend URL
};
