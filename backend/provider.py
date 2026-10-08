"""Bounded, pinned CSV provider with immutable raw-byte custody."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Protocol

from .models import Observation, Provenance, Station

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = "2da4e849-2249-4e15-a609-a6166e30a300"
SOURCE = f"https://nwdp.nwic.gov.in/dataset/3782ba15-9b12-46a8-ae44-410b1f84020e/resource/{RESOURCE}/download/gwl_tel_6_hourly_cgwb_mh_2021_2025.csv"
RESOURCE_URL = f"https://www.nwdp.nwic.gov.in/en/dataset/ground-water-level-telemetry-daily-cgwb-as-assam/resource/{RESOURCE}"
TERMS = "https://www.nwdp.nwic.gov.in/en/footer/copyrightPolicy"
MEASUREMENT = "Groundwater Level Telemetry 6 Hourly (meter)"
GROUP_FIELDS = ["Station", "Agency", "State", "District", "Latitude", "Longitude"]
COHORT = {"Ambhasi", "Baigaon Budruk", "Bharosa_1", "Bhosa_2", "Bhokardan"}
START, END = datetime(2024, 1, 1), datetime(2024, 4, 1)


class SourceUnavailable(Exception):
    """No trustworthy local snapshot is available."""


class Provider(Protocol):
    def load(self) -> tuple[Provenance, dict[str, Station], dict[str, list[Observation]]]: ...


def parse_row(row: dict, row_number: int, snapshot_id: str) -> tuple[Station, Observation]:
    basis = {key: row[key] for key in GROUP_FIELDS}
    group_key = "group-" + hashlib.sha256(json.dumps(basis, sort_keys=True).encode()).hexdigest()[:16]
    station = Station(station_group_key=group_key, label=row["Station"], district=row["District"], agency=row["Agency"], state=row["State"], grouping_basis=basis)
    raw, stamp, issues = row[MEASUREMENT], row["Data Acquisition Time"], []
    try:
        value = float(raw)
        if not math.isfinite(value):
            value = None
            issues.append("NONFINITE_NUMERIC")
    except (ValueError, TypeError):
        value = None
        issues.append("MISSING_NUMERIC" if not raw.strip() else "UNPARSEABLE_NUMERIC")
    try:
        time = datetime.strptime(stamp, "%d-%m-%Y %H:%M")
    except (ValueError, TypeError):
        time = None
        issues.append("UNPARSEABLE_TIMESTAMP")
    return station, Observation(observation_id=f"{snapshot_id}:row:{row_number}", station_group_key=group_key, source_row=row_number, snapshot_id=snapshot_id, measurement_raw=raw, raw_timestamp=stamp, raw_numeric_value=value, source_time=time, issues=issues)


class CSVProvider:
    def __init__(self, data_dir: Path = ROOT / "data"):
        self.data_dir = data_dir

    def load(self):
        path = self.data_dir / "raw" / "official.csv"
        try:
            manifest = Provenance.model_validate_json((self.data_dir / "manifest.json").read_text(encoding="utf-8"))
            with path.open("rb") as raw:
                digest = hashlib.file_digest(raw, "sha256").hexdigest()
            if digest != manifest.sha256 or path.stat().st_size != manifest.byte_count:
                raise SourceUnavailable("Snapshot checksum or size mismatch; reacquire official data.")
            stations, rows = {}, defaultdict(list)
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                required = set(GROUP_FIELDS + [MEASUREMENT, "Data Acquisition Time"])
                if not required.issubset(reader.fieldnames or []):
                    raise SourceUnavailable("Official CSV schema changed; adapter review required.")
                for line, row in enumerate(reader, 2):
                    if row["Station"] not in COHORT:
                        continue
                    station, observation = parse_row(row, line, manifest.snapshot_id)
                    # Keep unparseable selected-station rows for quality accounting.
                    if observation.source_time is None or START <= observation.source_time < END:
                        stations[station.station_group_key] = station
                        rows[station.station_group_key].append(observation)
            if not rows:
                raise SourceUnavailable("No selected cohort observations in the configured window.")
            return manifest, stations, dict(rows)
        except SourceUnavailable:
            raise
        except (OSError, ValueError, KeyError, TypeError, csv.Error) as error:
            raise SourceUnavailable("Official snapshot missing or invalid; run acquisition.") from error
