import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { Logo } from "../ui";

export default function Login() {
  const { loginSuccess } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const officer = params.get("role") === "admin";
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    name: "",
    phone: officer ? "9990001111" : "9876543210",
    password: officer ? "admin123" : "farmer123",
    village: "Kunjpura",
    district: "Karnal",
  });
  const [error, setError] = useState("");

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const path = mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const body =
        mode === "register"
          ? { ...form, lat: 29.71, lng: 77.01 }
          : { phone: form.phone, password: form.password };
      const data = await api(path, { method: "POST", body: JSON.stringify(body) });
      loginSuccess(data);
      navigate(data.role === "farmer" ? "/app/book" : "/admin");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="min-h-screen field-band flex items-center justify-center px-4 py-12">
      <form onSubmit={submit} className="w-full max-w-md rounded-2xl bg-cream p-8 text-soil">
        <Logo />
        <h1 className="mt-6 font-display text-3xl text-forest">{officer ? "Officer sign in" : "Farmer sign in"}</h1>
        <p className="mt-1 text-sm text-moss">Same desk for SMS-linked phones and procurement officers.</p>
        {mode === "register" && (
          <label className="mt-4 block text-sm">
            Name
            <input className="mt-1 w-full rounded-lg border border-straw bg-white px-3 py-2" value={form.name} onChange={(e) => set("name", e.target.value)} required />
          </label>
        )}
        <label className="mt-4 block text-sm">
          Mobile
          <input className="mt-1 w-full rounded-lg border border-straw bg-white px-3 py-2" value={form.phone} onChange={(e) => set("phone", e.target.value)} required />
        </label>
        <label className="mt-4 block text-sm">
          Password
          <input type="password" className="mt-1 w-full rounded-lg border border-straw bg-white px-3 py-2" value={form.password} onChange={(e) => set("password", e.target.value)} required />
        </label>
        {error && <p className="mt-3 text-sm text-rose-700">{error}</p>}
        <button className="mt-6 w-full rounded-full bg-forest py-3 font-semibold text-cream">Continue</button>
        {!officer && (
          <button type="button" className="mt-3 w-full text-sm text-leaf" onClick={() => setMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? "New farmer? Register" : "Already registered? Sign in"}
          </button>
        )}
      </form>
    </div>
  );
}
