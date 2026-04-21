import { type AuditChainEntry, type AuditChainVerification, verifyAuditHashChain } from "./verify.js";

const REISSUE_ACTION = "certificate.reissued";
const NOTIFICATION_ACTION = "certificate.reissue.notified";
const APPROVAL_ACTION = "certificate.reissue.approved";
const SHA256_HEX = /^[a-f0-9]{64}$/i;
const UTC_ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/;
const REVISION = /^R(\d+)$/;

export interface ControlledReissueMetadataIssue {
  id: string;
  action: string;
  missingFields: string[];
  invalidFields: string[];
}

export interface ControlledReissueAuditVerification {
  ok: boolean;
  hashChain: AuditChainVerification;
  approvalErrors: Array<"approvals_below_minimum" | "approvers_not_distinct">;
  missingActions: Array<typeof REISSUE_ACTION | typeof NOTIFICATION_ACTION>;
  sequenceErrors: Array<"notification_must_follow_reissue">;
  invalidEntries: ControlledReissueMetadataIssue[];
}

export function verifyControlledReissueAuditTrail(
  entries: AuditChainEntry[],
): ControlledReissueAuditVerification {
  const hashChain = verifyAuditHashChain(entries);
  const invalidEntries: ControlledReissueMetadataIssue[] = [];
  const approvalActorsBeforeReissue: string[] = [];
  let reissueIndex = -1;
  let notificationIndex = -1;

  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index]!;
    const action = extractAction(entry.payload);

    if (action === APPROVAL_ACTION) {
      const metadata = readApprovalMetadata(entry.payload);
      const missingFields: string[] = [];
      const invalidFields: string[] = [];

      if (!isNonEmptyString(metadata.actorId)) missingFields.push("actorId");
      if (!isNonEmptyString(metadata.timestampUtc)) {
        missingFields.push("timestampUtc");
      } else if (!isUtcIsoTimestamp(metadata.timestampUtc)) {
        invalidFields.push("timestampUtc");
      }

      if (
        missingFields.length === 0 &&
        invalidFields.length === 0 &&
        reissueIndex === -1 &&
        isNonEmptyString(metadata.actorId)
      ) {
        approvalActorsBeforeReissue.push(metadata.actorId);
      }

      if (missingFields.length > 0 || invalidFields.length > 0) {
        invalidEntries.push({
          id: entry.id,
          action,
          missingFields,
          invalidFields,
        });
      }
    }

    if (action === REISSUE_ACTION) {
      if (reissueIndex === -1) reissueIndex = index;

      const metadata = readReissueMetadata(entry.payload);
      const missingFields: string[] = [];
      const invalidFields: string[] = [];

      if (!isNonEmptyString(metadata.previousCertificateHash)) {
        missingFields.push("previousCertificateHash");
      } else if (!SHA256_HEX.test(metadata.previousCertificateHash)) {
        invalidFields.push("previousCertificateHash");
      }

      if (!isNonEmptyString(metadata.previousRevision)) {
        missingFields.push("previousRevision");
      } else if (!isRevision(metadata.previousRevision)) {
        invalidFields.push("previousRevision");
      }

      if (!isNonEmptyString(metadata.newRevision)) {
        missingFields.push("newRevision");
      } else if (!isSequentialRevision(metadata.previousRevision, metadata.newRevision)) {
        invalidFields.push("newRevision");
      }

      if (missingFields.length > 0 || invalidFields.length > 0) {
        invalidEntries.push({
          id: entry.id,
          action,
          missingFields,
          invalidFields,
        });
      }
    }

    if (action === NOTIFICATION_ACTION) {
      if (notificationIndex === -1) notificationIndex = index;

      const metadata = readNotificationMetadata(entry.payload);
      const missingFields: string[] = [];
      const invalidFields: string[] = [];

      if (!isNonEmptyString(metadata.recipient)) missingFields.push("recipient");
      if (!isNonEmptyString(metadata.timestampUtc)) {
        missingFields.push("timestampUtc");
      } else if (!isUtcIsoTimestamp(metadata.timestampUtc)) {
        invalidFields.push("timestampUtc");
      }

      if (missingFields.length > 0 || invalidFields.length > 0) {
        invalidEntries.push({
          id: entry.id,
          action,
          missingFields,
          invalidFields,
        });
      }
    }
  }

  const missingActions: ControlledReissueAuditVerification["missingActions"] = [];
  if (reissueIndex === -1) missingActions.push(REISSUE_ACTION);
  if (notificationIndex === -1) missingActions.push(NOTIFICATION_ACTION);

  const approvalErrors: ControlledReissueAuditVerification["approvalErrors"] = [];
  if (reissueIndex !== -1) {
    if (approvalActorsBeforeReissue.length < 2) {
      approvalErrors.push("approvals_below_minimum");
    } else if (new Set(approvalActorsBeforeReissue).size < 2) {
      approvalErrors.push("approvers_not_distinct");
    }
  }

  const sequenceErrors: ControlledReissueAuditVerification["sequenceErrors"] = [];
  if (reissueIndex !== -1 && notificationIndex !== -1 && notificationIndex < reissueIndex) {
    sequenceErrors.push("notification_must_follow_reissue");
  }

  return {
    ok:
      hashChain.ok &&
      approvalErrors.length === 0 &&
      missingActions.length === 0 &&
      sequenceErrors.length === 0 &&
      invalidEntries.length === 0,
    hashChain,
    approvalErrors,
    missingActions,
    sequenceErrors,
    invalidEntries,
  };
}

