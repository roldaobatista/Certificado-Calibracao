import type {
  EmissionDryRunCatalog,
  EmissionWorkspaceCatalog,
  OnboardingCatalog,
  ReviewSignatureCatalog,
  SelfSignupCatalog,
  SignatureQueueCatalog,
  UserDirectoryCatalog,
} from "@afere/contracts";

import { buildSelfSignupCatalogView } from "../auth/self-signup-scenarios";
import { buildUserDirectoryCatalogView } from "../auth/user-directory-scenarios";
import { buildEmissionDryRunCatalogView } from "../emission/emission-dry-run-scenarios";
import { buildEmissionWorkspaceCatalogView } from "../emission/emission-workspace-scenarios";
import { buildReviewSignatureCatalogView } from "../emission/review-signature-scenarios";
import { buildSignatureQueueCatalogView } from "../emission/signature-queue-scenarios";
import { buildOnboardingCatalogView } from "../onboarding/onboarding-scenarios";

export interface OperationsOverviewCard {
  href: string;
  eyebrow: string;
  title: string;
  description: string;
  statusTone: "ok" | "warn" | "neutral";
  statusLabel: string;
  cta: string;
}

export interface OperationsOverviewModel {
  readyCount: number;
  blockedCount: number;
  allSourcesAvailable: boolean;
  heroStatusTone: "ok" | "warn";
  heroStatusLabel: string;
  heroStatusDescription: string;
  cards: OperationsOverviewCard[];
}

