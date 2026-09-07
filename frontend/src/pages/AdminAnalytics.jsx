import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";

export default function AdminAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api("/api/admin/analytics").then(setData);
  }, []);

  if (!data) return <p>Loading analytics…</p>;

  return (
    <div>
      <h1 className="font-display text-3xl text-forest">Analytics & prediction</h1>
      <p className="mt-1 text-moss">
        Busiest day: {data.busiest_day}. Expected arrivals today: {data.expected_arrivals_today}. Expected volume:{" "}
        {data.expected_volume_today} qtl.
      </p>
      <div className="mt-8 h-80 rounded-2xl border border-straw bg-white/80 p-4">
        <h2 className="font-display text-lg text-forest">Expected farmer arrivals by weekday</h2>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={data.by_weekday}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="weekday" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="expected_farmers" name="Farmers" fill="#143528" />
            <Bar dataKey="avg_wait_minutes" name="Avg wait (min)" fill="#c5922a" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-8 overflow-x-auto rounded-2xl border border-straw bg-white/80">
        <table className="w-full text-left text-sm">
          <thead className="bg-forest text-cream">
            <tr>
              <th className="px-3 py-2">Centre</th>
              <th className="px-3 py-2">Booked today</th>
              <th className="px-3 py-2">Capacity</th>
              <th className="px-3 py-2">Utilization</th>
            </tr>
          </thead>
          <tbody>
            {data.centre_utilization.map((c) => (
              <tr key={c.code} className="border-t border-straw">
                <td className="px-3 py-2">{c.centre}</td>
                <td className="px-3 py-2">{c.booked}</td>
                <td className="px-3 py-2">{c.capacity}</td>
                <td className="px-3 py-2">{c.utilization}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
