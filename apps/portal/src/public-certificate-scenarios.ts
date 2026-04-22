import type { PublicCertificateQrVerificationResult } from "@afere/contracts";

import { buildPublicCertificatePageModel } from "./public-certificate-page";

const SCENARIOS = {
  authentic: {
    label: "Certificado autentico",
    description: "Mostra o recorte minimo de metadados para um certificado valido e nao reemitido.",
    result: {
      ok: true,
      status: "authentic",
      certificate: {
        certificateId: "cert-001",
        certificateNumber: "AFR-000123",
        issuedAtUtc: "2026-04-21T14:00:00Z",
        revision: "R0",
        instrumentDescription: "Balanca IPNA 300 kg",
        serialNumber: "SN-42",
        customerName: "Cliente Sigiloso",
        customerAddress: "Rua Interna, 123",
      },
    },
  },
  reissued: {
    label: "Certificado reemitido",
    description: "Explicita a reemissao preservando apenas os metadados publicos estritamente necessarios.",
    result: {
      ok: true,
      status: "reissued",
      certificate: {
        certificateId: "cert-002",
        certificateNumber: "AFR-000124",
        issuedAtUtc: "2026-04-20T09:00:00Z",
        revision: "R1",
        instrumentDescription: "Balanca IPNA 300 kg",
        serialNumber: "SN-99",
        reissuedAtUtc: "2026-04-21T16:00:00Z",
        replacementCertificateNumber: "AFR-000124-R1",
        actorId: "signer-1",
      },
    },
  },
  "not-found": {
    label: "Nao localizado",
    description: "Fluxo fail-closed quando o portal nao encontra evidencias suficientes para expor dados publicos.",
    result: {
      ok: false,
      status: "not_found",
      reason: "certificate_not_found",
    },
  },
} as const satisfies Record<string, {
  label: string;
  description: string;
  result: PublicCertificateQrVerificationResult;
}>;

export type PublicCertificateScenarioId = keyof typeof SCENARIOS;

export interface PublicCertificateScenario {
  id: PublicCertificateScenarioId;
  label: string;
  description: string;
  result: PublicCertificateQrVerificationResult;
  page: ReturnType<typeof buildPublicCertificatePageModel>;
}

const DEFAULT_SCENARIO: PublicCertificateScenarioId = "authentic";

export function resolvePublicCertificateScenario(scenarioId?: string): PublicCertificateScenario {
  const id = isPublicCertificateScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
    page: buildPublicCertificatePageModel(scenario.result),
  };
}

export function listPublicCertificateScenarios(): PublicCertificateScenario[] {
  return (Object.keys(SCENARIOS) as PublicCertificateScenarioId[]).map((scenarioId) =>
    resolvePublicCertificateScenario(scenarioId),
  );
}

function isPublicCertificateScenarioId(
  value: string | undefined,
): value is PublicCertificateScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
