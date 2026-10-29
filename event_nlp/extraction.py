"""Evidence-first rules, NLTK phrase analysis and optional learned BIO spans."""
import re
from datetime import date

from .classification import keyword_prediction
from .config import FIELDS
from .taxonomy import EVENT_CUE
from .temporal import DAY, MONTH, DATE_RE, DATE_RANGE_RE, TIME_RE, normalize_date, normalize_time

LOCATION_WORDS = r"hall|auditorium|room|lab|laboratory|centre|center|pavilion|park|garden|cafe|café|cafeteria|stadium|ground|theatre|theater|library|school|college|university|campus|building|block|office|studio|hub|lawn|courtyard|atrium|museum|hotel|restaurant|arena|pool|beach|court|church|temple|mosque|plaza|square|gallery|boardroom|classroom|terrace|resort|house|home|rooftop|field|track|mall|station|terminal|hospital|clinic|loft|community|zoom|teams|meet|webex|online"


def evidence(text: str, start: int, end: int, method: str, role: str = "event", normalized=None, rank: int = 50) -> dict:
    while start < end and text[start] in " \t\r\n,:;–—":
        start += 1
    while end > start and text[end - 1] in " \t\r\n,:;.!–—":
        end -= 1
    return {"raw": text[start:end], "start": start, "end": end, "normalized": normalized, "method": method, "role": role, "rank": rank}


def local_prefix(text: str, start: int) -> str:
    prefix = text[max(0, start - 150):start]
    return re.split(r"[;!\n]|\.(?!\d)\s+|\b(?:but|whereas)\b", prefix, flags=re.I)[-1].lower()


def date_role(text: str, start: int) -> str:
    prefix = local_prefix(text, start)
    deadline = list(re.finditer(r"register|registration|deadline|applications?|submission|rsvp|apply|book(?:ing)? closes", prefix))
    event = list(re.finditer(rf"held|scheduled|event date|takes? place|happen|starts?|begins?|{EVENT_CUE}\s+(?:is\s+)?(?:on|at|from)", prefix, re.I))
    if deadline and (not event or deadline[-1].start() > event[-1].start()):
        return "deadline"
    if re.search(r"published|posted|last updated|born|founded", prefix) and not event:
        return "other"
    return "event"


def generic_name(raw: str) -> bool:
    if re.match(r"^(?:our|this|your|an?|the(?: next| upcoming)?)\s+", raw, re.I) and not any(word[:1].isupper() or word.isupper() for word in raw.split()[1:]):
        if re.search(rf"{EVENT_CUE}|tutorial|lab|presentation|discussion|briefing|show|evening|drive|programme|program|camp|fair|check-in|display|showcase|visit|walk|unveiling|debut", raw, re.I):
            return True
    clean = re.sub(r"^(?:(?:the|a|an|our|this|your|next|upcoming|annual|special)\s+)+", "", raw, flags=re.I).strip()
    return bool(re.fullmatch(EVENT_CUE, clean, re.I)) or clean.lower() in {"event", "session", "programme", "program", "everyone", "us", "all", "our community"}


def phrase_end(text: str, start: int, temporal: list[dict], venue: bool = False) -> int:
    end = min(len(text), start + (180 if venue else 140))
    for value in temporal:
        if start < value["start"] < end:
            end = value["start"]
    locations = "" if venue else "in|inside|outside|near|via|over|"
    boundary = re.search(r"[\n;!?]|\s+(?:" + locations + r"on|at|from|starting|beginning|scheduled|which|where|with|followed by|featuring|organized by|organised by|to discuss|and (?:bring|will|enjoy|then|the))\s+|\.(?=\s|$)", text[start:end], re.I)
    if boundary:
        end = start + boundary.start()
        if venue and re.search(r"\b(?:St|Dr|Mt|Jr|Sr)$", text[start:end], re.I):
            later = re.search(r"[\n;!?]|\.(?=\s|$)", text[end + 1:end + 120])
            end = end + 1 + later.start() if later else min(len(text), end + 120)
    if venue:
        appositive = re.search(r",\s+(?:a|an|our)\s+", text[start:end], re.I)
        if appositive:
            end = start + appositive.start()
    return end


