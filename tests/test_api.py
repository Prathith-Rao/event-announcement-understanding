from fastapi.testclient import TestClient

from backend.app import app
from event_nlp import service

client = TestClient(app)


def test_api_returns_evidence_and_analysis():
    text = 'Join the workshop "Data Skills" on 9 May 2027 at 10:00 AM in Room B12.'
    response = client.post("/api/analyze", json={"text":text,"include_analysis":True})
    assert response.status_code == 200
    result = response.json()
    assert result["analysis"]["tokens"]
    for value in result["fields"].values():
        assert text[value["start"]:value["end"]] == value["raw"]
    assert "model_status" in result


def test_api_validation():
    for payload in [{"text":""},{"text":"  "},{"text":"x"*20001},{"text":"workshop", "reference_date":"2027-02-31"}]:
        assert client.post("/api/analyze",json=payload).status_code == 422


def test_model_unavailable_has_labelled_fallback(monkeypatch):
    monkeypatch.setattr(service, "load_model", lambda mode: None)
    result = client.post("/api/analyze",json={"text":'Workshop "Data Skills" on 9 May 2027.'}).json()
    assert "unavailable" in result["model_status"]
    assert "model_unavailable" in {warning["code"] for warning in result["warnings"]}


def test_missing_nltk_resources_returns_actionable_error(monkeypatch):
    def missing(*args, **kwargs):
        raise LookupError("test missing resource")
    monkeypatch.setattr(service,"extract",missing)
    response = client.post("/api/analyze",json={"text":"workshop"})
    assert response.status_code == 503
    assert "download_nltk" in response.json()["detail"]


def test_saved_evaluation_and_methodology():
    assert client.get("/api/evaluation").status_code == 200
    assert "specification" in client.get("/api/methodology").json()
    assert client.get("/api/health").json()["nltk_resources"]
