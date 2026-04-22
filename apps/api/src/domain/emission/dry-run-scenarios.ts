import type {
  EmissionDryRunProfile,
  EmissionDryRunResult,
  EmissionDryRunScenarioId as ContractEmissionDryRunScenarioId,
} from "@afere/contracts";

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
        displayName: "Lab. Acme",
      },
      equipment: {
        customerId: "customer-001",
        customerName: "Industria Horizonte",
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
        tagCode: "BAL-007",
        manufacturer: "Toledo",
        model: "Prix 3",
      },
      standard: {
        source: "RBC",
        calibrationDate: "2026-04-22",
        hasValidCertificate: true,
        certificateValidUntil: "2026-12-31",
        certificateReference: "RBC CAL-1234",
        standardSetLabel: "PESO-001 / PESO-002 / TH-003",
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
        displayName: "Carlos Signatario",
        authorizationLabel: "Signatario autorizado",
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
        technicalReviewerName: "Maria Revisora",
        deviceId: "web-station-01",
      },
      environment: {
        procedureRangeLabel: "Temp 18C-25C | Umid 30%-70%",
        temperatureC: 22.4,
        humidityPercent: 55,
        pressureHpa: 1013,
        withinProcedureRange: true,
      },
      decision: {
        requested: true,
        ruleLabel: "ILAC G8 sem banda de guarda",
        outcomeLabel: "Aprovado",
      },
      notes: ["Execucao sem observacoes de campo.", "Foto da placa e do display anexadas no fluxo."],
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
        displayName: "Laboratorio Alfa",
      },
      equipment: {
        customerId: "customer-002",
        customerName: "Hospital Central",
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
        tagCode: "BAL-021",
        manufacturer: "Shimadzu",
        model: "ATX",
      },
      standard: {
        source: "ILAC_MRA",
        calibrationDate: "2026-04-22",
        hasValidCertificate: true,
        certificateValidUntil: "2027-01-15",
        certificateReference: "ILAC CAL-2026-88",
        standardSetLabel: "PESO-F1 / TH-010",
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
        displayName: "Paula Signataria",
        authorizationLabel: "Signataria acreditada",
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
        technicalReviewerName: "Renata Qualidade",
        deviceId: "web-station-02",
      },
      environment: {
        procedureRangeLabel: "Temp 20C-24C | Umid 40%-60%",
        temperatureC: 21.2,
        humidityPercent: 48,
        pressureHpa: 1009,
        withinProcedureRange: true,
      },
      decision: {
        requested: false,
      },
      notes: ["Simbolo Cgcre/RBC suprimido por ponto fora do escopo acreditado."],
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
        displayName: "Metrologia Campo Sul",
      },
      equipment: {
        customerId: "customer-003",
        customerName: "Cliente sem cadastro completo",
        address: {
          line1: "Rua Sem CEP, 10",
          city: "Campo Grande",
          state: "MS",
          country: "BR",
        },
        instrumentType: "ipna_classe_iii",
        instrumentDescription: "Balanca plataforma 500 kg",
        serialNumber: "SN-C-500",
        tagCode: "BAL-404",
        manufacturer: "Marte",
        model: "Plataforma 500",
      },
      standard: {
        source: "RBC",
        calibrationDate: "2026-04-22",
        hasValidCertificate: false,
        certificateReference: "RBC CAL-0099",
        standardSetLabel: "PESO-009 / TH-404",
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
        displayName: "Andre Signatario",
        authorizationLabel: "Competencia vencida",
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
        technicalReviewerName: "Revisor Pendente",
        deviceId: "web-station-03",
      },
      environment: {
        procedureRangeLabel: "Temp 18C-25C | Umid 30%-70%",
        temperatureC: 28.1,
        humidityPercent: 73,
        pressureHpa: 1002,
        withinProcedureRange: false,
      },
      decision: {
        requested: true,
        ruleLabel: "ILAC G8 com banda de guarda",
        outcomeLabel: "Indeterminado",
      },
      notes: [
        "Endereco do equipamento incompleto no cadastro.",
        "Campo livre traz termos proibidos para o perfil Tipo C.",
      ],
      freeText:
        "Organizacao nao acreditada, mas o texto menciona RBC e Cgcre de forma inadequada para o perfil C.",
    },
  },
} as const satisfies Record<ContractEmissionDryRunScenarioId, EmissionDryRunScenarioDefinition>;

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
