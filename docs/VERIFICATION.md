# Current release verification — October 11, 2026

This section supersedes all older counts, Git/AWS status and blockers below. Older sections are retained only as a dated audit history.

| Check | Result and scope |
|---|---|
| Backend | PASS: 55 tests in 5.80s; one Starlette/HTTPX deprecation warning |
| Frontend | PASS: six Node tests, syntax check and production build (9 files) |
| Official journey | PASS in fresh in-app browser: Network, Ambhasi search, FLATLINE no-match filter, reset, Station, selected Evidence, UNCERTAIN/ABSTAIN and Recommended Verification |
| Timeline | PASS: earliest official observation updates to INSUFFICIENT_EVIDENCE; synthetic flag supports TELEMETRY_EVIDENCE |
| Provenance/export | PASS: source rows expanded; downloaded official JSON equals exact selected-observation API response |
| Labels/layout | PASS: historical/not-live and synthetic labels; unverified datum/timezone; October 11 desktop 1440px/mobile 390px checks had no horizontal overflow |
| Standalone Playwright | BLOCKED earlier by Chrome Crashpad/pipe startup; not claimed passed or rerun this documentation cycle |
| SAM | PASS locally: CLI 1.168.0 template lint, Python 3.12 package build, 3 real-data artifact routes plus 404 using local S3 test double |
| Cloud | NOT VERIFIED: no verified S3 upload, Lambda/API Gateway deployment, CloudFront/public URL or cloud log proof |

Entry HEAD e9c6dc8 was four commits ahead. Direct `git ls-remote` returned remote main b2576fad7ca1500299b505da9595868033880b15. No authentication or AWS mutation was performed.

Both documented startup commands succeeded during October 11 verification: `./scripts/start-local.ps1 -Port 8768` and, separately, `.venv/Scripts/python.exe -m uvicorn scripts.synthetic_demo_app:app --host 127.0.0.1 --port 8770`. Keep both terminals open. Dependencies, pinned raw CSV/manifest and evaluation/results.json must exist. No secret environment variables or Node server are required for local analytics. Closing the server terminal causes connection refusal. See README for first-time setup.

The 150-case evaluation is the committed October 10 reproduction, not a new release-day rerun. Official FLATLINE/DROPOUT stay unavailable without verified metadata; all five groups remain UNCERTAIN. Screenshots in docs/images depict explicitly synthetic FLATLINE, not actual incidents.

Cloud work still requires approved non-root access and verified budget. The handler needs private S3 object reads and CloudWatch logging; deployment would additionally need scoped CloudFormation/Lambda/API Gateway/CloudFront permissions and restricted IAM PassRole. No provisioning is authorized. SAM packaging is not Docker runtime execution; the draft handler lacks selected-observation routing. Owner must confirm organizer acceptance of local SAM use, push, record and submit.

---

# Historical records (superseded)

# October 9 P0 verification update

Final backend run: **46 passed**, one dependency warning, 8.31 seconds. Production build and JS syntax pass; npm audit reports zero vulnerabilities.

- Clean local HEAD at entry: f20ce804b2e224f731c6927c878f0059118217a4. GitHub's commits API returns HTTP 409 (repository empty); no pushed commit exists to verify. Authenticated user check returns 401 and Git credential-helper launch is denied in this environment. No force push or credentials exposure.
- Supported-browser Playwright locators now pass the fresh full Network → Station → Evidence journey against the real API, including UNCERTAIN / ABSTAIN and NextCheck. A separate, prominently labelled OFFICIAL HISTORICAL TEST SUBSET uses three unchanged source rows and passes the same journey to INSUFFICIENT EVIDENCE / history-recovery NextCheck.
- Standalone `npm run test:e2e` still fails before test execution because Chrome's crash subprocess cannot launch. This is not counted as a suite pass. The saved suite now requires both the normal and short-history test server.
- EvidencePackage now integrates FLATLINE/DROPOUT statistics and source-row citations when an explicitly verified DetectorContext is supplied. Default official-data execution still withholds these detectors because the required facts are unverified. It never promotes a test configuration to official metadata.
- No held-out performance evaluation, complete P0 freeze, AWS deployment or spending is claimed. AWS CLI and approved non-root profile remain unavailable; follow AWS-ACCESS.

# Current verification — October 9, 2026

- Backend: **43 passed, 1 dependency deprecation warning**, 6.01 seconds in this cycle.
- Frontend: JS syntax and production static build pass (8 nonempty assets).
- Current HTTP checks: `/`, `/api/health`, `/api/network`, station history and evidence return **200** on port **8766**. The same station key links 356 preserved Ambhasi rows to raw selected value -14.22, UNCERTAIN, and an actionable NextCheck. All five groups use the official pinned snapshot.
- Prior supported-browser verification passed Network → Station → Evidence, back links, deep-link refresh, keyboard selection and 390px overflow checks. **Current browser rerun is blocked by the browser tool's URL policy**; no workaround was attempted. Standalone Chrome previously failed to launch its crash subprocess, so the saved Playwright suite is not reported as passed.
- Python dependency audit: no known vulnerabilities. npm audit: zero vulnerabilities (October 8, dependencies unchanged).
- SPIKE runs on real historical data. FLATLINE and DROPOUT algorithms and eligibility contracts pass controlled unit tests, but official resolution/active-interval/publication-allowance evidence is absent: real outputs stay UNAVAILABLE. Four-state triage requires affirmative verified corroboration for environmental interpretation; no reference-provider integration is claimed.
- GitHub remote is correct. Current environment still returns HTTP 401 after the user's external re-authentication; no successful push is claimed. Existing local history is preserved.
- AWS: root access reported by owner; no root credentials used. Mumbai is intended, not verified. IAM temporary-login setup and scoped read-only policy are in AWS-ACCESS. No provisioning or spending.
- Restored one same-origin frontend/API server on 8766. `scripts/start-local.ps1` lets the owner keep it running in their terminal across agent sessions.

