import type { PrismaClient } from "@prisma/client";

export type PersistedNonconformityRecord = {
  ncId: string;
  organizationId: string;
  serviceOrderId?: string;
  workOrderNumber?: string;
  certificateNumber?: string;
  ownerUserId?: string;
  ownerLabel: string;
  title: string;
  originLabel: string;
  severityLabel: string;
  status: "ready" | "attention" | "blocked";
  noticeLabel: string;
  rootCauseLabel: string;
  containmentLabel: string;
  correctiveActionLabel: string;
  evidenceLabel: string;
  blockers: string[];
  warnings: string[];
  openedAtUtc: string;
  dueAtUtc: string;
  resolvedAtUtc?: string;
};

export type PersistedNonconformingWorkRecord = {
  caseId: string;
  organizationId: string;
  serviceOrderId?: string;
  workOrderNumber?: string;
  nonconformityId?: string;
  title: string;
  classificationLabel: string;
  originLabel: string;
  affectedEntityLabel: string;
  status: "ready" | "attention" | "blocked";
  noticeLabel: string;
  containmentLabel: string;
  releaseRuleLabel: string;
  evidenceLabel: string;
  restorationLabel: string;
  blockers: string[];
  warnings: string[];
  createdAtUtc: string;
  updatedAtUtc: string;
};

export type PersistedInternalAuditChecklistItem = {
  key: string;
  requirementLabel: string;
  evidenceLabel: string;
  status: "ready" | "attention" | "blocked";
};

export type PersistedInternalAuditCycleRecord = {
  cycleId: string;
  organizationId: string;
  cycleLabel: string;
  windowLabel: string;
  scopeLabel: string;
  auditorLabel: string;
  auditeeLabel: string;
  periodLabel: string;
  reportLabel: string;
  evidenceLabel: string;
  nextReviewLabel: string;
  noticeLabel: string;
  status: "ready" | "attention" | "blocked";
  checklist: PersistedInternalAuditChecklistItem[];
  findingRefs: string[];
  blockers: string[];
  warnings: string[];
  scheduledAtUtc: string;
  completedAtUtc?: string;
};

export type PersistedManagementReviewAgendaItem = {
  key: string;
  label: string;
  status: "ready" | "attention" | "blocked";
};

export type PersistedManagementReviewDecisionItem = {
  key: string;
  label: string;
  ownerLabel: string;
  dueDateLabel: string;
  status: "ready" | "attention" | "blocked";
};

export type PersistedManagementReviewMeetingRecord = {
  meetingId: string;
  organizationId: string;
  titleLabel: string;
  status: "ready" | "attention" | "blocked";
  dateLabel: string;
  outcomeLabel: string;
  noticeLabel: string;
  nextMeetingLabel: string;
  chairLabel: string;
  attendeesLabel: string;
  periodLabel: string;
  ataLabel: string;
  evidenceLabel: string;
  agendaItems: PersistedManagementReviewAgendaItem[];
  decisions: PersistedManagementReviewDecisionItem[];
  blockers: string[];
  warnings: string[];
  scheduledForUtc: string;
  heldAtUtc?: string;
};

export type PersistedComplianceProfileRecord = {
  complianceProfileId: string;
  organizationId: string;
  organizationName: string;
  organizationSlug: string;
  regulatoryProfile: string;
  normativePackageVersion: string;
  organizationCode: string;
  planLabel: string;
  certificatePrefix: string;
  accreditationNumber?: string;
  accreditationValidUntilUtc?: string;
  scopeSummary: string;
  cmcSummary: string;
  scopeItemCount: number;
  cmcItemCount: number;
  legalOpinionStatus: string;
  legalOpinionReference: string;
  dpaReference: string;
  normativeGovernanceStatus: string;
  normativeGovernanceOwner: string;
  normativeGovernanceReference: string;
  releaseNormVersion: string;
  releaseNormStatus: string;
  lastReviewedAtUtc: string;
};

export type PersistedQualityIndicatorSnapshotRecord = {
  snapshotId: string;
  organizationId: string;
  indicatorId: string;
  monthStartUtc: string;
  valueNumeric: number;
  targetNumeric?: number;
  status: "ready" | "attention" | "blocked";
  sourceLabel: string;
  evidenceLabel: string;
  createdAtUtc: string;
  updatedAtUtc: string;
};

export type SaveNonconformityInput = {
  organizationId: string;
  ncId?: string;
  serviceOrderId?: string;
  ownerUserId?: string;
  title: string;
  originLabel: string;
  severityLabel: string;
  status: "ready" | "attention" | "blocked";
  noticeLabel: string;
  rootCauseLabel: string;
  containmentLabel: string;
  correctiveActionLabel: string;
  evidenceLabel: string;
  blockers: string[];
  warnings: string[];
  openedAt: Date;
  dueAt: Date;
  resolvedAt?: Date;
};

export type SaveNonconformingWorkInput = {
  organizationId: string;
  caseId?: string;
  serviceOrderId?: string;
  nonconformityId?: string;
  title: string;
  classificationLabel: string;
  originLabel: string;
  affectedEntityLabel: string;
  status: "ready" | "attention" | "blocked";
  noticeLabel: string;
  containmentLabel: string;
  releaseRuleLabel: string;
  evidenceLabel: string;
  restorationLabel: string;
  blockers: string[];
  warnings: string[];
};

export type SaveInternalAuditCycleInput = {
  organizationId: string;
  cycleId?: string;
  cycleLabel: string;
  windowLabel: string;
  scopeLabel: string;
  auditorLabel: string;
  auditeeLabel: string;
  periodLabel: string;
  reportLabel: string;
  evidenceLabel: string;
  nextReviewLabel: string;
  noticeLabel: string;
  status: "ready" | "attention" | "blocked";
  checklist: PersistedInternalAuditChecklistItem[];
  findingRefs: string[];
  blockers: string[];
  warnings: string[];
  scheduledAt: Date;
  completedAt?: Date;
};

