import type {
  MembershipRole,
  ReviewSignatureAction,
  ReviewSignatureCheck,
  ReviewSignatureCheckId,
  ReviewSignatureStage,
  ReviewSignatureStep,
  ReviewSignatureWorkflowResult,
  WorkflowActor,
  WorkflowSuggestion,
} from "@afere/contracts";

const REVIEWER_ROLES: MembershipRole[] = ["technical_reviewer", "quality_manager"];
const SIGNATORY_ROLES: MembershipRole[] = ["signatory"];
const EXECUTOR_ROLES: MembershipRole[] = ["technician"];

export interface WorkflowMembershipInput {
  userId: string;
  displayName: string;
  organizationId: string;
  roles: MembershipRole[];
  active: boolean;
  mfaEnabled: boolean;
  authorizedInstrumentTypes: string[];
  pendingAssignments: number;
}

export interface EvaluateReviewSignatureWorkflowInput {
  organizationId: string;
  instrumentType: string;
  stage: ReviewSignatureStage;
  executor: WorkflowMembershipInput;
  reviewer?: WorkflowMembershipInput;
  signatory?: WorkflowMembershipInput;
  candidates: WorkflowMembershipInput[];
}

export function evaluateReviewSignatureWorkflow(
  input: EvaluateReviewSignatureWorkflowInput,
): ReviewSignatureWorkflowResult {
  const reviewerSuggestion = selectReviewerSuggestion(input);
  const signatorySuggestion = selectSignatorySuggestion(input, reviewerSuggestion?.userId);

  const executorMembershipOk = isActorActiveInOrganization(input.executor, input.organizationId);
  const executorRoleOk = hasAnyRole(input.executor, EXECUTOR_ROLES);

  const reviewerMembershipOk = Boolean(
    input.reviewer && isActorActiveInOrganization(input.reviewer, input.organizationId) && hasAnyRole(input.reviewer, REVIEWER_ROLES),
  );
  const reviewerSegregationOk = Boolean(
    input.reviewer &&
      input.reviewer.userId !== input.executor.userId &&
      input.reviewer.userId !== input.signatory?.userId,
  );
  const reviewerCompetenceOk = Boolean(
    input.reviewer && supportsInstrumentType(input.reviewer, input.instrumentType),
  );

  const signatoryMembershipOk = Boolean(
    input.signatory &&
      isActorActiveInOrganization(input.signatory, input.organizationId) &&
      hasAnyRole(input.signatory, SIGNATORY_ROLES),
  );
  const signatorySegregationOk = Boolean(
    input.signatory &&
      input.signatory.userId !== input.executor.userId &&
      input.signatory.userId !== input.reviewer?.userId,
  );
  const signatoryCompetenceOk = Boolean(
    input.signatory && supportsInstrumentType(input.signatory, input.instrumentType),
  );
  const signatoryMfaOk = Boolean(input.signatory?.mfaEnabled);

  const blockers: string[] = [];

  if (!executorMembershipOk || !executorRoleOk) {
    blockers.push("executor sem membership tecnico valido na organizacao ativa");
  }

  if (!reviewerMembershipOk) {
    blockers.push("revisor sem papel elegivel de revisao tecnica na organizacao ativa");
  }
  if (input.reviewer && !reviewerSegregationOk) {
    blockers.push("revisor deve ser diferente do executor e do signatario");
  }
  if (input.reviewer && !reviewerCompetenceOk) {
    blockers.push("revisor sem competencia ativa para o tipo de instrumento");
  }

  if (!signatoryMembershipOk) {
    blockers.push("signatario sem papel elegivel na organizacao ativa");
  }
  if (input.signatory && !signatorySegregationOk) {
    blockers.push("signatario deve ser diferente do executor e do revisor");
  }
  if (input.signatory && !signatoryCompetenceOk) {
    blockers.push("signatario sem competencia ativa para o tipo de instrumento");
  }
  if (input.signatory && !signatoryMfaOk) {
    blockers.push("signatario sem MFA obrigatorio para concluir a emissao");
  }

  const checks: ReviewSignatureCheck[] = [
    buildCheck(
      "executor_membership",
      "Executor tecnico",
      executorMembershipOk && executorRoleOk,
      executorMembershipOk && executorRoleOk
        ? `${input.executor.displayName} esta vinculado a organizacao ativa como tecnico calibrador.`
        : "Executor precisa de membership ativo com papel tecnico na organizacao selecionada.",
    ),
    buildCheck(
      "reviewer_membership",
      "Papel do revisor",
      reviewerMembershipOk,
      reviewerMembershipOk
        ? `${input.reviewer?.displayName ?? "Revisor"} possui papel elegivel para revisao tecnica.`
        : "Revisor precisa ter membership ativo como revisor tecnico ou gestor da qualidade.",
    ),
    buildCheck(
      "reviewer_segregation",
      "Segregacao do revisor",
      reviewerSegregationOk,
      reviewerSegregationOk
        ? "Revisor esta segregado do executor e do signatario."
        : "Revisor nao pode coincidir com executor ou signatario no mesmo fluxo.",
    ),
    buildCheck(
      "reviewer_competence",
      "Competencia do revisor",
      reviewerCompetenceOk,
      reviewerCompetenceOk
        ? "Revisor cobre o tipo de instrumento deste fluxo."
        : "Revisor precisa ter competencia ativa para o tipo de instrumento.",
    ),
    buildCheck(
      "signatory_membership",
      "Papel do signatario",
      signatoryMembershipOk,
      signatoryMembershipOk
        ? `${input.signatory?.displayName ?? "Signatario"} possui papel autorizador para assinatura.`
        : "Signatario precisa ter membership ativo com papel de signatario autorizado.",
    ),
    buildCheck(
      "signatory_segregation",
      "Segregacao do signatario",
      signatorySegregationOk,
      signatorySegregationOk
        ? "Signatario esta segregado de executor e revisor."
        : "Signatario nao pode coincidir com executor ou revisor no mesmo fluxo.",
    ),
    buildCheck(
      "signatory_competence",
      "Competencia do signatario",
      signatoryCompetenceOk,
      signatoryCompetenceOk
        ? "Signatario cobre o tipo de instrumento deste certificado."
        : "Signatario precisa ter competencia ativa para o tipo de instrumento.",
    ),
    buildCheck(
      "signatory_mfa",
      "MFA do signatario",
      signatoryMfaOk,
      signatoryMfaOk
        ? "MFA obrigatorio do signatario esta habilitado."
        : "Assinatura permanece bloqueada enquanto o signatario nao habilitar MFA.",
    ),
  ];

  const reviewStepReady =
    executorMembershipOk &&
    executorRoleOk &&
    reviewerMembershipOk &&
    reviewerSegregationOk &&
    reviewerCompetenceOk;
  const signatoryReady =
    signatoryMembershipOk &&
    signatorySegregationOk &&
    signatoryCompetenceOk &&
    signatoryMfaOk;

  const reviewStep = buildReviewStep(input, reviewStepReady, reviewerSuggestion);
  const signatureStep = buildSignatureStep(input, signatoryReady, signatorySuggestion);

  return {
    status: blockers.length === 0 ? "ready" : "blocked",
    stage: input.stage,
    summary: buildSummary(input.stage, blockers.length === 0),
    blockers,
    warnings: [],
    allowedActions: buildAllowedActions(input.stage, reviewStep.status, signatureStep.status),
    reviewStep,
    signatureStep,
    checks,
    assignments: {
      executor: toWorkflowActor(input.executor),
      reviewer: input.reviewer ? toWorkflowActor(input.reviewer) : undefined,
      signatory: input.signatory ? toWorkflowActor(input.signatory) : undefined,
    },
    suggestions: {
      reviewer: reviewerSuggestion,
      signatory: signatorySuggestion,
    },
  };
}

