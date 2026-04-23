import type {
  CustomerAttachment,
  CustomerCertificateHighlight,
  CustomerHistoryItem,
  CustomerRegistryCatalog,
  EquipmentRegistryCatalog,
  ProcedureRegistryCatalog,
  ProcedureRegistryScenarioId,
  RegistryOperationalStatus,
  RegistryScenarioId,
  StandardCalibrationHistoryEntry,
  StandardRecentWorkOrder,
  StandardRegistryCatalog,
  StandardRegistryScenarioId,
} from "@afere/contracts";
import { evaluateStandardEligibility } from "@afere/normative-rules";

import { validateEquipmentRegistration } from "../equipment/equipment-registration.js";
import type {
  PersistedCustomerRecord,
  PersistedEquipmentRecord,
  PersistedProcedureRecord,
  PersistedRegistryAuditEventRecord,
  PersistedStandardRecord,
} from "./registry-persistence.js";

export type BuildPersistedCustomerRegistryCatalogInput = {
  nowUtc: string;
  selectedCustomerId?: string;
  customers: PersistedCustomerRecord[];
  equipment: PersistedEquipmentRecord[];
  selectedCustomerAuditEvents?: PersistedRegistryAuditEventRecord[];
};

export type BuildPersistedEquipmentRegistryCatalogInput = {
  nowUtc: string;
  selectedEquipmentId?: string;
  customers: PersistedCustomerRecord[];
  standards: PersistedStandardRecord[];
  procedures: PersistedProcedureRecord[];
  equipment: PersistedEquipmentRecord[];
};

export type BuildPersistedStandardRegistryCatalogInput = {
  nowUtc: string;
  selectedStandardId?: string;
  standards: PersistedStandardRecord[];
  equipment: PersistedEquipmentRecord[];
};

export type BuildPersistedProcedureRegistryCatalogInput = {
  nowUtc: string;
  selectedProcedureId?: string;
  procedures: PersistedProcedureRecord[];
  equipment: PersistedEquipmentRecord[];
};

type EquipmentStatusDetails = {
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
  missingFields: string[];
};

type StandardStatusDetails = {
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
  daysUntilExpiration: number | null;
};

type ProcedureStatusDetails = {
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
};

const DATE_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "UTC",
});

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC",
});

const TODAY_ONLY_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  timeZone: "UTC",
});

