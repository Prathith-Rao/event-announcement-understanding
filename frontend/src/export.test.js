import test from "node:test";
import assert from "node:assert/strict";
import { exportRecord, toCSV } from "./export.js";

test("edited field status does not retain a stale missing notice", () => {
  const source = {
    input: "An event",
    reference_date: null,
    category: {},
    warnings: [],
    fields: { event_name: null, date: null, time: null, venue: null },
    field_status: { venue: { state: "missing", message: "Not mentioned" } },
    training_metadata: { run: "expanded_v2", provenance: "synthetic" },
  };
  const record = exportRecord(source, { venue: "New Hall" }, "Meeting");
  assert.equal(record.field_status.venue.state, "edited");
  assert.equal(record.automatic_field_status.venue.state, "missing");
  assert.equal(record.training_metadata.provenance, "synthetic");
});

test("CSV retains model provenance without a main-flow warning", () => {
  const source = {
    input: "An event",
    reference_date: null,
    category: {},
    warnings: [],
    fields: { event_name: null, date: null, time: null, venue: null },
    training_metadata: { run: "expanded_v2", provenance: "synthetic" },
  };
  const record = exportRecord(source, {}, "Other event");
  assert.ok(toCSV(record).includes("training_metadata_json"));
  assert.ok(toCSV(record).includes("synthetic"));
});
const result = {
  input: "Seminar at West Hall",
  reference_date: null,
  category: { label: "Seminar" },
  warnings: [],
  fields: {
    event_name: null,
    date: { raw: "tomorrow", normalized: "2027-01-02", start: 0, end: 8 },
    time: null,
    venue: { raw: "West Hall", start: 11, end: 20 },
  },
};
test("edits export current values and invalidate stale evidence and date normalization", () => {
  const record = exportRecord(
    result,
    {
      event_name: "New title",
      date: "next week",
      time: "",
      venue: "East Hall",
    },
    "Meeting",
  );
  assert.equal(record.category, "Meeting");
  assert.equal(record.fields.venue.raw, "East Hall");
  assert.equal(record.fields.venue.evidence, null);
  assert.equal(record.fields.venue.automatic_suggestion.raw, "West Hall");
  assert.equal(record.fields.date.normalized, null);
  assert.equal(record.fields.time.raw, null);
});
test("unchanged values retain exact evidence", () => {
  const record = exportRecord(
    result,
    { date: "tomorrow", venue: "West Hall" },
    "Seminar",
  );
  assert.equal(record.fields.date.normalized, "2027-01-02");
  assert.equal(record.fields.venue.evidence.start, 11);
});
test("CSV escapes quotes/newlines and neutralizes spreadsheet formulas", () => {
  const record = exportRecord(
    result,
    { event_name: '=HYPERLINK("bad")', venue: "Hall, A\nFloor 2" },
    "Seminar",
  );
  const csv = toCSV(record);
  assert.ok(csv.includes("'=HYPERLINK"));
  assert.ok(csv.includes('""bad""'));
  assert.ok(csv.includes("Hall, A\nFloor 2"));
});
