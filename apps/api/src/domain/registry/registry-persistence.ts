import {
  equipmentMetrologyProfileSchema,
  standardMetrologyProfileSchema,
  type EquipmentMetrologyProfile,
  type StandardMetrologyProfile,
} from "@afere/contracts";
import { withTenant } from "@afere/db";
import { Prisma, type PrismaClient } from "@prisma/client";

export type RegistryEntityType = "customer" | "standard" | "procedure" | "equipment";

export type PersistedRegistryAuditEventRecord = {
  entityType: RegistryEntityType;
  entityId: string;
  action: string;
  summary: string;
  createdAtUtc: string;
  actorUserId?: string;
  actorType?: "human" | "agent" | "system";
};

export type PersistedCustomerRecord = {
  customerId: string;
  organizationId: string;
  legalName: string;
  tradeName: string;
  documentLabel: string;
  segmentLabel: string;
  accountOwnerName: string;
  accountOwnerEmail: string;
  contractLabel: string;
  specialConditionsLabel: string;
  contactName: string;
  contactRoleLabel: string;
  contactEmail: string;
  contactPhoneLabel?: string;
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode?: string;
  addressCountry: string;
  addressConditionsLabel?: string;
  createdAtUtc: string;
  updatedAtUtc: string;
  archivedAtUtc?: string;
};

export type PersistedStandardCalibrationRecord = {
  calibratedAtUtc: string;
  laboratoryLabel: string;
  certificateLabel: string;
  sourceLabel: string;
  uncertaintyLabel: string;
  validUntilUtc: string;
};

export type PersistedStandardRecord = {
  standardId: string;
  organizationId: string;
  code: string;
  title: string;
  kindLabel: string;
  nominalClassLabel: string;
  sourceLabel: string;
  certificateLabel: string;
  manufacturerLabel: string;
  modelLabel: string;
  serialNumberLabel: string;
  nominalValueLabel: string;
  classLabel: string;
  usageRangeLabel: string;
  measurementValue: number;
  applicableRangeMin: number;
  applicableRangeMax: number;
  uncertaintyLabel: string;
  correctionFactorLabel: string;
  metrologyProfile?: StandardMetrologyProfile;
  hasValidCertificate: boolean;
  certificateValidUntilUtc?: string;
  createdAtUtc: string;
  updatedAtUtc: string;
  archivedAtUtc?: string;
  calibrations: PersistedStandardCalibrationRecord[];
};

export type PersistedProcedureRecord = {
  procedureId: string;
  organizationId: string;
  code: string;
  title: string;
  typeLabel: string;
  revisionLabel: string;
  effectiveSinceUtc: string;
  effectiveUntilUtc?: string;
  lifecycleLabel: string;
  usageLabel: string;
  scopeLabel: string;
  environmentRangeLabel: string;
  curvePolicyLabel: string;
  standardsPolicyLabel: string;
  approvalLabel: string;
  relatedDocuments: string[];
  createdAtUtc: string;
  updatedAtUtc: string;
  archivedAtUtc?: string;
};

export type PersistedEquipmentRecord = {
  equipmentId: string;
  organizationId: string;
  customerId: string;
  procedureId?: string;
  primaryStandardId?: string;
  code: string;
  tagCode: string;
  serialNumber: string;
  typeModelLabel: string;
  capacityClassLabel: string;
  metrologyProfile?: EquipmentMetrologyProfile;
  supportingStandardCodes: string[];
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode?: string;
  addressCountry: string;
  addressConditionsLabel?: string;
  lastCalibrationAtUtc?: string;
  nextCalibrationAtUtc?: string;
  createdAtUtc: string;
  updatedAtUtc: string;
  archivedAtUtc?: string;
};

export type SaveCustomerInput = {
  organizationId: string;
  customerId?: string;
  actorUserId?: string;
  legalName: string;
  tradeName: string;
  documentLabel: string;
  segmentLabel: string;
  accountOwnerName: string;
  accountOwnerEmail: string;
  contractLabel: string;
  specialConditionsLabel: string;
  contactName: string;
  contactRoleLabel: string;
  contactEmail: string;
  contactPhoneLabel?: string;
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode?: string;
  addressCountry: string;
  addressConditionsLabel?: string;
};

export type SaveStandardInput = {
  organizationId: string;
  standardId?: string;
  actorUserId?: string;
  code: string;
  title: string;
  kindLabel: string;
  nominalClassLabel: string;
  sourceLabel: string;
  certificateLabel: string;
  manufacturerLabel: string;
  modelLabel: string;
  serialNumberLabel: string;
  nominalValueLabel: string;
  classLabel: string;
  usageRangeLabel: string;
  measurementValue: number;
  applicableRangeMin: number;
  applicableRangeMax: number;
  uncertaintyLabel: string;
  correctionFactorLabel: string;
  metrologyProfile?: StandardMetrologyProfile;
  hasValidCertificate: boolean;
  certificateValidUntilUtc?: string;
};

export type SaveProcedureInput = {
  organizationId: string;
  procedureId?: string;
  actorUserId?: string;
  code: string;
  title: string;
  typeLabel: string;
  revisionLabel: string;
  effectiveSinceUtc: string;
  effectiveUntilUtc?: string;
  lifecycleLabel: string;
  usageLabel: string;
  scopeLabel: string;
  environmentRangeLabel: string;
  curvePolicyLabel: string;
  standardsPolicyLabel: string;
  approvalLabel: string;
  relatedDocuments: string[];
};

