# Demo Observation Fixtures — Provenance & Licensing

> **Important:** Files in `data/fixtures/` are **synthetic demo fixtures** created for local development, automated testing, and offline hackathon demonstrations. They do **not** represent live feeds from IMD, CWC, DGRE, or ISRO.

## Files

### `sample_observations.csv`
- **Provenance:** Synthetic demo fixture (`is_demo_fixture = true`, `access_mode = sample`)
- **Licence:** CC-BY-4.0 (Synthetic Demo Data — HIMA-RAKSHAK Team 12)
- **Locations referenced:**
  - `JK-SGR-01` (Srinagar — Jhelum Floodplain)
  - `UK-JSH-01` (Joshimath — Alaknanda Slope & Valley)
  - `LA-DRS-01` (Drass — High-Altitude Snow Corridor)
- **Metrics included:** `rain_mm`, `river_level_m`, `snow_depth_cm`, `wind_kmh`, `temp_c`
- **Timestamps:** Timezone-aware ISO-8601 UTC timestamps (`+00:00` / `Z`).