export type SaveManagementReviewMeetingInput = {
  organizationId: string;
  meetingId?: string;
  titleLabel: string;
  status: "ready" | "attention" | "blocked";
  dateLabel: string;
  outcomeLabel: string;
  noticeLabel: string;
  nextMeetingLabel: string;
  chairLabel: string;
  attendeesLabel: string;
  periodLabel: string;
  ataLabel: string;
  evidenceLabel: string;
  agendaItems: PersistedManagementReviewAgendaItem[];
  decisions: PersistedManagementReviewDecisionItem[];
  blockers: string[];
  warnings: string[];
  scheduledFor: Date;
  heldAt?: Date;
};

export type SaveComplianceProfileInput = {
  organizationId: string;
  organizationCode: string;
  planLabel: string;
  certificatePrefix: string;
  accreditationNumber?: string;
  accreditationValidUntil?: Date;
  scopeSummary: string;
  cmcSummary: string;
  scopeItemCount: number;
  cmcItemCount: number;
  legalOpinionStatus: string;
  legalOpinionReference: string;
  dpaReference: string;
  normativeGovernanceStatus: string;
  normativeGovernanceOwner: string;
  normativeGovernanceReference: string;
  releaseNormVersion: string;
  releaseNormStatus: string;
  lastReviewedAt: Date;
  regulatoryProfile?: string;
};

export type SaveQualityIndicatorSnapshotInput = {
  organizationId: string;
  snapshotId?: string;
  indicatorId: string;
  monthStart: Date;
  valueNumeric: number;
  targetNumeric?: number;
  status: "ready" | "attention" | "blocked";
  sourceLabel: string;
  evidenceLabel: string;
};

export interface QualityPersistence {
  listNonconformitiesByOrganization(organizationId: string): Promise<PersistedNonconformityRecord[]>;
  saveNonconformity(input: SaveNonconformityInput): Promise<PersistedNonconformityRecord>;
  listNonconformingWorkByOrganization(organizationId: string): Promise<PersistedNonconformingWorkRecord[]>;
  saveNonconformingWork(input: SaveNonconformingWorkInput): Promise<PersistedNonconformingWorkRecord>;
  listInternalAuditCyclesByOrganization(organizationId: string): Promise<PersistedInternalAuditCycleRecord[]>;
  saveInternalAuditCycle(input: SaveInternalAuditCycleInput): Promise<PersistedInternalAuditCycleRecord>;
  listManagementReviewMeetingsByOrganization(
    organizationId: string,
  ): Promise<PersistedManagementReviewMeetingRecord[]>;
  saveManagementReviewMeeting(
    input: SaveManagementReviewMeetingInput,
  ): Promise<PersistedManagementReviewMeetingRecord>;
  getComplianceProfileByOrganization(
    organizationId: string,
  ): Promise<PersistedComplianceProfileRecord | null>;
  saveComplianceProfile(input: SaveComplianceProfileInput): Promise<PersistedComplianceProfileRecord>;
  listQualityIndicatorSnapshotsByOrganization(
    organizationId: string,
  ): Promise<PersistedQualityIndicatorSnapshotRecord[]>;
  saveQualityIndicatorSnapshot(
    input: SaveQualityIndicatorSnapshotInput,
  ): Promise<PersistedQualityIndicatorSnapshotRecord>;
}

