import { useAuth } from "../../context/AuthContext";

interface TopHeaderProps {
  onToggleMobileNav: () => void;
  isMobileNavOpen: boolean;
}

/** Fixed operational top bar displaying brand, active control station, and user session actions. */
export function TopHeader({ onToggleMobileNav, isMobileNavOpen }: TopHeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-surface-card/95 backdrop-blur-md border-b border-border-hairline px-4 md:px-6 flex items-center justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleMobileNav}
          aria-label={isMobileNavOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={isMobileNavOpen}
          className="md:hidden w-9 h-9 rounded-lg border border-border-hairline flex items-center justify-center text-text-primary hover:bg-surface-container cursor-pointer"
        >
          <span className="material-symbols-outlined text-[20px]">
            {isMobileNavOpen ? "close" : "menu"}
          </span>
        </button>

        <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center text-on-primary shadow-xs">
          <span className="material-symbols-outlined text-[18px]">ac_unit</span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-text-primary tracking-tight">HIMA-RAKSHAK</span>
            <span className="hidden lg:inline text-border-hairline">|</span>
            <span className="hidden lg:inline text-xs text-text-muted font-medium">
              Disaster Decision Support System
            </span>
          </div>
          <span className="text-[10px] text-text-muted uppercase tracking-[0.06em] font-semibold">
            Government of Jammu &amp; Kashmir
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {user ? (
          <>
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-text-primary leading-tight">
                {user.station}
              </span>
              <span className="text-[11px] text-text-muted leading-tight">{user.district}</span>
            </div>
            <div
              className="w-9 h-9 rounded-full bg-surface-container border border-border-hairline flex items-center justify-center font-bold text-xs text-text-primary"
              title={`${user.name} (${user.role})`}
            >
              {user.initials}
            </div>
            <button
              type="button"
              onClick={logout}
              aria-label="Sign out"
              title="Sign out"
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full border border-border-hairline bg-surface-container-low hover:bg-surface-container text-xs font-semibold text-text-primary transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[15px]">logout</span>
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </>
        ) : null}
      </div>
    </header>
  );
}
