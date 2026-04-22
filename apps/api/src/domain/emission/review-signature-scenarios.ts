import type {
  ReviewSignatureCatalog,
  ReviewSignatureScenario,
  ReviewSignatureScenarioId,
} from "@afere/contracts";

import {
  evaluateReviewSignatureWorkflow,
  type WorkflowMembershipInput,
} from "./review-signature-workflow.js";

const EXECUTOR: WorkflowMembershipInput = {
  userId: "tech-1",
  displayName: "Joao Executor",
  organizationId: "org-acme",
  roles: ["technician"],
  active: true,
  mfaEnabled: false,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 0,
};

const REVIEWER: WorkflowMembershipInput = {
  userId: "reviewer-1",
  displayName: "Maria Revisora",
  organizationId: "org-acme",
  roles: ["technical_reviewer"],
  active: true,
  mfaEnabled: false,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 1,
};

const QUALITY_MANAGER: WorkflowMembershipInput = {
  userId: "quality-1",
  displayName: "Renata Qualidade",
  organizationId: "org-acme",
  roles: ["quality_manager"],
  active: true,
  mfaEnabled: true,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 0,
};

const SIGNATORY: WorkflowMembershipInput = {
  userId: "signatory-1",
  displayName: "Carlos Signatario",
  organizationId: "org-acme",
  roles: ["signatory"],
  active: true,
  mfaEnabled: true,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 2,
};

const BACKUP_SIGNATORY: WorkflowMembershipInput = {
  userId: "signatory-2",
  displayName: "Paula Assinatura",
  organizationId: "org-acme",
  roles: ["signatory"],
  active: true,
  mfaEnabled: true,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 1,
};

const SCENARIOS: ReviewSignatureScenario[] = [
  {
    id: "segregated-ready",
    label: "Workflow segregado e pronto",
    description: "Executor, revisor e signatario estao segregados e elegiveis no perfil V1.",
    result: evaluateReviewSignatureWorkflow({
      organizationId: "org-acme",
      instrumentType: "balanca",
      stage: "in_review",
      executor: EXECUTOR,
      reviewer: REVIEWER,
      signatory: SIGNATORY,
      candidates: [EXECUTOR, REVIEWER, QUALITY_MANAGER, SIGNATORY, BACKUP_SIGNATORY],
    }),
  },
  {
    id: "reviewer-conflict",
    label: "Revisor igual ao executor",
    description: "O workflow bloqueia quando o executor tenta revisar a propria OS.",
    result: evaluateReviewSignatureWorkflow({
      organizationId: "org-acme",
      instrumentType: "balanca",
      stage: "in_review",
      executor: EXECUTOR,
      reviewer: { ...EXECUTOR, roles: ["technician", "technical_reviewer"] },
      signatory: SIGNATORY,
      candidates: [EXECUTOR, REVIEWER, QUALITY_MANAGER, SIGNATORY, BACKUP_SIGNATORY],
    }),
  },
  {
    id: "signatory-mfa-blocked",
    label: "Assinatura bloqueada por MFA",
    description: "Mesmo apos a revisao, a emissao falha fechado sem MFA no signatario.",
    result: evaluateReviewSignatureWorkflow({
      organizationId: "org-acme",
      instrumentType: "balanca",
      stage: "approved",
      executor: EXECUTOR,
      reviewer: REVIEWER,
      signatory: { ...SIGNATORY, mfaEnabled: false },
      candidates: [EXECUTOR, REVIEWER, QUALITY_MANAGER, SIGNATORY, BACKUP_SIGNATORY],
    }),
  },
];

export function listReviewSignatureScenarios(): ReviewSignatureScenario[] {
  return SCENARIOS;
}

export function resolveReviewSignatureScenario(scenarioId?: string): ReviewSignatureScenario {
  const scenario = SCENARIOS.find((item) => item.id === scenarioId) ?? SCENARIOS[0];

  if (!scenario) {
    throw new Error("missing_review_signature_scenarios");
  }

  return scenario;
}

export function buildReviewSignatureCatalog(scenarioId?: string): ReviewSignatureCatalog {
  const selectedScenario = resolveReviewSignatureScenario(scenarioId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listReviewSignatureScenarios(),
  };
}

export type ReviewSignatureScenarioDefinition = ReviewSignatureScenario;
export type ReviewSignatureScenarioSelection = ReviewSignatureScenarioId;
