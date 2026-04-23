import type {
  ManagementReviewAgendaItem,
  ManagementReviewAutomaticInput,
  ManagementReviewCatalog,
  ManagementReviewDecisionItem,
  ManagementReviewDetail,
  ManagementReviewMeetingItem,
  ManagementReviewScenario,
  ManagementReviewScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

import {
  buildManagementReviewCalendar,
  buildManagementReviewCalendarExportHref,
  formatManagementReviewSchedule,
  type ManagementReviewCalendarMeeting,
} from "./management-review-calendar.js";
import { buildManagementReviewSignature } from "./management-review-signature.js";

type ScenarioMeetingState = {
  meetingId: string;
  dateLabel: string;
  titleLabel: string;
  outcomeLabel: string;
  status: RegistryOperationalStatus;
  noticeLabel: string;
  nextMeetingLabel: string;
  chairLabel: string;
  attendeesLabel: string;
  periodLabel: string;
  ataLabel: string;
  evidenceLabel: string;
  agendaItems: ManagementReviewAgendaItem[];
  automaticInputs: ManagementReviewAutomaticInput[];
  decisions: ManagementReviewDecisionItem[];
  blockers: string[];
  warnings: string[];
  scheduledForUtc: string;
  heldAtUtc?: string;
  signedByLabel?: string;
  signatureDeviceId?: string;
  signatureStatement?: string;
  signedAtUtc?: string;
};

type ManagementReviewScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedMeetingId: string;
  meetings: ScenarioMeetingState[];
};

const ORDINARY_AGENDA: ManagementReviewAgendaItem[] = [
  { key: "customer-needs", label: "Mudancas nas necessidades do cliente", status: "ready" },
  { key: "objectives", label: "Atendimento de objetivos", status: "ready" },
  { key: "procedures", label: "Adequacao de politicas e procedimentos", status: "ready" },
  { key: "audits", label: "Resultado de auditorias internas e externas", status: "ready" },
  { key: "corrective-actions", label: "Acoes corretivas", status: "ready" },
  { key: "complaints", label: "Reclamacoes", status: "ready" },
  { key: "risks", label: "Resultados da identificacao de riscos", status: "ready" },
  { key: "resources", label: "Adequacao de recursos", status: "ready" },
];

