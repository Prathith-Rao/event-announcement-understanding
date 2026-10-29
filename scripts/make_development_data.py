"""AI-authored synthetic fixtures. Not human review or real-data evidence."""
import json

from event_nlp.config import DATA, FIELDS
from event_nlp.data import write_jsonl

TOPICS = {
    "Workshop": [("workshop", "Practical Python", "Practice coding with exercises and instructor feedback."), ("training", "Digital Mapping", "Bring a laptop for guided practical activities.")],
    "Seminar": [("seminar", "Climate Research", "A speaker will present findings followed by audience questions."), ("lecture", "Modern Astronomy", "Listen to an invited researcher discuss recent discoveries.")],
    "Competition": [("competition", "Design Challenge", "Teams will compete for prizes awarded by a panel of judges."), ("hackathon", "Campus Code Cup", "Entries will be ranked and winners receive awards.")],
    "Meeting": [("meeting", "Student Council", "Members will discuss the agenda and vote on proposals."), ("meeting", "Planning Committee", "Representatives should bring suggestions for the budget discussion.")],
    "Cultural event": [("concert", "Spring Melodies", "Enjoy an evening of live music and artistic performances."), ("festival", "Campus Arts", "The celebration features dance, theatre and musical performances.")],
}
TEMPLATES = [
    'Join our {kind} "{name}" on {day} March 2027 at 10:00 AM in Room B12. {detail}',
    'The department is hosting a {kind} on {name}. It will be held on {day} April 2027 at 2:30 PM. Venue: West Hall. {detail}',
    'You are invited to the {kind} entitled "{name}". Event date: {day} May 2027. Time: 11:00 AM. Venue: East Auditorium. {detail}',
    'Please attend the {kind} called "{name}" scheduled for {day} June 2027 at 3:00 PM in Room C7. {detail}',
    'Registration closes on 2 July 2027; the {kind} "{name}" will be held on {day} July 2027 at 9:00 AM. Venue: Maple Hall. {detail}',
    'Our association announces a {kind} about {name}. Save {day} August 2027 for this event at 4:00 PM. Venue: River Theatre. {detail}',
    'An upcoming {kind} on {name} welcomes all students. The event takes place on {day} September 2027 at 1:00 PM in Room D9. {detail}',
    'The {kind} "{name}" is scheduled on {day} October 2027. It starts at 12:30 PM. Venue: North Hall. {detail}',
    'Make time for a {kind} entitled "{name}" on {day} November 2027 at 5:00 PM. Venue: South Hall. {detail}',
    'All members can join the {kind} "{name}". Date: {day} December 2027. Time: 6:00 PM. Venue: Main Auditorium. {detail}',
    'There will be a {kind} on {name} on {day} January 2028 at 10:30 AM. Venue: Cedar Hall. {detail}',
    'Students are welcome at our {kind} called "{name}" on {day} February 2028 at 2:00 PM. Venue: Lake Theatre. {detail}',
    'Reserve an afternoon for the {kind} "{name}". The event is on {day} March 2028 at 3:30 PM. Venue: Elm Hall. {detail}',
    'A {kind} on {name} has been arranged for {day} April 2028 at 11:30 AM. Venue: Pine Auditorium. {detail}',
    'The student society invites you to its {kind} "{name}" on {day} May 2028 at 9:30 AM. Venue: Oak Hall. {detail}',
    'Attend a special {kind} about {name} on {day} June 2028 at 4:30 PM. Venue: Room E4. {detail}',
]


def challenge(identifier, text, fields, expected_status="needs_review", reference=None, tags=None):
    gold = {}
    for field in FIELDS:
        raw = fields.get(field)
        if raw is None:
            gold[field] = None
        else:
            start = text.index(raw)
            gold[field] = {"raw": raw, "start": start, "end": start + len(raw), "normalized": None}
    return {"id": identifier, "text": text, "provenance": "synthetic", "review_status": "needs_review",
            "human": None, "reference_date": reference, "gold": gold,
            "expected_status": expected_status, "tags": tags or [], "gold_origin": "AI-authored expected values; human audit pending"}