export function createMemoryQualityPersistence(seed: {
  nonconformities?: PersistedNonconformityRecord[];
  nonconformingWork?: PersistedNonconformingWorkRecord[];
  internalAuditCycles?: PersistedInternalAuditCycleRecord[];
  managementReviewMeetings?: PersistedManagementReviewMeetingRecord[];
  complianceProfiles?: PersistedComplianceProfileRecord[];
  qualityIndicatorSnapshots?: PersistedQualityIndicatorSnapshotRecord[];
} = {}): QualityPersistence {
  const nonconformities = new Map(
    (seed.nonconformities ?? []).map((record) => [record.ncId, structuredClone(record)]),
  );
  const nonconformingWork = new Map(
    (seed.nonconformingWork ?? []).map((record) => [record.caseId, structuredClone(record)]),
  );
  const internalAuditCycles = new Map(
    (seed.internalAuditCycles ?? []).map((record) => [record.cycleId, structuredClone(record)]),
  );
  const managementReviewMeetings = new Map(
    (seed.managementReviewMeetings ?? []).map((record) => [record.meetingId, structuredClone(record)]),
  );
  const complianceProfiles = new Map(
    (seed.complianceProfiles ?? []).map((record) => [record.organizationId, structuredClone(record)]),
  );
  const qualityIndicatorSnapshots = new Map(
    (seed.qualityIndicatorSnapshots ?? []).map((record) => [record.snapshotId, structuredClone(record)]),
  );

  return {
    async listNonconformitiesByOrganization(organizationId) {
      return Array.from(nonconformities.values())
        .filter((record) => record.organizationId === organizationId)
        .map((record) => structuredClone(record))
        .sort(compareNonconformities);
    },
    async saveNonconformity(input) {
      const ncId = input.ncId ?? `memory-nc-${nonconformities.size + 1}`;
      const existing = input.ncId ? nonconformities.get(input.ncId) : undefined;
      const record: PersistedNonconformityRecord = {
        ncId,
        organizationId: input.organizationId,
        serviceOrderId: input.serviceOrderId,
        workOrderNumber: existing?.workOrderNumber,
        certificateNumber: existing?.certificateNumber,
        ownerUserId: input.ownerUserId,
        ownerLabel: existing?.ownerLabel ?? "Responsavel da Qualidade",
        title: input.title.trim(),
        originLabel: input.originLabel.trim(),
        severityLabel: input.severityLabel.trim(),
        status: input.status,
        noticeLabel: input.noticeLabel.trim(),
        rootCauseLabel: input.rootCauseLabel.trim(),
        containmentLabel: input.containmentLabel.trim(),
        correctiveActionLabel: input.correctiveActionLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
        openedAtUtc: input.openedAt.toISOString(),
        dueAtUtc: input.dueAt.toISOString(),
        resolvedAtUtc: input.resolvedAt?.toISOString(),
      };

      nonconformities.set(ncId, record);
      return structuredClone(record);
    },
    async listNonconformingWorkByOrganization(organizationId) {
      return Array.from(nonconformingWork.values())
        .filter((record) => record.organizationId === organizationId)
        .map((record) => structuredClone(record))
        .sort((left, right) => right.updatedAtUtc.localeCompare(left.updatedAtUtc));
    },
    async saveNonconformingWork(input) {
      const caseId = input.caseId ?? `memory-ncw-${nonconformingWork.size + 1}`;
      const existing = input.caseId ? nonconformingWork.get(input.caseId) : undefined;
      const nowUtc = new Date().toISOString();
      const record: PersistedNonconformingWorkRecord = {
        caseId,
        organizationId: input.organizationId,
        serviceOrderId: input.serviceOrderId,
        workOrderNumber: existing?.workOrderNumber,
        nonconformityId: input.nonconformityId,
        title: input.title.trim(),
        classificationLabel: input.classificationLabel.trim(),
        originLabel: input.originLabel.trim(),
        affectedEntityLabel: input.affectedEntityLabel.trim(),
        status: input.status,
        noticeLabel: input.noticeLabel.trim(),
        containmentLabel: input.containmentLabel.trim(),
        releaseRuleLabel: input.releaseRuleLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        restorationLabel: input.restorationLabel.trim(),
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
        createdAtUtc: existing?.createdAtUtc ?? nowUtc,
        updatedAtUtc: nowUtc,
      };

      nonconformingWork.set(caseId, record);
      return structuredClone(record);
    },
    async listInternalAuditCyclesByOrganization(organizationId) {
      return Array.from(internalAuditCycles.values())
        .filter((record) => record.organizationId === organizationId)
        .map((record) => structuredClone(record))
        .sort((left, right) => right.scheduledAtUtc.localeCompare(left.scheduledAtUtc));
    },
    async saveInternalAuditCycle(input) {
      const cycleId = input.cycleId ?? `memory-audit-${internalAuditCycles.size + 1}`;
      const record: PersistedInternalAuditCycleRecord = {
        cycleId,
        organizationId: input.organizationId,
        cycleLabel: input.cycleLabel.trim(),
        windowLabel: input.windowLabel.trim(),
        scopeLabel: input.scopeLabel.trim(),
        auditorLabel: input.auditorLabel.trim(),
        auditeeLabel: input.auditeeLabel.trim(),
        periodLabel: input.periodLabel.trim(),
        reportLabel: input.reportLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        nextReviewLabel: input.nextReviewLabel.trim(),
        noticeLabel: input.noticeLabel.trim(),
        status: input.status,
        checklist: sanitizeChecklist(input.checklist),
        findingRefs: sanitizeStringArray(input.findingRefs),
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
        scheduledAtUtc: input.scheduledAt.toISOString(),
        completedAtUtc: input.completedAt?.toISOString(),
      };

      internalAuditCycles.set(cycleId, record);
      return structuredClone(record);
    },
    async listManagementReviewMeetingsByOrganization(organizationId) {
      return Array.from(managementReviewMeetings.values())
        .filter((record) => record.organizationId === organizationId)
        .map((record) => structuredClone(record))
        .sort((left, right) => right.scheduledForUtc.localeCompare(left.scheduledForUtc));
    },
    async saveManagementReviewMeeting(input) {
      const meetingId = input.meetingId ?? `memory-review-${managementReviewMeetings.size + 1}`;
      const record: PersistedManagementReviewMeetingRecord = {
        meetingId,
        organizationId: input.organizationId,
        titleLabel: input.titleLabel.trim(),
        status: input.status,
        dateLabel: input.dateLabel.trim(),
        outcomeLabel: input.outcomeLabel.trim(),
        noticeLabel: input.noticeLabel.trim(),
        nextMeetingLabel: input.nextMeetingLabel.trim(),
        chairLabel: input.chairLabel.trim(),
        attendeesLabel: input.attendeesLabel.trim(),
        periodLabel: input.periodLabel.trim(),
        ataLabel: input.ataLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        agendaItems: sanitizeAgendaItems(input.agendaItems),
        decisions: sanitizeDecisionItems(input.decisions),
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
        scheduledForUtc: input.scheduledFor.toISOString(),
        heldAtUtc: input.heldAt?.toISOString(),
      };

      managementReviewMeetings.set(meetingId, record);
      return structuredClone(record);
    },
    async getComplianceProfileByOrganization(organizationId) {
      return structuredClone(complianceProfiles.get(organizationId) ?? null);
    },
    async saveComplianceProfile(input) {
      const existing = complianceProfiles.get(input.organizationId);
      const record: PersistedComplianceProfileRecord = {
        complianceProfileId: existing?.complianceProfileId ?? `memory-profile-${complianceProfiles.size + 1}`,
        organizationId: input.organizationId,
        organizationName: existing?.organizationName ?? "Laboratorio Persistido",
        organizationSlug: existing?.organizationSlug ?? "lab-persistido",
        regulatoryProfile: input.regulatoryProfile ?? existing?.regulatoryProfile ?? "type_b",
        normativePackageVersion: existing?.normativePackageVersion ?? "2026-04-20-baseline-v0.1.0",
        organizationCode: input.organizationCode.trim(),
        planLabel: input.planLabel.trim(),
        certificatePrefix: input.certificatePrefix.trim(),
        accreditationNumber: trimOptional(input.accreditationNumber),
        accreditationValidUntilUtc: input.accreditationValidUntil?.toISOString(),
        scopeSummary: input.scopeSummary.trim(),
        cmcSummary: input.cmcSummary.trim(),
        scopeItemCount: Math.max(0, input.scopeItemCount),
        cmcItemCount: Math.max(0, input.cmcItemCount),
        legalOpinionStatus: input.legalOpinionStatus.trim(),
        legalOpinionReference: input.legalOpinionReference.trim(),
        dpaReference: input.dpaReference.trim(),
        normativeGovernanceStatus: input.normativeGovernanceStatus.trim(),
        normativeGovernanceOwner: input.normativeGovernanceOwner.trim(),
        normativeGovernanceReference: input.normativeGovernanceReference.trim(),
        releaseNormVersion: input.releaseNormVersion.trim(),
        releaseNormStatus: input.releaseNormStatus.trim(),
        lastReviewedAtUtc: input.lastReviewedAt.toISOString(),
      };

      complianceProfiles.set(input.organizationId, record);
      return structuredClone(record);
    },
    async listQualityIndicatorSnapshotsByOrganization(organizationId) {
      return Array.from(qualityIndicatorSnapshots.values())
        .filter((record) => record.organizationId === organizationId)
        .map((record) => structuredClone(record))
        .sort((left, right) => {
          if (left.indicatorId !== right.indicatorId) {
            return left.indicatorId.localeCompare(right.indicatorId);
          }
          return left.monthStartUtc.localeCompare(right.monthStartUtc);
        });
    },
    async saveQualityIndicatorSnapshot(input) {
      const snapshotId = input.snapshotId ?? `memory-indicator-snapshot-${qualityIndicatorSnapshots.size + 1}`;
      const record: PersistedQualityIndicatorSnapshotRecord = {
        snapshotId,
        organizationId: input.organizationId,
        indicatorId: input.indicatorId.trim(),
        monthStartUtc: input.monthStart.toISOString(),
        valueNumeric: input.valueNumeric,
        targetNumeric: input.targetNumeric,
        status: input.status,
        sourceLabel: input.sourceLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        createdAtUtc: qualityIndicatorSnapshots.get(snapshotId)?.createdAtUtc ?? new Date().toISOString(),
        updatedAtUtc: new Date().toISOString(),
      };

      qualityIndicatorSnapshots.set(snapshotId, record);
      return structuredClone(record);
    },
  };
}