export type SaveEquipmentInput = {
  organizationId: string;
  equipmentId?: string;
  actorUserId?: string;
  customerId: string;
  procedureId?: string;
  primaryStandardId?: string;
  code: string;
  tagCode: string;
  serialNumber: string;
  typeModelLabel: string;
  capacityClassLabel: string;
  metrologyProfile?: EquipmentMetrologyProfile;
  supportingStandardCodes: string[];
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode?: string;
  addressCountry: string;
  addressConditionsLabel?: string;
  lastCalibrationAtUtc?: string;
  nextCalibrationAtUtc?: string;
};

export interface RegistryPersistence {
  listCustomersByOrganization(organizationId: string): Promise<PersistedCustomerRecord[]>;
  saveCustomer(input: SaveCustomerInput): Promise<PersistedCustomerRecord>;
  setCustomerArchived(
    organizationId: string,
    customerId: string,
    archived: boolean,
    actorUserId?: string,
  ): Promise<void>;
  listCustomerAuditEvents(
    organizationId: string,
    customerId: string,
  ): Promise<PersistedRegistryAuditEventRecord[]>;
  listStandardsByOrganization(organizationId: string): Promise<PersistedStandardRecord[]>;
  saveStandard(input: SaveStandardInput): Promise<PersistedStandardRecord>;
  setStandardArchived(
    organizationId: string,
    standardId: string,
    archived: boolean,
    actorUserId?: string,
  ): Promise<void>;
  listProceduresByOrganization(organizationId: string): Promise<PersistedProcedureRecord[]>;
  saveProcedure(input: SaveProcedureInput): Promise<PersistedProcedureRecord>;
  setProcedureArchived(
    organizationId: string,
    procedureId: string,
    archived: boolean,
    actorUserId?: string,
  ): Promise<void>;
  listEquipmentByOrganization(organizationId: string): Promise<PersistedEquipmentRecord[]>;
  saveEquipment(input: SaveEquipmentInput): Promise<PersistedEquipmentRecord>;
  setEquipmentArchived(
    organizationId: string,
    equipmentId: string,
    archived: boolean,
    actorUserId?: string,
  ): Promise<void>;
}

