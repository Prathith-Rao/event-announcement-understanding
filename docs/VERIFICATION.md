# Version-2 verification

Executed locally on Windows on 28 October 2026. These checks are software evidence, not human annotation.

- Python regression suite: **69 passed**, one upstream Starlette/httpx deprecation warning.
- JavaScript export checks: **5 passed**; corrections, stale evidence, CSV escaping, model provenance and edited field-status behavior are covered.
- React/Vite production build succeeds; Python compileall succeeds.
- Dataset integrity test checks all 11,922 records' expected spans, synthetic provenance, human-null state and group/exact-duplicate overlap.
- Actual classifier and CRF artifacts are loaded and exercised. API request/response contracts, missing resources/models and errors are tested.
- Independent regression cases cover all 18 specific categories, informal coffee/picnic plans, short meeting notices, venue-format distractors, deadline sentence boundaries, unknown proper-name venues, relative dates, intervals and invalid clocks.
- The version-2 final test is evaluated once; code/data/model hashes and all predictions are saved. No recognition tuning follows that final result. Version-1 frozen artifacts remain preserved.

## Measured limits

Consult reports/expanded_v2/test_metrics.json and extraction_test.json for exact final values. The word/character classifier's final synthetic macro F1 is about 0.983. In the frozen extraction test, date/time F1 are about 0.994 and venue F1 about 0.952. Title boundaries remain substantially harder, with strict name F1 about 0.665 and complete-record accuracy about 0.564. The broader validation scores were higher; that gap is retained, not concealed or tuned away.

These are authored synthetic expectations with repeated themes/descriptions, not independently reviewed real-data accuracy. A strong classifier does not establish equally strong extraction. The application provides source evidence, partial results, inline notices and edits rather than claiming every sentence is solved.

## Browser verification

The revised main page is tested against the built FastAPI-served app. It has no repeated synthetic-model warning banner. The informal picnic example produces Social gathering, noon and Rose Garden; missing title and reference-date needs appear beside their fields. The category selector lists 19 choices. Desktop/mobile screenshots are retained under docs/screenshots.

JSON/CSV export tests retain training provenance without presenting it as an extraction warning. Current browser JSON-download verification confirmed an edited event name, null evidence for that edit, retained automatic suggestions, and retained training provenance. The reference-date shortcut explicitly filled 2026-10-28 and resolved tomorrow to 2026-10-29. Saved evaluation/methodology views displayed the version-2 artifacts. At a 390-pixel mobile viewport, the document had no horizontal overflow; both desktop and mobile screenshots were inspected.

Local warm-request timings are measured by scripts.benchmark and saved in reports/expanded_v2/performance.json. Their scope is six short cases and 60 HTTP requests; they exclude browser rendering and are not a hardware-independent latency guarantee.

The preview server is temporary. Start/restart the local application with README's command after handoff.
