import { createHash } from "node:crypto";

import type { EmissionDryRunProfile } from "@afere/contracts";

import {
  renderCertificateDocument,
  type RenderedCertificateDocument,
} from "./certificate-renderer.js";
import { runCertificateEmissionDryRun, type RunCertificateEmissionDryRunInput } from "./dry-run.js";
import {
  resolveEmissionDryRunScenario,
  type EmissionDryRunScenarioId,
} from "./dry-run-scenarios.js";

type SnapshotVariant = {
  id: string;
  label: string;
  description: string;
  profile: EmissionDryRunProfile;
  sourceScenarioId: EmissionDryRunScenarioId;
  mutate: (input: RunCertificateEmissionDryRunInput, index: number) => void;
};

export type CanonicalCertificateSnapshot = {
  id: string;
  label: string;
  description: string;
  profile: EmissionDryRunProfile;
  baselinePath: string;
  currentPath: string;
  requirementRefs: string[];
  renderer: string;
  pdfaStatus: string;
  sha256: string;
  bytes: Buffer;
  document: RenderedCertificateDocument;
};

export const SNAPSHOTS_PER_PROFILE = 10;
export const CANONICAL_CERTIFICATE_REQUIREMENT_REFS = ["REQ-EMISSION"];

export function listCanonicalCertificateSnapshots(): CanonicalCertificateSnapshot[] {
  return buildVariants().map((variant, index) => buildCanonicalSnapshot(variant, index));
}

function buildCanonicalSnapshot(variant: SnapshotVariant, index: number): CanonicalCertificateSnapshot {
  const source = resolveEmissionDryRunScenario(variant.sourceScenarioId);
  const clonedInput = structuredClone(source.input);
  variant.mutate(clonedInput, index);
  const result = runCertificateEmissionDryRun(clonedInput);
  const document = renderCertificateDocument({
    snapshotId: variant.id,
    label: variant.label,
    description: variant.description,
    input: clonedInput,
    result,
  });

  return {
    id: variant.id,
    label: variant.label,
    description: variant.description,
    profile: variant.profile,
    baselinePath: `compliance/validation-dossier/snapshots/baseline/${variant.id}.pdf`,
    currentPath: `compliance/validation-dossier/snapshots/current/${variant.id}.pdf`,
    requirementRefs: [...CANONICAL_CERTIFICATE_REQUIREMENT_REFS],
    renderer: document.renderer,
    pdfaStatus: document.pdfaStatus,
    sha256: createHash("sha256").update(document.bytes).digest("hex"),
    bytes: document.bytes,
    document,
  };
}

function buildVariants(): SnapshotVariant[] {
  return [...buildProfileAVariants(), ...buildProfileBVariants(), ...buildProfileCVariants()];
}

