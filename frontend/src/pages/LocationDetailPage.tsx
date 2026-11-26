import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchLocationDetail, type LocationOut } from "../api/locations";
import { fetchLocationRiskState, type LocationRiskState } from "../api/risk";
import { HazardEngineCard } from "../components/location/HazardEngineCard";
import { LocationKpiCard } from "../components/location/LocationKpiCard";
import { Badge, type BadgeTone } from "../components/ui/Badge";
import { getLocationDetail } from "../data/locationDetails";
import { MOCK_SECTORS } from "../data/mockSectors";

const AGENCY_BADGE: Record<"IMD" | "CWC" | "DGRE", BadgeTone> = {
  IMD: "imd",
  CWC: "cwc",
  DGRE: "dgre",
};

const DIRECTIVE_ICONS = {
  done: { icon: "check_circle", className: "text-alert-green" },
  pending: { icon: "schedule", className: "text-agency-dgre" },
  warning: { icon: "warning", className: "text-emergency-red" },
} as const;

const SENSOR_DOTS = {
  online: "bg-alert-green",
  delayed: "bg-hazard-yellow",
  offline: "bg-emergency-red",
} as const;

const SENSOR_TEXT = {
  online: "text-on-surface-variant",
  delayed: "text-agency-dgre",
  offline: "text-emergency-red",
} as const;

const FACILITY_ICONS: Record<string, string> = {
  Clinics: "local_hospital",
  PHC: "local_hospital",
  CHC: "local_hospital",
  Schools: "school",
  Shelters: "home",
  Helipads: "flight",
};

