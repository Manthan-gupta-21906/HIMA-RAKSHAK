import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { MonitoringSector } from "../../data/mockSectors";

const JK_CENTER: [number, number] = [34.12, 74.65];
const JK_DEFAULT_ZOOM = 8;

interface HazardMapProps {
  sectors: MonitoringSector[];
  selectedSectorId: string | null;
  onSelectSector: (sector: MonitoringSector) => void;
}

function getMarkerColor(sector: MonitoringSector): string {
  if (sector.isStale) return "#7e765d";
  return sector.hazard === "flood" ? "#f4472c" : "#c48022";
}

/** Interactive Leaflet map displaying J&K monitoring sectors with severity-coded markers. */
export function HazardMap({ sectors, selectedSectorId, onSelectSector }: HazardMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: JK_CENTER,
      zoom: JK_DEFAULT_ZOOM,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(map);

    markersLayerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      markersLayerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const layer = markersLayerRef.current;
    if (!layer) return;

    layer.clearLayers();
    sectors.forEach((sector) => {
      const isSelected = sector.id === selectedSectorId;
      const color = getMarkerColor(sector);
      const size = isSelected ? 20 : 14;

      const icon = L.divIcon({
        className: "hima-sector-pin",
        html: `<span style="display:block;width:${size}px;height:${size}px;border-radius:9999px;background:${color};border:${isSelected ? "3px solid #1c1a15" : "2px solid #ffffff"};box-shadow:0 2px 6px rgba(0,0,0,0.35);"></span>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
      });

      const marker = L.marker([sector.lat, sector.lng], { icon });
      marker.bindPopup(
        `<strong>${sector.name}</strong><br/><span>${sector.threatLabel} (${sector.riskTier})</span><br/><small>${sector.summaryMetric}</small>`
      );
      marker.on("click", () => onSelectSector(sector));
      marker.addTo(layer);
    });
  }, [sectors, selectedSectorId, onSelectSector]);

  const handleResetView = () => {
    mapRef.current?.setView(JK_CENTER, JK_DEFAULT_ZOOM);
  };

  return (
    <div className="relative w-full h-[460px] lg:h-[560px] rounded-xl overflow-hidden border border-border-hairline bg-surface-container-low">
      <div ref={containerRef} className="w-full h-full z-0" aria-label="Jammu and Kashmir hazard map" />
      <button
        type="button"
        onClick={handleResetView}
        className="absolute top-3 right-3 z-[400] inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-card border border-border-hairline shadow-sm text-xs font-semibold text-text-primary hover:bg-surface-container cursor-pointer"
      >
        <span className="material-symbols-outlined text-[15px]">my_location</span>
        <span>Reset J&amp;K View</span>
      </button>
    </div>
  );
}
