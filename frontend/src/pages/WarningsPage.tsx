import { useMemo, useState } from "react";
import { Badge, type BadgeTone } from "../components/ui/Badge";
import { MOCK_WARNINGS } from "../data/mockWarnings";
import type {
  OfficialWarning,
  WarningAgency,
  WarningHazard,
  WarningSeverity,
} from "../types/warning";

type AgencyFilter = "all" | WarningAgency;
type HazardFilter = "all" | WarningHazard;
type SeverityFilter = "all" | WarningSeverity;

const AGENCY_TONE: Record<WarningAgency, BadgeTone> = {
  IMD: "imd",
  CWC: "cwc",
  DGRE: "dgre",
};

const SEVERITY_TONE: Record<WarningSeverity, BadgeTone> = {
  Red: "emergency",
  Orange: "warning",
  Yellow: "neutral",
};

/** Read-only authoritative agency warnings listing with filters and detail panel. */
export function WarningsPage() {
  const [agencyFilter, setAgencyFilter] = useState<AgencyFilter>("all");
  const [hazardFilter, setHazardFilter] = useState<HazardFilter>("all");
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string>(MOCK_WARNINGS[0].id);

  const filteredWarnings = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return MOCK_WARNINGS.filter((w) => {
      if (agencyFilter !== "all" && w.agency !== agencyFilter) return false;
      if (hazardFilter !== "all" && w.hazard !== hazardFilter) return false;
      if (severityFilter !== "all" && w.severity !== severityFilter) return false;
      if (
        q &&
        !w.title.toLowerCase().includes(q) &&
        !w.district.toLowerCase().includes(q) &&
        !w.bulletinCode.toLowerCase().includes(q)
      ) {
        return false;
      }
      return true;
    });
  }, [agencyFilter, hazardFilter, severityFilter, searchQuery]);

  const activeWarning: OfficialWarning | null =
    filteredWarnings.find((w) => w.id === selectedId) ?? filteredWarnings[0] ?? null;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
              Authoritative Agency Bulletins
            </span>
            <Badge tone="neutral">Read-Only</Badge>
          </div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight mt-0.5">
            Official Warnings
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-0.5">
            Official IMD, CWC, and DGRE bulletins remain authoritative and are never altered by prototype models.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-card border border-border-hairline text-xs text-text-muted self-start lg:self-auto">
          <span className="material-symbols-outlined text-[16px] text-text-primary">lock</span>
          <span className="font-medium text-text-primary">Sample Cached Bulletins • Unmodified</span>
        </div>
      </div>

      <section
        aria-label="Warning filters"
        className="bg-surface-card border border-border-hairline rounded-xl p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3"
      >
        <div className="flex flex-wrap items-center gap-2">
          {(["all", "IMD", "CWC", "DGRE"] as const).map((agency) => (
            <button
              key={agency}
              type="button"
              onClick={() => setAgencyFilter(agency)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                agencyFilter === agency
                  ? "bg-primary-container text-on-primary"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
              }`}
            >
              {agency === "all" ? "All Agencies" : agency}
            </button>
          ))}

          <select
            aria-label="Filter by hazard"
            value={hazardFilter}
            onChange={(e) => setHazardFilter(e.target.value as HazardFilter)}
            className="h-8 px-3 rounded-full bg-surface-container-low border border-border-hairline text-xs font-semibold text-text-primary"
          >
            <option value="all">All Hazards</option>
            <option value="flood">Flood</option>
            <option value="avalanche">Avalanche</option>
            <option value="weather">Weather</option>
          </select>

          <select
            aria-label="Filter by severity"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value as SeverityFilter)}
            className="h-8 px-3 rounded-full bg-surface-container-low border border-border-hairline text-xs font-semibold text-text-primary"
          >
            <option value="all">All Severities</option>
            <option value="Red">Red (Emergency)</option>
            <option value="Orange">Orange (Warning)</option>
            <option value="Yellow">Yellow (Watch)</option>
          </select>
        </div>

        <div className="relative w-full lg:w-64">
          <span className="material-symbols-outlined text-[16px] text-text-muted absolute left-3 top-1/2 -translate-y-1/2">
            search
          </span>
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search district or bulletin..."
            aria-label="Search warnings"
            className="w-full h-9 pl-9 pr-3 rounded-full bg-surface-container-lowest border border-border-hairline text-xs text-text-primary focus:outline-none focus:border-primary-container"
          />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        <div className="lg:col-span-7 flex flex-col gap-3">
          {filteredWarnings.length === 0 ? (
            <div className="bg-surface-card border border-border-hairline rounded-xl p-6 text-center text-xs text-text-muted">
              No official bulletins match the current filter criteria.
            </div>
          ) : (
            filteredWarnings.map((warning) => {
              const isSelected = activeWarning?.id === warning.id;
              return (
                <button
                  key={warning.id}
                  type="button"
                  onClick={() => setSelectedId(warning.id)}
                  className={`w-full text-left bg-surface-card rounded-xl p-5 border transition-all cursor-pointer flex flex-col gap-2.5 ${
                    isSelected
                      ? "border-primary-container shadow-sm"
                      : "border-border-hairline hover:bg-surface-container-low/50"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge tone={AGENCY_TONE[warning.agency]} showDot>
                        {warning.agency}
                      </Badge>
                      <Badge tone={SEVERITY_TONE[warning.severity]}>{warning.severity}</Badge>
                      <span className="text-[11px] font-semibold text-text-muted">
                        {warning.bulletinCode}
                      </span>
                    </div>
                    <span className="text-[11px] text-text-muted">{warning.issuedAt}</span>
                  </div>

                  <h2 className="text-sm sm:text-base font-bold text-text-primary">
                    {warning.title}
                  </h2>
                  <p className="text-xs text-secondary line-clamp-2">{warning.summary}</p>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border-hairline text-[11px] text-text-muted">
                    <span>District: {warning.district}</span>
                    <span>Valid until: {warning.validUntil}</span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        <aside className="lg:col-span-5">
          {activeWarning ? (
            <div className="bg-surface-card border border-border-hairline rounded-xl p-5 sm:p-6 flex flex-col gap-4 shadow-xs">
              <div className="flex items-center justify-between gap-2 pb-3 border-b border-border-hairline">
                <div className="flex items-center gap-2">
                  <Badge tone={AGENCY_TONE[activeWarning.agency]} showDot>
                    {activeWarning.agency}
                  </Badge>
                  <Badge tone={SEVERITY_TONE[activeWarning.severity]}>
                    {activeWarning.severity} Alert
                  </Badge>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  Read-Only Record
                </span>
              </div>

              <div>
                <p className="text-[11px] font-semibold text-text-muted">
                  {activeWarning.agencyFullName} • {activeWarning.bulletinCode}
                </p>
                <h2 className="text-lg font-bold text-text-primary mt-1">{activeWarning.title}</h2>
              </div>

              <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
                {activeWarning.summary}
              </p>

              <div className="p-3.5 rounded-lg bg-surface-container-low border border-border-hairline flex flex-col gap-1.5 text-xs">
                <div className="flex justify-between gap-2">
                  <span className="text-text-muted">Issued</span>
                  <span className="font-semibold text-text-primary">{activeWarning.issuedAt}</span>
                </div>
                <div className="flex justify-between gap-2">
                  <span className="text-text-muted">Valid Until</span>
                  <span className="font-semibold text-text-primary">
                    {activeWarning.validUntil}
                  </span>
                </div>
                <div className="flex justify-between gap-2">
                  <span className="text-text-muted">District</span>
                  <span className="font-semibold text-text-primary">{activeWarning.district}</span>
                </div>
                <div className="flex justify-between gap-2">
                  <span className="text-text-muted">Sectors</span>
                  <span className="font-semibold text-text-primary text-right">
                    {activeWarning.affectedSectors.join(", ")}
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-surface-subtle/60 border border-border-hairline text-xs text-on-surface-variant">
                <p className="font-bold text-text-primary mb-1">Official Advisory Note</p>
                <p>{activeWarning.advisoryNotes}</p>
                <p className="text-[11px] text-text-muted mt-2">
                  Provenance: {activeWarning.sourceReference}
                </p>
              </div>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
