import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLocations } from "../api/locations";
import { mapLocationAndRiskToSector } from "../api/mappers";
import { fetchLocationRiskState } from "../api/risk";
import { Badge } from "../components/ui/Badge";
import { PageSkeleton } from "../components/ui/PageSkeleton";
import { MOCK_SECTORS, REGIONAL_KPIS, type MonitoringSector, type RegionalKpi } from "../data/mockSectors";

/** Regional Hazard Monitor overview connected to backend location & risk APIs. */
export function OverviewPage() {
  const [sectors, setSectors] = useState<MonitoringSector[]>(MOCK_SECTORS);
  const [kpis, setKpis] = useState<RegionalKpi[]>(REGIONAL_KPIS);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("Sample Data");

  const loadData = async (isManualRefresh = false) => {
    if (isManualRefresh) setIsRefreshing(true);
    setError(null);

    try {
      const locResponse = await fetchLocations();
      if (locResponse && Array.isArray(locResponse.items) && locResponse.items.length > 0) {
        // Fetch risk states for all locations
        const mappedSectors = await Promise.all(
          locResponse.items.map(async (loc) => {
            try {
              const riskState = await fetchLocationRiskState(loc.location_id);
              return mapLocationAndRiskToSector(loc, riskState);
            } catch {
              return mapLocationAndRiskToSector(loc, null);
            }
          })
        );

        setSectors(mappedSectors);
        setIsLive(true);
        setLastUpdated(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));

        // Compute real KPIs from backend data
        const alertCount = mappedSectors.filter(
          (s) => s.isPriority || s.riskTier === "High Risk" || s.riskTier === "Stage 3"
        ).length;
        const nominalCount = mappedSectors.filter((s) => !s.isStale).length;
        const delayedCount = mappedSectors.filter((s) => s.isStale).length;

        setKpis([
          {
            label: "Active Alerts",
            value: `${alertCount} Sectors`,
            subtitle: alertCount > 0 ? "Requires active attention" : "Nominal baseline",
          },
          {
            label: "Monitored Locations",
            value: `${mappedSectors.length} Active`,
            subtitle: `${nominalCount} nominal, ${delayedCount} delayed`,
          },
          {
            label: "River Basins",
            value: `${mappedSectors.filter((s) => s.hazard === "flood").length} Flood`,
            subtitle: "Jhelum & Chenab basins",
          },
          {
            label: "Alpine Ridges",
            value: `${mappedSectors.filter((s) => s.hazard === "avalanche").length} Avalanche`,
            subtitle: "Gulmarg & Pir Panjal",
          },
        ]);
      } else if (locResponse && Array.isArray(locResponse.items) && locResponse.items.length === 0) {
        setSectors([]);
        setIsLive(true);
      }
    } catch (err) {
      // In unit tests or when backend is unavailable, log and keep default fallback
      setError((err as Error).message || "Could not connect to backend service");
    } finally {
      if (!isManualRefresh) {
        setIsRefreshing(false);
      }
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData(true);
    window.setTimeout(() => setIsRefreshing(false), 350);
  };

  if (isRefreshing) {
    return <PageSkeleton />;
  }

  const prioritySectors = sectors.filter((s) => s.isPriority || s.riskTier === "High Risk" || s.riskTier === "Stage 3");
  const displaySectors = prioritySectors.length > 0 ? prioritySectors : sectors;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.08em]">
              Sector J&amp;K Overview
            </span>
            <span className="text-border-hairline">•</span>
            <span className="text-[10px] font-semibold text-secondary">
              {isLive ? `Live Backend Data • Updated ${lastUpdated}` : `Updated 2m ago (${lastUpdated})`}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">
            Regional Hazard Monitor
          </h1>
          <p className="text-xs sm:text-sm text-secondary">
            Monitoring across critical districts and river basins in Jammu &amp; Kashmir.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 dark:bg-amber-950/40 border border-border-hairline text-xs">
            <span className="material-symbols-outlined text-[16px] text-agency-dgre">warning</span>
            <span className="font-medium text-text-primary">
              {sectors.length > 0 ? `${sectors.filter((s) => !s.isStale).length}/${sectors.length} Stations Synced` : "0 Stations"}
            </span>
            <span className="text-border-hairline">•</span>
            <span className="font-semibold text-agency-dgre">
              {sectors.filter((s) => s.isStale).length} Delayed
            </span>
          </div>
          <button
            type="button"
            onClick={handleRefresh}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-surface-container hover:bg-surface-container-high text-text-primary text-xs font-semibold transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            <span>Refresh</span>
          </button>
          <Link
            to="/sources"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-surface-container hover:bg-surface-container-high text-text-primary text-xs font-semibold transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">sensors</span>
            <span>Sources</span>
          </Link>
        </div>
      </div>

      {error && !isLive && (
        <div
          role="alert"
          className="p-3.5 rounded-xl bg-surface-card border border-border-hairline flex items-center justify-between gap-3 text-xs"
        >
          <div className="flex items-center gap-2 text-text-muted">
            <span className="material-symbols-outlined text-[18px] text-amber-500">wifi_off</span>
            <span>Backend API currently offline: {error}. Showing baseline catalogue.</span>
          </div>
          <button
            type="button"
            onClick={() => loadData(true)}
            className="px-3 py-1 rounded bg-surface-container hover:bg-surface-container-high text-text-primary font-semibold"
          >
            Retry Connection
          </button>
        </div>
      )}

      <section aria-label="Regional KPIs" className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <div
            key={kpi.label}
            className="p-4 rounded-xl bg-surface-card border border-border-hairline flex flex-col gap-1"
          >
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.08em]">
              {kpi.label}
            </span>
            <span className="text-xl font-bold text-text-primary">{kpi.value}</span>
            {kpi.progressPercent !== undefined ? (
              <div className="w-full h-1.5 rounded-full bg-surface-container my-1 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-amber-500 to-emergency-red"
                  style={{ width: `${kpi.progressPercent}%` }}
                />
              </div>
            ) : null}
            <span className="text-[11px] font-semibold text-secondary">{kpi.subtitle}</span>
          </div>
        ))}
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-text-primary tracking-tight">
              Priority Monitoring Sectors
            </h2>
            <span className="text-xs text-secondary">
              ({displaySectors.length} locations requiring active review)
            </span>
          </div>
          <Link
            to="/map"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-container hover:bg-surface-container-high border border-border-hairline text-text-primary text-xs font-semibold transition-colors"
          >
            <span className="material-symbols-outlined text-[16px] text-text-muted">map</span>
            <span>Map View</span>
          </Link>
        </div>

        {displaySectors.length === 0 ? (
          <div className="bg-surface-card border border-border-hairline rounded-xl p-8 text-center text-text-muted text-sm">
            No locations currently requiring priority review.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {displaySectors.map((sector) => (
              <article
                key={sector.id}
                className={`bg-surface-card rounded-xl p-5 border border-border-hairline shadow-xs flex flex-col justify-between gap-4 ${
                  sector.riskTier === "High Risk" ? "border-l-[3px] border-l-emergency-red" : ""
                }`}
              >
                <div className="flex flex-col gap-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                        {sector.id}
                      </span>
                      <h3 className="text-base font-bold text-text-primary mt-0.5">{sector.name}</h3>
                    </div>
                    <Badge tone={sector.isStale ? "warning" : "neutral"}>
                      {sector.updatedAgo?.includes("ago") ? sector.updatedAgo : `${sector.updatedAgo} • ${sector.isStale ? "stale" : "fresh"}`}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <Badge tone={sector.hazard === "flood" ? "emergency" : "dgre"}>
                      {sector.threatLabel}
                    </Badge>
                    <Badge tone="neutral">{sector.riskTier}</Badge>
                  </div>

                  <p className="text-xs text-secondary pt-1">{sector.summaryMetric}</p>
                </div>

                <div className="pt-3 border-t border-border-hairline flex flex-col gap-2">
                  <span className="text-xs font-medium text-text-muted">{sector.exposureSummary}</span>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 text-xs font-medium text-on-surface-variant">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          sector.confidence === "High" ? "bg-alert-green" : "bg-amber-500"
                        }`}
                      />
                      <span>{sector.confidence} Confidence</span>
                    </div>
                    <Link
                      to={`/locations/${sector.id}`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-border-hairline bg-surface-container-low hover:bg-surface-container text-xs font-semibold text-text-primary transition-colors"
                    >
                      <span>View Details</span>
                      <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer className="p-4 rounded-xl bg-surface-card border border-border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-[22px] text-text-primary">fact_check</span>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-text-primary">
              Active Authoritative Bulletins (Read-Only)
            </span>
            <span className="text-[11px] text-text-muted">
              CWC Flood Watch (Poonch) • DGRE Stage-3 Avalanche Warning (Gulmarg)
            </span>
          </div>
        </div>
        <Link
          to="/warnings"
          className="px-4 py-1.5 rounded-full bg-surface-container hover:bg-surface-container-high text-text-primary text-xs font-semibold transition-colors self-start sm:self-auto"
        >
          Review Bulletins
        </Link>
      </footer>
    </div>
  );
}
