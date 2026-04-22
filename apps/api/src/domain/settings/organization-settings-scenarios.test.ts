import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildOrganizationSettingsCatalog,
  listOrganizationSettingsScenarios,
  resolveOrganizationSettingsScenario,
} from "./organization-settings-scenarios.js";

test("lists every canonical organization settings scenario", () => {
  const scenarios = listOrganizationSettingsScenarios();

  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-ready", "renewal-attention", "profile-change-blocked"],
  );
});

test("returns the default organization settings scenario when the query is unknown", () => {
  const scenario = resolveOrganizationSettingsScenario("unknown");

  assert.equal(scenario.id, "operational-ready");
  assert.equal(scenario.selectedSectionKey, "regulatory_profile");
  assert.equal(scenario.detail.status, "ready");
});

test("keeps the organization settings blocked when profile change lacks approvals", () => {
  const scenario = resolveOrganizationSettingsScenario("profile-change-blocked", "regulatory_profile");

  assert.equal(scenario.summary.status, "blocked");
  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /dupla aprovacao/i);
});

test("builds the canonical organization settings catalog with selected section", () => {
  const catalog = buildOrganizationSettingsCatalog("renewal-attention", "lgpd_dpo");
  const selectedScenario = catalog.scenarios.find((scenario) => scenario.id === "renewal-attention");

  assert.equal(catalog.selectedScenarioId, "renewal-attention");
  assert.ok(selectedScenario);
  assert.equal(selectedScenario.selectedSectionKey, "lgpd_dpo");
  assert.equal(selectedScenario.detail.sectionKey, "lgpd_dpo");
  assert.equal(selectedScenario.summary.status, "attention");
});