def main():
    rows = []
    for category, topics in TOPICS.items():
        for index, template in enumerate(TEMPLATES):
            kind, name, detail = topics[index % len(topics)]
            text = template.format(kind=kind, name=name, detail=detail, day=10 + index)
            rows.append({"id": f"synthetic-{category.split()[0].lower()}-{index:02}", "text": text,
                         "institution": None, "source_url": None, "collection_date": None, "publication_date": None,
                         "proposed": {"category": category, "fields": {}}, "label": category,
                         "group_id": f"authored-template-{index:02}", "provenance": "synthetic",
                         "review_status": "needs_review", "human": None, "split": "unassigned"})
    write_jsonl(DATA / "synthetic_development.jsonl", rows)
    dev = [
        challenge("dev-01", 'Registration closes on 4 May 2027; the workshop "Data Skills" will be held on 9 May 2027 at 10:00 AM in Room B12.', {"event_name":"Data Skills", "date":"9 May 2027", "time":"10:00 AM", "venue":"Room B12"}, tags=["deadline"]),
        challenge("dev-02", 'Join the seminar "New Horizons" on 8 June at 2:00 PM. Venue: West Hall.', {"event_name":"New Horizons", "date":"8 June", "time":"2:00 PM", "venue":"West Hall"}, tags=["missing_year"]),
        challenge("dev-03", 'The meeting "Council Review" is tomorrow at 3:00 PM in Room C7.', {"event_name":"Council Review", "date":"tomorrow", "time":"3:00 PM", "venue":"Room C7"}, reference="2027-06-01", tags=["relative_reference"]),
        challenge("dev-04", 'The meeting "Council Review" is tomorrow at 3:00 PM in Room C7.', {"event_name":"Council Review", "date":"tomorrow", "time":"3:00 PM", "venue":"Room C7"}, tags=["relative_no_reference"]),
        challenge("dev-05", 'Attend the competition "Code Race" on 14 July 2027. Venue: East Hall.', {"event_name":"Code Race", "date":"14 July 2027", "venue":"East Hall"}, tags=["missing_time"]),
        challenge("dev-06", 'The seminar "Ocean Science" takes place on 11 August 2027 at 11:00 AM.', {"event_name":"Ocean Science", "date":"11 August 2027", "time":"11:00 AM"}, tags=["missing_venue"]),
        challenge("dev-07", 'Organizer address: at Old Hall. The workshop "Robotics" will be held on 12 September 2027 at 9:00 AM. Venue: New Hall.', {"event_name":"Robotics", "date":"12 September 2027", "time":"9:00 AM", "venue":"New Hall"}, tags=["venue_distractor"]),
        challenge("dev-08", 'Join the workshop and seminar on 10 October 2027 at 10:00 AM. Venue: Main Hall.', {"date":"10 October 2027", "time":"10:00 AM", "venue":"Main Hall"}, tags=["overlap"]),
        challenge("dev-09", 'The library has acquired new books. Return borrowed items before the end of term.', {}, expected_status="unsupported", tags=["unrelated"]),
        challenge("dev-10", 'A workshop on 10 May 2027 at 9:00 AM is followed by a seminar on 11 May 2027 at 2:00 PM.', {}, expected_status="unsupported", tags=["multiple_events"]),
        challenge("dev-11", 'Our workshop on Practical Astronomy is on 20 May 2027 at 10:00 AM inside Rose Pavilion.', {"event_name":"Practical Astronomy", "date":"20 May 2027", "time":"10:00 AM", "venue":"Rose Pavilion"}, tags=["unfamiliar_venue", "chunking"]),
        challenge("dev-12", 'The concert "Moonlight" is on 03/04/2027 at 7:00 PM. Venue: Music Hall.', {"event_name":"Moonlight", "date":"03/04/2027", "time":"7:00 PM", "venue":"Music Hall"}, tags=["numeric_ambiguity"]),
        challenge("dev-13", 'The seminar "Research Methods" is on 12 May 2027 or 13 May 2027 at 10:00 AM or 2:00 PM. Venue: Birch Hall.', {"event_name":"Research Methods", "venue":"Birch Hall"}, tags=["multiple_dates_times"]),
        challenge("dev-14", 'Our workshop "Model Building" runs from 12-14 May 2027 at 9:00 AM. Venue: West Hall.', {"event_name":"Model Building", "time":"9:00 AM", "venue":"West Hall"}, tags=["date_range"]),
        challenge("dev-15", 'Join the seminar "Strange Calendar" on 31 February 2027 at 10:00 AM. Venue: Maple Hall.', {"event_name":"Strange Calendar", "date":"31 February 2027", "time":"10:00 AM", "venue":"Maple Hall"}, tags=["invalid_date"]),
        challenge("dev-16", 'A gathering of curious minds explores distant planets in the observatory next week.', {}, expected_status="unsupported", tags=["unfamiliar_phrasing"]),
    ]
    write_jsonl(DATA / "challenge_development.jsonl", dev)
    # Separate fixtures; never imported by development evaluation.
    final = [
        challenge("final-01", 'Applications close on 7 November 2028; the seminar "Urban Futures" is scheduled for 19 November 2028 at 4:00 PM. Venue: Atrium Hall.', {"event_name":"Urban Futures", "date":"19 November 2028", "time":"4:00 PM", "venue":"Atrium Hall"}, tags=["deadline"]),
        challenge("final-02", 'Our concert "Evening Ragas" will be held on 22 December 2028. Venue: Lotus Theatre.', {"event_name":"Evening Ragas", "date":"22 December 2028", "venue":"Lotus Theatre"}, tags=["missing_time"]),
        challenge("final-03", 'The competition "Logic League" takes place on 15 January 2029 at 8:30 AM.', {"event_name":"Logic League", "date":"15 January 2029", "time":"8:30 AM"}, tags=["missing_venue"]),
        challenge("final-04", 'Attend the meeting "Budget Forum" next Monday at 1:30 PM in Room Z8.', {"event_name":"Budget Forum", "date":"next Monday", "time":"1:30 PM", "venue":"Room Z8"}, reference="2029-01-06", tags=["relative_reference"]),
        challenge("final-05", 'Attend the meeting "Budget Forum" next Monday at 1:30 PM in Room Z8.', {"event_name":"Budget Forum", "date":"next Monday", "time":"1:30 PM", "venue":"Room Z8"}, tags=["relative_no_reference"]),
        challenge("final-06", 'Contact office at Silver Hall. The seminar "Water Security" will be held on 17 February 2029 at 2:30 PM. Venue: Jade Hall.', {"event_name":"Water Security", "date":"17 February 2029", "time":"2:30 PM", "venue":"Jade Hall"}, tags=["venue_distractor"]),
        challenge("final-07", 'The festival includes a judged competition on 8 March 2029 at 5:30 PM. Venue: Open Theatre.', {"date":"8 March 2029", "time":"5:30 PM", "venue":"Open Theatre"}, tags=["overlap"]),
        challenge("final-08", 'A workshop on 5 April 2029 at 9:30 AM and a concert on 6 April 2029 at 6:00 PM welcome visitors.', {}, expected_status="unsupported", tags=["multiple_events"]),
        challenge("final-09", 'The seminar "Open Questions" may be on 9 May 2029 or 10 May 2029 at 11:00 AM or 3:00 PM. Venue: Glass Hall.', {"event_name":"Open Questions", "venue":"Glass Hall"}, tags=["multiple_dates_times"]),
        challenge("final-10", 'Experience a discourse about coastal resilience under the banyan canopy this weekend.', {}, expected_status="unsupported", tags=["unfamiliar_phrasing"]),
        challenge("final-11", 'The cafeteria menu has changed. New breakfast options will be available from Monday.', {}, expected_status="unsupported", tags=["unrelated"]),
        challenge("final-12", 'We invite students to a workshop on Creative Electronics on 23 June 2029 at 2:00 PM inside Amber Pavilion.', {"event_name":"Creative Electronics", "date":"23 June 2029", "time":"2:00 PM", "venue":"Amber Pavilion"}, tags=["chunking"]),
    ]
    write_jsonl(DATA / "challenge_final.jsonl", final)
    print(f"Created {len(rows)} synthetic classification records, {len(dev)} development and {len(final)} reserved final challenges. Human review: none.")


if __name__ == "__main__":
    main()
