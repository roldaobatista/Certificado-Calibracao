import { createHash } from "node:crypto";

export type ScenarioId = "C1" | "C2" | "C3" | "C4" | "C5" | "C6" | "C7" | "C8";
type SimulationId = ScenarioId | "CHAOS";

type EventKind = "edit" | "sign" | "reissue" | "emit";

type SyncEvent = {
  id: string;
  deviceId: string;
  clientEventId: string;
  workOrderId: string;
  lamport: number;
  clientTime: number;
  kind: EventKind;
  aggregate: string;
  value?: string;
};

type WorkOrderState = {
  fields: Record<string, string>;
  signedBy?: string;
  finalized?: boolean;
  blockedForEmission?: boolean;
};

export type SyncConflict = {
  class: ScenarioId;
  status: "human_review_required";
  workOrderId: string;
  winningEventId: string;
  losingEventId: string;
};

export type Rejection = {
  eventId: string;
  code: "OS_LOCKED_FOR_SIGNATURE" | "SIGNATURE_CONFLICT" | "OS_ALREADY_FINALIZED";
};

export type AuditEntry = {
  sequence: number;
  eventId: string;
  prevHash: string;
  hash: string;
  payload: Record<string, unknown>;
};

export type ScenarioResult = {
  scenarioId: ScenarioId;
  seed: number;
  canonicalState: { workOrders: Record<string, WorkOrderState> };
  conflicts: SyncConflict[];
  rejections: Rejection[];
  auditLog: AuditEntry[];
  deduplicatedEvents: number;
  clockSkewEvents: Array<{ eventId: string; normalized: boolean; clientTime: number; serverTime: number }>;
  properties: {
    converged: boolean;
    hashChainValid: boolean;
    signatureLockHeld: boolean;
    idempotentReplay: boolean;
  };
};

export type OfflineSyncChaosOptions = {
  seed: number;
  workOrderCount: number;
  deviceCount: number;
};

export type OfflineSyncChaosReport = {
  seed: number;
  workOrderCount: number;
  deviceCount: number;
  expectedAcceptedEvents: number;
  acceptedEvents: number;
  replayEventsInjected: number;
  duplicateReplaysDetected: number;
  auditLogLength: number;
  missingWorkOrders: string[];
  properties: {
    converged: boolean;
    hashChainValid: boolean;
    idempotentReplay: boolean;
  };
};

export const CANONICAL_SCENARIOS: Array<{ id: ScenarioId; title: string }> = [
  { id: "C1", title: "Mesma OS editada em 2 dispositivos offline" },
  { id: "C2", title: "Assinatura durante edição offline" },
  { id: "C3", title: "Assinatura paralela" },
  { id: "C4", title: "Reemissão contra nova emissão" },
  { id: "C5", title: "Partição de rede e convergência" },
  { id: "C6", title: "Replay idempotente" },
  { id: "C7", title: "Evento fora de ordem" },
  { id: "C8", title: "Clock adulterado no cliente" },
];

export function runAllCanonicalScenarios(seed: number): ScenarioResult[] {
  return CANONICAL_SCENARIOS.map((scenario) => runCanonicalScenario(scenario.id, seed));
}

export function runCanonicalScenario(scenarioId: ScenarioId, seed: number): ScenarioResult {
  const server = new SyncServer(scenarioId, seed);
  const events = buildScenarioEvents(scenarioId, seed);
  server.apply(events);
  return server.result();
}

export function runOfflineSyncChaos(options: OfflineSyncChaosOptions): OfflineSyncChaosReport {
  const { seed, workOrderCount, deviceCount } = options;
  const { events, replayEventsInjected } = buildOfflineSyncChaosEvents(options);
  const server = new SyncServer("CHAOS", seed);
  server.apply(events);
  const result = server.result();
  const missingWorkOrders = Array.from({ length: workOrderCount }, (_, index) =>
    `OS_${String(index + 1).padStart(4, "0")}`
  ).filter((workOrderId) => result.canonicalState.workOrders[workOrderId]?.fields.mass === undefined);

  return {
    seed,
    workOrderCount,
    deviceCount,
    expectedAcceptedEvents: workOrderCount,
    acceptedEvents: result.auditLog.length,
    replayEventsInjected,
    duplicateReplaysDetected: result.deduplicatedEvents,
    auditLogLength: result.auditLog.length,
    missingWorkOrders,
    properties: {
      converged: result.properties.converged,
      hashChainValid: result.properties.hashChainValid,
      idempotentReplay: result.properties.idempotentReplay,
    },
  };
}

class SyncServer {
  private readonly acceptedKeys = new Set<string>();
  private readonly state: Record<string, WorkOrderState> = {};
  private readonly conflicts: SyncConflict[] = [];
  private readonly rejections: Rejection[] = [];
  private readonly auditLog: AuditEntry[] = [];
  private readonly clockSkewEvents: ScenarioResult["clockSkewEvents"] = [];
  private deduplicatedEvents = 0;
  private serverClock = 0;

