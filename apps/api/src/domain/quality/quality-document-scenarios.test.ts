import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildQualityDocumentCatalog,
  listQualityDocumentScenarios,
  resolveQualityDocumentScenario,
} from "./quality-document-scenarios.js";

test("lists every canonical quality document scenario", () => {
  const scenarios = listQualityDocumentScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-ready", "revision-attention", "obsolete-blocked"],
  );
});

test("returns the default quality document scenario when the query is unknown", () => {
  const scenario = resolveQualityDocumentScenario("unknown");

  assert.equal(scenario.id, "revision-attention");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps documents in attention while a preventive revision remains open", () => {
  const scenario = resolveQualityDocumentScenario("revision-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.warnings.join(" "), /revisao preventiva/i);
});

test("blocks the document registry when an obsolete revision is selected", () => {
  const scenario = resolveQualityDocumentScenario("obsolete-blocked");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /obsoleta|operacional/i);
});

test("allows switching the selected document inside the same scenario", () => {
  const scenario = resolveQualityDocumentScenario(
    "operational-ready",
    "document-pt005-r04",
  );

  assert.equal(scenario.selectedDocumentId, "document-pt005-r04");
  assert.equal(scenario.detail.documentId, "document-pt005-r04");
});

test("builds the canonical quality document catalog with selected scenario", () => {
  const catalog = buildQualityDocumentCatalog(
    "obsolete-blocked",
    "document-pg005-r01",
  );

  assert.equal(catalog.selectedScenarioId, "obsolete-blocked");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "obsolete-blocked")
      ?.selectedDocumentId,
    "document-pg005-r01",
  );
});
