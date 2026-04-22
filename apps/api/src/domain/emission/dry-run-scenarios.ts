import type { EmissionDryRunProfile, EmissionDryRunResult } from "@afere/contracts";

import {
  runCertificateEmissionDryRun,
  type RunCertificateEmissionDryRunInput,
} from "./dry-run.js";

type EmissionDryRunScenarioDefinition = {
  label: string;
  description: string;
  profile: EmissionDryRunProfile;
  input: RunCertificateEmissionDryRunInput;
};

const SCENARIOS = {
  "type-b-ready": {
    label: "Tipo B pronto",
    description: "Emissao controlada sem acreditacao, com padrao RBC valido e todos os gates V1 verdes.",
    profile: "B",
    input: {
      organization: {
        organizationId: "org-b",
        organizationCode: "AFR",
        profile: "B",
      },
      equipment: {
        customerId: "customer-001",
        address: {
          line1: "Rua da Calibracao, 100",
          city: "Cuiaba",
          state: "MT",
          postalCode: "78000-000",
          country: "BR",
        },
        instrumentType: "ipna_classe_iii",
        instrumentDescription: "Balanca IPNA 300 kg",
        serialNumber: "SN-300-01",
      },
      standard: {
        source: "RBC",
        calibrationDate: "2026-04-22",
        hasValidCertificate: true,
        certificateValidUntil: "2026-12-31",
        measurementValue: 150,
        applicableRange: {
          minimum: 0,
          maximum: 300,
        },
      },
      measurement: {
        resultValue: 149.98,
        expandedUncertaintyValue: 0.05,
        coverageFactor: 2,
        unit: "kg",
      },
      signatory: {
        signatoryId: "signatory-b",
        competencies: [
          {
            instrumentType: "ipna_classe_iii",
            validFromUtc: "2026-01-01T00:00:00Z",
            validUntilUtc: "2026-12-31T23:59:59Z",
          },
        ],
      },
      certificate: {
        certificateId: "cert-dry-b-001",
        revision: "R0",
        publicVerificationToken: "token-b-001",
        expectedQrHost: "portal.afere.local",
        issuedNumbers: [
          {
            organizationId: "org-b",
            certificateNumber: "AFR-000123",
          },
        ],
      },
      audit: {
        calibrationExecutedAtUtc: "2026-04-22T13:30:00Z",
        technicalReviewCompletedAtUtc: "2026-04-22T13:40:00Z",
        signedAtUtc: "2026-04-22T13:44:00Z",
        emittedAtUtc: "2026-04-22T13:45:00Z",
        technicalReviewerId: "reviewer-b",
        deviceId: "web-station-01",
      },
      freeText:
        "Resultados rastreaveis ao SI por meio dos padroes usados, calibrados por laboratorio RBC acreditado.",
    },
  },
  "type-a-suppressed": {
    label: "Tipo A com simbolo suprimido",
    description: "Emissao permitida em perfil acreditado, mas fora do escopo do ponto ensaiado; simbolo fica suprimido.",
    profile: "A",
    input: {
      organization: {
        organizationId: "org-a",
        organizationCode: "CALA",
        profile: "A",
      },
      equipment: {
        customerId: "customer-002",
        address: {
          line1: "Avenida da Metrologia, 55",
          city: "Goiania",
          state: "GO",
          postalCode: "74000-000",
          country: "BR",
        },
        instrumentType: "ipna_classe_ii",
        instrumentDescription: "Balanca analitica 32 kg",
        serialNumber: "SN-A-32",
      },
      standard: {
        source: "ILAC_MRA",
        calibrationDate: "2026-04-22",
        hasValidCertificate: true,
        certificateValidUntil: "2027-01-15",
        measurementValue: 12,
        applicableRange: {
          minimum: 0,
          maximum: 32,
        },
      },
      measurement: {
        resultValue: 12.003,
        expandedUncertaintyValue: 0.08,
        coverageFactor: 2,
        unit: "kg",
      },
      signatory: {
        signatoryId: "signatory-a",
        competencies: [
          {
            instrumentType: "ipna_classe_ii",
            validFromUtc: "2026-01-01T00:00:00Z",
            validUntilUtc: "2026-12-31T23:59:59Z",
          },
        ],
      },
      certificate: {
        certificateId: "cert-dry-a-001",
        revision: "R0",
        publicVerificationToken: "token-a-001",
        expectedQrHost: "portal.afere.local",
        issuedNumbers: [
          {
            organizationId: "org-a",
            certificateNumber: "CALA-000031",
          },
        ],
      },
      audit: {
        calibrationExecutedAtUtc: "2026-04-22T10:00:00Z",
        technicalReviewCompletedAtUtc: "2026-04-22T10:12:00Z",
        signedAtUtc: "2026-04-22T10:14:00Z",
        emittedAtUtc: "2026-04-22T10:15:00Z",
        technicalReviewerId: "reviewer-a",
        deviceId: "web-station-02",
      },
      accreditation: {
        accreditationActive: true,
        hasRegisteredScope: true,
        hasRegisteredCmc: true,
        withinAccreditedScope: false,
        declaredCmc: 0.05,
      },
      freeText: "Certificado emitido sob rastreabilidade metrologica ao SI.",
    },
  },
  "type-c-blocked": {
    label: "Tipo C bloqueado",
    description: "Mostra bloqueios reais quando o perfil, o cadastro, a competencia e o QR ainda nao atendem ao minimo de V1.",
    profile: "C",
    input: {
      organization: {
        organizationId: "org-c",
        organizationCode: "LABC",
        profile: "C",
      },
      equipment: {
        customerId: "customer-003",
        address: {
          line1: "Rua Sem CEP, 10",
          city: "Campo Grande",
          state: "MS",
          country: "BR",
        },
        instrumentType: "ipna_classe_iii",
        instrumentDescription: "Balanca plataforma 500 kg",
        serialNumber: "SN-C-500",
      },
      standard: {
        source: "RBC",
        calibrationDate: "2026-04-22",
        hasValidCertificate: false,
        measurementValue: 450,
        applicableRange: {
          minimum: 0,
          maximum: 300,
        },
      },
      measurement: {
        resultValue: 449.2,
        expandedUncertaintyValue: 0.12,
        coverageFactor: 2,
        unit: "kg",
      },
      signatory: {
        signatoryId: "signatory-c",
        competencies: [
          {
            instrumentType: "ipna_classe_iii",
            validFromUtc: "2025-01-01T00:00:00Z",
            validUntilUtc: "2025-12-31T23:59:59Z",
          },
        ],
      },
      certificate: {
        certificateId: "cert-dry-c-001",
        revision: "R0",
        publicVerificationToken: "",
        expectedQrHost: "portal.afere.local",
        issuedNumbers: [
          {
            organizationId: "org-c",
            certificateNumber: "LABC-000007",
          },
        ],
      },
      audit: {
        calibrationExecutedAtUtc: "2026-04-22T15:00:00Z",
        technicalReviewCompletedAtUtc: "2026-04-22T15:10:00Z",
        signedAtUtc: "2026-04-22T15:20:00Z",
        emittedAtUtc: "2026-04-22T15:21:00Z",
        technicalReviewerId: "reviewer-c",
        deviceId: "web-station-03",
      },
      freeText:
        "Organizacao nao acreditada, mas o texto menciona RBC e Cgcre de forma inadequada para o perfil C.",
    },
  },
} as const satisfies Record<string, EmissionDryRunScenarioDefinition>;