export function buildPersistedCustomerRegistryCatalog(
  input: BuildPersistedCustomerRegistryCatalogInput,
): CustomerRegistryCatalog {
  const customers = input.customers;
  const equipmentByCustomer = groupEquipmentByCustomer(input.equipment);
  const selectedCustomer =
    customers.find((record) => record.customerId === input.selectedCustomerId) ?? customers[0];

  if (!selectedCustomer) {
    throw new Error("persisted_customer_registry_empty");
  }

  const selectedCustomerEquipment = equipmentByCustomer.get(selectedCustomer.customerId) ?? [];
  const customerItems = customers.map((customer) =>
    buildCustomerListItem(customer, equipmentByCustomer.get(customer.customerId) ?? [], input.nowUtc),
  );
  const selectedCustomerItem =
    customerItems.find((item) => item.customerId === selectedCustomer.customerId) ?? customerItems[0];

  if (!selectedCustomerItem) {
    throw new Error("persisted_customer_registry_missing_selected");
  }

  const highlightedEquipment = selectedCustomerEquipment
    .map((record) => buildEquipmentHighlight(record, input.nowUtc))
    .slice(0, 4);
  const selectedEquipment = selectEquipment(
    highlightedEquipment,
    selectedCustomerEquipment,
    input.nowUtc,
  );
  const blockers = uniqueStrings([
    ...(selectedCustomer.archivedAtUtc ? ["Cliente arquivado no cadastro operacional."] : []),
    ...selectedCustomerEquipment.flatMap((record) =>
      resolveEquipmentStatus(record, input.nowUtc).status === "blocked"
        ? [`${record.code}: ${buildEquipmentRegistrationStatusLabel(record, input.nowUtc)}`]
        : [],
    ),
  ]);
  const warnings = uniqueStrings([
    ...selectedCustomerEquipment.flatMap((record) =>
      resolveEquipmentStatus(record, input.nowUtc).status === "attention"
        ? [`${record.code}: ${formatEquipmentNextCalibrationLabel(record, input.nowUtc)}`]
        : [],
    ),
    ...(selectedCustomerEquipment.length === 0
      ? ["Cliente ainda sem equipamento vinculado ao cadastro persistido."]
      : []),
  ]);
  const status = resolveCustomerStatus(selectedCustomer, selectedCustomerEquipment, input.nowUtc);
  const scenarioId = resolveRegistryScenarioId(status);

  const detail = {
    customerId: selectedCustomer.customerId,
    title: `${selectedCustomer.tradeName} · ${selectedCustomer.documentLabel}`,
    status,
    statusLine: buildCustomerStatusLine(status, selectedCustomer.accountOwnerName),
    accountOwnerLabel: `${selectedCustomer.accountOwnerName} (${selectedCustomer.accountOwnerEmail})`,
    contractLabel: selectedCustomer.contractLabel,
    specialConditionsLabel: selectedCustomer.specialConditionsLabel,
    tabs: [
      { key: "data" as const, label: "Dados" },
      { key: "contacts" as const, label: "Contatos", countLabel: "1" },
      { key: "addresses" as const, label: "Enderecos", countLabel: "1" },
      {
        key: "equipment" as const,
        label: "Equipamentos",
        countLabel: String(selectedCustomerEquipment.length),
      },
      {
        key: "certificates" as const,
        label: "Certificados",
        countLabel: String(buildCustomerCertificateHighlights(selectedCustomerEquipment, input.nowUtc).length),
      },
      { key: "attachments" as const, label: "Anexos", countLabel: "2" },
      {
        key: "history" as const,
        label: "Hist.",
        countLabel: String(
          buildCustomerHistory(input.selectedCustomerAuditEvents, selectedCustomer).length,
        ),
      },
    ],
    contacts: [
      {
        name: selectedCustomer.contactName,
        roleLabel: selectedCustomer.contactRoleLabel,
        email: selectedCustomer.contactEmail,
        phoneLabel: selectedCustomer.contactPhoneLabel,
        primary: true,
      },
    ],
    addresses: [
      {
        label: "Principal",
        line1: selectedCustomer.addressLine1,
        cityStateLabel: `${selectedCustomer.addressCity} / ${selectedCustomer.addressState}`,
        postalCodeLabel: selectedCustomer.addressPostalCode ?? "CEP pendente",
        countryLabel: selectedCustomer.addressCountry,
        conditionsLabel: selectedCustomer.addressConditionsLabel,
      },
    ],
    equipmentHighlights:
      highlightedEquipment.length > 0
        ? highlightedEquipment
        : [
            {
              equipmentId: "no-equipment-linked",
              code: "Sem equipamento",
              tagCode: "Pendente",
              typeModelLabel: "Vincule o primeiro equipamento para liberar a trilha operacional.",
              nextDueLabel: "Cadastrar equipamento",
              status,
            },
          ],
    certificateHighlights: buildCustomerCertificateHighlights(selectedCustomerEquipment, input.nowUtc),
    attachments: buildCustomerAttachments(selectedCustomer),
    history: buildCustomerHistory(input.selectedCustomerAuditEvents, selectedCustomer),
    blockers,
    warnings,
    links: {
      equipmentScenarioId: selectedEquipment
        ? resolveRegistryScenarioId(resolveEquipmentStatus(selectedEquipment, input.nowUtc).status)
        : scenarioId,
      selectedEquipmentId: selectedEquipment?.equipmentId,
    },
  };

  return {
    selectedScenarioId: scenarioId,
    scenarios: [
      {
        id: scenarioId,
        label: buildRegistryLabel("cliente", status),
        description: `Cadastro persistido do tenant com ${customers.length} cliente(s) carregado(s) do banco multitenant.`,
        summary: {
          status,
          headline: buildCustomerHeadline(status),
          activeCustomers: customerItems.filter((item) => item.status !== "blocked").length,
          attentionCustomers: customerItems.filter((item) => item.status === "attention").length,
          blockedCustomers: customerItems.filter((item) => item.status === "blocked").length,
          totalEquipment: input.equipment.length,
          certificatesThisMonth: customerItems.reduce(
            (sum, item) => sum + item.certificatesThisMonth,
            0,
          ),
          dueSoonCount: input.equipment.filter((record) => isDueSoon(record.nextCalibrationAtUtc, input.nowUtc))
            .length,
          recommendedAction: buildCustomerRecommendedAction(status, selectedCustomer.tradeName),
          blockers,
          warnings,
        },
        selectedCustomerId: selectedCustomer.customerId,
        customers: customerItems,
        detail,
      },
    ],
  };
}

export function buildPersistedEquipmentRegistryCatalog(
  input: BuildPersistedEquipmentRegistryCatalogInput,
): EquipmentRegistryCatalog {
  const customerMap = new Map(input.customers.map((record) => [record.customerId, record]));
  const standardMap = new Map(input.standards.map((record) => [record.standardId, record]));
  const procedureMap = new Map(input.procedures.map((record) => [record.procedureId, record]));
  const selectedEquipment =
    input.equipment.find((record) => record.equipmentId === input.selectedEquipmentId) ?? input.equipment[0];

  if (!selectedEquipment) {
    throw new Error("persisted_equipment_registry_empty");
  }

  const items = input.equipment.map((record) =>
    buildEquipmentListItem(record, customerMap.get(record.customerId), input.nowUtc),
  );
  const selectedItem =
    items.find((item) => item.equipmentId === selectedEquipment.equipmentId) ?? items[0];

  if (!selectedItem) {
    throw new Error("persisted_equipment_registry_missing_selected");
  }

  const statusDetails = resolveEquipmentStatus(selectedEquipment, input.nowUtc);
  const status = statusDetails.status;
  const customer = customerMap.get(selectedEquipment.customerId);
  const linkedProcedure = selectedEquipment.procedureId
    ? procedureMap.get(selectedEquipment.procedureId)
    : undefined;
  const primaryStandard = selectedEquipment.primaryStandardId
    ? standardMap.get(selectedEquipment.primaryStandardId)
    : undefined;
  const standardCodes = [
    ...(primaryStandard ? [primaryStandard.code] : []),
    ...selectedEquipment.supportingStandardCodes,
  ];
  const scenarioId = resolveRegistryScenarioId(status);

  const detail = {
    equipmentId: selectedEquipment.equipmentId,
    title: `${selectedEquipment.code} · ${selectedEquipment.tagCode} · ${selectedEquipment.typeModelLabel}`,
    status,
    statusLine: buildEquipmentStatusLine(status, customer?.tradeName ?? "Cliente nao vinculado"),
    customerLabel: customer?.legalName ?? "Cliente nao encontrado",
    addressLabel: formatEquipmentAddress(selectedEquipment),
    standardSetLabel:
      standardCodes.length > 0 ? standardCodes.join(" / ") : "Padroes ainda nao vinculados",
    lastServiceOrderLabel: linkedProcedure
      ? `${linkedProcedure.code} rev.${linkedProcedure.revisionLabel}`
      : "Procedimento nao vinculado",
    nextCalibrationLabel: formatEquipmentNextCalibrationLabel(selectedEquipment, input.nowUtc),
    blockers: statusDetails.blockers,
    warnings: statusDetails.warnings,
    links: {
      customerScenarioId: customer
        ? resolveRegistryScenarioId(
            resolveCustomerStatus(customer, input.equipment.filter((record) => record.customerId === customer.customerId), input.nowUtc),
          )
        : "registration-blocked",
      customerId: selectedEquipment.customerId,
    },
  };

  return {
    selectedScenarioId: scenarioId,
    scenarios: [
      {
        id: scenarioId,
        label: buildRegistryLabel("equipamento", status),
        description: `Equipamentos persistidos do tenant com ${input.equipment.length} item(ns) ativos na carteira operacional.`,
        summary: {
          status,
          headline: buildEquipmentHeadline(status),
          totalEquipment: items.length,
          readyCount: items.filter((item) => item.status === "ready").length,
          attentionCount: items.filter((item) => item.status === "attention").length,
          blockedCount: items.filter((item) => item.status === "blocked").length,
          dueSoonCount: input.equipment.filter((record) => isDueSoon(record.nextCalibrationAtUtc, input.nowUtc))
            .length,
          recommendedAction: buildEquipmentRecommendedAction(status, selectedEquipment.code),
          blockers: detail.blockers,
          warnings: detail.warnings,
        },
        selectedEquipmentId: selectedEquipment.equipmentId,
        items,
        detail,
      },
    ],
  };
}

