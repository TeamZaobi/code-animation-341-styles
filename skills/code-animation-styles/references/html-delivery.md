# Standalone HTML delivery

Use one UTF-8 HTML file that runs from `file://` without a build, CDN, fetch, external font, or external asset. Inline a selected asset only when needed. If the user explicitly requests external dependencies, disclose the resulting online requirement.

Provide a visible title, a short accessible description of the animated scene, and labeled native play/pause, replay, and timeline controls. Keep them usable at narrow widths and under keyboard navigation. Honor `prefers-reduced-motion` by starting paused. Use local system fonts with Chinese fallbacks when needed.

Drive scene state from elapsed time. Seeking, replay, resizing, and pause/resume should preserve the same scene for the same timestamp. Seed randomness or precompute stable particles; replace frame-dependent accumulation when adapting upstream examples. Scale Canvas backing resolution for device pixel ratio without changing the scene's coordinate system. Keep animation work bounded.

Separate animation settings (content, colors, duration) from rendering logic so the user can edit a short configuration object. Render a useful first frame before requesting animation frames. For silent output, state that fact; a browser animation is not an exported video or audio track.

Keep a source comment identifying the repository, pinned commit, selected IDs, modifications, and applicable license. Include the upstream attribution visibly. When redistributing an adaptation, include the relevant license text or stable license link as required by upstream; MIT portions retain their corresponding copyright and permission notices. Classify catalog licensing from `vendor/NOTICE.md`; do not infer commercial permission for every style or for a specific generated deliverable from the catalog label alone.

Acceptance checks:

1. Load the file with networking disabled or establish that it makes zero external requests; check console/runtime errors.
2. Observe two different animation timestamps and confirm the scene changes.
3. Pause and verify the timeline remains fixed; replay returns to the start; seeking produces a frame at the selected time.
4. Resize to a narrow viewport and inspect legibility, controls, and overflow.
5. Inspect reduced-motion behavior when browser tooling supports it. Report untested branches explicitly.
