import { Badge } from "../ui/Badge";
import type { LocationKpi, ProgressTone } from "../../types/location";

const PROGRESS_CLASSES: Record<ProgressTone, string> = {
  emergency: "bg-emergency-red",
  warning: "bg-agency-dgre",
  clear: "bg-alert-green",
  cwc: "bg-agency-cwc",
};

/** Compact KPI tile used by the location detail summary strip. */
export function LocationKpiCard({ kpi }: { kpi: LocationKpi }) {
  return (
    <div className="bg-surface-card rounded-xl border border-border-hairline shadow-xs p-4 sm:p-5 flex flex-col justify-between min-h-[118px] gap-2">
      <div className="flex items-start justify-between gap-2">
        <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
          {kpi.label}
        </span>
        {kpi.badge ? <Badge tone={kpi.badgeTone ?? "neutral"}>{kpi.badge}</Badge> : null}
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-lg sm:text-xl font-bold text-text-primary tracking-tight">
          {kpi.value}
        </span>

        {kpi.progressPercent !== undefined ? (
          <div className="w-full h-1.5 rounded-full bg-surface-container overflow-hidden my-0.5">
            <div
              className={`h-full rounded-full ${PROGRESS_CLASSES[kpi.progressTone ?? "warning"]}`}
              style={{ width: `${Math.min(100, Math.max(0, kpi.progressPercent))}%` }}
            />
          </div>
        ) : null}

        <span className="text-[11px] font-medium text-secondary">{kpi.subtitle}</span>
      </div>
    </div>
  );
}
