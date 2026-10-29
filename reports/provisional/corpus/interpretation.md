# Training corpus interpretation (provisional)

Only 15 assigned training records contribute to these linguistic statistics. Class counts: {'Workshop': 5, 'Competition': 7, 'Seminar': 1, 'Cultural event': 1, 'Meeting': 1}.
Raw token count 865 and vocabulary 319 become 410 and 218 after filtering and POS-aware lemmatization. Lower vocabulary is not evidence of better classification; compare held-out raw/preprocessed results.

`distinctive_words.csv` ranks add-one-smoothed log class-versus-rest token probability ratios. These are descriptive training associations, not causal effects. Repeated format words can reveal template artifacts. `collocations.csv` uses sentence-local PMI and minimum frequency 2; rare pairs remain unstable at this corpus size. `pos.csv` shows linguistic composition by category; formatting and genre confound any class-specific interpretation.

`chunk_patterns.csv` reports candidate EVENT and VENUE grammars, not successfully extracted or manually confirmed entities. Proper-noun sequences can identify unfamiliar titles and locations; generic noun phrases, addresses, and names of speakers produce false candidates. Selection context is therefore necessary. The controlled extraction comparison, rather than chunk counts, measures usefulness.

Observed top five preprocessed words per category: {'Workshop': [('workshop', 6), ('university', 3), ('academic', 2), ('education', 2), ('october', 2)], 'Seminar': [('national', 1), ('seminar', 1), ('culture', 1), ('tradition', 1), ('tribe', 1)], 'Competition': [('innovation', 14), ('competition', 10), ('project', 9), ('student', 9), ('hsuhk', 8)], 'Meeting': [('meeting', 2), ('first', 1), ('college', 1), ('faculty', 1), ('academic', 1)], 'Cultural event': [('come', 1), ('together', 1), ('make', 1), ('festival', 1), ('truly', 1)]}.

Observed high-PMI collocations after the minimum-frequency-2 filter: [{'bigram': 'creative concepts', 'frequency': 2, 'pmi': 8.44086916761087}, {'bigram': 'entrepreneurship wucie', 'frequency': 2, 'pmi': 8.44086916761087}, {'bigram': 'jieh yee', 'frequency': 2, 'pmi': 8.44086916761087}, {'bigram': 'leadership iysl', 'frequency': 2, 'pmi': 8.44086916761087}, {'bigram': 'should demonstrate', 'frequency': 2, 'pmi': 8.44086916761087}, {'bigram': 'strategic partners', 'frequency': 2, 'pmi': 8.44086916761087}]. Their recurrence motivates testing bigram features, but templates and institutional names can dominate. This is a training-data observation, not held-out evidence for choosing a model.

`chunk_examples.csv` gives actual training input spans and POS patterns so each representative chunk can be checked. `lengths_by_category.png` shows the class-conditional length distributions; small supports and synthetic construction constrain interpretation.

If this is development mode, all these examples are AI-authored synthetic text. Balanced class counts and clean vocabulary reflect fixture construction and do not establish performance on real institutional announcements. Real-data training analysis will only be academically final after human review and a reviewed-mode run.
