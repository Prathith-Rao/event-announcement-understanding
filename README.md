# EventLens — expanded local event understanding

Version 2 recognizes **19 event categories**, rejects non-event text, and extracts name, date, time and venue with exact source evidence. It combines Python, NLTK, scikit-learn, a trained CRF, FastAPI and React/Vite. All inference runs locally on CPU.

The expanded corpus contains **11,922 explicitly synthetic examples**, replacing the original 80-example development corpus. Models train on 7,152 records; validation has 2,386 and the separate test has 2,384. A CRF learns name/venue BIO tags from 4,000 train-only examples. The 26-record real pilot remains separate and unreviewed. Provenance is available in data, methodology, evaluation and exports rather than repeated warnings in the main flow.

## Run on Windows

Python 3.13 and Node 22.12+ are recommended. From PowerShell:

~~~powershell
Set-Location D:\NLP_AAT
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m scripts.download_nltk
Set-Location frontend
npm ci
npm run build
Set-Location ..
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
~~~

Open **http://127.0.0.1:8000**. API docs: **http://127.0.0.1:8000/docs**. The bundled trained model is ready after installation; no retraining is required to use it. Ctrl+C stops the server. For frontend development run npm run dev in frontend and use http://127.0.0.1:5173 with FastAPI on 8000.

If initial environment creation fails during ensurepip, recover it using python -m pip --python .venv install pip, then install the lockfile. No activation or PowerShell execution-policy change is necessary.

Packages and standard NLTK resources download once into the project. Runtime requires no network inference, paid API, GPU or database. CRF dependencies are included in the locks. Do not load untrusted pickle files.

## What changed

- 19 categories: Workshop, Seminar, Competition, Meeting, Cultural event, Conference, Webinar, Hackathon, Sports event, Exhibition, Career event, Community service, Social gathering, Training course, Product launch, Academic assessment, Ceremony, Tour or excursion, Other event. An internal Not an event class supports rejection.
- Trained raw/lemmatized TF-IDF logistic classifiers, word/character TF-IDF classifier, NLTK Naive Bayes, majority and keyword baselines.
- Learned categories are no longer blocked by keyword ties. Contextual explicit-format interpretation supports short notices and distinguishes venue words from event purpose.
- A trained CRF complements NLTK sentence segmentation, tokenization, POS, lemmatization and explicit RegexpParser grammars.
- Broader dates, relative forms, ranges, noon/midnight, bare hours, 24-hour times, online platforms, address distractors and unfamiliar proper-name venues.
- Missing fields and date/time clarifications appear beside the affected field. Necessary global notices remain. Edited exports invalidate stale evidence/normalization and retain original suggestions.
- Client timeout, typed API response schemas, expanded regression tests, readable frontend formatting and saved measurements.

The system supports many common English sentence styles. **Correct interpretation of every possible sentence is not guaranteed.** Complicated titles and unseen phrasing can need correction. Evidence, alternatives and editable fields make that visible.

## Reproduce training and evaluation

The shipped dataset and final artifacts are frozen. Inspect their saved results directly. In a fresh working copy, before final evaluation:

~~~powershell
.\.venv\Scripts\python.exe -m scripts.build_expanded_data
.\.venv\Scripts\python.exe -m scripts.train_expanded
.\.venv\Scripts\python.exe -m scripts.evaluate_expanded --partition validation
.\.venv\Scripts\python.exe -m scripts.corpus --mode expanded_v2
~~~

On an unfrozen run only, train_expanded --overwrite retrains. Dataset replacement requires the explicit build_expanded_data --replace-unfrozen flag and preserves the earlier corpus. Once the test is evaluated neither operation may overwrite the run.

After model choices and recognition code are frozen:

~~~powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_expanded --partition test
.\.venv\Scripts\python.exe -m scripts.corpus --mode expanded_v2
.\.venv\Scripts\python.exe -m scripts.report_expanded
~~~