export function buildPersistedStandardRegistryCatalog(
  input: BuildPersistedStandardRegistryCatalogInput,
): StandardRegistryCatalog {
  const relatedEquipment = input.equipment;
  const selectedStandard =
    input.standards.find((record) => record.standardId === input.selectedStandardId) ?? input.standards[0];

  if (!selectedStandard) {
    throw new Error("persisted_standard_registry_empty");
  }

  const items = input.standards.map((record) => buildStandardListItem(record, input.nowUtc));
  const selectedItem =
    items.find((item) => item.standardId === selectedStandard.standardId) ?? items[0];

  if (!selectedItem) {
    throw new Error("persisted_standard_registry_missing_selected");
  }

  const details = resolveStandardStatus(selectedStandard, input.nowUtc);
  const linkedEquipment = relatedEquipment.filter(
    (record) =>
      record.primaryStandardId === selectedStandard.standardId ||
      record.supportingStandardCodes.includes(selectedStandard.code),
  );
  const firstLinkedEquipment = linkedEquipment[0];
  const status = details.status;
  const scenarioId = resolveStandardScenarioId(status);

  return {
    selectedScenarioId: scenarioId,
    scenarios: [
      {
        id: scenarioId,
        label: buildStandardLabel(status),
        description: `Carteira persistida com ${input.standards.length} padrao(es) e auxiliares carregados do banco.`,
        summary: {
          status,
          headline: buildStandardHeadline(status),
          activeCount: items.filter((item) => item.status !== "blocked").length,
          expiringSoonCount: items.filter((item) => item.status === "attention").length,
          expiredCount: items.filter((item) => item.status === "blocked").length,
          recommendedAction: buildStandardRecommendedAction(status, selectedStandard.code),
          blockers: details.blockers,
          warnings: details.warnings,
          expirationPanel: items.map((item) => ({
            standardId: item.standardId,
            label: renderStandardPanelLabel(
              input.standards.find((record) => record.standardId === item.standardId)?.code ?? item.standardId,
            ),
            dueInLabel: renderDueInLabel(item.validUntilLabel, input.nowUtc),
            status: item.status,
          })),
        },
        selectedStandardId: selectedStandard.standardId,
        items,
        detail: {
          standardId: selectedStandard.standardId,
          title: `${selectedStandard.code} · ${selectedStandard.title}`,
          status,
          noticeLabel: buildStandardNoticeLabel(status, details.daysUntilExpiration),
          manufacturerLabel: selectedStandard.manufacturerLabel,
          modelLabel: selectedStandard.modelLabel,
          serialNumberLabel: selectedStandard.serialNumberLabel,
          nominalValueLabel: selectedStandard.nominalValueLabel,
          classLabel: selectedStandard.classLabel,
          usageRangeLabel: selectedStandard.usageRangeLabel,
          uncertaintyLabel: selectedStandard.uncertaintyLabel,
          correctionFactorLabel: selectedStandard.correctionFactorLabel,
          history: buildStandardHistory(selectedStandard),
          recentWorkOrders: buildStandardRecentWorkOrders(linkedEquipment),
          blockers: details.blockers,
          warnings: details.warnings,
          links: {
            registryScenarioId: firstLinkedEquipment
              ? resolveRegistryScenarioId(resolveEquipmentStatus(firstLinkedEquipment, input.nowUtc).status)
              : undefined,
            selectedEquipmentId: firstLinkedEquipment?.equipmentId,
          },
        },
      },
    ],
  };
}

