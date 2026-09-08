const API = import.meta.env.VITE_API_BASE_URL || "https://kisanq.onrender.com";

export function token() {
  return localStorage.getItem("kisanq_token");
}

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  
  const res = await fetch(`${API}${path}`, { ...options, headers });
  
  if (!res.ok) {
    let detail = "Request failed";
    try {
      const text = await res.text();
      try {
        const body = JSON.parse(text);
        detail = body.detail || JSON.stringify(body);
      } catch {
        detail = text || "Request failed";
      }
    } catch {
      detail = "Request failed";
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }
  
  return res.json();
}
