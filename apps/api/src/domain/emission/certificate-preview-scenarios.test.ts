import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildCertificatePreviewCatalog,
  listCertificatePreviewScenarios,
  resolveCertificatePreviewScenario,
} from "./certificate-preview-scenarios.js";

test("lists every canonical certificate preview scenario", () => {
  const scenarios = listCertificatePreviewScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["type-b-ready", "type-a-suppressed", "type-c-blocked"],
  );
});

test("returns the default certificate preview scenario when the query is unknown", () => {
  const scenario = resolveCertificatePreviewScenario("unknown");

  assert.equal(scenario.id, "type-b-ready");
  assert.equal(scenario.result.status, "ready");
  assert.equal(scenario.result.suggestedReturnStep, undefined);
});

test("keeps the accredited preview ready while suppressing the symbol outside scope", () => {
  const scenario = resolveCertificatePreviewScenario("type-a-suppressed");

  assert.equal(scenario.result.status, "ready");
  assert.equal(scenario.result.symbolPolicy, "suppressed");
  assert.match(
    scenario.result.sections.find((section) => section.key === "header")?.fields[3]?.value ?? "",
    /suprimido/i,
  );
});

test("suggests the earliest wizard step to revisit when the preview is blocked", () => {
  const scenario = resolveCertificatePreviewScenario("type-c-blocked");

  assert.equal(scenario.result.status, "blocked");
  assert.equal(scenario.result.suggestedReturnStep, 2);
  assert.match(scenario.result.blockers.join(" "), /QR publico/i);
});

test("builds the canonical certificate preview catalog with selected scenario", () => {
  const catalog = buildCertificatePreviewCatalog("type-c-blocked");

  assert.equal(catalog.selectedScenarioId, "type-c-blocked");
  assert.equal(catalog.scenarios.length, 3);
});
