import assert from "node:assert/strict";
import { test } from "node:test";

import {
  emissionDryRunCatalogSchema,
  emissionWorkspaceCatalogSchema,
  onboardingCatalogSchema,
  reviewSignatureCatalogSchema,
  serviceOrderReviewCatalogSchema,
  selfSignupCatalogSchema,
  signatureQueueCatalogSchema,
  userDirectoryCatalogSchema,
} from "@afere/contracts";

import { buildOperationsOverviewModel } from "./operations-overview.js";

const EMISSION_WORKSPACE_CATALOG = emissionWorkspaceCatalogSchema.parse({
  selectedScenarioId: "team-attention",
  scenarios: [
    {
      id: "team-attention",
      label: "Equipe em atencao preventiva",
      description: "Competencias proximas do vencimento.",
      summary: {
        status: "attention",
        headline: "Operacao exige acao preventiva antes da assinatura",
        readyToEmit: false,
        recommendedAction: "Renovar as competencias que estao expirando antes da proxima janela de emissao.",
        readyModules: 4,
        attentionModules: 1,
        blockedModules: 0,
        blockers: [],
        warnings: ["Equipe com 1 competencia(s) expirando."],
      },
      modules: [
        {
          key: "team",
          title: "Equipe e competencias",
          status: "attention",
          detail: "Equipe em atencao preventiva: 1 competencia expirando para 4 usuarios ativos.",
          href: "/auth/users?scenario=expiring-competencies",
        },
      ],
      references: {
        selfSignupScenarioId: "admin-guided",
        onboardingScenarioId: "ready",
        userDirectoryScenarioId: "expiring-competencies",
        dryRunScenarioId: "type-b-ready",
        reviewSignatureScenarioId: "segregated-ready",
      },
      nextActions: ["Renovar a autorizacao do signatario antes do vencimento."],
    },
  ],
});

const SELF_SIGNUP_CATALOG = selfSignupCatalogSchema.parse({
  selectedScenarioId: "signatory-ready",
  scenarios: [
    {
      id: "signatory-ready",
      label: "Signatario pronto",
      description: "Todos os provedores obrigatorios estao habilitados.",
      role: "signatory",
      result: {
        ok: true,
        missingProviders: [],
        mfaRequired: true,
      },
    },
  ],
});

const ONBOARDING_CATALOG = onboardingCatalogSchema.parse({
  selectedScenarioId: "blocked",
  scenarios: [
    {
      id: "blocked",
      label: "Bloqueado por prerequisitos",
      description: "Ainda faltam passos obrigatorios.",
      result: {
        completedWithinTarget: false,
        canEmitFirstCertificate: false,
        blockingReasons: ["primary_signatory_pending", "public_qr_pending"],
      },
    },
  ],
});

const EMISSION_CATALOG = emissionDryRunCatalogSchema.parse({
  selectedScenarioId: "type-b-ready",
  scenarios: [
    {
      id: "type-b-ready",
      label: "Tipo B pronto",
      description: "Todos os gates passam.",
      profile: "B",
      result: {
        status: "ready",
        profile: "B",
        summary: "Dry-run pronto para emissao controlada no perfil B.",
        blockers: [],
        warnings: [],
        checks: [
          {
            id: "profile_policy",
            title: "Politica regulatoria",
            status: "passed",
            detail: "Perfil B compativel com template-b.",
          },
          {
            id: "qr_authenticity",
            title: "QR publico",
            status: "passed",
            detail: "QR autenticado em dry-run com status authentic.",
          },
        ],
        artifacts: {
          templateId: "template-b",
          symbolPolicy: "blocked",
          certificateNumber: "AFR-000124",
          declarationSummary: "Resultado: 149.98 kg | U: +/-0.05 kg | k=2",
          qrCodeUrl: "https://portal.afere.local/verify?certificate=cert-dry-b-001&token=token-b-001",
          qrVerificationStatus: "authentic",
          publicPreview: {
            certificateNumber: "AFR-000124",
          },
        },
      },
    },
  ],
});

