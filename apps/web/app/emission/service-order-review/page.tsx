import { cookies } from "next/headers";
import type { ServiceOrderMeasurementRawData } from "@afere/contracts";

import { loadAuthSession } from "@/src/auth/session-api";
import { loadUserDirectoryCatalog } from "@/src/auth/user-directory-api";
import { loadServiceOrderReviewCatalog } from "@/src/emission/service-order-review-api";
import { buildServiceOrderReviewCatalogView } from "@/src/emission/service-order-review-scenarios";
import { loadCustomerRegistryCatalog } from "@/src/registry/customer-registry-api";
import { loadEquipmentRegistryCatalog } from "@/src/registry/equipment-registry-api";
import { loadProcedureRegistryCatalog } from "@/src/registry/procedure-registry-api";
import { loadStandardRegistryCatalog } from "@/src/registry/standard-registry-api";
import { AppShell, NavCard, StatusPill } from "@/ui/components/chrome";

const API_BASE_URL = process.env.AFERE_API_BASE_URL ?? "http://127.0.0.1:3000";
const WEB_BASE_URL = "http://127.0.0.1:3002";

type PageProps = {
  searchParams?: {
    scenario?: string;
    item?: string;
  };
};

export const dynamic = "force-dynamic";

function statusTone(status: "ready" | "attention" | "blocked"): "ok" | "warn" {
  return status === "ready" ? "ok" : "warn";
}

function statusLabel(status: "ready" | "attention" | "blocked"): string {
  switch (status) {
    case "ready":
      return "Revisao pronta";
    case "attention":
      return "Revisao em atencao";
    case "blocked":
      return "Revisao bloqueada";
    default:
      return status;
  }
}

function itemStatusLabel(
  status: "in_execution" | "awaiting_review" | "awaiting_signature" | "emitted" | "blocked",
): string {
  switch (status) {
    case "in_execution":
      return "Em execucao";
    case "awaiting_review":
      return "Aguardando revisao";
    case "awaiting_signature":
      return "Aguardando assinatura";
    case "emitted":
      return "Emitida";
    case "blocked":
      return "Bloqueada";
    default:
      return status;
  }
}

function timelineLabel(status: "complete" | "current" | "pending"): string {
  switch (status) {
    case "complete":
      return "Concluida";
    case "current":
      return "Atual";
    case "pending":
      return "Pendente";
    default:
      return status;
  }
}

function actionLabel(
  action: "return_to_technician" | "approve_review" | "open_preview" | "open_signature_queue",
): string {
  switch (action) {
    case "return_to_technician":
      return "Devolver ao tecnico";
    case "approve_review":
      return "Aprovar revisao";
    case "open_preview":
      return "Abrir previa";
    case "open_signature_queue":
      return "Abrir fila de assinatura";
    default:
      return action;
  }
}

function buildMeasurementRawDataDraft(unit = "kg"): ServiceOrderMeasurementRawData {
  return {
    captureMode: "manual",
    environment: {
      temperatureStartC: 22,
      temperatureEndC: 22.2,
      relativeHumidityPercent: 48,
      atmosphericPressureHpa: 1013,
    },
    repeatabilityRuns: [
      {
        loadValue: 15,
        unit,
        indications: [15.001, 15.001, 15.002, 15.001, 15.001],
      },
    ],
    eccentricityPoints: [
      {
        positionLabel: "centro",
        loadValue: 15,
        indicationValue: 15.001,
        unit,
      },
      {
        positionLabel: "frontal",
        loadValue: 15,
        indicationValue: 15.003,
        unit,
      },
    ],
    linearityPoints: [
      {
        pointLabel: "50%",
        sequence: "ascending",
        appliedLoadValue: 15,
        referenceValue: 15,
        indicationValue: 15.001,
        unit,
      },
    ],
    evidenceAttachments: [
      {
        attachmentId: "evidence-001",
        label: "Foto da montagem",
        kind: "photo",
        mediaType: "image/jpeg",
      },
    ],
  };
}

function formatMeasurementRawDataValue(
  rawData?: ServiceOrderMeasurementRawData,
  unit?: string,
): string {
  return JSON.stringify(rawData ?? buildMeasurementRawDataDraft(unit), null, 2);
}

function summarizeMeasurementRawData(rawData?: ServiceOrderMeasurementRawData): string[] {
  if (!rawData) {
    return ["Sem leituras estruturadas persistidas nesta OS."];
  }

  const summary = [
    `Modo de captura: ${rawData.captureMode}`,
    `Repetitividade: ${rawData.repeatabilityRuns.length} serie(s)`,
    `Excentricidade: ${rawData.eccentricityPoints.length} ponto(s)`,
    `Linearidade: ${rawData.linearityPoints.length} ponto(s)`,
    `Anexos estruturados: ${rawData.evidenceAttachments.length}`,
  ];

  if (rawData.environment) {
    summary.push(
      `Ambiente estruturado: ${rawData.environment.temperatureStartC} a ${rawData.environment.temperatureEndC} C / ${rawData.environment.relativeHumidityPercent}% UR`,
    );
  }

  return summary;
}

