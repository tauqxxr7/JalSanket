# JalSanket — Evidence Trail

**Heat & Water · Environmental Hacks · working local prototype**

Groundwater readings need investigation context: telemetry alone cannot reliably distinguish acquisition problems from genuine groundwater movement. JalSanket connects Network → Station → Evidence → Recommended Verification, preserving uncertainty instead of forcing a diagnosis.

## Architecture and differentiation

CGWB/NWDP CSV → checksum-verified provider → Pydantic validation → quality and eligibility → deterministic SPIKE/FLATLINE/DROPOUT → EvidencePackage → FastAPI → static HTML/CSS/JS.

Search, filters, interactive timeline, supporting/contradicting/missing evidence, conservative four-state triage, provenance and exact JSON export make each next check traceable. Five internal groupings are not official station IDs. Original measurement/time tokens remain intact; datum, sign interpretation and timezone remain unverified. Data is historical, not live. See [manifest](../data/manifest.json) and [attribution](ATTRIBUTIONS.md).

## Actual AWS use

AWS SAM CLI 1.168.0 locally validates the template and packages the draft aggregate Lambda handler. `scripts/verify-sam.ps1` checks three real-data routes plus 404 using exported evidence and an explicit local S3 test double. This is local AWS open-source tooling, not cloud deployment, S3 access proof or Docker runtime emulation. No S3 upload or public hosting is verified. The draft handler lacks the refined per-observation endpoint. Organizer acceptance for prize eligibility remains an owner confirmation.

## Demonstration

From the repository root, keep two PowerShell terminals open:

```powershell
.\scripts\start-local.ps1 -Port 8768
```

```powershell
.\.venv\Scripts\python.exe -m uvicorn scripts.synthetic_demo_app:app --host 127.0.0.1 --port 8770
```

Open http://127.0.0.1:8768/. Inspect official uncertainty, then click **Start 90-second synthetic demo**. Inspect FLATLINE → selected Evidence → uncertainty → Recommended Verification → JSON export. Installation/source acquisition: [README](../README.md). [Storyboard](VIDEO-STORYBOARD.md).

## Testing and limitations

October 11: 55 backend tests, six frontend tests, syntax and production build passed. In-app checks exercised official/synthetic journeys, mobile layout and exact JSON/API equality. Standalone Playwright remains blocked by browser-process startup restrictions. SAM lint/build/artifact checks passed locally.

Recorded controlled evaluation: 150 cases across 25 Q2 windows. SPIKE/FLATLINE/DROPOUT F1: 0.649/0.611/1.000; recall: 0.48/0.44/1.00. Full modifications and configuration: [results](../evaluation/results.json). This evaluates detection of controlled synthetic anomaly patterns. It does not establish accuracy for diagnosing real physical sensor failures.

Official FLATLINE/DROPOUT remain unavailable without required verified metadata; all five official assessments are UNCERTAIN. No forecasting, chatbot, maps or Bedrock.

Repository: https://github.com/tauqxxr7/JalSanket — owner must push release commits. Video: not supplied. Public deployment: none verified. [AI disclosure](AI_USAGE.md) · [Verification](VERIFICATION.md).
