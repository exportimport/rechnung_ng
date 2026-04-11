import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import logo from "../assets/logo.svg";
import { settingsApi } from "../api/settings";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/customers", label: "Kunden" },
  { to: "/plans", label: "Tarife" },
  { to: "/contracts", label: "Verträge" },
  { to: "/invoices", label: "Rechnungen" },
  { to: "/mail-templates", label: "Mail-Vorlagen" },
  { to: "/settings", label: "Einstellungen" },
];

export default function Layout() {
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: settingsApi.get });

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-violet-200 via-indigo-100 to-blue-200">
      <aside className="relative w-64 shrink-0 bg-white/30 backdrop-blur-xl flex flex-col">
        <div className="px-4 py-5 space-y-2">
          <img src={logo} alt="rechnung_ng" className="h-16 w-auto" />
          {settings?.company.name && (
            <p className="text-xs font-medium text-violet-700/80 text-center truncate px-1">
              {settings.company.name}
            </p>
          )}
        </div>
        <nav className="flex-1 px-3 py-2 space-y-1">
          {navItems.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "block px-4 py-2.5 rounded-full text-sm font-medium transition-all",
                  isActive
                    ? "bg-white/70 text-violet-700 shadow-sm"
                    : "text-violet-900/70 hover:bg-white/40 hover:text-violet-800",
                ].join(" ")
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Wavy right edge — replaces the straight border */}
        <svg
          className="absolute top-0 right-0 h-full translate-x-full pointer-events-none"
          width="28"
          viewBox="0 0 28 1000"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M0,0 C18,150 -8,300 14,500 C28,650 4,800 0,1000 L0,0 Z"
            fill="rgba(255,255,255,0.30)"
          />
        </svg>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
