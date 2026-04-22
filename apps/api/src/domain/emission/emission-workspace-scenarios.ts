import type {
  EmissionDryRunScenarioId,
  EmissionWorkspaceCatalog,
  EmissionWorkspaceModule,
  EmissionWorkspaceScenario,
  EmissionWorkspaceScenarioId,
  EmissionWorkspaceScenarioRefs,
  EmissionWorkspaceStatus,
  OnboardingBlockingReason,
  ReviewSignatureWorkflowResult,
  SelfSignupScenarioId,
  UserDirectoryScenarioId,
} from "@afere/contracts";

import { resolveSelfSignupScenario } from "../auth/self-signup-scenarios.js";
import { resolveUserDirectoryScenario } from "../auth/user-directory-scenarios.js";
import { resolveOnboardingScenario } from "../onboarding/onboarding-scenarios.js";
import { resolveEmissionDryRunScenario } from "./dry-run-scenarios.js";
import { resolveReviewSignatureScenario } from "./review-signature-scenarios.js";

type EmissionWorkspaceScenarioDefinition = {
  label: string;
  description: string;
  headline: string;
  recommendedAction: string;
  references: EmissionWorkspaceScenarioRefs;
  nextActions: string[];
};

const SCENARIOS = {
  "baseline-ready": {
    label: "Baseline operacional pronta",
    description: "Auth, onboarding, equipe, dry-run e workflow canonicamente alinhados para seguir no fluxo de V1.",
    headline: "Operacao pronta para seguir com revisao e assinatura",
    recommendedAction: "Concluir a revisao tecnica da OS atual para liberar a assinatura.",
    references: {
      selfSignupScenarioId: "signatory-ready",
      onboardingScenarioId: "ready",
      userDirectoryScenarioId: "operational-team",
      dryRunScenarioId: "type-b-ready",
      reviewSignatureScenarioId: "segregated-ready",
    },
    nextActions: [
      "Concluir a revisao tecnica da OS corrente.",
      "Manter a equipe de revisao e assinatura sem conflito de segregacao.",
      "Prosseguir para assinatura somente apos a aprovacao tecnica.",
    ],
  },
  "team-attention": {
    label: "Equipe em atencao preventiva",
    description: "A operacao ainda consegue seguir, mas o diretorio de competencias ja aponta risco proximo para o time de assinatura.",
    headline: "Operacao exige acao preventiva antes da assinatura",
    recommendedAction: "Renovar as competencias que estao expirando antes da proxima janela de emissao.",
    references: {
      selfSignupScenarioId: "admin-guided",
      onboardingScenarioId: "ready",
      userDirectoryScenarioId: "expiring-competencies",
      dryRunScenarioId: "type-b-ready",
      reviewSignatureScenarioId: "segregated-ready",
    },
    nextActions: [
      "Renovar a autorizacao do signatario antes do vencimento.",
      "Confirmar se a fila atual sera concluida antes da expiracao da competencia.",
      "Revalidar o workspace apos atualizar a evidencia de competencia.",
    ],
  },
  "release-blocked": {
    label: "Liberacao bloqueada",
    description: "O workspace consolida prerequisitos, equipe e assinatura em estado fail-closed antes da emissao oficial.",
    headline: "Operacao bloqueada por gates criticos de V1",
    recommendedAction: "Corrigir onboarding, equipe, dry-run e MFA do signatario antes de tentar emitir.",
    references: {
      selfSignupScenarioId: "signatory-ready",
      onboardingScenarioId: "blocked",
      userDirectoryScenarioId: "suspended-access",
      dryRunScenarioId: "type-c-blocked",
      reviewSignatureScenarioId: "signatory-mfa-blocked",
    },
    nextActions: [
      "Fechar os prerequisitos pendentes do onboarding da organizacao.",
      "Regularizar o revisor suspenso e as competencias vencidas da equipe.",
      "Habilitar MFA no signatario antes da etapa final de assinatura.",
    ],
  },
} as const satisfies Record<EmissionWorkspaceScenarioId, EmissionWorkspaceScenarioDefinition>;

const DEFAULT_SCENARIO: EmissionWorkspaceScenarioId = "baseline-ready";

export function listEmissionWorkspaceScenarios(): EmissionWorkspaceScenario[] {
  return (Object.keys(SCENARIOS) as EmissionWorkspaceScenarioId[]).map((scenarioId) =>
    resolveEmissionWorkspaceScenario(scenarioId),
  );
}

