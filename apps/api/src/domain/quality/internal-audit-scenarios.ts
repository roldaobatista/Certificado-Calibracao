import type {
  InternalAuditCatalog,
  InternalAuditChecklistItem,
  InternalAuditCycleListItem,
  InternalAuditDetail,
  InternalAuditFindingItem,
  InternalAuditScenario,
  InternalAuditScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

type ScenarioCycleState = {
  cycleId: string;
  cycleLabel: string;
  windowLabel: string;
  scopeLabel: string;
  auditorLabel: string;
  auditeeLabel: string;
  periodLabel: string;
  reportLabel: string;
  evidenceLabel: string;
  nextReviewLabel: string;
  status: RegistryOperationalStatus;
  statusLabel: string;
  findingsLabel: string;
  noticeLabel: string;
  checklist: InternalAuditChecklistItem[];
  findings: InternalAuditFindingItem[];
  blockers: string[];
  warnings: string[];
  nonconformityScenarioId?: InternalAuditDetail["links"]["nonconformityScenarioId"];
};

type InternalAuditScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  programLabel: string;
  selectedCycleId: string;
  counts: {
    plannedCycleCount: number;
    completedCycleCount: number;
    openFindingCount: number;
  };
  cycles: ScenarioCycleState[];
};

const SCENARIOS: Record<InternalAuditScenarioId, InternalAuditScenarioDefinition> = {
  "program-on-track": {
    label: "Programa anual em trilho",
    description:
      "Programa anual com ciclo encerrado, historico arquivado e proximos ciclos preparados dentro da cadencia prevista.",
    recommendedAction:
      "Manter o programa anual vigente, arquivar o historico encerrado e preparar a amostragem do proximo ciclo ordinario.",
    programLabel: "Auditoria Interna 2026",
    selectedCycleId: "audit-cycle-2026-1",
    counts: {
      plannedCycleCount: 3,
      completedCycleCount: 1,
      openFindingCount: 0,
    },
    cycles: [
      {
        cycleId: "audit-cycle-2026-1",
        cycleLabel: "Ciclo 1",
        windowLabel: "Mar/2026",
        scopeLabel: "§6.4 Equipamentos | §7.6 Incerteza",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Carlos, Maria",
        periodLabel: "10/03/2026 a 12/03/2026",
        reportLabel: "Relatorio IA-2026-C1 assinado e arquivado",
        evidenceLabel:
          "Checklist aplicado, relatorio final e evidencias do ciclo arquivados no dossie da Qualidade.",
        nextReviewLabel:
          "Preparar o ciclo 2 para 09/2026 com foco em pessoal e certificados antes da abertura formal.",
        status: "ready",
        statusLabel: "Concluido e arquivado",
        findingsLabel: "Historico sem NC aberta",
        noticeLabel: "Ciclo concluido, arquivado e pronto para consulta auditavel do historico.",
        checklist: [
          {
            key: "inventory-updated",
            requirementLabel: "§6.4 Inventario atualizado",
            evidenceLabel: "Relatorio PadInv-202603 arquivado.",
            status: "ready",
          },
          {
            key: "traceable-calibration",
            requirementLabel: "§6.4 Calibracao rastreavel",
            evidenceLabel: "Certificados vigentes dos padroes conferidos.",
            status: "ready",
          },
          {
            key: "visible-status-label",
            requirementLabel: "§6.4 Etiqueta de status visivel",
            evidenceLabel: "Achado antigo saneado e mantido apenas para historico.",
            status: "ready",
          },
          {
            key: "uncertainty-balance",
            requirementLabel: "§7.6 Balanco documentado",
            evidenceLabel: "PTs amostrados com balanco vigente e evidenciado no relatorio final.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c1-closed-01",
            title: "Historico encerrado: etiqueta de status regularizada",
            severityLabel: "Baixa",
            ownerLabel: "Maria",
            dueDateLabel: "Encerrada em 25/04/2026",
            status: "ready",
            nonconformityId: "nc-011",
          },
        ],
        blockers: [],
        warnings: [],
        nonconformityScenarioId: "resolved-history",
      },
      {
        cycleId: "audit-cycle-2026-2",
        cycleLabel: "Ciclo 2",
        windowLabel: "Set/2026",
        scopeLabel: "§6.2 Pessoal | §7.8 Certificados",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Joao Silva, revisores e signatarios",
        periodLabel: "Janela prevista para 09/2026",
        reportLabel: "Checklist-base pronto para aplicacao",
        evidenceLabel:
          "Programa anual aprovado, janela reservada e checklist padrao publicados para preparacao do ciclo.",
        nextReviewLabel: "Confirmar agenda, amostragem e trilha de competencias antes da abertura do ciclo.",
        status: "ready",
        statusLabel: "Planejada",
        findingsLabel: "Sem achado aberto",
        noticeLabel: "Ciclo planejado e pronto para execucao sem desvio material no programa anual.",
        checklist: [
          {
            key: "competency-matrix",
            requirementLabel: "§6.2 Matriz de competencias pronta",
            evidenceLabel: "Usuarios e competencias vigentes ja consolidados para a amostragem.",
            status: "ready",
          },
          {
            key: "certificate-sample",
            requirementLabel: "§7.8 Amostra de certificados definida",
            evidenceLabel: "Amostragem preliminar reservada para o ciclo ordinario.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c2-prep",
            title: "Nenhum achado aberto antes da execucao do ciclo",
            severityLabel: "Informativo",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Revisar na abertura do ciclo",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
      },
      {
        cycleId: "audit-cycle-2026-3",
        cycleLabel: "Ciclo 3",
        windowLabel: "Nov/2026",
        scopeLabel: "§8.4 Registros | §8.9 Analise critica",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Qualidade e direcao",
        periodLabel: "Janela prevista para 11/2026",
        reportLabel: "Escopo anual reservado no programa aprovado",
        evidenceLabel:
          "Programa anual e pauta preliminar reservam o fechamento do ano para registros e analise critica.",
        nextReviewLabel: "Validar insumos de indicadores e atas antes de congelar a amostragem final.",
        status: "ready",
        statusLabel: "Planejada",
        findingsLabel: "Sem achado aberto",
        noticeLabel: "Ciclo final do programa anual segue planejado e sem bloqueio no recorte atual.",
        checklist: [
          {
            key: "record-sampling",
            requirementLabel: "§8.4 Amostragem de registros definida",
            evidenceLabel: "Recorte preliminar reservado para o fechamento anual.",
            status: "ready",
          },
          {
            key: "management-inputs",
            requirementLabel: "§8.9 Insumos para analise critica identificados",
            evidenceLabel: "Entradas de NC, riscos, reclamacoes e indicadores ja estao mapeadas no programa.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c3-prep",
            title: "Nenhum achado aberto antes da execucao do ciclo",
            severityLabel: "Informativo",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Revisar na abertura do ciclo",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
  "follow-up-attention": {
    label: "Ciclo concluido com follow-up pendente",
    description:
      "O ciclo 1 ja encerrou a execucao, mas ainda sustenta NCs em tratamento antes da abertura do proximo ciclo ordinario.",
    recommendedAction:
      "Fechar as NCs pendentes do ciclo atual e usar o follow-up como ancora antes de abrir o proximo ciclo do programa anual.",
    programLabel: "Auditoria Interna 2026",
    selectedCycleId: "audit-cycle-2026-1",
    counts: {
      plannedCycleCount: 4,
      completedCycleCount: 1,
      openFindingCount: 2,
    },
    cycles: [
      {
        cycleId: "audit-cycle-2026-1",
        cycleLabel: "Ciclo 1",
        windowLabel: "Mar/2026",
        scopeLabel: "§6.4 Equipamentos | §7.6 Incerteza",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Carlos, Maria",
        periodLabel: "10/03/2026 a 12/03/2026",
        reportLabel: "Relatorio IA-2026-C1 emitido com follow-up aberto",
        evidenceLabel:
          "Checklist aplicado, achados formalizados e plano de follow-up arquivados no dossie do programa anual.",
        nextReviewLabel:
          "Fechar NC-013 e NC-014 antes de confirmar a abertura do ciclo 2 e registrar a verificacao de eficacia minima.",
        status: "attention",
        statusLabel: "2 NC em tratamento",
        findingsLabel: "2 NC em tratamento",
        noticeLabel: "Ciclo concluido, mas ainda dependente do fechamento formal dos achados abertos.",
        checklist: [
          {
            key: "inventory-updated",
            requirementLabel: "§6.4 Inventario atualizado",
            evidenceLabel: "Relatorio PadInv-202603 [PDF].",
            status: "ready",
          },
          {
            key: "traceable-calibration",
            requirementLabel: "§6.4 Calibracao rastreavel",
            evidenceLabel: "Padroes e certificados conferidos no recorte do ciclo.",
            status: "ready",
          },
          {
            key: "visible-status-label",
            requirementLabel: "§6.4 Etiqueta de status visivel",
            evidenceLabel: "NC-014 aberta para regularizar a visibilidade das etiquetas.",
            status: "attention",
          },
          {
            key: "maintenance-program",
            requirementLabel: "§6.4 Programa de manutencao",
            evidenceLabel: "Plano de manutencao conferido no ciclo.",
            status: "ready",
          },
          {
            key: "method-evaluation",
            requirementLabel: "§7.6 Avaliacao por metodo",
            evidenceLabel: "Metodo conferido no relatorio do ciclo.",
            status: "ready",
          },
          {
            key: "documented-balance",
            requirementLabel: "§7.6 Balanco documentado para todos",
            evidenceLabel: "NC-013 aberta para PT-005, PT-006 e PT-008.",
            status: "attention",
          },
          {
            key: "cmc-consistency",
            requirementLabel: "§7.6 Coerencia com CMC",
            evidenceLabel: "Amostra auditada permaneceu coerente com CMC declarada.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c1-nc013",
            title: "NC-013 - Balanco de incerteza nao documentado",
            severityLabel: "Media",
            ownerLabel: "Carlos",
            dueDateLabel: "11/04/2026",
            status: "attention",
            nonconformityId: "nc-013",
          },
          {
            findingId: "finding-2026-c1-nc014",
            title: "NC-014 - Etiqueta de status nao visivel",
            severityLabel: "Baixa",
            ownerLabel: "Maria",
            dueDateLabel: "11/05/2026",
            status: "attention",
            nonconformityId: "nc-014",
          },
        ],
        blockers: [],
        warnings: ["O ciclo 2 nao deve abrir sem follow-up minimo das NCs geradas no ciclo 1."],
        nonconformityScenarioId: "open-attention",
      },
      {
        cycleId: "audit-cycle-2026-2",
        cycleLabel: "Ciclo 2",
        windowLabel: "Set/2026",
        scopeLabel: "§6.2 Pessoal | §7.8 Certificados",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Joao Silva, revisores e signatarios",
        periodLabel: "Janela prevista para 09/2026",
        reportLabel: "Checklist-base pronto para aplicacao",
        evidenceLabel: "Ciclo mantido no programa anual, mas dependente do fechamento minimo do follow-up anterior.",
        nextReviewLabel: "Revalidar agenda quando as NCs do ciclo 1 tiverem evidencia minima de saneamento.",
        status: "ready",
        statusLabel: "Planejada",
        findingsLabel: "Sem achado aberto",
        noticeLabel: "Ciclo futuro continua reservado, aguardando apenas o follow-up minimo do ciclo anterior.",
        checklist: [
          {
            key: "competency-matrix",
            requirementLabel: "§6.2 Matriz de competencias pronta",
            evidenceLabel: "Base de usuarios e competencias reservada para amostragem.",
            status: "ready",
          },
          {
            key: "certificate-sample",
            requirementLabel: "§7.8 Amostra de certificados definida",
            evidenceLabel: "Amostragem preliminar preparada para o ciclo 2.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c2-prep",
            title: "Nenhum achado aberto antes da execucao do ciclo",
            severityLabel: "Informativo",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Revisar na abertura do ciclo",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: ["A confirmacao do ciclo depende do follow-up do ciclo 1."],
      },
      {
        cycleId: "audit-cycle-2026-3",
        cycleLabel: "Ciclo 3",
        windowLabel: "Nov/2026",
        scopeLabel: "§8.4 Registros | §8.9 Analise critica",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Qualidade e direcao",
        periodLabel: "Janela prevista para 11/2026",
        reportLabel: "Escopo anual reservado no programa aprovado",
        evidenceLabel: "Programa anual preserva o fechamento do ano para registros e analise critica.",
        nextReviewLabel: "Congelar a amostragem apenas apos estabilizar os achados abertos do ciclo 1.",
        status: "ready",
        statusLabel: "Planejada",
        findingsLabel: "Sem achado aberto",
        noticeLabel: "Ciclo final permanece reservado, sem bloqueio formal no programa anual.",
        checklist: [
          {
            key: "record-sampling",
            requirementLabel: "§8.4 Amostragem de registros definida",
            evidenceLabel: "Escopo preliminar reservado no programa.",
            status: "ready",
          },
          {
            key: "management-inputs",
            requirementLabel: "§8.9 Insumos mapeados",
            evidenceLabel: "NCs, riscos, reclamacoes e indicadores ja alimentam a pauta prevista.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c3-prep",
            title: "Nenhum achado aberto antes da execucao do ciclo",
            severityLabel: "Informativo",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Revisar na abertura do ciclo",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
      },
      {
        cycleId: "audit-cycle-2026-4",
        cycleLabel: "Ciclo 4",
        windowLabel: "Dez/2026",
        scopeLabel: "Revisao final de follow-up",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Qualidade",
        periodLabel: "Reserva opcional do programa 2026",
        reportLabel: "Janela de contingencia reservada",
        evidenceLabel: "Programa anual preserva uma janela de contingencia para validar eficacia e fechamento do ano.",
        nextReviewLabel: "Usar apenas se algum achado relevante permanecer aberto no fechamento do ano.",
        status: "ready",
        statusLabel: "Reserva de contingencia",
        findingsLabel: "Sem achado aberto",
        noticeLabel: "Janela de contingencia mantida apenas como reserva regulada do programa anual.",
        checklist: [
          {
            key: "contingency-window",
            requirementLabel: "Janela de contingencia registrada",
            evidenceLabel: "Reserva anual aprovada pela Qualidade.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c4-prep",
            title: "Nenhum achado aberto antes do uso da contingencia",
            severityLabel: "Informativo",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Somente se a janela for ativada",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
  "extraordinary-escalation": {
    label: "Auditoria extraordinaria exigida",
    description:
      "O programa anual segue preservado, mas um recorte critico exige ciclo extraordinario antes de qualquer liberacao operacional.",
    recommendedAction:
      "Abrir a auditoria extraordinaria, usar NC e trilha como ancora e so retomar o fluxo apos parecer minimo do ciclo.",
    programLabel: "Auditoria Interna 2026",
    selectedCycleId: "audit-cycle-extra-2026",
    counts: {
      plannedCycleCount: 4,
      completedCycleCount: 1,
      openFindingCount: 3,
    },
    cycles: [
      {
        cycleId: "audit-cycle-extra-2026",
        cycleLabel: "Ciclo Extra",
        windowLabel: "Abr/2026",
        scopeLabel: "§7.8 Certificados | §8.4 Registros | §7.10 Trabalho nao conforme",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Carlos, Maria, Joao Silva",
        periodLabel: "Janela extraordinaria solicitada em 22/04/2026",
        reportLabel: "Abertura extraordinaria pendente de parecer inicial",
        evidenceLabel:
          "Briefing critico, trilha bloqueada, reclamacao RECL-007 e NC-015 anexados ao preparo do ciclo extraordinario.",
        nextReviewLabel:
          "Abrir o ciclo extraordinario antes de qualquer liberacao operacional do caso critico e registrar parecer preliminar.",
        status: "blocked",
        statusLabel: "Extraordinaria pendente",
        findingsLabel: "1 critica e 2 graves",
        noticeLabel: "Ciclo extraordinario exigido pelo recorte critico e ainda pendente de abertura formal.",
        checklist: [
          {
            key: "hash-chain-check",
            requirementLabel: "§8.4 Integridade da hash-chain verificada",
            evidenceLabel: "Divergencia ativa na trilha critica impede considerar o recorte seguro.",
            status: "blocked",
          },
          {
            key: "controlled-reissue",
            requirementLabel: "§7.8 Reemissao controlada com dupla aprovacao",
            evidenceLabel: "Fluxo iniciado, mas parecer extraordinario ainda nao concluido.",
            status: "attention",
          },
          {
            key: "nonconforming-containment",
            requirementLabel: "§7.10 Contencao formal do caso",
            evidenceLabel: "NC-015 aberta e contencao em acompanhamento pela Qualidade.",
            status: "attention",
          },
          {
            key: "client-response",
            requirementLabel: "§7.9 Resposta formal ao cliente",
            evidenceLabel: "RECL-007 ainda sem resposta conclusiva registrada.",
            status: "blocked",
          },
        ],
        findings: [
          {
            findingId: "finding-extra-01",
            title: "Hash-chain divergente em recorte critico",
            severityLabel: "Alta",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Imediato",
            status: "blocked",
            nonconformityId: "nc-015",
          },
          {
            findingId: "finding-extra-02",
            title: "Resposta formal ao cliente ainda nao concluida",
            severityLabel: "Alta",
            ownerLabel: "Joao Silva",
            dueDateLabel: "48h uteis",
            status: "attention",
          },
          {
            findingId: "finding-extra-03",
            title: "Reemissao controlada sem ciclo extraordinario concluido",
            severityLabel: "Media",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Antes de liberar qualquer certificado",
            status: "blocked",
          },
        ],
        blockers: [
          "O caso critico exige auditoria extraordinaria antes de qualquer liberacao operacional.",
          "A divergencia de trilha ainda impede concluir o parecer inicial do ciclo.",
        ],
        warnings: ["NC-015 e RECL-007 precisam continuar ancorando o follow-up do caso extraordinario."],
        nonconformityScenarioId: "critical-response",
      },
      {
        cycleId: "audit-cycle-2026-1",
        cycleLabel: "Ciclo 1",
        windowLabel: "Mar/2026",
        scopeLabel: "§6.4 Equipamentos | §7.6 Incerteza",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Carlos, Maria",
        periodLabel: "10/03/2026 a 12/03/2026",
        reportLabel: "Relatorio IA-2026-C1 com follow-up residual",
        evidenceLabel: "Ciclo 1 permanece arquivado, servindo de referencia para o escalonamento atual.",
        nextReviewLabel: "Usar apenas como historico de contexto do programa anual.",
        status: "attention",
        statusLabel: "Historico com follow-up",
        findingsLabel: "2 NC historicas",
        noticeLabel: "Ciclo historico mantido para contexto, sem substituir a auditoria extraordinaria atual.",
        checklist: [
          {
            key: "inventory-updated",
            requirementLabel: "§6.4 Inventario atualizado",
            evidenceLabel: "Relatorio PadInv-202603 arquivado.",
            status: "ready",
          },
          {
            key: "documented-balance",
            requirementLabel: "§7.6 Balanco documentado",
            evidenceLabel: "Historico do achado NC-013 mantido para comparacao.",
            status: "attention",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c1-nc013",
            title: "NC-013 - Balanco de incerteza nao documentado",
            severityLabel: "Media",
            ownerLabel: "Carlos",
            dueDateLabel: "Historico de follow-up",
            status: "attention",
            nonconformityId: "nc-013",
          },
        ],
        blockers: [],
        warnings: [],
        nonconformityScenarioId: "open-attention",
      },
      {
        cycleId: "audit-cycle-2026-2",
        cycleLabel: "Ciclo 2",
        windowLabel: "Set/2026",
        scopeLabel: "§6.2 Pessoal | §7.8 Certificados",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Joao Silva, revisores e signatarios",
        periodLabel: "Janela prevista para 09/2026",
        reportLabel: "Ciclo ordinario preservado no programa",
        evidenceLabel: "Programa anual mantem o ciclo 2 reservado, mas subordinado ao fechamento do caso extraordinario.",
        nextReviewLabel: "Nao abrir o ciclo 2 antes do parecer minimo da auditoria extraordinaria.",
        status: "ready",
        statusLabel: "Planejada",
        findingsLabel: "Sem achado aberto",
        noticeLabel: "Ciclo ordinario permanece reservado, sem substituir a resposta extraordinaria atual.",
        checklist: [
          {
            key: "certificate-sample",
            requirementLabel: "§7.8 Amostra de certificados definida",
            evidenceLabel: "Amostragem preliminar mantida no programa anual.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c2-prep",
            title: "Nenhum achado aberto antes da execucao do ciclo",
            severityLabel: "Informativo",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Revisar na abertura do ciclo",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
      },
      {
        cycleId: "audit-cycle-2026-3",
        cycleLabel: "Ciclo 3",
        windowLabel: "Nov/2026",
        scopeLabel: "§8.4 Registros | §8.9 Analise critica",
        auditorLabel: "Ana Costa",
        auditeeLabel: "Qualidade e direcao",
        periodLabel: "Janela prevista para 11/2026",
        reportLabel: "Escopo anual reservado no programa",
        evidenceLabel: "Ciclo final continua reservado para consolidacao do ano, sem efeito sobre o caso critico atual.",
        nextReviewLabel: "Revalidar apenas depois que o caso extraordinario estiver formalmente contido.",
        status: "ready",
        statusLabel: "Planejada",
        findingsLabel: "Sem achado aberto",
        noticeLabel: "Ciclo final do ano permanece planejado e subordinado ao fechamento do recorte critico.",
        checklist: [
          {
            key: "record-sampling",
            requirementLabel: "§8.4 Amostragem de registros definida",
            evidenceLabel: "Reserva anual mantida no programa.",
            status: "ready",
          },
        ],
        findings: [
          {
            findingId: "finding-2026-c3-prep",
            title: "Nenhum achado aberto antes da execucao do ciclo",
            severityLabel: "Informativo",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Revisar na abertura do ciclo",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
};

const DEFAULT_SCENARIO: InternalAuditScenarioId = "follow-up-attention";

export function listInternalAuditScenarios(): InternalAuditScenario[] {
  return (Object.keys(SCENARIOS) as InternalAuditScenarioId[]).map((scenarioId) =>
    resolveInternalAuditScenario(scenarioId),
  );
}

export function resolveInternalAuditScenario(
  scenarioId?: string,
  cycleId?: string,
): InternalAuditScenario {
  const definition = resolveDefinition(scenarioId);
  const cycles = definition.cycles.map(buildCycleListItem);
  const selectedCycle =
    cycles.find((cycle) => cycle.cycleId === cycleId) ??
    cycles.find((cycle) => cycle.cycleId === definition.selectedCycleId) ??
    cycles[0];

  if (!selectedCycle) {
    throw new Error("missing_internal_audit_cycles");
  }

  const detail = buildCycleDetail(definition, selectedCycle.cycleId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition, detail),
    selectedCycleId: selectedCycle.cycleId,
    cycles,
    detail,
  };
}

export function buildInternalAuditCatalog(
  scenarioId?: string,
  cycleId?: string,
): InternalAuditCatalog {
  const selectedScenario = resolveInternalAuditScenario(scenarioId, cycleId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listInternalAuditScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildCycleListItem(state: ScenarioCycleState): InternalAuditCycleListItem {
  return {
    cycleId: state.cycleId,
    cycleLabel: state.cycleLabel,
    windowLabel: state.windowLabel,
    scopeLabel: state.scopeLabel,
    auditorLabel: state.auditorLabel,
    findingsLabel: state.findingsLabel,
    status: state.status,
    statusLabel: state.statusLabel,
  };
}

function buildCycleDetail(
  definition: InternalAuditScenarioDefinition,
  cycleId: string,
): InternalAuditDetail {
  const cycle = getCycleState(definition, cycleId);

  return {
    cycleId: cycle.cycleId,
    title: `${cycle.cycleLabel} - ${cycle.scopeLabel}`,
    status: cycle.status,
    noticeLabel: cycle.noticeLabel,
    auditorLabel: cycle.auditorLabel,
    auditeeLabel: cycle.auditeeLabel,
    periodLabel: cycle.periodLabel,
    scopeLabel: cycle.scopeLabel,
    reportLabel: cycle.reportLabel,
    evidenceLabel: cycle.evidenceLabel,
    nextReviewLabel: cycle.nextReviewLabel,
    checklist: cycle.checklist,
    findings: cycle.findings,
    blockers: cycle.blockers,
    warnings: cycle.warnings,
    links: {
      nonconformityScenarioId: cycle.nonconformityScenarioId,
    },
  };
}

function buildSummary(
  definition: InternalAuditScenarioDefinition,
  detail: InternalAuditDetail,
): InternalAuditScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Programa de auditoria interna controlado e pronto para acompanhamento"
        : detail.status === "attention"
          ? "Follow-up de auditoria interna exige fechamento de achados"
          : "Programa exige auditoria extraordinaria antes da proxima liberacao",
    programLabel: definition.programLabel,
    plannedCycleCount: definition.counts.plannedCycleCount,
    completedCycleCount: definition.counts.completedCycleCount,
    openFindingCount: definition.counts.openFindingCount,
    recommendedAction: definition.recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function resolveScenarioId(scenarioId?: string): InternalAuditScenarioId {
  return isInternalAuditScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): InternalAuditScenarioDefinition {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = SCENARIOS[resolvedScenarioId];

  if (!definition) {
    throw new Error(`missing_internal_audit_scenario:${resolvedScenarioId}`);
  }

  return definition;
}

function getCycleState(
  definition: InternalAuditScenarioDefinition,
  cycleId: string,
): ScenarioCycleState {
  const cycle = definition.cycles.find((item) => item.cycleId === cycleId);
  if (!cycle) {
    throw new Error(`missing_internal_audit_cycle:${cycleId}`);
  }

  return cycle;
}

function isInternalAuditScenarioId(
  value: string | undefined,
): value is InternalAuditScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