function extractAction(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") return undefined;
  const action = (payload as { action?: unknown }).action;
  return typeof action === "string" ? action : undefined;
}

function readApprovalMetadata(payload: unknown): { actorId?: string; timestampUtc?: string } {
  if (!payload || typeof payload !== "object") return {};
  const typedPayload = payload as Record<string, unknown>;

  return {
    actorId: typeof typedPayload.actorId === "string" ? typedPayload.actorId : undefined,
    timestampUtc: typeof typedPayload.timestampUtc === "string" ? typedPayload.timestampUtc : undefined,
  };
}

function readReissueMetadata(payload: unknown): {
  previousCertificateHash?: string;
  previousRevision?: string;
  newRevision?: string;
} {
  if (!payload || typeof payload !== "object") return {};
  const typedPayload = payload as Record<string, unknown>;

  return {
    previousCertificateHash:
      typeof typedPayload.previousCertificateHash === "string" ? typedPayload.previousCertificateHash : undefined,
    previousRevision: typeof typedPayload.previousRevision === "string" ? typedPayload.previousRevision : undefined,
    newRevision: typeof typedPayload.newRevision === "string" ? typedPayload.newRevision : undefined,
  };
}

function readNotificationMetadata(payload: unknown): { recipient?: string; timestampUtc?: string } {
  if (!payload || typeof payload !== "object") return {};
  const typedPayload = payload as Record<string, unknown>;

  return {
    recipient: typeof typedPayload.recipient === "string" ? typedPayload.recipient : undefined,
    timestampUtc: typeof typedPayload.timestampUtc === "string" ? typedPayload.timestampUtc : undefined,
  };
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isUtcIsoTimestamp(value: string): boolean {
  if (!UTC_ISO_TIMESTAMP.test(value)) return false;
  return Number.isFinite(Date.parse(value));
}

function isRevision(value: string): boolean {
  return REVISION.test(value);
}

function isSequentialRevision(previousRevision: unknown, newRevision: string): boolean {
  if (typeof previousRevision !== "string") return false;

  const previousMatch = previousRevision.match(REVISION);
  const nextMatch = newRevision.match(REVISION);
  if (!previousMatch || !nextMatch) return false;

  return Number(nextMatch[1]) === Number(previousMatch[1]) + 1;
}
