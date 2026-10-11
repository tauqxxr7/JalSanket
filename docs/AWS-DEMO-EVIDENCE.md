# AWS evidence for the final video

Owner reports 11 snapshots in `jalsanket-evidence-2026-tauq`, region `ap-southeast-2`. Agent verification is blocked: AWS CLI returned NoCredentials. Object contents, count and public accessibility are not independently confirmed.

The FastAPI application uses local CSVProvider, not S3. The reported bucket is a separate evidence store. SAM locally packages a draft S3-reading Lambda handler; no Lambda/API Gateway deployment is established.

## Record using an existing authorized non-root session

1. Open the existing bucket in S3 Console and show its actual region, object list/count and modified dates.
2. Open one existing evidence JSON. Show provenance/hash, station grouping, assessment and next_check; compare with the local export if possible.
3. Say: “S3 stores exported evidence snapshots. The investigation app currently runs locally and does not read this bucket at runtime.”
4. Do not expose credentials/account menus, make objects public, upload files or change permissions.

Optional read-only commands if already authenticated as non-root:

```powershell
aws s3api get-bucket-location --bucket jalsanket-evidence-2026-tauq --region ap-southeast-2
aws s3api list-objects-v2 --bucket jalsanket-evidence-2026-tauq --region ap-southeast-2 --query 'Contents[].{Key:Key,Bytes:Size,Modified:LastModified}'
```

If access fails, do not describe the objects as verified. The [official rules](https://www.wemakedevs.org/aws/env/rules) require AWS use shown in the video; local SAM alone does not establish compliance. Organizer acceptance remains unresolved. Upload the video to YouTube public/unlisted, under three minutes, and verify it signed out.