function buildProfileAVariants(): SnapshotVariant[] {
  const instruments = [
    "Balanca analitica 32 kg",
    "Balanca comparadora 21 kg",
    "Balanca semi-analitica 8 kg",
    "Balanca precisao 15 kg",
    "Balanca laboratoral 12 kg",
    "Balanca farmaceutica 6 kg",
    "Balanca micro 3 kg",
    "Balanca classe II 10 kg",
    "Balanca bancada 20 kg",
    "Balanca pesquisa 5 kg",
  ];
  const cities = ["Goiania", "Cuiaba", "Brasilia", "Campo Grande", "Uberlandia"];
  const sources: Array<RunCertificateEmissionDryRunInput["standard"]["source"]> = [
    "RBC",
    "ILAC_MRA",
    "INM",
    "RBC",
    "INM",
    "ILAC_MRA",
    "RBC",
    "INM",
    "ILAC_MRA",
    "RBC",
  ];
  const scopeFlags = [true, false, true, false, true, false, true, true, false, true];

  return Array.from({ length: SNAPSHOTS_PER_PROFILE }, (_value, index) => ({
    id: `profile-a-${String(index + 1).padStart(2, "0")}`,
    label: `Tipo A canonico ${String(index + 1).padStart(2, "0")}`,
    description: "Certificado canonico acreditado com variacoes controladas de escopo e rastreabilidade.",
    profile: "A",
    sourceScenarioId: "type-a-suppressed",
    mutate(input) {
      const withinScope = scopeFlags[index] ?? true;
      const organizationId = `org-a-${String(index + 1).padStart(2, "0")}`;
      input.organization.organizationId = organizationId;
      input.organization.displayName = `Laboratorio Alfa ${String(index + 1).padStart(2, "0")}`;
      input.equipment.customerId = `customer-a-${String(index + 1).padStart(2, "0")}`;
      input.equipment.customerName = `Cliente A ${String(index + 1).padStart(2, "0")}`;
      input.equipment.instrumentDescription = instruments[index] ?? input.equipment.instrumentDescription;
      input.equipment.serialNumber = `A-SN-${String(index + 1).padStart(3, "0")}`;
      input.equipment.tagCode = `A-TAG-${String(index + 1).padStart(3, "0")}`;
      input.equipment.address = {
        line1: `Avenida Metrologia ${100 + index}`,
        city: cities[index % cities.length] ?? "Goiania",
        state: "GO",
        postalCode: `7400${index}-000`,
        country: "BR",
      };
      input.standard.source = sources[index] ?? "RBC";
      input.standard.certificateReference = `CAL-A-${String(index + 1).padStart(4, "0")}`;
      input.standard.certificateValidUntil = `2027-0${(index % 9) + 1}-15`;
      input.standard.standardSetLabel = `PADRAO-A-${String(index + 1).padStart(2, "0")}`;
      input.standard.measurementValue = 8 + index;
      input.measurement.resultValue = Number((8 + index + 0.003).toFixed(3));
      input.measurement.expandedUncertaintyValue = withinScope ? 0.08 : 0.09;
      input.certificate.publicVerificationToken = `token-a-${String(index + 1).padStart(3, "0")}`;
      input.certificate.issuedNumbers = [
        {
          organizationId,
          certificateNumber: `CALA-${String(200 + index).padStart(6, "0")}`,
        },
      ];
      input.audit.technicalReviewerName = `Revisora A ${String(index + 1).padStart(2, "0")}`;
      input.audit.deviceId = `device-a-${String(index + 1).padStart(2, "0")}`;
      input.notes = [
        withinScope
          ? "Escopo acreditado confirmado para o ponto selecionado."
          : "Ponto fora do escopo acreditado; simbolo suprimido de forma controlada.",
        `Snapshot canonico A-${String(index + 1).padStart(2, "0")}.`,
      ];
      input.accreditation = {
        accreditationActive: true,
        hasRegisteredScope: true,
        hasRegisteredCmc: true,
        withinAccreditedScope: withinScope,
        declaredCmc: withinScope ? 0.08 : 0.05,
      };
      input.freeText = withinScope
        ? "Certificado emitido sob rastreabilidade metrologica ao SI com cadeia valida."
        : "Certificado emitido sob rastreabilidade metrologica ao SI com supressao controlada de simbolo.";
    },
  }));
}

