import type {
  PortalCertificateAction,
  PortalCertificateCatalog,
  PortalCertificateDetail,
  PortalCertificateListItem,
  PortalCertificateScenario,
  PortalCertificateScenarioId,
  PortalDashboardCatalog,
  PortalDashboardScenario,
  PortalDashboardScenarioId,
  PortalEquipmentCatalog,
  PortalEquipmentDetail,
  PortalEquipmentListItem,
  PortalEquipmentScenario,
  PortalEquipmentScenarioId,
  PublicCertificateScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

import type { PersistedCustomerRecord, PersistedEquipmentRecord } from "../registry/registry-persistence.js";
import type {
  PersistedCertificatePublicationRecord,
  PersistedServiceOrderRecord,
} from "../emission/service-order-persistence.js";

type PortalCustomerContext = {
  organizationName: string;
  userEmail: string;
};

export function resolvePortalCustomerByEmail(
  context: PortalCustomerContext,
  customers: PersistedCustomerRecord[],
) {
  const normalizedEmail = context.userEmail.trim().toLowerCase();
  const matches = customers.filter(
    (customer) =>
      !customer.archivedAtUtc &&
      (customer.accountOwnerEmail === normalizedEmail || customer.contactEmail === normalizedEmail),
  );

  if (matches.length !== 1) {
    throw new Error(matches.length === 0 ? "portal_customer_not_found" : "portal_customer_ambiguous");
  }

  return matches[0]!;
}

export function buildPersistedPortalDashboardCatalog(input: {
  nowUtc: string;
  organizationName: string;
  customer: PersistedCustomerRecord;
  equipment: PersistedEquipmentRecord[];
  publications: PersistedCertificatePublicationRecord[];
}): PortalDashboardCatalog {
  const customerEquipment = selectCustomerEquipment(input.customer.customerId, input.equipment);
  const currentPublications = selectCurrentCustomerPublications(
    input.customer.customerId,
    input.publications,
  );
  const expiringEquipments = customerEquipment
    .map((item) => mapDashboardEquipmentItem(input.nowUtc, item))
    .filter((item) => item.status !== "ready")
    .sort(compareStatusThenDue);
  const status = deriveCollectionStatus(expiringEquipments.map((item) => item.status));
  const scenarioId = mapStatusToDashboardScenario(status);

  const scenario: PortalDashboardScenario = {
    id: scenarioId,
    label: dashboardScenarioLabel(scenarioId),
    description: dashboardScenarioDescription(scenarioId),
    summary: {
      status,
      clientName: input.customer.accountOwnerName,
      organizationName: input.organizationName,
      equipmentCount: customerEquipment.length,
      certificateCount: currentPublications.length,
      expiringSoonCount: expiringEquipments.filter((item) => item.status === "attention").length,
      overdueCount: expiringEquipments.filter((item) => item.status === "blocked").length,
      recommendedAction: dashboardRecommendedAction(status),
      blockers: expiringEquipments
        .filter((item) => item.status === "blocked")
        .map((item) => `${item.tag} sem certificado vigente no recorte atual.`),
      warnings: expiringEquipments
        .filter((item) => item.status === "attention")
        .map((item) => `${item.tag} vence em breve e deve entrar na proxima janela de calibracao.`),
    },
    expiringEquipments,
    recentCertificates: currentPublications.slice(0, 5).map((publication) => ({
      certificateId: publication.publicationId,
      certificateNumber: formatPublicationNumber(publication),
      equipmentLabel: publication.equipmentLabel,
      issuedAtLabel: formatDate(publication.issuedAtUtc),
      statusLabel: publication.revision === "R0" ? "Autentico" : `Revisao ${publication.revision}`,
      verifyScenarioId: mapPublicationToPublicScenario(publication),
    })),
  };

  return {
    selectedScenarioId: scenario.id,
    scenarios: [scenario],
  };
}

export function buildPersistedPortalEquipmentCatalog(input: {
  nowUtc: string;
  customer: PersistedCustomerRecord;
  equipment: PersistedEquipmentRecord[];
  publications: PersistedCertificatePublicationRecord[];
  selectedEquipmentId?: string;
}): PortalEquipmentCatalog {
  const items = selectCustomerEquipment(input.customer.customerId, input.equipment).map((item) =>
    mapPortalEquipmentListItem(input.nowUtc, item),
  );
  const selectedItem = items.find((item) => item.equipmentId === input.selectedEquipmentId) ?? items[0];
  if (!selectedItem) {
    throw new Error("portal_equipment_empty");
  }

  const status = deriveCollectionStatus(items.map((item) => item.status));
  const scenarioId = mapStatusToEquipmentScenario(status);
  const detail = buildPortalEquipmentDetail({
    nowUtc: input.nowUtc,
    customer: input.customer,
    equipment: input.equipment.find((item) => item.equipmentId === selectedItem.equipmentId)!,
    publications: input.publications.filter((item) => item.equipmentId === selectedItem.equipmentId),
  });

  const scenario: PortalEquipmentScenario = {
    id: scenarioId,
    label: equipmentScenarioLabel(scenarioId),
    description: equipmentScenarioDescription(scenarioId),
    summary: {
      status,
      headline: equipmentHeadline(status),
      equipmentCount: items.length,
      attentionCount: items.filter((item) => item.status === "attention").length,
      blockedCount: items.filter((item) => item.status === "blocked").length,
      recommendedAction: dashboardRecommendedAction(status),
      blockers: items
        .filter((item) => item.status === "blocked")
        .map((item) => `${item.tag} ultrapassou a validade e exige atendimento imediato.`),
      warnings: items
        .filter((item) => item.status === "attention")
        .map((item) => `${item.tag} entra em janela preventiva nos proximos 30 dias.`),
    },
    selectedEquipmentId: selectedItem.equipmentId,
    items,
    detail,
  };

  return {
    selectedScenarioId: scenario.id,
    scenarios: [scenario],
  };
}

export function buildPersistedPortalCertificateCatalog(input: {
  nowUtc: string;
  organizationName: string;
  customer: PersistedCustomerRecord;
  equipment: PersistedEquipmentRecord[];
  publications: PersistedCertificatePublicationRecord[];
  serviceOrders: PersistedServiceOrderRecord[];
  selectedCertificateId?: string;
}): PortalCertificateCatalog {
  const items = input.publications
    .filter((publication) => publication.customerId === input.customer.customerId)
    .sort(comparePublicationDesc)
    .map(mapPortalCertificateListItem);
  const selectedItem = items.find((item) => item.certificateId === input.selectedCertificateId) ?? items[0];
  if (!selectedItem) {
    throw new Error("portal_certificate_empty");
  }

  const selectedPublication = input.publications.find(
    (publication) => publication.publicationId === selectedItem.certificateId,
  );
  if (!selectedPublication) {
    throw new Error("portal_certificate_selected_missing");
  }

  const selectedOrder = input.serviceOrders.find(
    (record) => record.serviceOrderId === selectedPublication.serviceOrderId,
  );
  if (!selectedOrder) {
    throw new Error("portal_certificate_service_order_missing");
  }

  const equipmentCatalog = buildPersistedPortalEquipmentCatalog({
    nowUtc: input.nowUtc,
    customer: input.customer,
    equipment: input.equipment,
    publications: input.publications,
    selectedEquipmentId: selectedPublication.equipmentId,
  });
  const dashboardCatalog = buildPersistedPortalDashboardCatalog({
    nowUtc: input.nowUtc,
    organizationName: input.organizationName,
    customer: input.customer,
    equipment: input.equipment,
    publications: input.publications,
  });

  const scenarioId = derivePortalCertificateScenarioId(selectedPublication);
  const detail = buildPortalCertificateDetail({
    publication: selectedPublication,
    serviceOrder: selectedOrder,
    equipmentScenarioId: equipmentCatalog.selectedScenarioId,
    dashboardScenarioId: dashboardCatalog.selectedScenarioId,
  });

  const scenario: PortalCertificateScenario = {
    id: scenarioId,
    label: certificateScenarioLabel(scenarioId),
    description: certificateScenarioDescription(scenarioId),
    summary: {
      status: deriveCollectionStatus(items.map((item) => item.status)),
      headline: certificateHeadline(items),
      totalCertificates: items.length,
      readyCount: items.filter((item) => item.status === "ready").length,
      attentionCount: items.filter((item) => item.status === "attention").length,
      blockedCount: items.filter((item) => item.status === "blocked").length,
      recommendedAction:
        scenarioId === "download-blocked"
          ? "Regularizar a publicação antes de compartilhar ou baixar o documento."
          : selectedPublication.revision === "R0"
            ? "Usar o link público ou o PDF autenticado conforme a necessidade do cliente."
            : "Conferir a revisão vigente e manter o histórico anterior acessível para auditoria.",
      blockers: detail.blockers,
      warnings: detail.warnings,
    },
    selectedCertificateId: selectedItem.certificateId,
    items,
    detail,
  };

  return {
    selectedScenarioId: scenario.id,
    scenarios: [scenario],
  };
}

function buildPortalEquipmentDetail(input: {
  nowUtc: string;
  customer: PersistedCustomerRecord;
  equipment: PersistedEquipmentRecord;
  publications: PersistedCertificatePublicationRecord[];
}): PortalEquipmentDetail {
  const status = deriveEquipmentStatus(input.nowUtc, input.equipment.nextCalibrationAtUtc);
  const publications = [...input.publications].sort(comparePublicationDesc);

  return {
    equipmentId: input.equipment.equipmentId,
    title: `${input.equipment.tagCode} · ${input.equipment.typeModelLabel}`,
    status,
    manufacturerLabel: extractManufacturer(input.equipment.typeModelLabel),
    modelLabel: input.equipment.typeModelLabel,
    serialLabel: input.equipment.serialNumber,
    capacityClassLabel: input.equipment.capacityClassLabel,
    locationLabel: renderEquipmentLocation(input.equipment),
    recommendedAction:
      status === "blocked"
        ? "Regularizar imediatamente a calibracao antes do proximo uso critico."
        : status === "attention"
          ? "Planejar a proxima calibracao antes do vencimento."
          : "Manter o acompanhamento normal da carteira.",
    blockers:
      status === "blocked"
        ? [`${input.equipment.tagCode} ultrapassou a validade planejada do certificado.`]
        : [],
    warnings:
      status === "attention"
        ? [`${input.equipment.tagCode} entra em janela preventiva nos proximos 30 dias.`]
        : [],
    certificateHistory: publications.length > 0
      ? publications.map((publication) => ({
          certificateId: publication.publicationId,
          issuedAtLabel: formatDate(publication.issuedAtUtc),
          certificateNumber: formatPublicationNumber(publication),
          resultLabel: publication.revision === "R0" ? "Certificado autenticado" : "Revisao rastreada",
          uncertaintyLabel: publication.reissueReason ?? "Historico vinculado ao certificado emitido.",
          verifyScenarioId: mapPublicationToPublicScenario(publication),
        }))
      : [
          {
            certificateId: input.equipment.equipmentId,
            issuedAtLabel: "Sem emissao",
            certificateNumber: "Pendente",
            resultLabel: "Aguardando primeira emissao",
            uncertaintyLabel: "Sem historico publico disponivel.",
            verifyScenarioId: "not-found",
          },
        ],
  };
}

function buildPortalCertificateDetail(input: {
  publication: PersistedCertificatePublicationRecord;
  serviceOrder: PersistedServiceOrderRecord;
  equipmentScenarioId: PortalEquipmentScenarioId;
  dashboardScenarioId: PortalDashboardScenarioId;
}): PortalCertificateDetail {
  const scenarioId = derivePortalCertificateScenarioId(input.publication);
  const status =
    scenarioId === "download-blocked" ? "blocked" : scenarioId === "reissued-history" ? "attention" : "ready";
  const publicLink = `https://${input.publication.qrHost}/verify?certificate=${encodeURIComponent(
    input.publication.serviceOrderId,
  )}&token=${encodeURIComponent(input.publication.publicVerificationToken)}`;

  return {
    certificateId: input.publication.publicationId,
    title: formatPublicationNumber(input.publication),
    status,
    hashLabel: `sha256:${input.publication.documentHash.slice(0, 16)}`,
    signatureLabel:
      input.serviceOrder.signatoryName && input.publication.signedAtUtc
        ? `Assinado por ${input.serviceOrder.signatoryName} em ${formatDateTime(input.publication.signedAtUtc)}`
        : "Assinatura indisponivel",
    viewerLabel:
      status === "blocked"
        ? "Viewer integral bloqueado ate recompor a publicacao"
        : input.publication.revision === "R0"
          ? "Viewer autenticado disponivel"
          : `Viewer autenticado da revisao ${input.publication.revision}`,
    publicLinkLabel: publicLink,
    recommendedAction:
      status === "blocked"
        ? "Recompor a publicacao antes de disponibilizar o certificado ao cliente."
        : input.publication.revision === "R0"
          ? "Usar o QR publico para terceiros e o portal autenticado para a leitura integral."
          : "Conferir a revisao vigente e manter o certificado anterior apenas como historico rastreado.",
    metadataFields: [
      { label: "Numero base", value: input.publication.certificateNumber },
      { label: "Revisao", value: input.publication.revision },
      { label: "Emitido em", value: formatDateTime(input.publication.issuedAtUtc) },
      { label: "OS", value: input.publication.workOrderNumber },
      ...(input.publication.previousCertificateHash
        ? [{ label: "Hash anterior", value: `sha256:${input.publication.previousCertificateHash.slice(0, 16)}` }]
        : []),
      ...(input.publication.replacementCertificateNumber
        ? [{ label: "Substituido por", value: input.publication.replacementCertificateNumber }]
        : []),
    ],
    actions: buildCertificateActions(status),
    verificationSteps: [
      "Conferir o hash resumido exibido no portal autenticado.",
      "Usar o link publico para verificacao externa por QR.",
      "Em caso de revisao R1/R2, manter o historico anterior apenas para rastreabilidade.",
    ],
    blockers:
      status === "blocked"
        ? ["A publicacao atual nao possui QR ou hash suficientes para liberar o viewer integral."]
        : [],
    warnings:
      input.publication.revision !== "R0"
        ? ["Este certificado faz parte de uma reemissao controlada e preserva historico anterior."]
        : [],
    equipmentId: input.publication.equipmentId,
    equipmentScenarioId: input.equipmentScenarioId,
    dashboardScenarioId: input.dashboardScenarioId,
    publicVerifyScenarioId: mapPublicationToPublicScenario(input.publication),
  };
}

function buildCertificateActions(status: RegistryOperationalStatus): PortalCertificateAction[] {
  const actionStatus = status === "blocked" ? "blocked" : "ready";
  return [
    { key: "download_pdf", label: "Baixar PDF", status: actionStatus },
    { key: "share_public_link", label: "Compartilhar link publico", status: actionStatus },
    { key: "print_certificate", label: "Imprimir certificado", status: actionStatus },
  ];
}

function mapDashboardEquipmentItem(
  nowUtc: string,
  equipment: PersistedEquipmentRecord,
): PortalDashboardScenario["expiringEquipments"][number] {
  return {
    equipmentId: equipment.equipmentId,
    tag: equipment.tagCode,
    description: equipment.typeModelLabel,
    locationLabel: renderEquipmentLocation(equipment),
    lastCalibrationLabel: equipment.lastCalibrationAtUtc ? formatDate(equipment.lastCalibrationAtUtc) : "Nao informado",
    dueAtLabel: equipment.nextCalibrationAtUtc ? formatDate(equipment.nextCalibrationAtUtc) : "Nao informado",
    status: deriveEquipmentStatus(nowUtc, equipment.nextCalibrationAtUtc),
  };
}

function mapPortalEquipmentListItem(
  nowUtc: string,
  equipment: PersistedEquipmentRecord,
): PortalEquipmentListItem {
  return {
    equipmentId: equipment.equipmentId,
    tag: equipment.tagCode,
    description: equipment.typeModelLabel,
    manufacturerModelLabel: equipment.typeModelLabel,
    locationLabel: renderEquipmentLocation(equipment),
    lastCalibrationLabel: equipment.lastCalibrationAtUtc ? formatDate(equipment.lastCalibrationAtUtc) : "Nao informado",
    nextDueLabel: equipment.nextCalibrationAtUtc ? formatDate(equipment.nextCalibrationAtUtc) : "Nao informado",
    status: deriveEquipmentStatus(nowUtc, equipment.nextCalibrationAtUtc),
  };
}

function mapPortalCertificateListItem(
  publication: PersistedCertificatePublicationRecord,
): PortalCertificateListItem {
  const scenarioId = derivePortalCertificateScenarioId(publication);
  return {
    certificateId: publication.publicationId,
    certificateNumber: formatPublicationNumber(publication),
    equipmentLabel: publication.equipmentLabel,
    issuedAtLabel: formatDate(publication.issuedAtUtc),
    statusLabel:
      scenarioId === "download-blocked"
        ? "Publicacao bloqueada"
        : publication.revision === "R0"
          ? "Autentico"
          : `Revisao ${publication.revision}`,
    verifyScenarioId: mapPublicationToPublicScenario(publication),
    status:
      scenarioId === "download-blocked"
        ? "blocked"
        : publication.revision === "R0"
          ? "ready"
          : "attention",
  };
}

function selectCustomerEquipment(customerId: string, equipment: PersistedEquipmentRecord[]) {
  return equipment.filter((item) => item.customerId === customerId && !item.archivedAtUtc);
}

function selectCurrentCustomerPublications(
  customerId: string,
  publications: PersistedCertificatePublicationRecord[],
) {
  return publications
    .filter((publication) => publication.customerId === customerId && !publication.supersededAtUtc)
    .sort(comparePublicationDesc);
}

function comparePublicationDesc(
  left: PersistedCertificatePublicationRecord,
  right: PersistedCertificatePublicationRecord,
) {
  if (left.issuedAtUtc !== right.issuedAtUtc) {
    return right.issuedAtUtc.localeCompare(left.issuedAtUtc);
  }

  return right.createdAtUtc.localeCompare(left.createdAtUtc);
}

function compareStatusThenDue(
  left: PortalDashboardScenario["expiringEquipments"][number],
  right: PortalDashboardScenario["expiringEquipments"][number],
) {
  const weight = (status: RegistryOperationalStatus) =>
    status === "blocked" ? 0 : status === "attention" ? 1 : 2;
  if (weight(left.status) !== weight(right.status)) {
    return weight(left.status) - weight(right.status);
  }

  return left.dueAtLabel.localeCompare(right.dueAtLabel);
}

function deriveEquipmentStatus(nowUtc: string, nextCalibrationAtUtc?: string): RegistryOperationalStatus {
  if (!nextCalibrationAtUtc) {
    return "attention";
  }

  const diffDays = Math.floor((new Date(nextCalibrationAtUtc).getTime() - new Date(nowUtc).getTime()) / 86400000);
  if (diffDays < 0) {
    return "blocked";
  }
  if (diffDays <= 30) {
    return "attention";
  }

  return "ready";
}

function deriveCollectionStatus(statuses: RegistryOperationalStatus[]): RegistryOperationalStatus {
  if (statuses.includes("blocked")) {
    return "blocked";
  }
  if (statuses.includes("attention")) {
    return "attention";
  }

  return "ready";
}

function mapStatusToDashboardScenario(status: RegistryOperationalStatus): PortalDashboardScenarioId {
  return status === "blocked" ? "overdue-blocked" : status === "attention" ? "expiring-soon" : "stable-portfolio";
}

function mapStatusToEquipmentScenario(status: RegistryOperationalStatus): PortalEquipmentScenarioId {
  return mapStatusToDashboardScenario(status);
}

function derivePortalCertificateScenarioId(
  publication: PersistedCertificatePublicationRecord,
): PortalCertificateScenarioId {
  if (!publication.documentHash || !publication.publicVerificationToken) {
    return "download-blocked";
  }
  if (publication.revision !== "R0" || Boolean(publication.replacementCertificateNumber)) {
    return "reissued-history";
  }

  return "current-valid";
}

function mapPublicationToPublicScenario(
  publication: PersistedCertificatePublicationRecord,
): PublicCertificateScenarioId {
  return publication.supersededAtUtc ? "reissued" : "authentic";
}

function dashboardScenarioLabel(scenarioId: PortalDashboardScenarioId) {
  switch (scenarioId) {
    case "overdue-blocked":
      return "Carteira com equipamento vencido";
    case "expiring-soon":
      return "Carteira em janela preventiva";
    default:
      return "Carteira estavel";
  }
}

function dashboardScenarioDescription(scenarioId: PortalDashboardScenarioId) {
  switch (scenarioId) {
    case "overdue-blocked":
      return "O portal do cliente encontrou ao menos um equipamento vencido e exige acao imediata.";
    case "expiring-soon":
      return "O portal destaca equipamentos que entram em vencimento nos proximos 30 dias.";
    default:
      return "O cliente acompanha a carteira ativa sem alertas criticos no recorte atual.";
  }
}

function equipmentScenarioLabel(scenarioId: PortalEquipmentScenarioId) {
  return dashboardScenarioLabel(scenarioId);
}

function equipmentScenarioDescription(scenarioId: PortalEquipmentScenarioId) {
  return dashboardScenarioDescription(scenarioId);
}

function certificateScenarioLabel(scenarioId: PortalCertificateScenarioId) {
  switch (scenarioId) {
    case "download-blocked":
      return "Viewer bloqueado";
    case "reissued-history":
      return "Historico de reemissao";
    default:
      return "Certificado autenticado";
  }
}

function certificateScenarioDescription(scenarioId: PortalCertificateScenarioId) {
  switch (scenarioId) {
    case "download-blocked":
      return "O portal falha fechado quando a publicacao do certificado nao esta completa.";
    case "reissued-history":
      return "O viewer destaca a revisao vigente e preserva o historico da reemissao controlada.";
    default:
      return "O cliente visualiza o certificado autenticado com hash, assinatura e QR publico.";
  }
}

function dashboardRecommendedAction(status: RegistryOperationalStatus) {
  switch (status) {
    case "blocked":
      return "Abrir atendimento imediato para regularizar o equipamento vencido.";
    case "attention":
      return "Programar a proxima calibracao antes de perder validade.";
    default:
      return "Manter o monitoramento periodico da carteira do cliente.";
  }
}

function equipmentHeadline(status: RegistryOperationalStatus) {
  switch (status) {
    case "blocked":
      return "Carteira do cliente com bloqueio operacional";
    case "attention":
      return "Carteira do cliente com vencimentos proximos";
    default:
      return "Carteira do cliente pronta para consulta";
  }
}

function certificateHeadline(items: PortalCertificateListItem[]) {
  const reissuedCount = items.filter((item) => item.status === "attention").length;
  const blockedCount = items.filter((item) => item.status === "blocked").length;
  if (blockedCount > 0) {
    return "Alguns certificados exigem recompor a publicacao antes do download.";
  }
  if (reissuedCount > 0) {
    return "A carteira contem revisoes rastreadas sem perder o historico anterior.";
  }

  return "Certificados autenticados prontos para consulta.";
}

function formatPublicationNumber(publication: PersistedCertificatePublicationRecord) {
  return publication.revision !== "R0"
    ? `${publication.certificateNumber}-${publication.revision}`
    : publication.certificateNumber;
}

function renderEquipmentLocation(equipment: PersistedEquipmentRecord) {
  return `${equipment.addressCity}/${equipment.addressState}`;
}

function extractManufacturer(typeModelLabel: string) {
  return typeModelLabel.split(" ").slice(0, 1).join(" ") || "Fabricante nao informado";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(new Date(value));
}