function buildReviewStep(
  input: EvaluateReviewSignatureWorkflowInput,
  reviewStepReady: boolean,
  reviewerSuggestion?: WorkflowSuggestion,
): ReviewSignatureStep {
  if (input.stage === "approved" || input.stage === "emitted") {
    return {
      title: "Revisao tecnica",
      status: "complete",
      actorLabel: input.reviewer?.displayName ?? reviewerSuggestion?.displayName ?? "Revisor nao informado",
      detail: "A revisao tecnica ja foi concluida e o fluxo avancou para a proxima etapa.",
    };
  }

  if (reviewStepReady) {
    return {
      title: "Revisao tecnica",
      status: "ready",
      actorLabel: input.reviewer?.displayName ?? "Revisor atribuido",
      detail: "A revisao tecnica pode seguir com segregacao valida e competencia ativa.",
    };
  }

  return {
    title: "Revisao tecnica",
    status: "blocked",
    actorLabel: input.reviewer?.displayName ?? reviewerSuggestion?.displayName ?? "Reatribuicao necessaria",
    detail: reviewerSuggestion
      ? `Revise a atribuicao atual. Sugestao: ${reviewerSuggestion.displayName}.`
      : "Nao ha revisor elegivel disponivel para este fluxo na organizacao ativa.",
  };
}

