import { verifyAuditHashChain, type AuditChainEntry, type AuditChainVerification } from "./verify.js";

const DEFAULT_REQUIRED_ACTIONS = [
  "calibration.executed",
  "technical_review.completed",
  "certificate.signed",
  "certificate.emitted",
] as const;

export type CriticalAuditTrailVerification = {
  ok: boolean;
  hashChain: AuditChainVerification;
  missingActions: string[];
};

export function verifyCriticalEventAuditTrail(
  entries: AuditChainEntry[],
  options: { requireReissue?: boolean } = {},
): CriticalAuditTrailVerification {
  const hashChain = verifyAuditHashChain(entries);
  const requiredActions = options.requireReissue
    ? [...DEFAULT_REQUIRED_ACTIONS, "certificate.reissued"]
    : [...DEFAULT_REQUIRED_ACTIONS];

  const presentActions = new Set(
    entries
      .map((entry) => extractAction(entry.payload))
      .filter((action): action is string => typeof action === "string"),
  );

  const missingActions = requiredActions.filter((action) => !presentActions.has(action));

  return {
    ok: hashChain.ok && missingActions.length === 0,
    hashChain,
    missingActions,
  };
}

function extractAction(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") {
    return undefined;
  }

  const maybeAction = (payload as { action?: unknown }).action;
  return typeof maybeAction === "string" ? maybeAction : undefined;
}
