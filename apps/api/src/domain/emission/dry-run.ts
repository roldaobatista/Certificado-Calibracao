import {
  computeAuditHash,
  verifyCriticalEventAuditTrail,
  verifyTechnicalReviewSignatureAudit,
  type AuditChainEntry,
} from "@afere/audit-log";
import type { EmissionDryRunCheck, EmissionDryRunProfile, EmissionDryRunResult } from "@afere/contracts";
import { reserveSequentialCertificateNumber, type IssuedCertificateNumber } from "@afere/db";
import { buildCertificateMeasurementDeclaration } from "@afere/engine-uncertainty";
import {
  evaluateAccreditedScopeCmc,
  evaluateStandardEligibility,
  resolveRegulatoryPdfPolicy,
  validateRegulatoryFreeText,
} from "@afere/normative-rules";

import {
  evaluateSignatoryCompetence,
  type SignatoryCompetenceRecord,
} from "../competencies/signatory-competence.js";
import { verifyPublicCertificateQrAuthenticity } from "../certificates/public-qr.js";
import {
  validateEquipmentRegistration,
  type EquipmentRegistrationAddress,
} from "../equipment/equipment-registration.js";

export interface RunCertificateEmissionDryRunInput {
  organization: {
    organizationId: string;
    organizationCode: string;
    profile: EmissionDryRunProfile;
  };
  equipment: {
    customerId?: string;
    address?: EquipmentRegistrationAddress;
    instrumentType: string;
    instrumentDescription: string;
    serialNumber: string;
  };
  standard: {
    source: "INM" | "RBC" | "ILAC_MRA";
    calibrationDate: string;
    hasValidCertificate: boolean;
    certificateValidUntil?: string;
    measurementValue?: number;
    applicableRange?: {
      minimum: number;
      maximum: number;
    };
  };
  measurement: {
    resultValue: number;
    expandedUncertaintyValue: number;
    coverageFactor: number;
    unit: string;
  };
  signatory: {
    signatoryId: string;
    competencies: SignatoryCompetenceRecord[];
  };
  certificate: {
    certificateId: string;
    revision: string;
    publicVerificationToken: string;
    expectedQrHost: string;
    issuedNumbers: IssuedCertificateNumber[];
  };
  audit: {
    calibrationExecutedAtUtc: string;
    technicalReviewCompletedAtUtc: string;
    signedAtUtc: string;
    emittedAtUtc: string;
    technicalReviewerId: string;
    deviceId: string;
  };
  accreditation?: {
    accreditationActive?: boolean;
    hasRegisteredScope?: boolean;
    hasRegisteredCmc?: boolean;
    withinAccreditedScope?: boolean;
    declaredCmc?: number;
  };
  freeText?: string;
}

