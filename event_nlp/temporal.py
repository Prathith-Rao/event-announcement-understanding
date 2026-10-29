"""Calendar normalization uses an explicit reference, never today's date."""
import re
from datetime import date, timedelta
from dateutil import parser

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
DAY = r"\d{1,2}(?:st|nd|rd|th)?"
WEEKDAY = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
DATE_RE = re.compile(rf"\b(?:\d{{4}}-\d{{2}}-\d{{2}}|(?:the\s+)?{DAY}\s+(?:of\s+)?{MONTH}(?:\s*,?\s*\d{{4}})?|{MONTH}\s+{DAY}(?:\s*,?\s*\d{{4}})?|\d{{1,2}}[/.\-]\d{{1,2}}[/.\-]\d{{4}}|day after tomorrow|tomorrow|tonight|today|yesterday|(?:(?:next|this)\s+)?{WEEKDAY}|in\s+(?:\d+|one|two|three|four|five|six|seven)\s+days?|next week|this weekend)\b", re.I)
DATE_RANGE_RE = re.compile(rf"\b{DAY}\s*(?:-|–|—|to)\s*{DAY}\s+{MONTH}(?:\s*,?\s*\d{{4}})?\b", re.I)
MERIDIEM = r"[ap]\.?m\.?"
CLOCK = rf"\d{{1,2}}(?:(?::|\.)\d{{2}})?\s*(?:{MERIDIEM})?"
TIME_RE = re.compile(rf"\b(?:{CLOCK}\s*(?:-|–|—|to|until)\s*{CLOCK}|\d{{1,2}}(?::|\.)\d{{2}}\s*(?:{MERIDIEM})?|\d{{1,2}}\s*{MERIDIEM}|noon|midnight|\d{{1,2}}\s*o['’]clock)(?:\s+(?:IST|UTC|GMT|EST|EDT|PST|PDT|CET|CEST|BST))?\b", re.I)


def normalize_date(raw: str, reference_date: str | None) -> tuple[str | None, str | None]:
    lower = raw.strip().lower()
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    relative = lower in ("today", "tomorrow", "tonight", "yesterday", "day after tomorrow", "next week", "this weekend") or re.fullmatch(r"(?:(?:next|this)\s+)?" + WEEKDAY, lower, re.I) or re.fullmatch(r"in (?:\d+|one|two|three|four|five|six|seven) days?", lower)
    if relative:
        if not reference_date:
            return None, "relative_date_without_reference"
        reference = date.fromisoformat(reference_date)
        offsets = {"today": 0, "tonight": 0, "tomorrow": 1, "yesterday": -1, "day after tomorrow": 2}
        if lower in offsets:
            return (reference + timedelta(days=offsets[lower])).isoformat(), None
        if lower in ("next week", "this weekend"):
            return None, "imprecise_date"
        if lower.startswith("in "):
            count = lower.split()[1]
            number = int(count) if count.isdigit() else ["zero", "one", "two", "three", "four", "five", "six", "seven"].index(count)
            return (reference + timedelta(days=number)).isoformat(), None
        weekday = next(value for value in weekdays if lower.endswith(value))
        delta = (weekdays.index(weekday) - reference.weekday()) % 7
        if lower.startswith("next ") and delta == 0:
            delta = 7
        return (reference + timedelta(days=delta)).isoformat(), "relative_weekday_convention"
    interval = re.fullmatch(rf"({DAY})\s*(?:-|–|—|to)\s*({DAY})\s+({MONTH})(?:\s*,?\s*(\d{{4}}))?", raw, re.I)
    if interval:
        if not interval[4]:
            return None, "missing_year"
        first, _ = normalize_date(f"{interval[1]} {interval[3]} {interval[4]}", None)
        last, _ = normalize_date(f"{interval[2]} {interval[3]} {interval[4]}", None)
        return (first + "/" + last, None) if first and last and first <= last else (None, "invalid_date")
    if not re.search(r"\b\d{4}\b", raw):
        return None, "missing_year"
    numeric = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", raw)
    if numeric and int(numeric[1]) <= 12 and int(numeric[2]) <= 12 and int(numeric[1]) != int(numeric[2]):
        return None, "ambiguous_numeric_date"
    clean = re.sub(r"\bthe\s+|\bof\s+|(?<=\d)(?:st|nd|rd|th)\b", "", raw, flags=re.I)
    try:
        return parser.parse(clean, dayfirst=bool(numeric), default=parser.parse("2000-01-01")).date().isoformat(), None
    except (ValueError, OverflowError):
        return None, "invalid_date"


def normalize_time(raw: str) -> tuple[str | None, str | None]:
    lower = raw.lower().strip()
    if lower in ("noon", "midnight"):
        return ("12:00" if lower == "noon" else "00:00"), None
    if re.search(r"\s(?:to|until)\s|[-–—]", lower):
        return None, None
    match = re.fullmatch(r"(\d{1,2})(?:(?::|\.)(\d{2}))?\s*([ap])?\.?m?\.?(?:\s+(IST|UTC|GMT|EST|EDT|PST|PDT|CET|CEST|BST))?", raw, re.I)
    if not match:
        return None, "imprecise_time"
    hour, minute = int(match[1]), int(match[2] or 0)
    meridiem = (match[3] or "").lower()
    if minute > 59 or hour > (12 if meridiem else 23) or meridiem and hour == 0:
        return None, "invalid_time"
    if not meridiem and not match[2]:
        return None, "missing_meridiem"
    if meridiem:
        hour = hour % 12 + (12 if meridiem == "p" else 0)
    return f"{hour:02}:{minute:02}" + (" " + match[4].upper() if match[4] else ""), None
