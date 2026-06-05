const API_URL = import.meta.env.VITE_API_URL || "https://venturemindai-3q51.onrender.com";

export function getToken() {
  return localStorage.getItem("venturemind_token");
}

export function setSession(session) {
  localStorage.setItem("venturemind_token", session.access_token);
  localStorage.setItem("venturemind_user", JSON.stringify(session.user));
}

export function clearSession() {
  localStorage.removeItem("venturemind_token");
  localStorage.removeItem("venturemind_user");
}

export function getStoredUser() {
  const raw = localStorage.getItem("venturemind_user");
  return raw ? JSON.parse(raw) : null;
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch (error) {
    throw new Error(`Cannot reach VentureMind API at ${API_URL}. Check backend health and CORS settings.`);
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(data.detail || "Request failed");
  }
  if (options.raw) return response;
  return response.json();
}

export const api = {
  login: (payload) => request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  register: (payload) => request("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/api/auth/me"),
  createAnalysis: (payload) => request("/api/analysis", { method: "POST", body: JSON.stringify(payload) }),
  reports: () => request("/api/analysis/reports"),
  report: (id) => request(`/api/analysis/reports/${id}`),
  userDashboard: () => request("/api/dashboard/user"),
  adminDashboard: () => request("/api/dashboard/admin"),
  evaluation: () => request("/api/dashboard/evaluation"),
  security: () => request("/api/dashboard/security"),
  users: () => request("/api/admin/users"),
  agentLogs: () => request("/api/admin/agent-logs"),
  auditLogs: () => request("/api/admin/audit-logs"),
  search: (payload) => request("/api/rag/search", { method: "POST", body: JSON.stringify(payload) }),
  upload: (formData) => request("/api/rag/upload", { method: "POST", body: formData }),
  ingestUrl: (payload) => request("/api/rag/ingest-url", { method: "POST", body: JSON.stringify(payload) }),
  feedback: (id, payload) => request(`/api/reports/${id}/feedback`, { method: "POST", body: JSON.stringify(payload) }),
  downloadUrl: (id, type) => `${API_URL}/api/reports/${id}/download.${type}?token=${getToken() || ""}`
};
