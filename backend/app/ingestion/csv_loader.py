"""CSV loader for environmental observations."""

import csv
import io
from pathlib import Path

from pydantic import BaseModel, ValidationError

from app.ingestion.column_mapping import (
    ColumnMapping,
    compute_idempotency_key,
    normalize_unit_and_value,
    parse_aware_timestamp,
)
from app.schemas.observation import ObservationContract, ObservationMetric


class CsvRowError(BaseModel):
    """Validation or parsing error captured for a single CSV row."""

    row_number: int
    message: str


class ParsedCsvResult(BaseModel):
    """Outcome of parsing and validating a CSV batch."""

    total_rows: int
    valid: list[ObservationContract]
    errors: list[CsvRowError]


def load_observations_from_csv(
    csv_source: str | Path,
    source_id: str,
    mapping: ColumnMapping | None = None,
    is_demo_fixture: bool = True,
) -> ParsedCsvResult:
    """Parse a CSV string or file path into validated ObservationContract items."""
    col = mapping or ColumnMapping()
    if isinstance(csv_source, Path):
        text = csv_source.read_text(encoding="utf-8")
    else:
        text = csv_source

    reader = csv.DictReader(io.StringIO(text))
    valid: list[ObservationContract] = []
    errors: list[CsvRowError] = []
    total_rows = 0

    for idx, row in enumerate(reader, start=2):
        total_rows += 1
        try:
            location_id = (row.get(col.location_id) or "").strip()
            raw_ts = row.get(col.observed_at) or ""
            raw_metric = (row.get(col.metric) or "").strip()
            raw_val_str = (row.get(col.value) or "").strip()
            raw_unit = (row.get(col.unit) or "").strip()

            observed_at = parse_aware_timestamp(raw_ts)
            metric = ObservationMetric(raw_metric)
            raw_val = float(raw_val_str)
            norm_val, norm_unit = normalize_unit_and_value(metric, raw_val, raw_unit)

            obs_id = (
                (row.get(col.observation_id) or "").strip()
                if col.observation_id
                else ""
            )
            if not obs_id:
                obs_id = compute_idempotency_key(
                    location_id, source_id, observed_at, metric.value
                )[:24]

            contract = ObservationContract(
                observation_id=obs_id,
                location_id=location_id,
                source_id=source_id,
                observed_at=observed_at,
                metric=metric,
                value=norm_val,
                unit=norm_unit,
                is_demo_fixture=is_demo_fixture,
            )
            valid.append(contract)
        except (ValueError, KeyError, ValidationError) as exc:
            errors.append(CsvRowError(row_number=idx, message=str(exc)))

    return ParsedCsvResult(total_rows=total_rows, valid=valid, errors=errors)
