import {
  emissionWorkspaceCatalogSchema,
  type EmissionWorkspaceCatalog,
  type EmissionWorkspaceScenario as ContractEmissionWorkspaceScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildUserDirectory } from "../../domain/auth/user-directory.js";
import { evaluateOnboardingReadiness } from "../../domain/onboarding/onboarding-readiness.js";
import {
  listEmissionWorkspaceScenarios,
  resolveEmissionWorkspaceScenario,
  type EmissionWorkspaceScenarioDefinitionView,
} from "../../domain/emission/emission-workspace-scenarios.js";
import { requireWorkspaceAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerEmissionWorkspaceRoutes(
  app: FastifyInstance,
  persistence: CorePersistence,
) {
  app.get("/emission/workspace", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireWorkspaceAccess(request, reply, persistence);
      if (!context) {
        return reply;
      }

      const [users, onboarding] = await Promise.all([
        persistence.listUsersByOrganization(context.user.organizationId),
        persistence.getOnboardingByOrganization(context.user.organizationId),
      ]);

      if (!onboarding) {
        return reply.code(404).send({ error: "onboarding_not_found" });
      }

      const directory = buildUserDirectory({
        organizationName: context.user.organizationName,
        nowUtc: new Date().toISOString(),
        users: users.map((user) => ({
          userId: user.userId,
          displayName: user.displayName,
          email: user.email,
          roles: user.roles,
          status: user.status,
          teamName: user.teamName,
          lastLoginUtc: user.lastLoginUtc,
          deviceCount: user.deviceCount,
          competencies: user.competencies.map((competency) => ({
            instrumentType: competency.instrumentType,
            roleLabel: competency.roleLabel,
            validUntilUtc: competency.validUntilUtc,
          })),
        })),
      });

      const onboardingResult = evaluateOnboardingReadiness({
        startedAtUtc: onboarding.startedAtUtc,
        completedAtUtc: onboarding.completedAtUtc ?? new Date().toISOString(),
        prerequisites: {
          organizationProfileCompleted: onboarding.organizationProfileCompleted,
          primarySignatoryReady: onboarding.primarySignatoryReady,
          certificateNumberingConfigured: onboarding.certificateNumberingConfigured,
          scopeReviewCompleted: onboarding.scopeReviewCompleted,
          publicQrConfigured: onboarding.publicQrConfigured,
        },
      });

      const privilegedMfaMissing =
        (context.user.roles.includes("admin") || context.user.roles.includes("signatory")) &&
        !context.user.mfaEnrolled;
      const signatoriesReady = users.some(
        (user) =>
          user.status === "active" &&
          user.roles.includes("signatory") &&
          user.mfaEnrolled &&
          user.competencies.some((competency) => competency.status === "authorized"),
      );
      const reviewersReady = users.some(
        (user) =>
          user.status === "active" &&
          (user.roles.includes("technical_reviewer") || user.roles.includes("quality_manager")) &&
          user.competencies.every((competency) => competency.status !== "expired"),
      );

      const authStatus = privilegedMfaMissing ? "blocked" : "ready";
      const onboardingStatus = onboardingResult.canEmitFirstCertificate ? "ready" : "blocked";
      const teamStatus =
        directory.summary.suspendedUsers > 0 || directory.summary.expiredCompetencies > 0
          ? "blocked"
          : directory.summary.expiringCompetencies > 0
            ? "attention"
            : "ready";
      const dryRunStatus =
        authStatus === "ready" && onboardingStatus === "ready" && teamStatus !== "blocked"
          ? "ready"
          : "blocked";
      const workflowStatus = signatoriesReady && reviewersReady && !privilegedMfaMissing ? "ready" : "blocked";
      const statuses = [authStatus, onboardingStatus, teamStatus, dryRunStatus, workflowStatus] as const;
      const blockedModules = statuses.filter((status) => status === "blocked").length;
      const attentionModules = statuses.filter((status) => status === "attention").length;
      const readyModules = statuses.filter((status) => status === "ready").length;
      const selectedScenarioId =
        blockedModules > 0 ? "release-blocked" : attentionModules > 0 ? "team-attention" : "baseline-ready";

      const payload: EmissionWorkspaceCatalog = emissionWorkspaceCatalogSchema.parse({
        selectedScenarioId,
        scenarios: [
          {
            id: selectedScenarioId,
            label: "Workspace persistido do tenant",
            description: "Resumo operacional derivado de sessao, equipe e onboarding reais.",
            summary: {
              status:
                blockedModules > 0 ? "blocked" : attentionModules > 0 ? "attention" : "ready",
              headline:
                blockedModules > 0
                  ? "Workspace bloqueado por sessao, onboarding ou equipe"
                  : attentionModules > 0
                    ? "Workspace exige acao preventiva antes da emissao"
                    : "Workspace pronto para destravar V2 com dados persistidos",
              readyToEmit: blockedModules === 0 && attentionModules === 0,
              recommendedAction:
                blockedModules > 0
                  ? "Fechar os bloqueios persistidos antes de abrir o fluxo operacional central."
                  : attentionModules > 0
                    ? "Eliminar riscos preventivos do time antes da proxima emissao."
                    : "Seguir para os cadastros principais sobre a base persistida de V1.",
              readyModules,
              attentionModules,
              blockedModules,
              blockers: [
                ...(privilegedMfaMissing ? ["Sessao privilegiada sem MFA ativa."] : []),
                ...onboardingResult.blockingReasons.map((reason) => `Onboarding: ${reason}.`),
                ...(directory.summary.suspendedUsers > 0
                  ? [`Equipe com ${directory.summary.suspendedUsers} usuario(s) suspenso(s).`]
                  : []),
                ...(directory.summary.expiredCompetencies > 0
                  ? [`Equipe com ${directory.summary.expiredCompetencies} competencia(s) vencida(s).`]
                  : []),
                ...(!signatoriesReady ? ["Nao ha signatario ativo com competencia autorizada."] : []),
                ...(!reviewersReady ? ["Nao ha revisor tecnico ativo elegivel para o gate."] : []),
              ],
              warnings:
                directory.summary.expiringCompetencies > 0
                  ? [`Equipe com ${directory.summary.expiringCompetencies} competencia(s) expirando.`]
                  : [],
            },
            modules: [
              {
                key: "auth",
                title: "Auth e sessao",
                status: authStatus,
                detail: privilegedMfaMissing
                  ? "Usuario privilegiado autenticado sem MFA concluida."
                  : `Sessao ativa para ${context.user.displayName} em ${context.user.organizationName}.`,
                href: "/auth/login",
              },
              {
                key: "onboarding",
                title: "Onboarding do tenant",
                status: onboardingStatus,
                detail: onboardingResult.canEmitFirstCertificate
                  ? "Prerequisitos persistidos liberam a primeira emissao."
                  : `${onboardingResult.blockingReasons.length} prerequisito(s) persistido(s) ainda bloqueiam a organizacao.`,
                href: "/onboarding",
              },
              {
                key: "team",
                title: "Equipe e competencias",
                status: teamStatus,
                detail:
                  teamStatus === "blocked"
                    ? "Ha usuarios suspensos ou competencias vencidas na equipe persistida."
                    : teamStatus === "attention"
                      ? "Competencias estao proximas do vencimento."
                      : "Equipe ativa e competencias autorizadas no banco.",
                href: "/auth/users",
              },
              {
                key: "dry_run",
                title: "Prontidao estrutural",
                status: dryRunStatus,
                detail:
                  dryRunStatus === "ready"
                    ? "Sessao, onboarding e equipe sustentam a base de V1 sem payload estatico."
                    : "A fundacao ainda nao sustenta o gate estrutural sem bloqueios reais.",
                href: "/emission/dry-run",
              },
              {
                key: "workflow",
                title: "Revisao e assinatura",
                status: workflowStatus,
                detail:
                  workflowStatus === "ready"
                    ? "Existe revisor tecnico e signatario elegiveis no tenant."
                    : "O tenant ainda nao possui combinacao elegivel para revisao e assinatura.",
                href: "/emission/review-signature",
              },
            ],
            references: {
              selfSignupScenarioId: "admin-guided",
              onboardingScenarioId: onboardingResult.canEmitFirstCertificate ? "ready" : "blocked",
              userDirectoryScenarioId:
                teamStatus === "blocked"
                  ? "suspended-access"
                  : teamStatus === "attention"
                    ? "expiring-competencies"
                    : "operational-team",
              dryRunScenarioId: dryRunStatus === "ready" ? "type-b-ready" : "type-c-blocked",
              reviewSignatureScenarioId:
                workflowStatus === "ready" ? "segregated-ready" : "signatory-mfa-blocked",
            },
            nextActions:
              blockedModules > 0
                ? [
                    "Concluir o onboarding persistido da organizacao.",
                    "Regularizar MFA, revisor e signatario do tenant.",
                    "Remover competencias vencidas antes de seguir para V2.",
                  ]
                : attentionModules > 0
                  ? [
                      "Renovar competencias proximas do vencimento.",
                      "Revalidar a equipe antes da proxima janela de emissao.",
                      "Abrir V2 sem perder a consistencia da fundacao.",
                    ]
                  : [
                      "Seguir para V2 com cadastros reais sobre a base persistida.",
                      "Manter onboarding e equipe sincronizados com o tenant.",
                      "Preservar o workspace sem voltar a payloads estaticos no nucleo.",
                    ],
          },
        ],
      });

      return reply.code(200).send(payload);
    }

    const selectedScenario = resolveEmissionWorkspaceScenario(query.data.scenario);
    const payload: EmissionWorkspaceCatalog = emissionWorkspaceCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listEmissionWorkspaceScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(
  scenario: EmissionWorkspaceScenarioDefinitionView,
): ContractEmissionWorkspaceScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    summary: scenario.summary,
    modules: scenario.modules,
    references: scenario.references,
    nextActions: scenario.nextActions,
  };
}
