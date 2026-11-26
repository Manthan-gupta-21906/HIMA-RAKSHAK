# GIS Layers & Spatial Fixtures Catalogue

This directory holds documented vector and raster metadata layers for the HIMA-RAKSHAK multi-hazard risk intelligence system.

## Project Coordinate Reference System (CRS)

All spatial vector datasets, geometries, and location points in HIMA-RAKSHAK are normalized to **WGS 84 (EPSG:4326)** longitude/latitude coordinates. Transformations from Web Mercator (EPSG:3857) are supported and automatically normalized upon layer ingestion.

## Layer Catalogue

### 1. `pilot_coverage_zones.geojson`
- **Layer ID:** `pilot_coverage_zones`
- **Name:** Himalayan Pilot Districts & Buffer Envelopes
- **Type:** Vector (`Polygon` / `FeatureCollection`)
- **Native CRS:** EPSG:4326 (WGS 84)
- **Target CRS:** EPSG:4326
- **Provenance:** `demo_fixture:pilot_catchment_corridors`
- **Status:** Synthetic demo fixture
- **Locations Included:**
  - `JK-SGR-01`: Srinagar / Jhelum Flood Basin envelope
  - `UK-JSH-01`: Joshimath / Alaknanda Catchment envelope
  - `LA-DRS-01`: Drass / High-Altitude Avalanche Basin envelope
- **Usage:** Used by `GeospatialService` and spatial join pipelines to assign environmental observations and field sensor points to monitored risk hubs.

### 2. Digital Elevation & Catchment Rasters (Documented Metadata)
- **DEM Source:** SRTM 30m / Copernicus DEM 30m (Himalayan Corridor coverage)
- **Drainage & River Basins:** CWC Hydro-basin level 6 polygons
- **Access Mode:** Sample / Cached metadata (offline demo mode)