export function createMemoryRegistryPersistence(seed: {
  customers?: PersistedCustomerRecord[];
  standards?: PersistedStandardRecord[];
  procedures?: PersistedProcedureRecord[];
  equipment?: PersistedEquipmentRecord[];
  auditEvents?: PersistedRegistryAuditEventRecord[];
} = {}): RegistryPersistence {
  const customers = new Map(
    (seed.customers ?? []).map((record) => [record.customerId, structuredClone(record)]),
  );
  const standards = new Map(
    (seed.standards ?? []).map((record) => [record.standardId, structuredClone(record)]),
  );
  const procedures = new Map(
    (seed.procedures ?? []).map((record) => [record.procedureId, structuredClone(record)]),
  );
  const equipment = new Map(
    (seed.equipment ?? []).map((record) => [record.equipmentId, structuredClone(record)]),
  );
  const auditEvents = (seed.auditEvents ?? []).map((record) => structuredClone(record));

  return {
    async listCustomersByOrganization(organizationId) {
      return sortByArchivedThenName(
        Array.from(customers.values()).filter((record) => record.organizationId === organizationId),
        (record) => record.tradeName,
      );
    },
    async saveCustomer(input) {
      const customerId = input.customerId ?? `memory-customer-${customers.size + 1}`;
      const nowUtc = new Date().toISOString();
      const existing = customers.get(customerId);
      const saved: PersistedCustomerRecord = {
        customerId,
        organizationId: input.organizationId,
        legalName: input.legalName,
        tradeName: input.tradeName,
        documentLabel: input.documentLabel,
        segmentLabel: input.segmentLabel,
        accountOwnerName: input.accountOwnerName,
        accountOwnerEmail: input.accountOwnerEmail.toLowerCase(),
        contractLabel: input.contractLabel,
        specialConditionsLabel: input.specialConditionsLabel,
        contactName: input.contactName,
        contactRoleLabel: input.contactRoleLabel,
        contactEmail: input.contactEmail.toLowerCase(),
        contactPhoneLabel: normalizeOptional(input.contactPhoneLabel),
        addressLine1: input.addressLine1,
        addressCity: input.addressCity,
        addressState: input.addressState,
        addressPostalCode: normalizeOptional(input.addressPostalCode),
        addressCountry: input.addressCountry,
        addressConditionsLabel: normalizeOptional(input.addressConditionsLabel),
        createdAtUtc: existing?.createdAtUtc ?? nowUtc,
        updatedAtUtc: nowUtc,
        archivedAtUtc: existing?.archivedAtUtc,
      };
      customers.set(customerId, saved);
      auditEvents.push({
        entityType: "customer",
        entityId: customerId,
        action: existing ? "update" : "create",
        summary: existing
          ? `Cadastro do cliente ${saved.tradeName} atualizado.`
          : `Cadastro do cliente ${saved.tradeName} criado.`,
        actorUserId: input.actorUserId,
        actorType: "human",
        createdAtUtc: nowUtc,
      });
      return structuredClone(saved);
    },
    async setCustomerArchived(organizationId, customerId, archived, actorUserId) {
      const existing = customers.get(customerId);
      if (!existing || existing.organizationId !== organizationId) {
        throw new Error("memory_customer_not_found");
      }

      const updated: PersistedCustomerRecord = {
        ...existing,
        archivedAtUtc: archived ? new Date().toISOString() : undefined,
        updatedAtUtc: new Date().toISOString(),
      };
      customers.set(customerId, updated);
      auditEvents.push({
        entityType: "customer",
        entityId: customerId,
        action: archived ? "archive" : "restore",
        summary: archived
          ? `Cliente ${existing.tradeName} arquivado.`
          : `Cliente ${existing.tradeName} reativado.`,
        actorUserId,
        actorType: "human",
        createdAtUtc: updated.updatedAtUtc,
      });
    },
    async listCustomerAuditEvents(organizationId, customerId) {
      return auditEvents
        .filter(
          (record) =>
            record.entityType === "customer" &&
            record.entityId === customerId &&
            customers.get(customerId)?.organizationId === organizationId,
        )
        .sort((left, right) => right.createdAtUtc.localeCompare(left.createdAtUtc))
        .map((record) => structuredClone(record));
    },
    async listStandardsByOrganization(organizationId) {
      return sortByArchivedThenName(
        Array.from(standards.values()).filter((record) => record.organizationId === organizationId),
        (record) => record.code,
      );
    },
    async saveStandard(input) {
      const standardId = input.standardId ?? `memory-standard-${standards.size + 1}`;
      const nowUtc = new Date().toISOString();
      const existing = standards.get(standardId);
      const calibrationEntry = buildCalibrationEntryFromSave(input, nowUtc);
      const saved: PersistedStandardRecord = {
        standardId,
        organizationId: input.organizationId,
        code: input.code,
        title: input.title,
        kindLabel: input.kindLabel,
        nominalClassLabel: input.nominalClassLabel,
        sourceLabel: input.sourceLabel,
        certificateLabel: input.certificateLabel,
        manufacturerLabel: input.manufacturerLabel,
        modelLabel: input.modelLabel,
        serialNumberLabel: input.serialNumberLabel,
        nominalValueLabel: input.nominalValueLabel,
        classLabel: input.classLabel,
        usageRangeLabel: input.usageRangeLabel,
        measurementValue: input.measurementValue,
        applicableRangeMin: input.applicableRangeMin,
        applicableRangeMax: input.applicableRangeMax,
        uncertaintyLabel: input.uncertaintyLabel,
        correctionFactorLabel: input.correctionFactorLabel,
        metrologyProfile: input.metrologyProfile ? structuredClone(input.metrologyProfile) : undefined,
        hasValidCertificate: input.hasValidCertificate,
        certificateValidUntilUtc: normalizeOptional(input.certificateValidUntilUtc),
        createdAtUtc: existing?.createdAtUtc ?? nowUtc,
        updatedAtUtc: nowUtc,
        archivedAtUtc: existing?.archivedAtUtc,
        calibrations: mergeCalibrationHistory(existing?.calibrations ?? [], calibrationEntry),
      };
      standards.set(standardId, saved);
      auditEvents.push({
        entityType: "standard",
        entityId: standardId,
        action: existing ? "update" : "create",
        summary: existing
          ? `Padrao ${saved.code} atualizado.`
          : `Padrao ${saved.code} cadastrado.`,
        actorUserId: input.actorUserId,
        actorType: "human",
        createdAtUtc: nowUtc,
      });
      return structuredClone(saved);
    },
    async setStandardArchived(organizationId, standardId, archived, actorUserId) {
      const existing = standards.get(standardId);
      if (!existing || existing.organizationId !== organizationId) {
        throw new Error("memory_standard_not_found");
      }

      const updated: PersistedStandardRecord = {
        ...existing,
        archivedAtUtc: archived ? new Date().toISOString() : undefined,
        updatedAtUtc: new Date().toISOString(),
      };
      standards.set(standardId, updated);
      auditEvents.push({
        entityType: "standard",
        entityId: standardId,
        action: archived ? "archive" : "restore",
        summary: archived
          ? `Padrao ${existing.code} arquivado.`
          : `Padrao ${existing.code} reativado.`,
        actorUserId,
        actorType: "human",
        createdAtUtc: updated.updatedAtUtc,
      });
    },
    async listProceduresByOrganization(organizationId) {
      return sortByArchivedThenName(
        Array.from(procedures.values()).filter((record) => record.organizationId === organizationId),
        (record) => `${record.code}-${record.revisionLabel}`,
      );
    },
    async saveProcedure(input) {
      const procedureId = input.procedureId ?? `memory-procedure-${procedures.size + 1}`;
      const nowUtc = new Date().toISOString();
      const existing = procedures.get(procedureId);
      const saved: PersistedProcedureRecord = {
        procedureId,
        organizationId: input.organizationId,
        code: input.code,
        title: input.title,
        typeLabel: input.typeLabel,
        revisionLabel: input.revisionLabel,
        effectiveSinceUtc: input.effectiveSinceUtc,
        effectiveUntilUtc: normalizeOptional(input.effectiveUntilUtc),
        lifecycleLabel: input.lifecycleLabel,
        usageLabel: input.usageLabel,
        scopeLabel: input.scopeLabel,
        environmentRangeLabel: input.environmentRangeLabel,
        curvePolicyLabel: input.curvePolicyLabel,
        standardsPolicyLabel: input.standardsPolicyLabel,
        approvalLabel: input.approvalLabel,
        relatedDocuments: input.relatedDocuments,
        createdAtUtc: existing?.createdAtUtc ?? nowUtc,
        updatedAtUtc: nowUtc,
        archivedAtUtc: existing?.archivedAtUtc,
      };
      procedures.set(procedureId, saved);
      auditEvents.push({
        entityType: "procedure",
        entityId: procedureId,
        action: existing ? "update" : "create",
        summary: existing
          ? `Procedimento ${saved.code} rev.${saved.revisionLabel} atualizado.`
          : `Procedimento ${saved.code} rev.${saved.revisionLabel} cadastrado.`,
        actorUserId: input.actorUserId,
        actorType: "human",
        createdAtUtc: nowUtc,
      });
      return structuredClone(saved);
    },
    async setProcedureArchived(organizationId, procedureId, archived, actorUserId) {
      const existing = procedures.get(procedureId);
      if (!existing || existing.organizationId !== organizationId) {
        throw new Error("memory_procedure_not_found");
      }

      const updated: PersistedProcedureRecord = {
        ...existing,
        archivedAtUtc: archived ? new Date().toISOString() : undefined,
        updatedAtUtc: new Date().toISOString(),
      };
      procedures.set(procedureId, updated);
      auditEvents.push({
        entityType: "procedure",
        entityId: procedureId,
        action: archived ? "archive" : "restore",
        summary: archived
          ? `Procedimento ${existing.code} rev.${existing.revisionLabel} arquivado.`
          : `Procedimento ${existing.code} rev.${existing.revisionLabel} reativado.`,
        actorUserId,
        actorType: "human",
        createdAtUtc: updated.updatedAtUtc,
      });
    },
    async listEquipmentByOrganization(organizationId) {
      return sortByArchivedThenName(
        Array.from(equipment.values()).filter((record) => record.organizationId === organizationId),
        (record) => record.code,
      );
    },
    async saveEquipment(input) {
      const equipmentId = input.equipmentId ?? `memory-equipment-${equipment.size + 1}`;
      const nowUtc = new Date().toISOString();
      const existing = equipment.get(equipmentId);
      const saved: PersistedEquipmentRecord = {
        equipmentId,
        organizationId: input.organizationId,
        customerId: input.customerId,
        procedureId: normalizeOptional(input.procedureId),
        primaryStandardId: normalizeOptional(input.primaryStandardId),
        code: input.code,
        tagCode: input.tagCode,
        serialNumber: input.serialNumber,
        typeModelLabel: input.typeModelLabel,
        capacityClassLabel: input.capacityClassLabel,
        metrologyProfile: input.metrologyProfile ? structuredClone(input.metrologyProfile) : undefined,
        supportingStandardCodes: input.supportingStandardCodes,
        addressLine1: input.addressLine1,
        addressCity: input.addressCity,
        addressState: input.addressState,
        addressPostalCode: normalizeOptional(input.addressPostalCode),
        addressCountry: input.addressCountry,
        addressConditionsLabel: normalizeOptional(input.addressConditionsLabel),
        lastCalibrationAtUtc: normalizeOptional(input.lastCalibrationAtUtc),
        nextCalibrationAtUtc: normalizeOptional(input.nextCalibrationAtUtc),
        createdAtUtc: existing?.createdAtUtc ?? nowUtc,
        updatedAtUtc: nowUtc,
        archivedAtUtc: existing?.archivedAtUtc,
      };
      equipment.set(equipmentId, saved);
      auditEvents.push({
        entityType: "equipment",
        entityId: equipmentId,
        action: existing ? "update" : "create",
        summary: existing
          ? `Equipamento ${saved.code} atualizado.`
          : `Equipamento ${saved.code} cadastrado.`,
        actorUserId: input.actorUserId,
        actorType: "human",
        createdAtUtc: nowUtc,
      });
      return structuredClone(saved);
    },
    async setEquipmentArchived(organizationId, equipmentId, archived, actorUserId) {
      const existing = equipment.get(equipmentId);
      if (!existing || existing.organizationId !== organizationId) {
        throw new Error("memory_equipment_not_found");
      }

      const updated: PersistedEquipmentRecord = {
        ...existing,
        archivedAtUtc: archived ? new Date().toISOString() : undefined,
        updatedAtUtc: new Date().toISOString(),
      };
      equipment.set(equipmentId, updated);
      auditEvents.push({
        entityType: "equipment",
        entityId: equipmentId,
        action: archived ? "archive" : "restore",
        summary: archived
          ? `Equipamento ${existing.code} arquivado.`
          : `Equipamento ${existing.code} reativado.`,
        actorUserId,
        actorType: "human",
        createdAtUtc: updated.updatedAtUtc,
      });
    },
  };
}