export function runCertificateEmissionDryRun(
  input: RunCertificateEmissionDryRunInput,
): EmissionDryRunResult {
  const policy = resolveRegulatoryPdfPolicy({
    profile: input.organization.profile,
    withinAccreditedScope: input.accreditation?.withinAccreditedScope,
  });
  const checks: EmissionDryRunCheck[] = [];
  const blockers = new Set<string>();
  const warnings = new Set<string>();

  let symbolPolicy = policy.symbolPolicy;

  for (const warning of policy.warnings) {
    warnings.add(renderProfileWarning(warning));
  }

  const profileIssues: string[] = [];
  if (!policy.allowedStandardSources.includes(input.standard.source)) {
    profileIssues.push(`fonte de padrao ${input.standard.source} fora da politica do perfil`);
  }

  for (const issue of validateRegulatoryFreeText(input.organization.profile, input.freeText ?? "")) {
    profileIssues.push(renderFreeTextIssue(issue));
  }

  if (input.organization.profile === "A") {
    const scopeEvaluation = evaluateAccreditedScopeCmc({
      profile: input.organization.profile,
      accreditationActive: input.accreditation?.accreditationActive,
      hasRegisteredScope: input.accreditation?.hasRegisteredScope,
      hasRegisteredCmc: input.accreditation?.hasRegisteredCmc,
      withinAccreditedScope: input.accreditation?.withinAccreditedScope,
      expandedUncertainty: input.measurement.expandedUncertaintyValue,
      declaredCmc: input.accreditation?.declaredCmc,
    });

    symbolPolicy = scopeEvaluation.symbolPolicy;

    for (const warning of scopeEvaluation.warnings) {
      warnings.add(renderProfileWarning(warning));
    }

    for (const blocker of scopeEvaluation.blockers) {
      profileIssues.push(renderProfileBlocker(blocker));
    }
  }

  if (profileIssues.length > 0) {
    blockers.add("Politica regulatoria do perfil");
  }
  checks.push({
    id: "profile_policy",
    title: "Politica regulatoria",
    status: profileIssues.length === 0 ? "passed" : "failed",
    detail:
      profileIssues.length === 0
        ? `Perfil ${input.organization.profile} compativel com ${policy.templateId} e politica de simbolo ${symbolPolicy}.`
        : `Bloqueios: ${profileIssues.join("; ")}.`,
  });

  const equipment = validateEquipmentRegistration({
    customerId: input.equipment.customerId,
    address: input.equipment.address,
  });
  if (!equipment.ok) {
    blockers.add("Cadastro do equipamento");
  }
  checks.push({
    id: "equipment_registration",
    title: "Cadastro do equipamento",
    status: equipment.ok ? "passed" : "failed",
    detail: equipment.ok
      ? "Cliente e endereco minimo do equipamento preenchidos."
      : `Campos ausentes: ${equipment.missingFields.join(", ")}.`,
  });

  const standard = evaluateStandardEligibility({
    calibrationDate: input.standard.calibrationDate,
    hasValidCertificate: input.standard.hasValidCertificate,
    certificateValidUntil: input.standard.certificateValidUntil,
    measurementValue: input.standard.measurementValue,
    applicableRange: input.standard.applicableRange,
  });
  if (!standard.eligible) {
    blockers.add("Elegibilidade do padrao");
  }
  checks.push({
    id: "standard_eligibility",
    title: "Elegibilidade do padrao",
    status: standard.eligible ? "passed" : "failed",
    detail: standard.eligible
      ? "Padrao valido, dentro da faixa aplicavel e aceito pelo perfil regulatorio."
      : `Bloqueios: ${standard.blockers.map(renderStandardEligibilityBlocker).join("; ")}.`,
  });

  const competence = evaluateSignatoryCompetence({
    signatoryId: input.signatory.signatoryId,
    instrumentType: input.equipment.instrumentType,
    signedAtUtc: input.audit.signedAtUtc,
    competencies: input.signatory.competencies,
  });
  if (!competence.ok) {
    blockers.add("Competencia do signatario");
  }
  checks.push({
    id: "signatory_competence",
    title: "Competencia do signatario",
    status: competence.ok ? "passed" : "failed",
    detail: competence.ok
      ? `Competencia vigente encontrada para ${input.equipment.instrumentType}.`
      : `Bloqueio: ${renderSignatoryReason(competence.reason)}.`,
  });

  const numbering = reserveSequentialCertificateNumber({
    organizationId: input.organization.organizationId,
    organizationCode: input.organization.organizationCode,
    issuedNumbers: input.certificate.issuedNumbers,
  });
  if (!numbering.ok) {
    blockers.add("Numeracao do certificado");
  }
  checks.push({
    id: "certificate_numbering",
    title: "Numeracao do certificado",
    status: numbering.ok ? "passed" : "failed",
    detail: numbering.ok
      ? `Proximo numero reservado em dry-run: ${numbering.certificateNumber}.`
      : `Bloqueios: ${numbering.errors.map(renderCertificateNumberingError).join("; ")}.`,
  });

  let declarationSummary: string | undefined;
  let measurementError: string | undefined;
  try {
    declarationSummary = buildCertificateMeasurementDeclaration({
      resultValue: input.measurement.resultValue,
      expandedUncertaintyValue: input.measurement.expandedUncertaintyValue,
      coverageFactor: input.measurement.coverageFactor,
      unit: input.measurement.unit,
    }).summary;
  } catch (error) {
    measurementError = error instanceof Error ? renderMeasurementError(error.message) : "erro_desconhecido";
    blockers.add("Declaracao metrologica");
  }
  checks.push({
    id: "measurement_declaration",
    title: "Declaracao metrologica",
    status: measurementError ? "failed" : "passed",
    detail: measurementError
      ? `Bloqueio: ${measurementError}.`
      : declarationSummary ?? "Declaracao tecnica nao disponivel.",
  });

  const auditEntries = buildAuditTrailPreview(input, numbering.certificateNumber);
  const criticalAudit = verifyCriticalEventAuditTrail(auditEntries);
  const reviewSignatureAudit = verifyTechnicalReviewSignatureAudit(auditEntries);
  const auditIssues = [
    ...criticalAudit.missingActions.map((action) => `acao critica ausente: ${action}`),
    ...reviewSignatureAudit.missingActions.map((action) => `acao de revisao/assinatura ausente: ${action}`),
    ...reviewSignatureAudit.invalidEntries.flatMap((entry) => [
      entry.missingFields.length > 0 ? `metadados ausentes em ${entry.action}: ${entry.missingFields.join(", ")}` : "",
      entry.invalidFields.length > 0 ? `metadados invalidos em ${entry.action}: ${entry.invalidFields.join(", ")}` : "",
    ]),
  ].filter((issue) => issue.length > 0);

  if (!criticalAudit.ok || !reviewSignatureAudit.ok) {
    blockers.add("Audit trail da emissao");
  }
  checks.push({
    id: "audit_trail",
    title: "Audit trail da emissao",
    status: criticalAudit.ok && reviewSignatureAudit.ok ? "passed" : "failed",
    detail:
      criticalAudit.ok && reviewSignatureAudit.ok
        ? "Hash-chain, eventos criticos e metadados de revisao/assinatura consistentes."
        : `Bloqueios: ${auditIssues.join("; ")}.`,
  });

  let qrCodeUrl: string | undefined;
  let qrVerificationStatus: EmissionDryRunResult["artifacts"]["qrVerificationStatus"];
  let publicPreview: Record<string, string> = {};
  let qrFailureDetail: string | undefined;

  if (
    numbering.certificateNumber &&
    isNonEmptyString(input.certificate.certificateId) &&
    isNonEmptyString(input.certificate.publicVerificationToken) &&
    isNonEmptyString(input.certificate.expectedQrHost)
  ) {
    qrCodeUrl = buildQrCodeUrl(
      input.certificate.expectedQrHost,
      input.certificate.certificateId,
      input.certificate.publicVerificationToken,
    );

    const verification = verifyPublicCertificateQrAuthenticity({
      qrCodeUrl,
      expectedHost: input.certificate.expectedQrHost,
      certificates: [
        {
          certificateId: input.certificate.certificateId,
          certificateNumber: numbering.certificateNumber,
          publicVerificationToken: input.certificate.publicVerificationToken,
          issuedAtUtc: input.audit.emittedAtUtc,
          revision: input.certificate.revision,
          instrumentDescription: input.equipment.instrumentDescription,
          serialNumber: input.equipment.serialNumber,
        },
      ],
      auditEntries,
    });

    if (verification.ok) {
      qrVerificationStatus = verification.status;
      publicPreview = buildPublicPreview(verification.certificate);
    } else {
      qrFailureDetail = renderQrFailureReason(verification.reason);
    }
  } else {
    qrFailureDetail = "campos obrigatorios do QR ausentes para o preview";
  }

  if (qrFailureDetail) {
    blockers.add("QR publico");
  }
  checks.push({
    id: "qr_authenticity",
    title: "QR publico",
    status: qrFailureDetail ? "failed" : "passed",
    detail: qrFailureDetail
      ? `Bloqueio: ${qrFailureDetail}.`
      : `QR autenticado em dry-run com status ${qrVerificationStatus}.`,
  });

  const status = checks.every((check) => check.status === "passed") ? "ready" : "blocked";

  return {
    status,
    profile: input.organization.profile,
    summary:
      status === "ready"
        ? `Dry-run pronto para emissao controlada no perfil ${input.organization.profile}.`
        : `Dry-run bloqueado por ${checks.filter((check) => check.status === "failed").length} verificacoes no perfil ${input.organization.profile}.`,
    blockers: [...blockers],
    warnings: [...warnings],
    checks,
    artifacts: {
      templateId: policy.templateId,
      symbolPolicy,
      certificateNumber: numbering.certificateNumber,
      declarationSummary,
      qrCodeUrl,
      qrVerificationStatus,
      publicPreview,
    },
  };
}

