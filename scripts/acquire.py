"""Operator-only official resource acquisition; never accepts user-provided URLs."""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.models import Provenance
from backend.provider import ROOT, RESOURCE, SOURCE, RESOURCE_URL, TERMS


def main():
    destination = ROOT / "data" / "raw"
    destination.mkdir(parents=True, exist_ok=True)
    temporary = destination / "official.csv.part"
    digest, size = hashlib.sha256(), 0
    with urlopen(Request(SOURCE, headers={"User-Agent": "JalSanket/0.1 research prototype"}), timeout=90) as response:
        if response.status != 200:
            raise RuntimeError("Full HTTP 200 resource required; partial bytes are not a snapshot")
        expected = response.headers.get("Content-Length")
        with temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > 100 * 1024 * 1024:
                    raise RuntimeError("Resource exceeds reviewed 100 MiB acquisition bound")
                digest.update(chunk)
                output.write(chunk)
    if expected and size != int(expected):
        raise RuntimeError("Truncated resource; expected Content-Length not met")
    manifest = Provenance(snapshot_id="nwdp-" + digest.hexdigest()[:16], resource_id=RESOURCE, source_url=SOURCE, resource_url=RESOURCE_URL, retrieved_at_utc=datetime.now(timezone.utc), sha256=digest.hexdigest(), byte_count=size, full_file=True, terms_url=TERMS, transformations=["Raw CSV preserved byte-for-byte; finite numeric parsing without sign conversion", "Source clock parsed without timezone conversion", "Five feasibility-selected labels, 2024-01-01 inclusive to 2024-04-01 exclusive", "Station grouping uses exact label, agency, state, district and coordinate tokens"], exclusions=["Other stations and out-of-window timestamps excluded from this bounded pilot", "Malformed selected-station timestamps retained for quality audit, cannot be assigned to window", "Conflicting duplicate timestamp values withheld from analytics", "Q1 2024 was inspected before the event; not an untouched evaluation holdout"])
    os.replace(temporary, destination / "official.csv")
    (ROOT / "data" / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    print(json.dumps({"snapshot_id": manifest.snapshot_id, "byte_count": size, "sha256": digest.hexdigest(), "retrieved_at_utc": manifest.retrieved_at_utc.isoformat()}))


if __name__ == "__main__":
    main()