export function buildPersistedProcedureRegistryCatalog(
  input: BuildPersistedProcedureRegistryCatalogInput,
): ProcedureRegistryCatalog {
  const selectedProcedure =
    input.procedures.find((record) => record.procedureId === input.selectedProcedureId) ?? input.procedures[0];

  if (!selectedProcedure) {
    throw new Error("persisted_procedure_registry_empty");
  }

  const items = input.procedures.map((record) => buildProcedureListItem(record, input.nowUtc));
  const selectedItem =
    items.find((item) => item.procedureId === selectedProcedure.procedureId) ?? items[0];

  if (!selectedItem) {
    throw new Error("persisted_procedure_registry_missing_selected");
  }

  const details = resolveProcedureStatus(selectedProcedure, input.nowUtc);
  const status = details.status;
  const scenarioId = resolveProcedureScenarioId(status);

  return {
    selectedScenarioId: scenarioId,
    scenarios: [
      {
        id: scenarioId,
        label: buildProcedureLabel(status),
        description: `Carteira versionada persistida com ${input.procedures.length} revisao(oes) de procedimento disponiveis.`,
        summary: {
          status,
          headline: buildProcedureHeadline(status),
          activeCount: items.filter((item) => item.status === "ready").length,
          attentionCount: items.filter((item) => item.status === "attention").length,
          obsoleteCount: items.filter((item) => item.status === "blocked").length,
          recommendedAction: buildProcedureRecommendedAction(status, selectedProcedure.code),
          blockers: details.blockers,
          warnings: details.warnings,
        },
        selectedProcedureId: selectedProcedure.procedureId,
        items,
        detail: {
          procedureId: selectedProcedure.procedureId,
          title: `${selectedProcedure.code} rev.${selectedProcedure.revisionLabel} · ${selectedProcedure.title}`,
          status,
          noticeLabel: buildProcedureNoticeLabel(status, selectedProcedure.lifecycleLabel),
          scopeLabel: selectedProcedure.scopeLabel,
          environmentRangeLabel: selectedProcedure.environmentRangeLabel,
          curvePolicyLabel: selectedProcedure.curvePolicyLabel,
          standardsPolicyLabel: selectedProcedure.standardsPolicyLabel,
          approvalLabel: selectedProcedure.approvalLabel,
          relatedDocuments:
            selectedProcedure.relatedDocuments.length > 0
              ? selectedProcedure.relatedDocuments
              : ["Sem documento relacionado cadastrado."],
          blockers: details.blockers,
          warnings: details.warnings,
          links: {},
        },
      },
    ],
  };
}

function buildCustomerListItem(
  customer: PersistedCustomerRecord,
  equipment: PersistedEquipmentRecord[],
  nowUtc: string,
) {
  return {
    customerId: customer.customerId,
    legalName: customer.legalName,
    tradeName: customer.tradeName,
    documentLabel: customer.documentLabel,
    segmentLabel: customer.segmentLabel,
    equipmentCount: equipment.length,
    certificatesThisMonth: equipment.filter((record) => isSameMonth(record.lastCalibrationAtUtc, nowUtc))
      .length,
    nextDueLabel: findEarliestDueLabel(equipment, nowUtc),
    status: resolveCustomerStatus(customer, equipment, nowUtc),
  };
}

function buildEquipmentListItem(
  equipment: PersistedEquipmentRecord,
  customer: PersistedCustomerRecord | undefined,
  nowUtc: string,
) {
  const details = resolveEquipmentStatus(equipment, nowUtc);

  return {
    equipmentId: equipment.equipmentId,
    customerId: equipment.customerId,
    customerName: customer?.tradeName ?? "Cliente nao encontrado",
    code: equipment.code,
    tagCode: equipment.tagCode,
    serialNumber: equipment.serialNumber,
    typeModelLabel: equipment.typeModelLabel,
    capacityClassLabel: equipment.capacityClassLabel,
    lastCalibrationLabel: equipment.lastCalibrationAtUtc
      ? formatDateLabel(equipment.lastCalibrationAtUtc)
      : "Nao informada",
    nextCalibrationLabel: formatEquipmentNextCalibrationLabel(equipment, nowUtc),
    registrationStatusLabel: buildEquipmentRegistrationStatusLabel(equipment, nowUtc),
    status: details.status,
    missingFields: details.missingFields,
  };
}

function buildStandardListItem(record: PersistedStandardRecord, nowUtc: string) {
  const details = resolveStandardStatus(record, nowUtc);

  return {
    standardId: record.standardId,
    kindLabel: record.kindLabel,
    nominalClassLabel: record.nominalClassLabel,
    sourceLabel: record.sourceLabel,
    certificateLabel: record.certificateLabel,
    validUntilLabel: record.certificateValidUntilUtc
      ? formatDateLabel(record.certificateValidUntilUtc)
      : "Nao informada",
    status: details.status,
  };
}

function buildProcedureListItem(record: PersistedProcedureRecord, nowUtc: string) {
  const details = resolveProcedureStatus(record, nowUtc);

  return {
    procedureId: record.procedureId,
    code: record.code,
    title: record.title,
    typeLabel: record.typeLabel,
    revisionLabel: record.revisionLabel,
    effectiveSinceLabel: formatDateLabel(record.effectiveSinceUtc),
    effectiveUntilLabel: record.effectiveUntilUtc
      ? formatDateLabel(record.effectiveUntilUtc)
      : undefined,
    lifecycleLabel: record.lifecycleLabel,
    usageLabel: record.usageLabel,
    status: details.status,
  };
}

function resolveCustomerStatus(
  customer: PersistedCustomerRecord,
  equipment: PersistedEquipmentRecord[],
  nowUtc: string,
): RegistryOperationalStatus {
  if (customer.archivedAtUtc) {
    return "blocked";
  }

  if (equipment.some((record) => resolveEquipmentStatus(record, nowUtc).status === "blocked")) {
    return "blocked";
  }

  if (
    equipment.length === 0 ||
    equipment.some((record) => resolveEquipmentStatus(record, nowUtc).status === "attention")
  ) {
    return "attention";
  }

  return "ready";
}

