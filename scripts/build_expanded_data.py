"""Reproducible, explicitly synthetic training corpus with exact generated spans.

This authors development announcements; it is not a public-source collection or
human annotation. Template families and entity pools are partitioned before use.
"""
import argparse
import hashlib
import json
import random
import re
from collections import Counter
from datetime import date, timedelta

from event_nlp.config import DATA, FIELDS, SEED
from event_nlp.data import write_jsonl
from event_nlp.taxonomy import NON_EVENT

# purpose: explicit/implicit format descriptions, title themes, explanatory prose.
BANKS = {
    "Workshop": (["workshop", "hands-on lab", "guided practical session", "interactive tutorial", "skill-building session"], ["Python Essentials", "Creative Electronics", "Data Storytelling", "Watercolour Basics", "Design Thinking", "Robotics Lab"], ["Bring a laptop for guided exercises and individual practice.", "Participants will build something themselves with help from an instructor.", "Work through practical activities in small groups."]),
    "Seminar": (["seminar", "guest lecture", "research talk", "invited presentation", "scholarly discussion"], ["Climate Frontiers", "Quantum Horizons", "Modern Biology", "Urban Futures", "Research Methods", "Ocean Science"], ["An invited speaker will present findings and answer audience questions.", "Listen to a researcher explain recent discoveries, followed by discussion.", "The speaker will share insights and take questions from the audience."]),
    "Competition": (["competition", "judged contest", "intercollege quiz", "debating contest", "competitive challenge"], ["Logic League", "Design Challenge", "Math Quest", "Debate Cup", "Idea Arena", "Photography Prize"], ["Entries will be judged and the highest-ranked teams will receive prizes.", "Contestants compete for first place and awards from the judging panel.", "Winners will be selected using published judging criteria."]),
    "Meeting": (["meeting", "committee discussion", "team check-in", "planning session", "board discussion"], ["Budget Review", "Project Sync", "Student Council", "Planning Forum", "Operations Review", "Research Group"], ["Members will review the agenda, discuss progress and decide next steps.", "Please bring updates and proposals for the group to discuss.", "Representatives will vote on the proposed budget and assign responsibilities."]),
    "Cultural event": (["concert", "cultural festival", "dance performance", "theatre show", "musical evening"], ["Evening Ragas", "Spring Melodies", "Rhythm Nights", "Stage Lights", "Arts Mosaic", "Monsoon Music"], ["Enjoy live music, dance and performances by local artists.", "The evening brings artistic performances and a celebration of culture.", "Performers will take the stage to entertain the audience."]),
    "Conference": (["conference", "research symposium", "international summit", "industry convention", "multi-track academic gathering"], ["Future Systems", "Global Sustainability", "Connected Science", "Innovation Summit", "Research Exchange", "Digital Society"], ["Delegates can attend parallel sessions, keynotes and panel discussions.", "Researchers from several institutions will present papers across multiple tracks.", "The programme brings together speakers, delegates and industry panels."]),
    "Webinar": (["webinar", "live online presentation", "webcast", "virtual speaker session", "online expert briefing"], ["Digital Horizons", "Remote Research", "Accessible Technology", "Finance Insights", "Global Learning", "Future Careers"], ["Join the live online broadcast and submit questions through the chat.", "The presenter will share slides remotely and take online audience questions.", "A joining link will be sent to registered online participants."]),
    "Hackathon": (["hackathon", "coding sprint", "prototype-building marathon", "codeathon", "collaborative coding challenge"], ["Code Forge", "Build for Good", "Campus Hacks", "Prototype Sprint", "Byte Quest", "Open Innovation"], ["Teams have 24 hours to build and demonstrate a working software prototype.", "Developers will code together overnight and pitch their projects to mentors.", "Build an app with your team during the timed coding challenge."]),
    "Sports event": (["football match", "cricket tournament", "basketball game", "badminton tournament", "marathon", "athletics meet", "swimming race"], ["Champions Cup", "Campus League", "City Run", "Victory Series", "Summer Games", "Open Athletics"], ["Players and spectators are welcome; teams will compete on the field.", "Athletes should arrive early for warm-up and the referee briefing.", "Cheer for the teams as they compete in the sporting fixture."]),
    "Exhibition": (["exhibition", "art gallery opening", "science expo", "photography display", "public showcase"], ["New Perspectives", "Science in Sight", "Visual Stories", "Creative Gallery", "Future Objects", "Innovation Display"], ["Visitors can walk through the displays and view the exhibited work.", "Browse the installations, photographs and objects on public display.", "Artists and exhibitors will explain their work to visiting audiences."]),
    "Career event": (["career fair", "recruitment drive", "placement event", "employer networking session", "job fair"], ["Career Connect", "Future Talent", "Campus Hiring", "Opportunity Day", "Graduate Pathways", "Employer Exchange"], ["Meet recruiters, explore job opportunities and bring an updated resume.", "Employers will speak with candidates about internships and open positions.", "Students can network with hiring managers and apply for vacancies."]),
    "Community service": (["volunteering drive", "blood donation camp", "community cleanup", "charity fundraiser", "environmental outreach event"], ["Clean Streets", "Give for Life", "Community Care", "Green Neighbourhood", "Helping Hands", "River Rescue"], ["Volunteers will support the local community; donations and helping hands are welcome.", "Join residents in service activities that benefit people in need.", "We are bringing volunteers together for a community cause."]),
    "Social gathering": (["birthday party", "alumni reunion", "family picnic", "social get-together", "potluck dinner"], ["Friends Together", "Homecoming Social", "Class Reunion", "Summer Picnic", "Birthday Bash", "Neighbourhood Evening"], ["Come along for informal conversation, food and time with friends.", "Families and friends are invited to relax and celebrate together.", "Bring a dish to share and enjoy catching up with everyone."]),
    "Training course": (["training course", "certification programme", "multi-session bootcamp", "professional course", "structured training programme"], ["Cloud Foundations", "Data Analytics Certificate", "Leadership Academy", "Applied Computing", "First Aid Certification", "Project Management"], ["Learners will complete a structured curriculum over several sessions and receive a certificate.", "Enrol in the course to follow the modules and complete practical assignments.", "The programme includes lessons, assessments and certification on completion."]),
    "Product launch": (["product launch", "unveiling", "new product debut", "release event", "service launch"], ["Nova Device", "Orbit Platform", "Pulse App", "Atlas Release", "Eco Mobility", "Smart Home"], ["The team will unveil the new product, demonstrate its features and answer questions.", "Be among the first to see the new release and its live demonstration.", "The company will introduce its latest offering to customers and the press."]),
    "Academic assessment": (["examination", "viva", "thesis defense", "practical assessment", "final exam"], ["Algorithms Assessment", "Research Defence", "Physics Practical", "Semester Evaluation", "Project Viva", "Mathematics Examination"], ["Candidates must bring their student ID and arrive before the assessment begins.", "Students will be evaluated by the examiners; no study materials are permitted.", "Prepare your answers and presentation for the academic evaluation."]),
    "Ceremony": (["graduation ceremony", "inauguration", "awards ceremony", "felicitation", "convocation"], ["Graduate Celebration", "New Beginnings", "Annual Honours", "Achievement Day", "Campus Inauguration", "Excellence Awards"], ["Guests will witness the formal proceedings and presentation of honours.", "Dignitaries will preside over the formal ceremony and congratulate the recipients.", "Please take your seats before the procession and official proceedings begin."]),
    "Tour or excursion": (["guided tour", "field trip", "industrial visit", "heritage walk", "excursion"], ["City Heritage", "Nature Discovery", "Factory Insight", "Museum Explorer", "Coastal Journey", "Historic Trails"], ["Participants will travel together with a guide and visit the scheduled locations.", "Wear comfortable shoes for the guided visit and outdoor exploration.", "The group will depart together for an educational trip."]),
    "Other event": (["open day", "public event", "community session", "organized gathering", "special programme"], ["Open Doors", "Discovery Day", "Community Exchange", "New Connections", "Public Forum", "Campus Welcome"], ["Everyone is welcome to attend this organized event and meet the hosts.", "The organizers invite the public to join the scheduled gathering.", "Participants can drop in, meet the organizers and explore the programme."]),
}

