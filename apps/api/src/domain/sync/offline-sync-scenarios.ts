import type {
  OfflineSyncCatalog,
  OfflineSyncConflictDetail,
  OfflineSyncConflictQueueItem,
  OfflineSyncOutboxItem,
  OfflineSyncScenario,
  OfflineSyncScenarioId,
  OfflineSyncSummary,
} from "@afere/contracts";

type ScenarioDefinition = {
  label: string;
  description: string;
  summary: OfflineSyncSummary;
  selectedOutboxItemId: string;
  selectedConflictId: string;
  outboxItems: OfflineSyncOutboxItem[];
  conflicts: OfflineSyncConflictQueueItem[];
  details: Record<string, OfflineSyncConflictDetail>;
};

const SCENARIOS: Record<OfflineSyncScenarioId, ScenarioDefinition> = {
  "stable-upload": {
    label: "Upload convergente sem conflito aberto",
    description:
      "A outbox principal convergiu apos particao de rede e o registro residual foi mantido apenas para rastreabilidade.",
    summary: {
      status: "ready",
      headline: "Sync convergente com trilha auditavel preservada",
      queuedDevices: 2,
      queuedItems: 1,
      openConflictCount: 0,
      escalatedConflictCount: 0,
      blockedWorkOrders: 0,
      resolvedLast24h: 1,
      recommendedAction: "Arquivar a resolucao automatica e seguir monitorando a drenagem do lote residual.",
      blockers: [],
      warnings: ["Um lote residual ainda aguarda ACK final do servidor para arquivamento."],
    },
    selectedOutboxItemId: "sync-os-2026-0042",
    selectedConflictId: "conflict-c5-0042",
    outboxItems: [
      {
        itemId: "sync-os-2026-0042",
        sessionId: "session-android-0042",
        workOrderId: "os-2026-0042",
        workOrderNumber: "OS-2026-0042",
        deviceId: "device-field-01",
        deviceLabel: "Android campo 01",
        certificateNumber: "AFR-000201",
        status: "ready",
        networkLabel: "Rede restaurada e lote apto para upload canonico.",
        storageLabel: "SQLCipher ativo com chave derivada por device.",
        queuedAtLabel: "22/04 08:15",
        lastAttemptLabel: "22/04 08:21",
        eventCount: 3,
        replayProtectedCount: 3,
        nextActionLabel: "Aguardar o ACK final do servidor e arquivar o trace do sync.",
        blockers: [],
        warnings: ["Um replay idempotente foi deduplicado e permanece visivel para auditoria."],
        envelopes: [
          {
            eventId: "evt-c5-0042-a",
            clientEventId: "evt-c5-0042-a",
            aggregateLabel: "temperatura",
            eventKind: "edit",
            lamport: 1,
            payloadDigest: "sha256:evt-c5-0042-a",
            state: "uploaded",
            replayProtected: true,
          },
          {
            eventId: "evt-c5-0042-b",
            clientEventId: "evt-c5-0042-b",
            aggregateLabel: "umidade",
            eventKind: "edit",
            lamport: 2,
            payloadDigest: "sha256:evt-c5-0042-b",
            state: "uploaded",
            replayProtected: true,
          },
          {
            eventId: "evt-c6-0042-replay",
            clientEventId: "evt-c6-0042",
            aggregateLabel: "pressao",
            eventKind: "edit",
            lamport: 3,
            payloadDigest: "sha256:evt-c6-0042",
            state: "deduplicated",
            replayProtected: true,
          },
        ],
      },
    ],
    conflicts: [
      {
        conflictId: "conflict-c5-0042",
        workOrderId: "os-2026-0042",
        workOrderNumber: "OS-2026-0042",
        class: "C5",
        status: "resolved",
        openedAtLabel: "22/04 08:16",
        deadlineLabel: "Arquivado em 22/04 08:19",
        responsibleLabel: "Servidor canonico",
        summaryLabel: "Particao de rede convergiu por Lamport + device_id sem perda de evento.",
        recommendedAction: "Arquivar a resolucao.",
        blockingScopeLabel: "Sem bloqueio ativo para emissao.",
      },
    ],
    details: {
      "conflict-c5-0042": {
        conflictId: "conflict-c5-0042",
        title: "OS-2026-0042 · convergencia automatica do sync",
        status: "resolved",
        class: "C5",
        summary:
          "Os tres dispositivos convergiram de forma deterministica e o lote foi mantido apenas como registro auditavel da auto-resolucao.",
        decisionDeadlineLabel: "Arquivado em 22/04 08:19",
        responsibleLabel: "Servidor canonico",
        queueSlaLabel: "Convergencia automatica registrada antes de qualquer bloqueio de SLA.",
        winningEventId: "evt-c5-0042-b",
        blockedForEmission: false,
        regulatorEscalationRequired: false,
        recommendedDecisionLabel: "Arquivar a resolucao automatica e manter o trace para auditoria.",
        rationaleTemplate:
          "Convergencia C5 confirmada por Lamport + device_id; nenhuma perda, duplicata aceita ou drift semantico detectado.",
        resolutionOptions: [
          {
            action: "archive_resolution",
            label: "Arquivar resolucao",
            detail: "Manter apenas o trace canonico como evidencia da auto-resolucao do sync.",
            allowed: true,
          },
        ],
        auditRequirements: [
          "Registrar seed e classe do conflito no dossie.",
          "Manter hash dos envelopes aceitos e deduplicados.",
          "Anexar justificativa curta de auto-resolucao para rastreabilidade.",
        ],
        blockers: [],
        warnings: ["Conflito mantido apenas por trilha historica e nao exige acao humana."],
        links: {
          workspaceScenarioId: "baseline-ready",
          serviceOrderScenarioId: "review-ready",
          auditTrailScenarioId: "recent-emission",
        },
      },
    },
  },
  "human-review-open": {
    label: "Conflito humano aberto bloqueando emissao",
    description:
      "Dois dispositivos editaram a mesma OS offline e o backend preservou o conflito em fila humana antes de liberar qualquer emissao.",
    summary: {
      status: "attention",
      headline: "Triagem humana pendente para liberar a OS",
      queuedDevices: 2,
      queuedItems: 2,
      openConflictCount: 1,
      escalatedConflictCount: 0,
      blockedWorkOrders: 1,
      resolvedLast24h: 0,
      recommendedAction: "Triar o conflito C1 em ate 24h uteis e registrar o evento vencedor com justificativa.",
      blockers: ["OS-2026-0047 bloqueada para emissao ate a decisao humana da fila de sync."],
      warnings: ["Enquanto o conflito permanecer aberto, o lote continua somente como rascunho auditavel."],
    },
    selectedOutboxItemId: "sync-os-2026-0047",
    selectedConflictId: "conflict-c1-0047",
    outboxItems: [
      {
        itemId: "sync-os-2026-0047",
        sessionId: "session-android-0047",
        workOrderId: "os-2026-0047",
        workOrderNumber: "OS-2026-0047",
        deviceId: "device-field-02",
        deviceLabel: "Android campo 02",
        certificateNumber: "AFR-000247",
        status: "attention",
        networkLabel: "Rede online, mas lote retido por conflito aberto.",
        storageLabel: "SQLCipher ativo com chave derivada por device.",
        queuedAtLabel: "22/04 09:02",
        lastAttemptLabel: "22/04 09:08",
        eventCount: 2,
        replayProtectedCount: 2,
        nextActionLabel: "Abrir a triagem humana e decidir o evento vencedor antes da emissao.",
        pendingConflictClass: "C1",
        blockers: ["A OS nao pode emitir enquanto a decisao humana nao for registrada em audit log."],
        warnings: ["A diferenca entre os valores de massa precisa ser justificada pelo responsavel tecnico."],
        envelopes: [
          {
            eventId: "evt-c1-0047-a",
            clientEventId: "evt-c1-0047-a",
            aggregateLabel: "massa",
            eventKind: "edit",
            lamport: 1,
            payloadDigest: "sha256:evt-c1-0047-a",
            state: "uploaded",
            replayProtected: true,
          },
          {
            eventId: "evt-c1-0047-b",
            clientEventId: "evt-c1-0047-b",
            aggregateLabel: "massa",
            eventKind: "edit",
            lamport: 1,
            payloadDigest: "sha256:evt-c1-0047-b",
            state: "uploaded",
            replayProtected: true,
          },
        ],
      },
      {
        itemId: "sync-os-2026-0048",
        sessionId: "session-android-0048",
        workOrderId: "os-2026-0048",
        workOrderNumber: "OS-2026-0048",
        deviceId: "device-field-03",
        deviceLabel: "Android campo 03",
        certificateNumber: "AFR-000248",
        status: "ready",
        networkLabel: "Rede online e lote apto para confirmacao final.",
        storageLabel: "SQLCipher ativo com chave derivada por device.",
        queuedAtLabel: "22/04 09:11",
        lastAttemptLabel: "22/04 09:13",
        eventCount: 1,
        replayProtectedCount: 1,
        nextActionLabel: "Acompanhar ACK final do servidor.",
        blockers: [],
        warnings: [],
        envelopes: [
          {
            eventId: "evt-c5-0048-a",
            clientEventId: "evt-c5-0048-a",
            aggregateLabel: "temperatura",
            eventKind: "edit",
            lamport: 1,
            payloadDigest: "sha256:evt-c5-0048-a",
            state: "uploaded",
            replayProtected: true,
          },
        ],
      },
    ],
    conflicts: [
      {
        conflictId: "conflict-c1-0047",
        workOrderId: "os-2026-0047",
        workOrderNumber: "OS-2026-0047",
        class: "C1",
        status: "open",
        openedAtLabel: "22/04 09:08",
        deadlineLabel: "Triagem inicial ate 23/04 09:08",
        responsibleLabel: "Renata Qualidade",
        summaryLabel: "Dois edits offline concorreram sobre o mesmo agregado de massa.",
        recommendedAction: "Comparar os eventos e registrar o vencedor.",
        blockingScopeLabel: "Bloqueia emissao da OS selecionada.",
      },
    ],
    details: {
      "conflict-c1-0047": {
        conflictId: "conflict-c1-0047",
        title: "OS-2026-0047 · conflito C1 aguardando triagem humana",
        status: "open",
        class: "C1",
        summary:
          "Os dispositivos `device-field-02` e `device-field-07` editaram o mesmo agregado com Lamport idêntico. O servidor preservou ambos os eventos e bloqueou a emissao ate a decisao humana.",
        decisionDeadlineLabel: "Triagem inicial ate 23/04 09:08",
        responsibleLabel: "Renata Qualidade",
        queueSlaLabel: "24h uteis para triagem inicial e 48h uteis para resolucao.",
        winningEventId: "evt-c1-0047-b",
        losingEventId: "evt-c1-0047-a",
        blockedForEmission: true,
        regulatorEscalationRequired: false,
        recommendedDecisionLabel: "Comparar a evidencia da massa e registrar o evento vencedor com justificativa.",
        rationaleTemplate:
          "Selecionar o evento vencedor com base na evidencia metrologica, registrar justificativa e manter o evento perdedor somente como trilha auditavel.",
        resolutionOptions: [
          {
            action: "accept_server_winner",
            label: "Manter vencedor do servidor",
            detail: "Aceitar o tiebreaker atual e arquivar o evento perdedor como evidencia.",
            allowed: true,
          },
          {
            action: "accept_device_winner",
            label: "Manter evento do device",
            detail: "Promover explicitamente o evento alternativo como vencedor com justificativa humana.",
            allowed: true,
          },
          {
            action: "merge_fields",
            label: "Mesclar por campos",
            detail: "Aplicar decisao manual por agregado sem perder a trilha dos dois envelopes.",
            allowed: true,
          },
          {
            action: "escalate_to_regulator",
            label: "Escalar para regulator",
            detail: "Usar apenas se a divergencia depender de interpretacao normativa e nao apenas tecnica.",
            allowed: false,
          },
        ],
        auditRequirements: [
          "Registrar `resolver_id`, timestamp e justificativa da decisao humana.",
          "Manter `winning_event_id` e `losing_event_id` no audit log.",
          "Anexar referencia cruzada para a OS bloqueada e para o trace do simulador.",
        ],
        blockers: ["A emissao da OS permanece bloqueada por arquitetura enquanto este conflito estiver aberto."],
        warnings: ["Padrao recorrente acima de 3 ocorrencias deve sugerir nova regra automatica no pacote normativo."],
        links: {
          workspaceScenarioId: "release-blocked",
          serviceOrderScenarioId: "review-blocked",
          auditTrailScenarioId: "recent-emission",
        },
      },
    },
  },
  "regulator-escalated": {
    label: "Conflito escalado por interpretacao regulatoria",
    description:
      "Uma tentativa de reemissao concorreu com nova emissao sobre OS finalizada, exigindo parecer regulatorio antes da decisao final.",
    summary: {
      status: "blocked",
      headline: "Sync retido em escala regulatoria",
      queuedDevices: 1,
      queuedItems: 1,
      openConflictCount: 0,
      escalatedConflictCount: 1,
      blockedWorkOrders: 1,
      resolvedLast24h: 0,
      recommendedAction: "Aguardar parecer regulatorio e manter a OS travada ate a decisao oficial.",
      blockers: ["OS-2026-0051 permanece sem emissao enquanto a disputa entre reemissao e nova emissao nao for resolvida."],
      warnings: ["O conflito toca reemissao controlada e preservacao de hash-chain, exigindo leitura normativa."],
    },
    selectedOutboxItemId: "sync-os-2026-0051",
    selectedConflictId: "conflict-c4-0051",
    outboxItems: [
      {
        itemId: "sync-os-2026-0051",
        sessionId: "session-android-0051",
        workOrderId: "os-2026-0051",
        workOrderNumber: "OS-2026-0051",
        deviceId: "device-field-05",
        deviceLabel: "Android campo 05",
        certificateNumber: "AFR-000251-R1",
        status: "blocked",
        networkLabel: "Rede online, mas lote travado por escala regulatoria.",
        storageLabel: "SQLCipher ativo com chave derivada por device.",
        queuedAtLabel: "22/04 10:01",
        lastAttemptLabel: "22/04 10:09",
        eventCount: 2,
        replayProtectedCount: 2,
        nextActionLabel: "Aguardar parecer regulatorio antes de reenfileirar reemissao ou nova emissao.",
        pendingConflictClass: "C4",
        blockers: ["Conflito C4 impede qualquer emissao ate parecer registrado em audit log."],
        warnings: ["A hash-chain do certificado original precisa permanecer verificavel independentemente da decisao."],
        envelopes: [
          {
            eventId: "evt-c4-0051-reissue",
            clientEventId: "evt-c4-0051-reissue",
            aggregateLabel: "certificado",
            eventKind: "reissue",
            lamport: 1,
            payloadDigest: "sha256:evt-c4-0051-reissue",
            state: "uploaded",
            replayProtected: true,
          },
          {
            eventId: "evt-c4-0051-emit",
            clientEventId: "evt-c4-0051-emit",
            aggregateLabel: "certificado",
            eventKind: "emit",
            lamport: 2,
            payloadDigest: "sha256:evt-c4-0051-emit",
            state: "rejected",
            replayProtected: true,
          },
        ],
      },
    ],
    conflicts: [
      {
        conflictId: "conflict-c4-0051",
        workOrderId: "os-2026-0051",
        workOrderNumber: "OS-2026-0051",
        class: "C4",
        status: "escalated",
        openedAtLabel: "22/04 10:09",
        deadlineLabel: "Escalado para regulator em 22/04 10:41",
        responsibleLabel: "Regulator",
        summaryLabel: "Reemissao e nova emissao concorreram sobre a mesma OS finalizada.",
        recommendedAction: "Aguardar parecer formal antes de qualquer desbloqueio.",
        blockingScopeLabel: "Bloqueia emissao e reemissao da OS selecionada.",
      },
    ],
    details: {
      "conflict-c4-0051": {
        conflictId: "conflict-c4-0051",
        title: "OS-2026-0051 · reemissao versus nova emissao",
        status: "escalated",
        class: "C4",
        summary:
          "Uma tentativa de reemissao controlada chegou enquanto outro device ainda tentava nova emissao. Como a OS ja estava finalizada, a decisao depende de interpretacao normativa sobre a cadeia vigente.",
        decisionDeadlineLabel: "Parecer requerido antes do desbloqueio operacional",
        responsibleLabel: "Regulator",
        queueSlaLabel: "Escalado apos triagem por envolver reemissao controlada e preservacao de hash-chain.",
        winningEventId: "evt-c4-0051-reissue",
        losingEventId: "evt-c4-0051-emit",
        blockedForEmission: true,
        regulatorEscalationRequired: true,
        recommendedDecisionLabel: "Manter a OS travada ate o parecer regulatorio registrar a decisao final.",
        rationaleTemplate:
          "Conflito C4 com impacto em reemissao controlada; registrar parecer regulatorio, justificativa e referencia ao certificado anterior antes de qualquer desbloqueio.",
        resolutionOptions: [
          {
            action: "accept_server_winner",
            label: "Manter vencedor do servidor",
            detail: "Nao disponivel sem parecer regulatorio formal.",
            allowed: false,
          },
          {
            action: "accept_device_winner",
            label: "Promover evento do device",
            detail: "Nao disponivel sem parecer regulatorio formal.",
            allowed: false,
          },
          {
            action: "merge_fields",
            label: "Mesclar manualmente",
            detail: "Nao permitido porque a OS ja estava finalizada.",
            allowed: false,
          },
          {
            action: "escalate_to_regulator",
            label: "Escalar para regulator",
            detail: "Abrir parecer formal sobre reemissao versus nova emissao preservando a hash-chain.",
            allowed: true,
          },
        ],
        auditRequirements: [
          "Registrar parecer regulatorio datado antes da decisao final.",
          "Preservar referencia ao hash anterior e ao certificado original.",
          "Manter notificacao e justificativa de bloqueio no audit log da OS.",
        ],
        blockers: ["Nenhum certificado pode ser emitido enquanto a disputa normativa estiver em aberto."],
        warnings: ["O QR do certificado original deve permanecer verificavel independentemente do parecer."],
        links: {
          workspaceScenarioId: "release-blocked",
          serviceOrderScenarioId: "review-blocked",
          auditTrailScenarioId: "reissue-attention",
        },
      },
    },
  },
};

