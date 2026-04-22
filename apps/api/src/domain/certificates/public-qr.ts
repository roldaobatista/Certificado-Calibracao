import { verifyAuditHashChain, verifyControlledReissueAuditTrail, type AuditChainEntry } from "@afere/audit-log";
import type {
  PublicCertificateQrVerificationResult,
  PublicCertificateRecord,
} from "@afere/contracts";

export interface VerifyPublicCertificateQrAuthenticityInput {
  qrCodeUrl: string;
  expectedHost: string;
  certificates: PublicCertificateRecord[];
  auditEntries: AuditChainEntry[];
}

export function verifyPublicCertificateQrAuthenticity(
  input: VerifyPublicCertificateQrAuthenticityInput,
): PublicCertificateQrVerificationResult {
  const parsedUrl = tryParseQrCodeUrl(input.qrCodeUrl);
  if (!parsedUrl || parsedUrl.protocol !== "https:" || parsedUrl.host !== input.expectedHost) {
    return { ok: false, status: "not_found", reason: "invalid_qr_url" };
  }

  const certificateId = parsedUrl.searchParams.get("certificate");
  const token = parsedUrl.searchParams.get("token");
  if (!isNonEmptyString(certificateId) || !isNonEmptyString(token)) {
    return { ok: false, status: "not_found", reason: "invalid_qr_url" };
  }

  const certificate = input.certificates.find((item) => item.certificateId === certificateId);
  if (!certificate) {
    return { ok: false, status: "not_found", reason: "certificate_not_found" };
  }

  if (!isNonEmptyString(certificate.publicVerificationToken) || certificate.publicVerificationToken !== token) {
    return { ok: false, status: "not_found", reason: "token_mismatch" };
  }

  const certificateEntries = input.auditEntries.filter((entry) =>
    extractCertificateId(entry.payload) === certificateId,
  );
  const hashChain = verifyAuditHashChain(certificateEntries);
  if (!hashChain.ok) {
    return { ok: false, status: "not_found", reason: "invalid_audit_trail" };
  }

  const hasEmission = certificateEntries.some(
    (entry) => extractAction(entry.payload) === "certificate.emitted",
  );
  if (!hasEmission) {
    return { ok: false, status: "not_found", reason: "missing_emission_event" };
  }

  const isReissued = isNonEmptyString(certificate.reissuedAtUtc) || isNonEmptyString(certificate.replacementCertificateNumber);
  if (isReissued) {
    const reissueTrail = verifyControlledReissueAuditTrail(certificateEntries);
    if (!reissueTrail.ok) {
      return { ok: false, status: "not_found", reason: "missing_reissue_evidence" };
    }

    return {
      ok: true,
      status: "reissued",
      certificate,
    };
  }

  return {
    ok: true,
    status: "authentic",
    certificate,
  };
}

function tryParseQrCodeUrl(value: string): URL | undefined {
  try {
    return new URL(value);
  } catch {
    return undefined;
  }
}

function extractAction(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") return undefined;

  const action = (payload as { action?: unknown }).action;
  return typeof action === "string" ? action : undefined;
}

function extractCertificateId(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") return undefined;

  const certificateId = (payload as { certificateId?: unknown }).certificateId;
  return typeof certificateId === "string" ? certificateId : undefined;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}
