import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { CrowdBadge } from "../ui";

export default function BookSlot() {
  const navigate = useNavigate();
  const [crops, setCrops] = useState([]);
  const [centres, setCentres] = useState([]);
  const [estimate, setEstimate] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    crop_id: "",
    quantity_quintals: 25,
    preferred_centre_id: "",
    preferred_date: new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    api("/api/crops").then(setCrops);
    api("/api/centres?lat=29.71&lng=77.01").then((d) => setCentres(d.centres));
  }, []);

  useEffect(() => {
    if (!form.crop_id || !form.quantity_quintals) return;
    api("/api/estimate-time", {
      method: "POST",
      body: JSON.stringify({ crop_id: Number(form.crop_id), quantity_quintals: Number(form.quantity_quintals) }),
    })
      .then(setEstimate)
      .catch(() => setEstimate(null));
  }, [form.crop_id, form.quantity_quintals]);

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await api("/api/slots/book", {
        method: "POST",
        body: JSON.stringify({
          crop_id: Number(form.crop_id),
          quantity_quintals: Number(form.quantity_quintals),
          preferred_centre_id: Number(form.preferred_centre_id),
          preferred_date: form.preferred_date,
          lat: 29.71,
          lng: 77.01,
        }),
      });
      localStorage.setItem("kisanq_active", String(data.procurement.id));
      setResult(data);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="rounded-2xl border border-straw bg-white/80 p-6">
        <h1 className="font-display text-3xl text-forest">Smart slot allocation</h1>
        <p className="mt-1 text-moss">Quantity drives processing time. We spread arrivals across bays.</p>
        <form onSubmit={submit} className="mt-6 grid gap-4">
          <label className="text-sm">
            Crop
            <select className="mt-1 w-full rounded-lg border border-straw px-3 py-2" value={form.crop_id} onChange={(e) => setForm({ ...form, crop_id: e.target.value })} required>
              <option value="">Select crop</option>
              {crops.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.name_hi})
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Expected quantity (quintals)
            <input type="number" min="1" step="0.5" className="mt-1 w-full rounded-lg border border-straw px-3 py-2" value={form.quantity_quintals} onChange={(e) => setForm({ ...form, quantity_quintals: e.target.value })} />
          </label>
          <label className="text-sm">
            Preferred centre
            <select className="mt-1 w-full rounded-lg border border-straw px-3 py-2" value={form.preferred_centre_id} onChange={(e) => setForm({ ...form, preferred_centre_id: e.target.value })} required>
              <option value="">Select centre</option>
              {centres.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} · {c.distance_km} km · wait {c.estimated_wait_minutes} min
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Date
            <input type="date" className="mt-1 w-full rounded-lg border border-straw px-3 py-2" value={form.preferred_date} onChange={(e) => setForm({ ...form, preferred_date: e.target.value })} />
          </label>
          {estimate && (
            <div className="rounded-xl bg-straw/50 px-4 py-3 text-sm">
              Estimated processing time: <strong>{estimate.estimated_minutes} minutes</strong>. {estimate.message}
            </div>
          )}
          {error && <p className="text-rose-700 text-sm">{error}</p>}
          <button className="rounded-full bg-forest py-3 font-semibold text-cream">Assign best slot</button>
        </form>
        {result && (
          <div className="mt-6 rounded-xl border border-leaf/30 bg-leaf/5 p-4">
            <p className="font-display text-2xl text-forest">
              Token #{result.procurement.token_number} · {result.procurement.slot.start_time}
            </p>
            <p className="mt-1">{result.procurement.centre.name}</p>
            {result.recommendation && <p className="mt-2 text-sm text-leaf">{result.recommendation}</p>}
            <p className="mt-2 text-sm text-moss">SMS/WhatsApp: your procurement slot is tomorrow/today at the assigned time.</p>
            <button className="mt-4 rounded-full bg-gold px-4 py-2 font-semibold text-forest" onClick={() => navigate("/app/queue")}>
              Open live queue
            </button>
          </div>
        )}
      </section>
      <aside>
        <h2 className="font-display text-2xl text-forest">Crowd forecast</h2>
        <div className="mt-4 space-y-3">
          {centres.map((c) => (
            <article key={c.id} className="rounded-xl border border-straw bg-white/80 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-forest">{c.name}</h3>
                  <p className="text-sm text-moss">
                    {c.distance_km} km · {c.available_slots} slots open
                  </p>
                </div>
                <CrowdBadge crowd={c.crowd} />
              </div>
              <p className="mt-2 text-sm">Wait ~ {c.estimated_wait_minutes} min · {c.booked_farmers}/{c.capacity_farmers} farmers</p>
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}
