import assert from "node:assert/strict";
import { test } from "node:test";

import { internalAuditCatalogSchema } from "@afere/contracts";

import { loadInternalAuditCatalog } from "./internal-audit-api.js";
import { buildInternalAuditCatalogView } from "./internal-audit-scenarios.js";

const CATALOG_FIXTURE = internalAuditCatalogSchema.parse({
  selectedScenarioId: "follow-up-attention",
  scenarios: [
    {
      id: "follow-up-attention",
      label: "Ciclo concluido com follow-up pendente",
      description: "Ciclo 1 encerrado, mas com NCs ainda em tratamento.",
      summary: {
        status: "attention",
        headline: "Follow-up de auditoria interna exige fechamento de achados",
        programLabel: "Auditoria Interna 2026",
        plannedCycleCount: 4,
        completedCycleCount: 1,
        openFindingCount: 2,
        recommendedAction: "Fechar NC-013 e NC-014 antes do proximo ciclo.",
        blockers: [],
        warnings: ["O ciclo 2 nao deve abrir sem follow-up minimo."],
      },
      selectedCycleId: "audit-cycle-2026-1",
      cycles: [
        {
          cycleId: "audit-cycle-2026-1",
          cycleLabel: "Ciclo 1",
          windowLabel: "Mar/2026",
          scopeLabel: "§6.4 Equipamentos | §7.6 Incerteza",
          auditorLabel: "Ana Costa",
          findingsLabel: "2 NC em tratamento",
          status: "attention",
          statusLabel: "2 NC em tratamento",
        },
      ],
      detail: {
        cycleId: "audit-cycle-2026-1",
        title: "Ciclo 1 - §6.4 Equipamentos | §7.6 Incerteza",
        status: "attention",
        noticeLabel: "Ciclo concluido, mas ainda dependente do fechamento formal dos achados abertos.",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Carlos, Maria",
        periodLabel: "10/03/2026 a 12/03/2026",
        scopeLabel: "§6.4 Equipamentos | §7.6 Incerteza",
        reportLabel: "Relatorio IA-2026-C1 emitido com follow-up aberto",
        evidenceLabel: "Checklist aplicado e follow-up arquivados.",
        nextReviewLabel: "Fechar NC-013 e NC-014 antes do ciclo 2.",
        checklist: [
          {
            key: "inventory-updated",
            requirementLabel: "§6.4 Inventario atualizado",
            evidenceLabel: "Relatorio PadInv-202603 [PDF].",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c1-nc013",
            title: "NC-013 - Balanco de incerteza nao documentado",
            severityLabel: "Media",
            ownerLabel: "Carlos",
            dueDateLabel: "11/04/2026",
            status: "attention",
            nonconformityId: "nc-013",
          },
        ],
        blockers: [],
        warnings: ["O ciclo 2 nao deve abrir sem follow-up minimo."],
        links: {
          nonconformityScenarioId: "open-attention",
        },
      },
    },
    {
      id: "extraordinary-escalation",
      label: "Auditoria extraordinaria exigida",
      description: "Caso critico exige ciclo extraordinario.",
      summary: {
        status: "blocked",
        headline: "Programa exige auditoria extraordinaria antes da proxima liberacao",
        programLabel: "Auditoria Interna 2026",
        plannedCycleCount: 4,
        completedCycleCount: 1,
        openFindingCount: 3,
        recommendedAction: "Abrir a auditoria extraordinaria imediatamente.",
        blockers: ["O caso critico exige auditoria extraordinaria."],
        warnings: ["NC-015 segue ancorando o caso."],
      },
      selectedCycleId: "audit-cycle-extra-2026",
      cycles: [
        {
          cycleId: "audit-cycle-extra-2026",
          cycleLabel: "Ciclo Extra",
          windowLabel: "Abr/2026",
          scopeLabel: "§7.8 Certificados | §8.4 Registros | §7.10 Trabalho nao conforme",
          auditorLabel: "Ana Costa",
          findingsLabel: "1 critica e 2 graves",
          status: "blocked",
          statusLabel: "Extraordinaria pendente",
        },
      ],
      detail: {
        cycleId: "audit-cycle-extra-2026",
        title: "Ciclo Extra - §7.8 Certificados | §8.4 Registros | §7.10 Trabalho nao conforme",
        status: "blocked",
        noticeLabel: "Ciclo extraordinario exigido pelo recorte critico e ainda pendente de abertura formal.",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Carlos, Maria, Joao Silva",
        periodLabel: "Janela extraordinaria solicitada em 22/04/2026",
        scopeLabel: "§7.8 Certificados | §8.4 Registros | §7.10 Trabalho nao conforme",
        reportLabel: "Abertura extraordinaria pendente de parecer inicial",
        evidenceLabel: "Briefing critico e NC-015 anexados ao preparo.",
        nextReviewLabel: "Abrir o ciclo extraordinario antes de qualquer liberacao operacional.",
        checklist: [
          {
            key: "hash-chain-check",
            requirementLabel: "§8.4 Integridade da hash-chain verificada",
            evidenceLabel: "Divergencia ativa na trilha critica.",
            status: "blocked",
          },
        ],
        findings: [
          {
            findingId: "finding-extra-01",
            title: "Hash-chain divergente em recorte critico",
            severityLabel: "Alta",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Imediato",
            status: "blocked",
            nonconformityId: "nc-015",
          },
        ],
        blockers: ["O caso critico exige auditoria extraordinaria."],
        warnings: ["NC-015 segue ancorando o caso."],
        links: {
          nonconformityScenarioId: "critical-response",
        },
      },
    },
  ],
});

test("selects the active internal audit scenario from the backend catalog", () => {
  const view = buildInternalAuditCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "follow-up-attention");
  assert.equal(view.selectedScenario.selectedCycle.cycleId, "audit-cycle-2026-1");
  assert.match(view.selectedScenario.summaryLabel, /2 achado\(s\) em follow-up/i);
});

test("loads and validates the internal audit catalog from the backend endpoint", async () => {
  const catalog = await loadInternalAuditCatalog({
    scenarioId: "follow-up-attention",
    cycleId: "audit-cycle-2026-1",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/internal-audit?scenario=follow-up-attention&cycle=audit-cycle-2026-1",
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
  assert.equal(catalog.selectedScenarioId, "follow-up-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the internal audit backend payload is invalid", async () => {
  const catalog = await loadInternalAuditCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "follow-up-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
