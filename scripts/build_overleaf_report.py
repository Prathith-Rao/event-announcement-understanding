"""Build report chapters from saved evidence without rerunning experiments."""
from pathlib import Path
import json
import re
import shutil
from event_nlp.config import ROOT

OUT = ROOT / "output/overleaf/EventLens_Report"

def tex(text: str) -> str:
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
               "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}
    text = "".join(mapping.get(c, c) for c in text)
    text = text.replace("–", "--").replace("—", "---").replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)

def convert(lines: list[str]) -> str:
    output, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                row = [c.strip() for c in lines[i].strip("|").split("|")]
                if not all(re.fullmatch("[-: ]+", c) for c in row):
                    rows.append(row)
                i += 1
            if rows and "Input excerpt" in rows[0]:
                output.append(r"\begin{enumerate}")
                for row in rows[1:4]:
                    output.append(r"\item " + tex(f"{row[1]} ({row[0]}): expected {row[3]}; predicted {row[4]}."))
                output.append(r"\end{enumerate}")
                continue
            n = len(rows[0])
            columns = "p{.25\\textwidth}X" if n == 2 else "X" + "r" * (n - 1)
            if n == 7:
                columns = "p{.12\\textwidth}p{.20\\textwidth}" + "r" * 5
            long = n == 2
            if long:
                columns = r"p{.25\textwidth}p{.69\textwidth}"
                output += [r"\begingroup\small\begin{longtable}{" + columns + r"}\toprule"]
            else:
                output += [r"\begin{center}\small\renewcommand{\arraystretch}{1.12}",
                           r"\begin{tabularx}{\textwidth}{" + columns + r"}\toprule"]
            output.append(" & ".join(r"\textbf{" + tex(c) + "}" for c in rows[0]) + r"\\\midrule")
            output += [" & ".join(tex(c) for c in row) + r"\\" for row in rows[1:]]
            output += [r"\bottomrule\end{longtable}\endgroup"] if long else [r"\bottomrule\end{tabularx}", r"\end{center}"]
            continue
        if line.startswith("### "):
            title = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", line[4:])
            command = "subsection" if title in ["Actual validation errors", "Actual test errors"] else "section"
            output.append("\\" + command + "{" + tex(title) + "}")
        elif line.startswith("!["):
            alt, _ = re.match(r"!\[(.*?)\]\((.*?)\)", line).groups()
            asset = {"Class counts and lengths": "coverage.png", "POS distributions": "pos.png",
                     "Revised application": "application.jpg"}[alt]
            if alt == "Revised application":
                output += [r"\section{Output (screenshots)}",
                           "The actual interface shows an informal picnic announcement, its category, supported date/time normalization, venue evidence, and an inline notice for the missing name."]
            output += [r"\begin{figure}[!htbp]\centering",
                       r"\includegraphics[width=\textwidth,height=.78\textheight,keepaspectratio]{assets/" + asset + "}",
                       r"\caption{" + tex(alt) + r". Actual saved project artifact.}", r"\end{figure}"]
            if alt == "Revised application":
                output += [r"\begin{figure}[!htbp]\centering",
                           r"\includegraphics[width=.88\textwidth,height=.55\textheight,keepaspectratio,trim={790 455 25 393},clip]{assets/application.jpg}",
                           r"\caption{Detail of the result fields and missing-name notice from the same screenshot.}",
                           r"\end{figure}"]
        else:
            output.append(tex(line) if line.strip() else "")
        i += 1
    return "\n".join(output)

def main() -> None:
    for folder in ["assets", "chapters", "evidence"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    result = ROOT / "reports/expanded_v2"
    for name in ["manifest.json", "test_metrics.json", "validation_metrics.json",
                 "extraction_test.json", "extraction_validation.json", "performance.json"]:
        shutil.copy2(result / name, OUT / "evidence" / name)
    for source, name in [
        ("reports/expanded_v2/corpus/coverage_lengths.png", "coverage.png"),
        ("reports/expanded_v2/corpus/pos_distribution.png", "pos.png"),
        ("reports/expanded_v2/confusion_test_logistic_word_char.png", "confusion.png"),
        ("docs/screenshots/v2-desktop.jpg", "application.jpg")]:
        shutil.copy2(ROOT / source, OUT / "assets" / name)
    source = (ROOT / "docs/AAT_REPORT.md").read_text(encoding="utf-8")
    source = re.sub(r"The user authorized broader categories.*?exports\.", "", source, flags=re.S)
    source = source.replace("Version 1 had five categories, 80 synthetic development records and narrow phrase rules. Its keyword gate could veto the learned classifier and reject unfamiliar sentences. The revised system targets", "The system targets")
    source = source.replace("**{'train': 7152, 'test': 2384, 'validation': 2386}**", "**7,152 train, 2,386 validation and 2,384 test examples**")
    for old, new in [("logistic_preprocessed", "LR lemmas"), ("logistic_word_char", "LR word+char"),
                     ("logistic_raw", "LR raw"), ("hybrid_context", "Hybrid context"), ("nltk_nb", "NLTK NB")]:
        source = source.replace(old, new)
    source = source.replace("| held-out test |", "| test |")
    parts = re.split(r"^## \d+\. .+$", source, flags=re.M)[1:]
    parts[-1] = parts[-1].split("## References")[0]
    titles = ["Introduction and Problem Statement", "Design Approach", "System Requirements", "Implementation", "Conclusion"]
    filenames = ["01_introduction", "02_design", "03_requirements", "04_implementation", "05_conclusion"]
    for index, (title, filename, part) in enumerate(zip(titles, filenames, parts)):
        body = r"\chapter{" + title + "}\n"
        if index == 0:
            body += r"\section{Problem statement}" + "\n"
        if index == 3:
            body += r"\input{supplements/algorithm}" + "\n"
        body += convert(part.strip().splitlines())
        body = body.replace("[1]", r"\cite{crf}")
        body += "\n" + r"\input{supplements/" + filename + "}\n"
        (OUT / "chapters" / (filename + ".tex")).write_text(body, encoding="utf-8")
    test = json.loads((result / "test_metrics.json").read_text(encoding="utf-8"))["models"]
    output = r"\begin{center}\small\begin{tabularx}{\textwidth}{Xrrrr}\toprule Class & P & R & F1 & Support\\\midrule" + "\n"
    for category, m in test["logistic_word_char"]["per_class"].items():
        output += tex(category) + " & " + " & ".join(f"{m[k]:.4f}" for k in ["precision", "recall", "f1-score"]) + f" & {int(m['support'])}" + r"\\" + "\n"
    output += r"\bottomrule\end{tabularx}\end{center}"
    (OUT / "evidence/per_class.tex").write_text(output, encoding="utf-8")
    from scripts.restyle_report_figures import main as restyle_figures
    restyle_figures()
    print(f"Prepared chapters and evidence: {OUT}")

if __name__ == "__main__":
    main()