export function resolveEmissionWorkspaceScenario(scenarioId?: string): EmissionWorkspaceScenario {
  const id = isEmissionWorkspaceScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const definition = SCENARIOS[id];
  const selfSignupScenario = resolveSelfSignupScenario(definition.references.selfSignupScenarioId);
  const onboardingScenario = resolveOnboardingScenario(definition.references.onboardingScenarioId);
  const userDirectoryScenario = resolveUserDirectoryScenario(definition.references.userDirectoryScenarioId);
  const dryRunScenario = resolveEmissionDryRunScenario(definition.references.dryRunScenarioId);
  const reviewSignatureScenario = resolveReviewSignatureScenario(
    definition.references.reviewSignatureScenarioId,
  );

  const modules: EmissionWorkspaceModule[] = [
    buildAuthModule(selfSignupScenario.id, selfSignupScenario.label, selfSignupScenario.result),
    buildOnboardingModule(
      onboardingScenario.id,
      onboardingScenario.label,
      onboardingScenario.result.canEmitFirstCertificate,
      onboardingScenario.result.completedWithinTarget,
      onboardingScenario.result.blockingReasons,
    ),
    buildTeamModule(userDirectoryScenario.id, userDirectoryScenario.label, userDirectoryScenario.summary),
    buildDryRunModule(dryRunScenario.id, dryRunScenario.label, dryRunScenario.result),
    buildWorkflowModule(
      reviewSignatureScenario.id,
      reviewSignatureScenario.label,
      reviewSignatureScenario.result,
    ),
  ];

  const summary = buildWorkspaceSummary(
    definition,
    modules,
    selfSignupScenario.result.missingProviders,
    onboardingScenario.result.blockingReasons,
    userDirectoryScenario.summary,
    dryRunScenario.result.blockers,
    dryRunScenario.result.warnings,
    reviewSignatureScenario.result,
  );

  return {
    id,
    label: definition.label,
    description: definition.description,
    summary,
    modules,
    references: definition.references,
    nextActions: definition.nextActions,
  };
}

export function buildEmissionWorkspaceCatalog(scenarioId?: string): EmissionWorkspaceCatalog {
  const selectedScenario = resolveEmissionWorkspaceScenario(scenarioId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listEmissionWorkspaceScenarios(),
  };
}

export type EmissionWorkspaceScenarioDefinitionView = EmissionWorkspaceScenario;

function buildAuthModule(
  scenarioId: SelfSignupScenarioId,
  label: string,
  result: { ok: boolean; missingProviders: string[]; mfaRequired: boolean },
): EmissionWorkspaceModule {
  return {
    key: "auth",
    title: "Auth e auto-cadastro",
    status: result.ok ? "ready" : "blocked",
    detail: result.ok
      ? `${label} com provedores obrigatorios ativos${result.mfaRequired ? " e MFA prevista." : "."}`
      : `Faltam provedores obrigatorios: ${result.missingProviders.join(", ")}.`,
    href: `/auth/self-signup?scenario=${scenarioId}`,
  };
}

function buildOnboardingModule(
  scenarioId: "ready" | "blocked",
  label: string,
  canEmitFirstCertificate: boolean,
  completedWithinTarget: boolean,
  blockingReasons: OnboardingBlockingReason[],
): EmissionWorkspaceModule {
  return {
    key: "onboarding",
    title: "Onboarding da organizacao",
    status: canEmitFirstCertificate ? "ready" : "blocked",
    detail: canEmitFirstCertificate
      ? `${label}: primeira emissao liberada${completedWithinTarget ? " dentro" : " fora"} da meta de 1 hora.`
      : `${blockingReasons.length} prerequisito(s) ainda bloqueiam a primeira emissao.`,
    href: `/onboarding?scenario=${scenarioId}`,
  };
}

function buildTeamModule(
  scenarioId: UserDirectoryScenarioId,
  label: string,
  summary: {
    status: "ready" | "attention";
    activeUsers: number;
    invitedUsers: number;
    suspendedUsers: number;
    expiringCompetencies: number;
    expiredCompetencies: number;
  },
): EmissionWorkspaceModule {
  if (summary.suspendedUsers > 0 || summary.expiredCompetencies > 0) {
    return {
      key: "team",
      title: "Equipe e competencias",
      status: "blocked",
      detail: `${label}: ${summary.suspendedUsers} suspenso(s) e ${summary.expiredCompetencies} competencia(s) vencida(s).`,
      href: `/auth/users?scenario=${scenarioId}`,
    };
  }

  if (summary.expiringCompetencies > 0) {
    return {
      key: "team",
      title: "Equipe e competencias",
      status: "attention",
      detail: `${label}: ${summary.expiringCompetencies} competencia(s) expirando para ${summary.activeUsers} usuario(s) ativo(s).`,
      href: `/auth/users?scenario=${scenarioId}`,
    };
  }

  return {
    key: "team",
    title: "Equipe e competencias",
    status: "ready",
    detail: `${label}: ${summary.activeUsers} ativo(s) e ${summary.invitedUsers} convite(s) pendente(s) sem risco critico.`,
    href: `/auth/users?scenario=${scenarioId}`,
  };
}