const DEFAULT_SCENARIO: OfflineSyncScenarioId = "stable-upload";

export function listOfflineSyncScenarios(): OfflineSyncScenario[] {
  return (Object.keys(SCENARIOS) as OfflineSyncScenarioId[]).map((scenarioId) =>
    resolveOfflineSyncScenario(scenarioId),
  );
}

export function resolveOfflineSyncScenario(
  scenarioId?: string,
  outboxItemId?: string,
  conflictId?: string,
): OfflineSyncScenario {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = SCENARIOS[resolvedScenarioId];

  const selectedOutboxItem =
    definition.outboxItems.find((item) => item.itemId === outboxItemId) ??
    definition.outboxItems.find((item) => item.itemId === definition.selectedOutboxItemId);
  if (!selectedOutboxItem) {
    throw new Error("missing_offline_sync_outbox_items");
  }

  const selectedConflict =
    definition.conflicts.find((item) => item.conflictId === conflictId) ??
    definition.conflicts.find((item) => item.conflictId === definition.selectedConflictId);
  if (!selectedConflict) {
    throw new Error("missing_offline_sync_conflicts");
  }

  const detail = definition.details[selectedConflict.conflictId];
  if (!detail) {
    throw new Error(`missing_offline_sync_conflict_detail:${selectedConflict.conflictId}`);
  }

  return {
    id: resolvedScenarioId,
    label: definition.label,
    description: definition.description,
    summary: definition.summary,
    selectedOutboxItemId: selectedOutboxItem.itemId,
    selectedConflictId: selectedConflict.conflictId,
    outboxItems: definition.outboxItems,
    conflicts: definition.conflicts,
    detail,
  };
}

export function buildOfflineSyncCatalog(
  scenarioId?: string,
  outboxItemId?: string,
  conflictId?: string,
): OfflineSyncCatalog {
  const selectedScenario = resolveOfflineSyncScenario(scenarioId, outboxItemId, conflictId);
  const scenarios = listOfflineSyncScenarios().map((scenario) =>
    scenario.id === selectedScenario.id ? selectedScenario : scenario,
  );

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios,
  };
}

function resolveScenarioId(scenarioId?: string): OfflineSyncScenarioId {
  if (scenarioId && scenarioId in SCENARIOS) {
    return scenarioId as OfflineSyncScenarioId;
  }

  return DEFAULT_SCENARIO;
}
