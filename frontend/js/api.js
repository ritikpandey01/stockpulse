// API Client Wrapper
const API_BASE = '/api'; // Stays relative because everything is on Render

const api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('supabase_token');
        const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
            const contentType = response.headers.get("content-type");

            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Server request failed');
                return data;
            } else {
                // This handles the Render "Wake up" HTML screen without crashing
                throw new Error("Backend is waking up...");
            }
        } catch (err) {
            console.error('API Error:', err);
            throw err;
        }
    },
    async get(endpoint) { return this.request(endpoint); },
    async post(endpoint, body) {
        return this.request(endpoint, { method: 'POST', body: JSON.stringify(body) });
    }
};
