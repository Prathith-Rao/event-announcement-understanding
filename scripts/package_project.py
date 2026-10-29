"""Create a portable course handoff, omitting caches and downloaded runtimes."""
import hashlib
import json
import os
import zipfile

from event_nlp.config import ROOT, DATA


def main():
    archive = ROOT / "EventLens_AAT.zip"
    manifest_path = ROOT / "SUBMISSION_MANIFEST.json"
    ignored = {".venv", "node_modules", "nltk_data", "__pycache__", ".pytest_cache", "tmp", "archive", ".git", ".agents", ".codex", ".aws"}
    files = []
    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in ignored]
        for name in sorted(names):
            path = ROOT / os.path.relpath(os.path.join(directory, name), ROOT)
            if path in (archive, manifest_path) or path.suffix == ".log":
                continue
            content = path.read_bytes()
            files.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    manifest = {"project": "Event Announcement Understanding Using a Hybrid NLP Approach", "collection": json.loads((DATA / "collection_summary.json").read_text(encoding="utf-8")),
                "expanded_dataset": json.loads((DATA / "expanded_v2/manifest.json").read_text(encoding="utf-8")) if (DATA / "expanded_v2/manifest.json").exists() else None,
                "status": "Version 2 operational; expanded synthetic results frozen, independent real-data review pending", "omitted": "Environments, downloads, caches and internal development archive; reinstall from locks and README", "files": files}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for item in files:
            output.write(ROOT / item["path"], item["path"])
        output.write(manifest_path, manifest_path.name)
    with zipfile.ZipFile(archive) as result:
        assert result.testzip() is None
        assert {
            "README.md", "docs/AAT_REPORT.md", "data/real.jsonl",
            "data/expanded_v2/records.jsonl", "models/expanded_v2.pkl",
            "reports/expanded_v2/test_metrics.json", "reports/expanded_v2/extraction_test.json",
            "docs/screenshots/v2-desktop.jpg", "frontend/dist/index.html",
        }.issubset(result.namelist())
    print(f"Created and verified {archive}: {archive.stat().st_size:,} bytes, {len(files) + 1} files")


if __name__ == "__main__":
    main()
