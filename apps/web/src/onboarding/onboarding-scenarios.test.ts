import assert from "node:assert/strict";
import { test } from "node:test";

import { listOnboardingScenarios, resolveOnboardingScenario } from "./onboarding-scenarios.js";

test("falls back to the ready onboarding scenario when the query is unknown", () => {
  const scenario = resolveOnboardingScenario("desconhecido");

  assert.equal(scenario.id, "ready");
  assert.equal(scenario.summary.status, "ready");
  assert.deepEqual(scenario.summary.blockingSteps, []);
});

test("exposes the expected blocking steps in the blocked onboarding scenario", () => {
  const scenario = listOnboardingScenarios().find((item) => item.id === "blocked");

  assert.ok(scenario);
  assert.equal(scenario.summary.status, "blocked");
  assert.deepEqual(scenario.summary.blockingSteps, [
    "Numeracao de certificado",
    "Escopo e CMC",
    "QR publico",
  ]);
});