No accuracy/F1/field-failure result or full P0 readiness is claimed. Remaining blockers: GitHub credential access, fresh browser E2E, verified detector metadata, AWS identity/budget, held-out evaluation.

---

## Earlier first-cycle record (superseded where noted above)

# First execution cycle — October 8, 2026

## Actual results

| Check | Result | Scope / limitation |
|---|---|---|
| Python test suite | 25 passed in 6.04 seconds | Schema, raw preservation, invalid input, duplicate conflicts, causal spike examples, gap/zero-scale abstention, gradual-change regressions, evidence, API, real pinned CSV integration |
| JS syntax | PASS: `npm run check` | Syntax, not behavior proof |
| Running API smoke | PASS | HTTP health/network/evidence; five real groups, 29 source rows in selected evidence, next check and UNCERTAIN |
| Supported in-app browser | PASS for inspected first-screen journey | Actual API → network → selected station evidence preview → abstention → next check → quality/provenance rows; keyboard Enter selection; filter/no-match; 1440px and 390px no horizontal overflow |
| Browser source failure/retry | PASS | Temporarily blocked only local `/api/*` requests; explicit unavailable state and unknown counts; removed block and retry restored five groups. No test network override left active |
| Figma legend assets | PASS | Four original local SVGs nonempty and rendered at 10×10; no broken images. Conditional map excluded by product requirements |
| Browser console before deliberate fault | No warning/error entries | Not a performance or general reliability claim |
| Standalone Playwright suite | BLOCKED, NOT PASSED | Python subprocess pipe access denied; Node Chrome spawn EPERM in managed environment. Saved Node runner requires a permitted browser-launch environment. Three-screen suite is not implemented yet |
| Python dependency audit | No known vulnerabilities after correction | Initial audit reported vulnerabilities in pip 24.0; upgraded local pip to 26.2.1. Pin audit passed; not proof of complete security |
| npm audit | 0 vulnerabilities | Two browser-tool dependencies; no frontend runtime npm dependency |
| Prospective tracked-file secret scan | No matching credentials in 30 files at scan time | AWS key IDs, private-key headers, GitHub tokens and bounded secret assignments; limited pattern scan, not a comprehensive guarantee |

TestClient emits one dependency deprecation warning about its HTTPX transport; requests/tests passed. It is recorded, not suppressed.

Final experimental spike run: 1,776 preserved observations, 1,236 eligible detector executions, 540 unavailable/insufficient-history cases, zero flags. All five station assessments are UNCERTAIN. Initial four v0 flags were inspected and corrected as gradual departures; these are not final findings. No precision/recall/F1 or field-failure accuracy has been evaluated. Controlled unit examples are not an evaluation benchmark.

Screenshots and machine-readable local diagnostics reside in ignored `artifacts/`; they are local verification evidence, not a hosted demo. Source raw bytes also remain ignored. The browser is connected to the real local API, not Figma mock values.

## Exact implemented files

| Area | Files |
|---|---|
| Domain/API | `backend/__init__.py`, `backend/models.py`, `backend/provider.py`, `backend/quality.py`, `backend/spike.py`, `backend/evidence.py`, `backend/api.py` |
| Frontend | `frontend/index.html`, `frontend/styles.css`, `frontend/app.js` |
| Original Figma legend assets | `frontend/assets/telemetry.svg`, `frontend/assets/environment.svg`, `frontend/assets/uncertain.svg`, `frontend/assets/insufficient.svg` |
| Acquisition / browser test | `scripts/acquire.py`, `scripts/check-browser.cjs` |
| Automated backend tests | `tests/conftest.py`, `tests/test_core.py` |
| Provenance | `data/manifest.json` |
| Dependencies | `requirements.in`, `requirements.lock`, `package.json`, `package-lock.json` |
| Project / disclosure | `.gitignore`, `LICENSE`, `README.md`, `docs/AI_USAGE.md`, `docs/ATTRIBUTIONS.md`, `docs/DECISIONS.md`, `docs/TASK-BOARD.md`, `docs/VERIFICATION.md` |

## Remaining gates

AWS CLI and default profile absent; no AWS identity/region, core service authorization, quotas, billing visibility or budget verified. No resource was provisioned. GitHub authentication works and the repository was newly created during the event. User-supplied live/start email clears build authorization; participant eligibility/check-in/Builder Center confirmation remains pending separately. Submission deadline is reported as October 11, 8 PM IST by the newer organizer article; final form/receipt remains a future check.

Next engineering action: run the saved standalone browser suite in a permitted environment, then complete isolated-spike/reversion semantics and remaining P0 according to the frozen dependency order. Begin AWS read-only account checks once the approved authentication route is available. No held-out performance claims or AWS deployment claims until measured.

## October 10 local integration verification

AWS SAM CLI 1.168.0: template lint validation and Python 3.12 build passed. `scripts/verify-sam.ps1` is the local demonstration command. The SAM-built handler is checked against exported evidence using an explicit local S3 test double; this is not cloud deployment or Lambda runtime emulation. Backend: 52 tests passed; frontend build passed. Controlled evaluation rerun matched all 150 cases and metrics. Browser Network → Station → Evidence → NextCheck passed on port 8768.
