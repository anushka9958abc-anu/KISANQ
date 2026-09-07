import { useEffect, useState } from "react";
import { api } from "../api";

const LABELS = {
  registered: "Registered",
  slot_assigned: "Slot assigned",
  arrived: "Arrived",
  weighing: "Weighing",
  quality_check: "Quality check",
  procurement_completed: "Completed",
  payment_initiated: "Payment",
  paid: "Paid",
};

export default function AdminHome() {
  const [data, setData] = useState(null);
  const [centres, setCentres] = useState([]);
  const [centreId, setCentreId] = useState("");
  const [error, setError] = useState("");

  async function load(id = centreId) {
    const q = id ? `&centre_id=${id}` : "";
    setData(await api(`/api/admin/dashboard?${q}`));
  }

  useEffect(() => {
    api("/api/centres").then((d) => setCentres(d.centres));
    load("").catch((e) => setError(e.message));
  }, []);

  async function advance(id) {
    await api(`/api/admin/procurements/${id}/advance`, { method: "POST", body: JSON.stringify({ note: "Officer desk" }) });
    await load(centreId);
  }

  if (error) return <p className="text-rose-700">{error}</p>;
  if (!data) return <p>Loading desk…</p>;

  const cards = [
    ["Today's farmers", data.todays_farmers],
    ["Queue length", data.queue_length],
    ["Centre capacity (qtl)", data.centre_capacity_quintals],
    ["Pending", data.pending_procurements],
    ["Avg processing (min)", data.average_processing_time],
    ["Completed", data.completed_procurements],
  ];

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-forest">Officer dashboard</h1>
          <p className="text-moss">{data.date} · utilization {data.utilization}%</p>
        </div>
        <select
          className="rounded-lg border border-straw px-3 py-2"
          value={centreId}
          onChange={async (e) => {
            setCentreId(e.target.value);
            await load(e.target.value);
          }}
        >
          <option value="">All centres</option>
          {centres.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([k, v]) => (
          <div key={k} className="rounded-2xl border border-straw bg-white/80 p-5">
            <div className="text-sm text-moss">{k}</div>
            <div className="mt-1 font-display text-3xl text-forest">{v}</div>
          </div>
        ))}
      </div>
      <div className="mt-8 overflow-x-auto rounded-2xl border border-straw bg-white/80">
        <table className="w-full text-left text-sm">
          <thead className="bg-forest text-cream">
            <tr>
              <th className="px-3 py-2">Token</th>
              <th className="px-3 py-2">Farmer</th>
              <th className="px-3 py-2">Centre</th>
              <th className="px-3 py-2">Crop / qty</th>
              <th className="px-3 py-2">Slot</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {data.farmers.map((p) => (
              <tr key={p.id} className="border-t border-straw">
                <td className="px-3 py-2 font-semibold">#{p.token_number}</td>
                <td className="px-3 py-2">{p.farmer_name}</td>
                <td className="px-3 py-2">{p.centre.name}</td>
                <td className="px-3 py-2">
                  {p.crop.name} · {p.quantity_quintals} qtl
                </td>
                <td className="px-3 py-2">{p.slot ? p.slot.start_time : "—"}</td>
                <td className="px-3 py-2">{LABELS[p.status]}</td>
                <td className="px-3 py-2">
                  {p.status !== "paid" && (
                    <button className="rounded-full bg-gold px-3 py-1 text-xs font-semibold text-forest" onClick={() => advance(p.id)}>
                      Advance
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