function buildDryRunModule(
  scenarioId: EmissionDryRunScenarioId,
  label: string,
  result: {
    status: "ready" | "blocked";
    checks: Array<{ status: "passed" | "failed" }>;
    summary: string;
  },
): EmissionWorkspaceModule {
  const passedChecks = result.checks.filter((check) => check.status === "passed").length;

  return {
    key: "dry_run",
    title: "Pipeline seco de emissao",
    status: result.status === "ready" ? "ready" : "blocked",
    detail: `${label}: ${passedChecks}/${result.checks.length} checks verdes. ${result.summary}`,
    href: `/emission/dry-run?scenario=${scenarioId}`,
  };
}

function buildWorkflowModule(
  scenarioId: "segregated-ready" | "reviewer-conflict" | "signatory-mfa-blocked",
  label: string,
  result: ReviewSignatureWorkflowResult,
): EmissionWorkspaceModule {
  return {
    key: "workflow",
    title: "Revisao e assinatura",
    status: result.status === "ready" ? "ready" : "blocked",
    detail: `${label}: ${result.summary}`,
    href: `/emission/review-signature?scenario=${scenarioId}`,
  };
}

function buildWorkspaceSummary(
  definition: EmissionWorkspaceScenarioDefinition,
  modules: EmissionWorkspaceModule[],
  missingProviders: string[],
  onboardingBlockingReasons: OnboardingBlockingReason[],
  teamSummary: {
    suspendedUsers: number;
    expiringCompetencies: number;
    expiredCompetencies: number;
  },
  dryRunBlockers: string[],
  dryRunWarnings: string[],
  workflowResult: ReviewSignatureWorkflowResult,
): EmissionWorkspaceScenario["summary"] {
  const readyModules = modules.filter((module) => module.status === "ready").length;
  const attentionModules = modules.filter((module) => module.status === "attention").length;
  const blockedModules = modules.filter((module) => module.status === "blocked").length;

  const blockers = uniqueStrings([
    ...(missingProviders.length > 0
      ? [`Auto-cadastro sem provedores obrigatorios: ${missingProviders.join(", ")}.`]
      : []),
    ...onboardingBlockingReasons.map(renderOnboardingBlockingReason),
    ...(teamSummary.suspendedUsers > 0
      ? [`Equipe com ${teamSummary.suspendedUsers} usuario(s) suspenso(s).`]
      : []),
    ...(teamSummary.expiredCompetencies > 0
      ? [`Equipe com ${teamSummary.expiredCompetencies} competencia(s) vencida(s).`]
      : []),
    ...dryRunBlockers,
    ...workflowResult.blockers,
  ]);

  const warnings = uniqueStrings([
    ...(teamSummary.expiringCompetencies > 0
      ? [`Equipe com ${teamSummary.expiringCompetencies} competencia(s) expirando.`]
      : []),
    ...dryRunWarnings,
    ...workflowResult.warnings,
  ]);

  return {
    status: resolveWorkspaceStatus(blockedModules, attentionModules),
    headline: definition.headline,
    readyToEmit:
      modules.every((module) => module.status === "ready") && workflowResult.stage === "approved",
    recommendedAction: definition.recommendedAction,
    readyModules,
    attentionModules,
    blockedModules,
    blockers,
    warnings,
  };
}

function resolveWorkspaceStatus(
  blockedModules: number,
  attentionModules: number,
): EmissionWorkspaceStatus {
  if (blockedModules > 0) {
    return "blocked";
  }

  if (attentionModules > 0) {
    return "attention";
  }

  return "ready";
}

function renderOnboardingBlockingReason(reason: OnboardingBlockingReason): string {
  switch (reason) {
    case "organization_profile_pending":
      return "Onboarding com perfil organizacional pendente.";
    case "primary_signatory_pending":
      return "Onboarding sem signatario principal liberado.";
    case "certificate_numbering_pending":
      return "Onboarding sem numeracao de certificado configurada.";
    case "scope_review_pending":
      return "Onboarding sem revisao de escopo concluida.";
    case "public_qr_pending":
      return "Onboarding sem QR publico configurado.";
    default:
      return "Onboarding com pendencia nao identificada.";
  }
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}

function isEmissionWorkspaceScenarioId(
  value: string | undefined,
): value is EmissionWorkspaceScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
