"""Package the standalone, compiled Overleaf report without TeX caches or application files."""
import hashlib
import json
import shutil
import zipfile
from event_nlp.config import ROOT


def main() -> None:
    project = ROOT / "output/overleaf/EventLens_Report"
    layout = json.loads((project / "evidence/layout_verification.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((project / "main.pdf").read_bytes()).hexdigest() == layout["pdf_sha256"], "Verify the latest compiled PDF before packaging"
    preview = ROOT / "output/pdf/EventLens_AAT_Report.pdf"
    preview.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(project / "main.pdf", preview)
    shutil.copy2(preview, project / "compiled_report.pdf")
    allowed = {".tex", ".png", ".jpg", ".json", ".csv", ".md", ".txt", ".ttf"}
    files = [p for p in project.rglob("*") if p.is_file() and (p.suffix in allowed or p.name == "latexmkrc")
             and p.name != "REPORT_MANIFEST.json"]
    files.append(project / "compiled_report.pdf")
    manifest = {"main": "main.tex", "compiler": "XeLaTeX",
                "format_source": "Supplied report-format PDF; no original LaTeX source was available",
                "preview_pages": layout["pages"],
                "first_numbered_page": "Introduction = 1",
                "files": [{"path": p.relative_to(project).as_posix(),
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                          for p in sorted(files)]}
    manifest_file = project / "REPORT_MANIFEST.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive = ROOT / "output/overleaf/EventLens_Overleaf_Report.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files + [manifest_file]:
            z.write(p, p.relative_to(project).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for entry in manifest["files"]:
            assert hashlib.sha256(z.read(entry["path"])).hexdigest() == entry["sha256"]
        assert {"main.tex", "metadata.tex", "formatting.tex", "compiled_report.pdf"}.issubset(z.namelist())
    print(f"Verified {archive}: {len(files)+1} files, {archive.stat().st_size:,} bytes")
    print(f"PDF preview: {preview}")


if __name__ == "__main__":
    main()
