import { Link } from "react-router-dom";
import { Badge, type BadgeTone } from "../ui/Badge";
import type {
  EngineStatus,
  EngineTone,
  HazardEngine,
  ProgressTone,
} from "../../types/location";

const ACCENT_CLASSES: Record<EngineStatus, string> = {
  warning: "bg-emergency-red",
  watch: "bg-hazard-yellow",
  normal: "bg-alert-green",
  insufficient: "bg-text-muted",
  offline: "bg-text-muted",
};

const STATUS_BADGE: Record<EngineStatus, BadgeTone> = {
  warning: "emergency",
  watch: "warning",
  normal: "clear",
  insufficient: "neutral",
  offline: "warning",
};

const PROGRESS_CLASSES: Record<ProgressTone, string> = {
  emergency: "bg-emergency-red",
  warning: "bg-agency-dgre",
  clear: "bg-alert-green",
  cwc: "bg-agency-cwc",
};

const NOTE_CLASSES: Record<EngineTone, string> = {
  critical: "bg-error-container/60 border-emergency-red/30 text-on-error-container",
  emergency: "bg-error-container/60 border-emergency-red/30 text-on-error-container",
  warning: "bg-amber-50 dark:bg-amber-950/40 border-hazard-yellow/70 text-amber-900 dark:text-amber-200",
  info: "bg-surface-container-low border-border-hairline text-on-surface-variant",
  neutral: "bg-surface-container-low border-border-hairline text-on-surface-variant",
  clear: "bg-alert-green/10 border-alert-green/40 text-[#054024]",
};

const NOTE_ICONS: Record<EngineTone, string> = {
  critical: "error",
  emergency: "error",
  warning: "warning",
  info: "info",
  neutral: "info",
  clear: "check_circle",
};

const CONFIDENCE_DOT: Record<HazardEngine["confidence"], string> = {
  High: "bg-alert-green",
  Moderate: "bg-agency-dgre",
  Low: "bg-emergency-red",
};

/**
 * One hazard engine (Flood or Avalanche). The two pathways are intentionally
 * rendered as independent cards so their status and confidence are never merged.
 */
export function HazardEngineCard({
  engine,
  fieldLogHref,
}: {
  engine: HazardEngine;
  fieldLogHref: string;
}) {
  const readinessGate = engine.readiness !== "operational";

  return (
    <article
      aria-labelledby={`engine-${engine.id}-title`}
      className={`bg-surface-card rounded-xl border border-border-hairline shadow-xs p-5 flex flex-col gap-4 ${
        engine.available ? "" : "border-dashed"
      }`}
    >
      <header className="flex flex-wrap items-start justify-between gap-2 pb-3 border-b border-border-hairline">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${ACCENT_CLASSES[engine.status]}`} />
          <h3
            id={`engine-${engine.id}-title`}
            className="text-base font-bold text-text-primary tracking-tight"
          >
            {engine.title}
          </h3>
        </div>
        <Badge tone={STATUS_BADGE[engine.status]}>{engine.statusLabel}</Badge>
      </header>

      <p className="text-xs text-secondary">{engine.summary}</p>

      {readinessGate ? (
        <div
          role="status"
          className="rounded-lg border border-hazard-yellow/70 bg-[#fffbe6] p-3 flex items-start gap-2"
        >
          <span className="material-symbols-outlined text-[17px] text-agency-dgre shrink-0 mt-0.5">
            warning
          </span>
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-bold text-text-primary">{engine.readinessLabel}</span>
            {engine.readinessNote ? (
              <span className="text-[11px] text-on-surface-variant">{engine.readinessNote}</span>
            ) : null}
          </div>
        </div>
      ) : null}

      {engine.progress ? (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-text-muted">{engine.progress.label}</span>
            <span className="font-semibold text-text-primary">{engine.progress.valueText}</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-surface-container overflow-hidden">
            <div
              className={`h-full rounded-full ${PROGRESS_CLASSES[engine.progress.tone]}`}
              style={{ width: `${Math.min(100, Math.max(0, engine.progress.percent))}%` }}
            />
          </div>
        </div>
      ) : null}

      <dl className="flex flex-col divide-y divide-border-hairline border-t border-border-hairline">
        {engine.metrics.map((metric) => (
          <div
            key={metric.label}
            className="flex flex-wrap items-baseline justify-between gap-2 py-2"
          >
            <dt className="text-xs text-text-muted">{metric.label}</dt>
            <dd className="text-xs font-semibold text-text-primary text-right">
              {metric.value}
              {metric.hint ? (
                <span className="block text-[10px] font-normal text-text-muted">{metric.hint}</span>
              ) : null}
            </dd>
          </div>
        ))}
      </dl>

      <div
        className={`rounded-lg border p-3 text-[11px] flex items-start gap-2 ${NOTE_CLASSES[engine.noteTone]}`}
      >
        <span className="material-symbols-outlined text-[16px] shrink-0 mt-0.5">
          {NOTE_ICONS[engine.noteTone]}
        </span>
        <span className="font-medium">{engine.note}</span>
      </div>

      <footer className="pt-3 border-t border-border-hairline flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div className="flex flex-col gap-1">
          <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-on-surface-variant">
            <span className={`w-1.5 h-1.5 rounded-full ${CONFIDENCE_DOT[engine.confidence]}`} />
            {engine.confidence} Confidence ({engine.freshness})
          </span>
          <span className="text-[10px] text-text-muted">
            {engine.agency} • {engine.provenance}
          </span>
        </div>

        <Link
          to={fieldLogHref}
          className="inline-flex items-center justify-center gap-1.5 h-9 px-3.5 rounded-full bg-surface-container-low border border-border-hairline hover:bg-surface-container text-[11px] font-semibold text-text-primary transition-colors"
        >
          <span>{engine.actionLabel}</span>
          <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
        </Link>
      </footer>
    </article>
  );
}
