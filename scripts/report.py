"""Write a report draft from saved artifacts; never synthesize performance numbers."""
import json
from pathlib import Path

from event_nlp.config import DATA, REPORTS, ROOT, CATEGORIES, FIELDS
from event_nlp.data import read_jsonl


def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def mdtable(headers, rows):
    return "| " + " | ".join(headers) + " |\n|" + "|".join("---" for _ in headers) + "|\n" + "".join("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in row) + " |\n" for row in rows)


def main():
    collection = load(DATA / "collection_summary.json") or {}
    pilot = load(REPORTS / "pilot_audit.json") or {}
    manifests = {mode: load(REPORTS / mode / "manifest.json") for mode in ["development", "provisional", "reviewed"]}
    sections = []
    for mode, manifest in manifests.items():
        if not manifest:
            continue
        validation = load(REPORTS / mode / "validation_metrics.json")
        test = load(REPORTS / mode / "test_metrics.json")
        sections.append(f"### {mode.capitalize()} classification: {manifest['label_status']}\n\n")
        sections.append(f"Actual splits: {manifest['split_sizes']}; independent groups {manifest['audit']['groups']}; group overlap {manifest['audit']['group_overlap']}. NB vocabulary: {manifest['nb_vocabulary_size']} training-derived lemmas. Selection: `{manifest['selection']}`.\n\n")
        metrics_rows = []
        for partition, metrics in [("validation", validation), ("test", (test or {}).get("models"))]:
            if metrics:
                for name, values in metrics.items():
                    metrics_rows.append([partition, name, *[f"{values[key]:.3f}" for key in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]], values["sample_count"]])
        sections.append(mdtable(["Partition", "Model", "Accuracy", "Macro P", "Macro R", "Macro F1", "n"], metrics_rows))
        raw, processed = validation["logistic_raw"]["macro_f1"], validation["logistic_preprocessed"]["macro_f1"]
        sections.append(f"\nValidation preprocessing macro-F1 difference (preprocessed minus raw): **{processed - raw:+.3f}**. This measures this partition only. There is no basis to claim preprocessing is universally better.\n\n")
        sections.append("Partition class coverage (absent classes have zero support):\n\n" + mdtable(["Class", "Train", "Validation", "Test"], [[category, *[manifest["audit"]["coverage"][split].get(category, 0) for split in ["train", "validation", "test"]]] for category in CATEGORIES]))
        errors = load(REPORTS / mode / "validation_errors.json") or []
        if errors:
            sections.append("\nActual validation disagreements (truth here means the stated label source, not necessarily human gold):\n\n" + mdtable(["Record", "Model", "Target", "Prediction", "Input excerpt"], [[row["id"], row["model"], row["truth"], row["prediction"], row["text"][:200]] for row in errors[:8]]))
        else:
            sections.append("\nNo validation classification errors were observed in the saved artifact. This does not establish generalization.\n")
        corpus = load(REPORTS / mode / "corpus/summary.json")
        if corpus:
            sections.append(f"\nTraining-only corpus: {corpus['records']} records, {corpus['raw_tokens']} raw tokens / {corpus['raw_vocabulary']} raw types, {corpus['preprocessed_tokens']} preprocessed tokens / {corpus['preprocessed_vocabulary']} preprocessed types. Class counts: {corpus['class_counts']}.\n\n")
            sections.append(f"![Training class counts and lengths](../reports/{mode}/corpus/coverage_lengths.png)\n\n![POS proportions](../reports/{mode}/corpus/pos_distribution.png)\n\n")
            sections.append(f"Full frequent/distinctive words, minimum-frequency-2 sentence-local PMI collocations, POS distributions and candidate chunk patterns are in `reports/{mode}/corpus/`. Interpretations are in its `interpretation.md`; candidate counts are not successful extractions.\n\n")
        sections.append(f"Confusion matrices (counts, with an ABSTAIN column) are saved as `reports/{mode}/confusion_validation_*.png`; test matrices exist only after explicit test evaluation.\n\n")
    extraction_sections = []
    for partition in ["development", "final"]:
        experiment = load(REPORTS / f"extraction_{partition}.json")
        if not experiment:
            extraction_sections.append(f"### {partition.capitalize()} extraction\n\nNot yet evaluated.\n\n")
            continue
        extraction_sections.append(f"### {partition.capitalize()} extraction — synthetic, AI-authored expectations\n\nIdentical {experiment['hybrid']['sample_count']} inputs, normalization rules and reference dates for both methods.\n\n")
        extraction_sections.append(mdtable(["Method", "Field", "P", "R", "F1", "Exact", "Raw exact", "Gold present"], [[method, field, *[f"{metric[key]:.3f}" for key in ["precision", "recall", "f1", "exact_match", "raw_exact_match"]], metric["present_gold"]] for method in ["rules", "hybrid"] for field, metric in experiment[method]["fields"].items()]))
        extraction_sections.append("\n" + mdtable(["Method", "Complete record", "Unsupported handling", "Missing warnings", "Ambiguity warnings"], [[method, *[f"{experiment[method][key]:.3f}" if experiment[method][key] is not None else "n/a" for key in ["complete_record_accuracy", "unsupported_detection_accuracy", "missing_warning_accuracy", "ambiguity_warning_accuracy"]]] for method in ["rules", "hybrid"]]))
        delta = experiment["hybrid"]["complete_record_accuracy"] - experiment["rules"]["complete_record_accuracy"]
        extraction_sections.append(f"\nComplete-record delta (hybrid minus rules): **{delta:+.3f}**. A tiny authored set cannot establish real-data superiority.\n\n")
        failures = [[method, error["id"], error["field"], (error["expected"] or {}).get("raw"), (error["predicted"] or {}).get("raw"), error["text"][:180]] for method in ["rules", "hybrid"] for error in experiment[method]["errors"]]
        extraction_sections.append("Actual failures from saved outputs:\n\n" + mdtable(["Method", "ID", "Field", "Expected", "Predicted", "Input excerpt"], failures[:10]) if failures else "No extraction mismatches observed on this fixture set. Expectations still require human audit.\n")
        extraction_sections.append("\n\n")
    source_table = mdtable(["Institution / organization", "Records"], collection.get("institutions", {}).items())
    category_table = mdtable(["Proposed category", "Count (not human gold)"], [[category, collection.get("proposed_categories", {}).get(category, 0)] for category in CATEGORIES + ["needs_review"]])
    report = f"""# Event Announcement Understanding Using a Hybrid NLP Approach

Natural Language Processing course AAT — working draft, generated from actual saved artifacts.

Student names, identifiers, team membership, guide assignment, signatures, certificate and declaration are intentionally unfilled. The team must supply accurate details and complete course-specific disclosure. This draft follows the supplied report template's chapter organization. It does not attest to certification or institutional approval.

## Abstract

We implement a local English announcement-understanding application using NLTK, classical supervised learning, contextual rules and exact source evidence. The system returns five-way category suggestions, event name/date/time/venue, ambiguity warnings and an inspectable linguistic trace. Evaluation compares majority and keyword baselines, NLTK Naive Bayes, and raw/preprocessed TF-IDF logistic regression, plus a rules-versus-chunking extraction ablation. The available real corpus has {collection.get('actual_count',0)} retained records and {collection.get('human_reviewed',0)} accepted human reviews; real-data final performance is therefore pending. Synthetic experiments demonstrate operation and scenario behavior; their results must not be described as measured real-world accuracy.

## 1. Problem statement

### 1.1 Motivation and scope

Institutional event notices mix names, dates, deadlines, times and locations in prose. Manually transferring them risks treating registration deadlines as occurrence dates or filling details from assumptions. We focus on one English announcement with primary-purpose categories Workshop, Seminar, Competition, Meeting and Cultural event. Multiple-event schedules and unrelated inputs require abstention/review. This is an applied NLP contribution through integration and evaluation, not a new algorithm.

### 1.2 Objectives and actual work

Deliver exact field evidence, conservative normalization, a learned classifier, explicit NLTK linguistic processing, training-only corpus analysis, leakage-aware evaluation and a small local interface. Ethical handling of uncertain labels and honest limitations is part of the system design. No transformer was added merely to match other teams; the student-readable CPU baselines directly address the instructional question.

## 2. Design approach

### 2.1 Hybrid pipeline and rationale

1. Preserve the untouched input; segment with NLTK English Punkt and tokenize with Treebank span tokenization.
2. Assign Penn POS tags using the downloaded English perceptron model. Two explicit RegexpParser grammars propose EVENT and VENUE phrases [1].
3. Independently detect date/time expressions and labelled/quoted phrases. Local clause context separates registration/deadline and occurrence roles. Context selects single fields and exact `[start,end)` evidence; ambiguous choices remain null.
4. For classification only, compare raw text against alphabetic lowercased tokens with stopword filtering and POS-aware WordNet lemmatization. Train NB on binary lemma features [2], and logistic regression on sublinear TF-IDF word unigrams/bigrams [3,4].
5. Expose results, warnings, model status and linguistic evidence through FastAPI and React. User edits affect exports but never silently create dataset gold.

Rules suit recognizable dates/times and exact evidence. Learned lexical models support category generalization when sufficient reviewed data exists. Chunking proposes unfamiliar proper-name titles/venues but can merge dates, titles and locations or capture generic noun phrases. Chunk candidates alone are not entities. Training only the classifiers is distinct from using a pretrained POS tagger.

### 2.2 Category and overlap definitions

Workshop: participant practice/training. Seminar: speaker-led knowledge presentation. Competition: judging/ranking/winners. Meeting: organizational decisions/planning. Cultural event: artistic performance/celebration. Prioritize the announcement's primary purpose; judged cultural contests are Competition. Mixed equal-purpose inputs require review. Do not use metadata or a “seminar room” as a gold category. Full boundary rules and annotation examples are in `ANNOTATION_GUIDE.md`.

### 2.3 Collection, annotation and corpus analysis

Public-source HTML collection checks robots, uses at least 1.5 seconds between requests per hostname, respects longer crawl delays, and skips redirects/denied/unavailable sources. Inputs are single natural paragraphs, not manufactured text assembled from structured fields. The first 25-candidate pilot was screened before expansion. Current retained count: **{collection.get('actual_count',0)}**; excluded: **{collection.get('excluded_records',0)}**; sources: **{len(collection.get('institutions',{}))}**; independent automatic groups: **{collection.get('independent_groups',0)}**. The attempted 300-record expansion is a requested limit, not a claimed achievement. The discovery frontier was exhausted at the actual accessible yield.

{source_table}

{category_table}

Automatic proposed field coverage: `{pilot.get('proposed_field_coverage',{})}`. This is not gold coverage or recall. Many event pages keep times and venues in tables outside prose. This creates a serious field-coverage limitation, especially for time; a larger, more balanced, field-rich reviewed corpus remains necessary. Repeated annual competition pages concentrate the source distribution and may share templates. Exclusions, encoding corrections and original sources are preserved separately. Human review and agreement/adjudication have not been fabricated.

### 2.4 Reproducibility, model selection and leakage

Group supplied templates, same canonical source event pages, exact normalized duplicates and sequence-similar texts (threshold 0.84) before splitting. Use seed 42 and group allocation targeting 60/20/20 while favoring class coverage. Because indivisible groups vary in size, actual counts differ. Label-based coverage selection does not use predictions or test outcomes. The threshold can miss paraphrases; humans must inspect template groups before final reviewed experiments.

NB selects up to 1500 lemmas by training-document frequency. Both logistic pipelines fit their vocabulary and IDF on training only, and select C from {{0.5,2.0}} on validation macro F1. Test examples are not predicted during training. Save split assignments, model/data hashes and library versions. NB versus logistic changes representation and classifier; raw versus preprocessed logistic uses the same split and model family. We follow standard training-only transformation practice [5]. Final evaluation is explicit and frozen; no provisional real final-test command is exposed.

## 3. System requirements

### 3.1 Hardware

CPU-only local system. No GPU required. The current small corpus is manageable on an ordinary Windows laptop; large-scale speed/memory measurements have not been collected, so no unmeasured hardware guarantee is made.

### 3.2 Software

Python 3.13.3 and Node 22.16.0 were used. Direct dependencies and full Python lockfile are included; React/Vite dependencies use npm's lockfile. NLTK resources are downloaded once and used locally. The API, UI and trained local artifacts require no paid service or model inference endpoint. Exact setup/training/evaluation/startup commands are in README.

## 4. Implementation

### 4.1 Algorithm and modules

`linguistics.py`: sentence and token spans, POS tags, EVENT/VENUE chunk grammars, classification-only lemmatization. `extraction.py`: conservative date/time candidates, context roles, phrase selection and warnings. `classification.py`: keyword baseline and training-derived NB features. `data.py`: grouping, deterministic partitions, annotation validation and leakage assertions. `experiment.py`: genuine supervised fitting and validation selection. `evaluation.py`: explicit metric accounting. `corpus.py`: train-only tables/plots. FastAPI is a thin adapter; React provides input, editable fields, evidence, exports and saved methodology/results.

Pseudocode:

```text
read original paragraph and optional reference date
tokenize and POS-tag; parse EVENT and VENUE candidates
detect date/time/quoted/labelled candidates with exact spans
assign occurrence/deadline roles using local clauses
abstain on unsupported/multiple-event input; warn on ambiguous candidates
select fields without inventing absent values
classify using a trusted local trained model or labelled keyword fallback
return original evidence, warnings, optional linguistic trace and editable result
```

### 4.2 Metrics and experiments

Classification: accuracy; macro precision/recall/F1 over five classes with zero division zero; per-class support and matrices including ABSTAIN. Extraction: a correct present value is TP; a false value is FP and, when gold exists, FN; both-null is correct absence, not TP. Wrong present strings count as both FP and FN. Field exact match divides by all examples; complete-record accuracy requires all four fields. Raw and normalized equality are separately recorded; dates only normalize when explicitly supported. Full formulas and missing/ambiguity metric definitions are in `METRICS.md` and follow standard classification metric terminology [6].

{''.join(sections)}

Provisional validation measures agreement with automatic suggestions, which can be circular for the keyword baseline. It does **not** establish correctness. Classes with one record cannot be represented across three disjoint partitions; coverage tables show the actual gaps. Synthetic templates share recurring topic words and titles, making their classification unusually easy. No statistical significance or broad superiority claim is warranted.

{''.join(extraction_sections)}

The development challenge was used to debug rules. It cannot be treated as an untouched estimate. The separate final synthetic challenge is evaluated once after freezing, with errors retained and no subsequent rule tuning. Its gold spans were authored with automated assistance and still require human audit. A reviewed-real extraction comparison is pending.

### 4.3 Interface and verification

The application has announcement input, optional reference date, clearly labelled synthetic samples, classifier/extractor options, editable results, JSON/CSV export and source highlighting. Edited exports preserve automatic suggestions but invalidate stale evidence/normalization for changed fields. NLP inspection exposes tokens/POS/chunks. Dataset annotation is a separate CSV workflow. Empty input, unavailable models, missing resources and backend failures have explicit handling. Automated test counts and browser verification are recorded in `VERIFICATION.md`.

![Local application, desktop verification](screenshots/desktop-analysis.jpg)

![Local application, mobile breakpoint verification](screenshots/mobile-analysis.jpg)

### 4.4 Error analysis and limits

The tables include actual saved failure examples. The rules-only method cannot recover all unfamiliar unquoted titles/venues. Chunking can recover some of these but can also swallow context or suggest a generic noun phrase; positive context filters reduce, not eliminate, this. The tagger can mislabel punctuation and capitalized commands, and WordNet lemmas can be linguistically inappropriate in context. Deadline detection is local and can fail across complex discourse. Multiple-event detection relies on recognizable event-format/date clauses. Date ranges and implied metadata remain review cases. Real prose often omits structured fields, and the reviewed corpus is still absent.

## 5. Conclusion

The operational application combines substantive NLTK processing, actual supervised training, contextual information extraction, exact evidence, reproducible artifacts and an auditable review workflow. Measured preprocessing/chunking effects are those in the saved tables, including zero differences and errors. This is an applied NLP course project, not a new algorithm. Completing human annotation, improving real field/category coverage, independently reviewing challenge expectations, and running a frozen reviewed-real final evaluation are required before claiming academically final performance. Team details, certification/declaration and course disclosure need genuine human completion.

## References

1. Bird, S., Klein, E., and Loper, E. *Natural Language Processing with Python*, chapter 7, information extraction and chunking. https://www.nltk.org/book/ch07.html
2. Bird, S., Klein, E., and Loper, E. *Natural Language Processing with Python*, chapter 6, supervised classification and Naive Bayes. https://www.nltk.org/book/ch06.html
3. scikit-learn documentation, text feature extraction. https://scikit-learn.org/stable/modules/feature_extraction.html
4. scikit-learn documentation, LogisticRegression. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
5. scikit-learn documentation, common pitfalls and data leakage. https://scikit-learn.org/stable/common_pitfalls.html
6. scikit-learn documentation, model evaluation and scoring. https://scikit-learn.org/stable/modules/model_evaluation.html
7. NLTK WordNetLemmatizer documentation. https://www.nltk.org/api/nltk.stem.wordnet.html
8. Source announcement URLs and retrieval audit: `data/real.jsonl` and `data/source_log.jsonl` (actual collection date stored per record).
9. Local course references supplied by the team: `NLP_course_Rubrics.pdf`; `UG_CSE-7th sem-NLP AAT-ReportFormat-Sept 2026.pdf`. Used as reference material, not project data or evidence of approval.

Automated assistance and human review disclosure: `ASSISTANCE_AND_REVIEW.md`.
"""
    (ROOT / "docs/AAT_REPORT.md").write_text(report, encoding="utf-8")
    metrics_md = "# Actual saved evaluation tables\n\n" + "".join(sections + extraction_sections)
    (REPORTS / "RESULTS.md").write_text(metrics_md, encoding="utf-8")
    print("Generated docs/AAT_REPORT.md and reports/RESULTS.md from saved artifacts.")


if __name__ == "__main__":
    main()
