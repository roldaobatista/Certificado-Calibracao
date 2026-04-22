import type { EmissionDryRunResult } from "@afere/contracts";

export interface EmissionDryRunSummaryViewModel {
  status: "ready" | "blocked";
  headline: string;
  templateLabel: string;
  symbolLabel: string;
  passedChecks: number;
  failedChecks: number;
  blockers: string[];
  warnings: string[];
}

export function buildEmissionDryRunSummary(
  result: EmissionDryRunResult,
): EmissionDryRunSummaryViewModel {
  const failedChecks = result.checks.filter((check) => check.status === "failed").length;
  const passedChecks = result.checks.length - failedChecks;

  return {
    status: result.status,
    headline:
      result.status === "ready"
        ? "Pipeline seco pronto para emissao"
        : "Pipeline seco bloqueado antes da emissao",
    templateLabel: renderTemplateLabel(result.artifacts.templateId),
    symbolLabel: renderSymbolPolicyLabel(result.artifacts.symbolPolicy),
    passedChecks,
    failedChecks,
    blockers: result.blockers,
    warnings: result.warnings,
  };
}

function renderTemplateLabel(templateId: EmissionDryRunResult["artifacts"]["templateId"]) {
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

function renderSymbolPolicyLabel(
  symbolPolicy: EmissionDryRunResult["artifacts"]["symbolPolicy"],
) {
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
