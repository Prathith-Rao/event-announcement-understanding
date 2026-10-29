"""Add saved real-data results to the current personalized report, not a fresh template."""
import json
import shutil
from pathlib import Path
from event_nlp.config import ROOT

def main():
    directory=ROOT/"reports/real_review_v1"
    m=json.loads((directory/"metrics.json").read_text(encoding="utf-8"))
    r=ROOT/"output/overleaf/EventLens_Report"
    names={"majority":"Majority","keywords":"Keyword rules","nltk_nb":"NLTK NB",
           "logistic_raw":"LR raw","logistic_preprocessed":"LR lemmas",
           "logistic_word_char":"LR words+chars","hybrid_context":"Hybrid context"}
    text=r"""\Needspace{.42\textheight}
\section{Separate real-announcement evaluation}
The completed single-reviewer annotation file covers 82 public-source excerpts. Of these, 59
are accepted for scoring, 19 remain unresolved and four are excluded. Original input text is
preserved, with exact source spans validated before evaluation. Models, vocabulary, thresholds
and extraction rules are frozen; no real records are used for training or model selection.
The accepted sample contains 12 of the 20 target labels and comes from 33 source pages.

\subsection{Classification on reviewed real text}
\begin{center}\setlength{\tabcolsep}{4pt}
\begin{tabularx}{\textwidth}{Xrrrr}\toprule
Model & Accuracy & Macro P & Macro R & Macro F1\\\midrule
"""
    for name,v in m["models"].items():
        a=v["supported_class_macro"]
        text+=names[name]+" & "+" & ".join(f"{a[k]:.4f}" for k in ["accuracy","macro_precision","macro_recall","macro_f1"])+r"\\"+"\n"
    text+=r"""\bottomrule\end{tabularx}\end{center}
These macro averages use the 12 labels present in this real sample; eight absent labels are
not silently interpreted as measured classes. For the fixed 20-label convention, macro F1 is
0.2422 for word/character LR, 0.1707 for NB, and 0.2862 for hybrid context. The 12-label averages
above and synthetic 20-label averages therefore have different class coverage.

Word/character LR gets 28 of 59 correct (47.46\%), while the complete hybrid gets 32 (54.24\%).
Naive Bayes gets 12 (20.34\%), despite 1.0000 validation macro F1 on authored synthetic data.
The real sample therefore exposes substantial domain shift. Keyword rules match the hybrid's
accuracy and have higher supported-class macro F1. Lemmatization has lower real accuracy than
raw-word LR; the default is retained as frozen rather than selected again using this evaluation.

\subsection{Coverage and previously unseen collection}
\begin{center}\begin{tabularx}{\textwidth}{XrXr}\toprule
Class & n & Class & n\\\midrule
"""
    counts=list(m["class_counts"].items())
    for i in range(0,len(counts),2):
        a,b=counts[i:i+2];text+=f"{a[0]} & {a[1]} & {b[0]} & {b[1]}"+r"\\"+"\n"
    text+=r"""\bottomrule\end{tabularx}\end{center}
Of the accepted records, 25 come from the earlier collection pilot and 34 were collected after
the model/rules freeze. The pilot had been available for development inspection, so the following
new-only slice is reported separately. All 34 remain outside fitting and tuning.

\begin{center}\begin{tabularx}{\textwidth}{Xrr}\toprule
Model & New-only accuracy & Macro F1 (9 labels)\\\midrule
"""
    for name,v in m["new_post_freeze_metrics"].items():
        text+=f"{names[name]} & {v['accuracy']:.4f} & {v['macro_f1']:.4f}"+r"\\"+"\n"
    text+=r"""\bottomrule\end{tabularx}\end{center}
On the new-only slice, raw-word LR has the highest measured accuracy (0.5000); hybrid accuracy
is 0.3235. These descriptive rankings use a small, source-clustered sample, not a new model-selection
round. Non-event recall is zero on the two accepted negative examples for both the default
word/character model and hybrid system; this tiny denominator makes the rejection gap visible
but does not estimate population rejection performance precisely.

\subsection{Extraction on reviewed real text}
\begin{center}\setlength{\tabcolsep}{4pt}
\begin{tabularx}{\textwidth}{Xrrrrr}\toprule
Field & Gold n & P & R & F1 & Exact\\\midrule
"""
    for field,v in m["extraction"]["hybrid"]["fields"].items():
        text+=field.replace("_"," ")+f" & {v['present_gold']} & "+" & ".join(f"{v[k]:.4f}" for k in ["precision","recall","f1","exact_match"])+r"\\"+"\n"
    text+=r"""\bottomrule\end{tabularx}\end{center}
Rules-only and hybrid return the same selected field values on these 59 inputs, yielding identical
field metrics and complete-record accuracy of 0.3559 (21/59). Thus the added linguistic/CRF
candidates provide no measured improvement on this real sample. Missing-field notice accuracy
is 0.9185. There are only three present clock times, so time F1 of 0.8000 has very limited support.
Of 236 field slots, 184 are missing in the annotations; present-field F1 is needed alongside
exact match to avoid hiding false extractions behind correct absences.

One real title error predicts an extra leading article and duration before
\emph{Advanced Energy Transition Workshop}. Another returns only
\emph{AI for Education and Research} when the reviewed name includes the workshop format.
These strict boundary mismatches count as both FP and FN. Generic words such as \emph{Music}
and \emph{register} also create unsupported title candidates. These errors are retained with
per-record evidence in the repository.

\begin{figure}[!htbp]\centering
\includegraphics[width=\textwidth]{assets/real_confusion.png}
\caption{Frozen word/character classifier confusion matrix on 59 reviewed real excerpts.}
\end{figure}
"""
    p=r/"supplements/04_implementation.tex";s=p.read_text(encoding="utf-8");s=s[:s.index(r"\Needspace{.42\textheight}")]+text;p.write_text(s,encoding="utf-8")
    p=r/"chapters/04_implementation.tex";s=p.read_text(encoding="utf-8")
    s=s.replace("All numerical model results in this report currently use authored synthetic expectations.","Synthetic results and the separate human-reviewed real results use different data sources and class coverage.")
    s=s.replace("The collected public convenience sample is awaiting blind human annotation and may contain\nsource/template clustering and category gaps.","The real evaluation uses one reviewer, with no inter-annotator agreement estimate. It is a public-source convenience sample with source/template clustering, category gaps and sparse date/time fields; 25 accepted pilot excerpts predate the model freeze. General-text and topic/title boundaries can remain subjective.")
    s=s.replace("Actual executed checks are in VERIFICATION.md.","Executed software checks are available in the linked repository.")
    s=s.replace("Local warm HTTP benchmark:","The current software regression suite passes 71 Python tests and five JavaScript export tests; the Vite production build succeeds.\n\nLocal warm HTTP benchmark:")
    p.write_text(s,encoding="utf-8")
    p=r/"chapters/02_design.tex";s=p.read_text(encoding="utf-8").replace("human annotations are pending.","59 external records now have accepted human annotations, reported separately in Section 4.15.");p.write_text(s,encoding="utf-8")
    p=r/"chapters/05_conclusion.tex";s=p.read_text(encoding="utf-8")
    s=s.replace("The next empirical step is a separately reported,\nhuman-labelled natural-announcement evaluation using the frozen models.","The separate 59-record real evaluation finds only 0.4746 default-classifier accuracy and 0.5424 hybrid accuracy, with no hybrid extraction gain. This contrast identifies domain coverage and title-boundary supervision as higher priorities than adding complexity to improve an already easy synthetic benchmark.")
    p.write_text(s,encoding="utf-8")
    p=r/"supplements/05_conclusion.tex";s=p.read_text(encoding="utf-8").replace("Future experiments can use independently annotated departmental notices, club invitations and","Following this first single-reviewer real evaluation, future experiments can use independently annotated departmental notices, club invitations and");p.write_text(s,encoding="utf-8")
    for name in ["metrics.json","gold.json","review_decisions.json"]:
        shutil.copy2(directory/name,r/"evidence"/("real_"+name))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"Times New Roman","font.size":12})
    v=m["models"]["logistic_word_char"];fig,ax=plt.subplots(figsize=(13,12))
    ax.imshow(v["confusion_matrix"],cmap="Blues")
    ax.set_xticks(range(len(v["labels"])),v["labels"],rotation=65,ha="right")
    ax.set_yticks(range(len(v["labels"])),v["labels"])
    for i,row in enumerate(v["confusion_matrix"]):
        for j,n in enumerate(row):ax.text(j,i,n,ha="center",va="center")
    ax.set(xlabel="Predicted",ylabel="Reviewed label",title="Real reviewed text / frozen word-character LR / n=59")
    fig.tight_layout();fig.savefig(r/"assets/real_confusion.png",dpi=160);fig.savefig(directory/"confusion.png",dpi=160);plt.close(fig)
    # Public, readable summary of the separate evaluation.
    summary=["# Frozen model evaluation on reviewed real text\n","59 accepted;19 unresolved;4 excluded. One human reviewer, source spans validated. No fitting/tuning.","\n|Model|Accuracy|Macro F1 (12 supported labels)|Macro F1 (fixed 20)|\n|---|---:|---:|---:|"]
    for name,v in m["models"].items():summary.append(f"|{name}|{v['accuracy']:.4f}|{v['supported_class_macro']['macro_f1']:.4f}|{v['macro_f1']:.4f}|")
    summary+=["\n34 newly collected post-freeze accepted records are reported separately in metrics.json; the other25 are earlier pilot records.","\nRules and hybrid complete-record accuracy:0.3559. Field F1:name0.2353,date0.3529,time0.8000,venue0.3077. Present supports:29,8,3,12. Two negative examples:default/hybrid non-event recall0.","\nNo inter-annotator agreement or population-level generalization claim; source clusters and limited coverage constrain interpretation."]
    (directory/"RESULTS.md").write_text("\n".join(summary),encoding="utf-8")
    print("Updated personalized report with saved real metrics.")

if __name__=="__main__":main()
