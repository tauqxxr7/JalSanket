# Attribution and terms

- Telemetry: CGWB producer; NWIC/NWDP publisher, Ministry of Jal Shakti. Exact resource, retrieval/hash and transformations are in `data/manifest.json`. [Resource](https://www.nwdp.nwic.gov.in/en/dataset/ground-water-level-telemetry-daily-cgwb-as-assam/resource/2da4e849-2249-4e15-a609-a6166e30a300), [reuse policy](https://www.nwdp.nwic.gov.in/en/footer/copyrightPolicy), rechecked October 8. Resource metadata says Other (Open); no GODL license is invented. Raw full CSV stays outside Git. No agency endorsement implied.
- UI: user's [JalSanket — Evidence Trail](https://www.figma.com/design/WkyawTvNQYtHiuOuypXoSp/JalSanket-%E2%80%94-Evidence-Trail), Network Overview 7:44. Four original 10px SVG legend assets: telemetry 7:184, environmental 7:187, uncertain 7:190, insufficient 7:193. Conditional map assets are deliberately omitted under the no-map requirement. System font fallback; no proprietary font file copied.
- Runtime direct dependencies: FastAPI (MIT), Pydantic (MIT), Uvicorn (BSD-3-Clause). Test/tool direct dependencies: HTTPX (BSD-3-Clause), pytest (MIT), pip-audit (Apache-2.0), Playwright (Apache-2.0). Exact installed versions are recorded in Python/npm lockfiles. Upstream packages retain their own notices/licenses; project MIT does not relicense them.
- OpenAI Codex and Figma MCP assistance: see AI_USAGE.md. No competitor implementation was copied.

- AWS SAM CLI: AWS open-source serverless validation/build tooling, Apache-2.0; https://github.com/aws/aws-sam-cli. Used locally to build the existing Lambda handler, with no cloud deployment claimed. Version pinned in requirements-sam.txt.

- README screenshots: captured from the local JalSanket application on October 11, 2026. Both show explicitly synthetic FLATLINE modifications on attributed historical telemetry; neither depicts a verified physical sensor incident or cloud deployment.
