import { type AuditChainEntry, type AuditChainVerification, verifyAuditHashChain } from "./verify.js";

const REQUIRED_ACTIONS = ["technical_review.completed", "certificate.signed"] as const;
const UTC_ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/;

type RequiredAction = (typeof REQUIRED_ACTIONS)[number];

export interface ReviewSignatureMetadataIssue {
  id: string;
  action: RequiredAction;
  missingFields: Array<"actorId" | "timestampUtc" | "deviceId">;
  invalidFields: Array<"timestampUtc">;
}

export interface ReviewSignatureAuditVerification {
  ok: boolean;
  hashChain: AuditChainVerification;
  missingActions: RequiredAction[];
  invalidEntries: ReviewSignatureMetadataIssue[];
}

export function verifyTechnicalReviewSignatureAudit(
  entries: AuditChainEntry[],
): ReviewSignatureAuditVerification {
  const hashChain = verifyAuditHashChain(entries);
  const presentActions = new Set<RequiredAction>();
  const invalidEntries: ReviewSignatureMetadataIssue[] = [];

  for (const entry of entries) {
    const action = extractRequiredAction(entry.payload);
    if (!action) continue;

    presentActions.add(action);

    const metadata = extractMetadata(entry.payload);
    const missingFields: ReviewSignatureMetadataIssue["missingFields"] = [];
    const invalidFields: ReviewSignatureMetadataIssue["invalidFields"] = [];

    if (!isNonEmptyString(metadata.actorId)) missingFields.push("actorId");
    if (!isNonEmptyString(metadata.deviceId)) missingFields.push("deviceId");
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

  const missingActions = REQUIRED_ACTIONS.filter((action) => !presentActions.has(action));

  return {
    ok: hashChain.ok && missingActions.length === 0 && invalidEntries.length === 0,
    hashChain,
    missingActions,
    invalidEntries,
  };
}

function extractRequiredAction(payload: unknown): RequiredAction | undefined {
  if (!payload || typeof payload !== "object") return undefined;

  const action = (payload as { action?: unknown }).action;
  return REQUIRED_ACTIONS.find((candidate) => candidate === action);
}

function extractMetadata(payload: unknown): {
  actorId?: unknown;
  timestampUtc?: unknown;
  deviceId?: unknown;
} {
  if (!payload || typeof payload !== "object") return {};
  const typedPayload = payload as Record<string, unknown>;

  return {
    actorId: typedPayload.actorId,
    timestampUtc: typedPayload.timestampUtc,
    deviceId: typedPayload.deviceId,
  };
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isUtcIsoTimestamp(value: string): boolean {
  if (!UTC_ISO_TIMESTAMP.test(value)) return false;

  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp);
}
