import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildCustomerRegistryCatalog,
  buildEquipmentRegistryCatalog,
  listCustomerRegistryScenarios,
  listEquipmentRegistryScenarios,
  resolveCustomerRegistryScenario,
  resolveEquipmentRegistryScenario,
} from "./customer-equipment-scenarios.js";

test("lists every canonical customer registry scenario", () => {
  const scenarios = listCustomerRegistryScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-ready", "certificate-attention", "registration-blocked"],
  );
});

test("returns the default customer registry scenario when the query is unknown", () => {
  const scenario = resolveCustomerRegistryScenario("unknown");

  assert.equal(scenario.id, "operational-ready");
  assert.equal(scenario.detail.status, "ready");
});

test("keeps customer registry in attention when the selected client has a due-soon calibration", () => {
  const scenario = resolveCustomerRegistryScenario("certificate-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.warnings.join(" "), /proxima calibracao critica/i);
  assert.equal(scenario.summary.dueSoonCount, 1);
});

test("blocks customer registry when the selected client depends on incomplete equipment registration", () => {
  const scenario = resolveCustomerRegistryScenario("registration-blocked");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /CEP validado|Campos ausentes/i);
});

test("allows switching the selected customer inside the same scenario", () => {
  const scenario = resolveCustomerRegistryScenario("operational-ready", "customer-002");

  assert.equal(scenario.selectedCustomerId, "customer-002");
  assert.equal(scenario.detail.customerId, "customer-002");
  assert.match(scenario.detail.title, /Padaria Pao Doce/i);
});

test("lists every canonical equipment registry scenario", () => {
  const scenarios = listEquipmentRegistryScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-ready", "certificate-attention", "registration-blocked"],
  );
});

test("returns the default equipment registry scenario when the query is unknown", () => {
  const scenario = resolveEquipmentRegistryScenario("unknown");

  assert.equal(scenario.id, "operational-ready");
  assert.equal(scenario.detail.status, "ready");
});

test("keeps equipment registry in attention when a selected item is near expiration", () => {
  const scenario = resolveEquipmentRegistryScenario("certificate-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.warnings.join(" "), /janela critica de vencimento/i);
  assert.equal(scenario.summary.dueSoonCount, 1);
});

test("blocks equipment registry when the selected item is missing minimum address data", () => {
  const scenario = resolveEquipmentRegistryScenario("registration-blocked");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /address\.postalCode/i);
});

test("allows switching the selected equipment inside the same scenario", () => {
  const scenario = resolveEquipmentRegistryScenario("operational-ready", "equipment-002");

  assert.equal(scenario.selectedEquipmentId, "equipment-002");
  assert.equal(scenario.detail.equipmentId, "equipment-002");
  assert.match(scenario.detail.title, /EQ-0011/i);
});

test("builds the canonical customer and equipment catalogs with selected scenario", () => {
  const customerCatalog = buildCustomerRegistryCatalog("certificate-attention");
  const equipmentCatalog = buildEquipmentRegistryCatalog("registration-blocked");

  assert.equal(customerCatalog.selectedScenarioId, "certificate-attention");
  assert.equal(customerCatalog.scenarios.length, 3);
  assert.equal(equipmentCatalog.selectedScenarioId, "registration-blocked");
  assert.equal(equipmentCatalog.scenarios.length, 3);
});
