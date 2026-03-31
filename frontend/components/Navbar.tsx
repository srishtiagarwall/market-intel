import Link from "next/link";
import { TrendingUp } from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/signals", label: "MF Signals" },
  { href: "/stocks", label: "Stocks" },
  { href: "/portfolio", label: "Portfolio" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-700 bg-slate-900/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-bold text-sky-400">
          <TrendingUp size={18} />
          Market Intel
        </Link>
        <div className="flex gap-4">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="text-sm text-slate-400 transition hover:text-slate-100"
            >
              {n.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