export function createPrismaRegistryPersistence(prisma: PrismaClient): RegistryPersistence {
  return {
    async listCustomersByOrganization(organizationId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const records = await tx.customer.findMany({
          where: { organizationId },
          orderBy: [{ archivedAt: "asc" }, { tradeName: "asc" }],
        });

        return records.map(mapCustomerRecord);
      });
    },
    async saveCustomer(input) {
      return withTenant(prisma, input.organizationId, async (tx) => {
        const saved = input.customerId
          ? await tx.customer.update({
              where: { id: input.customerId },
              data: mapCustomerSaveData(input),
            })
          : await tx.customer.create({
              data: {
                organizationId: input.organizationId,
                ...mapCustomerSaveData(input),
              },
            });

        await recordRegistryAuditEvent(tx, {
          organizationId: input.organizationId,
          entityType: "customer",
          entityId: saved.id,
          action: input.customerId ? "update" : "create",
          summary: input.customerId
            ? `Cadastro do cliente ${saved.tradeName} atualizado.`
            : `Cadastro do cliente ${saved.tradeName} criado.`,
          actorUserId: input.actorUserId,
          actorType: "human",
        });

        return mapCustomerRecord(saved);
      });
    },
    async setCustomerArchived(organizationId, customerId, archived, actorUserId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const updated = await tx.customer.update({
          where: { id: customerId },
          data: {
            archivedAt: archived ? new Date() : null,
          },
        });

        await recordRegistryAuditEvent(tx, {
          organizationId,
          entityType: "customer",
          entityId: customerId,
          action: archived ? "archive" : "restore",
          summary: archived
            ? `Cliente ${updated.tradeName} arquivado.`
            : `Cliente ${updated.tradeName} reativado.`,
          actorUserId,
          actorType: "human",
        });
      });
    },
    async listCustomerAuditEvents(organizationId, customerId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const records = await tx.registryAuditEvent.findMany({
          where: {
            organizationId,
            entityType: "customer",
            entityId: customerId,
          },
          orderBy: { createdAt: "desc" },
        });

        return records.map(mapAuditRecord);
      });
    },
    async listStandardsByOrganization(organizationId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const records = await tx.standard.findMany({
          where: { organizationId },
          include: {
            calibrations: {
              orderBy: { calibratedAt: "desc" },
            },
          },
          orderBy: [{ archivedAt: "asc" }, { code: "asc" }],
        });

        return records.map(mapStandardRecord);
      });
    },
    async saveStandard(input) {
      return withTenant(prisma, input.organizationId, async (tx) => {
        const now = new Date();
        const saved = input.standardId
          ? await tx.standard.update({
              where: { id: input.standardId },
              data: mapStandardSaveData(input),
            })
          : await tx.standard.create({
              data: {
                organizationId: input.organizationId,
                ...mapStandardSaveData(input),
              },
            });

        await ensureLatestStandardCalibration(tx, saved.id, input.organizationId, input, now);
        await recordRegistryAuditEvent(tx, {
          organizationId: input.organizationId,
          entityType: "standard",
          entityId: saved.id,
          action: input.standardId ? "update" : "create",
          summary: input.standardId ? `Padrao ${saved.code} atualizado.` : `Padrao ${saved.code} cadastrado.`,
          actorUserId: input.actorUserId,
          actorType: "human",
        });

        const reloaded = await tx.standard.findUniqueOrThrow({
          where: { id: saved.id },
          include: {
            calibrations: {
              orderBy: { calibratedAt: "desc" },
            },
          },
        });

        return mapStandardRecord(reloaded);
      });
    },
    async setStandardArchived(organizationId, standardId, archived, actorUserId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const updated = await tx.standard.update({
          where: { id: standardId },
          data: {
            archivedAt: archived ? new Date() : null,
          },
        });

        await recordRegistryAuditEvent(tx, {
          organizationId,
          entityType: "standard",
          entityId: standardId,
          action: archived ? "archive" : "restore",
          summary: archived ? `Padrao ${updated.code} arquivado.` : `Padrao ${updated.code} reativado.`,
          actorUserId,
          actorType: "human",
        });
      });
    },
    async listProceduresByOrganization(organizationId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const records = await tx.procedureRevision.findMany({
          where: { organizationId },
          orderBy: [{ archivedAt: "asc" }, { code: "asc" }, { revisionLabel: "desc" }],
        });

        return records.map(mapProcedureRecord);
      });
    },
    async saveProcedure(input) {
      return withTenant(prisma, input.organizationId, async (tx) => {
        const saved = input.procedureId
          ? await tx.procedureRevision.update({
              where: { id: input.procedureId },
              data: mapProcedureSaveData(input),
            })
          : await tx.procedureRevision.create({
              data: {
                organizationId: input.organizationId,
                ...mapProcedureSaveData(input),
              },
            });

        await recordRegistryAuditEvent(tx, {
          organizationId: input.organizationId,
          entityType: "procedure",
          entityId: saved.id,
          action: input.procedureId ? "update" : "create",
          summary: input.procedureId
            ? `Procedimento ${saved.code} rev.${saved.revisionLabel} atualizado.`
            : `Procedimento ${saved.code} rev.${saved.revisionLabel} cadastrado.`,
          actorUserId: input.actorUserId,
          actorType: "human",
        });

        return mapProcedureRecord(saved);
      });
    },
    async setProcedureArchived(organizationId, procedureId, archived, actorUserId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const updated = await tx.procedureRevision.update({
          where: { id: procedureId },
          data: {
            archivedAt: archived ? new Date() : null,
          },
        });

        await recordRegistryAuditEvent(tx, {
          organizationId,
          entityType: "procedure",
          entityId: procedureId,
          action: archived ? "archive" : "restore",
          summary: archived
            ? `Procedimento ${updated.code} rev.${updated.revisionLabel} arquivado.`
            : `Procedimento ${updated.code} rev.${updated.revisionLabel} reativado.`,
          actorUserId,
          actorType: "human",
        });
      });
    },
    async listEquipmentByOrganization(organizationId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const records = await tx.equipment.findMany({
          where: { organizationId },
          orderBy: [{ archivedAt: "asc" }, { code: "asc" }],
        });

        return records.map(mapEquipmentRecord);
      });
    },
    async saveEquipment(input) {
      return withTenant(prisma, input.organizationId, async (tx) => {
        const saved = input.equipmentId
          ? await tx.equipment.update({
              where: { id: input.equipmentId },
              data: mapEquipmentSaveData(input),
            })
          : await tx.equipment.create({
              data: {
                organizationId: input.organizationId,
                ...mapEquipmentSaveData(input),
              },
            });

        await recordRegistryAuditEvent(tx, {
          organizationId: input.organizationId,
          entityType: "equipment",
          entityId: saved.id,
          action: input.equipmentId ? "update" : "create",
          summary: input.equipmentId
            ? `Equipamento ${saved.code} atualizado.`
            : `Equipamento ${saved.code} cadastrado.`,
          actorUserId: input.actorUserId,
          actorType: "human",
        });

        return mapEquipmentRecord(saved);
      });
    },
    async setEquipmentArchived(organizationId, equipmentId, archived, actorUserId) {
      return withTenant(prisma, organizationId, async (tx) => {
        const updated = await tx.equipment.update({
          where: { id: equipmentId },
          data: {
            archivedAt: archived ? new Date() : null,
          },
        });

        await recordRegistryAuditEvent(tx, {
          organizationId,
          entityType: "equipment",
          entityId: equipmentId,
          action: archived ? "archive" : "restore",
          summary: archived
            ? `Equipamento ${updated.code} arquivado.`
            : `Equipamento ${updated.code} reativado.`,
          actorUserId,
          actorType: "human",
        });
      });
    },
  };
}