def _venue_at(text: str, start: int, temporal: list[dict]) -> list[dict]:
    if any(value["start"] <= start < value["end"] for value in temporal):
        return []
    prefix = local_prefix(text, start)
    if re.search(r"organizer|organiser|contact|address|office (?:is|located)", prefix, re.I):
        return []
    if text[start:].startswith("the "):
        start += 4
    end = phrase_end(text, start, temporal, venue=True)
    raw = text[start:end].strip(" ,.")
    familiar = bool(re.search(rf"\b(?:{LOCATION_WORDS})\b", raw, re.I))
    proper = bool(re.fullmatch(r"[A-Z][\w’'&-]*(?:\s+[A-Z][\w’'&-]*){0,7}", raw))
    if not raw or not (familiar or proper):
        return []
    if len(raw.split()) > 16 or re.search(r"\b(?:will|should|would|must|because|participants|register|bring)\b", raw, re.I):
        return []
    return [evidence(text, start, start + len(raw), "venue_context" if familiar else "proper_location_context", rank=75 if familiar else 60)]


def _candidates(text: str, mode: str, language: dict | None, entity_model=None) -> dict:
    candidates = {field: [] for field in FIELDS}
    intervals = list(DATE_RANGE_RE.finditer(text))
    for match in intervals + list(DATE_RE.finditer(text)):
        if any(other.start() <= match.start() < other.end() for other in intervals) and not any(match.start() == other.start() and match.end() == other.end() for other in intervals):
            continue
        role = date_role(text, match.start())
        candidates["date"].append(evidence(text, match.start(), match.end(), "date_rule", role, rank=100 if re.search(r"(?:date|when)\s*:\s*$", local_prefix(text, match.start())) else 60))
    for match in TIME_RE.finditer(text):
        if any(match.start() < value["end"] and match.end() > value["start"] for value in candidates["date"]):
            continue
        if re.fullmatch(r"\d+\s*[-–—]\s*\d+", match.group()) and not re.search(r"\b(?:at|from|time)\s*:?\s*$", text[max(0, match.start()-12):match.start()], re.I):
            continue
        candidates["time"].append(evidence(text, match.start(), match.end(), "time_rule", date_role(text, match.start()), rank=80))
    for match in re.finditer(r"\b(?:at|time\s*:)\s+(?P<time>\d{1,2})(?![\d:/.])\b", text, re.I):
        start, end = match.span("time")
        if not any(value["start"] <= start < value["end"] for field in ("date", "time") for value in candidates[field]):
            candidates["time"].append(evidence(text, start, end, "contextual_hour", date_role(text, start), rank=50))
    temporal = candidates["date"] + candidates["time"]
    for value in candidates["date"]:
        if re.fullmatch(r"(?:next |this )?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", value["raw"], re.I):
            if any(other is not value and re.search(MONTH, other["raw"], re.I) and 0 <= other["start"] - value["end"] <= 5 for other in candidates["date"]):
                value["role"] = "weekday_modifier"
    title_patterns = [
        (r"(?im)\b(?:event(?: name)?|title|programme name|program name)\s*:\s*(?P<value>[^\n;]+)", "title_label", 100),
        (r"(?im)^\s*name\s*:\s*(?P<value>[^\n;]+)", "title_label", 100),
        (r'["“‘](?P<value>[^"”’\n]{2,120})["”’]', "quoted_title", 90),
        (rf"\b{EVENT_CUE}\s+(?:on|about|entitled|titled|called|named)\s+(?P<value>[^\n;.!?]+)", "event_topic", 80),
        (r"(?im)(?:^|(?<=[.!?])\s+)(?P<value>[^\n.!?]{2,100}?)\s+(?:is(?: now)? (?:a|an|scheduled|happening|set)|will (?:be held|take place|bring)|takes? place|starts?|begins?|has been announced)\b", "leading_title", 75),
        (r"\b(?:join (?:us )?for|invited to|invite (?:you|students|everyone) to|announc(?:e|es|ing)|presenting|hosting|attend|welcome to|save the date for|confirmed|arranged|ready for|reminder that|make time for)\s+(?P<value>[^\n;.!?]+)", "invitation_title", 70),
        (r"\b(?:organizing|organising|organizes|organises|pleased to host|love you to attend)\s+(?P<value>[^\n;.!?]+)", "organized_title", 88),
        (r"\b(?:our|the|this)\s+[^.!?\n]{2,60}?\s+will be\s+(?P<value>[^\n;.!?]+)", "future_named_event", 80),
    ]
    for pattern, method, rank in title_patterns:
        for match in re.finditer(pattern, text, re.I):
            start, end = match.span("value")
            if method == "quoted_title":
                before = text[max(0, start-35):start-1]
                if re.search(r"(?:^|\s)(?:at|in|inside|venue|location|speaker|says?)\s*:?\s*$", before, re.I):
                    continue
            else:
                end = min(end, phrase_end(text, start, temporal))
                trailing = re.search(r"\s+(?:is|are|will be|will|has been|is happening|is scheduled)\s*$", text[start:end], re.I)
                if trailing:
                    end = start + trailing.start()
                split = re.search(rf",\s*(?:a|an|our)\s+|\s*[—–|]\s*|\s*\([^)]*{EVENT_CUE}", text[start:end], re.I)
                if split:
                    end = start + split.start()
                trim = re.match(rf"(?:(?:the|a|an|our|this|upcoming)\s+)*{EVENT_CUE}\s+(?:on|about|entitled|titled|called|named)\s+", text[start:end], re.I)
                if trim:
                    start += trim.end()
                if method == "invitation_title" and re.match(r"(?:the|a|an|our)\s+", text[start:end], re.I):
                    # A format prefix precedes the first proper-name word: "the conference North Star".
                    named = re.search(r"\b[A-Z][\w&'-]*", text[start:end])
                    if named and named.start() > 0 and re.search(rf"{EVENT_CUE}|lab|tutorial|session|discussion|presentation|briefing|game|meet|race|opening|display|fair|drive|camp|dinner|programme|unveiling|debut|walk|visit", text[start:start+named.start()], re.I):
                        start += named.start()
            value = evidence(text, start, end, method, rank=rank)
            if value["raw"] and not generic_name(value["raw"]) and not DATE_RE.match(value["raw"]) and len(value["raw"].split()) <= 18:
                candidates["event_name"].append(value)
    for match in re.finditer(r"\b(?:venue|location|where|place)\s*:\s*(?P<value>[^\n;]+)", text, re.I):
        start, end = match.span("value")
        end = min(end, phrase_end(text, start, temporal, venue=True))
        inline = re.search(r"\b(?:date|time|registration|register|contact)\s*:", text[start:end], re.I)
        if inline:
            end = start + inline.start()
        if end > start:
            candidates["venue"].append(evidence(text, start, end, "venue_label", rank=100))
    for match in re.finditer(r"(?=\b(?:at|in|inside|outside|near|via|over|on)\s+(?P<value>\S))", text, re.I):
        candidates["venue"].extend(_venue_at(text, match.start("value"), temporal))
    if mode == "hybrid" and language:
        for chunk in language["chunks"]:
            prefix = text[max(0, chunk["start"] - 55):chunk["start"]]
            if chunk["label"] == "VENUE" and re.search(r"\b(?:at|in|inside|outside|near|via)\s+(?:the\s+)?$", prefix, re.I):
                if not re.search(r"organizer|organiser|address|contact", local_prefix(text, chunk["start"])) and re.search(LOCATION_WORDS, chunk["raw"], re.I) and not any(chunk["start"] <= value["start"] < chunk["end"] for value in temporal):
                    candidates["venue"].append(evidence(text, chunk["start"], chunk["end"], "nltk_venue_chunk", rank=45))
        if entity_model is not None:
            from .sequence import features, decode
            tokens = language["tokens"]
            x = features(tokens)
            if x:
                for span in decode(text, tokens, entity_model.predict_single(x), entity_model.predict_marginals_single(x)):
                    if span["sequence_score"] >= .65 and not generic_name(span["raw"]):
                        if span["field"] == "venue" and re.search(r"organizer|organiser|address|contact", local_prefix(text, span["start"])):
                            continue
                        span["rank"] = 86 if span["field"] == "event_name" and span["sequence_score"] >= .8 else 70
                        candidates[span.pop("field")].append(span)
    for field, values in candidates.items():
        unique = {}
        for value in values:
            if value["end"] <= value["start"]:
                continue
            key = value["start"], value["end"]
            if key not in unique or value["rank"] > unique[key]["rank"]:
                unique[key] = value
        candidates[field] = sorted(unique.values(), key=lambda value: (-value["rank"], value["start"]))
    return candidates


