import { useEffect, useState } from "react";
import { api } from "../api";

export default function QueuePage() {
  const [list, setList] = useState([]);
  const [active, setActive] = useState(localStorage.getItem("kisanq_active"));
  const [queue, setQueue] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/procurements/mine").then((rows) => {
      setList(rows);
      if (!active && rows[0]) setActive(String(rows[0].id));
    });
  }, []);

  useEffect(() => {
    if (!active) return;
    let timer;
    async function load() {
      try {
        setQueue(await api(`/api/queue/${active}`));
        setError("");
      } catch (e) {
        setError(e.message);
      }
    }
    load();
    timer = setInterval(load, 4000);
    return () => clearInterval(timer);
  }, [active]);

  return (
    <div className="grid gap-8 md:grid-cols-[280px_1fr]">
      <aside className="rounded-2xl border border-straw bg-white/80 p-4">
        <h2 className="font-display text-xl text-forest">Your tokens</h2>
        <div className="mt-3 space-y-2">
          {list.map((p) => (
            <button
              key={p.id}
              onClick={() => {
                setActive(String(p.id));
                localStorage.setItem("kisanq_active", String(p.id));
              }}
              className={`w-full rounded-xl px-3 py-2 text-left text-sm ${String(p.id) === String(active) ? "bg-forest text-cream" : "bg-straw/40"}`}
            >
              #{p.token_number} · {p.centre.name}
            </button>
          ))}
        </div>
      </aside>
      <section className="rounded-2xl border border-straw bg-white/80 p-8">
        <h1 className="font-display text-3xl text-forest">Live queue tracking</h1>
        {error && <p className="mt-3 text-rose-700">{error}</p>}
        {queue && (
          <>
            <p className="mt-6 font-display text-5xl text-forest">You are #{queue.token_number}</p>
            <p className="mt-2 text-2xl text-gold">approx. {queue.estimated_wait_minutes} min remaining</p>
            <p className="mt-4 max-w-xl text-lg">{queue.message}</p>
            <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Stat label="Now serving" value={`#${queue.current_token}`} />
              <Stat label="Your position" value={queue.position} />
              <Stat label="Farmers ahead" value={queue.farmers_ahead} />
              <Stat label="Slot" value={queue.slot.start_time} />
            </div>
            <p className="mt-6 text-sm text-moss">{queue.centre} · {queue.slot.date}</p>
          </>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl bg-straw/40 p-4">
      <div className="text-xs uppercase tracking-wide text-moss">{label}</div>
      <div className="mt-1 font-display text-2xl text-forest">{value}</div>
    </div>
  );
}