async function ensureLatestStandardCalibration(
  prisma: PrismaClient,
  standardId: string,
  organizationId: string,
  input: SaveStandardInput,
  now: Date,
) {
  const validUntil = normalizeDate(input.certificateValidUntilUtc);
  if (!validUntil) {
    return;
  }

  const latest = await prisma.standardCalibration.findFirst({
    where: {
      organizationId,
      standardId,
    },
    orderBy: { calibratedAt: "desc" },
  });

  if (
    latest &&
    latest.certificateLabel === input.certificateLabel &&
    latest.validUntil.toISOString() === validUntil.toISOString()
  ) {
    return;
  }

  await prisma.standardCalibration.create({
    data: {
      organizationId,
      standardId,
      calibratedAt: now,
      laboratoryLabel: input.sourceLabel,
      certificateLabel: input.certificateLabel,
      sourceLabel: input.sourceLabel,
      uncertaintyLabel: input.uncertaintyLabel,
      validUntil,
    },
  });
}

async function recordRegistryAuditEvent(
  prisma: PrismaClient,
  input: {
    organizationId: string;
    entityType: RegistryEntityType;
    entityId: string;
    action: string;
    summary: string;
    actorUserId?: string;
    actorType?: "human" | "agent" | "system";
  },
) {
  await prisma.registryAuditEvent.create({
    data: {
      organizationId: input.organizationId,
      entityType: input.entityType,
      entityId: input.entityId,
      action: input.action,
      actorUserId: input.actorUserId ?? null,
      actorType: input.actorType ?? null,
      summary: input.summary,
    },
  });
}