function mapServiceOrderScenarioToRegistryContext(scenarioId: string): {
  scenarioId: string;
  customerId: string;
  equipmentId: string;
} {
  switch (scenarioId) {
    case "history-pending":
      return {
        scenarioId: "certificate-attention",
        customerId: "customer-003",
        equipmentId: "equipment-003",
      };
    case "review-blocked":
      return {
        scenarioId: "registration-blocked",
        customerId: "customer-004",
        equipmentId: "equipment-004",
      };
    default:
      return {
        scenarioId: "operational-ready",
        customerId: "customer-001",
        equipmentId: "equipment-001",
      };
  }
}

function mapServiceOrderScenarioToProcedureContext(scenarioId: string): {
  scenarioId: string;
  procedureId: string;
} {
  switch (scenarioId) {
    case "review-blocked":
      return {
        scenarioId: "revision-attention",
        procedureId: "procedure-pt009-r02",
      };
    default:
      return {
        scenarioId: "operational-ready",
        procedureId: "procedure-pt005-r04",
      };
  }
}

function mapServiceOrderScenarioToAuditTrailContext(scenarioId: string): {
  scenarioId: string;
  eventId: string;
} {
  switch (scenarioId) {
    case "history-pending":
      return {
        scenarioId: "reissue-attention",
        eventId: "audit-7",
      };
    case "review-blocked":
      return {
        scenarioId: "integrity-blocked",
        eventId: "audit-3",
      };
    default:
      return {
        scenarioId: "recent-emission",
        eventId: "audit-4",
      };
  }
}

