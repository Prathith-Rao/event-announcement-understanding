"""Validate supplied human review and score frozen v2. No training or rule edits."""
import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from event_nlp.config import ROOT, MODEL_LABELS, FIELDS
from event_nlp.service import analyze, load_model, active_mode
from event_nlp.evaluation import classification_metrics, extraction_metrics
from scripts.train_expanded import predict_models

OUT=ROOT/"reports/real_review_v1"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")

def import_annotations(path):
    original={r["id"]:r for r in map(json.loads,(ROOT/"data/real_review/records.jsonl").read_text(encoding="utf-8").splitlines())}
    with path.open(encoding="utf-8-sig",newline="") as f:raw=list(csv.DictReader(f))
    assert len(raw)==len(original) and len({r["id"] for r in raw})==len(raw)
    corrections=[];accepted=[];all_rows=[]
    canonical={c.casefold():c for c in MODEL_LABELS}
    generic={"workshop","meetings","festival","concert series","conference","session","printmaking"}
    # Explicit source-only repairs: copied values from adjacent rows and raw/normalized mix-ups.
    manual={
        5:{"venue":None},
        18:{"event_name":"HSUHK Social Innovation Competition"},
        20:{"event_name":None},
        21:{"event_name":"HSMC Innovation Project Competition"},
        24:{"event_name":"College Faculty Meeting"},
        37:{"date":"Sunday October 4"},
        43:{"time":"7pm"},
        49:{"time":"5 PM"},
        58:{"venue":"Narnia"},
        59:{"venue":"Stanford’s O’Donohue Family Farm"},
        60:{"venue":None},
    }
    for i,r in enumerate(raw,1):
        source=original[r["id"]]
        assert r["text"]==source["text"],f"Original input edited: {i}"
        assert r["reviewer"].strip() and datetime.fromisoformat(r["reviewed_at"]).utcoffset() is not None
        assert r["decision"] in ["accepted","excluded","needs_review"]
        label=canonical.get(r["category"].strip().casefold())
        if r["decision"]=="accepted":assert label,f"Missing accepted category {i}"
        if label!=r["category"] and r["category"]:corrections.append({"id":r["id"],"field":"category","from":r["category"],"to":label,"reason":"canonical category capitalization"})
        gold={};presence={}
        for field in FIELDS:
            value=r[field+"_raw"];state=r[field+"_presence"]
            before={"presence":state,"raw":value,"start":r[field+"_start"],"end":r[field+"_end"]}
            if r["decision"]=="accepted":
                if value.casefold().strip() in generic or label=="Not an event":value=""
                if field in manual.get(i,{}):value=manual[i][field] or ""
                state="present" if value else "missing"
            elif state=="pesent":state="present"
            if value:
                if value not in r["text"]:
                    # Nonaccepted rows are retained as unresolved, not promoted to gold.
                    assert r["decision"]!="accepted",f"Evidence absent in row {i}: {field}"
                    gold[field]=None;presence[field]=state;continue
                starts=[m.start() for m in re.finditer(re.escape(value),r["text"])]
                declared=int(r[field+"_start"]) if r[field+"_start"].isdigit() else None
                if len(starts)==1:start=starts[0]
                else:
                    assert declared is not None,f"Repeated evidence needs an offset: {i}/{field}"
                    start=min(starts,key=lambda a:abs(a-declared))
                gold[field]={"raw":value,"start":start,"end":start+len(value),"normalized":None}
            else:gold[field]=None
            after={"presence":state,"raw":value,"start":gold[field]["start"] if gold[field] else None,"end":gold[field]["end"] if gold[field] else None}
            # Blank offsets filled mechanically are recorded alongside corrections.
            if before!=after:corrections.append({"id":r["id"],"field":field,"from":before,"to":after,"reason":"source-evidence validation / deterministic span completion"})
            presence[field]=state
        row={**source,"label":label,"gold":gold,"review_status":"reviewed" if r["decision"]=="accepted" else r["decision"],
             "reference_date":r["reference_date"] or None,
             "expected_status":"unsupported" if label=="Not an event" else "ok",
             "human":{"reviewer":r["reviewer"],"reviewed_at":r["reviewed_at"],"decision":r["decision"],
                      "submitted_category":r["category"],"fields":gold,"field_presence":presence,"notes":r["notes"]},
             "label_origin":"human CSV with separately logged source-only validation"}
        all_rows.append(row)
        if r["decision"]=="accepted":accepted.append(row)
    assert all(row["text"][v["start"]:v["end"]]==v["raw"] for row in accepted for v in row["gold"].values() if v)
    return raw,all_rows,accepted,corrections

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--annotations",required=True);a=ap.parse_args()
    if (OUT/"metrics.json").exists():raise SystemExit("Real review run already frozen; use a new version for a different evaluation.")
    OUT.mkdir(exist_ok=True)
    source=Path(a.annotations)
    raw,all_rows,rows,corrections=import_annotations(source)
    # Preserve original review privately in archive; don't publish reviewer identities automatically.
    private=ROOT/"archive/human_review_original";private.mkdir(exist_ok=True)
    shutil.copy2(source,private/source.name)
    save("annotation_validation.json",{"input_sha256":sha(source),"rows":len(raw),"decisions":dict(Counter(r["decision"] for r in raw)),"accepted":len(rows),"corrections":corrections})
    # Public gold omits reviewer identity/timestamp; provenance/decision remain available.
    save("gold.json",[{k:v for k,v in row.items() if k not in ["human","proposed"]} for row in rows])
    save("review_decisions.json",[{"id":r["id"],"decision":r["human"]["decision"],"notes":r["human"]["notes"]} for r in all_rows])
    assert active_mode()=="expanded_v2"
    model=ROOT/"models/expanded_v2.pkl";before=sha(model)
    core={p.name:sha(p) for p in (ROOT/"event_nlp").glob("*.py")}
    bundle=load_model("expanded_v2");texts=[r["text"] for r in rows];truth=[r["label"] for r in rows]
    values=predict_models(bundle,texts)
    predictions={}
    for method in ["rules","hybrid"]:
        predictions[method]=[analyze(r["text"],r["reference_date"],extraction_mode=method) for r in rows]
        save("predictions_"+method+".json",[{"id":r["id"],**p} for r,p in zip(rows,predictions[method])])
    values["hybrid_context"]=[p["category"]["label"] or "Not an event" for p in predictions["hybrid"]]
    save("classification_predictions.json",[{"id":r["id"],"truth":r["label"],"predictions":{name:v[i] for name,v in values.items()}} for i,r in enumerate(rows)])
    supported=[c for c in MODEL_LABELS if c in truth]
    metrics={}
    for name,v in values.items():
        metrics[name]=classification_metrics(truth,v,MODEL_LABELS)
        metrics[name]["supported_class_macro"]=classification_metrics(truth,v,supported)
    fresh=[i for i,r in enumerate(rows) if r["id"].startswith("review-")]
    new_truth=[truth[i] for i in fresh];new_labels=[c for c in MODEL_LABELS if c in new_truth]
    new_metrics={name:classification_metrics(new_truth,[v[i] for i in fresh],new_labels) for name,v in values.items()}
    result={"provenance":"real","annotation":"single human reviewer; source-span validation; no model-derived gold",
      "input_sha256":sha(source),"records_supplied":len(raw),"accepted":len(rows),"decisions":dict(Counter(r["decision"] for r in raw)),
      "class_counts":dict(Counter(truth)),"supported_labels":supported,"institution_distribution":dict(Counter(r["institution"] for r in rows)),
      "source_pages":len({r["source_url"] for r in rows}),"source_groups":len({r["group_id"] for r in rows}),
      "new_post_freeze_records":len(fresh),"new_post_freeze_metrics":new_metrics,"models":metrics,
      "extraction":{method:extraction_metrics(rows,p) for method,p in predictions.items()},
      "model_sha256":before,"code_sha256":core,"training_performed":False,
      "limitations":"Convenience sample, source and template clusters, unsupported classes and sparse fields; single reviewer, no inter-annotator agreement; pilot examples predate model freeze."}
    assert before==sha(model) and core=={p.name:sha(p) for p in (ROOT/"event_nlp").glob("*.py")}
    save("metrics.json",result)
    print(json.dumps({"accepted":len(rows),"classes":len(supported),"new_only":len(fresh),
        "classifiers":{k:{"accuracy":v["accuracy"],"macro20":v["macro_f1"],"supported_macro":v["supported_class_macro"]["macro_f1"]} for k,v in metrics.items()},
        "extraction":{k:{"complete":v["complete_record_accuracy"],"f1":{f:m["f1"] for f,m in v["fields"].items()},"support":{f:m["present_gold"] for f,m in v["fields"].items()}} for k,v in result["extraction"].items()}},indent=2))

if __name__=="__main__":main()
