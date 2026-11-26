import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { MonitoringSector } from "../../data/mockSectors";

const JK_CENTER: [number, number] = [34.12, 74.65];
const JK_DEFAULT_ZOOM = 8;

type BaseLayerId = "standard" | "terrain";

const BASE_LAYERS: Record<
  BaseLayerId,
  { label: string; icon: string; url: string; attribution: string; maxZoom: number }
> = {
  standard: {
    label: "Standard",
    icon: "map",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
  },
  terrain: {
    label: "Terrain",
    icon: "terrain",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: "Tiles &copy; Esri — Esri, DeLorme, NAVTEQ",
    maxZoom: 18,
  },
};

interface HazardMapProps {
  sectors: MonitoringSector[];
  selectedSectorId: string | null;
  onSelectSector: (sector: MonitoringSector) => void;
}

function getMarkerColor(sector: MonitoringSector): string {
  if (sector.isStale) return "#7e765d";
  return sector.hazard === "flood" ? "#f4472c" : "#c48022";
}

function buildMarkerIcon(sector: MonitoringSector): L.DivIcon {
  const color = getMarkerColor(sector);

  return L.divIcon({
    className: "hima-sector-pin",
    html: `<span style="display:block;width:14px;height:14px;border-radius:9999px;background:${color};border:2px solid #ffffff;box-shadow:0 2px 6px rgba(0,0,0,0.35);transition:width 120ms ease,height 120ms ease,border-color 120ms ease;"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

/** Updates the pin's inner dot in place so an open popup is never destroyed. */
function applyMarkerSelection(
  marker: L.Marker,
  sector: MonitoringSector,
  isSelected: boolean
): void {
  const dot = marker.getElement()?.querySelector<HTMLElement>("span");
  if (!dot) return;

  const size = isSelected ? 20 : 14;
  dot.style.width = `${size}px`;
  dot.style.height = `${size}px`;
  dot.style.background = getMarkerColor(sector);
  dot.style.border = isSelected ? "3px solid #1c1a15" : "2px solid #ffffff";
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function buildPopupHtml(sector: MonitoringSector): string {
  return `
    <div style="font-family:Inter,system-ui,sans-serif;min-width:190px">
      <div style="font-size:10px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#7e765d">
        ${escapeHtml(sector.id)} • ${sector.elevationM}m
      </div>
      <div style="font-size:13px;font-weight:700;color:#0e1414;margin-top:2px">
        ${escapeHtml(sector.name)}
      </div>
      <div style="font-size:11px;font-weight:600;color:#4a463f;margin-top:4px">
        ${escapeHtml(sector.threatLabel)} (${escapeHtml(sector.riskTier)})
      </div>
      <div style="font-size:11px;color:#7e765d;margin-top:4px">
        ${escapeHtml(sector.summaryMetric)}
      </div>
      <a
        data-inspect-sector
        href="/locations/${encodeURIComponent(sector.id)}"
        style="display:inline-flex;align-items:center;gap:4px;margin-top:8px;padding:5px 11px;border-radius:9999px;background:#1d1b16;color:#ffffff;font-size:11px;font-weight:600;text-decoration:none"
      >
        View Details →
      </a>
    </div>
  `;
}

/** Interactive Leaflet map displaying J&K monitoring sectors with severity-coded markers. */
export function HazardMap({ sectors, selectedSectorId, onSelectSector }: HazardMapProps) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const markersByIdRef = useRef<Map<string, L.Marker>>(new Map());
  const onSelectSectorRef = useRef(onSelectSector);
  const [baseLayer, setBaseLayer] = useState<BaseLayerId>("standard");

  useEffect(() => {
    onSelectSectorRef.current = onSelectSector;
  }, [onSelectSector]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: JK_CENTER,
      zoom: JK_DEFAULT_ZOOM,
      zoomControl: true,
    });

    markersLayerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      tileLayerRef.current = null;
      markersLayerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }

    const config = BASE_LAYERS[baseLayer];
    tileLayerRef.current = L.tileLayer(config.url, {
      attribution: config.attribution,
      maxZoom: config.maxZoom,
    }).addTo(map);
  }, [baseLayer]);

  useEffect(() => {
    const layer = markersLayerRef.current;
    if (!layer) return;

    layer.clearLayers();
    markersByIdRef.current.clear();

    sectors.forEach((sector) => {
      const marker = L.marker([sector.lat, sector.lng], {
        icon: buildMarkerIcon(sector),
      });
      marker.bindPopup(buildPopupHtml(sector));
      marker.on("click", () => onSelectSectorRef.current(sector));
      marker.on("popupopen", (event) => {
        const link = event.popup
          .getElement()
          ?.querySelector<HTMLAnchorElement>("[data-inspect-sector]");
        if (!link || link.dataset.bound === "true") return;
        link.dataset.bound = "true";
        link.addEventListener("click", (clickEvent) => {
          clickEvent.preventDefault();
          navigate(`/locations/${sector.id}`);
        });
      });
      markersByIdRef.current.set(sector.id, marker);
      marker.addTo(layer);
    });
  }, [sectors, navigate]);

  useEffect(() => {
    sectors.forEach((sector) => {
      const marker = markersByIdRef.current.get(sector.id);
      if (!marker) return;
      applyMarkerSelection(marker, sector, sector.id === selectedSectorId);
    });
  }, [sectors, selectedSectorId]);

  const handleResetView = () => {
    mapRef.current?.setView(JK_CENTER, JK_DEFAULT_ZOOM);
  };

  return (
    <div className="relative w-full h-[460px] lg:h-[560px] rounded-xl overflow-hidden border border-border-hairline bg-surface-container-low">
      <div ref={containerRef} className="w-full h-full z-0" aria-label="Jammu and Kashmir hazard map" />

      <div className="absolute top-3 right-3 z-[400] flex flex-col items-end gap-2">
        <div
          role="group"
          aria-label="Base map layer"
          className="inline-flex items-center gap-0.5 rounded-full bg-surface-card border border-border-hairline shadow-sm p-0.5"
        >
          {(Object.keys(BASE_LAYERS) as BaseLayerId[]).map((layerId) => {
            const config = BASE_LAYERS[layerId];
            const isActive = baseLayer === layerId;
            return (
              <button
                key={layerId}
                type="button"
                aria-pressed={isActive}
                onClick={() => setBaseLayer(layerId)}
                className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-full text-[11px] font-semibold transition-colors cursor-pointer ${
                  isActive
                    ? "bg-primary-container text-on-primary"
                    : "text-on-surface-variant hover:bg-surface-container"
                }`}
              >
                <span className="material-symbols-outlined text-[14px]">{config.icon}</span>
                <span>{config.label}</span>
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={handleResetView}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-card border border-border-hairline shadow-sm text-xs font-semibold text-text-primary hover:bg-surface-container cursor-pointer"
        >
          <span className="material-symbols-outlined text-[15px]">my_location</span>
          <span>Reset J&amp;K View</span>
        </button>
      </div>
    </div>
  );
}
