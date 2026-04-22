import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildPortalCertificateCatalog,
  listPortalCertificateScenarios,
  resolvePortalCertificateScenario,
} from "./portal-certificate-scenarios.js";

test("lists every canonical portal certificate scenario", () => {
  const scenarios = listPortalCertificateScenarios();

  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["current-valid", "reissued-history", "download-blocked"],
  );
});

test("returns the default portal certificate scenario when the query is unknown", () => {
  const scenario = resolvePortalCertificateScenario("unknown");

  assert.equal(scenario.id, "current-valid");
  assert.equal(scenario.selectedCertificateId, "cert-00142");
});

test("keeps the portal certificate detail blocked when the viewer is not available", () => {
  const scenario = resolvePortalCertificateScenario("download-blocked", "cert-00128");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /viewer integral/i);
  assert.equal(scenario.detail.actions.some((action) => action.status === "blocked"), true);
});

test("builds the canonical portal certificate catalog with selected certificate", () => {
  const catalog = buildPortalCertificateCatalog("reissued-history", "cert-00135-r1");
  const selectedScenario = catalog.scenarios.find((scenario) => scenario.id === "reissued-history");

  assert.equal(catalog.selectedScenarioId, "reissued-history");
  assert.ok(selectedScenario);
  assert.equal(selectedScenario.selectedCertificateId, "cert-00135-r1");
  assert.equal(selectedScenario.detail.certificateId, "cert-00135-r1");
});
