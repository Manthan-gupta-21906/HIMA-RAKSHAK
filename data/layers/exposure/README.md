# Exposure Layers Documentation

## Overview
The Exposure & Vulnerability layer intersects hazard zones with geospatial assets to assess human and infrastructural impact without altering the hazard models' physical output.

## Layers & Attributes
1. **Settlements & Population (`settlements.geojson` / GIS catalogue)**:
   - Tracks villages, administrative headquarters, and approximate populations.
   - Values are explicitly tagged as `estimated` or `verified`.

2. **Residential Structures (`homes.geojson` / Building footprints)**:
   - Approximate residential dwelling counts located within steep slope or riverbank buffer zones.

3. **Roads & Transportation Arteries (`roads.geojson`)**:
   - Critical national highways (e.g., NH-3, NH-5), arterial passes, and local link roads (km exposed).

4. **Critical Infrastructure & Services (`critical_facilities.geojson`)**:
   - Hospitals, primary health centres (PHCs), electrical substations, telecom towers, and civil defense shelters.

## Data Coverage Status
- **`complete`**: All 4 asset layers are present and fresh for the pilot area.
- **`partial`**: One or more layers are unavailable (e.g., road network present but residential footprints missing).
- **`unknown`**: No verified asset layer exists; fallback estimation or zero counts are used.
