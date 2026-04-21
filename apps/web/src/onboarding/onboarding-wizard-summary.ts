const BLOCKING_REASON_LABELS: Record<string, string> = {
  organization_profile_pending: "Cadastro da organizacao",
  primary_signatory_pending: "Signatario principal",
  certificate_numbering_pending: "Numeracao de certificado",
  scope_review_pending: "Escopo e CMC",
  public_qr_pending: "QR publico",
};

export interface BuildOnboardingWizardSummaryInput {
  completedWithinTarget: boolean;
  canEmitFirstCertificate: boolean;
  blockingReasons: string[];
}

export interface OnboardingWizardSummary {
  status: "ready" | "blocked";
  title: string;
  timeTargetLabel: string;
  blockingSteps: string[];
}

export function buildOnboardingWizardSummary(
  input: BuildOnboardingWizardSummaryInput,
): OnboardingWizardSummary {
  return {
    status: input.canEmitFirstCertificate ? "ready" : "blocked",
    title: input.canEmitFirstCertificate
      ? "Onboarding pronto para primeira emissao"
      : "Emissao bloqueada ate concluir o onboarding",
    timeTargetLabel: input.completedWithinTarget
      ? "Dentro da meta de 1 hora"
      : "Acima da meta de 1 hora",
    blockingSteps: input.blockingReasons.map(
      (reason) => BLOCKING_REASON_LABELS[reason] ?? reason,
    ),
  };
}
