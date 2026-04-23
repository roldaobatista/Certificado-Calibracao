import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildManagementReviewCatalog,
  listManagementReviewScenarios,
  resolveManagementReviewScenario,
} from "./management-review-scenarios.js";

test("lists every canonical management review scenario", () => {
  const scenarios = listManagementReviewScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["ordinary-ready", "agenda-attention", "extraordinary-response"],
  );
});

test("returns the default management review scenario when the query is unknown", () => {
  const scenario = resolveManagementReviewScenario("unknown");

  assert.equal(scenario.id, "agenda-attention");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps the management review module in attention while the ordinary agenda still has pending decisions", () => {
  const scenario = resolveManagementReviewScenario("agenda-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.decisions.map((item) => item.label).join(" "), /NC-013|SLA/i);
});

test("blocks the management review module when an extraordinary meeting is required", () => {
  const scenario = resolveManagementReviewScenario("extraordinary-response");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /extraordinaria|liberacao|trilha/i);
  assert.equal(scenario.detail.signature.canSign, true);
  assert.equal(scenario.detail.signature.status, "pending");
});

test("allows switching the selected meeting inside the same scenario", () => {
  const scenario = resolveManagementReviewScenario(
    "ordinary-ready",
    "review-2026-q2",
  );

  assert.equal(scenario.selectedMeetingId, "review-2026-q2");
  assert.equal(scenario.detail.meetingId, "review-2026-q2");
});

test("builds the canonical management review catalog with selected scenario", () => {
  const catalog = buildManagementReviewCatalog(
    "extraordinary-response",
    "review-extra-2026-04",
  );

  assert.equal(catalog.selectedScenarioId, "extraordinary-response");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "extraordinary-response")
      ?.selectedMeetingId,
    "review-extra-2026-04",
  );
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "ordinary-ready")?.detail.signature.status,
    "signed",
  );
});