def extract(text: str, reference_date: str | None = None, mode: str = "hybrid", include_analysis: bool = False, entity_model=None, allow_event: bool = False) -> dict:
    if mode not in ("rules", "hybrid"):
        raise ValueError("mode must be rules or hybrid")
    if not text.strip():
        raise ValueError("Announcement must not be empty")
    if reference_date:
        date.fromisoformat(reference_date)
    language = None
    if mode == "hybrid" or include_analysis:
        from .linguistics import analyze_language
        language = analyze_language(text)
    candidates = _candidates(text, mode, language, entity_model)
    warnings = []

    def warn(code: str, message: str, field=None, severity="notice"):
        if not any(value["code"] == code and value.get("field") == field for value in warnings):
            warnings.append({"code": code, "message": message, "field": field, "severity": severity})

    category = keyword_prediction(text)
    temporal = candidates["date"] + candidates["time"]
    intent = bool(re.search(r"\b(?:join|attend|invited|invitation|host|holding|held|happening|scheduled|starts?|begins?|meet|let['’]s|come|see you|organis\w*|organiz\w*)\b", text, re.I))
    event_like = allow_event or any(category["scores"].values()) or intent and (temporal or candidates["venue"]) or len(temporal) >= 2 and candidates["venue"]
    anchors = re.findall(rf"\b{EVENT_CUE}\b[^.!?\n]{{0,100}}?\b(?:on|at)\s+(?:{DAY}\s+{MONTH}|{MONTH}\s+{DAY}|\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}(?::\d{{2}})?\s*[ap]m)", text, re.I)
    multiple = len(anchors) >= 2 or bool(re.search(r"\b(?:two|multiple|several)\s+(?:separate\s+)?events\b", text, re.I))
    unsupported = not event_like or multiple
    if multiple:
        warn("multiple_events", "This contains more than one event. Analyze each event separately.", severity="warning")
    elif not event_like:
        warn("unsupported_text", "No specific event could be identified in this text.", severity="warning")
    if category["needs_review"] and not unsupported:
        warn("category_overlap", "The event format is unclear; check the category.", "category")
    fields, statuses = {}, {}
    notes = {"missing_year": "Year not specified", "relative_date_without_reference": "Add a reference date to resolve this date", "ambiguous_numeric_date": "Day/month order is unclear", "invalid_date": "Check this calendar date", "relative_weekday_convention": "Uses the next matching weekday from your reference date", "imprecise_date": "A specific day is not stated", "invalid_time": "Check this clock time", "missing_meridiem": "AM/PM is not specified", "imprecise_time": "A precise clock time is not stated"}
    for field in FIELDS:
        values = [value for value in candidates[field] if value["role"] == "event"]
        for value in values:
            if field in ("date", "time"):
                normalized, issue = normalize_date(value["raw"], reference_date) if field == "date" else normalize_time(value["raw"])
                value["normalized"], value["issue"] = normalized, issue
        if values and field in ("event_name", "venue"):
            best = values[0]["rank"]
            values = [value for value in values if value["rank"] == best]
        elif values and any(value["rank"] == 100 for value in values):
            values = [value for value in values if value["rank"] == 100]
        distinct = {}
        for value in values:
            distinct.setdefault(value["normalized"] or value["raw"].casefold(), value)
        selected = next(iter(distinct.values())) if len(distinct) == 1 and not unsupported else None
        fields[field] = selected
        if len(distinct) > 1:
            statuses[field] = {"state": "ambiguous", "message": "Multiple values found — please choose one"}
            warn("ambiguous_" + field, statuses[field]["message"], field)
        elif selected is None:
            statuses[field] = {"state": "missing", "message": "Not mentioned in the announcement"}
            warn("missing_" + field, statuses[field]["message"], field, "info")
        elif selected.get("issue"):
            issue = selected["issue"]
            statuses[field] = {"state": "needs_reference" if issue == "relative_date_without_reference" else "notice", "message": notes[issue]}
            warn(issue, notes[issue], field)
        else:
            statuses[field] = {"state": "ok", "message": None}
    if any(value["role"] == "deadline" for value in candidates["date"]):
        warn("deadline_excluded", "Registration deadlines were excluded from the event date.", "date", "info")
    if not category["label"] and not unsupported and not any(category["scores"].values()):
        category["label"] = "Other event"
    return {"input": text, "reference_date": reference_date, "mode": mode,
            "status": "unsupported" if unsupported else "needs_review" if any(status["state"] in ("ambiguous", "needs_reference") for status in statuses.values()) else "ok",
            "event_like": bool(event_like), "multiple_events": multiple,
            "category": {**category, "label": None if unsupported else category["label"]},
            "fields": fields, "field_status": statuses, "warnings": warnings,
            "candidates": candidates, "analysis": language if include_analysis else None}