function buildSignatureStep(
  input: EvaluateReviewSignatureWorkflowInput,
  signatoryReady: boolean,
  signatorySuggestion?: WorkflowSuggestion,
): ReviewSignatureStep {
  if (input.stage === "emitted") {
    return {
      title: "Assinatura e emissao",
      status: "complete",
      actorLabel: input.signatory?.displayName ?? signatorySuggestion?.displayName ?? "Signatario nao informado",
      detail: "Assinatura e emissao ja foram concluidas para este fluxo.",
    };
  }

  if (input.stage === "approved") {
    if (signatoryReady) {
      return {
        title: "Assinatura e emissao",
        status: "ready",
        actorLabel: input.signatory?.displayName ?? "Signatario atribuido",
        detail: "O certificado esta pronto para re-autenticacao, assinatura e emissao.",
      };
    }

    return {
      title: "Assinatura e emissao",
      status: "blocked",
      actorLabel: input.signatory?.displayName ?? signatorySuggestion?.displayName ?? "Reatribuicao necessaria",
      detail: signatorySuggestion
        ? `A assinatura segue bloqueada. Sugestao: ${signatorySuggestion.displayName}.`
        : "Nao ha signatario elegivel disponivel para este fluxo na organizacao ativa.",
    };
  }

  if (signatoryReady) {
    return {
      title: "Assinatura e emissao",
      status: "pending",
      actorLabel: input.signatory?.displayName ?? "Signatario atribuido",
      detail: "A assinatura permanece em fila e sera liberada apos a aprovacao da revisao tecnica.",
    };
  }

  return {
    title: "Assinatura e emissao",
    status: "blocked",
    actorLabel: input.signatory?.displayName ?? signatorySuggestion?.displayName ?? "Reatribuicao necessaria",
    detail: signatorySuggestion
      ? `A assinatura futura ja esta bloqueada. Sugestao: ${signatorySuggestion.displayName}.`
      : "Nao ha signatario elegivel disponivel para este fluxo na organizacao ativa.",
  };
}

function buildAllowedActions(
  stage: ReviewSignatureStage,
  reviewStatus: ReviewSignatureStep["status"],
  signatureStatus: ReviewSignatureStep["status"],
): ReviewSignatureAction[] {
  if (stage === "in_review") {
    return reviewStatus === "ready" ? ["review_certificate", "reject_to_executor"] : [];
  }

  if (stage === "approved") {
    return signatureStatus === "ready" ? ["sign_certificate"] : [];
  }

  return ["archive_workflow"];
}

function buildSummary(stage: ReviewSignatureStage, ready: boolean): string {
  if (stage === "emitted") {
    return "Fluxo ja emitido, com revisao e assinatura registradas.";
  }

  if (ready && stage === "in_review") {
    return "Revisao tecnica liberada e assinatura futura preparada com segregacao valida.";
  }

  if (ready && stage === "approved") {
    return "Fluxo aprovado e pronto para assinatura do signatario autorizado.";
  }

  return "Workflow bloqueado por autorizacao incompleta ou segregacao de funcoes invalida.";
}

function selectReviewerSuggestion(
  input: EvaluateReviewSignatureWorkflowInput,
): WorkflowSuggestion | undefined {
  const candidate = input.candidates
    .filter(
      (actor) =>
        actor.userId !== input.executor.userId &&
        actor.userId !== input.signatory?.userId &&
        isActorActiveInOrganization(actor, input.organizationId) &&
        hasAnyRole(actor, REVIEWER_ROLES) &&
        supportsInstrumentType(actor, input.instrumentType),
    )
    .sort(compareByQueueAndName)[0];

  return candidate
    ? {
        userId: candidate.userId,
        displayName: candidate.displayName,
        rationale: "Menor fila entre revisores elegiveis para o tipo de instrumento.",
      }
    : undefined;
}

function selectSignatorySuggestion(
  input: EvaluateReviewSignatureWorkflowInput,
  reviewerUserId?: string,
): WorkflowSuggestion | undefined {
  const candidate = input.candidates
    .filter(
      (actor) =>
        actor.userId !== input.executor.userId &&
        actor.userId !== reviewerUserId &&
        isActorActiveInOrganization(actor, input.organizationId) &&
        hasAnyRole(actor, SIGNATORY_ROLES) &&
        supportsInstrumentType(actor, input.instrumentType) &&
        actor.mfaEnabled,
    )
    .sort(compareByQueueAndName)[0];

  return candidate
    ? {
        userId: candidate.userId,
        displayName: candidate.displayName,
        rationale: "Menor fila entre signatarios elegiveis com MFA obrigatorio ativo.",
      }
    : undefined;
}

function compareByQueueAndName(left: WorkflowMembershipInput, right: WorkflowMembershipInput): number {
  if (left.pendingAssignments !== right.pendingAssignments) {
    return left.pendingAssignments - right.pendingAssignments;
  }

  return left.displayName.localeCompare(right.displayName, "pt-BR");
}

function buildCheck(
  id: ReviewSignatureCheckId,
  title: string,
  passed: boolean,
  detail: string,
): ReviewSignatureCheck {
  return {
    id,
    title,
    status: passed ? "passed" : "failed",
    detail,
  };
}

function toWorkflowActor(input: WorkflowMembershipInput): WorkflowActor {
  return {
    userId: input.userId,
    displayName: input.displayName,
    roles: input.roles,
    mfaEnabled: input.mfaEnabled,
    pendingAssignments: input.pendingAssignments,
  };
}

function hasAnyRole(actor: WorkflowMembershipInput, roles: MembershipRole[]): boolean {
  const actorRoles = new Set(actor.roles);
  return roles.some((role) => actorRoles.has(role));
}

function supportsInstrumentType(actor: WorkflowMembershipInput, instrumentType: string): boolean {
  return actor.authorizedInstrumentTypes.includes(instrumentType);
}

function isActorActiveInOrganization(actor: WorkflowMembershipInput, organizationId: string): boolean {
  return actor.active && actor.organizationId === organizationId;
}
