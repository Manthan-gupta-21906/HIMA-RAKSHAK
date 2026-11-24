import { useState, type FormEvent } from "react";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useAuth } from "../context/AuthContext";
import { useTheme, type ThemeMode } from "../context/ThemeContext";
import {
  DEFAULT_PREFERENCES,
  type DefaultMapLayer,
  type OperatorPreferences,
  type RefreshIntervalMin,
  type UnitSystem,
} from "../types/preferences";
import { loadStoredPreferences, PREFS_STORAGE_KEY } from "../utils/preferences";

/** Operator profile and control-room preferences page. */
export function ProfilePage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [prefs, setPrefs] = useState<OperatorPreferences>(loadStoredPreferences);
  const [savedNotice, setSavedNotice] = useState(false);

  const handleSave = (event: FormEvent) => {
    event.preventDefault();
    localStorage.setItem(PREFS_STORAGE_KEY, JSON.stringify(prefs));
    setSavedNotice(true);
  };

  const handleReset = () => {
    localStorage.removeItem(PREFS_STORAGE_KEY);
    setPrefs(DEFAULT_PREFERENCES);
    setSavedNotice(false);
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
            Operator Account &amp; Console Preferences
          </span>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight mt-0.5">
            Profile &amp; Settings
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-0.5">
            Manage control-room session details, measurement units, and alert thresholds.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        <section
          aria-label="Account information"
          className="lg:col-span-5 bg-surface-card border border-border-hairline rounded-xl p-5 sm:p-6 flex flex-col gap-4 shadow-xs"
        >
          <div className="flex items-center gap-4 pb-4 border-b border-border-hairline">
            <div className="w-12 h-12 rounded-full bg-primary-container text-on-primary flex items-center justify-center font-bold text-base">
              {user?.initials ?? "OP"}
            </div>
            <div>
              <h2 className="text-base font-bold text-text-primary">{user?.name ?? "Operator"}</h2>
              <p className="text-xs text-text-muted">{user?.email}</p>
            </div>
          </div>

          <div className="flex flex-col gap-2.5 text-xs">
            <div className="flex justify-between gap-2">
              <span className="text-text-muted">Assigned Role</span>
              <Badge tone="neutral">{user?.role ?? "operator"}</Badge>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-text-muted">Control Station</span>
              <span className="font-semibold text-text-primary">{user?.station}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-text-muted">District / Sector</span>
              <span className="font-semibold text-text-primary">{user?.district}</span>
            </div>
          </div>

          <div className="pt-3 border-t border-border-hairline">
            <Button type="button" variant="secondary" onClick={logout} className="w-full">
              <span className="material-symbols-outlined text-[16px]">logout</span>
              <span>Sign Out of Session</span>
            </Button>
          </div>
        </section>

        <section
          aria-label="Application preferences"
          className="lg:col-span-7 bg-surface-card border border-border-hairline rounded-xl p-5 sm:p-6 shadow-xs"
        >
          <form onSubmit={handleSave} className="flex flex-col gap-5">
            <div className="pb-3 border-b border-border-hairline">
              <h2 className="text-base font-bold text-text-primary">Application Preferences</h2>
              <p className="text-xs text-text-muted mt-0.5">
                Stored locally for your control-room workstation.
              </p>
            </div>

            {savedNotice ? (
              <div
                role="status"
                className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs font-semibold text-[#054024] dark:text-emerald-200 flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                <span>Preferences saved for this workstation.</span>
              </div>
            ) : null}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="pref-units" className="text-xs font-semibold text-text-primary">
                  Measurement Units
                </label>
                <select
                  id="pref-units"
                  value={prefs.unitSystem}
                  onChange={(e) => {
                    setSavedNotice(false);
                    setPrefs((p) => ({ ...p, unitSystem: e.target.value as UnitSystem }));
                  }}
                  className="h-10 px-3 rounded-lg bg-surface-container-lowest border border-border-hairline text-xs font-medium text-text-primary"
                >
                  <option value="metric">Metric (mm, cm, m)</option>
                  <option value="imperial">Imperial (in, ft)</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="pref-map-layer" className="text-xs font-semibold text-text-primary">
                  Default Map Layer
                </label>
                <select
                  id="pref-map-layer"
                  value={prefs.defaultMapLayer}
                  onChange={(e) => {
                    setSavedNotice(false);
                    setPrefs((p) => ({
                      ...p,
                      defaultMapLayer: e.target.value as DefaultMapLayer,
                    }));
                  }}
                  className="h-10 px-3 rounded-lg bg-surface-container-lowest border border-border-hairline text-xs font-medium text-text-primary"
                >
                  <option value="standard">Standard Street</option>
                  <option value="terrain">Alpine Terrain</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="pref-theme" className="text-xs font-semibold text-text-primary">
                  Display Theme
                </label>
                <select
                  id="pref-theme"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value as ThemeMode)}
                  className="h-10 px-3 rounded-lg bg-surface-container-lowest border border-border-hairline text-xs font-medium text-text-primary"
                >
                  <option value="light">Light (Alpine Canvas)</option>
                  <option value="dark">Dark (Control Room)</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="pref-refresh" className="text-xs font-semibold text-text-primary">
                  Telemetry Auto-Refresh Interval
                </label>
                <select
                  id="pref-refresh"
                  value={prefs.autoRefreshIntervalMin}
                  onChange={(e) => {
                    setSavedNotice(false);
                    setPrefs((p) => ({
                      ...p,
                      autoRefreshIntervalMin: Number(e.target.value) as RefreshIntervalMin,
                    }));
                  }}
                  className="h-10 px-3 rounded-lg bg-surface-container-lowest border border-border-hairline text-xs font-medium text-text-primary"
                >
                  <option value={5}>Every 5 minutes</option>
                  <option value={15}>Every 15 minutes</option>
                  <option value={30}>Every 30 minutes</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-3 pt-2 border-t border-border-hairline">
              <label className="flex items-center justify-between gap-3 cursor-pointer">
                <div>
                  <p className="text-xs font-semibold text-text-primary">
                    Highlight Stale Telemetry (&gt;60m)
                  </p>
                  <p className="text-[11px] text-text-muted">
                    Display amber stale badges on sectors with delayed or offline sensors.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={prefs.staleDataAlerts}
                  onChange={(e) => {
                    setSavedNotice(false);
                    setPrefs((p) => ({ ...p, staleDataAlerts: e.target.checked }));
                  }}
                  className="w-4 h-4 accent-[#1d1b16]"
                />
              </label>

              <label className="flex items-center justify-between gap-3 cursor-pointer">
                <div>
                  <p className="text-xs font-semibold text-text-primary">
                    High-Risk Sector Alert Banner
                  </p>
                  <p className="text-[11px] text-text-muted">
                    Show priority banner when any J&amp;K sector enters High Risk or Stage 3.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={prefs.highRiskPushAlerts}
                  onChange={(e) => {
                    setSavedNotice(false);
                    setPrefs((p) => ({ ...p, highRiskPushAlerts: e.target.checked }));
                  }}
                  className="w-4 h-4 accent-[#1d1b16]"
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" onClick={handleReset}>
                Reset Defaults
              </Button>
              <Button type="submit">Save Preferences</Button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}
