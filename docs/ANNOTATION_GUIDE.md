# Annotation guide and review workflow

Version-2 category definitions are in event_nlp/taxonomy.py and the current AAT report. The original five-category boundaries below remain useful, with more-specific explicit formats such as hackathons, sports fixtures, conferences and career events now separate. The 11,922-record expanded corpus has programmatically authored expectations; none are falsely marked human-reviewed. Main-flow result edits still do not annotate training data.

## Scope and category decisions

Read **only the stored original announcement paragraph** as model input. Visit its source to confirm provenance, but do not fill absent fields from a webpage table that is not in the stored text. Whitespace is normalized once at collection; all offsets refer to the stored `text`. Correct English character-decoding errors before annotation, keeping the original collection and change log.

| Category | Primary purpose | Boundary |
|---|---|---|
| Workshop | Guided practice or skills training | A speaker may lecture inside a workshop; primary hands-on purpose wins. |
| Seminar | Speaker-led research/knowledge presentation and discussion | A generic conference or training course is not automatically a seminar. |
| Competition | Judging, ranking, winners or awards | Cultural contests are Competition if the contest is primary. |
| Meeting | Organizational discussion, planning, decisions, representation | A scientific conference called a “meeting” may be outside this definition. |
| Cultural event | Artistic performance, celebration or festival | Festival sub-events must be separable; do not invent a single category for a mixed schedule. |

Use `needs_review` for equal-purpose overlaps, unclear format, or multiple events. Use `excluded` for irrelevant text, navigation fragments, inaccessible provenance, non-English material, or duplicates. Explain the reason in notes. Do not infer a category merely from a source URL, institution, or a “seminar room” venue.

## Span annotations

- `event_name`: explicit title or named event phrase, not a made-up summary. For `workshop "Data Skills"`, annotate `Data Skills` without quotation marks. For `Workshop on Group Theory`, the whole explicit named phrase is acceptable if it is actually in the stored text; adopt a consistent title boundary and record uncertain cases.
- `date`: event occurrence date, not publication date, application date, or registration deadline. Annotate exact raw text. Missing year stays missing. For multiple competing dates/ranges that the single-date schema cannot represent, leave date null and note the candidates. Do not arbitrarily choose an endpoint.
- `time`: exact event clock expression or stated time range. Never use an office's opening hours or a registration closing time as event time. Do not invent AM/PM or timezone.
- `venue`: explicit event location or online platform. Exclude organizer addresses, speaker affiliations and contact-office locations unless clearly also the event venue.
- Missing/unsupported/ambiguous field = explicit null (blank raw cell in CSV). If a date is relative, supply a documented reference date or leave normalized date blank. `next Monday` follows the first strictly following Monday convention; flag alternate interpretations in notes.

## Review, independently of the application

1. Run `python -m scripts.audit_pilot`, then `python -m scripts.review export`. Work in `data/review.csv` using Excel or a UTF-8-aware editor. Back up your edited sheet before exporting a new one.
2. Preserve `id`, `text`, source metadata and `suggested_*`. Automatic suggestions are a starting point, not gold. The review fields begin blank.
3. Fill `reviewer` with a real team identifier, `reviewed_at` with an ISO timestamp, and `decision` with `accepted`, `needs_review` or `excluded`. For accepted records, choose a category and check **every** field, leaving absent raw cells blank deliberately. Add notes for ambiguity and the reason for exclusion. Copy exact substrings into `event_name_raw`, `date_raw`, `time_raw`, `venue_raw`.
4. Import with `python -m scripts.review import`. The importer validates evidence, timestamp, decision and category for all submitted rows before writing; corrections remain separate in `data/human_corrections.jsonl`. A repeated raw substring needs explicit JSON offsets in `human.fields`; do not silently use its first occurrence.
5. Have a second team member independently label a representative subset without seeing the first annotations. Log disagreements and adjudicate the primary-purpose and span-boundary decisions. Inter-annotator agreement is **pending** until this actually happens; no score is fabricated.
6. Only accepted human records enter `--mode reviewed`. Excluded and needs-review records remain in provenance records but do not become forced class labels. Ensure at least five independent groups and at least two classes; all five classes and reasonable held-out supports are strongly preferred. Report absent classes.

Application result edits do not change this dataset or count as human annotation. Synthetic challenge expectations were AI-authored and are also `needs_review`; team audit of them is pending. Test annotations must be finalized before the test partition is opened. Save any post-evaluation corrections in a new dataset version, rather than improving scores in place.

## Worked synthetic example (not a human review)

Input: `Register by 4 May 2027; the workshop "Data Skills" will be held on 9 May 2027 at 10:00 AM in Room B12.`

Category Workshop; name `Data Skills`; date `9 May 2027`; time `10:00 AM`; venue `Room B12`. The first date is a registration deadline. The field evidence must match the stored paragraph exactly. These are authored fixture expectations, not collected or human-verified labels.