/** Location detail view with separate flood and avalanche engines plus exposure. */
export function LocationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const sector = MOCK_SECTORS.find((item) => item.id === id);
  const detail = id ? getLocationDetail(id) : null;
  const [liveLocation, setLiveLocation] = useState<LocationOut | null>(null);
  const [, setLiveRiskState] = useState<LocationRiskState | null>(null);
  const [isLiveConnected, setIsLiveConnected] = useState(false);

  useEffect(() => {
    if (!id) return;
    let isMounted = true;
    Promise.allSettled([fetchLocationDetail(id), fetchLocationRiskState(id)])
      .then(([locRes, riskRes]) => {
        if (!isMounted) return;
        if (locRes.status === "fulfilled") {
          setLiveLocation(locRes.value);
          setIsLiveConnected(true);
        }
        if (riskRes.status === "fulfilled") {
          setLiveRiskState(riskRes.value);
          setIsLiveConnected(true);
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, [id]);

  if (!sector || !detail) {
    return (
      <div className="max-w-xl mx-auto bg-surface-card border border-border-hairline rounded-xl p-8 flex flex-col items-center text-center gap-3 mt-10">
        <span className="material-symbols-outlined text-[40px] text-text-muted">wrong_location</span>
        <h1 className="text-xl font-bold text-text-primary">Sector not found</h1>
        <p className="text-sm text-secondary">
          No location detail exists for <span className="font-semibold">{id ?? "this route"}</span>.
          Return to the risk map and select a monitored sector.
        </p>
        <Link
          to="/map"
          className="mt-2 inline-flex items-center gap-1.5 h-9 px-4 rounded-full bg-primary-container text-on-primary text-xs font-semibold"
        >
          <span className="material-symbols-outlined text-[16px]">arrow_back</span>
          Back to Risk Map
        </Link>
      </div>
    );
  }

  const offlineSensors = detail.sensors.filter((sensor) => sensor.status === "offline").length;
  const telemetryLabel =
    offlineSensors > 0
      ? `Telemetry: ${offlineSensors} Station${offlineSensors > 1 ? "s" : ""} Offline`
      : "Telemetry: All Stations Online";

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col lg:flex-row lg:items-start justify-between gap-4 pb-4 border-b border-border-hairline">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
            Location Detail • {detail.sectorId} • Updated {detail.updatedAgo}
          </span>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">{detail.title}</h1>
          <p className="text-xs sm:text-sm text-secondary">{detail.subtitle}</p>
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <Badge tone={sector.hazard === "flood" ? "emergency" : "dgre"}>
              {sector.threatLabel}
            </Badge>
            <Badge tone="neutral">{sector.riskTier}</Badge>
            <Badge tone="neutral">{sector.elevationM} m</Badge>
            {isLiveConnected && <Badge tone="clear">Live Backend Connected</Badge>}
            {liveLocation && <Badge tone="neutral">Coverage: {liveLocation.coverage_status}</Badge>}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium ${
              offlineSensors > 0
                ? "bg-amber-50 dark:bg-amber-950/40 border-hazard-yellow/70 text-amber-900 dark:text-amber-200"
                : "bg-surface-container-low border-border-hairline text-on-surface-variant"
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">
              {offlineSensors > 0 ? "warning" : "sensors"}
            </span>
            {telemetryLabel}
          </span>

          <Link
            to="/map"
            className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-full bg-surface-card border border-border-hairline shadow-xs hover:bg-surface-container text-xs font-semibold text-text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">arrow_back</span>
            Back to Risk Map
          </Link>
        </div>
      </header>

      <section aria-label="Location key metrics" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {detail.kpis.map((kpi) => (
          <LocationKpiCard key={kpi.label} kpi={kpi} />
        ))}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        <section className="lg:col-span-7 flex flex-col gap-4" aria-label="Hazard engine telemetry">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-xs font-bold uppercase tracking-[0.08em] text-text-muted">
              Hazard Engine Telemetry
            </h2>
            <span className="text-[11px] text-text-muted">
              Independent flood and avalanche pathways
            </span>
          </div>

          <HazardEngineCard
            engine={detail.avalanche}
            fieldLogHref={`/field-log?sector=${encodeURIComponent(detail.sectorId)}&hazard=avalanche`}
          />
          <HazardEngineCard
            engine={detail.flood}
            fieldLogHref={`/field-log?sector=${encodeURIComponent(detail.sectorId)}&hazard=flood`}
          />
        </section>

        <aside className="lg:col-span-5 flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-xs font-bold uppercase tracking-[0.08em] text-text-muted">
              Exposure &amp; Field Directives
            </h2>
            <span className="text-[11px] text-text-muted">SOP Tier 2</span>
          </div>

          <section
            aria-labelledby="exposure-title"
            className="bg-surface-card rounded-xl border border-border-hairline shadow-xs p-5 flex flex-col gap-3"
          >
            <div className="flex items-center justify-between gap-2 pb-3 border-b border-border-hairline">
              <h3 id="exposure-title" className="text-base font-bold text-text-primary">
                Exposure &amp; Critical Assets
              </h3>
              <Badge tone="neutral">{detail.exposure.population} residents</Badge>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-surface-container-low border border-border-hairline p-2.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  Elevation
                </span>
                <p className="font-semibold text-text-primary mt-0.5">{detail.exposure.elevation}</p>
              </div>
              <div className="rounded-lg bg-surface-container-low border border-border-hairline p-2.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  Population
                </span>
                <p className="font-semibold text-text-primary mt-0.5">{detail.exposure.population}</p>
              </div>
              <div className="col-span-2 rounded-lg bg-surface-container-low border border-border-hairline p-2.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  Access Road
                </span>
                <p className="font-semibold text-text-primary mt-0.5">{detail.exposure.road}</p>
              </div>
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Facilities
              </span>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                {detail.exposure.facilities.map((facility) => (
                  <span
                    key={facility.label}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container text-[10px] font-semibold text-on-surface-variant"
                  >
                    <span className="material-symbols-outlined text-[13px]">
                      {FACILITY_ICONS[facility.label] ?? "place"}
                    </span>
                    {facility.value} {facility.label}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Critical Assets
              </span>
              <ul className="mt-1.5 flex flex-col gap-1.5">
                {detail.exposure.criticalAssets.map((asset) => (
                  <li
                    key={asset}
                    className="flex items-start gap-1.5 text-[11px] text-on-surface-variant"
                  >
                    <span className="material-symbols-outlined text-[14px] text-text-muted shrink-0">
                      chevron_right
                    </span>
                    <span>{asset}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-3 border-t border-border-hairline flex items-start gap-2 text-[11px]">
              <span className="material-symbols-outlined text-[15px] text-agency-dgre shrink-0">
                route
              </span>
              <p className="text-on-surface-variant">
                <span className="font-semibold text-text-primary">
                  {detail.exposure.accessStatus}
                </span>{" "}
                — {detail.exposure.accessNote}
              </p>
            </div>
          </section>

          <section
            aria-labelledby="directives-title"
            className="bg-surface-card rounded-xl border border-border-hairline shadow-xs p-5"
          >
            <div className="flex items-center justify-between gap-2 pb-3 border-b border-border-hairline">
              <h3 id="directives-title" className="text-base font-bold text-text-primary">
                Active Authoritative Protocols
              </h3>
              <span className="text-[10px] font-semibold text-text-muted">
                {detail.directives.length} Mandates
              </span>
            </div>
            <ul className="divide-y divide-border-hairline">
              {detail.directives.map((directive) => {
                const style = DIRECTIVE_ICONS[directive.status];
                return (
                  <li key={directive.title} className="py-2.5 flex items-start gap-2.5">
                    <span className={`material-symbols-outlined text-[18px] shrink-0 mt-0.5 ${style.className}`}>
                      {style.icon}
                    </span>
                    <div className="flex flex-col">
                      <span className="text-xs font-semibold text-text-primary">
                        {directive.title}
                      </span>
                      <span className="text-[11px] text-text-muted">{directive.detail}</span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          <section
            aria-labelledby="sensors-title"
            className="bg-surface-card rounded-xl border border-border-hairline shadow-xs p-5"
          >
            <div className="flex items-center justify-between gap-2 pb-3 border-b border-border-hairline">
              <h3 id="sensors-title" className="text-base font-bold text-text-primary">
                Sensor Network Status
              </h3>
              <span className="text-[10px] font-semibold text-text-muted">
                Consensus {detail.consensusPercent}%
              </span>
            </div>
            <ul className="divide-y divide-border-hairline">
              {detail.sensors.map((sensor) => (
                <li
                  key={sensor.name}
                  className="py-2.5 flex flex-wrap items-center justify-between gap-2"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`w-2 h-2 rounded-full shrink-0 ${SENSOR_DOTS[sensor.status]}`}
                    />
                    <span className="text-xs font-medium text-text-primary truncate">
                      {sensor.name}
                    </span>
                    <Badge tone={AGENCY_BADGE[sensor.agency]}>{sensor.agency}</Badge>
                  </div>
                  <span className={`text-[11px] font-medium ${SENSOR_TEXT[sensor.status]}`}>
                    {sensor.detail}
                  </span>
                </li>
              ))}
            </ul>
            <div className="pt-3 border-t border-border-hairline flex flex-wrap items-center justify-between gap-2 text-[10px] text-text-muted">
              <span>Failover: IMD Synoptic Extrapolation</span>
              <Link
                to={`/field-log?sector=${encodeURIComponent(detail.sectorId)}`}
                className="font-semibold text-on-surface-variant underline underline-offset-2 hover:text-text-primary"
              >
                Manual Override
              </Link>
            </div>
          </section>
        </aside>
      </div>

      <footer className="rounded-xl bg-surface-card border border-border-hairline shadow-xs p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start sm:items-center gap-2.5 min-w-0">
          <Badge tone={AGENCY_BADGE[detail.bulletin.agency]} showDot>
            {detail.bulletin.agency} Bulletin
          </Badge>
          <p className="text-[11px] text-text-muted">
            <span className="font-semibold text-text-primary">{detail.bulletin.title}</span> •{" "}
            {detail.bulletin.detail}
          </p>
        </div>
        <Link
          to="/warnings"
          className="inline-flex items-center justify-center gap-1.5 h-9 px-4 rounded-full bg-primary-container text-on-primary text-[11px] font-semibold hover:bg-text-primary transition-colors shrink-0"
        >
          Review Warnings
          <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
        </Link>
      </footer>
    </div>
  );
}