function mapCustomerSaveData(input: SaveCustomerInput) {
  return {
    legalName: input.legalName.trim(),
    tradeName: input.tradeName.trim(),
    documentLabel: input.documentLabel.trim(),
    segmentLabel: input.segmentLabel.trim(),
    accountOwnerName: input.accountOwnerName.trim(),
    accountOwnerEmail: input.accountOwnerEmail.trim().toLowerCase(),
    contractLabel: input.contractLabel.trim(),
    specialConditionsLabel: input.specialConditionsLabel.trim(),
    contactName: input.contactName.trim(),
    contactRoleLabel: input.contactRoleLabel.trim(),
    contactEmail: input.contactEmail.trim().toLowerCase(),
    contactPhoneLabel: normalizeNullableString(input.contactPhoneLabel),
    addressLine1: input.addressLine1.trim(),
    addressCity: input.addressCity.trim(),
    addressState: input.addressState.trim(),
    addressPostalCode: normalizeNullableString(input.addressPostalCode),
    addressCountry: input.addressCountry.trim(),
    addressConditionsLabel: normalizeNullableString(input.addressConditionsLabel),
  };
}

function mapStandardSaveData(input: SaveStandardInput) {
  return {
    code: input.code.trim(),
    title: input.title.trim(),
    kindLabel: input.kindLabel.trim(),
    nominalClassLabel: input.nominalClassLabel.trim(),
    sourceLabel: input.sourceLabel.trim(),
    certificateLabel: input.certificateLabel.trim(),
    manufacturerLabel: input.manufacturerLabel.trim(),
    modelLabel: input.modelLabel.trim(),
    serialNumberLabel: input.serialNumberLabel.trim(),
    nominalValueLabel: input.nominalValueLabel.trim(),
    classLabel: input.classLabel.trim(),
    usageRangeLabel: input.usageRangeLabel.trim(),
    measurementValue: input.measurementValue,
    applicableRangeMin: input.applicableRangeMin,
    applicableRangeMax: input.applicableRangeMax,
    uncertaintyLabel: input.uncertaintyLabel.trim(),
    correctionFactorLabel: input.correctionFactorLabel.trim(),
    metrologyProfile: input.metrologyProfile
      ? toPrismaJsonValue(input.metrologyProfile)
      : Prisma.JsonNull,
    hasValidCertificate: input.hasValidCertificate,
    certificateValidUntil: normalizeDate(input.certificateValidUntilUtc),
  };
}

function mapProcedureSaveData(input: SaveProcedureInput) {
  return {
    code: input.code.trim(),
    title: input.title.trim(),
    typeLabel: input.typeLabel.trim(),
    revisionLabel: input.revisionLabel.trim(),
    effectiveSince: normalizeDate(input.effectiveSinceUtc) ?? new Date(),
    effectiveUntil: normalizeDate(input.effectiveUntilUtc),
    lifecycleLabel: input.lifecycleLabel.trim(),
    usageLabel: input.usageLabel.trim(),
    scopeLabel: input.scopeLabel.trim(),
    environmentRangeLabel: input.environmentRangeLabel.trim(),
    curvePolicyLabel: input.curvePolicyLabel.trim(),
    standardsPolicyLabel: input.standardsPolicyLabel.trim(),
    approvalLabel: input.approvalLabel.trim(),
    relatedDocuments: input.relatedDocuments,
  };
}

function mapEquipmentSaveData(input: SaveEquipmentInput) {
  return {
    customerId: input.customerId,
    procedureId: normalizeNullableString(input.procedureId),
    primaryStandardId: normalizeNullableString(input.primaryStandardId),
    code: input.code.trim(),
    tagCode: input.tagCode.trim(),
    serialNumber: input.serialNumber.trim(),
    typeModelLabel: input.typeModelLabel.trim(),
    capacityClassLabel: input.capacityClassLabel.trim(),
    metrologyProfile: input.metrologyProfile
      ? toPrismaJsonValue(input.metrologyProfile)
      : Prisma.JsonNull,
    supportingStandardCodes: input.supportingStandardCodes,
    addressLine1: input.addressLine1.trim(),
    addressCity: input.addressCity.trim(),
    addressState: input.addressState.trim(),
    addressPostalCode: normalizeNullableString(input.addressPostalCode),
    addressCountry: input.addressCountry.trim(),
    addressConditionsLabel: normalizeNullableString(input.addressConditionsLabel),
    lastCalibrationAt: normalizeDate(input.lastCalibrationAtUtc),
    nextCalibrationAt: normalizeDate(input.nextCalibrationAtUtc),
  };
}