export function buildOperationsOverviewModel(input: {
  selfSignupCatalog: SelfSignupCatalog | null;
  onboardingCatalog: OnboardingCatalog | null;
  emissionCatalog: EmissionDryRunCatalog | null;
  emissionWorkspaceCatalog: EmissionWorkspaceCatalog | null;
  reviewSignatureCatalog: ReviewSignatureCatalog | null;
  signatureQueueCatalog: SignatureQueueCatalog | null;
  userDirectoryCatalog: UserDirectoryCatalog | null;
}): OperationsOverviewModel {
  const cards: OperationsOverviewCard[] = [];
  let readyCount = 0;
  let blockedCount = 0;

  const selfSignupView = input.selfSignupCatalog
    ? buildSelfSignupCatalogView(input.selfSignupCatalog)
    : null;
  const onboardingView = input.onboardingCatalog
    ? buildOnboardingCatalogView(input.onboardingCatalog)
    : null;
  const emissionWorkspaceView = input.emissionWorkspaceCatalog
    ? buildEmissionWorkspaceCatalogView(input.emissionWorkspaceCatalog)
    : null;
  const emissionView = input.emissionCatalog
    ? buildEmissionDryRunCatalogView(input.emissionCatalog)
    : null;
  const reviewSignatureView = input.reviewSignatureCatalog
    ? buildReviewSignatureCatalogView(input.reviewSignatureCatalog)
    : null;
  const signatureQueueView = input.signatureQueueCatalog
    ? buildSignatureQueueCatalogView(input.signatureQueueCatalog)
    : null;
  const userDirectoryView = input.userDirectoryCatalog
    ? buildUserDirectoryCatalogView(input.userDirectoryCatalog)
    : null;

  cards.push(
    emissionWorkspaceView
      ? {
          href: `/emission/workspace?scenario=${emissionWorkspaceView.selectedScenario.id}`,
          eyebrow: "Workspace",
          title: emissionWorkspaceView.selectedScenario.label,
          description: emissionWorkspaceView.selectedScenario.summaryLabel,
          statusTone:
            emissionWorkspaceView.selectedScenario.summary.status === "ready" ? "ok" : "warn",
          statusLabel:
            emissionWorkspaceView.selectedScenario.summary.status === "ready"
              ? "Workspace pronto"
              : emissionWorkspaceView.selectedScenario.summary.status === "attention"
                ? "Workspace com atencao"
                : "Workspace bloqueado",
          cta: "Abrir workspace",
        }
      : unavailableCard({
          href: "/emission/workspace",
          eyebrow: "Workspace",
          title: "Prontidao consolidada da emissao",
          description: "Leitura canonica indisponivel no momento.",
          cta: "Abrir workspace",
        }),
  );

  cards.push(
    selfSignupView
      ? {
          href: `/auth/self-signup?scenario=${selfSignupView.selectedScenario.id}`,
          eyebrow: "Auth",
          title: selfSignupView.selectedScenario.label,
          description: `${selfSignupView.selectedScenario.viewModel.visibleMethods.length} metodos visiveis e ${selfSignupView.selectedScenario.viewModel.missingMethods.length} lacunas de habilitacao.`,
          statusTone: selfSignupView.selectedScenario.viewModel.status === "ready" ? "ok" : "warn",
          statusLabel:
            selfSignupView.selectedScenario.viewModel.status === "ready"
              ? "Fluxo liberado"
              : "Fluxo bloqueado",
          cta: "Abrir auth",
        }
      : unavailableCard({
          href: "/auth/self-signup",
          eyebrow: "Auth",
          title: "Checklist de auto-cadastro",
          description: "Leitura canonica indisponivel no momento.",
          cta: "Abrir auth",
        }),
  );

  cards.push(
    onboardingView
      ? {
          href: `/onboarding?scenario=${onboardingView.selectedScenario.id}`,
          eyebrow: "Onboarding",
          title: onboardingView.selectedScenario.label,
          description:
            onboardingView.selectedScenario.summary.blockingSteps.length === 0
              ? onboardingView.selectedScenario.summary.timeTargetLabel
              : `${onboardingView.selectedScenario.summary.blockingSteps.length} passos bloqueantes na primeira emissao.`,
          statusTone: onboardingView.selectedScenario.summary.status === "ready" ? "ok" : "warn",
          statusLabel:
            onboardingView.selectedScenario.summary.status === "ready"
              ? "Emissao liberada"
              : "Emissao bloqueada",
          cta: "Abrir onboarding",
        }
      : unavailableCard({
          href: "/onboarding",
          eyebrow: "Onboarding",
          title: "Prontidao da primeira emissao",
          description: "Leitura canonica indisponivel no momento.",
          cta: "Abrir onboarding",
        }),
  );

  cards.push(
    emissionView
      ? {
          href: `/emission/dry-run?scenario=${emissionView.selectedScenario.id}`,
          eyebrow: "Emissao",
          title: emissionView.selectedScenario.label,
          description: `${emissionView.selectedScenario.summary.passedChecks} checks verdes e ${emissionView.selectedScenario.summary.failedChecks} falhos.`,
          statusTone: emissionView.selectedScenario.summary.status === "ready" ? "ok" : "warn",
          statusLabel:
            emissionView.selectedScenario.summary.status === "ready"
              ? "Emissao pronta"
              : "Emissao bloqueada",
          cta: "Abrir dry-run",
        }
      : unavailableCard({
          href: "/emission/dry-run",
          eyebrow: "Emissao",
          title: "Dry-run consolidado",
          description: "Leitura canonica indisponivel no momento.",
          cta: "Abrir dry-run",
        }),
  );

  cards.push(
    reviewSignatureView
      ? {
          href: `/emission/review-signature?scenario=${reviewSignatureView.selectedScenario.id}`,
          eyebrow: "Revisao",
          title: reviewSignatureView.selectedScenario.label,
          description: `${reviewSignatureView.selectedScenario.summary.reviewStatusLabel} · ${reviewSignatureView.selectedScenario.summary.signatureStatusLabel}.`,
          statusTone: reviewSignatureView.selectedScenario.summary.status === "ready" ? "ok" : "warn",
          statusLabel:
            reviewSignatureView.selectedScenario.summary.status === "ready"
              ? "Workflow liberado"
              : "Workflow bloqueado",
          cta: "Abrir workflow",
        }
      : unavailableCard({
          href: "/emission/review-signature",
          eyebrow: "Revisao",
          title: "Workflow de revisao e assinatura",
          description: "Leitura canonica indisponivel no momento.",
          cta: "Abrir workflow",
        }),
  );

  cards.push(
    signatureQueueView
      ? {
          href: `/emission/signature-queue?scenario=${signatureQueueView.selectedScenario.id}&item=${signatureQueueView.selectedScenario.selectedItem.itemId}`,
          eyebrow: "Assinatura",
          title: signatureQueueView.selectedScenario.label,
          description: `${signatureQueueView.selectedScenario.summary.pendingCount} pendente(s) e ${signatureQueueView.selectedScenario.summary.batchReadyCount} pronto(s) para lote.`,
          statusTone: statusToneForQueue(signatureQueueView.selectedScenario.summary.status),
          statusLabel: statusLabelForQueue(signatureQueueView.selectedScenario.summary.status),
          cta: "Abrir fila",
        }
      : unavailableCard({
          href: "/emission/signature-queue",
          eyebrow: "Assinatura",
          title: "Fila de assinatura",
          description: "Leitura canonica indisponivel no momento.",
          cta: "Abrir fila",
        }),
  );

  cards.push(
    userDirectoryView
      ? {
          href: `/auth/users?scenario=${userDirectoryView.selectedScenario.id}`,
          eyebrow: "Equipe",
          title: userDirectoryView.selectedScenario.label,
          description: userDirectoryView.selectedScenario.summaryLabel,
          statusTone: userDirectoryView.selectedScenario.summary.status === "ready" ? "ok" : "warn",
          statusLabel:
            userDirectoryView.selectedScenario.summary.status === "ready"
              ? "Equipe saudavel"
              : "Equipe com atencao",
          cta: "Abrir usuarios",
        }
      : unavailableCard({
          href: "/auth/users",
          eyebrow: "Equipe",
          title: "Diretorio de usuarios",
          description: "Leitura canonica indisponivel no momento.",
          cta: "Abrir usuarios",
        }),
  );

  for (const card of cards) {
    if (card.statusTone === "ok") {
      readyCount += 1;
    } else if (card.statusTone === "warn") {
      blockedCount += 1;
    }
  }

  const allSourcesAvailable = Boolean(
    emissionWorkspaceView &&
      selfSignupView &&
      onboardingView &&
      emissionView &&
      reviewSignatureView &&
      signatureQueueView &&
      userDirectoryView,
  );

  return {
    readyCount,
    blockedCount,
    allSourcesAvailable,
    heroStatusTone: allSourcesAvailable && blockedCount === 0 ? "ok" : "warn",
    heroStatusLabel:
      allSourcesAvailable && blockedCount === 0
        ? "Operacao canonicamente pronta"
        : "Revisao operacional necessaria",
    heroStatusDescription: allSourcesAvailable
      ? `${readyCount} leituras prontas e ${blockedCount} fluxo(s) com atencao.`
      : "Uma ou mais leituras canonicas do backend estao indisponiveis.",
    cards,
  };
}

function statusToneForQueue(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabelForQueue(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Fila pronta";
    case "attention":
      return "Fila com atencao";
    case "blocked":
      return "Fila bloqueada";
    default:
      return status;
  }
}

function unavailableCard(input: {
  href: string;
  eyebrow: string;
  title: string;
  description: string;
  cta: string;
}): OperationsOverviewCard {
  return {
    ...input,
    statusTone: "warn",
    statusLabel: "Sem carga canonica",
  };
}
