import type {
  PublicCertificatePageModel,
  PublicCertificateQrVerificationResult,
} from "@afere/contracts";

const AUTHENTIC_METADATA_KEYS = [
  "certificateNumber",
  "issuedAtUtc",
  "revision",
  "instrumentDescription",
  "serialNumber",
] as const;

const REISSUED_METADATA_KEYS = [
  ...AUTHENTIC_METADATA_KEYS,
  "reissuedAtUtc",
  "replacementCertificateNumber",
] as const;

export function buildPublicCertificatePageModel(
  result: PublicCertificateQrVerificationResult,
): PublicCertificatePageModel {
  if (result.status === "not_found" || !result.certificate) {
    return {
      status: "not_found",
      title: "Certificado nao localizado",
      publicMetadata: {},
    };
  }

  const keys = result.status === "reissued" ? REISSUED_METADATA_KEYS : AUTHENTIC_METADATA_KEYS;

  return {
    status: result.status,
    title: result.status === "reissued" ? "Certificado reemitido" : "Certificado autentico",
    publicMetadata: pickPublicMetadata(result.certificate, keys),
  };
}

function pickPublicMetadata(
  certificate: Record<string, unknown>,
  keys: readonly string[],
): Record<string, string> {
  return Object.fromEntries(
    keys.flatMap((key) => {
      const value = certificate[key];
      return typeof value === "string" && value.length > 0 ? [[key, value]] : [];
    }),
  );
}
