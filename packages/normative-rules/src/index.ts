// @afere/normative-rules — Regras normativas executáveis
//
// Owner: regulator. Área CRÍTICA.
// Consumo: APENAS por apps/api. Violação bloqueada pelo Gate 6.
//
// Implementação real entra em paralelo com a V1 (harness/10-roadmap.md) e
// cada pacote normativo entra como bundle versionado em
// compliance/normative-packages/ (harness/04-compliance-pipeline.md Parte A).
//
// Escopo planejado:
// - Bloqueios regulatórios do PRD §9 (ex.: rastreabilidade do padrão ausente,
//   data de validade vencida, escopo fora de acreditação, etc.).
// - Validadores por tipo de certificado (A/B/C conforme DOQ-CGCRE).
// - Verificações de §16 (conformidade sistêmica ISO/IEC 17025).

export const NORMATIVE_RULES_VERSION = "0.0.1-scaffold";

export {
  assertSignedNormativePackage,
  hashNormativePackage,
  loadApprovedNormativePackageFromDirectory,
  loadNormativePackageManifest,
  loadSignedNormativePackageFromDirectory,
  parseNormativePackageYaml,
  signNormativePackage,
  verifyApprovedNormativePackageRepository,
  verifySignedNormativePackage,
  type ApprovedNormativePackageRepositoryVerification,
  type ApprovedNormativePackageVerification,
  type NormativePackageManifest,
  type NormativePackageManifestEntry,
  type NormativePackageSignatureMetadata,
  type NormativePackage,
  type NormativePackageVerification,
  type NormativeRuleSeverity,
  type SignedNormativePackageInput,
} from "./package.js";

export {
  resolveRegulatoryPdfPolicy,
  validateRegulatoryFreeText,
  type RegulatoryPdfPolicy,
  type RegulatoryProfileId,
} from "./regulatory-profiles.js";
