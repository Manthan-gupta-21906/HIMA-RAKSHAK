import { Badge, type BadgeTone } from "../../components/ui/Badge";
import type {
  OfficialWarning,
  WarningAgency,
  WarningSeverity,
} from "../../types/warning";

export interface WarningPanelProps {
  warning: OfficialWarning | null;
  className?: string;
}

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

function isWarningExpired(validUntilStr: string): boolean {
  try {
    const normalized = validUntilStr.replace(/\s*IST\b/i, " +05:30");
    const validUntilDate = new Date(normalized);
    if (!isNaN(validUntilDate.getTime())) {
      return Date.now() > validUntilDate.getTime();
    }
    const directDate = new Date(validUntilStr);
    if (!isNaN(directDate.getTime())) {
      return Date.now() > directDate.getTime();
    }
  } catch {
    // Fallback if string cannot be directly parsed by Date
  }
  return false;
}

/**
 * Authoritative official warning panel.
 * Displays agency bulletins separately from model-generated assessments without score alteration.
 */
export function WarningPanel({ warning, className = "" }: WarningPanelProps) {
  if (!warning) {
    return (
      <div
        data-testid="warning-panel-empty"
        className={`bg-surface-card border border-border-hairline rounded-xl p-8 text-center text-text-muted ${className}`}
      >
        <p className="text-sm">Select an official warning bulletin to inspect details.</p>
      </div>
    );
  }

  const expired = isWarningExpired(warning.validUntil);
  const isSample =
    warning.sourceReference?.includes("Sample") ||
    warning.id?.includes("SAMPLE");

  return (
    <div
      data-testid="warning-panel"
      className={`bg-surface-card border border-border-hairline rounded-xl p-5 sm:p-6 flex flex-col gap-4 shadow-xs ${className}`}
    >
      {/* Header tags and distinction disclaimer */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-border-hairline">
        <div className="flex items-center gap-2">
          <Badge tone={AGENCY_TONE[warning.agency]} showDot>
            {warning.agency}
          </Badge>
          <Badge tone={SEVERITY_TONE[warning.severity]}>
            {warning.severity} Alert
          </Badge>
          {expired ? (
            <span
              data-testid="warning-expired-tag"
              className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-danger-surface text-danger-text border border-danger-border"
            >
              Expired
            </span>
          ) : (
            <span
              data-testid="warning-active-tag"
              className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-success-surface text-success-text border border-success-border"
            >
              Active
            </span>
          )}
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
          Read-Only Record
        </span>
      </div>

      {/* Model isolation notice */}
      <div className="px-3 py-2 rounded-md bg-surface-subtle/80 border border-border-hairline text-[11px] text-text-muted flex items-start gap-1.5">
        <span className="font-semibold text-text-primary">Authoritative Agency Advisory:</span>
        <span>Kept separate from model risk calculations; not blended into automated scores.</span>
      </div>

      {/* Title & Agency Metadata */}
      <div>
        <p className="text-[11px] font-semibold text-text-muted">
          {warning.agencyFullName} • {warning.bulletinCode}
        </p>
        <h2 className="text-lg font-bold text-text-primary mt-1">{warning.title}</h2>
      </div>

      {/* Summary */}
      <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
        {warning.summary}
      </p>

      {/* Validity & Geo Scope Details */}
      <div className="p-3.5 rounded-lg bg-surface-container-low border border-border-hairline flex flex-col gap-1.5 text-xs">
        <div className="flex justify-between gap-2">
          <span className="text-text-muted">Issued</span>
          <span className="font-semibold text-text-primary">{warning.issuedAt}</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-text-muted">Valid Until</span>
          <span className="font-semibold text-text-primary">{warning.validUntil}</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-text-muted">District</span>
          <span className="font-semibold text-text-primary">{warning.district}</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-text-muted">Affected Sectors</span>
          <span className="font-semibold text-text-primary text-right">
            {warning.affectedSectors.join(", ")}
          </span>
        </div>
      </div>

      {/* Advisory & Source Provenance */}
      <div className="p-3.5 rounded-lg bg-surface-subtle/60 border border-border-hairline text-xs text-on-surface-variant">
        <p className="font-bold text-text-primary mb-1">Official Advisory Note</p>
        <p>{warning.advisoryNotes}</p>
        <p className="text-[11px] text-text-muted mt-2">
          Provenance: <span data-testid="warning-source-ref">{warning.sourceReference}</span>
        </p>
        {isSample && (
          <p className="text-[10px] text-amber-500 font-medium mt-1">
            * Sample warning fixture for training and integration.
          </p>
        )}
      </div>
    </div>
  );
}
