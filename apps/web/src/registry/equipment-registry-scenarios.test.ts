import assert from "node:assert/strict";
import { test } from "node:test";

import { equipmentRegistryCatalogSchema } from "@afere/contracts";

import { loadEquipmentRegistryCatalog } from "./equipment-registry-api.js";
import { buildEquipmentRegistryCatalogView } from "./equipment-registry-scenarios.js";

const CATALOG_FIXTURE = equipmentRegistryCatalogSchema.parse({
  selectedScenarioId: "registration-blocked",
  scenarios: [
    {
      id: "operational-ready",
      label: "Equipamentos ativos",
      description: "Tudo verde.",
      summary: {
        status: "ready",
        headline: "Equipamentos ativos e cadastros consistentes",
        totalEquipment: 4,
        readyCount: 4,
        attentionCount: 0,
        blockedCount: 0,
        dueSoonCount: 0,
        recommendedAction: "Seguir operacao.",
        blockers: [],
        warnings: [],
      },
      selectedEquipmentId: "equipment-001",
      items: [
        {
          equipmentId: "equipment-001",
          customerId: "customer-001",
          customerName: "Lab. Acme",
          code: "EQ-0007",
          tagCode: "BAL-007",
          serialNumber: "SN-300-01",
          typeModelLabel: "NAWI Toledo Prix 3",
          capacityClassLabel: "300 kg · 0,05 kg · III",
          lastCalibrationLabel: "18/04/2026",
          nextCalibrationLabel: "18/10/2026",
          registrationStatusLabel: "Cliente e endereco minimo validados.",
          status: "ready",
          missingFields: [],
          dryRunScenarioId: "type-b-ready",
        },
      ],
      detail: {
        equipmentId: "equipment-001",
        title: "EQ-0007 · BAL-007 · NAWI Toledo Prix 3",
        status: "ready",
        statusLine: "Equipamento apto.",
        customerLabel: "Lab. Acme Analises Ltda.",
        addressLabel: "Rua da Calibracao, 100",
        standardSetLabel: "PESO-001 / PESO-002 / TH-003",
        lastServiceOrderLabel: "OS-2026-00142 · 19/04",
        nextCalibrationLabel: "18/10/2026",
        blockers: [],
        warnings: [],
        links: {
          customerScenarioId: "operational-ready",
          customerId: "customer-001",
          serviceOrderScenarioId: "review-ready",
          reviewItemId: "os-2026-00142",
          dryRunScenarioId: "type-b-ready",
        },
      },
    },
    {
      id: "registration-blocked",
      label: "Cadastro bloqueado",
      description: "Endereco incompleto.",
      summary: {
        status: "blocked",
        headline: "Equipamento bloqueado por cadastro incompleto",
        totalEquipment: 5,
        readyCount: 4,
        attentionCount: 0,
        blockedCount: 1,
        dueSoonCount: 0,
        recommendedAction: "Completar endereco.",
        blockers: ["Endereco minimo do equipamento continua incompleto para a emissao."],
        warnings: ["Cliente permanece em homologacao assistida."],
      },
      selectedEquipmentId: "equipment-004",
      items: [
        {
          equipmentId: "equipment-004",
          customerId: "customer-004",
          customerName: "Cadastro pendente",
          code: "EQ-0404",
          tagCode: "BAL-404",
          serialNumber: "SN-C-500",
          typeModelLabel: "Balanca plataforma Marte 500",
          capacityClassLabel: "500 kg · 0,1 kg · III",
          lastCalibrationLabel: "19/04/2026",
          nextCalibrationLabel: "Cadastro pendente",
          registrationStatusLabel: "Cadastro incompleto: address.postalCode.",
          status: "blocked",
          missingFields: ["address.postalCode"],
          dryRunScenarioId: "type-c-blocked",
        },
      ],
      detail: {
        equipmentId: "equipment-004",
        title: "EQ-0404 · BAL-404 · Balanca plataforma Marte 500",
        status: "blocked",
        statusLine: "Equipamento bloqueado.",
        customerLabel: "Cliente sem cadastro completo",
        addressLabel: "Rua Sem CEP, 10",
        standardSetLabel: "PESO-009 / TH-404",
        lastServiceOrderLabel: "OS-2026-00147 · 19/04",
        nextCalibrationLabel: "Cadastro pendente",
        blockers: ["Campos ausentes: address.postalCode."],
        warnings: ["Cliente permanece em homologacao assistida."],
        links: {
          customerScenarioId: "registration-blocked",
          customerId: "customer-004",
          serviceOrderScenarioId: "review-blocked",
          reviewItemId: "os-2026-00147",
          dryRunScenarioId: "type-c-blocked",
        },
      },
    },
  ],
});

test("selects the active equipment registry scenario from the backend catalog", () => {
  const view = buildEquipmentRegistryCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "registration-blocked");
  assert.equal(view.selectedScenario.selectedEquipment.equipmentId, "equipment-004");
  assert.match(view.selectedScenario.summaryLabel, /1 equipamento\(s\) bloqueado/i);
});

test("loads and validates the equipment registry catalog from the backend endpoint", async () => {
  const catalog = await loadEquipmentRegistryCatalog({
    scenarioId: "operational-ready",
    equipmentId: "equipment-001",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/registry/equipment?scenario=operational-ready&equipment=equipment-001",
      );

      return new Response(JSON.stringify(CATALOG_FIXTURE), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      });
    },
  });

  assert.ok(catalog);
  assert.equal(catalog.selectedScenarioId, "registration-blocked");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the equipment registry backend payload is invalid", async () => {
  const catalog = await loadEquipmentRegistryCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "operational-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
