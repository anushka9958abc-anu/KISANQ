import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("kisanq_user");
    return raw ? JSON.parse(raw) : null;
  });

  useEffect(() => {
    const t = localStorage.getItem("kisanq_token");
    if (!t) return;
    api("/api/auth/me")
      .then((me) => {
        const next = { ...user, ...me };
        setUser(next);
        localStorage.setItem("kisanq_user", JSON.stringify(next));
      })
      .catch(() => {
        localStorage.removeItem("kisanq_token");
        localStorage.removeItem("kisanq_user");
        setUser(null);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loginSuccess(data) {
    localStorage.setItem("kisanq_token", data.access_token);
    const u = { id: data.user_id, name: data.name, role: data.role };
    localStorage.setItem("kisanq_user", JSON.stringify(u));
    setUser(u);
  }

  function logout() {
    localStorage.removeItem("kisanq_token");
    localStorage.removeItem("kisanq_user");
    setUser(null);
  }

  return <AuthCtx.Provider value={{ user, loginSuccess, logout }}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  return useContext(AuthCtx);
}
