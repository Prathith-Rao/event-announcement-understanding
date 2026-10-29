"""Explicit format interpretation complements statistical category predictions."""
import re

FORMATS = {
    "Workshop": r"workshop|hands[- ]on (?:lab|session)|practical tutorial",
    "Seminar": r"seminar(?!\s+(?:room|hall))|guest lecture|research talk|colloquium",
    "Competition": r"competition|contest|quiz|debate",
    "Meeting": r"meeting|team check-in|committee discussion",
    "Cultural event": r"concert|festival|dance performance|theatre show|musical evening|recital",
    "Conference": r"conference|symposium|summit|convention",
    "Webinar": r"webinar|webcast|online presentation",
    "Hackathon": r"hackathon|codeathon|coding sprint|prototype-building marathon|collaborative coding challenge",
    "Sports event": r"(?:football|cricket|basketball|badminton|hockey|tennis)\s+(?:match|game|tournament)|marathon|athletics meet|swimming race",
    "Exhibition": r"exhibition|gallery opening|science expo|photography display",
    "Career event": r"career fair|job fair|recruitment drive|placement (?:event|drive)|campus hiring",
    "Community service": r"blood donation|volunteering drive|community clean-?up|charity fundraiser|outreach event",
    "Social gathering": r"birthday party|party|reunion|picnic|social get-together|potluck|wedding reception|lunch|dinner|breakfast|coffee",
    "Training course": r"training course|certification (?:programme|program)|bootcamp|professional course",
    "Product launch": r"product launch|unveiling|product debut|release event|service launch",
    "Academic assessment": r"examination|exam|viva|thesis defen[cs]e|practical assessment",
    "Ceremony": r"ceremony|inauguration|felicitation|convocation|graduation",
    "Tour or excursion": r"guided tour|field trip|industrial visit|heritage walk|excursion",
}


def explicit_format(text: str) -> tuple[str | None, str | None]:
    matches = []
    for category, pattern in FORMATS.items():
        for match in re.finditer(r"\b(?:" + pattern + r")\b", text, re.I):
            matches.append((match.start(), -len(match.group()), category, match.group()))
    if not matches:
        return None, None
    _, _, category, raw = min(matches)
    return category, raw


def general_discussion(text: str) -> bool:
    return bool(re.search(r"\b(?:I (?:enjoy|like|love|read|study|am studying)|what (?:does|is|are)|explain|definition|meaning of|article describes|books? about|in general|not an invitation|only brainstorming)\b", text, re.I))