function resolveEquipmentStatus(
  equipment: PersistedEquipmentRecord,
  nowUtc: string,
): EquipmentStatusDetails {
  const validation = validateEquipmentRegistration({
    customerId: equipment.customerId,
    address: {
      line1: equipment.addressLine1,
      city: equipment.addressCity,
      state: equipment.addressState,
      postalCode: equipment.addressPostalCode,
      country: equipment.addressCountry,
    },
  });
  const missingFields = uniqueStrings([
    ...validation.missingFields,
    ...(equipment.procedureId ? [] : ["procedureId"]),
    ...(equipment.primaryStandardId ? [] : ["primaryStandardId"]),
  ]);
  const blockers = uniqueStrings([
    ...(equipment.archivedAtUtc ? ["Equipamento arquivado e indisponivel para nova emissao."] : []),
    ...(missingFields.length > 0
      ? [`Campos ausentes: ${missingFields.join(", ")}.`]
      : []),
    ...(isExpired(equipment.nextCalibrationAtUtc, nowUtc)
      ? ["Calibracao do equipamento vencida no cadastro persistido."]
      : []),
  ]);
  const warnings = uniqueStrings([
    ...(isDueSoon(equipment.nextCalibrationAtUtc, nowUtc)
      ? ["Equipamento entra na janela critica de vencimento nos proximos 30 dias."]
      : []),
    ...(!equipment.lastCalibrationAtUtc
      ? ["Ultima calibracao ainda nao registrada no cadastro persistido."]
      : []),
  ]);

  if (blockers.length > 0) {
    return { status: "blocked", blockers, warnings, missingFields };
  }

  if (warnings.length > 0) {
    return { status: "attention", blockers, warnings, missingFields };
  }

  return { status: "ready", blockers, warnings, missingFields };
}

function resolveStandardStatus(
  standard: PersistedStandardRecord,
  nowUtc: string,
): StandardStatusDetails {
  const latestCalibration = standard.calibrations[0];
  const evaluation = evaluateStandardEligibility({
    calibrationDate: latestCalibration?.calibratedAtUtc ?? nowUtc,
    hasValidCertificate: standard.hasValidCertificate,
    certificateValidUntil: standard.certificateValidUntilUtc,
    measurementValue: standard.measurementValue,
    applicableRange: {
      minimum: standard.applicableRangeMin,
      maximum: standard.applicableRangeMax,
    },
  });
  const daysUntilExpiration = getDaysUntil(standard.certificateValidUntilUtc, nowUtc);
  const blockers = uniqueStrings([
    ...(standard.archivedAtUtc ? ["Padrao arquivado e indisponivel para reserva."] : []),
    ...evaluation.blockers.map(renderStandardBlocker),
  ]);
  const warnings = uniqueStrings([
    ...evaluation.warnings,
    ...(daysUntilExpiration !== null && daysUntilExpiration >= 0 && daysUntilExpiration <= 30
      ? [`Padrao vence em ${daysUntilExpiration} dia(s).`]
      : []),
  ]);

  if (blockers.length > 0) {
    return { status: "blocked", blockers, warnings, daysUntilExpiration };
  }

  if (warnings.length > 0) {
    return { status: "attention", blockers, warnings, daysUntilExpiration };
  }

  return { status: "ready", blockers, warnings, daysUntilExpiration };
}

function resolveProcedureStatus(
  procedure: PersistedProcedureRecord,
  nowUtc: string,
): ProcedureStatusDetails {
  const lifecycle = procedure.lifecycleLabel.toLowerCase();
  const effectiveUntilDays = getDaysUntil(procedure.effectiveUntilUtc, nowUtc);
  const blockers = uniqueStrings([
    ...(procedure.archivedAtUtc ? ["Procedimento arquivado e bloqueado para novas OS."] : []),
    ...(lifecycle.includes("obsole") ? ["Revisao obsoleta mantida apenas para rastreabilidade."] : []),
    ...(effectiveUntilDays !== null && effectiveUntilDays < 0
      ? ["Vigencia encerrada para novas OS."]
      : []),
  ]);
  const warnings = uniqueStrings([
    ...(lifecycle.includes("revis") ? ["Procedimento em revisao de qualidade."] : []),
    ...(effectiveUntilDays !== null && effectiveUntilDays >= 0 && effectiveUntilDays <= 30
      ? [`Vigencia encerra em ${effectiveUntilDays} dia(s).`]
      : []),
  ]);

  if (blockers.length > 0) {
    return { status: "blocked", blockers, warnings };
  }

  if (warnings.length > 0) {
    return { status: "attention", blockers, warnings };
  }

  return { status: "ready", blockers, warnings };
}

function buildEquipmentHighlight(
  equipment: PersistedEquipmentRecord,
  nowUtc: string,
) {
  return {
    equipmentId: equipment.equipmentId,
    code: equipment.code,
    tagCode: equipment.tagCode,
    typeModelLabel: equipment.typeModelLabel,
    nextDueLabel: formatEquipmentNextCalibrationLabel(equipment, nowUtc),
    status: resolveEquipmentStatus(equipment, nowUtc).status,
  };
}

