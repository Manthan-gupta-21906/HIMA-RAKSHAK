import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";

interface TopHeaderProps {
  onToggleMobileNav: () => void;
  isMobileNavOpen: boolean;
}

/** Fixed operational top bar displaying brand, active control station, and user session link. */
export function TopHeader({ onToggleMobileNav, isMobileNavOpen }: TopHeaderProps) {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

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

        <img
          src="/hima-rakshak-logo.png"
          alt="HIMA-RAKSHAK Logo"
          className="h-12 w-auto rounded-lg object-contain shrink-0"
        />
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
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          className="w-9 h-9 rounded-full border border-border-hairline bg-surface-container-low hover:bg-surface-container flex items-center justify-center text-text-primary transition-colors cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">
            {theme === "dark" ? "light_mode" : "dark_mode"}
          </span>
        </button>

        {user ? (
          <>
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-text-primary leading-tight">
                {user.station}
              </span>
              <span className="text-[11px] text-text-muted leading-tight">{user.district}</span>
            </div>
            <Link
              to="/profile"
              aria-label="Open profile and settings"
              className="w-9 h-9 rounded-full bg-surface-container border border-border-hairline hover:border-primary-container flex items-center justify-center font-bold text-xs text-text-primary transition-colors"
              title={`${user.name} (${user.role}) — Profile & Settings`}
            >
              {user.initials}
            </Link>
          </>
        ) : null}
      </div>
    </header>
  );
}