export function createPrismaQualityPersistence(prisma: PrismaClient): QualityPersistence {
  return {
    async listNonconformitiesByOrganization(organizationId) {
      const records = await prisma.nonconformity.findMany({
        where: { organizationId },
        include: {
          ownerUser: true,
          serviceOrder: {
            select: {
              workOrderNumber: true,
              certificateNumber: true,
            },
          },
        },
        orderBy: [{ dueAt: "asc" }, { openedAt: "desc" }],
      });

      return records.map((record) => mapNonconformityRecord(record));
    },
    async saveNonconformity(input) {
      await assertTenantReferences(prisma, input.organizationId, {
        serviceOrderId: input.serviceOrderId,
        ownerUserId: input.ownerUserId,
      });
      if (input.ncId) {
        await assertRecordOwnership(prisma.nonconformity, input.ncId, input.organizationId);
      }

      const data = {
        serviceOrderId: input.serviceOrderId,
        ownerUserId: input.ownerUserId,
        title: input.title.trim(),
        originLabel: input.originLabel.trim(),
        severityLabel: input.severityLabel.trim(),
        status: input.status,
        noticeLabel: input.noticeLabel.trim(),
        rootCauseLabel: input.rootCauseLabel.trim(),
        containmentLabel: input.containmentLabel.trim(),
        correctiveActionLabel: input.correctiveActionLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
        openedAt: input.openedAt,
        dueAt: input.dueAt,
        resolvedAt: input.resolvedAt ?? null,
      };

      const record = input.ncId
        ? await prisma.nonconformity.update({
            where: { id: input.ncId },
            data,
            include: {
              ownerUser: true,
              serviceOrder: {
                select: {
                  workOrderNumber: true,
                  certificateNumber: true,
                },
              },
            },
          })
        : await prisma.nonconformity.create({
            data: {
              id: crypto.randomUUID(),
              organizationId: input.organizationId,
              ...data,
            },
            include: {
              ownerUser: true,
              serviceOrder: {
                select: {
                  workOrderNumber: true,
                  certificateNumber: true,
                },
              },
            },
          });

      if (record.organizationId !== input.organizationId) {
        throw new Error("nonconformity_organization_mismatch");
      }

      return mapNonconformityRecord(record);
    },
    async listNonconformingWorkByOrganization(organizationId) {
      const records = await prisma.nonconformingWorkCase.findMany({
        where: { organizationId },
        include: {
          serviceOrder: {
            select: {
              workOrderNumber: true,
            },
          },
        },
        orderBy: { updatedAt: "desc" },
      });

      return records.map((record) => mapNonconformingWorkRecord(record));
    },
    async saveNonconformingWork(input) {
      await assertTenantReferences(prisma, input.organizationId, {
        serviceOrderId: input.serviceOrderId,
        nonconformityId: input.nonconformityId,
      });
      if (input.caseId) {
        await assertRecordOwnership(prisma.nonconformingWorkCase, input.caseId, input.organizationId);
      }

      const data = {
        serviceOrderId: input.serviceOrderId,
        nonconformityId: input.nonconformityId,
        title: input.title.trim(),
        classificationLabel: input.classificationLabel.trim(),
        originLabel: input.originLabel.trim(),
        affectedEntityLabel: input.affectedEntityLabel.trim(),
        status: input.status,
        noticeLabel: input.noticeLabel.trim(),
        containmentLabel: input.containmentLabel.trim(),
        releaseRuleLabel: input.releaseRuleLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        restorationLabel: input.restorationLabel.trim(),
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
      };

      const record = input.caseId
        ? await prisma.nonconformingWorkCase.update({
            where: { id: input.caseId },
            data,
            include: {
              serviceOrder: {
                select: {
                  workOrderNumber: true,
                },
              },
            },
          })
        : await prisma.nonconformingWorkCase.create({
            data: {
              id: crypto.randomUUID(),
              organizationId: input.organizationId,
              ...data,
            },
            include: {
              serviceOrder: {
                select: {
                  workOrderNumber: true,
                },
              },
            },
          });

      if (record.organizationId !== input.organizationId) {
        throw new Error("nonconforming_work_organization_mismatch");
      }

      return mapNonconformingWorkRecord(record);
    },
    async listInternalAuditCyclesByOrganization(organizationId) {
      const records = await prisma.internalAuditCycle.findMany({
        where: { organizationId },
        orderBy: { scheduledAt: "desc" },
      });

      return records.map((record) => mapInternalAuditCycleRecord(record));
    },
    async saveInternalAuditCycle(input) {
      if (input.cycleId) {
        await assertRecordOwnership(prisma.internalAuditCycle, input.cycleId, input.organizationId);
      }
      const data = {
        cycleLabel: input.cycleLabel.trim(),
        windowLabel: input.windowLabel.trim(),
        scopeLabel: input.scopeLabel.trim(),
        auditorLabel: input.auditorLabel.trim(),
        auditeeLabel: input.auditeeLabel.trim(),
        periodLabel: input.periodLabel.trim(),
        reportLabel: input.reportLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        nextReviewLabel: input.nextReviewLabel.trim(),
        noticeLabel: input.noticeLabel.trim(),
        status: input.status,
        checklistItems: sanitizeChecklist(input.checklist) as unknown as object,
        findingRefs: sanitizeStringArray(input.findingRefs),
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
        scheduledAt: input.scheduledAt,
        completedAt: input.completedAt ?? null,
      };

      const record = input.cycleId
        ? await prisma.internalAuditCycle.update({
            where: { id: input.cycleId },
            data,
          })
        : await prisma.internalAuditCycle.create({
            data: {
              id: crypto.randomUUID(),
              organizationId: input.organizationId,
              ...data,
            },
          });

      if (record.organizationId !== input.organizationId) {
        throw new Error("internal_audit_organization_mismatch");
      }

      return mapInternalAuditCycleRecord(record);
    },
    async listManagementReviewMeetingsByOrganization(organizationId) {
      const records = await prisma.managementReviewMeeting.findMany({
        where: { organizationId },
        orderBy: { scheduledFor: "desc" },
      });

      return records.map((record) => mapManagementReviewMeetingRecord(record));
    },
    async saveManagementReviewMeeting(input) {
      if (input.meetingId) {
        await assertRecordOwnership(prisma.managementReviewMeeting, input.meetingId, input.organizationId);
      }
      const data = {
        titleLabel: input.titleLabel.trim(),
        status: input.status,
        dateLabel: input.dateLabel.trim(),
        outcomeLabel: input.outcomeLabel.trim(),
        noticeLabel: input.noticeLabel.trim(),
        nextMeetingLabel: input.nextMeetingLabel.trim(),
        chairLabel: input.chairLabel.trim(),
        attendeesLabel: input.attendeesLabel.trim(),
        periodLabel: input.periodLabel.trim(),
        ataLabel: input.ataLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        agendaItems: sanitizeAgendaItems(input.agendaItems) as unknown as object,
        decisions: sanitizeDecisionItems(input.decisions) as unknown as object,
        blockers: sanitizeStringArray(input.blockers),
        warnings: sanitizeStringArray(input.warnings),
        scheduledFor: input.scheduledFor,
        heldAt: input.heldAt ?? null,
      };

      const record = input.meetingId
        ? await prisma.managementReviewMeeting.update({
            where: { id: input.meetingId },
            data,
          })
        : await prisma.managementReviewMeeting.create({
            data: {
              id: crypto.randomUUID(),
              organizationId: input.organizationId,
              ...data,
            },
          });

      if (record.organizationId !== input.organizationId) {
        throw new Error("management_review_organization_mismatch");
      }

      return mapManagementReviewMeetingRecord(record);
    },
    async getComplianceProfileByOrganization(organizationId) {
      const record = await prisma.organizationComplianceProfile.findUnique({
        where: { organizationId },
        include: {
          organization: true,
        },
      });

      return record ? mapComplianceProfileRecord(record) : null;
    },
    async saveComplianceProfile(input) {
      const record = await prisma.organizationComplianceProfile.upsert({
        where: { organizationId: input.organizationId },
        update: {
          organizationCode: input.organizationCode.trim(),
          planLabel: input.planLabel.trim(),
          certificatePrefix: input.certificatePrefix.trim(),
          accreditationNumber: trimOptional(input.accreditationNumber) ?? null,
          accreditationValidUntil: input.accreditationValidUntil ?? null,
          scopeSummary: input.scopeSummary.trim(),
          cmcSummary: input.cmcSummary.trim(),
          scopeItemCount: Math.max(0, input.scopeItemCount),
          cmcItemCount: Math.max(0, input.cmcItemCount),
          legalOpinionStatus: input.legalOpinionStatus.trim(),
          legalOpinionReference: input.legalOpinionReference.trim(),
          dpaReference: input.dpaReference.trim(),
          normativeGovernanceStatus: input.normativeGovernanceStatus.trim(),
          normativeGovernanceOwner: input.normativeGovernanceOwner.trim(),
          normativeGovernanceReference: input.normativeGovernanceReference.trim(),
          releaseNormVersion: input.releaseNormVersion.trim(),
          releaseNormStatus: input.releaseNormStatus.trim(),
          lastReviewedAt: input.lastReviewedAt,
          organization: input.regulatoryProfile
            ? {
                update: {
                  regulatoryProfile: input.regulatoryProfile.trim(),
                },
              }
            : undefined,
        },
        create: {
          id: crypto.randomUUID(),
          organizationId: input.organizationId,
          organizationCode: input.organizationCode.trim(),
          planLabel: input.planLabel.trim(),
          certificatePrefix: input.certificatePrefix.trim(),
          accreditationNumber: trimOptional(input.accreditationNumber) ?? null,
          accreditationValidUntil: input.accreditationValidUntil ?? null,
          scopeSummary: input.scopeSummary.trim(),
          cmcSummary: input.cmcSummary.trim(),
          scopeItemCount: Math.max(0, input.scopeItemCount),
          cmcItemCount: Math.max(0, input.cmcItemCount),
          legalOpinionStatus: input.legalOpinionStatus.trim(),
          legalOpinionReference: input.legalOpinionReference.trim(),
          dpaReference: input.dpaReference.trim(),
          normativeGovernanceStatus: input.normativeGovernanceStatus.trim(),
          normativeGovernanceOwner: input.normativeGovernanceOwner.trim(),
          normativeGovernanceReference: input.normativeGovernanceReference.trim(),
          releaseNormVersion: input.releaseNormVersion.trim(),
          releaseNormStatus: input.releaseNormStatus.trim(),
          lastReviewedAt: input.lastReviewedAt,
        },
        include: {
          organization: true,
        },
      });

      return mapComplianceProfileRecord(record);
    },
    async listQualityIndicatorSnapshotsByOrganization(organizationId) {
      const records = await prisma.qualityIndicatorSnapshot.findMany({
        where: { organizationId },
        orderBy: [{ indicatorId: "asc" }, { monthStart: "asc" }],
      });

      return records.map((record) => mapQualityIndicatorSnapshotRecord(record));
    },
    async saveQualityIndicatorSnapshot(input) {
      if (input.snapshotId) {
        await assertRecordOwnership(prisma.qualityIndicatorSnapshot, input.snapshotId, input.organizationId);
      }

      const data = {
        indicatorId: input.indicatorId.trim(),
        monthStart: input.monthStart,
        valueNumeric: input.valueNumeric,
        targetNumeric: input.targetNumeric ?? null,
        status: input.status,
        sourceLabel: input.sourceLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
      };

      const record = input.snapshotId
        ? await prisma.qualityIndicatorSnapshot.update({
            where: { id: input.snapshotId },
            data,
          })
        : await prisma.qualityIndicatorSnapshot.create({
            data: {
              id: crypto.randomUUID(),
              organizationId: input.organizationId,
              ...data,
            },
          });

      if (record.organizationId !== input.organizationId) {
        throw new Error("quality_indicator_snapshot_organization_mismatch");
      }

      return mapQualityIndicatorSnapshotRecord(record);
    },
  };
}