function buildCustomerCertificateHighlights(
  equipment: PersistedEquipmentRecord[],
  nowUtc: string,
): CustomerCertificateHighlight[] {
  const highlights = equipment
    .slice()
    .sort((left, right) => {
      const leftDate = Date.parse(left.nextCalibrationAtUtc ?? left.updatedAtUtc);
      const rightDate = Date.parse(right.nextCalibrationAtUtc ?? right.updatedAtUtc);
      return leftDate - rightDate;
    })
    .slice(0, 3)
    .map((record) => ({
      certificateNumber: `Cadastro ${record.code}`,
      workOrderNumber: record.tagCode,
      issuedAtLabel: record.lastCalibrationAtUtc
        ? formatDateLabel(record.lastCalibrationAtUtc)
        : "Pendente",
      revisionLabel: record.procedureId ? "Com procedimento" : "Sem procedimento",
      statusLabel: buildStatusLabel(resolveEquipmentStatus(record, nowUtc).status),
    }));

  return highlights.length > 0
    ? highlights
    : [
        {
          certificateNumber: "Sem certificado emitido",
          workOrderNumber: "Cadastro inicial",
          issuedAtLabel: "Pendente",
          revisionLabel: "R0",
          statusLabel: "Aguardando vinculacao operacional",
        },
      ];
}

function buildCustomerAttachments(customer: PersistedCustomerRecord): CustomerAttachment[] {
  return [
    { label: "Contrato comercial", statusLabel: customer.contractLabel },
    { label: "Condicoes especiais", statusLabel: customer.specialConditionsLabel },
  ];
}

function buildCustomerHistory(
  auditEvents: PersistedRegistryAuditEventRecord[] | undefined,
  customer: PersistedCustomerRecord,
): CustomerHistoryItem[] {
  const items =
    auditEvents?.map((event) => ({
      label: event.summary,
      timestampLabel: formatDateTimeLabel(event.createdAtUtc),
    })) ?? [];

  if (items.length > 0) {
    return items.slice(0, 6);
  }

  return [
    {
      label: "Cliente cadastrado no tenant persistido.",
      timestampLabel: formatDateTimeLabel(customer.createdAtUtc),
    },
    {
      label: "Ultima atualizacao do cadastro registrada.",
      timestampLabel: formatDateTimeLabel(customer.updatedAtUtc),
    },
  ];
}

function buildStandardHistory(record: PersistedStandardRecord): StandardCalibrationHistoryEntry[] {
  const history = record.calibrations.map((entry) => ({
    calibratedAtLabel: formatDateLabel(entry.calibratedAtUtc),
    laboratoryLabel: entry.laboratoryLabel,
    certificateLabel: entry.certificateLabel,
    sourceLabel: entry.sourceLabel,
    uncertaintyLabel: entry.uncertaintyLabel,
    validUntilLabel: formatDateLabel(entry.validUntilUtc),
  }));

  return history.length > 0
    ? history
    : [
        {
          calibratedAtLabel: formatDateLabel(record.createdAtUtc),
          laboratoryLabel: record.sourceLabel,
          certificateLabel: record.certificateLabel,
          sourceLabel: record.sourceLabel,
          uncertaintyLabel: record.uncertaintyLabel,
          validUntilLabel: record.certificateValidUntilUtc
            ? formatDateLabel(record.certificateValidUntilUtc)
            : "Nao informada",
        },
      ];
}

function buildStandardRecentWorkOrders(
  relatedEquipment: PersistedEquipmentRecord[],
): StandardRecentWorkOrder[] {
  const items = relatedEquipment.slice(0, 3).map((record) => ({
    workOrderNumber: record.code,
    usedAtLabel: record.lastCalibrationAtUtc
      ? formatDateLabel(record.lastCalibrationAtUtc)
      : "Sem uso recente",
  }));

  return items.length > 0 ? items : [{ workOrderNumber: "Sem OS recente", usedAtLabel: "Sem uso" }];
}

function buildCustomerHeadline(status: RegistryOperationalStatus) {
  if (status === "blocked") {
    return "Cadastro bloqueado por dado minimo ausente ou equipamento vencido";
  }

  if (status === "attention") {
    return "Cadastro com cliente ou equipamento em janela de atencao";
  }

  return "Cadastros persistidos prontos para sustentar a emissao";
}

function buildEquipmentHeadline(status: RegistryOperationalStatus) {
  if (status === "blocked") {
    return "Equipamento bloqueado por cadastro incompleto ou validade vencida";
  }

  if (status === "attention") {
    return "Equipamento exige acao preventiva antes da proxima agenda";
  }

  return "Equipamentos persistidos e prontos para operacao controlada";
}

function buildStandardHeadline(status: RegistryOperationalStatus) {
  if (status === "blocked") {
    return "Padrao bloqueado por elegibilidade ou validade";
  }

  if (status === "attention") {
    return "Padrao entra em janela critica de vencimento";
  }

  return "Padroes validos e disponiveis para reserva";
}

function buildProcedureHeadline(status: RegistryOperationalStatus) {
  if (status === "blocked") {
    return "Revisao obsoleta ou encerrada visivel apenas para trilha historica";
  }

  if (status === "attention") {
    return "Procedimento vigente com revisao preventiva pendente";
  }

  return "Procedimentos vigentes e liberados para uso operacional";
}

function buildCustomerRecommendedAction(
  status: RegistryOperationalStatus,
  tradeName: string,
) {
  if (status === "blocked") {
    return `Completar o cadastro de ${tradeName} antes de liberar novas OS.`;
  }

  if (status === "attention") {
    return `Revisar a agenda operacional de ${tradeName} e antecipar os vencimentos proximos.`;
  }

  return `Manter a vigilancia de rotina do cadastro de ${tradeName}.`;
}

