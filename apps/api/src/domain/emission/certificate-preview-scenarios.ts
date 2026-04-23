import type {
  CertificatePreviewCatalog,
  CertificatePreviewField,
  CertificatePreviewScenario,
  EmissionCertificatePreview,
  EmissionDryRunCheckId,
} from "@afere/contracts";

import {
  listEmissionDryRunScenarios,
  resolveEmissionDryRunScenario,
  type EmissionDryRunScenario,
  type EmissionDryRunScenarioId,
} from "./dry-run-scenarios.js";

const STEP_BY_CHECK: Record<EmissionDryRunCheckId, number> = {
  profile_policy: 11,
  equipment_registration: 2,
  standard_eligibility: 3,
  signatory_competence: 14,
  certificate_numbering: 13,
  raw_measurement_capture: 9,
  measurement_declaration: 10,
  audit_trail: 15,
  qr_authenticity: 13,
};

export function listCertificatePreviewScenarios(): CertificatePreviewScenario[] {
  return listEmissionDryRunScenarios().map(toPreviewScenario);
}

export function resolveCertificatePreviewScenario(scenarioId?: string): CertificatePreviewScenario {
  return toPreviewScenario(resolveEmissionDryRunScenario(scenarioId));
}

export function buildCertificatePreviewCatalog(scenarioId?: string): CertificatePreviewCatalog {
  const selectedScenario = resolveCertificatePreviewScenario(scenarioId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listCertificatePreviewScenarios(),
  };
}

function toPreviewScenario(scenario: EmissionDryRunScenario): CertificatePreviewScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: buildCertificatePreview(scenario),
  };
}

