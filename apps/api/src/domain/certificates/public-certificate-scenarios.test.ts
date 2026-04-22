import assert from "node:assert/strict";
import { test } from "node:test";

import {
  listPublicCertificateScenarios,
  resolvePublicCertificateScenario,
} from "./public-certificate-scenarios.js";

test("returns the default public certificate scenario when the query is unknown", () => {
  const scenario = resolvePublicCertificateScenario("desconhecido");

  assert.equal(scenario.id, "authentic");
  assert.equal(scenario.result.status, "authentic");
  assert.equal(scenario.result.ok, true);
});

test("returns a sanitized authentic certificate without private metadata", () => {
  const scenario = resolvePublicCertificateScenario("authentic");

  assert.equal(scenario.result.ok, true);
  if (!scenario.result.ok) {
    assert.fail("expected authenticated result");
  }

  assert.equal(scenario.result.certificate.certificateNumber, "AFR-000123");
  assert.equal("customerName" in scenario.result.certificate, false);
  assert.equal("customerAddress" in scenario.result.certificate, false);
});

test("keeps the not-found scenario fail-closed", () => {
  const scenario = listPublicCertificateScenarios().find((item) => item.id === "not-found");

  assert.ok(scenario);
  assert.equal(scenario.result.status, "not_found");
  assert.equal(scenario.result.ok, false);
});
