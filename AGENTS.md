# Event Announcement Understanding

Local English NLP course project. Preserve the reference PDFs. No paid API, LLM inference, GPU, authentication, or database. Python NLP modules must stay independent from FastAPI and React. Do not add transformers for appearance.

Version 2 expands to 19 event categories plus an internal non-event label. The default runtime uses expanded_v2 classifier/CRF artifacts. Keep provenance in datasets, methodology, evaluation and exports; do not show repetitive synthetic-training banners in the main flow. Missing/ambiguous field notices belong beside their fields. No claim that arbitrary sentences are perfectly understood.

Current commands: python -m scripts.build_expanded_data (fresh corpus only); python -m scripts.train_expanded; python -m scripts.evaluate_expanded --partition validation; python -m scripts.evaluate_expanded --partition test (explicit, once frozen); python -m scripts.corpus --mode expanded_v2; python -m scripts.report_expanded. Use the project virtual-environment Python path as below. The version-1 ZIP/code/report are preserved under archive/ and their frozen results must not be tuned or overwritten.

## Integrity conventions
- `real` records require actual source URLs and naturally occurring paragraphs. Never synthesize source text from fields.
- Automatic suggestions never become human reviews. `human` is null until a person supplies annotations. Human review includes identity, timestamp and explicit field-presence decisions.
- Synthetic data and challenge fixtures stay separately identified. Experiments on provisional or synthetic labels must say so.
- Group duplicates, template variations and near-duplicates before splitting. Fit vocabulary and transformations on train only. Select on validation. Final evaluation requires an explicit command and a frozen experiment.
- Exact evidence uses Python character offsets `[start, end)` into untouched input. Missing values are null. Never infer an absent year or resolve relative dates without a supplied reference date.

## Commands (PowerShell, repository root)
`python -m venv .venv`
`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
`.\.venv\Scripts\python.exe -m scripts.download_nltk`
`.\.venv\Scripts\python.exe -m scripts.collect --limit 25`
`.\.venv\Scripts\python.exe -m scripts.review export`
`.\.venv\Scripts\python.exe -m scripts.experiment --mode development`
`.\.venv\Scripts\python.exe -m scripts.corpus`
`.\.venv\Scripts\python.exe -m pytest`
`.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`
`cd frontend; npm ci; npm run build; npm test; npm run dev`

## Code conventions
Use type hints, small functions, JSON/JSONL artifacts, UTF-8, seed 42, and root-relative paths resolved from `event_nlp.config.ROOT`. Download resources only in setup commands. Report missing resources explicitly at runtime. Do not silently substitute fabricated POS tags. Test parsing, date conservatism, leakage, review validation, API and exports. Keep final challenge gold out of tuning commands.
