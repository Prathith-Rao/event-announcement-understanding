# Version-2 viva notes

**What changed from version 1?** Five event categories became 19; the synthetic corpus grew from 80 to 11,922 records. A CRF now learns name/venue BIO tags from 4,000 train examples. A word/character classifier, context interpretation and field-level notices address the original narrow keyword gate and phrase rules.

**What is actually trained?** NLTK Naive Bayes and three TF-IDF logistic classifiers train on 7,152 records. The CRF uses a deterministic 4,000-record subset of that same training partition. POS tagging uses a standard pretrained NLTK resource; we do not claim to train it.

**Why keep NLTK?** Punkt segmentation, Treebank word/evidence spans, POS tags, POS-aware WordNet lemmas, explicit EVENT/VENUE RegexpParser grammars, Naive Bayes, frequency distributions and collocations all do actual work. NLTK POS tags also supply supervised sequence features.

**What is a CRF doing?** It labels each token O, B-NAME, I-NAME, B-VENUE or I-VENUE using word/POS/shape/context features and dependencies between adjacent labels. Contiguous token predictions become exact original spans. It can generalize some boundaries but is not semantic omniscience.

**Why both rules and sequence learning?** Rules recognize explicit temporal/labelled evidence and make conservative decisions. The sequence model proposes additional phrases from learned context. A/B extraction uses identical inputs and normalization; only hybrid adds linguistic/CRF candidates.

**Why do dates work better than titles?** Dates have relatively regular surface forms. Titles have open vocabulary, implicit boundaries and varied syntactic roles. The held-out test exposes that difference; the report does not conceal it.

**Is the larger dataset real?** No. It is explicitly synthetic with programmatically authored labels and spans, human null, and no invented source URLs. The separate real pilot has 26 retained candidates and no accepted human review at creation.

**Why remove synthetic warnings?** Provenance is relevant to methodology, evaluation and exports, not a repetitive warning on every extraction. The UI still gives necessary ambiguity/missing-data notices. We did not relabel synthetic data as real or call automatic labels human verified.

**How are splits protected?** Seventy known construction groups keep template variants, untitled and negative constructions within partitions. Name/venue prefix pools are partitioned. Train alone supplies feature vocabulary and IDF. C in {1,4} uses validation. Final evaluation is explicit and frozen; errors are not tuned afterward.

**Does zero group overlap prove no leakage?** No. Known families and normalized exact duplicates are checked. Purpose descriptions and title themes recur, and paraphrases can escape a grouping scheme. We disclose those limitations and do not equate synthetic accuracy with real-world generalization.

**Why not choose NB if it scores higher?** It remains selectable and can outperform LR on the authored benchmark. The default is selected among LR variants and includes character features for surface variation. We do not claim that this choice is proven superior overall or calibrated.

**What does hybrid_context mean in the classification table?** The final system also interprets explicit format in event context and rejects general discussion. That result includes rules and must not be presented as the standalone learned classifier.

**How do scores work?** LR predict_proba or NB posterior estimates are displayed only in an optional analysis view. They are uncalibrated model outputs, not verified probabilities of correctness.

**How are dates conservative?** No missing year, timezone or AM/PM is invented. Relative dates require a supplied reference. Explicit same-month ranges can normalize using the month/year inside the raw range. Conflicting date candidates remain a field-level decision for the user.

**What happens to missing details?** The value stays null with a short intimation beside its output field. User corrections export without stale source offsets or normalization. Automatic suggestions remain auditable.

**Does it understand every sentence?** No. It handles a wider range of common English announcements and informal notices. Complex titles, unusual discourse, open-set events and multiple-event schedules remain difficult. Editable evidence-backed output is deliberate.

**What is the contribution?** Applied NLP integration with actual training, language analysis, evidence-based extraction, reproducible comparisons, source/review integrity and a working local interface. It is not a new algorithm or a guarantee of universal recognition.

**What remains academic human work?** Independent annotation, adjudication/agreement, field-rich real-data evaluation, course disclosure and genuine team/certification details.
