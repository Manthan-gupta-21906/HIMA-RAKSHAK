import { Link } from "react-router-dom";
import { Badge } from "../components/ui/Badge";
import { MOCK_SECTORS, REGIONAL_KPIS } from "../data/mockSectors";

/** Regional Hazard Monitor overview matching Stitch main_dashboard_map_priority_list. */
export function OverviewPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.08em]">
              Sector J&amp;K Overview
            </span>
            <span className="text-border-hairline">•</span>
            <span className="text-[10px] font-semibold text-secondary">Updated 2m ago (Sample Data)</span>
          </div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">
            Regional Hazard Monitor
          </h1>
          <p className="text-xs sm:text-sm text-secondary">
            Monitoring across critical districts and river basins in Jammu &amp; Kashmir.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 border border-border-hairline text-xs">
            <span className="material-symbols-outlined text-[16px] text-agency-dgre">warning</span>
            <span className="font-medium text-text-primary">47/48 Stations Synced</span>
            <span className="text-border-hairline">•</span>
            <span className="font-semibold text-agency-dgre">1 Delayed</span>
          </div>
          <Link
            to="/sources"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-surface-container hover:bg-surface-container-high text-text-primary text-xs font-semibold transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">sensors</span>
            <span>Sources</span>
          </Link>
        </div>
      </div>

      <section aria-label="Regional KPIs" className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {REGIONAL_KPIS.map((kpi) => (
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
              ({MOCK_SECTORS.length} locations requiring active review)
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {MOCK_SECTORS.filter((s) => s.isPriority).map((sector) => (
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
                  <Badge tone={sector.isStale ? "warning" : "neutral"}>{sector.updatedAgo}</Badge>
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