function compareNonconformities(left: PersistedNonconformityRecord, right: PersistedNonconformityRecord) {
  const leftWeight = statusWeight(left.status);
  const rightWeight = statusWeight(right.status);
  if (leftWeight !== rightWeight) {
    return rightWeight - leftWeight;
  }
  return left.dueAtUtc.localeCompare(right.dueAtUtc);
}

function statusWeight(status: "ready" | "attention" | "blocked") {
  if (status === "blocked") return 3;
  if (status === "attention") return 2;
  return 1;
}

function sanitizeStringArray(values: string[]) {
  return values.map((value) => value.trim()).filter((value) => value.length > 0);
}

function sanitizeChecklist(values: PersistedInternalAuditChecklistItem[]) {
  return values
    .map((value, index) => ({
      key: value.key.trim() || `check-${index + 1}`,
      requirementLabel: value.requirementLabel.trim(),
      evidenceLabel: value.evidenceLabel.trim(),
      status: value.status,
    }))
    .filter((value) => value.requirementLabel.length > 0 && value.evidenceLabel.length > 0);
}

function sanitizeAgendaItems(values: PersistedManagementReviewAgendaItem[]) {
  return values
    .map((value, index) => ({
      key: value.key.trim() || `agenda-${index + 1}`,
      label: value.label.trim(),
      status: value.status,
    }))
    .filter((value) => value.label.length > 0);
}