TEMPLATES = [
    '{name} is {article} {kind}{schedule}. {details}',
    'Join us for {name}, {article} {kind}{schedule}. {details}',
    'We are organizing {name}. This {kind} will be held{schedule}. {details}',
    'You are invited to {name}{schedule}. It is {article} {kind}. {details}',
    'The {kind} called "{name}" takes place{schedule}. {details}',
    'Save the date for {name}! Our {kind} is scheduled{schedule}. {details}',
    'Please attend the {kind} on {name}{schedule}. {details}',
    '{name}\nA {kind}.\n{date_line}{time_line}{venue_line}{details}',
    'Event: {name}\nFormat: {kind}\n{date_line}{time_line}{venue_line}{details}',
    'Looking forward to seeing you{schedule} for {name}. Expect {article} {kind}. {details}',
    '{schedule_first}, we will host {name}, {article} {kind}. {details}',
    '{name} — our upcoming {kind} — is happening{schedule}. {details}',
    'Come to {name}{schedule}. This {kind} is open to everyone. {details}',
    'The department announces "{name}", {article} {kind}{schedule}. {details}',
    'A {kind} entitled {name} has been arranged{schedule}. {details}',
    'Don’t miss {name}. The {kind} begins{schedule}. {details}',
    'Here are the details of our {kind}:\nTitle: {name}\n{venue_line}{time_line}{date_line}{details}',
    '{name} will bring everyone together{schedule}. The programme is {article} {kind}. {details}',
    'Our next {kind}, {name}, is set{schedule}. {details}',
    'We welcome you{schedule} to {name}, {article} {kind}. {details}',
    'Registration is open for {name}. This {kind} will take place{schedule}. {details}',
    'Mark your calendar: {name}{schedule}. It will be {article} {kind}. {details}',
    'An invitation to {name}: our {kind} runs{schedule}. {details}',
    'Everyone is welcome at {name}{schedule}. We have planned {article} {kind}. {details}',
    'For the next {kind}, we present {name}{schedule}. {details}',
    'Get ready for {name}! A {kind} awaits{schedule}. {details}',
    'The organizers have confirmed {name}{schedule}. This is {article} {kind}. {details}',
    'Attend {name}, {article} {kind}. Schedule:{schedule}. {details}',
    'Our invitation: {name} ({kind}){schedule}. {details}',
    'The {kind} {name} is coming up{schedule}. {details}',
    'Make time for {name}{schedule}; this {kind} welcomes new participants. {details}',
    'We would love you to attend {name}. The {kind} starts{schedule}. {details}',
    '{name}, our {kind}, is now scheduled{schedule}. {details}',
    'There will be {article} {kind}, {name}{schedule}. {details}',
    'This is your invitation to the {kind} named {name}{schedule}. {details}',
    'Upcoming: {name}\n{kind_cap}\n{time_line}{date_line}{venue_line}{details}',
    'Our team is hosting the {kind} "{name}"{schedule}. {details}',
    'All are invited to {name}{schedule}, {article} {kind} organized for our community. {details}',
    'The programme lists {name}{schedule}. Participants can expect {article} {kind}. {details}',
    'We have arranged {name} as our next {kind}{schedule}. {details}',
    'A reminder that {name}, {article} {kind}, will go ahead{schedule}. {details}',
    'Invitation | {name} | {kind}\n{date_line}{venue_line}{time_line}{details}',
    'Plans are confirmed for the {kind} {name}{schedule}. {details}',
    'Meet us{schedule} for {name}. We are running {article} {kind}. {details}',
    'Our {kind} will be {name}{schedule}. {details}',
    '{name} has been announced as {article} {kind}{schedule}. {details}',
    'Would you like to attend {name}? The {kind} takes place{schedule}. {details}',
    'We’re pleased to host {name}, {article} {kind}{schedule}. {details}',
    'Details for participants: {name}, {article} {kind}. {venue_line}{date_line}{time_line}{details}',
    'Announcing the {kind} {name}{schedule}. {details}',
]
PREFIXES = {
    "train": ["Bright", "Silver", "Cedar", "Maple", "Aurora", "River", "Aspen", "Green", "Summit", "Cobalt", "Sunrise", "Unity"],
    "validation": ["Amber", "Coral", "Linden", "Copper", "Harbour", "Sapphire"],
    "test": ["Willow", "Juniper", "Ivory", "Cypress", "Crimson", "Meadow"],
}
PLACE_NOUNS = ["Hall", "Auditorium", "Pavilion", "Community Centre", "Garden", "Library", "Stadium", "Studio", "Cafe", "Convention Center", "Sports Ground", "Lecture Theatre", "Meeting Room", "Innovation Hub", "School", "Office", "Atrium", "Courtyard"]
NEGATIVES = [
    "The library contains several books about {topic}. I enjoy reading them at home.",
    "Can you explain the difference between {topic} and related ideas?",
    "I have been studying {topic} for my homework; this is not an invitation.",
    "The article describes how {topic} became popular over time.",
    "What does {topic} mean? Please give me a definition.",
    "Our website has a section about {topic}, but no dates have been announced.",
    "I like {topic}. It is an interesting subject to learn about.",
    "This paragraph is an explanation of {topic}, rather than a scheduled happening.",
    "A school assignment asks students to write about {topic} in general.",
    "Here is a list of ideas related to {topic}; I am only brainstorming.",
]
UNTITLED = {
    "train": [
        "We are holding {article} {kind}{schedule}. {details}",
        "Please attend our {kind}{schedule}. {details}",
        "Our next {kind} is scheduled{schedule}. {details}",
        "Join us for {article} {kind}{schedule}. {details}",
        "The department is hosting {article} {kind}{schedule}. {details}",
        "A reminder about our {kind}{schedule}. {details}",
    ],
    "validation": [
        "Everyone is invited to {article} {kind}{schedule}. {details}",
        "The upcoming {kind} begins{schedule}. {details}",
    ],
    "test": [
        "{kind_cap}{schedule}. {details}",
        "Notice for attendees: {article} {kind} will be held{schedule}. {details}",
    ],
}


