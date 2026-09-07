import { useEffect, useState } from "react";
import { api } from "../api";

const LABELS = {
  registered: "Registered",
  slot_assigned: "Slot assigned",
  arrived: "Arrived",
  weighing: "Weighing",
  quality_check: "Quality check",
  procurement_completed: "Procurement completed",
  payment_initiated: "Payment initiated",
  paid: "Paid",
};

export default function StatusPage() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api("/api/procurements/mine").then(setRows);
  }, []);

  return (
    <div>
      <h1 className="font-display text-3xl text-forest">Real-time procurement status</h1>
      <p className="mt-1 text-moss">Registered through paid, including QR gate check-in.</p>
      <div className="mt-8 space-y-6">
        {rows.map((p) => {
          const idx = p.status_flow.indexOf(p.status);
          return (
            <article key={p.id} className="rounded-2xl border border-straw bg-white/80 p-6">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="font-display text-2xl text-forest">
                  Token #{p.token_number} · {p.crop.name}
                </h2>
                <span className="text-sm text-moss">QR {p.qr_code}</span>
              </div>
              <p className="mt-1 text-sm">
                {p.centre.name} · {p.quantity_quintals} qtl · {p.slot ? `${p.slot.date} ${p.slot.start_time}` : "No slot"}
              </p>
              <ol className="mt-5 grid gap-2 md:grid-cols-4">
                {p.status_flow.map((s, i) => (
                  <li
                    key={s}
                    className={`rounded-lg px-3 py-2 text-sm ${i <= idx ? "bg-forest text-cream" : "bg-straw/40 text-moss"}`}
                  >
                    {i + 1}. {LABELS[s]}
                  </li>
                ))}
              </ol>
            </article>
          );
        })}
        {rows.length === 0 && <p>No procurements yet. Book a slot first.</p>}
      </div>
    </div>
  );
}
