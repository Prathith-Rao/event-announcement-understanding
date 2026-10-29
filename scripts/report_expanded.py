"""Generate the version-2 report from saved measurements, never invented scores."""
import json
from pathlib import Path
from event_nlp.config import DATA, REPORTS, ROOT, CATEGORIES
from event_nlp.taxonomy import DEFINITIONS


def read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def table(headers, rows):
    return "| " + " | ".join(headers) + " |\n|" + "|".join("---" for _ in headers) + "|\n" + "".join("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in row) + " |\n" for row in rows)


def main():
    directory = REPORTS / "expanded_v2"
    manifest = read(directory / "manifest.json")
    data = read(DATA / "expanded_v2/manifest.json")
    real = read(DATA / "collection_summary.json")
    validation = read(directory / "validation_metrics.json")
    final = read(directory / "test_metrics.json")
    corpus = read(directory / "corpus/summary.json")
    performance = read(directory / "performance.json")
    classification = []
    for partition, metrics in [("validation", validation), ("held-out test", (final or {}).get("models"))]:
        for model, values in (metrics or {}).items():
            classification.append([partition, model, values["sample_count"], *[f"{values[key]:.4f}" for key in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]]])
    classification_table = table(["Partition", "Model", "n", "Accuracy", "Macro P", "Macro R", "Macro F1"], classification)
    extraction_tables, error_tables = [], []
    for partition in ["validation", "test"]:
        result = read(directory / f"extraction_{partition}.json")
        if not result:
            continue
        rows = [[method, field, *[f"{values[key]:.4f}" for key in ["precision", "recall", "f1", "exact_match"]], values["present_gold"]]
                for method in ["rules", "hybrid"] for field, values in result[method]["fields"].items()]
        extraction_tables.append(f"### {partition.capitalize()} extraction ({result['hybrid']['sample_count']} authored examples)\n\n" +
                                 table(["Method", "Field", "P", "R", "F1", "Exact", "Gold present"], rows) +
                                 f"\nComplete-record accuracy: rules **{result['rules']['complete_record_accuracy']:.4f}**, hybrid **{result['hybrid']['complete_record_accuracy']:.4f}**.\n")
        errors = [[method, error["id"], error["field"], (error["expected"] or {}).get("raw"), (error["predicted"] or {}).get("raw"), error["text"][:180]]
                  for method in ["rules", "hybrid"] for error in result[method]["errors"]]
        error_tables.append(f"### Actual {partition} errors\n\n" + table(["Method", "ID", "Field", "Expected", "Predicted", "Input excerpt"], errors[:12]))
    report = f"""# Event Announcement Understanding Using a Hybrid NLP Approach

Version 2 course AAT report draft. Student names, identifiers, guide details, signatures, certificates and declarations remain for genuine human completion.

## 1. Problem statement

The application recognizes event categories and extracts name, date, time and venue from English announcements while preserving exact source evidence. Version 1 had five categories, 80 synthetic development records and narrow phrase rules. Its keyword gate could veto the learned classifier and reject unfamiliar sentences. The revised system targets invitations, paragraphs, informal plans, notices and labelled details with a broader taxonomy and learned span extraction. Arbitrary language is not guaranteed to be understood.

The user authorized broader categories, substantial synthetic data, revised extraction and a quieter interface. Missing or ambiguous details are now communicated beside their fields. Repeated synthetic-training banners were removed from the main flow; provenance remains in data, methodology, evaluation and exports.

## 2. Design approach

### 2.1 Categories and overlap

{table(["Category", "Definition"], DEFINITIONS.items())}

An internal **Not an event** label supports rejection of general discussion. Primary format is interpreted in event context: a workshop about careers remains Workshop, a recruitment drive with a talk remains Career event, and “Seminar Room” is a venue rather than a seminar cue. Specific hackathons and sporting fixtures have their own categories. Delivery platforms are not themselves category evidence. Explicit format interpretation is recorded separately from the statistical prediction so the final system is distinguishable from standalone classifier scores.

### 2.2 Substantive NLTK and supervised learning

NLTK English Punkt segments sentences; Treebank token spans retain original characters; Penn POS tags support candidate RegexpParser grammars and supervised sequence features. Classification-only preprocessing uses POS-aware WordNet lemmatization and stopword filtering without modifying extraction text. NLTK NaiveBayesClassifier is trained on 1,500 train-derived binary lemma features. FreqDist, collocations, POS distributions and representative chunks support training-only corpus analysis.

Raw and lemmatized TF-IDF word unigram/bigram logistic pipelines are compared on identical partitions. A further word/character 3–5-gram pipeline supports surface-form variation. The default is the best validation LR variant; Naive Bayes is also available and may outperform it on this authored corpus. No overall superiority of the default over Naive Bayes is claimed. Different representations make the NB-versus-LR comparison less controlled than raw-versus-lemmatized LR.

A conditional random field (CRF) is actually trained on **{manifest['sequence_training_records']}** train-only BIO-labelled announcements. Features include NLTK POS, word shape, casing, suffixes and a two-token context in each direction [1]. It proposes event-name and venue spans; context and evidence rules select them. Explicit title/venue labels and quoted titles outrank weak phrase candidates. This extends the original rules-plus-chunking approach without a transformer, GPU or external inference.

### 2.3 Data and reproducibility

The expanded corpus contains **{data['records']:,}** explicitly synthetic records: 600 per event category plus deduplicated negative examples. All have authored expected labels/spans and no invented human review. The real pilot remains separate at **{real['actual_count']}** retained candidates and **{real['human_reviewed']}** accepted human reviews.

Actual split sizes are **{manifest['split_sizes']}**, across **{manifest['audit']['groups']}** construction groups, with recorded group and normalized-exact-duplicate overlap zero. Known template variants, untitled constructions and negative constructions stay within one partition. Proper-name and venue-prefix pools are partitioned; standard platforms and category vocabulary necessarily recur. Title themes and purpose descriptions also recur, so this is not a test of wholly unseen topics or independent natural data.

Vocabulary and IDF fit only on train. Both LR settings C=1 and C=4 are selected on validation macro F1. NB feature selection uses train only. CRF uses a deterministic 4,000-record train subset. Source/model hashes, assignments, library versions, features and actual selection are saved. The final test is evaluated explicitly after freezing; its errors are recorded without subsequent tuning. Original version-1 results/challenges remain preserved and were not used as a new tuning set.

Synthetic construction randomizes field absence, sentence order, formats, case, deadlines and address distractors. Some location/type combinations are intentionally difficult or implausible. Authored descriptions and repeated themes make the task easier than independent real-world data. Group/exact audits do not prove that every paraphrase has been detected. Human review and independently sourced evaluation remain necessary for academic claims about real-data generalization.

## 3. System requirements

Python 3.13.3, NLTK, scikit-learn, sklearn-crfsuite/python-crfsuite, FastAPI, React and Vite. CPU only. Full dependency locks and project-local NLTK setup are provided. No database, authentication, paid API, GPU, external LLM inference or transformer is required.

## 4. Implementation and evaluation

### 4.1 Recognition and field handling

The application combines model predictions with explicit primary-format context rather than making keyword ties a prerequisite for inference. Rules recognize date/time formats, deadline roles, relative dates, ranges and location contexts. NLTK/CRF provide additional name and venue candidates. Exact spans always address the original input.

Relative dates require a reference date; missing years are not invented. Explicit ranges such as “3–5 November 2028” normalize as an ISO interval using only month/year stated inside that range. Bare hours retain raw text with an AM/PM note. Weekdays adjacent to an absolute date act as modifiers rather than competing dates. Organizer addresses are excluded. Multiple conflicting values remain editable with field notices. Clearly multiple-event text still requires separate analysis rather than pretending there is one correct date/venue.

Missing values are null and receive an inline intimation. General text and multiple events retain necessary global notices. Model provenance is recorded in evaluation/methodology/export metadata. Edited exports invalidate stale evidence/normalization and separately preserve automatic suggestions. API schemas validate response shapes; empty input, backend errors, missing models/resources and a client timeout are handled explicitly.

### 4.2 Classification

All results below are **synthetic benchmark measurements**, not human-reviewed real-data accuracy.

{classification_table}

The end-to-end hybrid-context row, when available, includes explicit-format and non-event interpretation; it must not be presented as the standalone statistical classifier. Per-class supports, full confusion matrices and errors are saved. Character features and lemmatization are not assumed to improve performance; compare measured rows. Very high NB scores reflect easy recurring authored lexical signals and do not demonstrate general deployment reliability.

### 4.3 Controlled extraction

Rules and hybrid use identical held-out inputs, category interpretation and normalization. Hybrid adds NLTK chunk and trained CRF candidates. Wrong present values count as both FP and FN when gold exists; absent/absent is correct absence, not TP. Complete-record accuracy requires all four fields. Metrics include absent examples, so present-gold supports are reported. See METRICS.md.

{''.join(extraction_tables)}

### 4.4 Training-only corpus analysis

{f"Training corpus: {corpus['records']} records, {corpus['raw_tokens']} raw tokens / {corpus['raw_vocabulary']} types; after classification preprocessing {corpus['preprocessed_tokens']} tokens / {corpus['preprocessed_vocabulary']} types." if corpus else "Training-only corpus artifacts are generated by scripts.corpus."}

![Class counts and lengths](../reports/expanded_v2/corpus/coverage_lengths.png)

![POS distributions](../reports/expanded_v2/corpus/pos_distribution.png)

Frequent/distinctive words, sentence-local PMI collocations with minimum frequency 2, POS distributions, candidate patterns, exact representative chunk spans and interpretations are in reports/expanded_v2/corpus. Recurring type descriptions can dominate features; chunk counts are not proof of extraction quality.

### 4.5 Actual errors and limits

{''.join(error_tables)}

All per-record predictions, candidates, warnings and evidence are retained for debugging. Remaining weaknesses include title boundaries in unusual constructions, unfamiliar generic venues, complicated discourse, open-set categories, ambiguous dates and domain shift. The application provides useful partial fields and notices rather than fabricating missing details. Perfect understanding of every sentence is not claimed.

### 4.6 Software verification

The expanded regression suite covers every new category, informal/short sentences, explicit-format versus venue distractors, exact spans, calendars, missing/ambiguous fields, data splits, actual trained artifacts, API validation/failures and export corrections. Browser checks cover the revised main flow and responsive layouts. Actual executed checks are in VERIFICATION.md.

{f"Local warm HTTP benchmark: median {performance['median_ms']:.1f} ms, p95 {performance['p95_ms']:.1f} ms across {performance['requests']} short requests; this excludes browser rendering and is not a hardware-independent guarantee." if performance else "Performance measurements are not yet recorded."}

![Revised application](screenshots/v2-desktop.jpg)

## 5. Conclusion

Version 2 replaces a tiny, narrow recognizer with a substantially larger trained system, 19 event categories, a trained sequence extractor, broader temporal/location handling and field-level feedback. Measured gains and failures are recorded rather than assumed. This is an applied NLP integration, not a new learning algorithm or a guarantee of universal sentence understanding. Real-data annotations, independent annotation agreement, team-specific details and course disclosure still require genuine human work.

## References

1. sklearn-crfsuite, supervised sequence tagging tutorial and feature construction. https://sklearn-crfsuite.readthedocs.io/en/latest/tutorial.html
2. Bird, Klein and Loper, Natural Language Processing with Python, chapters 5–7. https://www.nltk.org/book/ch05.html ; https://www.nltk.org/book/ch06.html ; https://www.nltk.org/book/ch07.html
3. scikit-learn, text feature extraction and leakage prevention. https://scikit-learn.org/stable/modules/feature_extraction.html ; https://scikit-learn.org/stable/common_pitfalls.html
4. Original announcement URLs and retrieval records: data/real.jsonl and data/source_log.jsonl.
5. Supplied course PDFs remain unchanged. Automated assistance and human review record: ASSISTANCE_AND_REVIEW.md.
"""
    (ROOT / "docs/AAT_REPORT.md").write_text(report, encoding="utf-8")
    (REPORTS / "RESULTS.md").write_text("# Version-2 measured results\n\nSynthetic benchmark; see the report for limitations.\n\n" + classification_table + "\n" + "".join(extraction_tables + error_tables), encoding="utf-8")
    print("Updated version-2 AAT report and measured-results tables.")


if __name__ == "__main__":
    main()