function buildCertificatePreview(scenario: EmissionDryRunScenario): EmissionCertificatePreview {
  const { input, result } = scenario;
  const suggestedReturnStep = selectSuggestedReturnStep(scenario);
  const declarationSummary = result.artifacts.declarationSummary ?? "Declaracao tecnica indisponivel.";
  const certificateNumber = result.artifacts.certificateNumber;
  const organizationName = input.organization.displayName ?? input.organization.organizationCode;
  const customerName = input.equipment.customerName ?? input.equipment.customerId ?? "Cliente nao identificado";
  const instrumentLine = [
    input.equipment.instrumentDescription,
    input.equipment.model,
    input.equipment.manufacturer,
  ]
    .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .join(" | ");

  return {
    status: result.status,
    headline:
      result.status === "ready"
        ? "Previa integral pronta para conferencia"
        : "Previa bloqueada antes da assinatura",
    templateId: result.artifacts.templateId,
    symbolPolicy: result.artifacts.symbolPolicy,
    certificateNumber,
    qrCodeUrl: result.artifacts.qrCodeUrl,
    qrVerificationStatus: result.artifacts.qrVerificationStatus,
    suggestedReturnStep,
    blockers: result.blockers,
    warnings: result.warnings,
    sections: [
      {
        key: "header",
        title: "Cabecalho",
        fields: compactFields([
          ["Organizacao emissora", organizationName],
          ["Perfil regulatorio", `Tipo ${input.organization.profile}`],
          ["Template", renderTemplateLabel(result.artifacts.templateId)],
          ["Politica de simbolo", renderSymbolPolicyLabel(result.artifacts.symbolPolicy)],
          ["Certificado", certificateNumber ?? "Numeracao ainda bloqueada"],
        ]),
      },
      {
        key: "identification",
        title: "Identificacao",
        fields: compactFields([
          ["Cliente", customerName],
          ["Equipamento", instrumentLine || input.equipment.instrumentDescription],
          ["Serie", input.equipment.serialNumber],
          ["TAG", input.equipment.tagCode ?? "Nao informada"],
          ["Faixa do item", renderApplicableRange(input.standard.applicableRange)],
        ]),
      },
      {
        key: "standards",
        title: "Padroes",
        fields: compactFields([
          ["Conjunto reservado", input.standard.standardSetLabel ?? "Padrao nao identificado"],
          ["Fonte", input.standard.source],
          ["Certificado do padrao", input.standard.certificateReference ?? "Nao informado"],
          ["Validade", input.standard.certificateValidUntil ?? "Nao informada"],
          ["Valor de referencia", renderOptionalNumber(input.standard.measurementValue, input.measurement.unit)],
        ]),
      },
      {
        key: "environment",
        title: "Ambiente",
        fields: compactFields([
          ["Faixa do procedimento", input.environment?.procedureRangeLabel ?? "Faixa nao modelada"],
          ["Temperatura", renderOptionalNumber(input.environment?.temperatureC, "C")],
          ["Umidade", renderOptionalNumber(input.environment?.humidityPercent, "%")],
          ["Pressao", renderOptionalNumber(input.environment?.pressureHpa, "hPa")],
          [
            "Status da faixa",
            input.environment?.withinProcedureRange === undefined
              ? "Nao avaliado neste cenario"
              : input.environment.withinProcedureRange
                ? "Dentro da faixa"
                : "Fora da faixa",
          ],
        ]),
      },
      {
        key: "results",
        title: "Resultados e incerteza",
        fields: compactFields([
          ["Resultado", renderOptionalNumber(input.measurement.resultValue, input.measurement.unit)],
          [
            "Incerteza expandida",
            renderOptionalNumber(input.measurement.expandedUncertaintyValue, input.measurement.unit),
          ],
          ["Fator de abrangencia", `k=${input.measurement.coverageFactor}`],
          ["Resumo tecnico", declarationSummary],
        ]),
      },
      {
        key: "decision",
        title: "Regra de decisao e observacoes",
        fields: compactFields([
          [
            "Regra de decisao",
            input.decision?.requested
              ? input.decision.ruleLabel ?? "Regra solicitada sem identificacao"
              : "Nao solicitada para esta OS",
          ],
          [
            "Resultado da decisao",
            input.decision?.requested
              ? input.decision.outcomeLabel ?? "Resultado pendente"
              : "Nao aplicavel",
          ],
          ["Observacoes", input.notes?.join(" | ") ?? "Sem observacoes complementares"],
        ]),
      },
      {
        key: "authorization",
        title: "Revisao e assinatura",
        fields: compactFields([
          ["Revisor tecnico", input.audit.technicalReviewerName ?? input.audit.technicalReviewerId],
          ["Signatario", input.signatory.displayName ?? input.signatory.signatoryId],
          ["Autorizacao", input.signatory.authorizationLabel ?? "Nao informada"],
          ["Assinatura prevista em", input.audit.signedAtUtc],
          [
            "Status do QR publico",
            result.artifacts.qrVerificationStatus ?? "QR ainda nao autenticado neste cenario",
          ],
        ]),
      },
      {
        key: "footer",
        title: "Rodape e publicacao",
        fields: compactFields([
          ["Revisao", input.certificate.revision],
          ["Emissao prevista em", input.audit.emittedAtUtc],
          ["Dispositivo", input.audit.deviceId],
          ["Link publico", result.artifacts.qrCodeUrl ?? "Preview do QR indisponivel"],
          [
            "Retorno sugerido",
            suggestedReturnStep ? `Voltar ao passo ${suggestedReturnStep}` : "Nenhum retorno corretivo sugerido",
          ],
        ]),
      },
    ],
  };
}

function selectSuggestedReturnStep(scenario: EmissionDryRunScenario): number | undefined {
  const failedSteps = scenario.result.checks
    .filter((check) => check.status === "failed")
    .map((check) => STEP_BY_CHECK[check.id]);

  if (failedSteps.length === 0) {
    return undefined;
  }

  return Math.min(...failedSteps);
}

function compactFields(values: Array<[string, string]>): CertificatePreviewField[] {
  return values.map(([label, value]) => ({ label, value }));
}

function renderTemplateLabel(templateId: EmissionCertificatePreview["templateId"]): string {
  switch (templateId) {
    case "template-a":
      return "Template A";
    case "template-b":
      return "Template B";
    case "template-c":
      return "Template C";
    default:
      return templateId;
  }
}

function renderSymbolPolicyLabel(symbolPolicy: EmissionCertificatePreview["symbolPolicy"]): string {
  switch (symbolPolicy) {
    case "allowed":
      return "Simbolo permitido";
    case "suppressed":
      return "Simbolo suprimido";
    case "blocked":
      return "Simbolo bloqueado";
    default:
      return symbolPolicy;
  }
}

function renderApplicableRange(
  range: EmissionDryRunScenario["input"]["standard"]["applicableRange"],
): string {
  if (!range) {
    return "Faixa nao informada";
  }

  return `${range.minimum} a ${range.maximum}`;
}

function renderOptionalNumber(value: number | undefined, unit: string): string {
  return typeof value === "number" ? `${value} ${unit}` : "Nao informado";
}

export type CertificatePreviewScenarioSelection = EmissionDryRunScenarioId;
