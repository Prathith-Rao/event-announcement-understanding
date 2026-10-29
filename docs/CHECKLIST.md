# Completion and evidence checklist

## Version-2 update

- [x] Expanded to 19 event categories plus an internal non-event label.
- [x] Generated 11,922 explicitly synthetic records, retaining provenance and exact authored spans.
- [x] Trained classifiers on 7,152 examples and a BIO CRF on 4,000 training examples.
- [x] Saved grouped assignments, train-only features, validation choices, frozen test outputs, code/model/data hashes and actual errors.
- [x] Replaced keyword vetoes with context/model interpretation and broader temporal/location handling.
- [x] Removed repeated synthetic banners from the main flow while retaining honest provenance in methodology, evaluation and exports.
- [x] Added inline missing/ambiguity/reference-date notices, typed API responses, client timeout and corrected export statuses.
- [x] Expanded tests: 69 Python regressions plus JS export checks; production build and local HTTP benchmark.
- [ ] Independent real-data annotation and field-rich evaluation still pending.
- [ ] Universal sentence understanding is not achieved or claimed. Held-out title boundaries remain a weak point; full measured limits are in VERIFICATION and the report.

The older checklist below records the original implementation; version-2 taxonomy and model changes supersede its five-category/model details.

## Implemented and verified

- [x] Existing course PDFs preserved and read as reference material.
- [x] Independent Python NLP modules; local FastAPI and React/Vite application.
- [x] Five category definitions, primary-purpose overlap rules and category abstention.
- [x] Real NLTK sentence/token spans, POS, POS-aware WordNet lemmatization, explicit EVENT/VENUE RegexpParser grammars.
- [x] Contextual field extraction, exact character evidence, deadlines, missing fields, conservative/relative dates, multiple-event/unrelated heuristics.
- [x] Actual NLTK Naive Bayes and raw/preprocessed TF-IDF logistic training; majority/keyword baselines.
- [x] Grouped reproducible splits, train-only vocabulary/IDF, validation C selection, split/data/model audits and explicit frozen final evaluation commands.
- [x] Training-only FreqDist, distinctive terms, sentence-local collocations (minimum 2), POS and chunk-pattern tables/plots/interpretations.
- [x] Real public collection, robots/rate-limit checks, source log, 25-candidate pilot and bounded expansion; actual retained counts in collection summary.
- [x] Automatic quality exclusions/character-decoding correction logs; original evidence and proposed/human separation.
- [x] Separate CSV annotation workflow with explicit decisions, reviewer/timestamp and field-span validation.
- [x] Synthetic development and separate final challenge fixtures with visible provenance and review status.
- [x] Metrics, confusion matrices, field/record metrics, actual disagreements and saved methodology views.
- [x] Editable result exports with stale-evidence removal; JSON download checked in browser.
- [x] Empty/error/unavailable-resource handling; meaningful Python and JS tests; production build.
- [x] Windows setup commands, dependency locks, AGENTS conventions, Markdown AAT report draft, demo and viva guide.
- [x] Browser verification and desktop/mobile screenshots; narrow viewport has no horizontal overflow.
- [x] Automated assistance disclosure; no invented personal/certification data.

## Pending human work / unavailable evidence

- [ ] Review **every** real category and all four fields in `data/review.csv`, including explicit absences. There are currently no accepted human reviews.
- [ ] Review excluded and needs-review records; independently check source eligibility, field coverage, natural paragraph selection, and duplicate/template groups.
- [ ] Improve category balance: Seminar and Meeting currently have very sparse proposed coverage; times are absent from current automatic field suggestions. Proposed coverage is not gold coverage.
- [ ] Collect more suitable natural, field-rich prose where permitted. The attempted 300-record collection did not establish a 250–500-record dataset; actual yield is recorded.
- [ ] Obtain independent second-annotator labels, adjudicate disagreements and compute agreement only after genuine annotation.
- [ ] Audit AI-authored synthetic gold and challenge expectations; do not describe them as manually verified.
- [ ] Train reviewed-real models, freeze decisions, then run reviewed-real final classification and extraction evaluation. No academically final real-data performance exists yet.
- [ ] Confirm course disclosure policy, team membership, student IDs, guide assignment and actual individual contributions. Complete genuine declarations/certificates/signatures separately.
- [ ] Check final report wording and required formatting, select screenshots, rehearse demo and viva, and submit with honest evidence.

Operational implementation is complete; academic finality depends on these human/data tasks. The application and experiment scripts remain usable while they are pending.
