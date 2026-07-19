/**
 * API Client — fetch wrapper for all backend calls.
 * 
 * Base URL points to the FastAPI backend (default: http://localhost:8000).
 * Automatically attaches JWT token from localStorage if present.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Generic fetch wrapper with auth header injection.
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = { ...options.headers };

  // Attach JWT token if available
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const res = await fetch(url, { ...options, headers });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────────

export async function login(username, password) {
  const data = await apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (typeof window !== "undefined") {
    localStorage.setItem("token", data.access_token);
  }
  return data;
}

export async function logout() {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } catch {
    // ignore errors on logout
  }
  if (typeof window !== "undefined") {
    localStorage.removeItem("token");
  }
}

export function getToken() {
  if (typeof window !== "undefined") {
    return localStorage.getItem("token");
  }
  return null;
}

// ── Dashboard ────────────────────────────────────────────────────────

export async function fetchDashboardSummary() {
  return apiFetch("/dashboard/summary");
}

// ── Videos ───────────────────────────────────────────────────────────

export async function uploadVideo(file) {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE}/videos/upload`;
  const headers = {};
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { method: "POST", headers, body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchVideoStatus(videoId) {
  return apiFetch(`/videos/${videoId}/status`);
}

// ── Parcels ──────────────────────────────────────────────────────────

export async function fetchParcels({ condition, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (condition) params.set("condition", condition);
  params.set("limit", limit);
  params.set("offset", offset);
  return apiFetch(`/parcels?${params.toString()}`);
}

export async function fetchParcelDetail(id) {
  return apiFetch(`/parcels/${id}`);
}

// ── Crop image URL helper ────────────────────────────────────────────

export function getCropImageUrl(imagePath) {
  if (!imagePath) return null;
  return `${API_BASE}/crops/${imagePath}`;
}

export function getVideoStreamUrl(videoId) {
  if (!videoId) return null;
  return `${API_BASE}/videos/${videoId}/stream`;
}