export default async function ServiceOrderReviewPage(props: PageProps) {
  const cookieHeader = cookies().toString();
  const authSession = await loadAuthSession({ cookieHeader });
  const catalog = await loadServiceOrderReviewCatalog({
    scenarioId: props.searchParams?.scenario,
    itemId: props.searchParams?.item,
    cookieHeader,
  });
  const isPersistedMode = authSession?.authenticated === true && !props.searchParams?.scenario;

  const [customerCatalog, equipmentCatalog, procedureCatalog, standardCatalog, userDirectoryCatalog] =
    isPersistedMode
      ? await Promise.all([
          loadCustomerRegistryCatalog({ cookieHeader }),
          loadEquipmentRegistryCatalog({ cookieHeader }),
          loadProcedureRegistryCatalog({ cookieHeader }),
          loadStandardRegistryCatalog({ cookieHeader }),
          loadUserDirectoryCatalog({ cookieHeader }),
        ])
      : [null, null, null, null, null];

  if (!catalog && authSession?.authenticated === false && !props.searchParams?.scenario) {
    return (
      <AppShell
        eyebrow="Emissao - OS e revisao tecnica"
        title="Lista protegida por sessao"
        description="As ordens de servico persistidas do tenant exigem autenticacao antes da leitura."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Acesso atual</span>
            <strong>Login necessario</strong>
            <StatusPill tone="warn" label="RBAC ativo" />
            <p>Entre com um papel operacional para abrir, editar e revisar OS reais do tenant.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="button-row">
            <a className="button-primary" href="/auth/login">
              Fazer login
            </a>
          </div>
        </section>
      </AppShell>
    );
  }

  if (!catalog && isPersistedMode) {
    const customerOptions = customerCatalog?.scenarios[0]?.customers ?? [];
    const equipmentOptions = equipmentCatalog?.scenarios[0]?.items ?? [];
    const procedureOptions = procedureCatalog?.scenarios[0]?.items ?? [];
    const standardOptions = standardCatalog?.scenarios[0]?.items ?? [];
    const userOptions = userDirectoryCatalog?.scenarios[0]?.users.filter((user) => user.status === "active") ?? [];

    return (
      <AppShell
        eyebrow="Emissao - OS e revisao tecnica"
        title="Nenhuma OS persistida cadastrada"
        description="A V3 persistida ja aceita abertura real de ordem de servico; este tenant ainda nao possui uma OS salva."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Modo atual</span>
            <strong>V3 persistida</strong>
            <StatusPill tone="warn" label="Sem OS" />
            <p>Abra a primeira OS real usando os cadastros V2 ja persistidos do tenant autenticado.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Abrir OS</span>
            <h2>Criar a primeira ordem de servico persistida</h2>
            <p>Cliente, equipamento, procedimento, padrao e executor sao obrigatorios e falham fechado no backend.</p>
          </div>

          <form className="form-grid" action={`${API_BASE_URL}/emission/service-order-review/manage`} method="post">
            <input type="hidden" name="action" value="save" />
            <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/emission/service-order-review`} />

            <label className="field">
              <span>Numero da OS</span>
              <input name="workOrderNumber" placeholder="OS-2026-0201" required />
            </label>
            <label className="field">
              <span>Cliente</span>
              <select name="customerId" required>
                <option value="">Selecione</option>
                {customerOptions.map((customer) => (
                  <option key={customer.customerId} value={customer.customerId}>
                    {customer.tradeName}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Equipamento</span>
              <select name="equipmentId" required>
                <option value="">Selecione</option>
                {equipmentOptions.map((equipment) => (
                  <option key={equipment.equipmentId} value={equipment.equipmentId}>
                    {equipment.code} · {equipment.customerName}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Procedimento</span>
              <select name="procedureId" required>
                <option value="">Selecione</option>
                {procedureOptions.map((procedure) => (
                  <option key={procedure.procedureId} value={procedure.procedureId}>
                    {procedure.code} rev.{procedure.revisionLabel}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Padrao principal</span>
              <select name="primaryStandardId" required>
                <option value="">Selecione</option>
                {standardOptions.map((standard) => (
                  <option key={standard.standardId} value={standard.standardId}>
                    {standard.standardId} · {standard.nominalClassLabel}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Tecnico executor</span>
              <select name="executorUserId" required>
                <option value="">Selecione</option>
                {userOptions.map((user) => (
                  <option key={user.userId} value={user.userId}>
                    {user.displayName}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Revisor atribuido</span>
              <select name="reviewerUserId">
                <option value="">Atribuir depois</option>
                {userOptions.map((user) => (
                  <option key={user.userId} value={user.userId}>
                    {user.displayName}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Signatario atribuido</span>
              <select name="signatoryUserId">
                <option value="">Atribuir depois</option>
                {userOptions.map((user) => (
                  <option key={user.userId} value={user.userId}>
                    {user.displayName}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Status</span>
              <select defaultValue="in_execution" name="workflowStatus">
                <option value="in_execution">Em execucao</option>
                <option value="awaiting_review">Aguardando revisao</option>
                <option value="awaiting_signature">Aguardando assinatura</option>
                <option value="blocked">Bloqueada</option>
                <option value="emitted">Emitida</option>
              </select>
            </label>
            <label className="field">
              <span>Ambiente</span>
              <input name="environmentLabel" placeholder="22,0 C · 48% UR" required />
            </label>
            <label className="field">
              <span>Pontos da curva</span>
              <input name="curvePointsLabel" placeholder="5 pontos (10% / 25% / 50% / 75% / 100%)" required />
            </label>
            <label className="field">
              <span>Evidencias</span>
              <input name="evidenceLabel" placeholder="8 evidencias anexadas" required />
            </label>
            <label className="field">
              <span>Incerteza</span>
              <input name="uncertaintyLabel" placeholder="U = 0,12 kg (k=2)" required />
            </label>
            <label className="field">
              <span>Conformidade</span>
              <input name="conformityLabel" placeholder="Aprovado com banda de guarda" required />
            </label>
            <label className="field">
              <span>Resultado da medicao</span>
              <input inputMode="decimal" name="measurementResultValue" placeholder="100,02" />
            </label>
            <label className="field">
              <span>U expandida</span>
              <input inputMode="decimal" name="measurementExpandedUncertaintyValue" placeholder="0,12" />
            </label>
            <label className="field">
              <span>Fator k</span>
              <input inputMode="decimal" name="measurementCoverageFactor" placeholder="2" />
            </label>
            <label className="field">
              <span>Unidade</span>
              <input name="measurementUnit" placeholder="kg" />
            </label>
            <label className="field field-full">
              <span>Dados brutos estruturados (JSON)</span>
              <textarea
                name="measurementRawData"
                defaultValue={formatMeasurementRawDataValue(undefined, "kg")}
                rows={18}
              />
            </label>
            <label className="field">
              <span>Regra de decisao</span>
              <input name="decisionRuleLabel" placeholder="ILAC G8 com banda de guarda de 50%" />
            </label>
            <label className="field">
              <span>Resultado da decisao</span>
              <input name="decisionOutcomeLabel" placeholder="Conforme" />
            </label>
            <label className="field field-full">
              <span>Declaracao livre</span>
              <textarea
                name="freeTextStatement"
                placeholder="Declaracao tecnica que seguira para previa, revisao e emissao."
                rows={3}
              />
            </label>
            <label className="field field-full">
              <span>Comentario tecnico</span>
              <textarea name="commentDraft" placeholder="Resumo para o revisor tecnico." rows={4} />
            </label>
            <div className="button-row">
              <button className="button-primary" type="submit">
                Criar OS
              </button>
            </div>
          </form>
        </section>
      </AppShell>
    );
  }

  if (!catalog) {
    return (
      <AppShell
        eyebrow="Emissao - OS e revisao tecnica"
        title="OS indisponivel para revisao"
        description="O back-office nao recebeu o payload canonico da lista e do detalhe da OS. Em fail-closed, nenhuma aprovacao local foi assumida."
        aside={
          <div className="hero-stat">
            <span className="eyebrow">Leitura atual</span>
            <strong>Backend obrigatorio</strong>
            <StatusPill tone="warn" label="Sem carga canonica" />
            <p>Suba o `apps/api` ou configure `AFERE_API_BASE_URL` para liberar a lista e a revisao canônica da OS.</p>
          </div>
        }
      >
        <section className="content-panel">
          <div className="section-copy">
            <span className="eyebrow">Proximo passo</span>
            <h2>Conectar a OS canônica ao backend</h2>
            <p>
              Esta pagina depende do endpoint `GET /emission/service-order-review`. Sem resposta valida, o web nao
              inventa linha do tempo, checklist tecnico ou acoes de aprovacao.
            </p>
          </div>
        </section>
      </AppShell>
    );
  }

  const { selectedScenario: scenario, scenarios } = buildServiceOrderReviewCatalogView(catalog);
  const selectedItem = scenario.selectedItem;
  const registryContext = mapServiceOrderScenarioToRegistryContext(scenario.id);
  const procedureContext = mapServiceOrderScenarioToProcedureContext(scenario.id);
  const auditTrailContext = mapServiceOrderScenarioToAuditTrailContext(scenario.id);
  const customerOptions = customerCatalog?.scenarios[0]?.customers ?? [];
  const equipmentOptions = equipmentCatalog?.scenarios[0]?.items ?? [];
  const procedureOptions = procedureCatalog?.scenarios[0]?.items ?? [];
  const standardOptions = standardCatalog?.scenarios[0]?.items ?? [];
  const userOptions = userDirectoryCatalog?.scenarios[0]?.users.filter((user) => user.status === "active") ?? [];

  return (
    <AppShell
      eyebrow="Emissao - OS e revisao tecnica"
      title={scenario.summary.headline}
      description={scenario.description}
      aside={
        <div className="hero-stat">
          <span className="eyebrow">Cenario ativo</span>
          <strong>{scenario.label}</strong>
          <StatusPill tone={statusTone(scenario.summary.status)} label={statusLabel(scenario.summary.status)} />
          <p>{scenario.summary.recommendedAction}</p>
        </div>
      }
    >
      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Lista</span>
          <strong>{scenario.summary.totalCount} OS no painel</strong>
          <p>
            {scenario.summary.awaitingReviewCount} aguardando revisao, {scenario.summary.awaitingSignatureCount} aguardando assinatura.
          </p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">OS selecionada</span>
          <strong>{selectedItem.workOrderNumber}</strong>
          <p>
            {selectedItem.customerName} · {selectedItem.equipmentLabel}
          </p>
          <div className="chip-list">
            <span className="chip">{selectedItem.technicianName}</span>
            <span className="chip">{selectedItem.updatedAtLabel}</span>
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Status da revisao</span>
          <strong>{statusLabel(scenario.detail.status)}</strong>
          <p>{scenario.detail.statusLine}</p>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Ordens de servico</span>
          <h2>Lista canonica do back-office</h2>
          <p>As OS abaixo refletem a leitura canônica de lista e permitem alternar o detalhe da revisão pela querystring.</p>
        </div>
      </section>

      <section className="nav-grid">
        {scenario.items.map((item) => (
          <NavCard
            key={item.itemId}
            href={
              isPersistedMode
                ? `/emission/service-order-review?item=${item.itemId}`
                : `/emission/service-order-review?scenario=${scenario.id}&item=${item.itemId}`
            }
            eyebrow={item.itemId === selectedItem.itemId ? "Selecionada" : "OS"}
            title={item.workOrderNumber}
            description={`${item.customerName} · ${item.technicianName} · atualizada ${item.updatedAtLabel}`}
            statusTone={statusTone(item.status === "blocked" ? "blocked" : item.status === "awaiting_review" ? scenario.detail.status : "ready")}
            statusLabel={itemStatusLabel(item.status)}
            cta="Abrir detalhe"
          />
        ))}
      </section>

      {isPersistedMode ? (
        <>
          <section className="content-panel">
            <div className="section-copy">
              <span className="eyebrow">Abrir OS</span>
              <h2>Criar nova ordem de servico persistida</h2>
              <p>O backend valida cliente, equipamento, procedimento, padrao e atores no tenant autenticado.</p>
            </div>

            <form className="form-grid" action={`${API_BASE_URL}/emission/service-order-review/manage`} method="post">
              <input type="hidden" name="action" value="save" />
              <input type="hidden" name="redirectTo" value={`${WEB_BASE_URL}/emission/service-order-review`} />

              <label className="field">
                <span>Numero da OS</span>
                <input name="workOrderNumber" placeholder="OS-2026-0201" required />
              </label>
              <label className="field">
                <span>Cliente</span>
                <select name="customerId" required>
                  <option value="">Selecione</option>
                  {customerOptions.map((customer) => (
                    <option key={customer.customerId} value={customer.customerId}>
                      {customer.tradeName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Equipamento</span>
                <select name="equipmentId" required>
                  <option value="">Selecione</option>
                  {equipmentOptions.map((equipment) => (
                    <option key={equipment.equipmentId} value={equipment.equipmentId}>
                      {equipment.code} · {equipment.customerName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Procedimento</span>
                <select name="procedureId" required>
                  <option value="">Selecione</option>
                  {procedureOptions.map((procedure) => (
                    <option key={procedure.procedureId} value={procedure.procedureId}>
                      {procedure.code} rev.{procedure.revisionLabel}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Padrao principal</span>
                <select name="primaryStandardId" required>
                  <option value="">Selecione</option>
                  {standardOptions.map((standard) => (
                    <option key={standard.standardId} value={standard.standardId}>
                      {standard.standardId} · {standard.nominalClassLabel}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Tecnico executor</span>
                <select name="executorUserId" required>
                  <option value="">Selecione</option>
                  {userOptions.map((user) => (
                    <option key={user.userId} value={user.userId}>
                      {user.displayName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Revisor</span>
                <select name="reviewerUserId">
                  <option value="">Atribuir depois</option>
                  {userOptions.map((user) => (
                    <option key={user.userId} value={user.userId}>
                      {user.displayName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Signatario</span>
                <select name="signatoryUserId">
                  <option value="">Atribuir depois</option>
                  {userOptions.map((user) => (
                    <option key={user.userId} value={user.userId}>
                      {user.displayName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Status inicial</span>
                <select defaultValue="in_execution" name="workflowStatus">
                  <option value="in_execution">Em execucao</option>
                  <option value="awaiting_review">Aguardando revisao</option>
                  <option value="awaiting_signature">Aguardando assinatura</option>
                  <option value="blocked">Bloqueada</option>
                  <option value="emitted">Emitida</option>
                </select>
              </label>
              <label className="field">
                <span>Ambiente</span>
                <input name="environmentLabel" placeholder="22,0 C · 48% UR" required />
              </label>
              <label className="field">
                <span>Pontos da curva</span>
                <input name="curvePointsLabel" placeholder="5 pontos com subida e descida" required />
              </label>
              <label className="field">
                <span>Evidencias</span>
                <input name="evidenceLabel" placeholder="8 evidencias anexadas" required />
              </label>
              <label className="field">
                <span>Incerteza</span>
                <input name="uncertaintyLabel" placeholder="U = 0,12 kg (k=2)" required />
              </label>
              <label className="field">
                <span>Conformidade</span>
                <input name="conformityLabel" placeholder="Aprovado com banda de guarda" required />
              </label>
              <label className="field">
                <span>Resultado da medicao</span>
                <input inputMode="decimal" name="measurementResultValue" placeholder="100,02" />
              </label>
              <label className="field">
                <span>U expandida</span>
                <input inputMode="decimal" name="measurementExpandedUncertaintyValue" placeholder="0,12" />
              </label>
              <label className="field">
                <span>Fator k</span>
                <input inputMode="decimal" name="measurementCoverageFactor" placeholder="2" />
              </label>
              <label className="field">
                <span>Unidade</span>
                <input name="measurementUnit" placeholder="kg" />
              </label>
              <label className="field">
                <span>Regra de decisao</span>
                <input name="decisionRuleLabel" placeholder="ILAC G8 com banda de guarda de 50%" />
              </label>
              <label className="field">
                <span>Resultado da decisao</span>
                <input name="decisionOutcomeLabel" placeholder="Conforme" />
              </label>
              <label className="field field-full">
                <span>Declaracao livre</span>
                <textarea
                  name="freeTextStatement"
                  placeholder="Declaracao tecnica que seguira para previa, revisao e emissao."
                  rows={3}
                />
              </label>
              <label className="field field-full">
                <span>Comentario tecnico</span>
                <textarea name="commentDraft" placeholder="Resumo para o revisor tecnico." rows={4} />
              </label>
              <div className="button-row">
                <button className="button-primary" type="submit">
                  Criar OS
                </button>
              </div>
            </form>
          </section>

          <section className="content-panel">
            <div className="section-copy">
              <span className="eyebrow">Manter OS</span>
              <h2>Editar a OS persistida selecionada</h2>
              <p>A mesma rota permite corrigir vinculos, atualizar o resumo tecnico e mover o status da OS.</p>
            </div>

            <form className="form-grid" action={`${API_BASE_URL}/emission/service-order-review/manage`} method="post">
              <input type="hidden" name="action" value="save" />
              <input type="hidden" name="serviceOrderId" value={scenario.detail.itemId} />
              <input
                type="hidden"
                name="redirectTo"
                value={`${WEB_BASE_URL}/emission/service-order-review?item=${scenario.detail.itemId}`}
              />

              <label className="field">
                <span>Numero da OS</span>
                <input defaultValue={selectedItem.workOrderNumber} name="workOrderNumber" required />
              </label>
              <label className="field">
                <span>Status</span>
                <select defaultValue={selectedItem.status} name="workflowStatus">
                  <option value="in_execution">Em execucao</option>
                  <option value="awaiting_review">Aguardando revisao</option>
                  <option value="awaiting_signature">Aguardando assinatura</option>
                  <option value="blocked">Bloqueada</option>
                  <option value="emitted">Emitida</option>
                </select>
              </label>
              <label className="field">
                <span>Cliente</span>
                <select defaultValue={scenario.detail.customerId ?? ""} name="customerId" required>
                  {customerOptions.map((customer) => (
                    <option key={customer.customerId} value={customer.customerId}>
                      {customer.tradeName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Equipamento</span>
                <select defaultValue={scenario.detail.equipmentId ?? ""} name="equipmentId" required>
                  {equipmentOptions.map((equipment) => (
                    <option key={equipment.equipmentId} value={equipment.equipmentId}>
                      {equipment.code} · {equipment.customerName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Procedimento</span>
                <select defaultValue={scenario.detail.procedureId ?? ""} name="procedureId" required>
                  {procedureOptions.map((procedure) => (
                    <option key={procedure.procedureId} value={procedure.procedureId}>
                      {procedure.code} rev.{procedure.revisionLabel}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Padrao principal</span>
                <select defaultValue={scenario.detail.primaryStandardId ?? ""} name="primaryStandardId" required>
                  {standardOptions.map((standard) => (
                    <option key={standard.standardId} value={standard.standardId}>
                      {standard.standardId} · {standard.nominalClassLabel}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Tecnico executor</span>
                <select defaultValue={scenario.detail.executorUserId ?? ""} name="executorUserId" required>
                  {userOptions.map((user) => (
                    <option key={user.userId} value={user.userId}>
                      {user.displayName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Revisor</span>
                <select defaultValue={scenario.detail.reviewerUserId ?? ""} name="reviewerUserId">
                  <option value="">Atribuir depois</option>
                  {userOptions.map((user) => (
                    <option key={user.userId} value={user.userId}>
                      {user.displayName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Signatario</span>
                <select defaultValue={scenario.detail.signatoryUserId ?? ""} name="signatoryUserId">
                  <option value="">Atribuir depois</option>
                  {userOptions.map((user) => (
                    <option key={user.userId} value={user.userId}>
                      {user.displayName}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Ambiente</span>
                <input defaultValue={scenario.detail.environmentLabel} name="environmentLabel" required />
              </label>
              <label className="field">
                <span>Pontos da curva</span>
                <input defaultValue={scenario.detail.curvePointsLabel} name="curvePointsLabel" required />
              </label>
              <label className="field">
                <span>Evidencias</span>
                <input defaultValue={scenario.detail.evidenceLabel} name="evidenceLabel" required />
              </label>
              <label className="field">
                <span>Incerteza</span>
                <input defaultValue={scenario.detail.uncertaintyLabel} name="uncertaintyLabel" required />
              </label>
              <label className="field">
                <span>Conformidade</span>
                <input defaultValue={scenario.detail.conformityLabel} name="conformityLabel" required />
              </label>
              <label className="field">
                <span>Resultado da medicao</span>
                <input
                  defaultValue={scenario.detail.measurementResultValue ?? ""}
                  inputMode="decimal"
                  name="measurementResultValue"
                />
              </label>
              <label className="field">
                <span>U expandida</span>
                <input
                  defaultValue={scenario.detail.measurementExpandedUncertaintyValue ?? ""}
                  inputMode="decimal"
                  name="measurementExpandedUncertaintyValue"
                />
              </label>
              <label className="field">
                <span>Fator k</span>
                <input
                  defaultValue={scenario.detail.measurementCoverageFactor ?? ""}
                  inputMode="decimal"
                  name="measurementCoverageFactor"
                />
              </label>
              <label className="field">
                <span>Unidade</span>
                <input defaultValue={scenario.detail.measurementUnit ?? ""} name="measurementUnit" />
              </label>
              <label className="field field-full">
                <span>Dados brutos estruturados (JSON)</span>
                <textarea
                  defaultValue={formatMeasurementRawDataValue(
                    scenario.detail.measurementRawData,
                    scenario.detail.measurementUnit,
                  )}
                  name="measurementRawData"
                  rows={18}
                />
              </label>
              <label className="field">
                <span>Regra de decisao</span>
                <input defaultValue={scenario.detail.decisionRuleLabel ?? ""} name="decisionRuleLabel" />
              </label>
              <label className="field">
                <span>Resultado da decisao</span>
                <input defaultValue={scenario.detail.decisionOutcomeLabel ?? ""} name="decisionOutcomeLabel" />
              </label>
              <label className="field field-full">
                <span>Declaracao livre</span>
                <textarea defaultValue={scenario.detail.freeTextStatement ?? ""} name="freeTextStatement" rows={3} />
              </label>
              <label className="field field-full">
                <span>Comentario tecnico</span>
                <textarea defaultValue={scenario.detail.commentDraft} name="commentDraft" rows={4} />
              </label>
              <div className="button-row">
                <button className="button-primary" type="submit">
                  Salvar OS
                </button>
              </div>
            </form>
          </section>
        </>
      ) : null}

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Detalhe da OS</span>
          <h2>{scenario.detail.title}</h2>
          <p>O painel abaixo resume linha do tempo, dados de execução e o checklist que sustentam a revisão técnica.</p>
        </div>

        <div className="detail-grid">
          <article className="detail-card">
            <span className="eyebrow">Linha do tempo</span>
            <strong>{scenario.detail.statusLine}</strong>
            <ul>
              {scenario.detail.timeline.map((step) => (
                <li key={step.key}>
                  {step.label}: {step.timestampLabel} ({timelineLabel(step.status)})
                </li>
              ))}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Dados da execucao</span>
            <strong>{scenario.detail.procedureLabel}</strong>
            <ul>
              <li>Padroes: {scenario.detail.standardsLabel}</li>
              <li>Ambiente: {scenario.detail.environmentLabel}</li>
              <li>Pontos da curva: {scenario.detail.curvePointsLabel}</li>
              <li>Evidencias: {scenario.detail.evidenceLabel}</li>
              <li>Incerteza: {scenario.detail.uncertaintyLabel}</li>
              <li>Conformidade: {scenario.detail.conformityLabel}</li>
              {scenario.detail.measurementResultValue !== undefined ? (
                <li>
                  Resultado: {scenario.detail.measurementResultValue} {scenario.detail.measurementUnit ?? ""}
                </li>
              ) : null}
              {scenario.detail.measurementExpandedUncertaintyValue !== undefined ? (
                <li>
                  U expandida: {scenario.detail.measurementExpandedUncertaintyValue} {scenario.detail.measurementUnit ?? ""}
                </li>
              ) : null}
              {scenario.detail.measurementCoverageFactor !== undefined ? (
                <li>Fator de abrangencia: k = {scenario.detail.measurementCoverageFactor}</li>
              ) : null}
              {summarizeMeasurementRawData(scenario.detail.measurementRawData).map((line) => (
                <li key={line}>Dados brutos: {line}</li>
              ))}
              {scenario.detail.decisionRuleLabel ? <li>Regra de decisao: {scenario.detail.decisionRuleLabel}</li> : null}
              {scenario.detail.decisionOutcomeLabel ? <li>Resultado da decisao: {scenario.detail.decisionOutcomeLabel}</li> : null}
              {scenario.detail.decisionAssistance ? (
                <li>Assistencia decisoria: {scenario.detail.decisionAssistance.alignmentLabel}</li>
              ) : null}
              {scenario.detail.decisionAssistance?.indicativeDecision ? (
                <li>Snapshot indicativo: {scenario.detail.decisionAssistance.indicativeDecision.summaryLabel}</li>
              ) : null}
              {scenario.detail.decisionAssistance?.officialDecisionJustification ? (
                <li>Justificativa da divergencia: {scenario.detail.decisionAssistance.officialDecisionJustification}</li>
              ) : null}
              {scenario.detail.freeTextStatement ? <li>Declaracao livre: {scenario.detail.freeTextStatement}</li> : null}
            </ul>
          </article>

          <article className="detail-card">
            <span className="eyebrow">Responsabilidades</span>
            <strong>{scenario.detail.assignedReviewerLabel}</strong>
            <p>{scenario.detail.statusLine}</p>
            <div className="chip-list">
              <span className="chip">Executor: {scenario.detail.executorLabel}</span>
              <span className="chip">Revisor: {scenario.detail.assignedReviewerLabel}</span>
              <span className="chip">Signatario: {scenario.detail.assignedSignatoryLabel ?? "Pendente"}</span>
            </div>
          </article>
        </div>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Metricas</span>
          <h2>Resumo tecnico da execucao</h2>
          <p>Essas metricas ajudam a contextualizar a analise do revisor sem substituir a leitura integral da previa.</p>
        </div>

        <div className="detail-grid">
          {scenario.detail.metrics.map((metric) => (
            <article className="detail-card" key={metric.label}>
              <span className="eyebrow">{metric.label}</span>
              <strong>{metric.value}</strong>
              <StatusPill
                tone={metric.tone === "ok" ? "ok" : metric.tone === "warn" ? "warn" : "neutral"}
                label={metric.tone === "ok" ? "OK" : metric.tone === "warn" ? "Atencao" : "Info"}
              />
            </article>
          ))}
        </div>
      </section>

      <section className="content-panel">
        <div className="section-copy">
          <span className="eyebrow">Checklist</span>
          <h2>Checklist de revisao tecnica</h2>
          <p>O checklist abaixo explica por que a OS pode ser aprovada, exige atencao complementar ou segue bloqueada.</p>
        </div>

        <ul className="check-list">
          {scenario.detail.checklist.map((item) => (
            <li key={`${scenario.detail.itemId}-${item.label}`}>
              <div className="metric-row">
                <strong>{item.label}</strong>
                <StatusPill
                  tone={item.status === "passed" ? "ok" : "warn"}
                  label={item.status === "passed" ? "Passou" : item.status === "pending" ? "Pendente" : "Falhou"}
                />
              </div>
              <p>{item.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="detail-grid">
        <article className="detail-card">
          <span className="eyebrow">Comentario de revisao</span>
          <strong>{scenario.detail.commentDraft.length > 0 ? "Rascunho disponivel" : "Sem comentario registrado"}</strong>
          <p>{scenario.detail.commentDraft || "Nenhum comentario de revisao foi registrado para esta OS neste cenario."}</p>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Acoes disponiveis</span>
          <strong>{scenario.detail.allowedActions.length} acao(oes) mapeada(s)</strong>
          <div className="chip-list">
            {scenario.detail.allowedActions.map((action) => (
              <span className="chip" key={action}>
                {actionLabel(action)}
              </span>
            ))}
          </div>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Bloqueios e warnings</span>
          <strong>
            {scenario.detail.blockers.length} bloqueio(s) · {scenario.detail.warnings.length} warning(s)
          </strong>
          <ul>
            {scenario.detail.blockers.map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
            {scenario.detail.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
            {scenario.detail.blockers.length === 0 && scenario.detail.warnings.length === 0 ? (
              <li>Sem bloqueios ou warnings adicionais neste cenario.</li>
            ) : null}
          </ul>
        </article>

        <article className="detail-card">
          <span className="eyebrow">Saida regulada</span>
          <strong>{scenario.detail.certificateNumber ?? "Certificado ainda nao emitido"}</strong>
          <ul>
            <li>Decisao da revisao: {scenario.detail.reviewDecision ?? "pending"}</li>
            <li>Signatario: {scenario.detail.assignedSignatoryLabel ?? "Nao atribuido"}</li>
            <li>Hash: {scenario.detail.documentHash ?? "Gerado apenas na emissao"}</li>
          </ul>
        </article>
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Atalhos</span>
          <h2>Rotas relacionadas a esta OS</h2>
          <p>Use as rotas abaixo para voltar aos sinais canônicos que sustentam esta revisão.</p>
        </div>
      </section>

      <section className="nav-grid">
        <NavCard
          href={
            isPersistedMode && scenario.detail.customerId
              ? `/registry/customer-detail?customer=${scenario.detail.customerId}`
              : `/registry/customer-detail?scenario=${registryContext.scenarioId}&customer=${registryContext.customerId}`
          }
          eyebrow="Cliente"
          title="Abrir detalhe do cliente"
          description="Conferir dados, contatos, enderecos e certificados ligados a esta OS."
          cta="Abrir cliente"
        />
        <NavCard
          href={
            isPersistedMode && scenario.detail.equipmentId
              ? `/registry/equipment?equipment=${scenario.detail.equipmentId}`
              : `/registry/equipment?scenario=${registryContext.scenarioId}&equipment=${registryContext.equipmentId}`
          }
          eyebrow="Equipamento"
          title="Abrir lista global de equipamentos"
          description="Voltar ao cadastro e ao vencimento do equipamento relacionado a esta OS."
          cta="Abrir equipamento"
        />
        <NavCard
          href={
            isPersistedMode && scenario.detail.procedureId
              ? `/registry/procedures?procedure=${scenario.detail.procedureId}`
              : `/registry/procedures?scenario=${procedureContext.scenarioId}&procedure=${procedureContext.procedureId}`
          }
          eyebrow="Procedimento"
          title="Abrir lista versionada"
          description="Conferir a vigencia e o contexto do procedimento associado a esta OS."
          cta="Abrir procedimento"
        />
        <NavCard
          href={
            isPersistedMode
              ? `/quality/audit-trail?item=${scenario.detail.itemId}`
              : `/quality/audit-trail?scenario=${auditTrailContext.scenarioId}&event=${auditTrailContext.eventId}`
          }
          eyebrow="Auditoria"
          title="Abrir trilha de auditoria"
          description="Conferir a cadeia append-only relacionada a esta OS e aos eventos criticos de emissao."
          cta="Abrir trilha"
        />
        <NavCard
          href={`/emission/workspace?scenario=${scenario.detail.links.workspaceScenarioId}`}
          eyebrow="Workspace"
          title="Abrir prontidao consolidada"
          description="Voltar ao workspace operacional agregado desta OS."
          cta="Abrir workspace"
        />
        {scenario.detail.links.previewScenarioId ? (
          <NavCard
            href={
              isPersistedMode
                ? `/emission/certificate-preview?item=${scenario.detail.itemId}`
                : `/emission/certificate-preview?scenario=${scenario.detail.links.previewScenarioId}`
            }
            eyebrow="Previa"
            title="Abrir previa do certificado"
            description="Conferir a peca canônica derivada desta mesma OS."
            cta="Abrir previa"
          />
        ) : null}
        {scenario.detail.links.reviewSignatureScenarioId ? (
          <NavCard
            href={
              isPersistedMode
                ? `/emission/review-signature?item=${scenario.detail.itemId}`
                : `/emission/review-signature?scenario=${scenario.detail.links.reviewSignatureScenarioId}`
            }
            eyebrow="Workflow"
            title="Abrir workflow de revisao"
            description="Inspecionar os checks de segregacao e elegibilidade do fluxo."
            cta="Abrir workflow"
          />
        ) : null}
        {scenario.detail.links.signatureQueueScenarioId ? (
          <NavCard
            href={
              isPersistedMode
                ? `/emission/signature-queue?item=${scenario.detail.itemId}`
                : `/emission/signature-queue?scenario=${scenario.detail.links.signatureQueueScenarioId}`
            }
            eyebrow="Fila"
            title="Abrir fila de assinatura"
            description="Seguir para a etapa final da emissao quando a OS ja estiver aprovada."
            cta="Abrir fila"
          />
        ) : null}
      </section>

      <section className="section-header">
        <div className="section-copy">
          <span className="eyebrow">Cenarios</span>
          <h2>Trocar o contexto da OS</h2>
          <p>
            {isPersistedMode
              ? "Os cards abaixo alternam o recorte pronto, em atencao ou bloqueado dentro do catalogo persistido."
              : "Os cenarios abaixo permitem revisar baseline, atencao complementar e bloqueio sem alterar codigo."}
          </p>
        </div>
      </section>

      <section className="nav-grid">
        {scenarios.map((item) => (
          <NavCard
            key={item.id}
            href={
              isPersistedMode
                ? `/emission/service-order-review?item=${item.selectedItem.itemId}`
                : `/emission/service-order-review?scenario=${item.id}&item=${item.selectedItem.itemId}`
            }
            eyebrow={item.id === scenario.id ? "Ativo" : "Disponivel"}
            title={item.label}
            description={item.summaryLabel}
            statusTone={statusTone(item.summary.status)}
            statusLabel={statusLabel(item.summary.status)}
            cta="Abrir OS"
          />
        ))}
      </section>
    </AppShell>
  );
}
