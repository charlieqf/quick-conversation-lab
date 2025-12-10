import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

// --- PROXY BYPASS LOGIC ---
// Allows pointing frontend to a different backend (e.g. direct Cloud Run)
const apiOverride = localStorage.getItem('VITE_API_BASE_URL');
if (apiOverride) {
  console.log(`[ProxyBypass] Enabled. Redirecting /api calls to: ${apiOverride}`);
  const originalFetch = window.fetch;
  window.fetch = async (input, init) => {
    let url = input;
    if (typeof url === 'string' && url.startsWith('/api')) {
      // Ensure no double slash if override ends with /
      const base = apiOverride.endsWith('/') ? apiOverride.slice(0, -1) : apiOverride;
      url = base + url;
    }
    return originalFetch(url, init);
  };
}
// --------------------------

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);