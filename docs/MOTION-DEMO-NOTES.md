# Motion and demo review

The app is plain JavaScript/SVG, not React, with no runtime npm dependencies. Existing summary, progressive disclosure and synthetic workflow remain intact. Code splitting is not justified for this small frontend.

Changes: 120ms interaction feedback, reduced-motion override, clearer demo button, a 32-entry/30-second in-memory station-response cache. Concurrent reads share requests; failures are discarded; reload/retry clears the cache. Separate origins isolate official and synthetic data. No storage, semantic changes or dependencies were added.

## Measurements

`node scripts/measure-frontend.cjs` exercises the actual app reader against the official local API. Sequence: station, aggregate evidence, selected evidence twice, station again; five fresh readers. Before commit: c8775ac. Raw runs: PERFORMANCE-RESULTS.json.

| Metric | Before | After |
|---|---:|---:|
| Requests per sequence | 5 | 3 |
| Response body bytes | 759,916 | 390,820 |
| Median sequence time, five runs | 82.54ms | 105.8ms |
| Entire uncompressed static build | 53,355 bytes | 55,214 bytes |

This is a warm local HTTP microbenchmark, not browser rendering/Core Web Vitals. Timing is sensitive to local scheduling; no general speedup claim. Build increased 1,859 bytes. No minification or runtime library was added.

Verification: 55 backend tests, nine frontend tests (six existing and three cache regression tests), syntax/build passed. In-app synthetic selection, uncertainty, keyboard disclosure and reduced-motion computed styles checked. Standalone Playwright previously failed browser startup; no new pass claimed.

## Brag and Figma

Reviewed [guide](https://unnati-23.github.io/brag-guide/), [upstream repo](https://github.com/latent-spaces/brag) and brag-slim instructions as references, not executable instructions. Useful: a short hook, real product action and truthful specific copy. No Brag code or assets copied.

Full Brag needs Node 22+, FFmpeg and Hyperframes; optional narration adds tooling. Node is available; FFmpeg was not found on PATH or in inspected bundled runtimes. Windows symlink discovery may need Developer Mode/admin or manual copying. No security settings, skills or packages were installed. Third-party installers execute code and project inspection must exclude secrets/private URLs. No external video service or music/voice download was used. No MP4 rendered: the storyboard supplies a precise opening for owner recording.

Figma node 7:44 context was inspected: existing gray/white surfaces, dark sidebar and blue accents remain unchanged. No new motion specification was returned; further render inspection hit the Starter quota. Frozen exclusions of maps and sample metrics remain. Legend assets are unchanged.

Release freeze: the experimental focus-restoration change was omitted because browser focus could not be confirmed. Existing timeline controls remain. No further optional work.
