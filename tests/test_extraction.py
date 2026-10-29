import pytest

from event_nlp.extraction import extract, normalize_date
from event_nlp.linguistics import analyze_language, preprocess


@pytest.mark.parametrize("mode", ["rules", "hybrid"])
def test_fields_and_exact_source_spans(mode):
    text = 'Join the workshop "Data Skills" on 9 May 2027 at 10:00 AM in Room B12.'
    result = extract(text, mode=mode, include_analysis=True)
    assert result["fields"]["event_name"]["raw"] == "Data Skills"
    assert result["fields"]["date"]["normalized"] == "2027-05-09"
    assert result["fields"]["time"]["raw"] == "10:00 AM"
    assert result["fields"]["venue"]["raw"] == "Room B12"
    for values in result["candidates"].values():
        for value in values:
            assert text[value["start"]:value["end"]] == value["raw"]
    assert result["analysis"]["tokens"]


@pytest.mark.parametrize("mode", ["rules", "hybrid"])
def test_deadline_is_not_event_date(mode):
    result = extract('Register by 4 May 2027; the workshop "Data Skills" will be held on 9 May 2027 at 10:00 AM. Venue: West Hall.', mode=mode)
    assert result["fields"]["date"]["raw"] == "9 May 2027"
    assert result["candidates"]["date"][0]["role"] == "deadline"
    assert "deadline_excluded" in {warning["code"] for warning in result["warnings"]}


@pytest.mark.parametrize("raw,reference,expected,issue", [
    ("tomorrow",None,None,"relative_date_without_reference"),
    ("tomorrow","2027-12-31","2028-01-01",None),
    ("next Monday","2027-05-10","2027-05-17","relative_weekday_convention"),
    ("8 June",None,None,"missing_year"),
    ("03/04/2027",None,None,"ambiguous_numeric_date"),
    ("31 February 2027",None,None,"invalid_date"),
    ("2027-02-28",None,"2027-02-28",None),
    ("14/05/2027",None,"2027-05-14",None),
])
def test_date_conservatism(raw, reference, expected, issue):
    assert normalize_date(raw, reference) == (expected, issue)


def test_missing_fields_and_unrelated_abstention():
    result = extract('Join the seminar "New Ideas" on 8 June.')
    assert result["fields"]["time"] is None
    assert result["fields"]["venue"] is None
    result = extract("The library has acquired three new books.")
    assert result["status"] == "unsupported"
    assert all(value is None for value in result["fields"].values())


def test_multiple_events_and_ambiguous_dates():
    result = extract("A workshop on 10 May 2027 at 9:00 AM is followed by a seminar on 11 May 2027 at 2:00 PM.")
    assert result["status"] == "unsupported"
    result = extract('Seminar "Research" on 10 May 2027 or 11 May 2027 at 10:00 AM or 2:00 PM. Venue: West Hall.')
    assert result["fields"]["date"] is None
    assert result["fields"]["time"] is None


def test_address_distractor():
    result = extract('Organizer address: at Old Hall. Join the seminar "Research" on 10 May 2027. Venue: New Hall.')
    assert result["fields"]["venue"]["raw"] == "New Hall"


def test_real_nltk_analysis_and_separate_preprocessing():
    text = "Students are building models in Room B12. They discussed ideas."
    language = analyze_language(text)
    assert len(language["sentences"]) == 2
    assert any(token["pos"] == "VBG" for token in language["tokens"])
    assert any(token["text"] == "B12" for token in language["tokens"])
    assert language["chunks"]
    processed = preprocess(text)
    assert "student" in processed and "build" in processed
    assert "B12" not in processed


def test_expanded_venue_rules_and_hybrid_both_find_pavilions():
    text = 'Join the workshop "Robotics" on 10 May 2027 at 10:00 AM inside Rose Pavilion.'
    assert extract(text, mode="rules")["fields"]["venue"]["raw"] == "Rose Pavilion"
    result = extract(text, mode="hybrid")
    assert result["fields"]["venue"]["raw"] == "Rose Pavilion"


def test_empty_input():
    with pytest.raises(ValueError):
        extract("  ")


def test_generic_event_format_is_not_a_name():
    result = extract("Join the workshop and seminar on 10 October 2027 at 10:00 AM. Venue: Main Hall.")
    assert result["fields"]["event_name"] is None
    assert result["category"]["needs_review"]
