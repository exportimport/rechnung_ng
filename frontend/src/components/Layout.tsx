import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/customers", label: "Kunden" },
  { to: "/plans", label: "Tarife" },
  { to: "/contracts", label: "Verträge" },
  { to: "/invoices", label: "Rechnungen" },
  { to: "/mail-templates", label: "Mail-Vorlagen" },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-violet-50">
      <aside className="w-56 shrink-0 bg-white border-r border-violet-100 flex flex-col">
        <div className="px-6 py-5 border-b border-violet-100">
          <span className="text-lg font-semibold text-violet-700">rechnung_ng</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "block px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-violet-100 text-violet-700"
                    : "text-gray-500 hover:bg-violet-50 hover:text-gray-900",
                ].join(" ")
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
