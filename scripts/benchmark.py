"""Small local HTTP benchmark; not a claim about every computer or text length."""
import json
import statistics
import time

import requests
from event_nlp.config import REPORTS

CASES = [
    "Meeting tomorrow at 6pm in my office.",
    "Let's meet for coffee tomorrow at 6pm at Starbucks.",
    'The workshop "Data Skills" is on 9 May 2028 at 10am in Room B12.',
    "The football match takes place on 22 November 2028 at 6pm in City Stadium.",
    "Career Connect is a recruitment drive on 24 November 2028 at 10:30 AM in Central Hall.",
    "I enjoy reading books about football.",
]

if __name__ == "__main__":
    session = requests.Session()
    session.trust_env = False
    first_start = time.perf_counter()
    session.get("http://127.0.0.1:8000/api/health", timeout=30).raise_for_status()
    times = []
    for _ in range(10):
        for text in CASES:
            start = time.perf_counter()
            response = session.post("http://127.0.0.1:8000/api/analyze", json={"text": text, "reference_date": "2028-05-01"}, timeout=30)
            response.raise_for_status()
            times.append((time.perf_counter() - start) * 1000)
    result = {"scope": "Warm local HTTP requests, six short regression sentences, 60 requests; excludes browser rendering",
              "requests": len(times), "median_ms": statistics.median(times), "p95_ms": statistics.quantiles(times, n=100, method="inclusive")[94],
              "minimum_ms": min(times), "maximum_ms": max(times), "failures": 0}
    (REPORTS / "expanded_v2/performance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
