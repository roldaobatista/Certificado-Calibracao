import {
  offlineCertificateDraftSchema,
  type OfflineCertificateDraft,
} from "../../../packages/contracts/src/mobile-offline-calibration.js";
import {
  offlineSyncEnvelopeSchema,
  offlineSyncOutboxItemSchema,
  type OfflineSyncConflictClass,
  type OfflineSyncEnvelope,
  type OfflineSyncEnvelopeState,
  type OfflineSyncEventKind,
  type OfflineSyncOutboxItem,
} from "../../../packages/contracts/src/offline-sync.js";

export interface OfflineSyncEventInput {
  eventId: string;
  clientEventId: string;
  aggregateLabel: string;
  eventKind: OfflineSyncEventKind;
  lamport: number;
  payloadDigest: string;
  state: OfflineSyncEnvelopeState;
  replayProtected: boolean;
}

export interface BuildOfflineSyncOutboxInput {
  draft: OfflineCertificateDraft;
  workOrderNumber: string;
  deviceId: string;
  deviceLabel: string;
  networkState: "offline" | "online" | "unstable";
  queuedAtLabel: string;
  lastAttemptLabel: string;
  storageProtected: boolean;
  deviceKeyDerived: boolean;
  events: OfflineSyncEventInput[];
  pendingConflictClass?: OfflineSyncConflictClass;
}

export interface BuildOfflineSyncOutboxResult {
  ok: boolean;
  reason?:
    | "invalid_draft"
    | "invalid_storage"
    | "invalid_events"
    | "missing_replay_protection";
  item?: OfflineSyncOutboxItem;
}

export function buildOfflineSyncOutboxItem(
  input: BuildOfflineSyncOutboxInput,
): BuildOfflineSyncOutboxResult {
  const parsedDraft = offlineCertificateDraftSchema.safeParse(input.draft);
  if (!parsedDraft.success) {
    return { ok: false, reason: "invalid_draft" };
  }

  if (!input.storageProtected || !input.deviceKeyDerived) {
    return { ok: false, reason: "invalid_storage" };
  }

  const envelopes = parseEnvelopes(input.events);
  if (!envelopes) {
    return { ok: false, reason: "invalid_events" };
  }

  if (envelopes.length === 0 || envelopes.some((event) => !event.replayProtected)) {
    return { ok: false, reason: "missing_replay_protection" };
  }

  const status = resolveOutboxStatus(input, envelopes);
  const blockers = buildOutboxBlockers(input, envelopes);
  const warnings = buildOutboxWarnings(input, envelopes);

  const item = offlineSyncOutboxItemSchema.parse({
    itemId: `${parsedDraft.data.sessionId}-outbox`,
    sessionId: parsedDraft.data.sessionId,
    workOrderId: parsedDraft.data.workOrderId,
    workOrderNumber: input.workOrderNumber,
    deviceId: input.deviceId,
    deviceLabel: input.deviceLabel,
    certificateNumber: parsedDraft.data.certificateNumber,
    status,
    networkLabel: buildNetworkLabel(input.networkState),
    storageLabel: "SQLCipher ativo com chave derivada por device.",
    queuedAtLabel: input.queuedAtLabel,
    lastAttemptLabel: input.lastAttemptLabel,
    eventCount: envelopes.length,
    replayProtectedCount: envelopes.filter((event) => event.replayProtected).length,
    nextActionLabel: buildNextActionLabel(input, envelopes),
    pendingConflictClass: input.pendingConflictClass,
    blockers,
    warnings,
    envelopes,
  });

  return {
    ok: true,
    item,
  };
}

function parseEnvelopes(events: OfflineSyncEventInput[]): OfflineSyncEnvelope[] | null {
  if (events.length === 0) {
    return null;
  }

  const parsed = events.map((event) => offlineSyncEnvelopeSchema.safeParse(event));
  if (parsed.some((result) => !result.success)) {
    return null;
  }

  return parsed.map((result) => result.data);
}

function resolveOutboxStatus(
  input: BuildOfflineSyncOutboxInput,
  envelopes: OfflineSyncEnvelope[],
): OfflineSyncOutboxItem["status"] {
  if (input.pendingConflictClass === "C4" || input.pendingConflictClass === "C2" || input.pendingConflictClass === "C3") {
    return "blocked";
  }

  if (input.pendingConflictClass) {
    return "attention";
  }

  if (envelopes.some((event) => event.state === "rejected")) {
    return "blocked";
  }

  if (input.networkState !== "online" || envelopes.some((event) => event.state === "queued")) {
    return "attention";
  }

  return "ready";
}

function buildOutboxBlockers(
  input: BuildOfflineSyncOutboxInput,
  envelopes: OfflineSyncEnvelope[],
): string[] {
  const blockers: string[] = [];

  if (input.pendingConflictClass) {
    blockers.push(
      `OS ${input.workOrderNumber} bloqueada para emissao enquanto o conflito ${input.pendingConflictClass} permanecer aberto.`,
    );
  }

  if (envelopes.some((event) => event.state === "rejected")) {
    blockers.push("Existe evento rejeitado pelo servidor e o lote nao pode ser reenviado automaticamente.");
  }

  return blockers;
}

function buildOutboxWarnings(
  input: BuildOfflineSyncOutboxInput,
  envelopes: OfflineSyncEnvelope[],
): string[] {
  const warnings: string[] = [];

  if (input.networkState === "offline") {
    warnings.push("Upload ainda depende de restabelecimento de rede.");
  }

  if (input.networkState === "unstable") {
    warnings.push("A conectividade esta instavel e pode reordenar tentativas de upload.");
  }

  if (envelopes.some((event) => event.state === "queued")) {
    warnings.push("Ainda existem eventos aguardando envio canonico.");
  }

  if (envelopes.some((event) => event.state === "deduplicated")) {
    warnings.push("Replay deduplicado preservado para auditoria do sync.");
  }

  return warnings;
}

function buildNextActionLabel(
  input: BuildOfflineSyncOutboxInput,
  envelopes: OfflineSyncEnvelope[],
): string {
  if (input.pendingConflictClass === "C4") {
    return "Escalar para parecer regulatorio antes de liberar nova emissao ou reemissao.";
  }

  if (input.pendingConflictClass) {
    return "Abrir a triagem humana da OS antes de liberar a emissao.";
  }

  if (envelopes.some((event) => event.state === "rejected")) {
    return "Investigar o evento rejeitado antes de uma nova tentativa de upload.";
  }

  if (input.networkState !== "online" || envelopes.some((event) => event.state === "queued")) {
    return "Aguardar rede estavel para reenfileirar a outbox.";
  }

  return "Acompanhar a confirmacao final do servidor e arquivar o trace do sync.";
}

function buildNetworkLabel(state: BuildOfflineSyncOutboxInput["networkState"]): string {
  switch (state) {
    case "offline":
      return "Sem conectividade; lote permanece somente no device.";
    case "unstable":
      return "Rede intermitente com replays controlados por idempotencia.";
    case "online":
      return "Rede online e apta para upload canonico.";
  }
}
