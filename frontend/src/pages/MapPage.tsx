import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLocations } from "../api/locations";
import { mapLocationAndRiskToSector } from "../api/mappers";
import { fetchLocationRiskState } from "../api/risk";
import { HazardMap } from "../components/map/HazardMap";
import { Badge } from "../components/ui/Badge";
import { MOCK_SECTORS, type HazardPathway, type MonitoringSector } from "../data/mockSectors";

type HazardFilter = "all" | HazardPathway;

/** Interactive multi-hazard map screen connected to backend location & risk APIs. */
export function MapPage() {
  const [sectors, setSectors] = useState<MonitoringSector[]>(MOCK_SECTORS);
  const [hazardFilter, setHazardFilter] = useState<HazardFilter>("all");
  const [staleOnly, setStaleOnly] = useState(false);
  const [selectedSector, setSelectedSector] = useState<MonitoringSector>(MOCK_SECTORS[0]);
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadMapData() {
      try {
        const locResponse = await fetchLocations();
        if (!isMounted) return;

        if (locResponse && Array.isArray(locResponse.items) && locResponse.items.length > 0) {
          // Filter locations with valid coordinates
          const validLocs = locResponse.items.filter(
            (loc) => typeof loc.latitude === "number" && typeof loc.longitude === "number"
          );

          const liveSectors = await Promise.all(
            validLocs.map(async (loc) => {
              try {
                const riskState = await fetchLocationRiskState(loc.location_id);
                return mapLocationAndRiskToSector(loc, riskState);
              } catch {
                return mapLocationAndRiskToSector(loc, null);
              }
            })
          );

          if (isMounted) {
            setSectors(liveSectors);
            setIsLive(true);
            if (liveSectors.length > 0) {
              setSelectedSector(liveSectors[0]);
            }
          }
        }
      } catch (err) {
        if (isMounted) {
          setError((err as Error).message || "Could not load backend map locations");
        }
      }
    }

    loadMapData();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredSectors = useMemo(() => {
    return sectors.filter((sector) => {
      if (hazardFilter !== "all" && sector.hazard !== hazardFilter) return false;
      if (staleOnly && !sector.isStale) return false;
      return true;
    });
  }, [sectors, hazardFilter, staleOnly]);

  const activeSector =
    filteredSectors.find((s) => s.id === selectedSector.id) ?? filteredSectors[0] ?? null;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border-hairline">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-text-muted">
            Spatial Risk Layer • {isLive ? "Live Backend Telemetry" : "Sample Telemetry"}
          </span>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight mt-0.5">
            Multi-Hazard Risk Map
          </h1>
          <p className="text-xs sm:text-sm text-secondary mt-0.5">
            Separate flood and avalanche monitoring markers across Jammu &amp; Kashmir sectors.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              { value: "all", label: "All Pathways" },
              { value: "flood", label: "Flood Pathway" },
              { value: "avalanche", label: "Avalanche Pathway" },
            ] as const
          ).map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setHazardFilter(opt.value)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
                hazardFilter === opt.value
                  ? "bg-primary-container text-on-primary"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
              }`}
            >
              {opt.label}
            </button>
          ))}

          <button
            type="button"
            onClick={() => setStaleOnly((prev) => !prev)}
            className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-colors cursor-pointer ${
              staleOnly
                ? "bg-hazard-yellow text-primary-container border-primary-container"
                : "bg-surface-card text-on-surface-variant border-border-hairline hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined text-[15px]">schedule</span>
            <span>Stale Only</span>
          </button>
        </div>
      </div>

      {error && !isLive && (
        <div
          role="alert"
          className="p-3 rounded-lg bg-surface-card border border-border-hairline text-xs text-text-muted flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-[18px] text-amber-500">info</span>
          <span>Backend spatial API unavailable ({error}). Displaying baseline cached sectors.</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        <div className="lg:col-span-8 flex flex-col gap-3">
          <HazardMap
            sectors={filteredSectors}
            selectedSectorId={activeSector?.id ?? null}
            onSelectSector={setSelectedSector}
          />

          <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-surface-card border border-border-hairline text-xs">
            <div className="flex flex-wrap items-center gap-4">
              <span className="inline-flex items-center gap-1.5 font-medium text-text-primary">
                <span className="w-2.5 h-2.5 rounded-full bg-emergency-red" />
                Flood Pathway
              </span>
              <span className="inline-flex items-center gap-1.5 font-medium text-text-primary">
                <span className="w-2.5 h-2.5 rounded-full bg-agency-dgre" />
                Avalanche Pathway
              </span>
              <span className="inline-flex items-center gap-1.5 font-medium text-text-muted">
                <span className="w-2.5 h-2.5 rounded-full bg-text-muted" />
                Stale / Offline Telemetry
              </span>
            </div>
            <span className="text-[11px] text-text-muted">
              Showing {filteredSectors.length} of {sectors.length} sectors
            </span>
          </div>
        </div>

        <aside className="lg:col-span-4 flex flex-col gap-4">
          {activeSector ? (
            <div className="bg-surface-card border border-border-hairline rounded-xl p-5 flex flex-col gap-3 shadow-xs">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                    {activeSector.id} • {activeSector.elevationM}m
                  </span>
                  <h2 className="text-base font-bold text-text-primary mt-0.5">
                    {activeSector.name}
                  </h2>
                </div>
                <Badge tone={activeSector.isStale ? "warning" : "neutral"}>
                  {activeSector.updatedAgo}
                </Badge>
              </div>

              <div className="flex flex-wrap gap-1.5">
                <Badge tone={activeSector.hazard === "flood" ? "emergency" : "dgre"}>
                  {activeSector.threatLabel}
                </Badge>
                <Badge tone="neutral">{activeSector.riskTier}</Badge>
              </div>

              <p className="text-xs text-secondary">{activeSector.summaryMetric}</p>
              <p className="text-xs text-text-muted border-t border-border-hairline pt-2">
                {activeSector.exposureSummary}
              </p>

              <div className="flex items-center gap-2 pt-1">
                <Link
                  to={`/locations/${activeSector.id}`}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 h-9 px-3 rounded-full bg-primary-container text-on-primary text-xs font-semibold"
                >
                  <span>Inspect Sector</span>
                  <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                </Link>
                <Link
                  to={`/field-log?sector=${activeSector.id}&hazard=${activeSector.hazard}`}
                  className="inline-flex items-center justify-center h-9 px-3 rounded-full bg-surface-container hover:bg-surface-container-high text-text-primary text-xs font-semibold"
                >
                  Field Log
                </Link>
              </div>
            </div>
          ) : (
            <div className="bg-surface-card border border-border-hairline rounded-xl p-5 text-xs text-text-muted">
              No sectors match the selected filters.
            </div>
          )}

          <div className="bg-surface-card border border-border-hairline rounded-xl p-4 flex flex-col gap-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted">
              Sectors ({filteredSectors.length})
            </h3>
            <div className="flex flex-col gap-1.5">
              {filteredSectors.map((sector) => {
                const isSelected = activeSector?.id === sector.id;
                return (
                  <button
                    key={sector.id}
                    type="button"
                    onClick={() => setSelectedSector(sector)}
                    className={`w-full text-left p-2.5 rounded-lg border transition-colors cursor-pointer flex items-center justify-between gap-2 ${
                      isSelected
                        ? "bg-surface-subtle border-primary-container"
                        : "bg-surface-container-low/50 border-border-hairline hover:bg-surface-container"
                    }`}
                  >
                    <div>
                      <p className="text-xs font-semibold text-text-primary">{sector.name}</p>
                      <p className="text-[11px] text-text-muted">
                        {sector.district} • {sector.riskTier}
                      </p>
                    </div>
                    <span
                      className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                        sector.isStale
                          ? "bg-text-muted"
                          : sector.hazard === "flood"
                            ? "bg-emergency-red"
                            : "bg-agency-dgre"
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
