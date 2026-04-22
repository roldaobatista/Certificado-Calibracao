import type { PortalCertificateCatalog, PortalCertificateScenario } from "@afere/contracts";

export interface PortalCertificateScenarioViewModel extends PortalCertificateScenario {
  selectedCertificate: PortalCertificateScenario["items"][number];
  summaryLabel: string;
}

export interface PortalCertificateCatalogViewModel {
  selectedScenario: PortalCertificateScenarioViewModel;
  scenarios: PortalCertificateScenarioViewModel[];
}

export function buildPortalCertificateCatalogView(
  catalog: PortalCertificateCatalog,
): PortalCertificateCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedCertificate =
      scenario.items.find((item) => item.certificateId === scenario.selectedCertificateId) ??
      scenario.items[0];

    if (!selectedCertificate) {
      throw new Error("missing_portal_certificate_items");
    }

    return {
      ...scenario,
      selectedCertificate,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.readyCount} certificado(s) pronto(s) para consulta`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCount} certificado(s) em reemissao rastreada`
            : `${scenario.summary.blockedCount} certificado(s) com viewer bloqueado`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_portal_certificate_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