function buildAuditTrailPreview(
  input: RunCertificateEmissionDryRunInput,
  certificateNumber?: string,
): AuditChainEntry[] {
  const entries: AuditChainEntry[] = [];

  appendAuditEntry(entries, "audit-1", {
    action: "calibration.executed",
    certificateId: input.certificate.certificateId,
    certificateNumber,
    timestampUtc: input.audit.calibrationExecutedAtUtc,
  });
  appendAuditEntry(entries, "audit-2", {
    action: "technical_review.completed",
    certificateId: input.certificate.certificateId,
    certificateNumber,
    actorId: input.audit.technicalReviewerId,
    timestampUtc: input.audit.technicalReviewCompletedAtUtc,
    deviceId: input.audit.deviceId,
  });
  appendAuditEntry(entries, "audit-3", {
    action: "certificate.signed",
    certificateId: input.certificate.certificateId,
    certificateNumber,
    actorId: input.signatory.signatoryId,
    timestampUtc: input.audit.signedAtUtc,
    deviceId: input.audit.deviceId,
  });
  appendAuditEntry(entries, "audit-4", {
    action: "certificate.emitted",
    certificateId: input.certificate.certificateId,
    certificateNumber,
    timestampUtc: input.audit.emittedAtUtc,
  });

  return entries;
}