function sanitizeDecisionItems(values: PersistedManagementReviewDecisionItem[]) {
  return values
    .map((value, index) => ({
      key: value.key.trim() || `decision-${index + 1}`,
      label: value.label.trim(),
      ownerLabel: value.ownerLabel.trim(),
      dueDateLabel: value.dueDateLabel.trim(),
      status: value.status,
    }))
    .filter((value) => value.label.length > 0 && value.ownerLabel.length > 0);
}

function trimOptional(value: string | undefined) {
  if (!value) return undefined;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

async function assertTenantReferences(
  prisma: PrismaClient,
  organizationId: string,
  refs: {
    serviceOrderId?: string;
    ownerUserId?: string;
    nonconformityId?: string;
  },
) {
  if (refs.serviceOrderId) {
    const serviceOrder = await prisma.serviceOrder.findUnique({
      where: { id: refs.serviceOrderId },
      select: { organizationId: true },
    });
    if (!serviceOrder || serviceOrder.organizationId !== organizationId) {
      throw new Error("service_order_organization_mismatch");
    }
  }

  if (refs.ownerUserId) {
    const user = await prisma.appUser.findUnique({
      where: { id: refs.ownerUserId },
      select: { organizationId: true },
    });
    if (!user || user.organizationId !== organizationId) {
      throw new Error("owner_user_organization_mismatch");
    }
  }

  if (refs.nonconformityId) {
    const nc = await prisma.nonconformity.findUnique({
      where: { id: refs.nonconformityId },
      select: { organizationId: true },
    });
    if (!nc || nc.organizationId !== organizationId) {
      throw new Error("nonconformity_organization_mismatch");
    }
  }
}

async function assertRecordOwnership(
  delegate: {
    findUnique(args: { where: { id: string }; select: { organizationId: true } }): Promise<{
      organizationId: string;
    } | null>;
  },
  id: string,
  organizationId: string,
) {
  const record = await delegate.findUnique({
    where: { id },
    select: { organizationId: true },
  });

  if (!record || record.organizationId !== organizationId) {
    throw new Error("record_organization_mismatch");
  }
}

function mapNonconformityRecord(
  record: {
    id: string;
    organizationId: string;
    serviceOrderId: string | null;
    ownerUserId: string | null;
    title: string;
    originLabel: string;
    severityLabel: string;
    status: string;
    noticeLabel: string;
    rootCauseLabel: string;
    containmentLabel: string;
    correctiveActionLabel: string;
    evidenceLabel: string;
    blockers: string[];
    warnings: string[];
    openedAt: Date;
    dueAt: Date;
    resolvedAt: Date | null;
    ownerUser?: { displayName: string } | null;
    serviceOrder?: { workOrderNumber: string; certificateNumber: string | null } | null;
  },
): PersistedNonconformityRecord {
  return {
    ncId: record.id,
    organizationId: record.organizationId,
    serviceOrderId: record.serviceOrderId ?? undefined,
    workOrderNumber: record.serviceOrder?.workOrderNumber ?? undefined,
    certificateNumber: record.serviceOrder?.certificateNumber ?? undefined,
    ownerUserId: record.ownerUserId ?? undefined,
    ownerLabel: record.ownerUser?.displayName ?? "Responsavel da Qualidade",
    title: record.title,
    originLabel: record.originLabel,
    severityLabel: record.severityLabel,
    status: normalizeOperationalStatus(record.status),
    noticeLabel: record.noticeLabel,
    rootCauseLabel: record.rootCauseLabel,
    containmentLabel: record.containmentLabel,
    correctiveActionLabel: record.correctiveActionLabel,
    evidenceLabel: record.evidenceLabel,
    blockers: record.blockers,
    warnings: record.warnings,
    openedAtUtc: record.openedAt.toISOString(),
    dueAtUtc: record.dueAt.toISOString(),
    resolvedAtUtc: record.resolvedAt?.toISOString(),
  };
}

function mapNonconformingWorkRecord(
  record: {
    id: string;
    organizationId: string;
    serviceOrderId: string | null;
    nonconformityId: string | null;
    title: string;
    classificationLabel: string;
    originLabel: string;
    affectedEntityLabel: string;
    status: string;
    noticeLabel: string;
    containmentLabel: string;
    releaseRuleLabel: string;
    evidenceLabel: string;
    restorationLabel: string;
    blockers: string[];
    warnings: string[];
    createdAt: Date;
    updatedAt: Date;
    serviceOrder?: { workOrderNumber: string } | null;
  },
): PersistedNonconformingWorkRecord {
  return {
    caseId: record.id,
    organizationId: record.organizationId,
    serviceOrderId: record.serviceOrderId ?? undefined,
    workOrderNumber: record.serviceOrder?.workOrderNumber ?? undefined,
    nonconformityId: record.nonconformityId ?? undefined,
    title: record.title,
    classificationLabel: record.classificationLabel,
    originLabel: record.originLabel,
    affectedEntityLabel: record.affectedEntityLabel,
    status: normalizeOperationalStatus(record.status),
    noticeLabel: record.noticeLabel,
    containmentLabel: record.containmentLabel,
    releaseRuleLabel: record.releaseRuleLabel,
    evidenceLabel: record.evidenceLabel,
    restorationLabel: record.restorationLabel,
    blockers: record.blockers,
    warnings: record.warnings,
    createdAtUtc: record.createdAt.toISOString(),
    updatedAtUtc: record.updatedAt.toISOString(),
  };
}

function mapInternalAuditCycleRecord(
  record: {
    id: string;
    organizationId: string;
    cycleLabel: string;
    windowLabel: string;
    scopeLabel: string;
    auditorLabel: string;
    auditeeLabel: string;
    periodLabel: string;
    reportLabel: string;
    evidenceLabel: string;
    nextReviewLabel: string;
    noticeLabel: string;
    status: string;
    checklistItems: unknown;
    findingRefs: string[];
    blockers: string[];
    warnings: string[];
    scheduledAt: Date;
    completedAt: Date | null;
  },
): PersistedInternalAuditCycleRecord {
  return {
    cycleId: record.id,
    organizationId: record.organizationId,
    cycleLabel: record.cycleLabel,
    windowLabel: record.windowLabel,
    scopeLabel: record.scopeLabel,
    auditorLabel: record.auditorLabel,
    auditeeLabel: record.auditeeLabel,
    periodLabel: record.periodLabel,
    reportLabel: record.reportLabel,
    evidenceLabel: record.evidenceLabel,
    nextReviewLabel: record.nextReviewLabel,
    noticeLabel: record.noticeLabel,
    status: normalizeOperationalStatus(record.status),
    checklist: parseChecklist(record.checklistItems),
    findingRefs: record.findingRefs,
    blockers: record.blockers,
    warnings: record.warnings,
    scheduledAtUtc: record.scheduledAt.toISOString(),
    completedAtUtc: record.completedAt?.toISOString(),
  };
}

function mapManagementReviewMeetingRecord(
  record: {
    id: string;
    organizationId: string;
    titleLabel: string;
    status: string;
    dateLabel: string;
    outcomeLabel: string;
    noticeLabel: string;
    nextMeetingLabel: string;
    chairLabel: string;
    attendeesLabel: string;
    periodLabel: string;
    ataLabel: string;
    evidenceLabel: string;
    agendaItems: unknown;
    decisions: unknown;
    blockers: string[];
    warnings: string[];
    scheduledFor: Date;
    heldAt: Date | null;
  },
): PersistedManagementReviewMeetingRecord {
  return {
    meetingId: record.id,
    organizationId: record.organizationId,
    titleLabel: record.titleLabel,
    status: normalizeOperationalStatus(record.status),
    dateLabel: record.dateLabel,
    outcomeLabel: record.outcomeLabel,
    noticeLabel: record.noticeLabel,
    nextMeetingLabel: record.nextMeetingLabel,
    chairLabel: record.chairLabel,
    attendeesLabel: record.attendeesLabel,
    periodLabel: record.periodLabel,
    ataLabel: record.ataLabel,
    evidenceLabel: record.evidenceLabel,
    agendaItems: parseAgendaItems(record.agendaItems),
    decisions: parseDecisionItems(record.decisions),
    blockers: record.blockers,
    warnings: record.warnings,
    scheduledForUtc: record.scheduledFor.toISOString(),
    heldAtUtc: record.heldAt?.toISOString(),
  };
}

function mapComplianceProfileRecord(
  record: {
    id: string;
    organizationId: string;
    organizationCode: string;
    planLabel: string;
    certificatePrefix: string;
    accreditationNumber: string | null;
    accreditationValidUntil: Date | null;
    scopeSummary: string;
    cmcSummary: string;
    scopeItemCount: number;
    cmcItemCount: number;
    legalOpinionStatus: string;
    legalOpinionReference: string;
    dpaReference: string;
    normativeGovernanceStatus: string;
    normativeGovernanceOwner: string;
    normativeGovernanceReference: string;
    releaseNormVersion: string;
    releaseNormStatus: string;
    lastReviewedAt: Date;
    organization: {
      legalName: string;
      slug: string;
      regulatoryProfile: string;
      normativePackageVersion: string;
    };
  },
): PersistedComplianceProfileRecord {
  return {
    complianceProfileId: record.id,
    organizationId: record.organizationId,
    organizationName: record.organization.legalName,
    organizationSlug: record.organization.slug,
    regulatoryProfile: record.organization.regulatoryProfile,
    normativePackageVersion: record.organization.normativePackageVersion,
    organizationCode: record.organizationCode,
    planLabel: record.planLabel,
    certificatePrefix: record.certificatePrefix,
    accreditationNumber: record.accreditationNumber ?? undefined,
    accreditationValidUntilUtc: record.accreditationValidUntil?.toISOString(),
    scopeSummary: record.scopeSummary,
    cmcSummary: record.cmcSummary,
    scopeItemCount: record.scopeItemCount,
    cmcItemCount: record.cmcItemCount,
    legalOpinionStatus: record.legalOpinionStatus,
    legalOpinionReference: record.legalOpinionReference,
    dpaReference: record.dpaReference,
    normativeGovernanceStatus: record.normativeGovernanceStatus,
    normativeGovernanceOwner: record.normativeGovernanceOwner,
    normativeGovernanceReference: record.normativeGovernanceReference,
    releaseNormVersion: record.releaseNormVersion,
    releaseNormStatus: record.releaseNormStatus,
    lastReviewedAtUtc: record.lastReviewedAt.toISOString(),
  };
}

function mapQualityIndicatorSnapshotRecord(
  record: {
    id: string;
    organizationId: string;
    indicatorId: string;
    monthStart: Date;
    valueNumeric: number;
    targetNumeric: number | null;
    status: string;
    sourceLabel: string;
    evidenceLabel: string;
    createdAt: Date;
    updatedAt: Date;
  },
): PersistedQualityIndicatorSnapshotRecord {
  return {
    snapshotId: record.id,
    organizationId: record.organizationId,
    indicatorId: record.indicatorId,
    monthStartUtc: record.monthStart.toISOString(),
    valueNumeric: record.valueNumeric,
    targetNumeric: record.targetNumeric ?? undefined,
    status: normalizeOperationalStatus(record.status),
    sourceLabel: record.sourceLabel,
    evidenceLabel: record.evidenceLabel,
    createdAtUtc: record.createdAt.toISOString(),
    updatedAtUtc: record.updatedAt.toISOString(),
  };
}

function parseChecklist(value: unknown): PersistedInternalAuditChecklistItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((entry): entry is Record<string, unknown> => Boolean(entry) && typeof entry === "object")
    .map((entry, index) => ({
      key: typeof entry.key === "string" && entry.key.length > 0 ? entry.key : `check-${index + 1}`,
      requirementLabel:
        typeof entry.requirementLabel === "string" ? entry.requirementLabel : "Requisito nao informado",
      evidenceLabel: typeof entry.evidenceLabel === "string" ? entry.evidenceLabel : "Evidencia nao informada",
      status: normalizeOperationalStatus(
        typeof entry.status === "string" ? entry.status : "attention",
      ),
    }));
}

