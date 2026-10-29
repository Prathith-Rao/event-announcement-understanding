import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { download, exportRecord, fieldNames } from "./export.js";
import "./styles.css";

const initialCategories = [
  "Workshop",
  "Seminar",
  "Competition",
  "Meeting",
  "Cultural event",
];
const samples = [
  {
    name: "Workshop",
    text: 'Join our workshop "Practical Python" on 18 March 2027 at 10:00 AM in Room B12. Bring a laptop for guided coding exercises.',
  },
  {
    name: "Deadline & event",
    text: 'Registration closes on 4 May 2027; the workshop "Data Skills" will be held on 9 May 2027 at 10:00 AM in Room B12.',
  },
  {
    name: "Missing details",
    text: 'Attend the competition "Code Race" on 14 July 2027. Teams will compete for prizes awarded by a panel of judges.',
  },
  {
    name: "Sports",
    text: "The Champions Cup football match takes place on 22 November 2027 at 6pm in Riverside Stadium. Players should arrive early for warm-up.",
  },
  {
    name: "Career fair",
    text: "Career Connect is a recruitment drive on 24 November 2027 at 10:30 AM in the Central Convention Center. Bring your resume and meet hiring managers.",
  },
  {
    name: "Everyday plans",
    text: "Let’s meet for a picnic tomorrow at noon in Rose Garden.",
  },
];
function Icon({ name, size = 20 }) {
  const paths = {
    lens: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 5 5M10 6v8M6 10h8" />
      </>
    ),
    analyze: (
      <>
        <path d="M5 3h10l4 4v14H5zM14 3v5h5M8 12h8M8 16h5" />
      </>
    ),
    chart: (
      <>
        <path d="M4 3v17h17M8 16v-5M13 16V7M18 16V4" />
      </>
    ),
    book: (
      <>
        <path d="M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1v15" />
      </>
    ),
    arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
    download: (
      <>
        <path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    spark: (
      <>
        <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z" />
      </>
    ),
    info: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v6M12 7v1" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.info}
    </svg>
  );
}
function Source({ result }) {
  const spans = fieldNames
    .map((field) => result.fields[field] && { ...result.fields[field], field })
    .filter(Boolean)
    .sort((a, b) => a.start - b.start);
  let end = 0;
  const parts = [];
  for (const span of spans) {
    if (span.start < end) continue;
    parts.push(result.input.slice(end, span.start));
    parts.push(
      <mark
        key={span.field}
        title={`${span.field}: characters ${span.start}–${span.end}`}
        className={`evidence-${span.field}`}
      >
        {result.input.slice(span.start, span.end)}
      </mark>,
    );
    end = span.end;
  }
  parts.push(result.input.slice(end));
  return <div className="source-text">{parts}</div>;
}
function Analysis({ result }) {
  const [tab, setTab] = useState("tokens");
  const language = result.analysis;
  if (!language)
    return (
      <p className="muted">
        Enable linguistic analysis and analyze again to inspect tokens, POS tags
        and phrase chunks.
      </p>
    );
  return (
    <>
      <div className="subtabs">
        {["tokens", "chunks", "candidates"].map((name) => (
          <button
            className={tab === name ? "selected" : ""}
            key={name}
            onClick={() => setTab(name)}
          >
            {name === "tokens"
              ? "Tokens & POS"
              : name === "chunks"
                ? "Phrase chunks"
                : "All field candidates"}
          </button>
        ))}
      </div>
      {tab === "tokens" && (
        <div className="token-list">
          {language.tokens.map((token, i) => (
            <span
              className="token"
              key={i}
              title={`Characters ${token.start}–${token.end}`}
            >
              <b>{token.text}</b>
              <small>{token.pos}</small>
            </span>
          ))}
        </div>
      )}
      {tab === "chunks" && (
        <>
          <div className="chunk-list">
            {language.chunks.map((chunk, i) => (
              <div key={i}>
                <span className="pill">{chunk.label}</span>
                <span>{chunk.raw}</span>
                <code>{chunk.pattern}</code>
              </div>
            ))}
          </div>
          <details>
            <summary>Explicit NLTK grammars</summary>
            <pre>{JSON.stringify(language.grammars, null, 2)}</pre>
          </details>
        </>
      )}
      {tab === "candidates" && (
        <div className="chunk-list">
          {Object.entries(result.candidates).flatMap(([field, values]) =>
            values.map((value, i) => (
              <div key={field + i}>
                <span className="pill">{field}</span>
                <span>{value.raw}</span>
                <small>
                  {value.role} · {value.method} · [{value.start}, {value.end})
                </small>
              </div>
            )),
          )}
        </div>
      )}
    </>
  );
}
function Results({
  result,
  edits,
  setEdits,
  category,
  setCategory,
  categories,
}) {
  const [detail, setDetail] = useState("evidence");
  const fieldLabels = {
    event_name: "Event name",
    date: "Event date",
    time: "Event time",
    venue: "Venue",
  };
  if (!result)
    return (
      <section className="card result-card empty-result">
        <div className="card-title">
          <span className="step">02</span>
          <h2>Structured understanding</h2>
          <span className="muted tiny">Awaiting input</span>
        </div>
        <div className="empty-center">
          <div className="empty-graphic">
            <Icon name="analyze" size={38} />
            <span>
              <Icon name="check" size={16} />
            </span>
          </div>
          <h3>
            A little structure.
            <br />A lot more clarity.
          </h3>
          <p>
            Your event details will appear here,
            <br />
            with the source text to back them up.
          </p>
          <div className="empty-fields">
            <span>Event name</span>
            <span>Date & time</span>
            <span>Venue</span>
          </div>
        </div>
        <div className="card-note">
          <Icon name="info" size={16} /> Missing details stay missing. Evidence
          stays visible.
        </div>
      </section>
    );
  const essentialWarnings = result.warnings.filter(
    (warning) => !warning.field && warning.severity !== "info",
  );
  const changed =
    fieldNames.some(
      (field) => (edits[field] || "") !== (result.fields[field]?.raw || ""),
    ) || category !== (result.category.label || "");
  return (
    <section className="card result-card">
      <div className="card-title">
        <span className="step">02</span>
        <h2>Structured understanding</h2>
        <span className={`status ${result.status === "ok" ? "good" : ""}`}>
          {result.status === "ok"
            ? "Extracted"
            : result.status === "unsupported"
              ? "No single event"
              : "Check details"}
        </span>
      </div>
      <div className="result-body">
        <label className="field-label" htmlFor="category">
          EVENT CATEGORY
        </label>
        <div className="category-row">
          <select
            id="category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">Needs review / unsupported</option>
            {categories.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
          <span className="tiny muted">Editable result</span>
        </div>
        {result.field_status?.category?.message && (
          <small className="field-note notice">
            {result.field_status.category.message}
          </small>
        )}
        {result.category.suggested_label && !result.category.label && (
          <p className="tiny muted">
            Model suggestion: {result.category.suggested_label}. Review category
            overlap before accepting.
          </p>
        )}
        <div className="result-fields">
          {fieldNames.map((field) => (
            <div
              className={
                field === "event_name" || field === "venue" ? "wide" : ""
              }
              key={field}
            >
              <label className="field-label" htmlFor={field}>
                {fieldLabels[field].toUpperCase()}
              </label>
              <input
                id={field}
                aria-describedby={`${field}-note`}
                value={edits[field] || ""}
                placeholder="Not provided"
                onChange={(event) =>
                  setEdits({ ...edits, [field]: event.target.value })
                }
              />
              <small
                id={`${field}-note`}
                className={`field-note ${result.field_status?.[field]?.state || ""}`}
              >
                {(edits[field] || "") !== (result.fields[field]?.raw || "")
                  ? "Edited"
                  : result.field_status?.[field]?.message}
              </small>
              {result.fields[field]?.normalized &&
                edits[field] === result.fields[field].raw && (
                  <small className="normalized">
                    Normalized: {result.fields[field].normalized}
                  </small>
                )}
            </div>
          ))}
        </div>
        {!!essentialWarnings.length && (
          <div className="warning-box">
            <div>
              <Icon name="info" size={17} />
              <b>Please check</b>
            </div>
            <ul>
              {essentialWarnings.map((warning, i) => (
                <li key={i}>{warning.message}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="subtabs result-tabs">
          {["evidence", "analysis", "scores"].map((value) => (
            <button
              key={value}
              className={detail === value ? "selected" : ""}
              onClick={() => setDetail(value)}
            >
              {value === "evidence"
                ? "Source evidence"
                : value === "analysis"
                  ? "NLP analysis"
                  : "Model scores"}
            </button>
          ))}
        </div>
        {detail === "evidence" && (
          <>
            <p className="tiny muted">
              Automatic field evidence in the original input. Edits do not
              create new source evidence.
            </p>
            <Source result={result} />
            <div className="legend">
              {fieldNames.map((field) => (
                <span key={field}>
                  <i className={`evidence-${field}`} />
                  {fieldLabels[field]}
                </span>
              ))}
            </div>
          </>
        )}
        {detail === "analysis" && <Analysis result={result} />}
        {detail === "scores" && (
          <div className="scores">
            <p className="tiny muted">
              {result.category.score_explanation}.{" "}
              {result.category.score_limitation ||
                "Counts are not confidence probabilities."}
            </p>
            {Object.entries(
              result.category.model_scores || result.category.scores,
            ).map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <progress
                  value={value}
                  max={
                    result.category.model_scores
                      ? 1
                      : Math.max(1, ...Object.values(result.category.scores))
                  }
                />
                <code>{value.toFixed(3)}</code>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="export-bar">
        <span className="tiny muted">
          {changed ? "Includes your edits" : "Export this result"}
        </span>
        <div>
          {["json", "csv"].map((format) => (
            <button
              key={format}
              className="button small"
              onClick={() =>
                download(exportRecord(result, edits, category), format)
              }
            >
              <Icon name="download" size={15} />
              {format.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
function Evaluation() {
  const [state, setState] = useState({});
  React.useEffect(() => {
    let active = true;
    fetch("/api/evaluation")
      .then(async (response) => {
        if (!response.ok) throw Error("Saved results could not be loaded.");
        return response.json();
      })
      .then((data) => active && setState({ data }))
      .catch((error) => active && setState({ error: error.message }));
    return () => {
      active = false;
    };
  }, []);
  if (state.error)
    return (
      <div className="warning-box" role="alert">
        {state.error}
      </div>
    );
  if (!state.data) return <p>Loading saved experiments…</p>;
  const { collection, runs } = state.data;
  const extractions = [
    ["v2 validation", state.data.expanded_extraction],
    ["v2 test", state.data.expanded_final_extraction],
    ["v1 development", state.data.extraction_development],
    ["v1 final", state.data.extraction_final],
  ].filter(([, result]) => result);
  return (
    <div className="evaluation">
      <div className="section-intro">
        <span className="eyebrow">MEASURED, NOT ASSUMED</span>
        <h1>The evidence behind the system.</h1>
        <p>
          Saved experiment artifacts. Synthetic results and unreviewed labels
          are explicitly identified.
        </p>
      </div>
      <div className="metric-grid">
        <div className="card metric">
          <small>Expanded training dataset</small>
          <strong>
            {state.data.expanded_dataset?.records?.toLocaleString() ?? 0}
          </strong>
        </div>
        <div className="card metric">
          <small>Supported event categories</small>
          <strong>19</strong>
        </div>
        <div className="card metric">
          <small>Dataset provenance</small>
          <strong className="text-metric">Synthetic + real pilot</strong>
        </div>
      </div>
      {Object.entries(runs).map(([name, run]) => (
        <section className="card table-card" key={name}>
          <div className="card-title">
            <h2>
              {name === "expanded_v2"
                ? "Expanded model · version 2"
                : name + " · archived baseline"}{" "}
              classification
            </h2>
            <span className="pill">{run.manifest.label_status}</span>
          </div>
          <p className="muted">
            Train {run.manifest.split_sizes.train} · validation{" "}
            {run.manifest.split_sizes.validation} · test{" "}
            {run.manifest.split_sizes.test} · {run.manifest.audit.groups} groups
            · group overlap {run.manifest.audit.group_overlap}
          </p>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Partition</th>
                  <th>Accuracy</th>
                  <th>Macro precision</th>
                  <th>Macro recall</th>
                  <th>Macro F1</th>
                  <th>n</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["validation", run.validation],
                  ["final test", run.test?.models],
                ].flatMap(([partition, metrics]) =>
                  Object.entries(metrics || {}).map(([model, metric]) => (
                    <tr key={partition + model}>
                      <td>{model.replaceAll("_", " ")}</td>
                      <td>{partition}</td>
                      {[
                        "accuracy",
                        "macro_precision",
                        "macro_recall",
                        "macro_f1",
                      ].map((key) => (
                        <td key={key}>{metric[key].toFixed(3)}</td>
                      ))}
                      <td>{metric.sample_count}</td>
                    </tr>
                  )),
                )}
              </tbody>
            </table>
          </div>
          <p className="tiny muted">{run.manifest.feature_notes}</p>
          <details>
            <summary>
              Per-class metrics, confusion matrices and run manifest
            </summary>
            <pre>{JSON.stringify(run, null, 2)}</pre>
          </details>
        </section>
      ))}
      {extractions.map(([partition, extraction]) => (
        <section key={partition} className="card table-card">
          <div className="card-title">
            <h2>Controlled extraction comparison</h2>
            <span className="pill">
              Synthetic {partition} · {extraction.hybrid.sample_count} cases
            </span>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Field</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>Exact match</th>
                </tr>
              </thead>
              <tbody>
                {["rules", "hybrid"].flatMap((method) =>
                  Object.entries(extraction[method].fields).map(
                    ([field, metric]) => (
                      <tr key={method + field}>
                        <td>{method}</td>
                        <td>{field.replaceAll("_", " ")}</td>
                        {["precision", "recall", "f1", "exact_match"].map(
                          (key) => (
                            <td key={key}>{metric[key].toFixed(3)}</td>
                          ),
                        )}
                      </tr>
                    ),
                  ),
                )}
              </tbody>
            </table>
          </div>
          <p className="muted">
            Complete-record accuracy: rules{" "}
            {extraction.rules.complete_record_accuracy.toFixed(3)} · hybrid{" "}
            {extraction.hybrid.complete_record_accuracy.toFixed(3)}. Synthetic
            benchmark results measure this dataset; they do not establish
            real-data accuracy.
          </p>
          <details>
            <summary>Actual extraction errors and handling metrics</summary>
            <pre>{JSON.stringify(extraction, null, 2)}</pre>
          </details>
        </section>
      ))}
      <section className="card table-card">
        <h2>Source distribution</h2>
        <div className="source-list">
          {Object.entries(collection?.institutions || {}).map(
            ([name, count]) => (
              <div key={name}>
                <span>{name}</span>
                <b>{count}</b>
              </div>
            ),
          )}
        </div>
        <p className="muted">
          All automatic labels require review. Annotation happens in the
          separate CSV workflow described in the project README.
        </p>
      </section>
    </div>
  );
}
function Methodology() {
  const [data, setData] = useState(null),
    [error, setError] = useState("");
  React.useEffect(() => {
    fetch("/api/methodology")
      .then((response) => {
        if (!response.ok) throw Error("Methodology unavailable.");
        return response.json();
      })
      .then(setData)
      .catch((error) => setError(error.message));
  }, []);
  return (
    <>
      <div className="section-intro">
        <span className="eyebrow">TRANSPARENT BY DESIGN</span>
        <h1>Language tools, working together.</h1>
        <p>
          Rules locate explicit details. Linguistic structure expands phrase
          candidates. Supervised models learn category patterns.
        </p>
      </div>
      <div className="method-grid">
        {[
          [
            "01",
            "Preserve the announcement",
            "Extraction retains case, numbers, punctuation, and prepositions. Every candidate points to exact original character offsets.",
          ],
          [
            "02",
            "Read its structure",
            "NLTK Punkt segments sentences, Treebank tokenizes words, and a trained tagger assigns Penn POS tags. Explicit RegexpParser grammars propose title and venue phrases; a trained CRF also learns their token boundaries.",
          ],
          [
            "03",
            "Select with context",
            "Context rules exclude deadlines and organizer addresses. Ambiguity and missing information produce review warnings. Relative dates require a reference date.",
          ],
          [
            "04",
            "Compare, then evaluate",
            "Train-only features, grouped splits, majority and keyword baselines, NLTK Naive Bayes, raw/preprocessed TF-IDF logistic regression, character n-grams and a trained CRF make choices inspectable.",
          ],
        ].map(([number, title, body]) => (
          <section className="card method-card" key={number}>
            <span className="step">{number}</span>
            <h2>{title}</h2>
            <p>{body}</p>
          </section>
        ))}
      </div>
      <div className="warning-box">
        The expanded model uses an authored synthetic corpus with held-out
        construction families and entity pools. Real pilot data remains
        separate. Evaluation reports the exact dataset and label source; model
        scores are uncalibrated.
      </div>
      {error && <p role="alert">{error}</p>}
      {data && (
        <section className="card table-card">
          <details>
            <summary>Full implementation specification</summary>
            <pre className="document-text">{data.specification}</pre>
          </details>
          <details>
            <summary>Exact evaluation definitions</summary>
            <pre className="document-text">{data.metrics}</pre>
          </details>
        </section>
      )}
    </>
  );
}
function App() {
  const [categories, setCategories] = useState(initialCategories);
  React.useEffect(() => {
    fetch("/api/config")
      .then((response) => response.json())
      .then((config) => setCategories(config.categories))
      .catch(() => {});
  }, []);
  const [page, setPage] = useState("analyze"),
    [text, setText] = useState(""),
    [reference, setReference] = useState(""),
    [include, setInclude] = useState(true),
    [classifier, setClassifier] = useState("auto"),
    [mode, setMode] = useState("hybrid");
  const [result, setResult] = useState(null),
    [edits, setEdits] = useState({}),
    [category, setCategory] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    if (!text.trim()) {
      setError("Enter an English event announcement to begin.");
      return;
    }
    setBusy(true);
    setError("");
    setResult(null);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        signal: controller.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          reference_date: reference || null,
          include_analysis: include,
          classifier,
          extraction_mode: mode,
        }),
      });
      const data = await response.json();
      if (!response.ok)
        throw Error(
          typeof data.detail === "string"
            ? data.detail
            : "Check your input and reference date, then try again.",
        );
      setResult(data);
      if (data.categories) setCategories(data.categories);
      setEdits(
        Object.fromEntries(
          fieldNames.map((field) => [field, data.fields[field]?.raw || ""]),
        ),
      );
      setCategory(data.category.label || "");
    } catch (error) {
      setError(
        error.name === "AbortError"
          ? "Analysis timed out. Try a shorter announcement and check that the backend is running."
          : error.message === "Failed to fetch"
            ? "The backend is unavailable. Start FastAPI on port 8000 and try again."
            : error.message,
      );
    } finally {
      clearTimeout(timeout);
      setBusy(false);
    }
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            setPage("analyze");
          }}
        >
          <span className="brand-icon">
            <Icon name="lens" size={24} />
          </span>
          eventlens<span className="brand-dot">.</span>
        </a>
        <div className="sidebar-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {[
            ["analyze", "analyze", "Analyze announcement"],
            ["evaluation", "chart", "Evaluation results"],
            ["methodology", "book", "Methodology"],
          ].map(([key, icon, label]) => (
            <button
              className={page === key ? "active" : ""}
              key={key}
              onClick={() => setPage(key)}
              aria-current={page === key ? "page" : undefined}
            >
              <Icon name={icon} />
              <span>{label}</span>
              {page === key && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-indicator">
            <span /> LOCAL NLP WORKSPACE
          </div>
          <p>
            Built to understand.
            <br />
            Designed to explain.
          </p>
          <div className="tech-tags">
            <span>NLTK</span>
            <span>scikit-learn</span>
          </div>
          <div className="project-caption">
            NATURAL LANGUAGE PROCESSING
            <br />
            COURSE AAT PROJECT
          </div>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            Event Announcement Understanding{" "}
            <span className="breadcrumb">
              /{" "}
              {page === "analyze"
                ? "Analyze"
                : page === "evaluation"
                  ? "Evaluation"
                  : "Methodology"}
            </span>
          </span>
          <span className="hybrid-badge">
            <span /> HYBRID NLP
          </span>
        </header>
        <div className="workspace">
          {page === "analyze" ? (
            <>
              <div className="section-intro">
                <span className="eyebrow">
                  LESS MANUAL READING. MORE UNDERSTANDING.
                </span>
                <h1>
                  From announcement
                  <br />
                  to <em>understanding.</em>
                </h1>
                <p>
                  Find the what, when, and where.
                  <br className="mobile-break" /> Keep the evidence along the
                  way.
                </p>
              </div>
              <div className="analysis-grid">
                <form className="card input-card" onSubmit={submit}>
                  <div className="card-title">
                    <span className="step">01</span>
                    <h2>Your announcement</h2>
                    <span className="muted tiny">English</span>
                  </div>
                  <div className="input-body">
                    <label className="sr-only" htmlFor="announcement">
                      Announcement text
                    </label>
                    <textarea
                      id="announcement"
                      value={text}
                      maxLength={20000}
                      disabled={busy}
                      onChange={(event) => {
                        setText(event.target.value);
                        setResult(null);
                      }}
                      placeholder={
                        "Paste an event announcement here…\n\nFor example, a workshop invitation, a seminar notice, or your next campus event."
                      }
                    />
                    <div className="input-caption">
                      <span>Original text is preserved for evidence.</span>
                      <span>{text.length.toLocaleString()} / 20,000</span>
                    </div>
                    <div className="sample-section">
                      <span className="field-label">TRY AN EXAMPLE</span>
                      <div className="sample-buttons">
                        {samples.map((sample) => (
                          <button
                            type="button"
                            key={sample.name}
                            disabled={busy}
                            onClick={() => {
                              setText(sample.text);
                              setResult(null);
                              setError("");
                            }}
                          >
                            {sample.name}
                            <span>↗</span>
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="reference">
                      <label htmlFor="reference">
                        Reference date <span>Optional</span>
                      </label>
                      <button
                        type="button"
                        className="today-button"
                        disabled={busy}
                        onClick={() => {
                          const now = new Date();
                          setReference(
                            [
                              now.getFullYear(),
                              String(now.getMonth() + 1).padStart(2, "0"),
                              String(now.getDate()).padStart(2, "0"),
                            ].join("-"),
                          );
                          setResult(null);
                        }}
                      >
                        Use today
                      </button>
                      <input
                        id="reference"
                        type="date"
                        value={reference}
                        disabled={busy}
                        onChange={(event) => {
                          setReference(event.target.value);
                          setResult(null);
                        }}
                      />
                      <small>
                        Required to resolve “tomorrow” or “next Monday”.
                      </small>
                    </div>
                    <details className="settings">
                      <summary>Analysis options</summary>
                      <div className="setting-row">
                        <label htmlFor="classifier">Category model</label>
                        <select
                          id="classifier"
                          value={classifier}
                          onChange={(event) =>
                            setClassifier(event.target.value)
                          }
                        >
                          <option value="auto">Recommended model</option>
                          <option value="logistic_word_char">
                            Word + character classifier
                          </option>
                          <option value="logistic_raw">
                            TF-IDF + logistic regression (raw)
                          </option>
                          <option value="logistic_preprocessed">
                            TF-IDF + logistic regression (NLTK)
                          </option>
                          <option value="nltk_nb">NLTK Naive Bayes</option>
                          <option value="keywords">Keyword baseline</option>
                        </select>
                      </div>
                      <div className="setting-row">
                        <label htmlFor="extraction">Extraction</label>
                        <select
                          id="extraction"
                          value={mode}
                          onChange={(event) => setMode(event.target.value)}
                        >
                          <option value="hybrid">
                            Hybrid: rules + NLTK + trained extractor
                          </option>
                          <option value="rules">Rules only</option>
                        </select>
                      </div>
                    </details>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={include}
                        onChange={(event) => setInclude(event.target.checked)}
                      />
                      <span>Include tokens, POS tags & phrase chunks</span>
                    </label>
                    {error && (
                      <div role="alert" className="error-box">
                        {error}
                      </div>
                    )}
                    <button
                      className="analyze-button"
                      disabled={busy || !text.trim()}
                      type="submit"
                    >
                      <Icon name="spark" size={18} />
                      {busy
                        ? "Reading the announcement…"
                        : "Analyze announcement"}
                      {!busy && <Icon name="arrow" size={19} />}
                    </button>
                    <p className="privacy-note">
                      Runs locally · No external model inference · No text
                      stored
                    </p>
                  </div>
                </form>
                <Results
                  result={result}
                  edits={edits}
                  setEdits={setEdits}
                  category={category}
                  setCategory={setCategory}
                  categories={categories}
                />
              </div>
              <div className="pipeline-strip">
                {[
                  ["01", "Linguistic analysis", "Tokenize · POS tag · Chunk"],
                  [
                    "02",
                    "Hybrid understanding",
                    "Classify · Extract · Validate",
                  ],
                  ["03", "Transparent results", "Evidence · Warnings · Export"],
                ].map(([number, title, detail]) => (
                  <div key={number}>
                    <span>{number}</span>
                    <div>
                      <b>{title}</b>
                      <small>{detail}</small>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : page === "evaluation" ? (
            <Evaluation />
          ) : (
            <Methodology />
          )}
          <footer>
            <span>
              EventLens / Event Announcement Understanding Using a Hybrid NLP
              Approach
            </span>
            <span>English · One announcement at a time</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")).render(<App />);