const REVIEW_SIGNATURE_CATALOG = reviewSignatureCatalogSchema.parse({
  selectedScenarioId: "segregated-ready",
  scenarios: [
    {
      id: "segregated-ready",
      label: "Workflow segregado e pronto",
      description: "Revisor e signatario estao corretos.",
      result: {
        status: "ready",
        stage: "in_review",
        summary: "Revisao tecnica liberada e assinatura futura preparada com segregacao valida.",
        blockers: [],
        warnings: [],
        allowedActions: ["review_certificate", "reject_to_executor"],
        reviewStep: {
          title: "Revisao tecnica",
          status: "ready",
          actorLabel: "Maria Revisora",
          detail: "A revisao pode seguir.",
        },
        signatureStep: {
          title: "Assinatura e emissao",
          status: "pending",
          actorLabel: "Carlos Signatario",
          detail: "Aguardando aprovacao da revisao.",
        },
        checks: [],
        assignments: {
          executor: {
            userId: "tech-1",
            displayName: "Joao Executor",
            roles: ["technician"],
            mfaEnabled: false,
            pendingAssignments: 0,
          },
          reviewer: {
            userId: "reviewer-1",
            displayName: "Maria Revisora",
            roles: ["technical_reviewer"],
            mfaEnabled: false,
            pendingAssignments: 1,
          },
          signatory: {
            userId: "signatory-1",
            displayName: "Carlos Signatario",
            roles: ["signatory"],
            mfaEnabled: true,
            pendingAssignments: 2,
          },
        },
        suggestions: {},
      },
    },
  ],
});

const SERVICE_ORDER_REVIEW_CATALOG = serviceOrderReviewCatalogSchema.parse({
  selectedScenarioId: "review-ready",
  scenarios: [
    {
      id: "review-ready",
      label: "OS pronta para revisao",
      description: "Linha do tempo, dados de execucao e checklist tecnico coerentes.",
      summary: {
        status: "ready",
        headline: "OS pronta para concluir a revisao tecnica",
        totalCount: 4,
        awaitingReviewCount: 1,
        awaitingSignatureCount: 1,
        inExecutionCount: 1,
        emittedCount: 1,
        blockedCount: 0,
        recommendedAction: "Aprovar a revisao tecnica.",
        blockers: [],
        warnings: [],
      },
      selectedItemId: "os-2026-00142",
      items: [
        {
          itemId: "os-2026-00142",
          workOrderNumber: "OS-2026-00142",
          customerName: "Lab. Acme",
          equipmentLabel: "Toledo Prix 3",
          status: "awaiting_review",
          technicianName: "Joao Executor",
          updatedAtLabel: "14:22",
        },
      ],
      detail: {
        itemId: "os-2026-00142",
        title: "OS-2026-00142 · Lab. Acme · Toledo Prix 3",
        status: "ready",
        statusLine: "Aguardando revisao · Atribuido a: Maria Revisora · Executado por: Joao Executor",
        executorLabel: "Joao Executor",
        assignedReviewerLabel: "Maria Revisora",
        procedureLabel: "PT-005 rev.04",
        standardsLabel: "PESO-001 / PESO-002",
        environmentLabel: "22.4 C",
        curvePointsLabel: "5 pontos",
        evidenceLabel: "12 evidencias",
        uncertaintyLabel: "0.05 kg",
        conformityLabel: "Aprovado",
        timeline: [
          {
            key: "created",
            label: "Criada",
            status: "complete",
            timestampLabel: "12/04 09:01",
          },
        ],
        metrics: [
          {
            label: "Repetibilidade",
            value: "sigma = 0,058 kg",
            tone: "ok",
          },
        ],
        checklist: [
          {
            label: "Padroes validos",
            status: "passed",
            detail: "Ok",
          },
        ],
        commentDraft: "Revisao liberada.",
        allowedActions: ["approve_review", "open_preview"],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
          previewScenarioId: "type-b-ready",
          reviewSignatureScenarioId: "segregated-ready",
          signatureQueueScenarioId: "approved-ready",
        },
      },
    },
  ],
});

