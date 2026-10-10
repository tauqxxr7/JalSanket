"""Exercise SAM-built handler with real exported evidence and a local S3 test double."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("sam_built_handler",root/".aws-sam/build/EvidenceApi/handler.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert (root/"infrastructure/handler.py").read_bytes()==Path(spec.origin).read_bytes()
def local_read(key):
    return json.loads((root/"dist-cloud/data"/key).read_text())
module.load_json=local_read  # Explicit local test double, not an S3 request.
network=local_read("network.json")
key=network["stations"][0]["station_group_key"]
for path,status in [("/api/network",200),(f"/api/stations/{key}",200),(f"/api/stations/{key}/evidence",200),("/api/invalid",404)]:
    response=module.handler({"rawPath":path,"requestContext":{"http":{"method":"GET"}}},SimpleNamespace(aws_request_id="local-sam-artifact-check"))
    assert response["statusCode"]==status
    if path.endswith("/evidence"):
        body=json.loads(response["body"])
        assert body["provenance"]["data_mode"]=="OFFICIAL_HISTORICAL"
        assert body["next_check"]["action"]
print("PASS: SAM-built handler, 3 real-data API routes + 404; local S3 test double. No Lambda runtime or cloud deployment claimed.")