function appendAuditEntry(entries: AuditChainEntry[], id: string, payload: unknown) {
  const prevHash = entries.length === 0 ? "0".repeat(64) : entries[entries.length - 1]!.hash;
  entries.push({
    id,
    prevHash,
    payload,
    hash: computeAuditHash(prevHash, payload),
  });
}

function buildQrCodeUrl(expectedHost: string, certificateId: string, token: string) {
  return `https://${expectedHost}/verify?certificate=${encodeURIComponent(certificateId)}&token=${encodeURIComponent(token)}`;
}

function buildPublicPreview(certificate: Record<string, unknown>): Record<string, string> {
  const previewKeys = [
    "certificateNumber",
    "issuedAtUtc",
    "revision",
    "instrumentDescription",
    "serialNumber",
  ] as const;

  return Object.fromEntries(
    previewKeys.flatMap((key) => {
      const value = certificate[key];
      return typeof value === "string" && value.length > 0 ? [[key, value]] : [];
    }),
  );
}

function renderProfileWarning(code: string) {
  switch (code) {
    case "outside_accredited_scope":
      return "Escopo acreditado fora do ponto ensaiado: simbolo sera suprimido.";
    case "accreditation_expired":
      return "Acreditacao vencida: simbolo nao pode ser usado.";
    case "not_applicable_to_non_accredited_profile":
      return "Politica de escopo acreditado nao se aplica a perfis B/C.";
    default:
      return code;
  }
}

function renderProfileBlocker(code: string) {
  switch (code) {
    case "missing_scope_registration":
      return "escopo acreditado nao cadastrado";
    case "missing_cmc_registration":
      return "CMC nao cadastrada";
    case "uncertainty_below_cmc":
      return "incerteza expandida abaixo da CMC declarada";
    default:
      return code;
  }
}

function renderFreeTextIssue(issue: string) {
  if (issue.startsWith("forbidden_term:")) {
    return `texto livre contem termo proibido ${issue.split(":")[1]}`;
  }

  return issue;
}

function renderStandardEligibilityBlocker(code: string) {
  switch (code) {
    case "invalid_calibration_date":
      return "data de calibracao invalida";
    case "missing_valid_certificate":
      return "padrao sem certificado valido";
    case "missing_certificate_validity":
      return "validade do certificado do padrao ausente";
    case "expired_certificate":
      return "certificado do padrao vencido";
    case "missing_applicable_range":
      return "faixa aplicavel ausente";
    case "invalid_applicable_range":
      return "faixa aplicavel invalida";
    case "missing_measurement_value":
      return "valor de medicao ausente";
    case "standard_out_of_applicable_range":
      return "padrao fora da faixa aplicavel";
    default:
      return code;
  }
}

function renderSignatoryReason(reason: string | undefined) {
  switch (reason) {
    case "missing_required_data":
      return "dados obrigatorios do signatario ausentes";
    case "invalid_signed_at":
      return "timestamp de assinatura invalido";
    case "invalid_competence_record":
      return "registro de competencia invalido";
    case "no_competence_for_instrument":
      return "nao ha competencia cadastrada para o instrumento";
    case "competence_not_current":
      return "competencia nao vigente no momento da assinatura";
    default:
      return "erro de competencia nao identificado";
  }
}

function renderCertificateNumberingError(code: string) {
  switch (code) {
    case "missing_organization_id":
      return "organizationId ausente";
    case "missing_organization_code":
      return "organizationCode ausente";
    case "invalid_organization_code":
      return "organizationCode invalido";
    case "invalid_issued_number_owner":
      return "historico de numeracao com owner invalido";
    case "invalid_issued_number_format":
      return "historico de numeracao com formato invalido";
    case "existing_number_collision":
      return "colisao de numero ja emitido";
    case "organization_prefix_mismatch":
      return "prefixo de organizacao inconsistente";
    case "next_number_already_allocated":
      return "proximo numero ja reservado";
    default:
      return code;
  }
}

function renderMeasurementError(code: string) {
  switch (code) {
    case "missing_unit":
      return "unidade de medida ausente";
    case "invalid_result_value":
      return "resultado invalido";
    case "invalid_expanded_uncertainty_value":
      return "incerteza expandida invalida";
    case "invalid_coverage_factor":
      return "fator de abrangencia invalido";
    default:
      return code;
  }
}

function renderQrFailureReason(code: string) {
  switch (code) {
    case "invalid_qr_url":
      return "URL do QR invalida";
    case "certificate_not_found":
      return "certificado nao localizado";
    case "token_mismatch":
      return "token publico nao confere";
    case "invalid_audit_trail":
      return "audit trail invalida para o QR";
    case "missing_emission_event":
      return "evento certificate.emitted ausente";
    case "missing_reissue_evidence":
      return "evidencia de reemissao ausente";
    default:
      return code;
  }
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}
