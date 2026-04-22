import {
  computeAuditHash,
  GENESIS_HASH,
  type AuditChainEntry,
} from "@afere/audit-log";
import type {
  PublicCertificateQrVerificationResult,
  PublicCertificateRecord,
  PublicCertificateScenarioId as ContractPublicCertificateScenarioId,
} from "@afere/contracts";

import { verifyPublicCertificateQrAuthenticity } from "./public-qr.js";

type PublicCertificateScenarioDefinition = {
  label: string;
  description: string;
  buildResult: () => PublicCertificateQrVerificationResult;
};

const SCENARIOS = {
  authentic: {
    label: "Certificado autentico",
    description: "Mostra o recorte minimo de metadados para um certificado valido e nao reemitido.",
    buildResult: () =>
      sanitizePublicCertificateVerificationResult(
        verifyPublicCertificateQrAuthenticity({
          qrCodeUrl:
            "https://verificar.afere.test/public/certificate?certificate=cert-001&token=tok-abc",
          expectedHost: "verificar.afere.test",
          certificates: [
            {
              certificateId: "cert-001",
              certificateNumber: "AFR-000123",
              publicVerificationToken: "tok-abc",
              issuedAtUtc: "2026-04-21T14:00:00Z",
              revision: "R0",
              instrumentDescription: "Balanca IPNA 300 kg",
              serialNumber: "SN-42",
              customerName: "Cliente Sigiloso",
              customerAddress: "Rua Interna, 123",
            },
          ],
          auditEntries: buildAuditTrail([
            {
              action: "certificate.emitted",
              certificateId: "cert-001",
              timestampUtc: "2026-04-21T14:00:00Z",
            },
          ]),
        }),
      ),
  },
  reissued: {
    label: "Certificado reemitido",
    description: "Explicita a reemissao preservando apenas os metadados publicos estritamente necessarios.",
    buildResult: () =>
      sanitizePublicCertificateVerificationResult(
        verifyPublicCertificateQrAuthenticity({
          qrCodeUrl:
            "https://verificar.afere.test/public/certificate?certificate=cert-002&token=tok-r1",
          expectedHost: "verificar.afere.test",
          certificates: [
            {
              certificateId: "cert-002",
              certificateNumber: "AFR-000124",
              publicVerificationToken: "tok-r1",
              issuedAtUtc: "2026-04-20T09:00:00Z",
              reissuedAtUtc: "2026-04-21T16:00:00Z",
              replacementCertificateNumber: "AFR-000124-R1",
              revision: "R1",
              instrumentDescription: "Balanca IPNA 300 kg",
              serialNumber: "SN-99",
              actorId: "signer-1",
            },
          ],
          auditEntries: buildAuditTrail([
            {
              action: "certificate.emitted",
              certificateId: "cert-002",
              timestampUtc: "2026-04-20T09:00:00Z",
            },
            {
              action: "certificate.reissue.approved",
              certificateId: "cert-002",
              actorId: "reviewer-1",
              timestampUtc: "2026-04-21T15:00:00Z",
            },
            {
              action: "certificate.reissue.approved",
              certificateId: "cert-002",
              actorId: "reviewer-2",
              timestampUtc: "2026-04-21T15:05:00Z",
            },
            {
              action: "certificate.reissued",
              certificateId: "cert-002",
              previousCertificateHash: "a".repeat(64),
              previousRevision: "R0",
              newRevision: "R1",
            },
            {
              action: "certificate.reissue.notified",
              certificateId: "cert-002",
              recipient: "cliente@example.com",
              timestampUtc: "2026-04-21T16:01:00Z",
            },
          ]),
        }),
      ),
  },
  "not-found": {
    label: "Nao localizado",
    description: "Fluxo fail-closed quando o portal nao encontra evidencias suficientes para expor dados publicos.",
    buildResult: () =>
      sanitizePublicCertificateVerificationResult(
        verifyPublicCertificateQrAuthenticity({
          qrCodeUrl:
            "https://verificar.afere.test/public/certificate?certificate=cert-404&token=tok-miss",
          expectedHost: "verificar.afere.test",
          certificates: [],
          auditEntries: [],
        }),
      ),
  },
} as const satisfies Record<
  ContractPublicCertificateScenarioId,
  PublicCertificateScenarioDefinition
>;

const PUBLIC_CERTIFICATE_KEYS = [
  "certificateNumber",
  "issuedAtUtc",
  "revision",
  "instrumentDescription",
  "serialNumber",
  "reissuedAtUtc",
  "replacementCertificateNumber",
] as const;

export type PublicCertificateScenarioId = keyof typeof SCENARIOS;

export interface PublicCertificateScenario {
  id: PublicCertificateScenarioId;
  label: string;
  description: string;
  result: PublicCertificateQrVerificationResult;
}

const DEFAULT_SCENARIO: PublicCertificateScenarioId = "authentic";

export function resolvePublicCertificateScenario(scenarioId?: string): PublicCertificateScenario {
  const id = isPublicCertificateScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.buildResult(),
  };
}

export function listPublicCertificateScenarios(): PublicCertificateScenario[] {
  return (Object.keys(SCENARIOS) as PublicCertificateScenarioId[]).map((scenarioId) =>
    resolvePublicCertificateScenario(scenarioId),
  );
}

function sanitizePublicCertificateVerificationResult(
  result: PublicCertificateQrVerificationResult,
): PublicCertificateQrVerificationResult {
  if (!result.ok) {
    return result;
  }

  return {
    ok: true,
    status: result.status,
    certificate: Object.fromEntries(
      PUBLIC_CERTIFICATE_KEYS.flatMap((key) => {
        const value = result.certificate[key];
        return typeof value === "string" && value.length > 0 ? [[key, value]] : [];
      }),
    ) as PublicCertificateRecord,
  };
}

function buildAuditTrail(payloads: Array<Record<string, unknown>>): AuditChainEntry[] {
  let prevHash = GENESIS_HASH;

  return payloads.map((payload, index) => {
    const entry = {
      id: `evt-${index + 1}`,
      prevHash,
      payload,
      hash: computeAuditHash(prevHash, payload),
    };

    prevHash = entry.hash;
    return entry;
  });
}

function isPublicCertificateScenarioId(
  value: string | undefined,
): value is PublicCertificateScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
