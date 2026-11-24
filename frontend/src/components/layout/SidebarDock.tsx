import { NavLink } from "react-router-dom";

export interface NavItem {
  to: string;
  label: string;
  icon: string;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Overview", icon: "grid_view" },
  { to: "/map", label: "Risk Map", icon: "explore" },
  { to: "/field-log", label: "Field Log", icon: "edit_note" },
  { to: "/warnings", label: "Warnings", icon: "fact_check" },
  { to: "/sources", label: "Sources", icon: "sensors" },
  { to: "/replay", label: "Replay", icon: "history" },
  { to: "/profile", label: "Profile", icon: "person" },
];

interface SidebarDockProps {
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

/** Fixed left navigation rail on desktop with responsive slide-over drawer on mobile. */
export function SidebarDock({ isMobileOpen, onCloseMobile }: SidebarDockProps) {
  return (
    <>
      <aside
        aria-label="Primary navigation"
        className="hidden md:flex fixed left-0 top-16 bottom-0 w-20 bg-surface-card border-r border-border-hairline z-40 flex-col justify-between py-4 items-center"
      >
        <nav className="flex flex-col items-center gap-1.5 w-full px-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center w-full py-2 px-1 rounded-xl transition-all text-center gap-0.5 ${
                  isActive
                    ? "bg-primary-container text-on-primary font-semibold shadow-sm"
                    : "text-on-surface-variant hover:bg-surface-container-high hover:text-text-primary"
                }`
              }
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
              <span className="text-[10px] tracking-wide leading-tight">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="px-2 w-full">
          <div className="flex flex-col items-center justify-center py-2 px-1 rounded-xl bg-surface-container-low border border-border-hairline text-center">
            <span className="w-2 h-2 rounded-full bg-alert-green mb-1" />
            <span className="text-[9px] font-bold uppercase tracking-wider text-text-primary">
              ONLINE
            </span>
          </div>
        </div>
      </aside>

      {isMobileOpen ? (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-primary-container/40"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <nav
            aria-label="Mobile navigation"
            className="relative z-50 mt-16 w-64 bg-surface-card border-r border-border-hairline p-4 flex flex-col gap-1.5 shadow-lg"
          >
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary-container text-on-primary font-semibold"
                      : "text-on-surface-variant hover:bg-surface-container"
                  }`
                }
              >
                <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      ) : null}
    </>
  );
}