const SCENARIOS: Record<ManagementReviewScenarioId, ManagementReviewScenarioDefinition> = {
  "ordinary-ready": {
    label: "Analise critica ordinaria arquivada",
    description:
      "A ultima reuniao ordinaria foi consolidada, arquivada e nao deixou deliberacoes abertas no recorte atual.",
    recommendedAction:
      "Manter a cadencia trimestral, arquivar as evidencias e reutilizar o consolidado como base da proxima pauta ordinaria.",
    selectedMeetingId: "review-2026-q1",
    meetings: [
      {
        meetingId: "review-2026-q1",
        dateLabel: "31/03/2026",
        titleLabel: "Analise critica Q1/2026",
        outcomeLabel: "Ata encerrada e sem deliberação aberta",
        status: "ready",
        noticeLabel: "Reuniao ordinaria encerrada, assinada e pronta para consulta auditavel.",
        nextMeetingLabel: "30/06/2026",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Q1/2026",
        ataLabel: "Ata AC-2026-Q1 assinada e arquivada",
        evidenceLabel:
          "Dossie trimestral consolidado com emissao, NCs, reclamacoes, riscos, auditoria interna e indicadores arquivado.",
        agendaItems: ORDINARY_AGENDA,
        automaticInputs: [
          {
            key: "emission-volume",
            label: "Certificados emitidos no periodo",
            valueLabel: "142 emitidos | 0 reemissoes por erro tecnico",
            sourceLabel: "Emissao",
            status: "ready",
          },
          {
            key: "nonconformities",
            label: "NCs e reincidencia",
            valueLabel: "0 abertas | 7 fechadas | reincidencia 0%",
            sourceLabel: "Nao conformidades",
            status: "ready",
            href: "/quality/nonconformities?scenario=resolved-history&nc=nc-011",
          },
          {
            key: "complaints",
            label: "Reclamacoes do periodo",
            valueLabel: "0 aberta | historico resolvido em < 24h",
            sourceLabel: "Reclamacoes",
            status: "ready",
            href: "/quality/complaints?scenario=resolved-history&complaint=recl-002",
          },
          {
            key: "internal-audit",
            label: "Programa de auditoria interna",
            valueLabel: "Ciclo 1 arquivado | sem achado aberto",
            sourceLabel: "Auditoria interna",
            status: "ready",
            href: "/quality/internal-audit?scenario=program-on-track&cycle=audit-cycle-2026-1",
          },
          {
            key: "indicators",
            label: "Indicadores de qualidade",
            valueLabel: "Tempo medio 32 min | todos dentro da meta",
            sourceLabel: "Indicadores",
            status: "ready",
            href: "/quality/indicators?scenario=baseline-ready&indicator=indicator-os-cycle-time",
          },
        ],
        decisions: [
          {
            key: "decision-q1-01",
            label: "Manter meta operacional de tempo medio por OS em 35 min",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Encerrada em 31/03/2026",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
        scheduledForUtc: "2026-03-31T13:00:00.000Z",
        heldAtUtc: "2026-03-31T14:25:00.000Z",
        signedByLabel: "Ana Costa",
        signatureDeviceId: "device-quality-01",
        signatureStatement: "Ata da analise critica Q1/2026 assinada e arquivada pela direcao.",
        signedAtUtc: "2026-03-31T14:40:00.000Z",
      },
      {
        meetingId: "review-2026-q2",
        dateLabel: "30/06/2026",
        titleLabel: "Analise critica Q2/2026",
        outcomeLabel: "Pauta reservada para proxima reuniao ordinaria",
        status: "ready",
        noticeLabel: "Proxima reuniao ordinaria reservada, sem pendencia critica no recorte atual.",
        nextMeetingLabel: "30/06/2026",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Q2/2026",
        ataLabel: "Pauta preliminar reservada",
        evidenceLabel: "Janela reservada no calendario da Qualidade com pauta preliminar pronta.",
        agendaItems: ORDINARY_AGENDA,
        automaticInputs: [
          {
            key: "ordinary-prep",
            label: "Pauta ordinaria preparada",
            valueLabel: "Entradas de NC, riscos, reclamacoes e indicadores reservadas",
            sourceLabel: "Preparacao da pauta",
            status: "ready",
          },
        ],
        decisions: [
          {
            key: "decision-q2-prep",
            label: "Nenhuma deliberacao aberta antes da reuniao",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Revisar em 30/06/2026",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
        scheduledForUtc: "2026-06-30T13:00:00.000Z",
      },
    ],
  },
  "agenda-attention": {
    label: "Pauta ordinaria com pendencias preventivas",
    description:
      "A proxima reuniao ordinaria ja possui pauta automatica, mas ainda depende do fechamento minimo de NCs, auditoria interna e indicadores em atencao.",
    recommendedAction:
      "Levar a pauta preparada para a reuniao de 30/06/2026 e fechar as pendencias preventivas antes de consolidar a ata.",
    selectedMeetingId: "review-2026-q2",
    meetings: [
      {
        meetingId: "review-2026-q1",
        dateLabel: "31/03/2026",
        titleLabel: "Analise critica Q1/2026",
        outcomeLabel: "Ata anterior arquivada",
        status: "ready",
        noticeLabel: "Ata anterior encerrada e usada como base para o novo follow-up.",
        nextMeetingLabel: "30/06/2026",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Q1/2026",
        ataLabel: "Ata AC-2026-Q1 arquivada",
        evidenceLabel: "Historico do trimestre anterior mantido para comparacao de decisoes.",
        agendaItems: ORDINARY_AGENDA,
        automaticInputs: [
          {
            key: "history-q1",
            label: "Historico encerrado",
            valueLabel: "Base anterior sem deliberação aberta",
            sourceLabel: "Ata anterior",
            status: "ready",
          },
        ],
        decisions: [
          {
            key: "decision-q1-history",
            label: "Historico anterior mantido apenas para comparacao",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Encerrada em 31/03/2026",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
        scheduledForUtc: "2026-03-31T13:00:00.000Z",
        heldAtUtc: "2026-03-31T14:25:00.000Z",
        signedByLabel: "Ana Costa",
        signatureDeviceId: "device-quality-01",
        signatureStatement: "Ata da analise critica Q1/2026 assinada e mantida como historico comparativo.",
        signedAtUtc: "2026-03-31T14:40:00.000Z",
      },
      {
        meetingId: "review-2026-q2",
        dateLabel: "30/06/2026",
        titleLabel: "Analise critica Q2/2026",
        outcomeLabel: "Pauta automatica pronta com follow-up pendente",
        status: "attention",
        noticeLabel: "Reuniao ordinaria preparada, mas ainda dependente do fechamento preventivo de achados e indicadores.",
        nextMeetingLabel: "30/06/2026",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Q2/2026",
        ataLabel: "Pauta automatica pronta para reuniao de 30/06/2026",
        evidenceLabel:
          "Consolidado trimestral de NCs, reclamacoes, riscos, auditoria interna e indicadores anexado para a pauta ordinaria.",
        agendaItems: [
          { key: "customer-needs", label: "Mudancas nas necessidades do cliente", status: "ready" },
          { key: "objectives", label: "Atendimento de objetivos", status: "ready" },
          { key: "procedures", label: "Adequacao de politicas e procedimentos", status: "ready" },
          { key: "audits", label: "Resultado de auditorias internas e externas", status: "attention" },
          { key: "corrective-actions", label: "Acoes corretivas", status: "attention" },
          { key: "complaints", label: "Reclamacoes", status: "attention" },
          { key: "risks", label: "Resultados da identificacao de riscos", status: "attention" },
          { key: "resources", label: "Adequacao de recursos", status: "ready" },
        ],
        automaticInputs: [
          {
            key: "emission-volume",
            label: "Certificados emitidos no periodo",
            valueLabel: "142 emitidos | 0 reemissoes por erro tecnico",
            sourceLabel: "Emissao",
            status: "ready",
          },
          {
            key: "nonconformities",
            label: "NCs e reincidencia",
            valueLabel: "2 abertas | 7 fechadas | reincidencia 0%",
            sourceLabel: "Nao conformidades",
            status: "attention",
            href: "/quality/nonconformities?scenario=open-attention&nc=nc-014",
          },
          {
            key: "complaints",
            label: "Reclamacoes do periodo",
            valueLabel: "1 aberta | resposta formal pendente",
            sourceLabel: "Reclamacoes",
            status: "attention",
            href: "/quality/complaints?scenario=open-follow-up&complaint=recl-004",
          },
          {
            key: "internal-audit",
            label: "Programa de auditoria interna",
            valueLabel: "Ciclo 1 | 2 NC em follow-up",
            sourceLabel: "Auditoria interna",
            status: "attention",
            href: "/quality/internal-audit?scenario=follow-up-attention&cycle=audit-cycle-2026-1",
          },
          {
            key: "risks",
            label: "Matriz de riscos e imparcialidade",
            valueLabel: "1 declaracao pendente | 3 riscos ativos",
            sourceLabel: "Riscos",
            status: "attention",
            href: "/quality/risk-register?scenario=annual-declarations&risk=risk-003",
          },
          {
            key: "indicators",
            label: "Indicadores de qualidade",
            valueLabel: "SLA CAPA 87,5% | 2 alertas preventivos",
            sourceLabel: "Indicadores",
            status: "attention",
            href: "/quality/indicators?scenario=action-sla-attention&indicator=indicator-capa-sla",
          },
        ],
        decisions: [
          {
            key: "decision-q2-01",
            label: "Fechar NC-013 e NC-014 antes da consolidacao final da ata",
            ownerLabel: "Ana Costa",
            dueDateLabel: "30/06/2026",
            status: "attention",
          },
          {
            key: "decision-q2-02",
            label: "Reavaliar recursos de follow-up para recuperar SLA de CAPA",
            ownerLabel: "Direcao",
            dueDateLabel: "05/07/2026",
            status: "attention",
          },
        ],
        blockers: [],
        warnings: [
          "A pauta ordinaria depende do follow-up minimo de auditoria interna e NCs.",
          "O SLA de CAPA segue abaixo da meta e precisa entrar como deliberação explicita.",
        ],
        scheduledForUtc: "2026-06-30T13:00:00.000Z",
      },
    ],
  },
  "extraordinary-response": {
    label: "Analise critica extraordinaria bloqueante",
    description:
      "O recorte critico exige reuniao extraordinaria da direcao antes de qualquer reemissao ou liberacao operacional.",
    recommendedAction:
      "Convocar a reuniao extraordinaria, consolidar a pauta critica e registrar deliberação antes de qualquer desbloqueio.",
    selectedMeetingId: "review-extra-2026-04",
    meetings: [
      {
        meetingId: "review-2026-q1",
        dateLabel: "31/03/2026",
        titleLabel: "Analise critica Q1/2026",
        outcomeLabel: "Ata anterior arquivada",
        status: "ready",
        noticeLabel: "Historico ordinario mantido apenas como referencia.",
        nextMeetingLabel: "Hoje | extraordinaria",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Q1/2026",
        ataLabel: "Ata AC-2026-Q1 arquivada",
        evidenceLabel: "Historico trimestral preservado para comparacao.",
        agendaItems: ORDINARY_AGENDA,
        automaticInputs: [
          {
            key: "history-q1",
            label: "Historico encerrado",
            valueLabel: "Base anterior sem deliberação aberta",
            sourceLabel: "Ata anterior",
            status: "ready",
          },
        ],
        decisions: [
          {
            key: "decision-q1-history",
            label: "Historico anterior mantido apenas para comparacao",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Encerrada em 31/03/2026",
            status: "ready",
          },
        ],
        blockers: [],
        warnings: [],
        scheduledForUtc: "2026-03-31T13:00:00.000Z",
        heldAtUtc: "2026-03-31T14:25:00.000Z",
        signedByLabel: "Ana Costa",
        signatureDeviceId: "device-quality-01",
        signatureStatement: "Ata da analise critica Q1/2026 assinada e preservada apenas para referencia.",
        signedAtUtc: "2026-03-31T14:40:00.000Z",
      },
      {
        meetingId: "review-extra-2026-04",
        dateLabel: "Hoje | extraordinaria",
        titleLabel: "Analise critica extraordinaria 04/2026",
        outcomeLabel: "Deliberacao obrigatoria antes de liberar o caso critico",
        status: "blocked",
        noticeLabel: "Reuniao extraordinaria obrigatoria antes de qualquer reemissao ou liberacao do recorte critico.",
        nextMeetingLabel: "Hoje | extraordinaria",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Direcao, Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Recorte extraordinario de 04/2026",
        ataLabel: "Ata extraordinaria ainda nao iniciada",
        evidenceLabel:
          "Dossie critico consolidado com NC-015, trilha divergente, reclamacao, auditoria extraordinaria e indicadores em deriva.",
        agendaItems: [
          { key: "critical-case", label: "Contencao do caso critico", status: "blocked" },
          { key: "audits", label: "Resultado de auditorias internas e externas", status: "blocked" },
          { key: "corrective-actions", label: "Acoes corretivas", status: "blocked" },
          { key: "complaints", label: "Reclamacoes", status: "blocked" },
          { key: "risks", label: "Resultados da identificacao de riscos", status: "attention" },
          { key: "validity", label: "Resultados de garantia da validade", status: "blocked" },
        ],
        automaticInputs: [
          {
            key: "audit-trail",
            label: "Integridade da trilha",
            valueLabel: "1 falha de hash-chain ativa",
            sourceLabel: "Trilha de auditoria",
            status: "blocked",
            href: "/quality/audit-trail?scenario=integrity-blocked&event=audit-9",
          },
          {
            key: "nonconformities",
            label: "NCs criticas",
            valueLabel: "1 NC critica aberta | follow-up bloqueante",
            sourceLabel: "Nao conformidades",
            status: "blocked",
            href: "/quality/nonconformities?scenario=critical-response&nc=nc-015",
          },
          {
            key: "complaints",
            label: "Reclamacoes do periodo",
            valueLabel: "2 abertas | resposta formal critica pendente",
            sourceLabel: "Reclamacoes",
            status: "blocked",
            href: "/quality/complaints?scenario=critical-response&complaint=recl-007",
          },
          {
            key: "internal-audit",
            label: "Auditoria interna",
            valueLabel: "Ciclo extraordinario pendente",
            sourceLabel: "Auditoria interna",
            status: "blocked",
            href: "/quality/internal-audit?scenario=extraordinary-escalation&cycle=audit-cycle-extra-2026",
          },
          {
            key: "risks",
            label: "Riscos escalados",
            valueLabel: "1 risco critico sem decisao colegiada",
            sourceLabel: "Riscos",
            status: "blocked",
            href: "/quality/risk-register?scenario=commercial-pressure&risk=risk-001",
          },
          {
            key: "indicators",
            label: "Indicadores de qualidade",
            valueLabel: "3 indicadores em deriva critica",
            sourceLabel: "Indicadores",
            status: "blocked",
            href: "/quality/indicators?scenario=critical-drift&indicator=indicator-reissue-free",
          },
        ],
        decisions: [
          {
            key: "decision-extra-01",
            label: "Manter o recorte bloqueado ate a validacao da hash-chain",
            ownerLabel: "Direcao",
            dueDateLabel: "Imediato",
            status: "blocked",
          },
          {
            key: "decision-extra-02",
            label: "Registrar resposta formal ao cliente e caminho de reemissao controlada",
            ownerLabel: "Joao Silva",
            dueDateLabel: "48h uteis",
            status: "attention",
          },
          {
            key: "decision-extra-03",
            label: "Abrir parecer inicial da auditoria extraordinaria",
            ownerLabel: "Ana Costa",
            dueDateLabel: "Hoje",
            status: "blocked",
          },
        ],
        blockers: [
          "A reuniao extraordinaria precisa ocorrer antes de qualquer liberacao operacional do caso critico.",
          "A trilha divergente e a NC critica impedem encerrar a pauta sem deliberação formal da direcao.",
        ],
        warnings: ["Os indicadores, a reclamacao e a auditoria extraordinaria precisam entrar na mesma ata."],
        scheduledForUtc: "2026-04-23T14:00:00.000Z",
        heldAtUtc: "2026-04-23T15:30:00.000Z",
      },
    ],
  },
};

const DEFAULT_SCENARIO: ManagementReviewScenarioId = "agenda-attention";

export function listManagementReviewScenarios(): ManagementReviewScenario[] {
  return (Object.keys(SCENARIOS) as ManagementReviewScenarioId[]).map((scenarioId) =>
    resolveManagementReviewScenario(scenarioId),
  );
}

export function resolveManagementReviewScenario(
  scenarioId?: string,
  meetingId?: string,
): ManagementReviewScenario {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = resolveDefinition(resolvedScenarioId);
  const meetings = definition.meetings.map(buildMeetingItem);
  const selectedMeeting =
    meetings.find((meeting) => meeting.meetingId === meetingId) ??
    meetings.find((meeting) => meeting.meetingId === definition.selectedMeetingId) ??
    meetings[0];

  if (!selectedMeeting) {
    throw new Error("missing_management_review_meetings");
  }

  const detail = buildMeetingDetail(definition, resolvedScenarioId, selectedMeeting.meetingId);

  return {
    id: resolvedScenarioId,
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition, detail),
    selectedMeetingId: selectedMeeting.meetingId,
    meetings,
    detail,
  };
}

export function buildManagementReviewCatalog(
  scenarioId?: string,
  meetingId?: string,
): ManagementReviewCatalog {
  const selectedScenario = resolveManagementReviewScenario(scenarioId, meetingId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listManagementReviewScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

export function resolveManagementReviewScenarioMeeting(
  scenarioId: string | undefined,
  meetingId: string,
): ManagementReviewCalendarMeeting {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = resolveDefinition(resolvedScenarioId);
  return toCalendarMeeting(getMeetingState(definition, meetingId));
}

function buildMeetingItem(state: ScenarioMeetingState): ManagementReviewMeetingItem {
  return {
    meetingId: state.meetingId,
    dateLabel: state.dateLabel,
    titleLabel: state.titleLabel,
    outcomeLabel: state.outcomeLabel,
    status: state.status,
  };
}

function buildMeetingDetail(
  definition: ManagementReviewScenarioDefinition,
  scenarioId: ManagementReviewScenarioId,
  meetingId: string,
): ManagementReviewDetail {
  const meeting = getMeetingState(definition, meetingId);
  const calendar = buildManagementReviewCalendar({
    meetings: definition.meetings.map(toCalendarMeeting),
    scenarioId,
  });

  return {
    meetingId: meeting.meetingId,
    title: meeting.titleLabel,
    status: meeting.status,
    noticeLabel: meeting.noticeLabel,
    nextMeetingLabel: meeting.nextMeetingLabel,
    scheduledForLabel: formatManagementReviewSchedule(meeting.scheduledForUtc),
    chairLabel: meeting.chairLabel,
    attendeesLabel: meeting.attendeesLabel,
    periodLabel: meeting.periodLabel,
    ataLabel: meeting.ataLabel,
    evidenceLabel: meeting.evidenceLabel,
    calendarExportHref: buildManagementReviewCalendarExportHref({
      meetingId: meeting.meetingId,
      scenarioId,
    }),
    calendar,
    signature: buildManagementReviewSignature({
      heldAtUtc: meeting.heldAtUtc,
      signedAtUtc: meeting.signedAtUtc,
      signedByLabel: meeting.signedByLabel,
      signatureDeviceId: meeting.signatureDeviceId,
      signatureStatement: meeting.signatureStatement,
    }),
    agendaItems: meeting.agendaItems,
    automaticInputs: meeting.automaticInputs,
    decisions: meeting.decisions,
    blockers: meeting.blockers,
    warnings: meeting.warnings,
  };
}

function buildSummary(
  definition: ManagementReviewScenarioDefinition,
  detail: ManagementReviewDetail,
): ManagementReviewScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Analise critica ordinaria arquivada e sem deliberações abertas"
        : detail.status === "attention"
          ? "Pauta ordinaria pronta, mas ainda dependente de follow-up preventivo"
          : "Analise critica extraordinaria bloqueia liberacao do recorte critico",
    nextMeetingLabel: detail.nextMeetingLabel,
    agendaCount: detail.agendaItems.length,
    automaticInputCount: detail.automaticInputs.length,
    openDecisionCount: detail.decisions.filter((item) => item.status !== "ready").length,
    recommendedAction: definition.recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function resolveScenarioId(scenarioId?: string): ManagementReviewScenarioId {
  return isManagementReviewScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): ManagementReviewScenarioDefinition {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = SCENARIOS[resolvedScenarioId];

  if (!definition) {
    throw new Error(`missing_management_review_scenario:${resolvedScenarioId}`);
  }

  return definition;
}

function getMeetingState(
  definition: ManagementReviewScenarioDefinition,
  meetingId: string,
): ScenarioMeetingState {
  const meeting = definition.meetings.find((item) => item.meetingId === meetingId);
  if (!meeting) {
    throw new Error(`missing_management_review_meeting:${meetingId}`);
  }

  return meeting;
}

function toCalendarMeeting(meeting: ScenarioMeetingState): ManagementReviewCalendarMeeting {
  return {
    meetingId: meeting.meetingId,
    titleLabel: meeting.titleLabel,
    status: meeting.status,
    scheduledForUtc: meeting.scheduledForUtc,
    noticeLabel: meeting.noticeLabel,
    chairLabel: meeting.chairLabel,
    attendeesLabel: meeting.attendeesLabel,
    periodLabel: meeting.periodLabel,
    outcomeLabel: meeting.outcomeLabel,
    evidenceLabel: meeting.evidenceLabel,
  };
}

function isManagementReviewScenarioId(
  value: string | undefined,
): value is ManagementReviewScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