function mapCustomerRecord(record: {
  id: string;
  organizationId: string;
  legalName: string;
  tradeName: string;
  documentLabel: string;
  segmentLabel: string;
  accountOwnerName: string;
  accountOwnerEmail: string;
  contractLabel: string;
  specialConditionsLabel: string;
  contactName: string;
  contactRoleLabel: string;
  contactEmail: string;
  contactPhoneLabel: string | null;
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode: string | null;
  addressCountry: string;
  addressConditionsLabel: string | null;
  createdAt: Date;
  updatedAt: Date;
  archivedAt: Date | null;
}): PersistedCustomerRecord {
  return {
    customerId: record.id,
    organizationId: record.organizationId,
    legalName: record.legalName,
    tradeName: record.tradeName,
    documentLabel: record.documentLabel,
    segmentLabel: record.segmentLabel,
    accountOwnerName: record.accountOwnerName,
    accountOwnerEmail: record.accountOwnerEmail,
    contractLabel: record.contractLabel,
    specialConditionsLabel: record.specialConditionsLabel,
    contactName: record.contactName,
    contactRoleLabel: record.contactRoleLabel,
    contactEmail: record.contactEmail,
    contactPhoneLabel: record.contactPhoneLabel ?? undefined,
    addressLine1: record.addressLine1,
    addressCity: record.addressCity,
    addressState: record.addressState,
    addressPostalCode: record.addressPostalCode ?? undefined,
    addressCountry: record.addressCountry,
    addressConditionsLabel: record.addressConditionsLabel ?? undefined,
    createdAtUtc: record.createdAt.toISOString(),
    updatedAtUtc: record.updatedAt.toISOString(),
    archivedAtUtc: record.archivedAt?.toISOString(),
  };
}

function mapStandardRecord(record: {
  id: string;
  organizationId: string;
  code: string;
  title: string;
  kindLabel: string;
  nominalClassLabel: string;
  sourceLabel: string;
  certificateLabel: string;
  manufacturerLabel: string;
  modelLabel: string;
  serialNumberLabel: string;
  nominalValueLabel: string;
  classLabel: string;
  usageRangeLabel: string;
  measurementValue: { toNumber(): number } | number;
  applicableRangeMin: { toNumber(): number } | number;
  applicableRangeMax: { toNumber(): number } | number;
  uncertaintyLabel: string;
  correctionFactorLabel: string;
  metrologyProfile: Prisma.JsonValue | null;
  hasValidCertificate: boolean;
  certificateValidUntil: Date | null;
  createdAt: Date;
  updatedAt: Date;
  archivedAt: Date | null;
  calibrations: Array<{
    calibratedAt: Date;
    laboratoryLabel: string;
    certificateLabel: string;
    sourceLabel: string;
    uncertaintyLabel: string;
    validUntil: Date;
  }>;
}): PersistedStandardRecord {
  return {
    standardId: record.id,
    organizationId: record.organizationId,
    code: record.code,
    title: record.title,
    kindLabel: record.kindLabel,
    nominalClassLabel: record.nominalClassLabel,
    sourceLabel: record.sourceLabel,
    certificateLabel: record.certificateLabel,
    manufacturerLabel: record.manufacturerLabel,
    modelLabel: record.modelLabel,
    serialNumberLabel: record.serialNumberLabel,
    nominalValueLabel: record.nominalValueLabel,
    classLabel: record.classLabel,
    usageRangeLabel: record.usageRangeLabel,
    measurementValue: toNumber(record.measurementValue),
    applicableRangeMin: toNumber(record.applicableRangeMin),
    applicableRangeMax: toNumber(record.applicableRangeMax),
    uncertaintyLabel: record.uncertaintyLabel,
    correctionFactorLabel: record.correctionFactorLabel,
    metrologyProfile: parseStandardMetrologyProfile(record.metrologyProfile),
    hasValidCertificate: record.hasValidCertificate,
    certificateValidUntilUtc: record.certificateValidUntil?.toISOString(),
    createdAtUtc: record.createdAt.toISOString(),
    updatedAtUtc: record.updatedAt.toISOString(),
    archivedAtUtc: record.archivedAt?.toISOString(),
    calibrations: record.calibrations.map((calibration) => ({
      calibratedAtUtc: calibration.calibratedAt.toISOString(),
      laboratoryLabel: calibration.laboratoryLabel,
      certificateLabel: calibration.certificateLabel,
      sourceLabel: calibration.sourceLabel,
      uncertaintyLabel: calibration.uncertaintyLabel,
      validUntilUtc: calibration.validUntil.toISOString(),
    })),
  };
}

function mapProcedureRecord(record: {
  id: string;
  organizationId: string;
  code: string;
  title: string;
  typeLabel: string;
  revisionLabel: string;
  effectiveSince: Date;
  effectiveUntil: Date | null;
  lifecycleLabel: string;
  usageLabel: string;
  scopeLabel: string;
  environmentRangeLabel: string;
  curvePolicyLabel: string;
  standardsPolicyLabel: string;
  approvalLabel: string;
  relatedDocuments: string[];
  createdAt: Date;
  updatedAt: Date;
  archivedAt: Date | null;
}): PersistedProcedureRecord {
  return {
    procedureId: record.id,
    organizationId: record.organizationId,
    code: record.code,
    title: record.title,
    typeLabel: record.typeLabel,
    revisionLabel: record.revisionLabel,
    effectiveSinceUtc: record.effectiveSince.toISOString(),
    effectiveUntilUtc: record.effectiveUntil?.toISOString(),
    lifecycleLabel: record.lifecycleLabel,
    usageLabel: record.usageLabel,
    scopeLabel: record.scopeLabel,
    environmentRangeLabel: record.environmentRangeLabel,
    curvePolicyLabel: record.curvePolicyLabel,
    standardsPolicyLabel: record.standardsPolicyLabel,
    approvalLabel: record.approvalLabel,
    relatedDocuments: record.relatedDocuments,
    createdAtUtc: record.createdAt.toISOString(),
    updatedAtUtc: record.updatedAt.toISOString(),
    archivedAtUtc: record.archivedAt?.toISOString(),
  };
}

