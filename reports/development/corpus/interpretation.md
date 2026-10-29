# Training corpus interpretation (development)

Only 50 assigned training records contribute to these linguistic statistics. Class counts: {'Workshop': 10, 'Seminar': 10, 'Competition': 10, 'Meeting': 10, 'Cultural event': 10}.
Raw token count 1654 and vocabulary 187 become 775 and 119 after filtering and POS-aware lemmatization. Lower vocabulary is not evidence of better classification; compare held-out raw/preprocessed results.

`distinctive_words.csv` ranks add-one-smoothed log class-versus-rest token probability ratios. These are descriptive training associations, not causal effects. Repeated format words can reveal template artifacts. `collocations.csv` uses sentence-local PMI and minimum frequency 2; rare pairs remain unstable at this corpus size. `pos.csv` shows linguistic composition by category; formatting and genre confound any class-specific interpretation.

`chunk_patterns.csv` reports candidate EVENT and VENUE grammars, not successfully extracted or manually confirmed entities. Proper-noun sequences can identify unfamiliar titles and locations; generic noun phrases, addresses, and names of speakers produce false candidates. Selection context is therefore necessary. The controlled extraction comparison, rather than chunk counts, measures usefulness.

Observed top five preprocessed words per category: {'Workshop': [('practical', 10), ('venue', 7), ('workshop', 6), ('python', 6), ('practice', 6)], 'Seminar': [('venue', 7), ('seminar', 6), ('climate', 6), ('research', 6), ('speaker', 6)], 'Competition': [('award', 10), ('venue', 7), ('competition', 6), ('design', 6), ('challenge', 6)], 'Meeting': [('meeting', 10), ('student', 8), ('venue', 7), ('council', 6), ('member', 6)], 'Cultural event': [('performance', 10), ('venue', 7), ('concert', 6), ('spring', 6), ('melody', 6)]}.

Observed high-PMI collocations after the minimum-frequency-2 filter: [{'bigram': 'budget discussion', 'frequency': 4, 'pmi': 8.222794902868111}, {'bigram': 'celebration features', 'frequency': 4, 'pmi': 8.222794902868111}, {'bigram': 'code cup', 'frequency': 4, 'pmi': 8.222794902868111}, {'bigram': 'digital mapping', 'frequency': 4, 'pmi': 8.222794902868111}, {'bigram': 'features dance', 'frequency': 4, 'pmi': 8.222794902868111}, {'bigram': 'modern astronomy', 'frequency': 4, 'pmi': 8.222794902868111}]. Their recurrence motivates testing bigram features, but templates and institutional names can dominate. This is a training-data observation, not held-out evidence for choosing a model.

`chunk_examples.csv` gives actual training input spans and POS patterns so each representative chunk can be checked. `lengths_by_category.png` shows the class-conditional length distributions; small supports and synthetic construction constrain interpretation.

If this is development mode, all these examples are AI-authored synthetic text. Balanced class counts and clean vocabulary reflect fixture construction and do not establish performance on real institutional announcements. Real-data training analysis will only be academically final after human review and a reviewed-mode run.
