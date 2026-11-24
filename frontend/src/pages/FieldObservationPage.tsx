import { Link, useSearchParams } from "react-router-dom";
import { ObservationForm } from "../components/observation/ObservationForm";
import { Badge } from "../components/ui/Badge";
import { SECTOR_OPTIONS } from "../data/observationDefaults";

const PROTOCOL_CHIPS = [
  {
    icon: "shield",
    color: "text-agency-dgre",
    title: "DGRE Protocol 3.2",
    detail: "Certified calibration standard",
  },
  {
    icon: "radar",
    color: "text-critical-blue",
    title: "IMD Doppler Sync",
    detail: "Cross-checked via Gulmarg radar",
  },
  {
    icon: "emergency",
    color: "text-emergency-red",
    title: "CWC Basin Alert",
    detail: "Hydraulic runoff cascade active",
  },
];

/** Field Observation page matching Stitch log_field_observation_validation_error (FORM OPS-JK-449). */
export function FieldObservationPage() {
  const [searchParams] = useSearchParams();
  const sectorFromUrl = searchParams.get("sector");
  const hazardFromUrl = searchParams.get("hazard");

  const defaultSector = SECTOR_OPTIONS.find((option) => option.value === sectorFromUrl);

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
            <span className="material-symbols-outlined text-[16px]">dashboard</span>
            Dashboard
          </div>
          <span className="text-text-muted">/</span>
          <span className="text-text-muted uppercase font-medium">Telemetry Override</span>
          <span className="text-text-muted">/</span>
          <span className="font-semibold text-text-primary uppercase">Log Observation</span>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-card border border-border-hairline shadow-xs">
          <span
            className="flex h-2 w-2 relative"
            style={{ animation: "ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite" }}
          >
            <span
              className="absolute inline-flex h-full w-full rounded-full bg-hazard-yellow opacity-75 animate-ping"
            />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-hazard-yellow" />
          </span>
          <span className="text-[10px] font-bold uppercase tracking-wider text-text-primary">
            DGRE Telemetry Latency: +38 Min • Field Manual Override Authorized
          </span>
        </div>
      </header>

      <div className="max-w-2xl mx-auto">
        <div className="bg-surface-card rounded-xl border border-border-hairline shadow-xs p-5 sm:p-7 relative overflow-hidden">
          <div className="flex items-start justify-between gap-4 pb-5 border-b border-border-hairline mb-5">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="px-2 py-0.5 rounded bg-surface-container-low text-text-muted text-[10px] font-bold uppercase tracking-wider">
                  Form Ops-Jk-449
                </span>
                <span className="text-[10px] text-text-muted font-semibold uppercase tracking-wider">
                  Secure Protocol Level 2
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-text-primary tracking-tight">
                Log Field Observation &amp; Verify Data
              </h1>
              <p className="text-xs sm:text-sm text-secondary mt-1">
                Field observations update local hazard models and trigger instantaneous recalculation
                of vulnerable sector threat tiers.
              </p>
            </div>
            <div className="hidden sm:flex items-center justify-center w-10 h-10 rounded-lg bg-surface-container-low border border-border-hairline text-text-primary shrink-0">
              <span className="material-symbols-outlined text-[22px]">edit_document</span>
            </div>
          </div>

          <ObservationForm
            initialSectorId={sectorFromUrl ?? undefined}
            initialHazardKind={
              (hazardFromUrl === "flood" ? "flood" : "avalanche") as "avalanche" | "flood"
            }
            onSubmit={(result) => {
              // Demo hook: in production this posts to the backend observation API.
              void result;
            }}
          />

          <footer className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-3 px-1">
            {PROTOCOL_CHIPS.map((chip) => (
              <div
                key={chip.title}
                className="flex items-center gap-3 p-3 rounded-lg bg-surface-card border border-border-hairline"
              >
                <div className="w-7 h-7 rounded bg-surface-container-low flex items-center justify-center text-xs">
                  <span className={`material-symbols-outlined text-[16px] ${chip.color}`}>
                    {chip.icon}
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-text-primary">{chip.title}</span>
                  <span className="text-[10px] text-text-muted">{chip.detail}</span>
                </div>
              </div>
            ))}
          </footer>
        </div>
      </div>

      <footer className="mt-4 flex items-center justify-between gap-3">
        <Badge tone="neutral">{defaultSector?.label ?? "No sector selected"}</Badge>
        <Link
          to="/map"
          className="inline-flex items-center justify-center gap-1.5 h-9 px-4 rounded-full bg-primary-container text-on-primary text-xs font-semibold hover:bg-text-primary transition-colors"
        >
          <span className="material-symbols-outlined text-[16px]">arrow_back</span>
          Back to Risk Map
        </Link>
      </footer>
    </div>
  );
}
