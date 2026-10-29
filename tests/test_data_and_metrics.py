import pytest

from event_nlp.data import group_records, split_records, leakage_audit, validate_human
from event_nlp.evaluation import extraction_metrics, classification_metrics
from event_nlp.classification import training_vocabulary
from event_nlp.extraction import extract


def test_leakage_is_rejected():
    with pytest.raises(ValueError, match="Leakage"):
        leakage_audit([{"id":"a", "group_id":"same", "text":"First", "split":"train"}, {"id":"b", "group_id":"same", "text":"Second", "split":"test"}])


def test_template_and_near_duplicate_grouping():
    rows = [{"id":"a", "text":"Join the workshop on 12 May 2027 in Main Hall.","group_id":None},
            {"id":"b", "text":"Join the workshop on 14 June 2028 in Main Hall.","group_id":None}]
    group_records(rows)
    assert rows[0]["group_id"] == rows[1]["group_id"]


def test_splits_reproducible_and_cover_groups():
    rows = [{"id":str(i), "text":"Record " + chr(65+i), "group_id":str(i//2), "label":"Workshop" if i%2 else "Meeting"} for i in range(20)]
    first, audit = split_records([dict(row) for row in rows])
    second, _ = split_records([dict(row) for row in rows])
    assert [row["split"] for row in first] == [row["split"] for row in second]
    assert audit["group_overlap"] == 0
    assert set(row["split"] for row in first) == {"train","validation","test"}


def test_train_vocabulary_never_reads_test_sentinel():
    vocabulary = training_vocabulary(["A workshop about models.", "A meeting about budgets."])
    assert "xylophoniczebra" not in vocabulary
    assert "model" in vocabulary


def test_annual_source_templates_group_even_with_different_prose():
    rows = [{"id":"a", "text":"An introductory paragraph about original ideas.", "source_url":"https://example.edu/competition-2025/"},
            {"id":"b", "text":"Participating teams will design remarkable inventions.", "source_url":"https://example.edu/competition-2024/"}]
    group_records(rows)
    assert rows[0]["group_id"] == rows[1]["group_id"]


def test_human_annotations_cannot_be_silent_or_false_evidence():
    row = {"text":"West Hall"}
    with pytest.raises(ValueError, match="reviewer"):
        validate_human(row, {"category":"Workshop"})
    annotation = {"category":"Workshop", "reviewer":"Test fixture", "reviewed_at":"2027-01-01", "decision":"accepted", "fields":{field:None for field in ["event_name","date","time","venue"]}}
    validate_human(row, annotation)
    annotation["fields"]["venue"] = {"raw":"East Hall","start":0,"end":9}
    with pytest.raises(ValueError, match="evidence"):
        validate_human(row, annotation)


def test_wrong_present_extraction_is_fp_and_fn():
    text = 'Seminar "Topic" on 12 May 2027. Venue: West Hall.'
    prediction = extract(text, mode="rules")
    gold = dict(prediction["fields"])
    gold["venue"] = {"raw":"East Hall"}
    metrics = extraction_metrics([{"id":"test", "text":text, "gold":gold}], [prediction])
    assert metrics["fields"]["venue"]["fp"] == 1
    assert metrics["fields"]["venue"]["fn"] == 1


def test_abstentions_are_classification_errors():
    metrics = classification_metrics(["Workshop","Seminar"], [None,"Seminar"])
    assert metrics["accuracy"] == .5
    assert metrics["abstentions"] == 1
    assert metrics["confusion_matrix"][0][-1] == 1
