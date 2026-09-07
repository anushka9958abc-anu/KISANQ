import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "./auth";

export function CrowdBadge({ crowd }) {
  const map = {
    low: { label: "Low crowd", cls: "bg-emerald-100 text-emerald-800 border-emerald-300" },
    moderate: { label: "Moderate", cls: "bg-amber-100 text-amber-900 border-amber-300" },
    high: { label: "High crowd", cls: "bg-rose-100 text-rose-800 border-rose-300" },
  };
  const m = map[crowd] || map.moderate;
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${m.cls}`}>{m.label}</span>;
}

export function Logo({ light = false }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`grid h-9 w-9 place-items-center rounded-md font-display text-lg font-bold ${light ? "bg-gold text-forest" : "bg-forest text-cream"}`}>
        KQ
      </span>
      <div>
        <div className={`font-display text-xl leading-none ${light ? "text-cream" : "text-forest"}`}>KISANQ</div>
        <div className={`text-[10px] uppercase tracking-[0.18em] ${light ? "text-straw" : "text-moss"}`}>Procurement status</div>
      </div>
    </div>
  );
}

export function Shell({ children, admin = false }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const farmerLinks = [
    ["/app/book", "Book slot"],
    ["/app/queue", "Live queue"],
    ["/app/status", "Procurement status"],
    ["/app/map", "Centres map"],
  ];
  const adminLinks = [
    ["/admin", "Today"],
    ["/admin/analytics", "Analytics"],
  ];
  const links = admin ? adminLinks : farmerLinks;

  return (
    <div className="min-h-screen">
      <header className="field-band text-cream">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <button onClick={() => navigate("/")}>
            <Logo light />
          </button>
          <nav className="hidden gap-1 md:flex">
            {links.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/admin"}
                className={({ isActive }) =>
                  `rounded-full px-3 py-1.5 text-sm ${isActive ? "bg-cream/15 text-white" : "text-straw hover:bg-cream/10"}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden sm:block text-straw">{user?.name}</span>
            <button
              className="rounded-full bg-gold px-3 py-1.5 text-forest font-semibold"
              onClick={() => {
                logout();
                navigate("/");
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children || <Outlet />}</main>
    </div>
  );
}