function buildProfileBVariants(): SnapshotVariant[] {
  const instruments = [
    "Balanca IPNA 300 kg",
    "Balanca plataforma 150 kg",
    "Balanca rodoviaria 1000 kg",
    "Transmissor de pressao 10 bar",
    "Indicador peso 60 kg",
    "Balanca comercial 30 kg",
    "Balanca industrial 600 kg",
    "Balanca pallet 500 kg",
    "Balanca bancada 50 kg",
    "Balanca recebimento 200 kg",
  ];
  const cities = ["Cuiaba", "Rondonopolis", "Sinop", "Varzea Grande"];
  const sources: Array<RunCertificateEmissionDryRunInput["standard"]["source"]> = [
    "RBC",
    "INM",
    "RBC",
    "INM",
    "RBC",
    "INM",
    "RBC",
    "INM",
    "RBC",
    "INM",
  ];

  return Array.from({ length: SNAPSHOTS_PER_PROFILE }, (_value, index) => ({
    id: `profile-b-${String(index + 1).padStart(2, "0")}`,
    label: `Tipo B canonico ${String(index + 1).padStart(2, "0")}`,
    description: "Certificado canonico nao acreditado com rastreabilidade via RBC/INM.",
    profile: "B",
    sourceScenarioId: "type-b-ready",
    mutate(input) {
      const organizationId = `org-b-${String(index + 1).padStart(2, "0")}`;
      input.organization.organizationId = organizationId;
      input.organization.displayName = `Laboratorio B ${String(index + 1).padStart(2, "0")}`;
      input.equipment.customerId = `customer-b-${String(index + 1).padStart(2, "0")}`;
      input.equipment.customerName = `Cliente B ${String(index + 1).padStart(2, "0")}`;
      input.equipment.instrumentDescription = instruments[index] ?? input.equipment.instrumentDescription;
      input.equipment.serialNumber = `B-SN-${String(index + 1).padStart(3, "0")}`;
      input.equipment.tagCode = `B-TAG-${String(index + 1).padStart(3, "0")}`;
      input.equipment.address = {
        line1: `Rua Calibracao ${200 + index}`,
        city: cities[index % cities.length] ?? "Cuiaba",
        state: "MT",
        postalCode: `7800${index}-000`,
        country: "BR",
      };
      input.standard.source = sources[index] ?? "RBC";
      input.standard.certificateReference = `CAL-B-${String(index + 1).padStart(4, "0")}`;
      input.standard.certificateValidUntil = `2027-${String((index % 9) + 1).padStart(2, "0")}-28`;
      input.standard.standardSetLabel = `PADRAO-B-${String(index + 1).padStart(2, "0")}`;
      input.standard.measurementValue = 50 + index * 10;
      input.measurement.resultValue = Number((50 + index * 10 - 0.02).toFixed(2));
      input.measurement.expandedUncertaintyValue = Number((0.05 + index * 0.01).toFixed(2));
      input.certificate.publicVerificationToken = `token-b-${String(index + 1).padStart(3, "0")}`;
      input.certificate.issuedNumbers = [
        {
          organizationId,
          certificateNumber: `AFR-${String(300 + index).padStart(6, "0")}`,
        },
      ];
      input.audit.technicalReviewerName = `Revisor B ${String(index + 1).padStart(2, "0")}`;
      input.audit.deviceId = `device-b-${String(index + 1).padStart(2, "0")}`;
      input.decision = {
        requested: index % 2 === 0,
        ruleLabel: index % 2 === 0 ? "ILAC G8 sem banda de guarda" : undefined,
        outcomeLabel: index % 2 === 0 ? "Aprovado" : undefined,
      };
      input.notes = [
        "Emissao tipo B sem simbolo acreditado, com rastreabilidade declarada.",
        `Snapshot canonico B-${String(index + 1).padStart(2, "0")}.`,
      ];
      input.freeText = "Padroes calibrados com rastreabilidade metrologica valida para o perfil B.";
    },
  }));
}