Duplicate final evaluation is refused. Create a new version for future development; do not reopen this test to improve its score. Version-1 code/report/ZIP are preserved under archive, and its old final challenge was not reused as the new tuning set.

All variants share partitions. Known template variations, untitled constructions and negative constructions stay within their groups. Proper-name/venue prefix pools differ across partitions. Vocabulary/IDF fit on train only. LR C in {1,4} is selected on validation. NB uses up to 1,500 train-derived binary lemma features. Default selection compares LR variants; NB remains available and can score higher on the synthetic benchmark. The end-to-end hybrid-context row includes deterministic interpretation and is not the standalone classifier.

Authored examples reuse title themes and purpose descriptions. High scores do not establish independent real-world generalization. See [measured results](reports/RESULTS.md), [data limitations](docs/DATA_CARD.md), and [the report](docs/AAT_REPORT.md).

## Real collection and annotation

The robots-aware collector, provenance and separate review workflow remain available:

~~~powershell
.\.venv\Scripts\python.exe -m scripts.collect --limit 25 --max-pages 90
.\.venv\Scripts\python.exe -m scripts.audit_pilot
.\.venv\Scripts\python.exe -m scripts.review export
# Humans complete data/review.csv before import:
.\.venv\Scripts\python.exe -m scripts.review import
~~~

Read [the annotation guide](docs/ANNOTATION_GUIDE.md). Automatic suggestions never become human reviews. Actual counts/gaps are in data/collection_summary.json. Real field-rich data, independent annotations and final reviewed-real evaluation remain pending. The runtime uses the expanded synthetic model rather than a fictitious reviewed model.

## Verify and package

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q event_nlp backend scripts
Set-Location frontend
npm test
npm run build
Set-Location ..
# With the API running:
.\.venv\Scripts\python.exe -m scripts.benchmark
.\.venv\Scripts\python.exe -m scripts.report_expanded
.\.venv\Scripts\python.exe -m scripts.package_project
~~~

The ZIP excludes environments, downloads, package caches and internal development archives. It includes source, locks, compiled frontend, models, datasets, evidence, plots and documentation.

| Location | Deliverable |
|---|---|
| event_nlp | Independent taxonomy, recognition, temporal, sequence and classification modules |
| data/expanded_v2 | 11,922 synthetic examples with exact spans, provenance and assignments |
| models/expanded_v2.pkl | Trained classifiers and BIO CRF |
| reports/expanded_v2 | Manifests, metrics, errors, per-record predictions, plots and benchmark |
| data/real.jsonl, data/review.csv | Separate real pilot and annotation worksheet |
| docs/AAT_REPORT.md | Current course report based on actual saved measurements |
| docs/DEMO_SCRIPT.md, docs/VIVA.md | Demonstration and viva notes |
| docs/VERIFICATION.md, docs/CHECKLIST.md | Executed checks and remaining evidence |
| archive | Preserved earlier implementation and artifacts |

No personal or certification details have been invented. Automated assistance and human work are recorded in docs/ASSISTANCE_AND_REVIEW.md.

## Independent real-announcement review

The blind review packet contains 82 public-source excerpts in [data/real_review](data/real_review). Read ANNOTATION_GUIDE.md, review ANNOUNCEMENTS.md, and fill annotations.csv without changing original text. Labels remain blank until human review. This convenience sample is source-clustered, not class-balanced; invitation-only evaluation does not measure non-event rejection. Report its reviewed results separately from frozen synthetic results.

Repository: https://github.com/Prathith-Rao/event-announcement-understanding

## Completed real-data evaluation

One supplied human annotation file covers82 public excerpts:59 accepted,19 unresolved and4 excluded. Frozen-model results, class/source coverage, new-only34-record slice and per-record predictions are in [reports/real_review_v1](reports/real_review_v1/RESULTS.md). Full hybrid accuracy is54.24%; word/character LR accuracy47.46%. These are source-clustered convenience-sample measurements, not new training results. The original supplied CSV is preserved privately; public gold retains source text and validated spans.
