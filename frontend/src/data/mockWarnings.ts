import type { OfficialWarning } from "../types/warning";

/** Sample cached authoritative bulletins for Jammu & Kashmir (read-only). */
export const MOCK_WARNINGS: OfficialWarning[] = [
  {
    id: "WARN-CWC-2026-104",
    bulletinCode: "CWC-JK-FLOOD-104",
    agency: "CWC",
    agencyFullName: "Central Water Commission",
    title: "Flash Flood Watch — Poonch & Surankote Tributaries",
    hazard: "flood",
    severity: "Red",
    affectedSectors: ["JK-PN-04", "Poonch - Surankote"],
    district: "Poonch",
    issuedAt: "2026-11-25 00:15 IST",
    validUntil: "2026-11-25 18:00 IST",
    summary:
      "Rapid rise observed on Surankote nallah and Poonch river gauge (17.80 ft vs 18.0 ft alert mark) following 68 mm rainfall in 6 hours.",
    advisoryNotes:
      "Authoritative CWC hydrological bulletin. Maintain continuous gauge watch along low-lying Surankote bridges and approach roads.",
    sourceReference: "CWC Northern Rivers Bulletin (Sample Cached Record)",
    isReadOnly: true,
  },
  {
    id: "WARN-DGRE-2026-038",
    bulletinCode: "DGRE-AVAL-038",
    agency: "DGRE",
    agencyFullName: "Defence Geoinformatics Research Establishment",
    title: "Stage-3 Avalanche Warning — Gulmarg & Affarwat Ridge",
    hazard: "avalanche",
    severity: "Orange",
    affectedSectors: ["JK-BM-12", "Gulmarg - Affarwat"],
    district: "Baramulla",
    issuedAt: "2026-11-24 21:00 IST",
    validUntil: "2026-11-25 21:00 IST",
    summary:
      "Medium-sized natural and triggered avalanches likely on steep slopes above 3,000 m following 45 cm fresh snowfall and 60 km/h NW winds.",
    advisoryNotes:
      "Authoritative DGRE avalanche bulletin. Restrict movement on wind-loaded slopes >35 degrees; follow local DDMA/Army clearance advisories.",
    sourceReference: "DGRE Chandigarh Avalanche Bulletin (Sample Cached Record)",
    isReadOnly: true,
  },
  {
    id: "WARN-IMD-2026-219",
    bulletinCode: "IMD-SRN-219",
    agency: "IMD",
    agencyFullName: "India Meteorological Department",
    title: "Heavy Precipitation & Snowfall Advisory — North Kashmir",
    hazard: "weather",
    severity: "Orange",
    affectedSectors: ["JK-KP-08", "JK-BD-09", "Kupwara - Machil", "Bandipora - Gurez"],
    district: "Kupwara & Bandipora",
    issuedAt: "2026-11-24 19:30 IST",
    validUntil: "2026-11-25 19:30 IST",
    summary:
      "Active Western Disturbance bringing moderate-to-heavy snowfall over higher reaches (Machil, Razdan Pass) and rain over valley floors.",
    advisoryNotes:
      "Authoritative IMD Meteorological Centre Srinagar bulletin. Expect reduced visibility and slippery mountain pass conditions.",
    sourceReference: "IMD MC Srinagar Nowcast/Bulletin (Sample Cached Record)",
    isReadOnly: true,
  },
  {
    id: "WARN-CWC-2026-099",
    bulletinCode: "CWC-JK-JHELUM-099",
    agency: "CWC",
    agencyFullName: "Central Water Commission",
    title: "Jhelum Basin Monitoring — Sangam & Ram Munshi Bagh",
    hazard: "flood",
    severity: "Yellow",
    affectedSectors: ["JK-AN-02", "Anantnag - Sangam Gauge"],
    district: "Anantnag",
    issuedAt: "2026-11-24 18:00 IST",
    validUntil: "2026-11-25 12:00 IST",
    summary:
      "River Jhelum at Sangam gauge holding steady at 16.4 ft. Catchment runoff remains elevated due to persistent valley rainfall.",
    advisoryNotes:
      "Authoritative CWC basin watch. Routine 3-hourly gauge reporting in effect; no flood-level breach at Sangam.",
    sourceReference: "CWC Jhelum Basin Desk (Sample Cached Record)",
    isReadOnly: true,
  },
];
