import type { ReviewSignatureWorkflowResult } from "@afere/contracts";

export interface ReviewSignatureSummaryViewModel {
  status: ReviewSignatureWorkflowResult["status"];
  headline: string;
  stageLabel: string;
  reviewStatusLabel: string;
  signatureStatusLabel: string;
  allowedActionsLabel: string;
  blockers: string[];
}

export function buildReviewSignatureSummary(
  result: ReviewSignatureWorkflowResult,
): ReviewSignatureSummaryViewModel {
  return {
    status: result.status,
    headline: buildHeadline(result),
    stageLabel: buildStageLabel(result.stage),
    reviewStatusLabel: `Revisao: ${buildStepLabel(result.reviewStep.status)}`,
    signatureStatusLabel: `Assinatura: ${buildStepLabel(result.signatureStep.status)}`,
    allowedActionsLabel:
      result.allowedActions.length === 0
        ? "Nenhuma acao liberada"
        : `${result.allowedActions.length} acao(oes) liberada(s)`,
    blockers: result.blockers,
  };
}

function buildHeadline(result: ReviewSignatureWorkflowResult): string {
  if (result.stage === "emitted") {
    return "Fluxo auditavel concluido";
  }

  if (result.status === "ready" && result.stage === "in_review") {
    return "Revisao tecnica liberada";
  }

  if (result.status === "ready" && result.stage === "approved") {
    return "Assinatura pronta para emissao";
  }

  return "Workflow bloqueado";
}

function buildStageLabel(stage: ReviewSignatureWorkflowResult["stage"]): string {
  switch (stage) {
    case "in_review":
      return "OS em revisao";
    case "approved":
      return "Fluxo aprovado";
    case "emitted":
      return "Certificado emitido";
  }
}

function buildStepLabel(status: ReviewSignatureWorkflowResult["reviewStep"]["status"]): string {
  switch (status) {
    case "ready":
      return "pronta";
    case "pending":
      return "pendente";
    case "blocked":
      return "bloqueada";
    case "complete":
      return "concluida";
  }
}
