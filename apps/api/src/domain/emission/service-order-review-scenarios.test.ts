import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildServiceOrderReviewCatalog,
  listServiceOrderReviewScenarios,
  resolveServiceOrderReviewScenario,
} from "./service-order-review-scenarios.js";

test("lists every canonical service-order review scenario", () => {
  const scenarios = listServiceOrderReviewScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["review-ready", "history-pending", "review-blocked"],
  );
});

test("returns the default service-order review scenario when the query is unknown", () => {
  const scenario = resolveServiceOrderReviewScenario("unknown");

  assert.equal(scenario.id, "review-ready");
  assert.equal(scenario.detail.status, "ready");
  assert.ok(scenario.detail.allowedActions.includes("approve_review"));
});

test("keeps the service-order review in attention when the checklist still has a pending historical check", () => {
  const scenario = resolveServiceOrderReviewScenario("history-pending");

  assert.equal(scenario.detail.status, "attention");
  assert.equal(scenario.detail.checklist.filter((item) => item.status === "pending").length, 1);
  assert.equal(scenario.detail.allowedActions.includes("approve_review"), false);
});

test("blocks the service-order review when reviewer segregation and preview gates fail", () => {
  const scenario = resolveServiceOrderReviewScenario("review-blocked");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /Revisor atual coincide com o executor/i);
  assert.equal(scenario.detail.allowedActions.includes("approve_review"), false);
});

test("allows switching the selected work order inside the same scenario", () => {
  const scenario = resolveServiceOrderReviewScenario("review-ready", "os-2026-00139");

  assert.equal(scenario.selectedItemId, "os-2026-00139");
  assert.equal(scenario.detail.itemId, "os-2026-00139");
  assert.match(scenario.detail.title, /OS-2026-00139/);
});

test("builds the canonical service-order review catalog with selected scenario", () => {
  const catalog = buildServiceOrderReviewCatalog("review-blocked");

  assert.equal(catalog.selectedScenarioId, "review-blocked");
  assert.equal(catalog.scenarios.length, 3);
});
