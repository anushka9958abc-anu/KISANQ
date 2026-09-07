import { useEffect, useState } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import { api } from "../api";
import { CrowdBadge } from "../ui";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export default function MapPage() {
  const [centres, setCentres] = useState([]);

  useEffect(() => {
    api("/api/centres?lat=29.71&lng=77.01").then((d) => setCentres(d.centres));
  }, []);

  const best = [...centres].sort((a, b) => a.estimated_wait_minutes - b.estimated_wait_minutes)[0];

  return (
    <div>
      <h1 className="font-display text-3xl text-forest">Map / GIS dashboard</h1>
      <p className="mt-1 text-moss">Distance, queue, capacity and open slots for nearby centres.</p>
      {best && (
        <p className="mt-4 rounded-xl bg-leaf/10 px-4 py-3 text-leaf">
          Recommendation: {best.name} is {best.distance_km} km away with about {best.estimated_wait_minutes} minutes wait.
        </p>
      )}
      <div className="mt-6 h-[420px] overflow-hidden rounded-2xl border border-straw">
        {centres.length > 0 && (
          <MapContainer center={[29.7, 76.95]} zoom={8} style={{ height: "100%", width: "100%" }}>
            <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {centres.map((c) => (
              <Marker key={c.id} position={[c.lat, c.lng]}>
                <Popup>
                  <strong>{c.name}</strong>
                  <br />
                  {c.distance_km} km · wait {c.estimated_wait_minutes} min
                  <br />
                  {c.available_slots} slots · crowd {c.crowd}
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        )}
      </div>
      <div className="mt-6 overflow-x-auto rounded-2xl border border-straw bg-white/80">
        <table className="w-full text-left text-sm">
          <thead className="bg-forest text-cream">
            <tr>
              <th className="px-3 py-2">Centre</th>
              <th className="px-3 py-2">Distance</th>
              <th className="px-3 py-2">Queue</th>
              <th className="px-3 py-2">Capacity</th>
              <th className="px-3 py-2">Open slots</th>
              <th className="px-3 py-2">Wait</th>
              <th className="px-3 py-2">Crowd</th>
            </tr>
          </thead>
          <tbody>
            {centres.map((c) => (
              <tr key={c.id} className="border-t border-straw">
                <td className="px-3 py-2 font-semibold">{c.name}</td>
                <td className="px-3 py-2">{c.distance_km} km</td>
                <td className="px-3 py-2">{c.queue_length}</td>
                <td className="px-3 py-2">{c.capacity_farmers} farmers / {c.daily_capacity_quintals} qtl</td>
                <td className="px-3 py-2">{c.available_slots}</td>
                <td className="px-3 py-2">{c.estimated_wait_minutes} min</td>
                <td className="px-3 py-2">
                  <CrowdBadge crowd={c.crowd} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