const SIGNATURE_QUEUE_CATALOG = signatureQueueCatalogSchema.parse({
  selectedScenarioId: "approved-ready",
  scenarios: [
    {
      id: "approved-ready",
      label: "Fila pronta para assinatura",
      description: "Itens verdes para assinar.",
      summary: {
        status: "ready",
        headline: "Fila pronta para assinatura controlada",
        pendingCount: 2,
        readyCount: 2,
        attentionCount: 0,
        blockedCount: 0,
        batchReadyCount: 2,
        oldestPendingLabel: "2h 12min",
        recommendedAction: "Assinar os itens prontos.",
        blockers: [],
        warnings: [],
      },
      selectedItemId: "os-2026-00142",
      items: [
        {
          itemId: "os-2026-00142",
          workOrderNumber: "OS-2026-00142",
          customerName: "Lab. Acme",
          equipmentLabel: "Toledo Prix 3",
          instrumentType: "Balanca",
          waitingSinceLabel: "18 min",
          certificateNumber: "AFR-000124",
          status: "ready",
          previewScenarioId: "type-b-ready",
          reviewSignatureScenarioId: "approved-ready",
          validations: [
            {
              label: "Revisao tecnica",
              status: "passed",
              detail: "Revisao concluida.",
            },
          ],
          blockers: [],
          warnings: [],
        },
      ],
      approval: {
        itemId: "os-2026-00142",
        title: "OS-2026-00142 - assinatura final",
        status: "ready",
        signatoryDisplayName: "Carlos Signatario",
        authorizationLabel: "Signatario autorizado",
        statement: "Confirmo a emissao.",
        documentHash: "a3f9",
        canSign: true,
        actionLabel: "Assinar e emitir",
        blockers: [],
        warnings: [],
        authRequirements: [
          {
            factor: "password",
            label: "Senha",
            status: "configured",
            detail: "Obrigatoria.",
          },
        ],
        compactPreview: [
          {
            label: "Cliente",
            value: "Lab. Acme",
          },
        ],
      },
    },
  ],
});

const USER_DIRECTORY_CATALOG = userDirectoryCatalogSchema.parse({
  selectedScenarioId: "operational-team",
  scenarios: [
    {
      id: "operational-team",
      label: "Equipe operacional",
      description: "Time pronto para operar.",
      summary: {
        status: "ready",
        organizationName: "Lab. Acme",
        activeUsers: 4,
        invitedUsers: 1,
        suspendedUsers: 0,
        expiringCompetencies: 0,
        expiredCompetencies: 0,
      },
      users: [
        {
          userId: "user-1",
          displayName: "Joao Admin",
          email: "joao@lab.com",
          roles: ["admin"],
          status: "active",
          deviceCount: 1,
          competencies: [],
        },
      ],
    },
  ],
});

test("summarizes the canonical readiness across auth, onboarding and emission", () => {
  const model = buildOperationsOverviewModel({
    emissionWorkspaceCatalog: EMISSION_WORKSPACE_CATALOG,
    selfSignupCatalog: SELF_SIGNUP_CATALOG,
    onboardingCatalog: ONBOARDING_CATALOG,
    emissionCatalog: EMISSION_CATALOG,
    serviceOrderReviewCatalog: SERVICE_ORDER_REVIEW_CATALOG,
    reviewSignatureCatalog: REVIEW_SIGNATURE_CATALOG,
    signatureQueueCatalog: SIGNATURE_QUEUE_CATALOG,
    userDirectoryCatalog: USER_DIRECTORY_CATALOG,
  });

  assert.equal(model.readyCount, 6);
  assert.equal(model.blockedCount, 2);
  assert.equal(model.allSourcesAvailable, true);
  assert.equal(model.heroStatusTone, "warn");
  assert.equal(model.cards[0]?.href, "/emission/workspace?scenario=team-attention");
  assert.equal(model.cards[0]?.statusLabel, "Workspace com atencao");
  assert.equal(model.cards[1]?.href, "/auth/self-signup?scenario=signatory-ready");
  assert.equal(model.cards[2]?.statusLabel, "Emissao bloqueada");
  assert.equal(model.cards[3]?.statusLabel, "Emissao pronta");
  assert.equal(model.cards[4]?.statusLabel, "OS pronta");
  assert.equal(
    model.cards[4]?.href,
    "/emission/service-order-review?scenario=review-ready&item=os-2026-00142",
  );
  assert.equal(model.cards[5]?.statusLabel, "Workflow liberado");
  assert.equal(model.cards[6]?.statusLabel, "Fila pronta");
  assert.equal(model.cards[7]?.statusLabel, "Equipe saudavel");
});

test("fails closed when one or more canonical sources are unavailable", () => {
  const model = buildOperationsOverviewModel({
    emissionWorkspaceCatalog: null,
    selfSignupCatalog: null,
    onboardingCatalog: null,
    emissionCatalog: null,
    serviceOrderReviewCatalog: null,
    reviewSignatureCatalog: null,
    signatureQueueCatalog: null,
    userDirectoryCatalog: null,
  });

  assert.equal(model.readyCount, 0);
  assert.equal(model.blockedCount, 8);
  assert.equal(model.allSourcesAvailable, false);
  assert.equal(model.heroStatusTone, "warn");
  assert.equal(model.heroStatusLabel, "Revisao operacional necessaria");
  assert.equal(model.cards.length, 8);
  assert.equal(model.cards.every((card) => card.statusLabel === "Sem carga canonica"), true);
});