function buildEquipmentRecommendedAction(
  status: RegistryOperationalStatus,
  code: string,
) {
  if (status === "blocked") {
    return `Corrigir os bloqueios do equipamento ${code} antes da proxima emissao.`;
  }

  if (status === "attention") {
    return `Programar a acao preventiva do equipamento ${code} antes do vencimento.`;
  }

  return `Manter o equipamento ${code} sob monitoramento de rotina.`;
}

function buildStandardRecommendedAction(
  status: RegistryOperationalStatus,
  code: string,
) {
  if (status === "blocked") {
    return `Retirar o padrao ${code} da reserva e anexar nova calibracao antes de reutilizar.`;
  }

  if (status === "attention") {
    return `Solicitar a recalibracao do padrao ${code} antes da proxima janela operacional.`;
  }

  return `Manter o padrao ${code} no calendario preventivo normal.`;
}

function buildProcedureRecommendedAction(
  status: RegistryOperationalStatus,
  code: string,
) {
  if (status === "blocked") {
    return `Usar a revisao vigente correspondente e manter ${code} apenas para trilha historica.`;
  }

  if (status === "attention") {
    return `Concluir a revisao preventiva do procedimento ${code} antes da proxima rodada sensivel.`;
  }

  return `Seguir com o procedimento ${code} e manter apenas a vigilancia de rotina.`;
}

function buildCustomerStatusLine(
  status: RegistryOperationalStatus,
  accountOwnerName: string,
) {
  if (status === "blocked") {
    return `Cadastro bloqueado no tenant persistido · Responsavel: ${accountOwnerName}`;
  }

  if (status === "attention") {
    return `Cadastro em atencao operacional · Responsavel: ${accountOwnerName}`;
  }

  return `Cadastro pronto para sustentar a emissao · Responsavel: ${accountOwnerName}`;
}

function buildEquipmentStatusLine(
  status: RegistryOperationalStatus,
  customerLabel: string,
) {
  if (status === "blocked") {
    return `Equipamento bloqueado por cadastro ou validade · Cliente: ${customerLabel}`;
  }

  if (status === "attention") {
    return `Equipamento exige acao preventiva de vencimento · Cliente: ${customerLabel}`;
  }

  return `Equipamento apto para emissao controlada · Cliente: ${customerLabel}`;
}

function buildStandardNoticeLabel(
  status: RegistryOperationalStatus,
  daysUntilExpiration: number | null,
) {
  if (status === "blocked") {
    return "Este padrao esta vencido, arquivado ou inelegivel para uso.";
  }

  if (status === "attention" && daysUntilExpiration !== null) {
    return `Este padrao vence em ${daysUntilExpiration} dia(s).`;
  }

  return "Padrao valido e liberado para uso no recorte persistido.";
}

function buildProcedureNoticeLabel(
  status: RegistryOperationalStatus,
  lifecycleLabel: string,
) {
  if (status === "blocked") {
    return `${lifecycleLabel} e indisponivel para novas OS.`;
  }

  if (status === "attention") {
    return `${lifecycleLabel} com revisao preventiva pendente.`;
  }

  return `${lifecycleLabel} e liberado para uso no recorte atual.`;
}

function buildRegistryLabel(kind: string, status: RegistryOperationalStatus) {
  if (status === "blocked") {
    return `${capitalize(kind)} persistido bloqueado`;
  }

  if (status === "attention") {
    return `${capitalize(kind)} persistido em atencao`;
  }

  return `${capitalize(kind)} persistido operacional`;
}

function buildStandardLabel(status: RegistryOperationalStatus) {
  return status === "blocked"
    ? "Padrao persistido bloqueado"
    : status === "attention"
      ? "Padrao persistido em atencao"
      : "Padrao persistido operacional";
}

function buildProcedureLabel(status: RegistryOperationalStatus) {
  return status === "blocked"
    ? "Procedimento persistido obsoleto"
    : status === "attention"
      ? "Procedimento persistido em revisao"
      : "Procedimento persistido operacional";
}

function resolveRegistryScenarioId(status: RegistryOperationalStatus): RegistryScenarioId {
  if (status === "blocked") {
    return "registration-blocked";
  }

  if (status === "attention") {
    return "certificate-attention";
  }

  return "operational-ready";
}

function resolveStandardScenarioId(
  status: RegistryOperationalStatus,
): StandardRegistryScenarioId {
  if (status === "blocked") {
    return "expired-blocked";
  }

  if (status === "attention") {
    return "expiration-attention";
  }

  return "operational-ready";
}

function resolveProcedureScenarioId(
  status: RegistryOperationalStatus,
): ProcedureRegistryScenarioId {
  if (status === "blocked") {
    return "obsolete-visible";
  }

  if (status === "attention") {
    return "revision-attention";
  }

  return "operational-ready";
}

function buildEquipmentRegistrationStatusLabel(
  equipment: PersistedEquipmentRecord,
  nowUtc: string,
) {
  const details = resolveEquipmentStatus(equipment, nowUtc);
  if (details.missingFields.length > 0) {
    return `Cadastro incompleto: ${details.missingFields.join(", ")}.`;
  }

  if (details.status === "attention") {
    return "Cadastro minimo valido, mas com acao preventiva pendente.";
  }

  return "Cliente, endereco, procedimento e padrao minimo validados.";
}

