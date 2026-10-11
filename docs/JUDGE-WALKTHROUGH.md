# 90-second evidence-first walkthrough

Keep the existing source CSV and evaluation/results.json available. Run the official historical application in one terminal:

```powershell
.\scripts\start-local.ps1 -Port 8768
```

Optional separate SYNTHETIC demonstration (one historical evaluation window with recorded flatline injection; never an actual CGWB incident):

```powershell
.\.venv\Scripts\python.exe -m uvicorn scripts.synthetic_demo_app:app --host 127.0.0.1 --port 8770
```

- **0–15 seconds:** Open http://127.0.0.1:8768/. Explain historical CGWB/NWDP provenance and the five internal groups. Filter by name, evidence state or flagged pattern. Zero detected spikes is an honest result, not a reason to fabricate an incident.
- **15–35 seconds:** Select Ambhasi. Show actual readings, visible gaps and uncertain physical semantics. Selecting the earliest reading produces insufficient history; the current review can abstain.
- **35–55 seconds:** For a flag demonstration, explicitly switch to http://127.0.0.1:8770/ and name the SYNTHETIC label. The one-click “Start 90-second synthetic demo” button on the official Network opens this separate demo and selects its FLATLINE station. Click Inspect FLATLINE pattern. The selected timestamp and evidence agree.
- **55–75 seconds:** Open Inspect Selected Evidence. Explain supporting rows, missing independent evidence and conservative telemetry concern. Read the recommendation to compare logger and portal records; this is not a physical-failure diagnosis.
- **75–90 seconds:** Expand provenance, distinguish retrieval from observation time, and download the exact evidence JSON. Close: JalSanket turns an observation into a traceable next verification step, while retaining uncertainty.

## Verification scope

Backend: 55 tests pass. UI logic: six Node tests pass. Production frontend build and syntax checks pass. In-app browser checks exercised search/filter/reset, official selection, insufficient evidence, synthetic FLATLINE selection, provenance, exact exported JSON/API equality and mobile evidence layout. Standalone Playwright could not launch Chrome in the restricted Codex process (Crashpad/pipe error), so its suite is not called a pass. Run `npm run test:investigation` in an unrestricted terminal with the official server on 8769.

AWS SAM 1.168.0 validates and builds the existing aggregate Lambda handler locally. `scripts/verify-sam.ps1` checks the built artifact with a local S3 test double. The new observation-specific endpoint runs in FastAPI; the draft Lambda adapter does not implement it. No cloud deployment or AWS-resource change occurred. Docker-based Lambda runtime validation remains unperformed.

## Refined Evidence Trail

Summary → interactive timeline → observed signal → Supporting Evidence → assessment/uncertainty → Recommended Verification → three visible caveats, expandable remainder → provenance and Download evidence JSON. Timeline points and the accessible selector update the displayed evidence; export matches that selection. Both local servers above must be running for the one-click demo. No cloud service is required.

Refinement verification (2026-10-11): fresh in-app browser completed one-click synthetic entry, Station → selected FLATLINE Evidence, timeline selection → INSUFFICIENT_EVIDENCE, return to flagged evidence, recommendation focus, expansion of all remaining limitations, and JSON download. Three limitations are initially visible. Desktop (1440px) and mobile (390px) had no horizontal overflow. Screenshots are local ignored artifacts under `artifacts/refined-evidence-*.png`. Both local servers must remain running.
