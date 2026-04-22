import type {
  EmissionDryRunCatalog,
  OnboardingCatalog,
  SelfSignupCatalog,
} from "@afere/contracts";

import { buildSelfSignupCatalogView } from "../auth/self-signup-scenarios";
import { buildEmissionDryRunCatalogView } from "../emission/emission-dry-run-scenarios";
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
  const emissionView = input.emissionCatalog
    ? buildEmissionDryRunCatalogView(input.emissionCatalog)
    : null;

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

  for (const card of cards) {
    if (card.statusTone === "ok") {
      readyCount += 1;
    } else if (card.statusTone === "warn") {
      blockedCount += 1;
    }
  }

  const allSourcesAvailable = Boolean(selfSignupView && onboardingView && emissionView);

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
