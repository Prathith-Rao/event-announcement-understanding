# Version-2 recognition specification

Accept one English announcement and optional explicit reference date. Return category, nullable name/date/time/venue, exact evidence, all candidates, per-field statuses and necessary global notices. Every span satisfies input[start:end] == raw using Python Unicode character offsets. Source text is never replaced by normalization.

The taxonomy has 19 event categories in event_nlp/taxonomy.py and an internal non-event class. Primary format is interpreted in context: a workshop about careers remains Workshop; Seminar Room is a venue; explicit hackathons/sports fixtures have their own classes. Statistical and explicit-format decisions are recorded separately. Unknown purposes can use Other event; unrelated text should abstain. Detection remains fallible.

Extraction preserves case, punctuation, numbers and prepositions. NLTK Punkt, Treebank, Penn POS and explicit EVENT/VENUE RegexpParser grammars remain substantive. POS-aware lemmatization is classification-only. A trained CRF proposes BIO name/venue spans from token/POS/shape/context features. Evidence and contextual boundaries prevent arbitrary missing-field invention.

Dates distinguish occurrence, deadline and publication roles. Missing years and ambiguous numeric ordering stay unnormalized. Relative expressions require a supplied reference date. The UI's Use today shortcut is an explicit user choice. Next weekday is strictly following when today matches; this/bare weekday is next matching including today. Explicit same-month ranges can normalize to an ISO interval using month/year actually present. No unspecified timezone or AM/PM is invented.

Field status contains state/message: ok, missing, ambiguous, notice or needs_reference. Missing-field intimations belong beside their fields. Necessary global notices cover unrelated/multiple-event input and failures. Synthetic provenance stays in datasets, methodology, evaluation and exports rather than a repetitive main-screen banner. UI edits are separate from dataset review and invalidate stale evidence/normalization.

The expanded corpus uses seed 42, 11,922 records, 70 construction groups and saved assignments. Splits are 7,152/2,386/2,384. Vocabulary, IDF and NB feature selection use train only. LR C values 1 and 4 use validation. A deterministic 4,000-record train subset teaches the CRF. All measurements state their provenance; authored theme/description reuse limits generalization claims. Real data stays separate until humans review it.

The explicit final test is frozen with code/data/model hashes and saved predictions. No further recognition changes should be selected against its results. Version-1 source/ZIP, data and final challenges remain preserved. Further development requires a new version and independent evaluation.

API: POST /api/analyze; GET /api/config, /api/health, /api/evaluation, /api/methodology. Request/response contracts are validated. Runtime uses local models/resources, without paid APIs, external LLM inference, GPU, authentication or database.

Common English styles are supported; universal sentence understanding is not promised. Complex titles, ambiguous prose and multiple events can require correction. No independent real-data accuracy, annotation agreement or new algorithm is claimed.
