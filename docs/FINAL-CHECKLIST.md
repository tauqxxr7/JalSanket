# Final release checklist — October 11

## Completed locally

- [x] Release freeze: documentation and screenshots only.
- [x] Main/remote inspected; no discarded changes.
- [x] 55 backend tests, six frontend tests, syntax and production build pass.
- [x] In-app journey, provenance, exact export and responsive evidence checked.
- [x] SAM validation, package build and local artifact contracts pass.
- [x] README desktop/mobile screenshots accurately labelled synthetic.
- [x] Submission summary, storyboard, disclosure and attribution updated.
- [x] [Organizer announcement](https://www.wemakedevs.org/blogs/what-is-happening-in-delhi-on-10-october) confirms October 11, 8 PM IST.

## Owner required

- [ ] Review and push release commits; verify remote SHA.
- [ ] Confirm registration/check-in, eligibility and Builder Center verification or permitted pending case.
- [ ] Confirm organizer acceptance of actual local AWS SAM use; no cloud deployment/S3 upload claim.
- [ ] Verify current deadline and required fields in the [signed-in submission form](https://www.wemakedevs.org/aws/env/submit).
- [ ] Record/upload demo, verify access and enter the real video URL.
- [ ] Submit truthful repository, tooling and AI-use details; save receipt.

## Remaining limitations

Standalone Playwright is blocked here; in-app checks are separate evidence. No public demo, verified S3 upload or cloud deployment exists in this audit. Non-root permissions/budget remain unverified. The draft Lambda adapter lacks selected-observation evidence. Synthetic evaluation does not diagnose physical failures; official metadata gates remain enforced.

## Safe push from repository root

```powershell
git status -sb
git fetch origin
git push origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

The final two SHAs must match. If rejected, stop and inspect remote changes; never force-push or discard work. Authenticate only in your own terminal if required, without sharing tokens.

**CONDITIONAL GO:** local demo is ready; owner push, video, eligibility/tooling acceptance and submission remain outstanding.

## Final AWS evidence status — October 11

Owner reports 11 evidence JSON snapshots uploaded to `jalsanket-evidence-2026-tauq` in `ap-southeast-2`. This session could not independently list/read them: AWS CLI STS returned `NoCredentials`. Public accessibility is not assumed. The running FastAPI application uses local CSVProvider, not S3. Therefore the reported S3 upload is an isolated evidence store, not a deployed application backend. The draft Lambda handler can read S3 but is not verified deployed and lacks selected-observation routing.

Local SAM validation/build and test-double contracts are verified; they alone do not establish compliance with the current rule requiring AWS use shown in the video. AWS eligibility remains unresolved until the owner demonstrates existing S3 objects and obtains any necessary organizer clarification. No uploads, IAM changes or deployments were performed. See [AWS demonstration steps](AWS-DEMO-EVIDENCE.md).

Final freeze checks: 55 backend and nine frontend tests pass; syntax/build pass. AWS CLI is installed but has no credentials. Both local network endpoints return actual data. Latest local commit must be pushed after this audit; verify remote refs.
