"""Independent regression scenarios, separate from both frozen challenge sets."""
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from event_nlp.config import DATA, CATEGORIES, FIELDS
from event_nlp.data import read_jsonl, leakage_audit
from event_nlp.service import analyze, load_model
from event_nlp.temporal import normalize_date, normalize_time

client = TestClient(app)

@pytest.mark.parametrize("category,description", [
    ("Workshop", "hands-on workshop"),
    ("Seminar", "guest lecture"),
    ("Conference", "research conference"),
    ("Webinar", "webinar"),
    ("Competition", "quiz competition"),
    ("Hackathon", "hackathon"),
    ("Meeting", "team meeting"),
    ("Cultural event", "concert"),
    ("Sports event", "football match"),
    ("Exhibition", "photography exhibition"),
    ("Career event", "recruitment drive"),
    ("Community service", "blood donation camp"),
    ("Social gathering", "birthday party"),
    ("Training course", "training course"),
    ("Product launch", "product launch"),
    ("Academic assessment", "final exam"),
    ("Ceremony", "graduation ceremony"),
    ("Tour or excursion", "heritage walk"),
])
def test_expanded_category_coverage(category, description):
    result = analyze(f'Join us for "{description.title()} Day", a {description}, on 17 November 2028 at 3pm in West Hall.')
    assert result["category"]["label"] == category
    assert result["fields"]["date"]["normalized"] == "2028-11-17"
    for value in result["fields"].values():
        if value:
            assert result["input"][value["start"]:value["end"]] == value["raw"]


def test_short_meeting_not_vetoed_by_model_or_missing_name():
    result = analyze("Meeting tomorrow at 6 in my office.")
    assert result["category"]["label"] == "Meeting"
    assert result["fields"]["date"]["raw"] == "tomorrow"
    assert result["fields"]["time"]["raw"] == "6"
    assert result["fields"]["venue"]["raw"] == "my office"
    assert result["fields"]["event_name"] is None
    assert result["field_status"]["date"]["state"] == "needs_reference"
    assert result["field_status"]["event_name"]["state"] == "missing"


def test_venue_format_word_does_not_change_primary_purpose():
    result = analyze('The workshop "Career Skills" is on 15 May 2028 at 9am in Seminar Room 31.')
    assert result["category"]["label"] == "Workshop"
    assert result["fields"]["venue"]["raw"] == "Seminar Room 31"


@pytest.mark.parametrize("text", [
    "Hello there.",
    "Photosynthesis is the process by which plants make food.",
    "I enjoy watching football on television.",
    "Can you explain what a workshop means?",
])
def test_non_announcements_are_rejected(text):
    result = analyze(text)
    assert result["status"] == "unsupported"
    assert result["category"]["label"] is None
    assert all(value is None for value in result["fields"].values())


@pytest.mark.parametrize("raw,reference,expected", [
    ("the 5th of June, 2028", None, "2028-06-05"),
    ("3-5 November 2028", None, "2028-11-03/2028-11-05"),
    ("this Saturday", "2028-06-03", "2028-06-03"),
    ("in three days", "2028-06-03", "2028-06-06"),
    ("day after tomorrow", "2028-12-31", "2029-01-02"),
])
def test_additional_date_forms(raw, reference, expected):
    assert normalize_date(raw, reference)[0] == expected


def test_time_forms_and_invalid_clock():
    assert normalize_time("noon") == ("12:00", None)
    assert normalize_time("7 p.m.") == ("19:00", None)
    assert normalize_time("16:30 IST") == ("16:30 IST", None)
    assert normalize_time("6") == (None, "missing_meridiem")
    assert normalize_time("25:90")[1] == "invalid_time"


def test_weekday_does_not_compete_with_adjacent_absolute_date():
    result = analyze("The conference is on Friday, 12 November 2027 at noon in Skyline Hall.")
    assert result["fields"]["date"]["normalized"] == "2027-11-12"


def test_model_is_genuinely_trained_and_larger_data_is_partitioned():
    bundle = load_model("expanded_v2")
    assert bundle["training_records"] > 5000
    assert len(bundle["labels"]) == len(CATEGORIES) + 1
    assert bundle["entity_crf"].classes_
    rows = read_jsonl(DATA / "expanded_v2/records.jsonl")
    assert len(rows) > 10000
    audit = leakage_audit(rows)
    assert audit["group_overlap"] == audit["normalized_duplicate_overlap"] == 0
    assert all(row["provenance"] == "synthetic" and row.get("human") is None for row in rows)
    for row in rows:
        for value in row["gold"].values():
            if value:
                assert row["text"][value["start"]:value["end"]] == value["raw"]


def test_config_and_api_report_field_intimations():
    assert len(client.get("/api/config").json()["categories"]) == 19
    response = client.post("/api/analyze", json={"text": "Join our meeting tomorrow at 6pm."})
    assert response.status_code == 200
    result = response.json()
    assert result["field_status"]["venue"]["state"] == "missing"
    assert "synthetic" not in result["model_status"].lower()
    assert result["training_metadata"]["provenance"] == "synthetic"


def test_deadline_sentence_ending_in_year_does_not_poison_event_clause():
    result = analyze('Registration closes on 8 May 2028. We are hosting "North Star", a workshop, on 14 May 2028 at 4pm in East Hall.')
    assert result["fields"]["date"]["raw"] == "14 May 2028"
    assert result["fields"]["time"]["raw"] == "4pm"


def test_organizer_address_is_not_recovered_as_a_chunk_venue():
    result = analyze('Join the seminar "North Star" on 14 May 2028. The organizer office is at Old Administration Building.')
    assert result["fields"]["venue"] is None


def test_unfamiliar_proper_venue_and_informal_plan():
    result = analyze("Let's meet for coffee tomorrow at 6pm at Starbucks.")
    assert result["category"]["label"] == "Social gathering"
    assert result["fields"]["venue"]["raw"] == "Starbucks"
