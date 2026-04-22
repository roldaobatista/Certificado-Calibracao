import assert from "node:assert/strict";
import { test } from "node:test";

import { customerRegistryCatalogSchema } from "@afere/contracts";

import { loadCustomerRegistryCatalog } from "./customer-registry-api.js";
import { buildCustomerRegistryCatalogView } from "./customer-registry-scenarios.js";

const CATALOG_FIXTURE = customerRegistryCatalogSchema.parse({
  selectedScenarioId: "certificate-attention",
  scenarios: [
    {
      id: "operational-ready",
      label: "Clientes ativos e cadastros consistentes",
      description: "Tudo verde.",
      summary: {
        status: "ready",
        headline: "Cadastros de clientes prontos para sustentar a emissao",
        activeCustomers: 3,
        attentionCustomers: 0,
        blockedCustomers: 0,
        totalEquipment: 94,
        certificatesThisMonth: 25,
        dueSoonCount: 0,
        recommendedAction: "Seguir operacao normal.",
        blockers: [],
        warnings: [],
      },
      selectedCustomerId: "customer-001",
      customers: [
        {
          customerId: "customer-001",
          legalName: "Lab. Acme Analises Ltda.",
          tradeName: "Lab. Acme",
          documentLabel: "12.345.678/0001-XX",
          segmentLabel: "Laboratorio clinico",
          equipmentCount: 23,
          certificatesThisMonth: 15,
          nextDueLabel: "02/05/2026",
          status: "ready",
        },
      ],
      detail: {
        customerId: "customer-001",
        title: "Lab. Acme · 12.345.678/0001-XX",
        status: "ready",
        statusLine: "Cadastro pronto.",
        accountOwnerLabel: "Joao",
        contractLabel: "Vigente",
        specialConditionsLabel: "Sala climatizada",
        tabs: [
          { key: "data", label: "Dados" },
          { key: "contacts", label: "Contatos", countLabel: "1" },
          { key: "addresses", label: "Enderecos", countLabel: "1" },
          { key: "equipment", label: "Equipamentos", countLabel: "23" },
          { key: "certificates", label: "Certificados", countLabel: "1" },
          { key: "attachments", label: "Anexos", countLabel: "1" },
          { key: "history", label: "Hist.", countLabel: "1" },
        ],
        contacts: [
          {
            name: "Joao",
            roleLabel: "RT",
            email: "joao@lab.com",
            primary: true,
          },
        ],
        addresses: [
          {
            label: "Matriz",
            line1: "Rua 1",
            cityStateLabel: "Cuiaba / MT",
            postalCodeLabel: "78000-000",
            countryLabel: "Brasil",
          },
        ],
        equipmentHighlights: [
          {
            equipmentId: "equipment-001",
            code: "EQ-0007",
            tagCode: "BAL-007",
            typeModelLabel: "NAWI Toledo Prix 3",
            nextDueLabel: "18/10/2026",
            status: "ready",
          },
        ],
        certificateHighlights: [
          {
            certificateNumber: "AFR-000124",
            workOrderNumber: "OS-2026-00142",
            issuedAtLabel: "22/04/2026",
            revisionLabel: "R0",
            statusLabel: "Emitido",
          },
        ],
        attachments: [{ label: "Contrato", statusLabel: "Vigente" }],
        history: [{ label: "Criado", timestampLabel: "12/04" }],
        blockers: [],
        warnings: [],
        links: {
          equipmentScenarioId: "operational-ready",
          selectedEquipmentId: "equipment-001",
          serviceOrderScenarioId: "review-ready",
          reviewItemId: "os-2026-00142",
          dryRunScenarioId: "type-b-ready",
        },
      },
    },
    {
      id: "certificate-attention",
      label: "Cliente com vencimento proximo",
      description: "Atencao.",
      summary: {
        status: "attention",
        headline: "Cliente com calendario operacional em atencao",
        activeCustomers: 3,
        attentionCustomers: 1,
        blockedCustomers: 0,
        totalEquipment: 94,
        certificatesThisMonth: 25,
        dueSoonCount: 1,
        recommendedAction: "Planejar recalibracao.",
        blockers: [],
        warnings: ["Cliente com proxima calibracao critica nas proximas 24 horas."],
      },
      selectedCustomerId: "customer-003",
      customers: [
        {
          customerId: "customer-003",
          legalName: "Industria XYZ Alimentos S.A.",
          tradeName: "Industria XYZ",
          documentLabel: "34.567.890/0001-ZZ",
          segmentLabel: "Industria alimenticia",
          equipmentCount: 67,
          certificatesThisMonth: 8,
          nextDueLabel: "23/04/2026 ⚠",
          status: "attention",
        },
      ],
      detail: {
        customerId: "customer-003",
        title: "Industria XYZ · 34.567.890/0001-ZZ",
        status: "attention",
        statusLine: "Cliente em atencao operacional.",
        accountOwnerLabel: "Carlos",
        contractLabel: "Vigente",
        specialConditionsLabel: "Janela noturna",
        tabs: [
          { key: "data", label: "Dados" },
          { key: "contacts", label: "Contatos", countLabel: "1" },
          { key: "addresses", label: "Enderecos", countLabel: "1" },
          { key: "equipment", label: "Equipamentos", countLabel: "67" },
          { key: "certificates", label: "Certificados", countLabel: "1" },
          { key: "attachments", label: "Anexos", countLabel: "1" },
          { key: "history", label: "Hist.", countLabel: "1" },
        ],
        contacts: [
          {
            name: "Carlos",
            roleLabel: "Manutencao",
            email: "carlos@xyz.com",
            primary: true,
          },
        ],
        addresses: [
          {
            label: "Planta",
            line1: "Distrito Industrial, 2200",
            cityStateLabel: "Varzea Grande / MT",
            postalCodeLabel: "78110-500",
            countryLabel: "Brasil",
          },
        ],
        equipmentHighlights: [
          {
            equipmentId: "equipment-003",
            code: "EQ-0008",
            tagCode: "BL-X-22",
            typeModelLabel: "NAWI Marte L50",
            nextDueLabel: "02/05/2026 ⚠",
            status: "attention",
          },
        ],
        certificateHighlights: [
          {
            certificateNumber: "XYZ-000218",
            workOrderNumber: "OS-2026-00141",
            issuedAtLabel: "Pendente",
            revisionLabel: "R0",
            statusLabel: "Revisao em atencao",
          },
        ],
        attachments: [{ label: "Contrato", statusLabel: "Vigente" }],
        history: [{ label: "Migrado", timestampLabel: "08/04" }],
        blockers: [],
        warnings: ["Cliente com proxima calibracao critica nas proximas 24 horas."],
        links: {
          equipmentScenarioId: "certificate-attention",
          selectedEquipmentId: "equipment-003",
          serviceOrderScenarioId: "history-pending",
          reviewItemId: "os-2026-00141",
          dryRunScenarioId: "type-b-ready",
        },
      },
    },
  ],
});

test("selects the active customer registry scenario from the backend catalog", () => {
  const view = buildCustomerRegistryCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "certificate-attention");
  assert.equal(view.selectedScenario.selectedCustomer.customerId, "customer-003");
  assert.match(view.selectedScenario.summaryLabel, /1 cliente\(s\) em atencao/i);
});

test("loads and validates the customer registry catalog from the backend endpoint", async () => {
  const catalog = await loadCustomerRegistryCatalog({
    scenarioId: "operational-ready",
    customerId: "customer-001",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/registry/customers?scenario=operational-ready&customer=customer-001",
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
  assert.equal(catalog.selectedScenarioId, "certificate-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the customer registry backend payload is invalid", async () => {
  const catalog = await loadCustomerRegistryCatalog({
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
