# Frozen model evaluation on reviewed real text

59 accepted;19 unresolved;4 excluded. One human reviewer, source spans validated. No fitting/tuning.

|Model|Accuracy|Macro F1 (12 supported labels)|Macro F1 (fixed 20)|
|---|---:|---:|---:|
|majority|0.1864|0.0262|0.0157|
|keywords|0.5424|0.4984|0.2991|
|nltk_nb|0.2034|0.2844|0.1707|
|logistic_raw|0.4237|0.3762|0.2257|
|logistic_preprocessed|0.3729|0.3988|0.2393|
|logistic_word_char|0.4746|0.4037|0.2422|
|hybrid_context|0.5424|0.4770|0.2862|

34 newly collected post-freeze accepted records are reported separately in metrics.json; the other25 are earlier pilot records.

Rules and hybrid complete-record accuracy:0.3559. Field F1:name0.2353,date0.3529,time0.8000,venue0.3077. Present supports:29,8,3,12. Two negative examples:default/hybrid non-event recall0.

No inter-annotator agreement or population-level generalization claim; source clusters and limited coverage constrain interpretation.