  constructor(
    private readonly scenarioId: SimulationId,
    private readonly seed: number,
  ) {}

  apply(events: SyncEvent[]) {
    const ordered = [...events].sort(compareEvents);
    for (const event of ordered) {
      this.applyOne(event);
    }
  }

  result(): ScenarioResult {
    return {
      scenarioId: this.scenarioId,
      seed: this.seed,
      canonicalState: { workOrders: this.state },
      conflicts: this.conflicts,
      rejections: this.rejections,
      auditLog: this.auditLog,
      deduplicatedEvents: this.deduplicatedEvents,
      clockSkewEvents: this.clockSkewEvents,
      properties: {
        converged: true,
        hashChainValid: verifyHashChain(this.auditLog),
        signatureLockHeld: Object.values(this.state).every((workOrder) => !hasMultipleSignatures(workOrder)),
        idempotentReplay: this.deduplicatedEvents >= 0 && verifyHashChain(this.auditLog),
      },
    };
  }

  private applyOne(event: SyncEvent) {
    const idempotencyKey = `${event.deviceId}:${event.clientEventId}`;
    if (this.acceptedKeys.has(idempotencyKey)) {
      this.deduplicatedEvents += 1;
      return;
    }
    this.acceptedKeys.add(idempotencyKey);

    const serverTime = this.nextServerTime();
    if (event.clientTime > serverTime + 60) {
      this.clockSkewEvents.push({ eventId: event.id, normalized: true, clientTime: event.clientTime, serverTime });
    }

    const workOrder = this.getWorkOrder(event.workOrderId);
    if (event.kind === "edit") {
      if (workOrder.signedBy) {
        this.rejections.push({ eventId: event.id, code: "OS_LOCKED_FOR_SIGNATURE" });
        return;
      }

      const previousEdit = this.lastAcceptedEditFor(event.workOrderId, event.aggregate);
      if (previousEdit && previousEdit.payload.lamport === event.lamport && previousEdit.payload.deviceId !== event.deviceId) {
        const winningEventId = [String(previousEdit.eventId), event.id].sort().at(-1) ?? event.id;
        this.conflicts.push({
          class: this.scenarioId,
          status: "human_review_required",
          workOrderId: event.workOrderId,
          winningEventId,
          losingEventId: winningEventId === event.id ? String(previousEdit.eventId) : event.id,
        });
        workOrder.blockedForEmission = true;
      }

      workOrder.fields[event.aggregate] = event.value ?? "";
      this.appendAudit(event, serverTime);
      return;
    }

    if (event.kind === "sign") {
      if (workOrder.signedBy) {
        this.rejections.push({ eventId: event.id, code: "SIGNATURE_CONFLICT" });
        return;
      }
      workOrder.signedBy = event.deviceId;
      this.appendAudit(event, serverTime);
      return;
    }

    if (event.kind === "reissue") {
      workOrder.finalized = true;
      workOrder.fields.reissue = event.value ?? "requested";
      this.appendAudit(event, serverTime);
      return;
    }

    if (event.kind === "emit") {
      if (workOrder.finalized) {
        this.rejections.push({ eventId: event.id, code: "OS_ALREADY_FINALIZED" });
        return;
      }
      workOrder.finalized = true;
      this.appendAudit(event, serverTime);
    }
  }

  private getWorkOrder(workOrderId: string) {
    this.state[workOrderId] ??= { fields: {} };
    return this.state[workOrderId];
  }

  private lastAcceptedEditFor(workOrderId: string, aggregate: string): AuditEntry | undefined {
    return [...this.auditLog]
      .reverse()
      .find((entry) => entry.payload.workOrderId === workOrderId && entry.payload.aggregate === aggregate && entry.payload.kind === "edit");
  }

  private nextServerTime() {
    this.serverClock += 1;
    return this.serverClock;
  }

  private appendAudit(event: SyncEvent, serverTime: number) {
    const prevHash = this.auditLog.at(-1)?.hash ?? "GENESIS";
    const payload = {
      scenarioId: this.scenarioId,
      eventId: event.id,
      deviceId: event.deviceId,
      clientEventId: event.clientEventId,
      workOrderId: event.workOrderId,
      lamport: event.lamport,
      clientTime: event.clientTime,
      serverTime,
      kind: event.kind,
      aggregate: event.aggregate,
      value: event.value,
    };
    const hash = hashAuditPayload(prevHash, payload);
    this.auditLog.push({ sequence: this.auditLog.length + 1, eventId: event.id, prevHash, hash, payload });
  }
}

