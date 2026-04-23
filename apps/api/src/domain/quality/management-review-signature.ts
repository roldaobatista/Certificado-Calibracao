import type { ManagementReviewSignature } from "@afere/contracts";

export type ManagementReviewSignatureSource = {
  heldAtUtc?: string;
  signedAtUtc?: string;
  signedByLabel?: string;
  signatureDeviceId?: string;
  signatureStatement?: string;
};

export function buildManagementReviewSignature(
  input: ManagementReviewSignatureSource,
): ManagementReviewSignature {
  const signed = Boolean(input.signedAtUtc);
  const canSign = !signed && Boolean(input.heldAtUtc);
  const blockers =
    signed || canSign ? [] : ["A reuniao ainda nao foi registrada como realizada, entao a ata segue sem assinatura."];

  return {
    status: signed ? "signed" : canSign ? "pending" : "blocked",
    statusLabel: signed ? "Ata assinada" : canSign ? "Pronta para assinatura" : "Assinatura bloqueada",
    signedByLabel: input.signedByLabel?.trim() || "Pendente",
    signedAtLabel: input.signedAtUtc ? formatManagementReviewSignatureDate(input.signedAtUtc) : "Pendente",
    deviceLabel: input.signatureDeviceId?.trim() || "Pendente",
    statementLabel:
      input.signatureStatement?.trim() || "Assinatura eletronica da analise critica ainda nao registrada.",
    canSign,
    blockers,
  };
}

export function formatManagementReviewSignatureDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}
