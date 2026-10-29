export const fieldNames = ["event_name", "date", "time", "venue"];
export function exportRecord(result, edits, category) {
  return {
    announcement: result.input,
    reference_date: result.reference_date,
    category: category || null,
    automatic_category: result.category,
    model_status: result.model_status,
    training_metadata: result.training_metadata,
    field_status: Object.fromEntries(
      fieldNames.map((field) => {
        const raw = edits[field]?.trim() || null;
        const changed = raw !== (result.fields[field]?.raw || null);
        return [
          field,
          changed
            ? {
                state: raw ? "edited" : "missing",
                message: raw ? "User correction" : "Not provided",
              }
            : result.field_status?.[field],
        ];
      }),
    ),
    automatic_field_status: result.field_status,
    warnings: result.warnings,
    fields: Object.fromEntries(
      fieldNames.map((field) => {
        const original = result.fields[field];
        const raw = edits[field]?.trim() || null;
        const edited = raw !== (original?.raw || null);
        return [
          field,
          {
            raw,
            normalized: edited ? null : original?.normalized || null,
            edited,
            evidence: edited ? null : original || null,
            automatic_suggestion: original || null,
          },
        ];
      }),
    ),
    review_note:
      "UI edits are session corrections, not dataset annotations or verified human review.",
  };
}
function cell(value) {
  let text = value == null ? "" : String(value);
  if (/^[=+\-@\t\r]/.test(text)) text = "'" + text;
  return '"' + text.replaceAll('"', '""') + '"';
}
export function toCSV(record) {
  const values = {
    category: record.category,
    ...Object.fromEntries(
      fieldNames.map((name) => [name, record.fields[name].raw]),
    ),
    date_normalized: record.fields.date.normalized,
    announcement: record.announcement,
    reference_date: record.reference_date,
    model_status: record.model_status,
    training_metadata_json: JSON.stringify(record.training_metadata || {}),
    field_status_json: JSON.stringify(record.field_status || {}),
    evidence_json: JSON.stringify(
      Object.fromEntries(
        fieldNames.map((name) => [name, record.fields[name].evidence]),
      ),
    ),
    warnings_json: JSON.stringify(record.warnings),
    corrections_json: JSON.stringify(record.fields),
  };
  return (
    Object.keys(values).map(cell).join(",") +
    "\r\n" +
    Object.values(values).map(cell).join(",") +
    "\r\n"
  );
}
export function download(record, format) {
  const blob = new Blob(
    [
      format === "json"
        ? JSON.stringify(record, null, 2)
        : "\uFEFF" + toCSV(record),
    ],
    { type: format === "json" ? "application/json" : "text/csv;charset=utf-8" },
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `eventlens-result.${format}`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
