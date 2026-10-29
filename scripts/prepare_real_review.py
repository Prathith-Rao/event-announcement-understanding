"""Collect public invitation paragraphs and make a blind manual-review packet."""
import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from event_nlp.config import ROOT

OUT=ROOT/"data/real_review"
AGENT="CourseEventNLPResearch/1.0"

def main():
    OUT.mkdir(exist_ok=True)
    s=requests.Session();s.headers["User-Agent"]=AGENT
    robots={};last={};log=[];rows=[];seen=set()
    def fetch(url):
        host=urlparse(url).netloc;base="https://"+host
        def get(u):
            time.sleep(max(0,1.5-(time.monotonic()-last.get(host,0))))
            last[host]=time.monotonic()
            return s.get(u,timeout=18,allow_redirects=False)
        if host not in robots:
            r=get(base+"/robots.txt")
            if r.status_code==200:
                rp=RobotFileParser();rp.parse(r.text.splitlines());robots[host]=rp
            elif r.status_code in [404,410]:robots[host]=None
            else:raise ValueError("robots unavailable")
        rp=robots[host]
        if rp and not rp.can_fetch(AGENT,url):raise ValueError("robots disallowed")
        if rp and (rp.crawl_delay(AGENT) or rp.crawl_delay("*")):time.sleep(rp.crawl_delay(AGENT) or rp.crawl_delay("*"))
        r=get(url)
        if r.status_code!=200:raise ValueError(f"HTTP {r.status_code}")
        return BeautifulSoup(r.content,"html.parser")
    def add(text,url,institution,method):
        key=re.sub(r"\W+","",text.lower())
        if key in seen:return
        seen.add(key)
        rows.append({"id":"review-"+hashlib.sha256((url+text).encode()).hexdigest()[:12],"text":text,
          "source_url":url,"institution":institution,"collection_date":datetime.now(timezone.utc).date().isoformat(),
          "publication_date":None,"provenance":"real","review_status":"pending_human","human":None,
          "group_id":"source-"+hashlib.sha256(url.encode()).hexdigest()[:10],"split":"external_review",
          "collection_method":method,"source_excerpt_hash":hashlib.sha256(text.encode()).hexdigest()})
    seeds=[("https://www.openspace.mit.edu/calendar","MIT Open Space"),
           ("https://ose.stanford.edu/cards","Stanford Office of Student Engagement"),
           ("https://saas.mit.edu/events.html","MIT SAAS"),
           ("https://web.mit.edu/tsmit/www/events.html","MIT Thai Students"),
           ("https://storytelling.stanford.edu/upcoming-events","Stanford Storytelling")]
    queue=list(seeds);visited=set()
    while queue and len(rows)<65 and len(visited)<85:
        url,institution=queue.pop(0)
        if url in visited:continue
        visited.add(url)
        entry={"url":url,"checked_at":datetime.now(timezone.utc).isoformat()}
        try:
            soup=fetch(url)
            if url==seeds[0][0]:
                for a in soup.select("h1 a,h2 a,h3 a"):
                    link=urljoin(url,a.get("href",""))
                    if "/calendar/" in link:queue.append((link,institution))
            for n in soup.select("nav,header,footer,script,style,aside,form"):n.decompose()
            nodes=soup.find_all("p")
            if "ose.stanford.edu" in url:nodes+=soup.find_all("li")
            taken=0
            for n in nodes:
                if n.find(["p","li"]):continue
                text=" ".join(n.get_text(" ",strip=True).split())
                if not 65<=len(text)<=1250:continue
                if re.search(r"[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d ()-]{9,}\d",text):continue
                if not re.search(r"\b(join|invited|invite|come|enjoy|attend|welcome|celebrate|stop by|gather|bring|register|workshop|concert|screening|tournament)\b",text,re.I):continue
                if re.search(r"likeness|cookies policy|privacy|photograph|social media|subscribe|copyright",text,re.I):continue
                add(text,url,institution,"one natural public HTML paragraph/list item; whitespace normalized only")
                taken+=1
                if taken >= (20 if url in [x[0] for x in seeds] else 2):break
            entry.update(status="fetched",accepted=taken)
        except Exception as e:entry.update(status="skipped",reason=str(e))
        log.append(entry)
        print(len(rows),entry["status"],url,flush=True)
    # Preserve existing genuine pilot paragraphs for broader institution coverage.
    pilot=[json.loads(l) for l in (ROOT/"data/real.jsonl").read_text(encoding="utf-8").splitlines()]
    fresh=rows;rows=[]
    for r in pilot:
        key=re.sub(r"\W+","",r["text"].lower())
        if key not in seen:
            seen.add(key);rows.append({**r,"human":None,"review_status":"pending_human","split":"external_review"})
    rows=(rows+fresh)[:100]
    (OUT/"records.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    (OUT/"source_log.jsonl").write_text("".join(json.dumps(r)+"\n" for r in log),encoding="utf-8")
    fields=["event_name","date","time","venue"]
    columns=["id","text","institution","source_url","reviewer","reviewed_at","decision","category","reference_date","notes"]
    columns += [v for f in fields for v in [f+"_presence",f+"_raw",f+"_start",f+"_end"]]+["date_normalized"]
    with (OUT/"annotations.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in ["id","text","institution","source_url"]})
    md=["# Public announcement annotation packet\n\nAll labels are blank. Annotate the supplied text only, not information visible elsewhere on the source page.\n"]
    for i,r in enumerate(rows,1):
        md += [f"## {i}. {r['id']}\n\nSource: {r['source_url']}\n\n{r['text']}\n"]
    (OUT/"ANNOUNCEMENTS.md").write_text("\n".join(md),encoding="utf-8")
    from collections import Counter
    (OUT/"manifest.json").write_text(json.dumps({"records":len(rows),"human_reviewed":0,"institution_distribution":dict(Counter(r["institution"] for r in rows)),"purpose":"Separate external evaluation candidate pool; not used to fit/tune frozen v2; public convenience sample with source/template clustering."},indent=2),encoding="utf-8")
    print("REVIEW PACKET",len(rows),flush=True)

if __name__=="__main__":main()