function parseAgendaItems(value: unknown): PersistedManagementReviewAgendaItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((entry): entry is Record<string, unknown> => Boolean(entry) && typeof entry === "object")
    .map((entry, index) => ({
      key: typeof entry.key === "string" && entry.key.length > 0 ? entry.key : `agenda-${index + 1}`,
      label: typeof entry.label === "string" ? entry.label : "Item de pauta",
      status: normalizeOperationalStatus(typeof entry.status === "string" ? entry.status : "attention"),
    }));
}

function parseDecisionItems(value: unknown): PersistedManagementReviewDecisionItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((entry): entry is Record<string, unknown> => Boolean(entry) && typeof entry === "object")
    .map((entry, index) => ({
      key: typeof entry.key === "string" && entry.key.length > 0 ? entry.key : `decision-${index + 1}`,
      label: typeof entry.label === "string" ? entry.label : "Deliberacao",
      ownerLabel: typeof entry.ownerLabel === "string" ? entry.ownerLabel : "Direcao",
      dueDateLabel: typeof entry.dueDateLabel === "string" ? entry.dueDateLabel : "Sem prazo",
      status: normalizeOperationalStatus(typeof entry.status === "string" ? entry.status : "attention"),
    }));
}

function normalizeOperationalStatus(value: string): "ready" | "attention" | "blocked" {
  if (value === "ready" || value === "attention" || value === "blocked") {
    return value;
  }

  if (/resolved|closed|complete|approved|archived/i.test(value)) {
    return "ready";
  }

  if (/critical|blocked|rejected|extraordinary/i.test(value)) {
    return "blocked";
  }

  return "attention";
}
