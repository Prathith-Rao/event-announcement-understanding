"""Small, rate-limited, robots-aware collector. Never bypass a denied source."""
import argparse
import hashlib
import json
import re
import time
from collections import Counter, deque
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from event_nlp.config import DATA
from event_nlp.data import read_jsonl, write_jsonl, group_records, fingerprint
from event_nlp.extraction import EVENT_CUE, DATE_RE, extract

AGENT = "CourseEventNLPResearch/1.0"


def clean_paragraphs(html: str) -> tuple[list[str], BeautifulSoup]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("nav, header, footer, script, style, noscript, form, aside, .breadcrumb, .breadcrumbs"):
        node.decompose()
    main = soup.select_one("article, main, [role=main], .entry-content") or soup
    paragraphs = []
    # Keep natural paragraphs, not a concatenation of title/date/venue tables.
    for node in main.find_all("p"):
        paragraph = " ".join(node.get_text(" ", strip=True).split())
        if (65 <= len(paragraph) <= 1800 and re.search(EVENT_CUE + r"|cultural|dance|music|performance", paragraph, re.I)
                and not re.search(r"[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d ()-]{9,}\d", paragraph)
                and not re.search(r"cookie|privacy policy|all rights reserved|subscribe|non-disclosure|NDAs|IP attorney|judging rubric|Canvas Learning|course material|\(i\) Name|^Awards\b|^Criteria\b", paragraph, re.I)):
            paragraphs.append(paragraph)
    return paragraphs, soup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--max-pages", type=int, default=90)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--discover-existing", action="store_true", help="Revisit seed pages to discover additional event links during expansion")
    parser.add_argument("--refresh-existing", action="store_true", help="Re-select natural paragraphs for unreviewed source pages; preserve previous records in collection corrections")
    args = parser.parse_args()
    if args.limit < 1 or args.delay < 1:
        parser.error("Positive limit and delay >= 1 second required")
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    rows = read_jsonl(DATA / "real.jsonl")
    seen_texts = {fingerprint(row["text"]) for row in rows}
    visited = {row["source_url"] for row in rows}
    frontier_path = DATA / "collection_frontier.json"
    frontier = json.loads(frontier_path.read_text(encoding="utf-8")) if frontier_path.exists() else []
    queue = deque(sources + frontier)
    by_page = {row["source_url"].split("?")[0].rstrip("/"): row for row in rows}
    existing_pages = {row["source_url"].split("?")[0].rstrip("/") for row in rows}
    existing_pages.update(row["source_url"].split("?")[0].rstrip("/") for row in read_jsonl(DATA / "excluded.jsonl"))
    if args.discover_existing:
        visited = set()
    if args.refresh_existing:
        visited = set()
        queue = deque({"url": row["source_url"], "institution": row["institution"], "link_pattern": "$^"} for row in rows if not row.get("human"))
    robots_cache, last_request = {}, {}
    session = requests.Session()
    session.headers["User-Agent"] = AGENT
    log_path = DATA / "source_log.jsonl"

    def fetch(url):
        domain = urlparse(url).netloc
        time.sleep(max(0, args.delay - (time.monotonic() - last_request.get(domain, 0))))
        last_request[domain] = time.monotonic()
        return session.get(url, timeout=20, allow_redirects=False)

    def permitted(url):
        base = urlparse(url)._replace(path="", params="", query="", fragment="").geturl()
        if base not in robots_cache:
            response = fetch(base + "/robots.txt")
            if response.status_code in (404, 410):
                robots_cache[base] = None
            elif response.status_code == 200:
                robot = RobotFileParser()
                robot.parse(response.text.splitlines())
                robots_cache[base] = robot
            else:
                raise RuntimeError(f"robots.txt unavailable ({response.status_code}); skipped conservatively")
        robot = robots_cache[base]
        if robot is not None:
            delay = robot.crawl_delay(AGENT) or robot.crawl_delay("*") or 0
            if delay > args.delay:
                time.sleep(delay - args.delay)
        return robot is None or robot.can_fetch(AGENT, url)

    attempts = 0
    while queue and len(rows) < args.limit and attempts < args.max_pages:
        source = queue.popleft()
        url = source["url"]
        if url in visited:
            continue
        visited.add(url)
        attempts += 1
        log = {"url": url, "institution": source["institution"], "checked_at": datetime.now(timezone.utc).isoformat(), "user_agent": AGENT}
        try:
            if not permitted(url):
                raise RuntimeError("robots_disallowed")
            response = fetch(url)
            log["http_status"] = response.status_code
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}; no redirect/access bypass attempted")
            if "text/html" not in response.headers.get("content-type", ""):
                raise RuntimeError("Non-HTML source not supported by this collector")
            paragraphs, soup = clean_paragraphs(response.content)
            publication = soup.select_one('meta[property="article:published_time"], meta[name="date"]')
            log["robots_permission"] = "allowed_or_no_robots_file"
            # One record per source page; choose the strongest naturally occurring announcement paragraph.
            def paragraph_score(paragraph):
                invitation = bool(re.search(r"invite|inviting|join us|welcome|delighted|will (?:be held|take place)|is (?:organising|organizing)|aims to promote", paragraph, re.I))
                named = bool(re.search(r"[A-Z][\w-]+(?:\s+[A-Z][\w-]+){1,7}\s+(?:Workshop|Seminar|Competition|Meeting|Festival)|(?:Workshop|Seminar|Competition|Meeting)\s+(?:on|entitled)", paragraph))
                schedule = len(DATE_RE.findall(paragraph)) >= 4
                return 6 * invitation + 4 * named + 3 * bool(DATE_RE.search(paragraph)) - 12 * schedule
            paragraphs.sort(key=paragraph_score, reverse=True)
            log["candidate_paragraphs"] = len(paragraphs)
            old = by_page.get(url.split("?")[0].rstrip("/"))
            if args.refresh_existing and old:
                seen_texts.discard(fingerprint(old["text"]))
            for paragraph in paragraphs if args.refresh_existing or url.split("?")[0].rstrip("/") not in existing_pages else []:
                if fingerprint(paragraph) in seen_texts:
                    continue
                result = extract(paragraph, mode="rules")
                identifier = "real-" + hashlib.sha256((url + paragraph).encode()).hexdigest()[:12]
                record = {"id": old["id"] if args.refresh_existing and old else identifier, "text": paragraph, "institution": source["institution"], "source_url": url,
                             "collection_date": datetime.now(timezone.utc).date().isoformat(),
                             "publication_date": publication.get("content") if publication else None,
                             "proposed": {"category": result["category"]["label"], "fields": result["fields"]},
                             "provenance": "real", "review_status": "needs_review" if result["status"] != "ok" else "suggested",
                             "human": None, "group_id": None, "split": "unassigned",
                             "collection_method": "single natural HTML paragraph; whitespace normalized; no metadata appended",
                             "source_excerpt_hash": hashlib.sha256(paragraph.encode()).hexdigest()}
                if args.refresh_existing and old:
                    if old["text"] != paragraph:
                        with (DATA / "collection_corrections.jsonl").open("a", encoding="utf-8") as file:
                            file.write(json.dumps({"id": old["id"], "kind": "paragraph reselection after automated pilot quality screen", "previous_record": old, "new_text": paragraph, "origin": "automated; human review pending"}, ensure_ascii=False) + "\n")
                    rows[rows.index(old)] = record
                else:
                    rows.append(record)
                seen_texts.add(fingerprint(paragraph))
                existing_pages.add(url.split("?")[0].rstrip("/"))
                log["record_id"] = identifier
                break
            for anchor in [] if args.refresh_existing else soup.find_all("a", href=True):
                link = urljoin(url, anchor["href"]).split("#")[0].split("?")[0]
                if urlparse(link).netloc == urlparse(url).netloc and re.search(source["link_pattern"], urlparse(link).path) and link not in visited:
                    queue.append({**source, "url": link})
            log["status"] = "collected" if "record_id" in log else "no_eligible_natural_paragraph"
        except (requests.RequestException, RuntimeError, ValueError) as error:
            log["status"] = "skipped"
            log["reason"] = str(error)
        with log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(log, ensure_ascii=False) + "\n")
        print(f"{len(rows)}/{args.limit} {log['status']}: {url}", flush=True)
        write_jsonl(DATA / "real.jsonl", group_records(rows))
    frontier_path.write_text(json.dumps(list(queue), indent=2), encoding="utf-8")
    summary = {"actual_count": len(rows), "requested_count": args.limit, "institutions": dict(Counter(row["institution"] for row in rows)),
               "proposed_categories": dict(Counter(row["proposed"]["category"] or "needs_review" for row in rows)),
               "human_reviewed": sum(row.get("human") is not None for row in rows), "new_page_attempts": attempts}
    (DATA / "collection_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