export type EmissionDryRunScenarioId = keyof typeof SCENARIOS;

export interface EmissionDryRunScenario {
  id: EmissionDryRunScenarioId;
  label: string;
  description: string;
  profile: EmissionDryRunProfile;
  input: RunCertificateEmissionDryRunInput;
  result: EmissionDryRunResult;
}

const DEFAULT_SCENARIO: EmissionDryRunScenarioId = "type-b-ready";

export function resolveEmissionDryRunScenario(scenarioId?: string): EmissionDryRunScenario {
  const id = isEmissionDryRunScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    profile: scenario.profile,
    input: scenario.input,
    result: runCertificateEmissionDryRun(scenario.input),
  };
}

export function resolveEmissionDryRunScenarioByProfile(
  profile: EmissionDryRunProfile,
): EmissionDryRunScenario {
  switch (profile) {
    case "A":
      return resolveEmissionDryRunScenario("type-a-suppressed");
    case "C":
      return resolveEmissionDryRunScenario("type-c-blocked");
    default:
      return resolveEmissionDryRunScenario("type-b-ready");
  }
}

export function listEmissionDryRunScenarios(): EmissionDryRunScenario[] {
  return (Object.keys(SCENARIOS) as EmissionDryRunScenarioId[]).map((scenarioId) =>
    resolveEmissionDryRunScenario(scenarioId),
  );
}

function isEmissionDryRunScenarioId(value: string | undefined): value is EmissionDryRunScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
