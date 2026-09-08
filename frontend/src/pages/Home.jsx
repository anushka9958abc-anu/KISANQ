import { Link } from "react-router-dom";
import { Logo } from "../components/Logo";

const features = [
  {
    title: "Smart slot allocation",
    body: "Enter crop quantity and a preferred centre. KISANQ assigns the best available time so mandis do not overflow.",
  },
  {
    title: "Live queue tracking",
    body: "See your token, farmers ahead, and remaining wait — for example, you are #18 with about 42 minutes left.",
  },
  {
    title: "Crowd prediction",
    body: "Centres are marked low, moderate, or high crowd, with a recommendation for a quieter yard.",
  },
  {
    title: "Map & GIS",
    body: "Nearby procurement centres with distance, capacity, open slots and estimated waiting time.",
  },
];

export default function Home() {
  return (
    <div>
      <header className="field-band text-cream">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <Logo light /> 
          <div className="flex gap-2">
            <Link to="/login" className="rounded-full border border-cream/30 px-4 py-2 text-sm">
              Sign in
            </Link>
            <Link to="/login?role=admin" className="rounded-full bg-gold px-4 py-2 text-sm font-semibold text-forest">
              Officer desk
            </Link>
          </div>
        </div>
        <div className="mx-auto grid max-w-6xl gap-10 px-4 pb-16 pt-8 md:grid-cols-2 md:items-end">
          <div>
            <p className="text-gold text-sm tracking-[0.2em] uppercase">Haryana procurement network</p>
            <h1 className="mt-3 font-display text-5xl leading-tight md:text-6xl">
              Reach the mandi when the bay is actually free.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-straw">
              KISANQ books your slot, watches the live queue, and steers you toward a less crowded centre — with SMS,
              WhatsApp and IVR when the network drops.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/login" className="rounded-full bg-cream px-5 py-3 font-semibold text-forest">
                Book a farmer slot
              </Link>
              <Link to="/login?role=admin" className="rounded-full border border-cream/40 px-5 py-3">
                Open admin dashboard
              </Link>
            </div>
          </div>
          <div className="rounded-2xl border border-cream/15 bg-forest/40 p-6 backdrop-blur">
            <p className="text-sm text-straw">Sample queue board</p>
            <p className="mt-3 font-display text-4xl">You are #18</p>
            <p className="mt-1 text-gold">approx. 42 min remaining</p>
            <div className="mt-6 grid grid-cols-3 gap-3 text-center text-sm">
              <div className="rounded-xl bg-cream/10 p-3">
                <div className="text-2xl font-display">5</div>
                <div className="text-straw">ahead</div>
              </div>
              <div className="rounded-xl bg-cream/10 p-3">
                <div className="text-2xl font-display">#12</div>
                <div className="text-straw">now serving</div>
              </div>
              <div className="rounded-xl bg-cream/10 p-3">
                <div className="text-2xl font-display">11:30</div>
                <div className="text-straw">your slot</div>
              </div>
            </div>
          </div>
        </div>
      </header>
      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="font-display text-3xl text-forest">What the platform does</h2>
        <div className="mt-8 grid gap-5 md:grid-cols-2">
          {features.map((f) => (
            <article key={f.title} className="rounded-2xl border border-straw bg-white/70 p-6">
              <h3 className="font-display text-xl text-forest">{f.title}</h3>
              <p className="mt-2 text-soil/80">{f.body}</p>
            </article>
          ))}
        </div>
        <p className="mt-10 text-sm text-moss">
          Demo farmer: 9876543210 / farmer123 · Admin: 9990001111 / admin123
        </p>
      </section>
    </div>
  );
}

