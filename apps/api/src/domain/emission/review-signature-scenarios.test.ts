import assert from "node:assert/strict";
import { test } from "node:test";

import { buildReviewSignatureCatalog, listReviewSignatureScenarios, resolveReviewSignatureScenario } from "./review-signature-scenarios.js";

test("lists every canonical review/signature workflow scenario", () => {
  const scenarios = listReviewSignatureScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["segregated-ready", "reviewer-conflict", "signatory-mfa-blocked"],
  );
});

test("returns the default review/signature scenario when the query is unknown", () => {
  const scenario = resolveReviewSignatureScenario("unknown");

  assert.equal(scenario.id, "segregated-ready");
  assert.equal(scenario.result.status, "ready");
});

test("returns a blocked workflow scenario with reassignment suggestions", () => {
  const scenario = resolveReviewSignatureScenario("reviewer-conflict");

  assert.equal(scenario.result.status, "blocked");
  assert.equal(scenario.result.reviewStep.status, "blocked");
  assert.equal(scenario.result.suggestions.reviewer?.displayName, "Renata Qualidade");
});

test("builds the canonical workflow catalog with selected scenario", () => {
  const catalog = buildReviewSignatureCatalog("signatory-mfa-blocked");

  assert.equal(catalog.selectedScenarioId, "signatory-mfa-blocked");
  assert.equal(catalog.scenarios.length, 3);
});
