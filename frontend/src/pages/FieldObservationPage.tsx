import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchObservations, type ObservationContract } from "../api/observations";
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
  const [activeSectorId, setActiveSectorId] = useState(sectorFromUrl ?? "JK-GUL-01");
  const [observations, setObservations] = useState<ObservationContract[]>([]);
  const [obsLoading, setObsLoading] = useState(false);
  const [obsError, setObsError] = useState<string | null>(null);

  const defaultSector = SECTOR_OPTIONS.find((option) => option.value === activeSectorId);

  const loadObservations = useCallback(async (locationId: string) => {
    setObsLoading(true);
    setObsError(null);
    try {
      const res = await fetchObservations({ location_id: locationId, page_size: 5 });
      setObservations(res.items ?? []);
    } catch (err: unknown) {
      setObsError(err instanceof Error ? err.message : "Unable to load persisted observations");
      setObservations([]);
    } finally {
      setObsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadObservations(activeSectorId);
  }, [activeSectorId, loadObservations]);

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <nav
          aria-label="Breadcrumb"
          className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-[0.06em]"
        >
          <Link
            to="/"
            className="inline-flex items-center gap-1 font-bold text-text-muted hover:text-text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-[15px]">dashboard</span>
            <span>Dashboard</span>
          </Link>
          <span className="text-border-hairline">/</span>
          <span className="font-medium text-text-muted">Telemetry Override</span>
          <span className="text-border-hairline">/</span>
          <span className="font-bold text-text-primary">Log Observation</span>
        </nav>

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
            onSectorChange={(nextSectorId) => setActiveSectorId(nextSectorId)}
            onSubmit={(result) => {
              setActiveSectorId(result.sectorId);
              void loadObservations(result.sectorId);
            }}
          />

          <section
            aria-label="Persisted Observations"
            className="mt-6 pt-5 border-t border-border-hairline"
          >
            <div className="flex items-center justify-between gap-2 mb-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-text-primary">
                Recent Persisted Observations ({activeSectorId})
              </h2>
              <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                Live Backend Ledger
              </span>
            </div>
            {obsLoading && (
              <p className="text-xs text-text-muted">Loading persisted observations…</p>
            )}
            {!obsLoading && obsError && (
              <p className="text-xs text-emergency-red">{obsError}</p>
            )}
            {!obsLoading && !obsError && observations.length === 0 && (
              <p className="text-xs text-text-muted">
                No persisted observations recorded yet for {activeSectorId}.
              </p>
            )}
            {!obsLoading && observations.length > 0 && (
              <ul className="divide-y divide-border-hairline rounded-lg border border-border-hairline bg-surface-container-low">
                {observations.map((obs) => (
                  <li
                    key={obs.observation_id}
                    className="flex items-center justify-between gap-3 px-3 py-2 text-xs"
                  >
                    <div className="flex flex-col">
                      <span className="font-semibold text-text-primary">
                        {obs.metric}: {obs.value} {obs.unit}
                      </span>
                      <span className="text-[10px] text-text-muted">
                        ID: {obs.observation_id} • Source: {obs.source_id}
                      </span>
                    </div>
                    <span className="text-[10px] text-text-muted tabular-nums">
                      {new Date(obs.observed_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

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