function buildProfileCVariants(): SnapshotVariant[] {
  const failureModes = [
    "ready",
    "forbidden_text",
    "missing_address",
    "ready",
    "expired_competence",
    "invalid_source",
    "ready",
    "missing_qr",
    "expired_standard",
    "ready",
  ] as const;
  const instruments = [
    "Padrao massa 5 kg",
    "Termometro digital 100 C",
    "Cronometro 60 min",
    "Balanca classe III 60 kg",
    "Manometro 6 bar",
    "Paquimetro 300 mm",
    "Bureta automatica 50 mL",
    "Higrometro 100 RH",
    "Balanca bancada 20 kg",
    "Micrometro 25 mm",
  ];

  return Array.from({ length: SNAPSHOTS_PER_PROFILE }, (_value, index) => ({
    id: `profile-c-${String(index + 1).padStart(2, "0")}`,
    label: `Tipo C canonico ${String(index + 1).padStart(2, "0")}`,
    description: "Certificado canonico do perfil C com cenarios fail-closed e prontos controlados.",
    profile: "C",
    sourceScenarioId: "type-c-blocked",
    mutate(input) {
      const organizationId = `org-c-${String(index + 1).padStart(2, "0")}`;
      const failureMode = failureModes[index] ?? "ready";
      input.organization.organizationId = organizationId;
      input.organization.displayName = `Metrologia Campo Sul ${String(index + 1).padStart(2, "0")}`;
      input.equipment.customerId = `customer-c-${String(index + 1).padStart(2, "0")}`;
      input.equipment.customerName = `Cliente C ${String(index + 1).padStart(2, "0")}`;
      input.equipment.instrumentDescription = instruments[index] ?? input.equipment.instrumentDescription;
      input.equipment.serialNumber = `C-SN-${String(index + 1).padStart(3, "0")}`;
      input.equipment.tagCode = `C-TAG-${String(index + 1).padStart(3, "0")}`;
      input.equipment.address = {
        line1: `Rua Campo ${300 + index}`,
        city: "Campo Grande",
        state: "MS",
        postalCode: `7900${index}-000`,
        country: "BR",
      };
      input.standard.source = "INM";
      input.standard.hasValidCertificate = true;
      input.standard.certificateReference = `CAL-C-${String(index + 1).padStart(4, "0")}`;
      input.standard.certificateValidUntil = `2027-${String((index % 9) + 1).padStart(2, "0")}-20`;
      input.standard.standardSetLabel = `PADRAO-C-${String(index + 1).padStart(2, "0")}`;
      input.standard.measurementValue = 20 + index;
      input.standard.applicableRange = {
        minimum: 0,
        maximum: 500,
      };
      input.measurement.resultValue = Number((20 + index + 0.01).toFixed(2));
      input.measurement.expandedUncertaintyValue = 0.1;
      input.signatory.authorizationLabel = "Signatario interno";
      input.signatory.competencies = [
        {
          instrumentType: input.equipment.instrumentType,
          validFromUtc: "2026-01-01T00:00:00Z",
          validUntilUtc: "2026-12-31T23:59:59Z",
        },
      ];
      input.certificate.publicVerificationToken = `token-c-${String(index + 1).padStart(3, "0")}`;
      input.certificate.issuedNumbers = [
        {
          organizationId,
          certificateNumber: `LABC-${String(400 + index).padStart(6, "0")}`,
        },
      ];
      input.audit.technicalReviewerName = `Revisor C ${String(index + 1).padStart(2, "0")}`;
      input.audit.deviceId = `device-c-${String(index + 1).padStart(2, "0")}`;
      input.environment = {
        procedureRangeLabel: "Temp 18C-25C | Umid 30%-70%",
        temperatureC: 22,
        humidityPercent: 50,
        pressureHpa: 1008,
        withinProcedureRange: true,
      };
      input.decision = {
        requested: index % 3 === 0,
        ruleLabel: index % 3 === 0 ? "ILAC G8 sem banda de guarda" : undefined,
        outcomeLabel: index % 3 === 0 ? "Aprovado" : undefined,
      };
      input.notes = [`Snapshot canonico C-${String(index + 1).padStart(2, "0")}.`];
      input.freeText = "Certificado emitido com rastreabilidade metrologica interna conforme politica do perfil C.";

      switch (failureMode) {
        case "forbidden_text":
          input.freeText = "Certificado emitido conforme RBC e Cgcre de forma indevida para o perfil C.";
          input.notes.push("Falha controlada por texto proibido.");
          break;
        case "missing_address":
          input.equipment.address = {
            line1: "Rua Campo 999",
            city: "Campo Grande",
            state: "MS",
            country: "BR",
          };
          input.notes.push("Falha controlada por endereco incompleto.");
          break;
        case "expired_competence":
          input.signatory.competencies = [
            {
              instrumentType: input.equipment.instrumentType,
              validFromUtc: "2025-01-01T00:00:00Z",
              validUntilUtc: "2025-12-31T23:59:59Z",
            },
          ];
          input.notes.push("Falha controlada por competencia vencida.");
          break;
        case "invalid_source":
          input.standard.source = "RBC";
          input.notes.push("Falha controlada por fonte de padrao proibida para o perfil C.");
          break;
        case "missing_qr":
          input.certificate.publicVerificationToken = "";
          input.notes.push("Falha controlada por token publico ausente.");
          break;
        case "expired_standard":
          input.standard.hasValidCertificate = false;
          input.standard.certificateValidUntil = undefined;
          input.notes.push("Falha controlada por padrao vencido.");
          break;
        case "ready":
        default:
          input.notes.push("Emissao controlada pronta no perfil C sem termos proibidos.");
          break;
      }
    },
  }));
}