function formatEquipmentNextCalibrationLabel(
  equipment: PersistedEquipmentRecord,
  nowUtc: string,
) {
  if (!equipment.nextCalibrationAtUtc) {
    return "Nao informada";
  }

  const label = formatDateLabel(equipment.nextCalibrationAtUtc);
  if (isExpired(equipment.nextCalibrationAtUtc, nowUtc)) {
    return `${label} vencida`;
  }

  if (isDueSoon(equipment.nextCalibrationAtUtc, nowUtc)) {
    return `${label} em atencao`;
  }

  return label;
}

function formatEquipmentAddress(equipment: PersistedEquipmentRecord) {
  return [
    equipment.addressLine1,
    `${equipment.addressCity}/${equipment.addressState}`,
    equipment.addressPostalCode ?? "CEP pendente",
  ].join(" · ");
}

function renderStandardBlocker(code: string) {
  switch (code) {
    case "missing_valid_certificate":
      return "Padrao sem certificado valido.";
    case "missing_certificate_validity":
      return "Validade do certificado ausente.";
    case "expired_certificate":
      return "Certificado do padrao vencido.";
    case "standard_out_of_applicable_range":
      return "Padrao fora da faixa aplicavel.";
    case "missing_applicable_range":
      return "Faixa aplicavel ausente.";
    case "missing_measurement_value":
      return "Valor de medicao ausente.";
    case "invalid_calibration_date":
      return "Data de calibracao invalida.";
    case "invalid_applicable_range":
      return "Faixa aplicavel invalida.";
    default:
      return code;
  }
}

function renderStandardPanelLabel(code: string) {
  return code.toUpperCase();
}

function renderDueInLabel(validUntilLabel: string, nowUtc: string) {
  const validUntil = parseDateFromDisplay(validUntilLabel);
  if (!validUntil) {
    return "validade desconhecida";
  }

  const daysUntilExpiration = Math.round(
    (validUntil.getTime() - startOfUtcDay(nowUtc).getTime()) / (24 * 60 * 60 * 1000),
  );
  if (daysUntilExpiration < 0) {
    return `${Math.abs(daysUntilExpiration)}d vencido`;
  }

  return `${daysUntilExpiration}d`;
}

function groupEquipmentByCustomer(equipment: PersistedEquipmentRecord[]) {
  const groups = new Map<string, PersistedEquipmentRecord[]>();

  for (const record of equipment) {
    const group = groups.get(record.customerId);
    if (group) {
      group.push(record);
    } else {
      groups.set(record.customerId, [record]);
    }
  }

  return groups;
}

function selectEquipment(
  highlights: Array<{ equipmentId: string }>,
  equipment: PersistedEquipmentRecord[],
  nowUtc: string,
) {
  return (
    equipment.find((record) => highlights.some((item) => item.equipmentId === record.equipmentId)) ??
    equipment.find((record) => resolveEquipmentStatus(record, nowUtc).status !== "ready") ??
    equipment[0]
  );
}

function findEarliestDueLabel(equipment: PersistedEquipmentRecord[], nowUtc: string) {
  const dated = equipment
    .filter((record) => typeof record.nextCalibrationAtUtc === "string")
    .slice()
    .sort((left, right) =>
      Date.parse(left.nextCalibrationAtUtc ?? left.updatedAtUtc) -
      Date.parse(right.nextCalibrationAtUtc ?? right.updatedAtUtc),
    );
  const first = dated[0];
  return first ? formatEquipmentNextCalibrationLabel(first, nowUtc) : "Sem agenda";
}

function buildStatusLabel(status: RegistryOperationalStatus) {
  if (status === "blocked") {
    return "Bloqueado";
  }

  if (status === "attention") {
    return "Em atencao";
  }

  return "Pronto";
}

function isDueSoon(dateUtc: string | undefined, nowUtc: string) {
  const daysUntil = getDaysUntil(dateUtc, nowUtc);
  return daysUntil !== null && daysUntil >= 0 && daysUntil <= 30;
}

function isExpired(dateUtc: string | undefined, nowUtc: string) {
  const daysUntil = getDaysUntil(dateUtc, nowUtc);
  return daysUntil !== null && daysUntil < 0;
}

function isSameMonth(dateUtc: string | undefined, nowUtc: string) {
  if (!dateUtc) {
    return false;
  }

  const date = new Date(dateUtc);
  const now = new Date(nowUtc);
  return (
    Number.isFinite(date.getTime()) &&
    date.getUTCFullYear() === now.getUTCFullYear() &&
    date.getUTCMonth() === now.getUTCMonth()
  );
}

function getDaysUntil(dateUtc: string | undefined, nowUtc: string) {
  if (!dateUtc) {
    return null;
  }

  const target = startOfUtcDay(dateUtc);
  const now = startOfUtcDay(nowUtc);
  if (!Number.isFinite(target.getTime()) || !Number.isFinite(now.getTime())) {
    return null;
  }

  return Math.round((target.getTime() - now.getTime()) / (24 * 60 * 60 * 1000));
}

function startOfUtcDay(value: string) {
  const day = TODAY_ONLY_FORMATTER.format(new Date(value));
  return new Date(`${day}T00:00:00.000Z`);
}

function formatDateLabel(value: string) {
  return DATE_FORMATTER.format(new Date(value));
}

function formatDateTimeLabel(value: string) {
  return DATE_TIME_FORMATTER.format(new Date(value)).replace(",", "");
}

function parseDateFromDisplay(value: string) {
  const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})/);
  if (!match) {
    return null;
  }

  const [, day, month, year] = match;
  return new Date(`${year}-${month}-${day}T00:00:00.000Z`);
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function uniqueStrings(values: string[]) {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)));
}
