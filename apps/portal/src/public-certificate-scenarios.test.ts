import assert from "node:assert/strict";
import { test } from "node:test";

import {
  listPublicCertificateScenarios,
  resolvePublicCertificateScenario,
} from "./public-certificate-scenarios.js";

test("falls back to the authentic public certificate scenario when the query is unknown", () => {
  const scenario = resolvePublicCertificateScenario("desconhecido");

  assert.equal(scenario.id, "authentic");
  assert.equal(scenario.page.status, "authentic");
  assert.equal(scenario.page.publicMetadata.certificateNumber, "AFR-000123");
});

test("keeps the not-found scenario empty and fail-closed", () => {
  const scenario = listPublicCertificateScenarios().find((item) => item.id === "not-found");

  assert.ok(scenario);
  assert.equal(scenario.page.status, "not_found");
  assert.deepEqual(scenario.page.publicMetadata, {});
});
