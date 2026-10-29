# Manual annotation instructions

Open annotations.csv (UTF-8) and read ANNOUNCEMENTS.md for the numbered original texts and source links. Do not change id, text, institution or source_url. All annotation cells are intentionally blank; model suggestions are withheld to reduce anchoring.

For each row fill:
- reviewer: your name or stable team reviewer ID.
- reviewed_at: ISO timestamp including timezone, for example 2026-10-29T15:00:00+05:30 (use your actual review time).
- decision: accepted, needs_review, or excluded. Explain ambiguity/exclusion in notes.
- category: one category below, or Not an event for genuinely unrelated/general text. For unresolved overlaps leave category blank and use needs_review.
- reference_date: YYYY-MM-DD only if an explicit independently known reference date applies to this text. Collection date is NOT an event reference date.
- For EACH of event_name/date/time/venue, set _presence to present, missing or ambiguous. Never leave presence undecided on an accepted row.
- If present, paste the exact substring in _raw. Offsets _start/_end are Python character offsets [start,end), not word indexes. For uniquely occurring raw substrings you may leave offsets blank; they can be derived and checked. For repeated substrings supply offsets to identify the intended occurrence.
- If missing, leave raw/start/end blank. If ambiguous, mark needs_review and explain competing candidates in notes.
- date_normalized: optional ISO date only when the text supplies the year/month/day or the supplied reference resolves it. Otherwise leave blank. Keep raw wording even when normalization is possible.

Annotate ONLY what appears in the supplied text. Do not copy a title/date/venue from another part of the source web page into the gold fields. Some real paragraphs contain no name, clock or venue. Missing is correct. Distinguish event dates from deadlines and organizer addresses from venues. Multiple events, generic recurring promotion or unclear category boundaries should be needs_review, not forced into a single label. Public invitation wording may also discuss a completed event; mark this in notes if relevant.

Category definitions:
- Workshop: A short, participatory session focused on practical exercises.
- Seminar: A speaker-led lecture, research talk or discussion.
- Competition: A judged contest with ranked entries or winners; excludes explicitly named hackathons and sports fixtures.
- Meeting: An organizational, planning, committee or team discussion.
- Cultural event: An arts performance, concert, dance, theatre or cultural festival.
- Conference: A formal conference, convention, summit or multi-session research gathering.
- Webinar: An explicitly described online presentation or webinar; an online practical workshop remains Workshop.
- Hackathon: A time-bounded collaborative coding or prototype-building contest.
- Sports event: An athletic fixture, race, tournament or organized fitness event.
- Exhibition: A public display, gallery, expo or showcase of objects or work.
- Career event: Recruitment, placement, career fair, networking for jobs or employer interaction.
- Community service: Volunteering, charity, community outreach, donation or environmental service.
- Social gathering: A party, reunion, picnic, informal celebration or social get-together.
- Training course: A structured multi-session course, certification programme or sustained professional training.
- Product launch: The introduction, unveiling or release event of a product or service.
- Academic assessment: An examination, viva, assessment, defense or evaluation session.
- Ceremony: Graduation, inauguration, felicitation, awards presentation or other formal ceremony.
- Tour or excursion: An organized visit, field trip, excursion, guided walk or tour.
- Other event: A specific organized happening whose purpose does not fit the categories above.

Overlap: use the primary explicit format/purpose. A career-topic workshop is Workshop; a recruitment fair with a talk is Career event. Seminar Room is a venue cue. Online delivery alone does not force Webinar. Use notes and needs_review for an unresolved overlap.

Return the completed CSV. We will validate exact spans and decisions before importing. Do not overwrite the originals. Ideally two people label independently, then adjudicate; a single review must not be reported as agreement between annotators.

Evaluation plan: this is an external convenience sample with repeated institutions/templates, not a new training set. Freeze the current models/rules, review blind, then report real-data results in a separate table with accepted n, class supports, source counts, field supports and exclusions. Do not tune on it and then describe the same rows as an untouched test. Invitation-only rows cannot estimate non-event recall; add independently sourced non-event controls separately. No real-data metric exists until labels are returned.

WhatsApp/club posters: private material is not accessible automatically. You may add consented, redacted exact text in a separate CSV using the same schema, source_type and a non-public source reference. Never publish private chat content without permission.
