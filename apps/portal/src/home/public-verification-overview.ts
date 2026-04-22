import type { PublicCertificateCatalog } from "@afere/contracts";

import { buildPublicCertificateCatalogView } from "../public-certificate-scenarios";

export interface PublicVerificationOverviewCard {
  href: string;
  eyebrow: string;
  title: string;
  description: string;
  statusTone: "ok" | "warn" | "neutral";
  statusLabel: string;
  cta: string;
}

export interface PublicVerificationOverviewModel {
  sourceAvailable: boolean;
  authenticCount: number;
  reissuedCount: number;
  notFoundCount: number;
  heroStatusTone: "ok" | "warn";
  heroStatusLabel: string;
  heroStatusDescription: string;
  featuredScenarioLabel: string;
  cards: PublicVerificationOverviewCard[];
}

export function buildPublicVerificationOverviewModel(
  catalog: PublicCertificateCatalog | null,
): PublicVerificationOverviewModel {
  if (!catalog) {
    return {
      sourceAvailable: false,
      authenticCount: 0,
      reissuedCount: 0,
      notFoundCount: 0,
      heroStatusTone: "warn",
      heroStatusLabel: "Backend obrigatorio",
      heroStatusDescription:
        "O portal depende do endpoint canonico GET /portal/verify para montar o resumo publico com seguranca.",
      featuredScenarioLabel: "Sem carga canonica",
      cards: [
        unavailableCard({
          href: "/verify?scenario=authentic",
          eyebrow: "Autenticidade",
          title: "Certificado autentico",
          description: "Sem carga canonica, o portal nao assume o recorte minimo de autenticidade.",
        }),
        unavailableCard({
          href: "/verify?scenario=reissued",
          eyebrow: "Rastreabilidade",
          title: "Certificado reemitido",
          description: "Sem carga canonica, a home nao exibe relacionamento de revisao publica.",
        }),
        unavailableCard({
          href: "/verify?scenario=not-found",
          eyebrow: "Fail-closed",
          title: "Nao localizado",
          description: "Sem backend valido, o portal permanece em resposta segura e minimizada.",
        }),
      ],
    };
  }

  const view = buildPublicCertificateCatalogView(catalog);
  let authenticCount = 0;
  let reissuedCount = 0;
  let notFoundCount = 0;

  const cards = view.scenarios.map((scenario) => {
    const statusTone =
      scenario.page.status === "authentic"
        ? "ok"
        : scenario.page.status === "reissued"
          ? "neutral"
          : "warn";
    const statusLabel =
      scenario.page.status === "authentic"
        ? "Certificado valido"
        : scenario.page.status === "reissued"
          ? "Reemissao rastreada"
          : "Sem dados publicos";

    if (scenario.page.status === "authentic") {
      authenticCount += 1;
    } else if (scenario.page.status === "reissued") {
      reissuedCount += 1;
    } else {
      notFoundCount += 1;
    }

    return {
      href: `/verify?scenario=${scenario.id}`,
      eyebrow: scenario.id === view.selectedScenario.id ? "Ativo" : "Disponivel",
      title: scenario.label,
      description: scenario.description,
      statusTone,
      statusLabel,
      cta: "Verificar",
    } satisfies PublicVerificationOverviewCard;
  });

  return {
    sourceAvailable: true,
    authenticCount,
    reissuedCount,
    notFoundCount,
    heroStatusTone: "ok",
    heroStatusLabel: "Catalogo publico carregado",
    heroStatusDescription: `${authenticCount} cenario(s) autentico(s), ${reissuedCount} reemitido(s) e ${notFoundCount} resposta(s) fail-closed no catalogo publico.`,
    featuredScenarioLabel: view.selectedScenario.label,
    cards,
  };
}

function unavailableCard(input: {
  href: string;
  eyebrow: string;
  title: string;
  description: string;
}): PublicVerificationOverviewCard {
  return {
    ...input,
    statusTone: "warn",
    statusLabel: "Sem carga canonica",
    cta: "Verificar",
  };
}