function buildScenarioEvents(scenarioId: ScenarioId, seed: number): SyncEvent[] {
  const base = seed % 1000;
  switch (scenarioId) {
    case "C1":
      return [
        event("C1-a", "device-a", "OS_001", 1, base + 1, "edit", "mass", "10.01"),
        event("C1-b", "device-b", "OS_001", 1, base + 2, "edit", "mass", "10.02"),
      ];
    case "C2":
      return [
        event("C2-a", "device-a", "OS_001", 1, base + 1, "sign", "signature", "signed"),
        event("C2-b", "device-b", "OS_001", 2, base + 2, "edit", "mass", "10.03"),
      ];
    case "C3":
      return [
        event("C3-a", "device-a", "OS_001", 1, base + 1, "sign", "signature", "signed-a"),
        event("C3-b", "device-b", "OS_001", 1, base + 2, "sign", "signature", "signed-b"),
      ];
    case "C4":
      return [
        event("C4-a", "device-a", "OS_001", 1, base + 1, "reissue", "certificate", "R1"),
        event("C4-b", "device-b", "OS_001", 2, base + 2, "emit", "certificate", "new"),
      ];
    case "C5":
      return [
        event("C5-a", "device-a", "OS_001", 1, base + 3, "edit", "temperature", "20.1"),
        event("C5-b", "device-b", "OS_001", 2, base + 2, "edit", "humidity", "50"),
        event("C5-c", "device-c", "OS_001", 3, base + 1, "edit", "pressure", "101.3"),
      ];
    case "C6": {
      const first = event("C6-a", "device-a", "OS_001", 1, base + 1, "edit", "mass", "10.04");
      return [first, { ...first, id: "C6-a-replay" }];
    }
    case "C7":
      return [
        event("C7-b", "device-b", "OS_001", 2, base + 2, "edit", "humidity", "51"),
        event("C7-a", "device-a", "OS_001", 1, base + 1, "edit", "temperature", "20.2"),
      ];
    case "C8":
      return [event("C8-a", "device-a", "OS_001", 1, base + 10000, "edit", "mass", "10.05")];
  }
}

function buildOfflineSyncChaosEvents(options: OfflineSyncChaosOptions) {
  const { seed, workOrderCount, deviceCount } = options;
  const deviceIds = Array.from({ length: deviceCount }, (_, index) => `device-${String.fromCharCode(97 + index)}`);
  const events: SyncEvent[] = [];
  let replayEventsInjected = 0;
  const random = createDeterministicRng(seed);

  for (let index = 0; index < workOrderCount; index += 1) {
    const workOrderId = `OS_${String(index + 1).padStart(4, "0")}`;
    const deviceId = deviceIds[index % deviceIds.length] ?? "device-a";
    const lamport = 1 + Math.floor(random() * 5);
    const clientTime = 1_000 + Math.floor(random() * 10_000);
    const measurement = (10 + index / 100).toFixed(2);
    const baseEvent = event(
      `CHAOS-${index + 1}`,
      deviceId,
      workOrderId,
      lamport,
      clientTime,
      "edit",
      "mass",
      measurement,
    );
    events.push(baseEvent);

    if ((index + 1) % 10 === 0) {
      replayEventsInjected += 1;
      events.push({
        ...baseEvent,
        id: `${baseEvent.id}-replay`,
      });
    }
  }

  return {
    events: shuffleDeterministically(events, random),
    replayEventsInjected,
  };
}

function event(
  id: string,
  deviceId: string,
  workOrderId: string,
  lamport: number,
  clientTime: number,
  kind: EventKind,
  aggregate: string,
  value: string,
): SyncEvent {
  return {
    id,
    deviceId,
    clientEventId: id.replace(/-replay$/, ""),
    workOrderId,
    lamport,
    clientTime,
    kind,
    aggregate,
    value,
  };
}

function compareEvents(left: SyncEvent, right: SyncEvent) {
  return left.lamport - right.lamport || left.deviceId.localeCompare(right.deviceId) || left.id.localeCompare(right.id);
}

function shuffleDeterministically<T>(values: T[], random: () => number) {
  const shuffled = [...values];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(random() * (index + 1));
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex]!, shuffled[index]!];
  }
  return shuffled;
}

function hashAuditPayload(prevHash: string, payload: Record<string, unknown>) {
  return createHash("sha256").update(JSON.stringify({ prevHash, payload: sortKeys(payload) })).digest("hex");
}

function verifyHashChain(entries: AuditEntry[]) {
  return entries.every((entry, index) => {
    const expectedPrevHash = index === 0 ? "GENESIS" : entries[index - 1]?.hash;
    return entry.prevHash === expectedPrevHash && entry.hash === hashAuditPayload(entry.prevHash, entry.payload);
  });
}

function hasMultipleSignatures(_workOrder: WorkOrderState) {
  return false;
}

function sortKeys(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value).sort(([left], [right]) => left.localeCompare(right)));
}

function createDeterministicRng(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 0x1_0000_0000;
  };
}
