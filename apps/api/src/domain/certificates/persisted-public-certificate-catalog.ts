import type {
  PublicCertificateCatalog,
  PublicCertificateQrVerificationResult,
  PublicCertificateRecord,
  PublicCertificateScenario,
} from "@afere/contracts";

import type {
  PersistedCertificatePublicationRecord,
  PersistedEmissionAuditEvent,
} from "../emission/service-order-persistence.js";
import { verifyPublicCertificateQrAuthenticity } from "./public-qr.js";

export function buildPersistedPublicCertificateCatalog(input: {
  serviceOrderId?: string;
  token?: string;
  publications: PersistedCertificatePublicationRecord[];
  auditEvents: PersistedEmissionAuditEvent[];
}): PublicCertificateCatalog {
  const selectedScenario = buildSelectedScenario(input);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: [selectedScenario],
  };
}

function buildSelectedScenario(input: {
  serviceOrderId?: string;
  token?: string;
  publications: PersistedCertificatePublicationRecord[];
  auditEvents: PersistedEmissionAuditEvent[];
}): PublicCertificateScenario {
  if (!input.serviceOrderId || !input.token) {
    return {
      id: "not-found",
      label: "Nao localizado",
      description: "Consulta publica sem certificado ou token suficientes para verificacao.",
      result: { ok: false, status: "not_found", reason: "invalid_qr_url" },
    };
  }

  const publication = input.publications.find(
    (item) =>
      item.serviceOrderId === input.serviceOrderId &&
      item.publicVerificationToken === input.token,
  );
  const replacementPublication = publication?.replacementPublicationId
    ? input.publications.find((item) => item.publicationId === publication.replacementPublicationId)
    : undefined;

  const result = publication
      ? verifyPublicCertificateQrAuthenticity({
        qrCodeUrl: `https://${publication.qrHost}/verify?certificate=${encodeURIComponent(
          publication.serviceOrderId,
        )}&token=${encodeURIComponent(publication.publicVerificationToken)}`,
        expectedHost: publication.qrHost,
        certificates: input.publications.map(toPublicCertificateRecord),
        auditEntries: input.auditEvents.map((event) =>
          toPublicAuditEntry(event, publication, replacementPublication),
        ),
      })
    : ({ ok: false, status: "not_found", reason: "certificate_not_found" } as PublicCertificateQrVerificationResult);

  return {
    id: mapResultToScenarioId(result),
    label: resultLabel(result),
    description: resultDescription(result),
    result,
  };
}

function toPublicCertificateRecord(
  publication: PersistedCertificatePublicationRecord,
): PublicCertificateRecord {
  return {
    certificateId: publication.serviceOrderId,
    certificateNumber:
      publication.revision !== "R0"
        ? `${publication.certificateNumber}-${publication.revision}`
        : publication.certificateNumber,
    publicVerificationToken: publication.publicVerificationToken,
    issuedAtUtc: publication.issuedAtUtc,
    reissuedAtUtc: publication.supersededAtUtc,
    replacementCertificateNumber: publication.replacementCertificateNumber,
    revision: publication.revision,
    instrumentDescription: publication.equipmentLabel,
    serialNumber: publication.equipmentSerialNumber,
  };
}

function toPublicAuditEntry(
  event: PersistedEmissionAuditEvent,
  publication: PersistedCertificatePublicationRecord,
  replacementPublication?: PersistedCertificatePublicationRecord,
) {
  return {
    id: event.eventId,
    prevHash: event.prevHash,
    hash: event.hash,
    payload: {
      action: event.action,
      actorId: event.actorUserId,
      actorLabel: event.actorLabel,
      certificateId: event.serviceOrderId,
      certificateNumber: event.certificateNumber,
      entityLabel: event.entityLabel,
      timestampUtc: event.occurredAtUtc,
      deviceId: event.deviceId,
      ...(event.metadata ?? {}),
      ...deriveReissueMetadata(event, publication, replacementPublication),
    },
  };
}

function deriveReissueMetadata(
  event: PersistedEmissionAuditEvent,
  publication: PersistedCertificatePublicationRecord,
  replacementPublication?: PersistedCertificatePublicationRecord,
) {
  if (event.action === "certificate.reissued" && replacementPublication) {
    return {
      previousCertificateHash: publication.documentHash,
      previousRevision: publication.revision,
      newRevision: replacementPublication.revision,
    };
  }

  if (event.action === "certificate.reissue.notified") {
    return {
      recipient:
        replacementPublication?.notificationRecipient ??
        publication.notificationRecipient,
      timestampUtc:
        replacementPublication?.notificationSentAtUtc ??
        publication.notificationSentAtUtc ??
        event.occurredAtUtc,
    };
  }

  return {};
}

function mapResultToScenarioId(result: PublicCertificateQrVerificationResult) {
  if (!result.ok) {
    return "not-found" as const;
  }

  return result.status === "reissued" ? ("reissued" as const) : ("authentic" as const);
}

function resultLabel(result: PublicCertificateQrVerificationResult) {
  if (!result.ok) {
    return "Nao localizado";
  }

  return result.status === "reissued" ? "Certificado reemitido" : "Certificado autentico";
}

function resultDescription(result: PublicCertificateQrVerificationResult) {
  if (!result.ok) {
    return "A verificacao publica falhou fechada sem evidencias suficientes para expor metadados.";
  }

  return result.status === "reissued"
    ? "O QR continua valido apenas para informar que existe revisao posterior rastreada."
    : "O QR confirma autenticidade publica com metadados minimos.";
}