function mapEquipmentRecord(record: {
  id: string;
  organizationId: string;
  customerId: string;
  procedureId: string | null;
  primaryStandardId: string | null;
  code: string;
  tagCode: string;
  serialNumber: string;
  typeModelLabel: string;
  capacityClassLabel: string;
  metrologyProfile: Prisma.JsonValue | null;
  supportingStandardCodes: string[];
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode: string | null;
  addressCountry: string;
  addressConditionsLabel: string | null;
  lastCalibrationAt: Date | null;
  nextCalibrationAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
  archivedAt: Date | null;
}): PersistedEquipmentRecord {
  return {
    equipmentId: record.id,
    organizationId: record.organizationId,
    customerId: record.customerId,
    procedureId: record.procedureId ?? undefined,
    primaryStandardId: record.primaryStandardId ?? undefined,
    code: record.code,
    tagCode: record.tagCode,
    serialNumber: record.serialNumber,
    typeModelLabel: record.typeModelLabel,
    capacityClassLabel: record.capacityClassLabel,
    metrologyProfile: parseEquipmentMetrologyProfile(record.metrologyProfile),
    supportingStandardCodes: record.supportingStandardCodes,
    addressLine1: record.addressLine1,
    addressCity: record.addressCity,
    addressState: record.addressState,
    addressPostalCode: record.addressPostalCode ?? undefined,
    addressCountry: record.addressCountry,
    addressConditionsLabel: record.addressConditionsLabel ?? undefined,
    lastCalibrationAtUtc: record.lastCalibrationAt?.toISOString(),
    nextCalibrationAtUtc: record.nextCalibrationAt?.toISOString(),
    createdAtUtc: record.createdAt.toISOString(),
    updatedAtUtc: record.updatedAt.toISOString(),
    archivedAtUtc: record.archivedAt?.toISOString(),
  };
}

function mapAuditRecord(record: {
  entityType: string;
  entityId: string;
  action: string;
  summary: string;
  createdAt: Date;
  actorUserId: string | null;
  actorType: string | null;
}): PersistedRegistryAuditEventRecord {
  return {
    entityType: record.entityType as RegistryEntityType,
    entityId: record.entityId,
    action: record.action,
    summary: record.summary,
    createdAtUtc: record.createdAt.toISOString(),
    actorUserId: record.actorUserId ?? undefined,
    actorType: (record.actorType ?? undefined) as PersistedRegistryAuditEventRecord["actorType"],
  };
}

function buildCalibrationEntryFromSave(
  input: SaveStandardInput,
  nowUtc: string,
): PersistedStandardCalibrationRecord {
  return {
    calibratedAtUtc: nowUtc,
    laboratoryLabel: input.sourceLabel,
    certificateLabel: input.certificateLabel,
    sourceLabel: input.sourceLabel,
    uncertaintyLabel: input.uncertaintyLabel,
    validUntilUtc: normalizeOptional(input.certificateValidUntilUtc) ?? nowUtc,
  };
}

function mergeCalibrationHistory(
  existing: PersistedStandardCalibrationRecord[],
  latest: PersistedStandardCalibrationRecord,
) {
  const [first] = existing;
  if (
    first &&
    first.certificateLabel === latest.certificateLabel &&
    first.validUntilUtc === latest.validUntilUtc
  ) {
    return existing;
  }

  return [latest, ...existing].slice(0, 6);
}

function sortByArchivedThenName<T extends { archivedAtUtc?: string }>(
  values: T[],
  getLabel: (value: T) => string,
) {
  return values
    .map((value) => structuredClone(value))
    .sort((left, right) => {
      const archivedLeft = left.archivedAtUtc ? 1 : 0;
      const archivedRight = right.archivedAtUtc ? 1 : 0;
      if (archivedLeft !== archivedRight) {
        return archivedLeft - archivedRight;
      }

      return getLabel(left).localeCompare(getLabel(right));
    });
}

function toPrismaJsonValue(
  value: EquipmentMetrologyProfile | StandardMetrologyProfile,
): Prisma.InputJsonValue {
  return value as Prisma.InputJsonValue;
}

function parseStandardMetrologyProfile(value: Prisma.JsonValue | null | undefined) {
  if (!value) {
    return undefined;
  }

  const parsed = standardMetrologyProfileSchema.safeParse(value);
  return parsed.success ? parsed.data : undefined;
}

function parseEquipmentMetrologyProfile(value: Prisma.JsonValue | null | undefined) {
  if (!value) {
    return undefined;
  }

  const parsed = equipmentMetrologyProfileSchema.safeParse(value);
  return parsed.success ? parsed.data : undefined;
}

function normalizeDate(value?: string | null) {
  if (!value) {
    return null;
  }

  const normalized = value.includes("T") ? value : `${value}T00:00:00.000Z`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function normalizeOptional<T extends string | null | undefined>(value: T) {
  if (typeof value !== "string") {
    return undefined;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function normalizeNullableString(value?: string | null) {
  return normalizeOptional(value) ?? null;
}

function toNumber(value: number | { toNumber(): number }) {
  return typeof value === "number" ? value : value.toNumber();
}