def mark(field: str, raw: str) -> str:
    return f"[[{field}|{raw}]]"


def render(marked: str) -> tuple[str, dict]:
    output, fields, cursor = "", dict.fromkeys(FIELDS), 0
    for match in re.finditer(r"\[\[(\w+)\|([^\]]+)\]\]", marked):
        output += marked[cursor:match.start()]
        start = len(output)
        output += match[2]
        if fields[match[1]] is None:
            fields[match[1]] = {"raw": match[2], "start": start, "end": len(output), "normalized": None}
        cursor = match.end()
    output += marked[cursor:]
    return output, fields


def make_record(category: str, family: int, variant: int, split: str, rng: random.Random) -> dict:
    kinds, themes, descriptions = BANKS[category]
    prefix = rng.choice(PREFIXES[split])
    kind = rng.choice(kinds)
    has_name = rng.random() > .16
    name = f"{prefix} {rng.choice(themes)}"
    place = f"{rng.choice(PREFIXES[split])} {rng.choice(PLACE_NOUNS)}"
    if rng.random() < .14:
        place = f"Room {rng.randint(101, 650)}, {prefix} Block"
    if category == "Webinar" or rng.random() < .1:
        place = rng.choice(["Zoom", "Microsoft Teams", "Google Meet", "Webex"])
    moment = date(2027, 1, 1) + timedelta(days=rng.randrange(1050))
    raw_date = moment.strftime(rng.choice(["%d %B %Y", "%B %d, %Y", "%Y-%m-%d", "%d %b %Y"]))
    reference = None
    if rng.random() < .12:
        raw_date = rng.choice(["tomorrow", "today", "next Friday", "this Saturday", "in 3 days"])
        reference = "2027-06-08" if rng.random() < .6 else None
    elif rng.random() < .1:
        raw_date = moment.strftime("%d %B")
    hour = rng.randint(8, 21)
    clock = rng.choice([f"{hour % 12 or 12}:{rng.choice(['00','15','30','45'])} {'AM' if hour < 12 else 'PM'}", f"{hour:02}:30", f"{hour % 12 or 12} {'am' if hour < 12 else 'pm'}"])
    present = {"date": rng.random() > .16, "time": rng.random() > .23, "venue": rng.random() > .19}
    name_text = mark("event_name", name) if has_name else f"our {kind}"
    d, t, v = mark("date", raw_date), mark("time", clock), mark("venue", place)
    date_part = (rng.choice(["on ", "scheduled for "]) if not re.match(r"today|tomorrow|next|this|in ", raw_date) else "") + d
    parts = [date_part if present["date"] else "", "at " + t if present["time"] else "", ("via " if place in ["Zoom", "Microsoft Teams", "Google Meet", "Webex"] else rng.choice(["at ", "in ", "inside "])) + v if present["venue"] else ""]
    if variant % 3 == 0:
        parts = [parts[2], parts[0], parts[1]]
    schedule = " ".join(part for part in parts if part)
    values = {"name": name_text, "kind": kind, "kind_cap": kind.capitalize(), "article": "an" if kind[0] in "aeiou" else "a",
              "schedule": " " + schedule if schedule else "", "schedule_first": schedule[:1].upper() + schedule[1:] if schedule else "For our community",
              "date_line": "Date: " + d + "\n" if present["date"] else "",
              "time_line": "Time: " + t + "\n" if present["time"] else "",
              "venue_line": "Venue: " + v + "\n" if present["venue"] else "", "details": rng.choice(descriptions)}
    marked = TEMPLATES[family].format(**values)
    if not has_name:
        marked = UNTITLED[split][family % len(UNTITLED[split])].format(**values)
    marked = marked.replace("A " + kind, values["article"].capitalize() + " " + kind)
    marked = re.sub(r"(held|place|scheduled|arranged|set|starts|begins|coming up|go ahead)\s+scheduled for", r"\1 on", marked)
    if variant % 7 == 0:
        marked = "Registration closes on 2 January 2027. " + marked
    if variant % 11 == 0:
        marked += " The organizer's office is at Old Administration Building."
    if variant % 8 == 0:
        marked = marked.lower()
    text, fields = render(marked)
    if not has_name:
        fields["event_name"] = None
    identifier = f"v2-{list(BANKS).index(category):02}-{family:02}-{variant:03}"
    return {"id": identifier, "text": text, "label": category, "gold": fields, "reference_date": reference,
            "provenance": "synthetic", "human": None, "review_status": "needs_review", "source_url": None, "institution": None,
            "collection_date": None, "publication_date": None, "proposed": {"category": category, "fields": fields},
            "group_id": f"v2-template-{family:02}" if has_name else f"v2-untitled-{split}-{family % len(UNTITLED[split])}", "template_family": family if has_name else f"untitled-{split}-{family % len(UNTITLED[split])}", "split": split,
            "annotation_origin": "Programmatically authored synthetic expectations, not human review"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-template", type=int, default=12)
    parser.add_argument("--replace-unfrozen", action="store_true")
    args = parser.parse_args()
    directory = DATA / "expanded_v2"
    if (directory / "records.jsonl").exists():
        if not args.replace_unfrozen or (DATA.parent / "reports/expanded_v2/test_metrics.json").exists():
            raise SystemExit("Expanded dataset exists/frozen. Use a new version or explicitly replace only an unfrozen run.")
        import shutil
        archive = DATA.parent / "archive/v2_initial"
        archive.mkdir(parents=True, exist_ok=True)
        if not (archive / "records.jsonl").exists():
            shutil.copy2(directory / "records.jsonl", archive / "records.jsonl")
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    family_ids = list(range(len(TEMPLATES)))
    rng.shuffle(family_ids)
    allocation = {family: "train" if order < 30 else "validation" if order < 40 else "test" for order, family in enumerate(family_ids)}
    rows = [make_record(category, family, variant, allocation[family], rng) for category in BANKS for family in range(len(TEMPLATES)) for variant in range(args.per_template)]
    topics = [term for kinds, themes, _ in BANKS.values() for term in kinds + themes] + ["cooking", "calendars", "sports", "campus life", "machine learning"]
    for family in range(len(TEMPLATES)):
        for variant in range(args.per_template):
            text = NEGATIVES[family % len(NEGATIVES)].format(topic=rng.choice(topics))
            # All variations of one negative construction belong to the same partition.
            split = "train" if family % 10 < 6 else "validation" if family % 10 < 8 else "test"
            rows.append({"id": f"v2-negative-{family:02}-{variant:03}", "text": text, "label": NON_EVENT, "gold": dict.fromkeys(FIELDS),
                         "reference_date": None, "provenance": "synthetic", "human": None, "review_status": "needs_review", "source_url": None,
                         "group_id": f"v2-negative-{family % 10}", "template_family": f"negative-{family % 10}", "split": split,
                         "annotation_origin": "Programmatically authored synthetic expectations, not human review"})
    # Repeated negative instances are removed, retaining their construction group.
    unique = {}
    for row in rows:
        unique.setdefault(row["text"], row)
    rows = list(unique.values())
    write_jsonl(directory / "records.jsonl", rows)
    manifest = {"version": "expanded_v2", "seed": SEED, "records": len(rows), "provenance": "synthetic",
                "labels": dict(Counter(row["label"] for row in rows)), "splits": dict(Counter(row["split"] for row in rows)),
                "template_families": len({row["group_id"] for row in rows}), "human_reviewed": 0,
                "split_policy": "Preassigned construction families; separate proper-name/venue prefix pools by partition. Negative construction families are also disjoint.",
                "limitations": "Authored templates and label descriptions can be easier than naturally occurring announcements. This is not human-reviewed real-data accuracy.",
                "sha256": hashlib.sha256((directory / "records.jsonl").read_bytes()).hexdigest()}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
