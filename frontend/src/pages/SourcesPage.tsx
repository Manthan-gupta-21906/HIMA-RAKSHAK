import { useMemo, useState } from "react";
import { Badge, type BadgeTone } from "../components/ui/Badge";
import { MOCK_DATA_SOURCES } from "../data/mockDataSources";
import type { SourceAgency, SourceStatus } from "../types/dataSource";

type StatusFilter = "all" | SourceStatus;
type AgencyFilter = "all" | SourceAgency;

const STATUS_BADGE: Record<SourceStatus, { tone: BadgeTone; label: string; dot: string }> = {
  online: { tone: "clear", label: "Online", dot: "bg-alert-green" },
  delayed: { tone: "warning", label: "Delayed", dot: "bg-amber-500" },
  offline: { tone: "emergency", label: "Offline", dot: "bg-emergency-red" },
};

const AGENCY_TONE: Record<SourceAgency, BadgeTone> = {
  IMD: "imd",
  CWC: "cwc",
  DGRE: "dgre",
  SDRF: "neutral",
};

/** Data source monitoring interface showing connection status, latency, and freshness. */
export function SourcesPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [agencyFilter, setAgencyFilter] = useState<AgencyFilter>("all");
  const [lastChecked, setLastChecked] = useState("Just now (Sample Registry)");

  const counts = useMemo(() => {
    return {
      total: MOCK_DATA_SOURCES.length,
      online: MOCK_DATA_SOURCES.filter((s) => s.status === "online").length,
      delayed: MOCK_DATA_SOURCES.filter((s) => s.status === "delayed").length,
      offline: MOCK_DATA_SOURCES.filter((s) => s.status === "offline").length,
    };
  }, []);

  const filteredSources = useMemo(() => {
    return MOCK_DATA_SOURCES.filter((src) => {
      if (statusFilter !== "all" && src.status !== statusFilter) return false;
      if (agencyFilter !== "all" && src.agency !== agencyFilter) return false;
      return true;
    });
  }, [statusFilter, agencyFilter]);

  const handleRefresh = () => {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    setLastChecked(`Checked at ${hh}:${mm} (Sample Registry)`);
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
            Telemetry Provenance &amp; Freshness
          </span>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight mt-0.5">
            Data Source Status
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-0.5">
            Monitor sensor connectivity, ingestion latency, and stale-data flags across J&amp;K feeds.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-text-muted px-3 py-1.5 rounded-full bg-surface-card border border-border-hairline">
            {lastChecked}
          </span>
          <button
            type="button"
            onClick={handleRefresh}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary text-xs font-semibold hover:bg-text-primary transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            <span>Refresh Status</span>
          </button>
        </div>
      </div>

      <section aria-label="Source health summary" className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface-card border border-border-hairline flex flex-col gap-1">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.08em]">
            Registered Feeds
          </span>
          <span className="text-xl font-bold text-text-primary">{counts.total} Sources</span>
          <span className="text-[11px] text-secondary">Sample cached registry</span>
        </div>
        <div className="p-4 rounded-xl bg-surface-card border border-border-hairline flex flex-col gap-1">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.08em]">
            Online
          </span>
          <span className="text-xl font-bold text-text-primary">{counts.online} Nominal</span>
          <span className="text-[11px] text-secondary">Within freshness SLA</span>
        </div>
        <div className="p-4 rounded-xl bg-surface-card border border-border-hairline flex flex-col gap-1">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.08em]">
            Delayed
          </span>
          <span className="text-xl font-bold text-agency-dgre">{counts.delayed} High Latency</span>
          <span className="text-[11px] text-secondary">Mountain backhaul lag</span>
        </div>
        <div className="p-4 rounded-xl bg-surface-card border border-border-hairline flex flex-col gap-1">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-[0.08em]">
            Offline / Stale
          </span>
          <span className="text-xl font-bold text-emergency-red">{counts.offline} Stale</span>
          <span className="text-[11px] text-secondary">Confidence downgraded</span>
        </div>
      </section>

      <section
        aria-label="Source filters"
        className="bg-surface-card border border-border-hairline rounded-xl p-4 flex flex-wrap items-center justify-between gap-3"
      >
        <div className="flex flex-wrap items-center gap-2">
          {(["all", "online", "delayed", "offline"] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setStatusFilter(status)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold capitalize transition-colors cursor-pointer ${
                statusFilter === status
                  ? "bg-primary-container text-on-primary"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
              }`}
            >
              {status === "all" ? "All Statuses" : status}
            </button>
          ))}
        </div>

        <select
          aria-label="Filter by agency"
          value={agencyFilter}
          onChange={(e) => setAgencyFilter(e.target.value as AgencyFilter)}
          className="h-9 px-3 rounded-full bg-surface-container-low border border-border-hairline text-xs font-semibold text-text-primary"
        >
          <option value="all">All Agencies</option>
          <option value="IMD">IMD</option>
          <option value="CWC">CWC</option>
          <option value="DGRE">DGRE</option>
          <option value="SDRF">SDRF</option>
        </select>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredSources.map((src) => {
          const statusMeta = STATUS_BADGE[src.status];
          return (
            <article
              key={src.id}
              className="bg-surface-card border border-border-hairline rounded-xl p-5 flex flex-col justify-between gap-3 shadow-xs"
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge tone={AGENCY_TONE[src.agency]} showDot={src.agency !== "SDRF"}>
                      {src.agency}
                    </Badge>
                    <span className="text-[11px] font-semibold text-text-muted">{src.id}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${statusMeta.dot}`} />
                    <Badge tone={statusMeta.tone}>{statusMeta.label}</Badge>
                  </div>
                </div>

                <h2 className="text-base font-bold text-text-primary">{src.name}</h2>
                <p className="text-xs text-secondary">
                  {src.category} • Coverage: {src.coverage}
                </p>
              </div>

              <div className="pt-3 border-t border-border-hairline flex flex-col gap-1.5 text-xs">
                <div className="flex justify-between gap-2">
                  <span className="text-text-muted">Last Updated</span>
                  <span className="font-semibold text-text-primary">{src.lastUpdated}</span>
                </div>
                <div className="flex justify-between gap-2">
                  <span className="text-text-muted">Latency / Cadence</span>
                  <span className="font-medium text-on-surface-variant">
                    {src.latencyLabel} ({src.cadence})
                  </span>
                </div>
                <p className="text-[11px] text-text-muted pt-1">{src.provenanceNote}</p>
                {src.knownLimitation ? (
                  <p className="text-[11px] text-agency-dgre font-medium bg-amber-50/70 dark:bg-amber-950/40 border border-border-hairline rounded-lg px-2.5 py-1.5 mt-1">
                    Limitation: {src.knownLimitation}
                  </p>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
