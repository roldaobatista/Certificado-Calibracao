import { computeAuditHash } from "@afere/audit-log";
import type { PrismaClient } from "@prisma/client";

import type { ServiceOrderListItemStatus } from "@afere/contracts";

export type ReviewDecision = "pending" | "approved" | "rejected";

export type PersistedEmissionAuditEvent = {
  eventId: string;
  organizationId: string;
  serviceOrderId: string;
  workOrderNumber: string;
  actorUserId?: string;
  actorLabel: string;
  action: string;
  entityLabel: string;
  deviceId?: string;
  certificateNumber?: string;
  prevHash: string;
  hash: string;
  occurredAtUtc: string;
};

export type PersistedServiceOrderRecord = {
  serviceOrderId: string;
  organizationId: string;
  customerId: string;
  customerName: string;
  customerAddress: {
    line1: string;
    city: string;
    state: string;
    postalCode?: string;
    country: string;
  };
  equipmentId: string;
  equipmentLabel: string;
  equipmentCode: string;
  equipmentTagCode: string;
  equipmentSerialNumber: string;
  instrumentType: string;
  procedureId: string;
  procedureLabel: string;
  primaryStandardId: string;
  standardsLabel: string;
  standardSource: "INM" | "RBC" | "ILAC_MRA";
  standardCertificateReference: string;
  standardHasValidCertificate: boolean;
  standardCertificateValidUntilUtc?: string;
  standardMeasurementValue: number;
  standardApplicableRange: {
    minimum: number;
    maximum: number;
  };
  executorUserId: string;
  executorName: string;
  reviewerUserId?: string;
  reviewerName?: string;
  signatoryUserId?: string;
  signatoryName?: string;
  workOrderNumber: string;
  workflowStatus: ServiceOrderListItemStatus;
  environmentLabel: string;
  curvePointsLabel: string;
  evidenceLabel: string;
  uncertaintyLabel: string;
  conformityLabel: string;
  measurementResultValue?: number;
  measurementExpandedUncertaintyValue?: number;
  measurementCoverageFactor?: number;
  measurementUnit?: string;
  decisionRuleLabel?: string;
  decisionOutcomeLabel?: string;
  freeTextStatement?: string;
  commentDraft: string;
  reviewDecision: ReviewDecision;
  reviewDecisionComment: string;
  reviewDeviceId?: string;
  signatureDeviceId?: string;
  signatureStatement?: string;
  certificateNumber?: string;
  certificateRevision?: string;
  publicVerificationToken?: string;
  documentHash?: string;
  qrHost?: string;
  createdAtUtc: string;
  acceptedAtUtc?: string;
  executionStartedAtUtc?: string;
  executedAtUtc?: string;
  reviewStartedAtUtc?: string;
  reviewCompletedAtUtc?: string;
  signatureStartedAtUtc?: string;
  signedAtUtc?: string;
  emittedAtUtc?: string;
  updatedAtUtc: string;
  archivedAtUtc?: string;
};

type ServiceOrderReferenceUser = {
  userId: string;
  organizationId: string;
  displayName: string;
  status: "active" | "invited" | "suspended";
};

type ServiceOrderReferenceCustomer = {
  customerId: string;
  organizationId: string;
  tradeName: string;
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode?: string;
  addressCountry: string;
};

type ServiceOrderReferenceEquipment = {
  equipmentId: string;
  organizationId: string;
  customerId: string;
  procedureId?: string;
  primaryStandardId?: string;
  code: string;
  tagCode: string;
  serialNumber: string;
  typeModelLabel: string;
};

type ServiceOrderReferenceProcedure = {
  procedureId: string;
  organizationId: string;
  code: string;
  revisionLabel: string;
};

type ServiceOrderReferenceStandard = {
  standardId: string;
  organizationId: string;
  code: string;
  title: string;
  sourceLabel: string;
  certificateLabel: string;
  hasValidCertificate: boolean;
  certificateValidUntilUtc?: string;
  measurementValue: number;
  applicableRangeMin: number;
  applicableRangeMax: number;
};

export type SaveServiceOrderInput = {
  organizationId: string;
  serviceOrderId?: string;
  customerId: string;
  equipmentId: string;
  procedureId: string;
  primaryStandardId: string;
  executorUserId: string;
  reviewerUserId?: string;
  signatoryUserId?: string;
  workOrderNumber: string;
  workflowStatus: ServiceOrderListItemStatus;
  environmentLabel: string;
  curvePointsLabel: string;
  evidenceLabel: string;
  uncertaintyLabel: string;
  conformityLabel: string;
  measurementResultValue?: number;
  measurementExpandedUncertaintyValue?: number;
  measurementCoverageFactor?: number;
  measurementUnit?: string;
  decisionRuleLabel?: string;
  decisionOutcomeLabel?: string;
  freeTextStatement?: string;
  commentDraft: string;
};

export type SaveServiceOrderWorkflowInput = {
  organizationId: string;
  serviceOrderId: string;
  reviewerUserId?: string;
  signatoryUserId?: string;
  workflowStatus: ServiceOrderListItemStatus;
  reviewDecision: ReviewDecision;
  reviewDecisionComment: string;
  reviewDeviceId?: string;
  commentDraft?: string;
};

export type EmitServiceOrderInput = {
  organizationId: string;
  serviceOrderId: string;
  signatoryUserId?: string;
  certificateNumber: string;
  certificateRevision: string;
  publicVerificationToken: string;
  documentHash: string;
  qrHost: string;
  signatureStatement: string;
  signatureDeviceId: string;
  occurredAt: Date;
};

type MutableAuditEventStore = {
  listByServiceOrder(serviceOrderId: string): Promise<PersistedEmissionAuditEvent[]>;
  append(input: {
    organizationId: string;
    serviceOrderId: string;
    workOrderNumber: string;
    actorUserId?: string;
    actorLabel: string;
    action: string;
    entityLabel: string;
    deviceId?: string;
    certificateNumber?: string;
    occurredAtUtc: string;
  }): Promise<PersistedEmissionAuditEvent>;
};

export interface ServiceOrderPersistence {
  listServiceOrdersByOrganization(organizationId: string): Promise<PersistedServiceOrderRecord[]>;
  listEmissionAuditEventsByOrganization(organizationId: string): Promise<PersistedEmissionAuditEvent[]>;
  saveServiceOrder(input: SaveServiceOrderInput): Promise<PersistedServiceOrderRecord>;
  saveServiceOrderWorkflow(input: SaveServiceOrderWorkflowInput): Promise<PersistedServiceOrderRecord>;
  emitServiceOrder(input: EmitServiceOrderInput): Promise<PersistedServiceOrderRecord>;
}

export function createMemoryServiceOrderPersistence(seed: {
  serviceOrders?: PersistedServiceOrderRecord[];
  emissionAuditEvents?: PersistedEmissionAuditEvent[];
  users?: ServiceOrderReferenceUser[];
  customers?: ServiceOrderReferenceCustomer[];
  equipment?: ServiceOrderReferenceEquipment[];
  procedures?: ServiceOrderReferenceProcedure[];
  standards?: ServiceOrderReferenceStandard[];
} = {}): ServiceOrderPersistence {
  const serviceOrders = new Map(
    (seed.serviceOrders ?? []).map((record) => [record.serviceOrderId, structuredClone(record)]),
  );
  const auditEvents = (seed.emissionAuditEvents ?? []).map((event) => structuredClone(event));
  const users = new Map((seed.users ?? []).map((user) => [user.userId, structuredClone(user)]));
  const customers = new Map(
    (seed.customers ?? []).map((customer) => [customer.customerId, structuredClone(customer)]),
  );
  const equipment = new Map(
    (seed.equipment ?? []).map((record) => [record.equipmentId, structuredClone(record)]),
  );
  const procedures = new Map(
    (seed.procedures ?? []).map((record) => [record.procedureId, structuredClone(record)]),
  );
  const standards = new Map(
    (seed.standards ?? []).map((record) => [record.standardId, structuredClone(record)]),
  );

  const auditStore: MutableAuditEventStore = {
    async listByServiceOrder(serviceOrderId) {
      return auditEvents
        .filter((event) => event.serviceOrderId === serviceOrderId)
        .sort(compareAuditEventsAsc)
        .map((event) => structuredClone(event));
    },
    async append(input) {
      const existing = auditEvents
        .filter((event) => event.serviceOrderId === input.serviceOrderId)
        .sort(compareAuditEventsAsc);
      const prevHash = existing.at(-1)?.hash ?? GENESIS_HASH;
      const hash = computeAuditHash(prevHash, buildAuditPayload(input));
      const event: PersistedEmissionAuditEvent = {
        eventId: `emission-audit-${auditEvents.length + 1}`,
        organizationId: input.organizationId,
        serviceOrderId: input.serviceOrderId,
        workOrderNumber: input.workOrderNumber,
        actorUserId: input.actorUserId,
        actorLabel: input.actorLabel,
        action: input.action,
        entityLabel: input.entityLabel,
        deviceId: input.deviceId,
        certificateNumber: input.certificateNumber,
        prevHash,
        hash,
        occurredAtUtc: input.occurredAtUtc,
      };
      auditEvents.push(event);
      return structuredClone(event);
    },
  };

  return {
    async listServiceOrdersByOrganization(organizationId) {
      return Array.from(serviceOrders.values())
        .filter((record) => record.organizationId === organizationId && !record.archivedAtUtc)
        .sort((left, right) => right.updatedAtUtc.localeCompare(left.updatedAtUtc))
        .map((record) => structuredClone(record));
    },
    async listEmissionAuditEventsByOrganization(organizationId) {
      return auditEvents
        .filter((event) => event.organizationId === organizationId)
        .sort(compareAuditEventsDesc)
        .map((event) => structuredClone(event));
    },
    async saveServiceOrder(input) {
      const existing = input.serviceOrderId ? serviceOrders.get(input.serviceOrderId) : undefined;
      const references = resolveMemoryReferences({
        input,
        organizationId: input.organizationId,
        customers,
        equipment,
        procedures,
        standards,
        users,
      });

      const duplicate = Array.from(serviceOrders.values()).find(
        (record) =>
          record.organizationId === input.organizationId &&
          record.workOrderNumber === input.workOrderNumber.trim() &&
          record.serviceOrderId !== input.serviceOrderId,
      );
      if (duplicate) {
        throw new Error("duplicate_work_order_number");
      }

      const nowUtc = new Date().toISOString();
      const saved: PersistedServiceOrderRecord = {
        serviceOrderId: input.serviceOrderId ?? `service-order-${serviceOrders.size + 1}`,
        organizationId: input.organizationId,
        customerId: references.customer.customerId,
        customerName: references.customer.tradeName,
        customerAddress: {
          line1: references.customer.addressLine1,
          city: references.customer.addressCity,
          state: references.customer.addressState,
          postalCode: references.customer.addressPostalCode,
          country: references.customer.addressCountry,
        },
        equipmentId: references.equipment.equipmentId,
        equipmentLabel: `${references.equipment.code} · ${references.equipment.typeModelLabel}`,
        equipmentCode: references.equipment.code,
        equipmentTagCode: references.equipment.tagCode,
        equipmentSerialNumber: references.equipment.serialNumber,
        instrumentType: inferInstrumentType(references.equipment.typeModelLabel),
        procedureId: references.procedure.procedureId,
        procedureLabel: `${references.procedure.code} rev.${references.procedure.revisionLabel}`,
        primaryStandardId: references.standard.standardId,
        standardsLabel: `${references.standard.code} · ${references.standard.title}`,
        standardSource: mapStandardSource(references.standard.sourceLabel),
        standardCertificateReference: references.standard.certificateLabel,
        standardHasValidCertificate: references.standard.hasValidCertificate,
        standardCertificateValidUntilUtc: references.standard.certificateValidUntilUtc,
        standardMeasurementValue: references.standard.measurementValue,
        standardApplicableRange: {
          minimum: references.standard.applicableRangeMin,
          maximum: references.standard.applicableRangeMax,
        },
        executorUserId: references.executor.userId,
        executorName: references.executor.displayName,
        reviewerUserId: references.reviewer?.userId,
        reviewerName: references.reviewer?.displayName,
        signatoryUserId: references.signatory?.userId ?? existing?.signatoryUserId,
        signatoryName: references.signatory?.displayName ?? existing?.signatoryName,
        workOrderNumber: input.workOrderNumber.trim(),
        workflowStatus: input.workflowStatus,
        environmentLabel: input.environmentLabel.trim(),
        curvePointsLabel: input.curvePointsLabel.trim(),
        evidenceLabel: input.evidenceLabel.trim(),
        uncertaintyLabel: input.uncertaintyLabel.trim(),
        conformityLabel: input.conformityLabel.trim(),
        measurementResultValue: input.measurementResultValue ?? existing?.measurementResultValue,
        measurementExpandedUncertaintyValue:
          input.measurementExpandedUncertaintyValue ?? existing?.measurementExpandedUncertaintyValue,
        measurementCoverageFactor:
          input.measurementCoverageFactor ?? existing?.measurementCoverageFactor,
        measurementUnit: normalizeOptionalString(input.measurementUnit) ?? existing?.measurementUnit,
        decisionRuleLabel: normalizeOptionalString(input.decisionRuleLabel) ?? existing?.decisionRuleLabel,
        decisionOutcomeLabel:
          normalizeOptionalString(input.decisionOutcomeLabel) ?? existing?.decisionOutcomeLabel,
        freeTextStatement:
          normalizeOptionalString(input.freeTextStatement) ?? existing?.freeTextStatement,
        commentDraft: input.commentDraft.trim(),
        reviewDecision: existing?.reviewDecision ?? "pending",
        reviewDecisionComment: existing?.reviewDecisionComment ?? "",
        reviewDeviceId: existing?.reviewDeviceId,
        signatureDeviceId: existing?.signatureDeviceId,
        signatureStatement: existing?.signatureStatement,
        certificateNumber: existing?.certificateNumber,
        certificateRevision: existing?.certificateRevision,
        publicVerificationToken: existing?.publicVerificationToken,
        documentHash: existing?.documentHash,
        qrHost: existing?.qrHost,
        createdAtUtc: existing?.createdAtUtc ?? nowUtc,
        acceptedAtUtc: resolveAcceptedAtUtc(existing, input.workflowStatus, nowUtc),
        executionStartedAtUtc: resolveExecutionStartedAtUtc(existing, input.workflowStatus, nowUtc),
        executedAtUtc: resolveExecutedAtUtc(existing, input.workflowStatus, nowUtc),
        reviewStartedAtUtc: resolveReviewStartedAtUtc(existing, input.workflowStatus, nowUtc),
        reviewCompletedAtUtc: resolveReviewCompletedAtUtc(existing, existing?.reviewDecision ?? "pending", input.workflowStatus, nowUtc),
        signatureStartedAtUtc: resolveSignatureStartedAtUtc(existing, input.workflowStatus, nowUtc),
        signedAtUtc: existing?.signedAtUtc,
        emittedAtUtc: input.workflowStatus === "emitted" ? existing?.emittedAtUtc ?? nowUtc : existing?.emittedAtUtc,
        updatedAtUtc: nowUtc,
        archivedAtUtc: existing?.archivedAtUtc,
      };

      serviceOrders.set(saved.serviceOrderId, saved);
      await ensureDerivedAuditEvents(auditStore, saved);
      return structuredClone(saved);
    },
    async saveServiceOrderWorkflow(input) {
      const existing = serviceOrders.get(input.serviceOrderId);
      if (!existing || existing.organizationId !== input.organizationId) {
        throw new Error("service_order_not_found");
      }

      const reviewer = input.reviewerUserId
        ? requireActiveUser(users.get(input.reviewerUserId), input.organizationId, "reviewer_not_found")
        : undefined;
      const signatory = input.signatoryUserId
        ? requireActiveUser(users.get(input.signatoryUserId), input.organizationId, "signatory_not_found")
        : undefined;
      const nowUtc = new Date().toISOString();
      const updated: PersistedServiceOrderRecord = {
        ...existing,
        reviewerUserId: input.reviewerUserId ?? existing.reviewerUserId,
        reviewerName: reviewer?.displayName ?? existing.reviewerName,
        signatoryUserId: input.signatoryUserId ?? existing.signatoryUserId,
        signatoryName: signatory?.displayName ?? existing.signatoryName,
        workflowStatus: input.workflowStatus,
        reviewDecision: input.reviewDecision,
        reviewDecisionComment: input.reviewDecisionComment.trim(),
        reviewDeviceId: normalizeOptionalString(input.reviewDeviceId),
        commentDraft: normalizeOptionalString(input.commentDraft) ?? existing.commentDraft,
        reviewStartedAtUtc: existing.reviewStartedAtUtc ?? nowUtc,
        reviewCompletedAtUtc:
          input.reviewDecision === "approved" || input.reviewDecision === "rejected"
            ? existing.reviewCompletedAtUtc ?? nowUtc
            : existing.reviewCompletedAtUtc,
        signatureStartedAtUtc:
          input.workflowStatus === "awaiting_signature" || input.workflowStatus === "emitted"
            ? existing.signatureStartedAtUtc ?? nowUtc
            : existing.signatureStartedAtUtc,
        updatedAtUtc: nowUtc,
      };

      serviceOrders.set(updated.serviceOrderId, updated);
      await ensureDerivedAuditEvents(auditStore, updated);
      return structuredClone(updated);
    },
    async emitServiceOrder(input) {
      const existing = serviceOrders.get(input.serviceOrderId);
      if (!existing || existing.organizationId !== input.organizationId) {
        throw new Error("service_order_not_found");
      }

      const signatoryId = input.signatoryUserId ?? existing.signatoryUserId;
      const signatory = signatoryId
        ? requireActiveUser(users.get(signatoryId), input.organizationId, "signatory_not_found")
        : undefined;

      if (!signatory) {
        throw new Error("signatory_not_found");
      }

      const occurredAtUtc = input.occurredAt.toISOString();
      const updated: PersistedServiceOrderRecord = {
        ...existing,
        signatoryUserId: signatory.userId,
        signatoryName: signatory.displayName,
        workflowStatus: "emitted",
        reviewDecision: "approved",
        certificateNumber: input.certificateNumber,
        certificateRevision: input.certificateRevision,
        publicVerificationToken: input.publicVerificationToken,
        documentHash: input.documentHash,
        qrHost: input.qrHost,
        signatureStatement: input.signatureStatement.trim(),
        signatureDeviceId: input.signatureDeviceId.trim(),
        signatureStartedAtUtc: existing.signatureStartedAtUtc ?? occurredAtUtc,
        signedAtUtc: existing.signedAtUtc ?? occurredAtUtc,
        emittedAtUtc: existing.emittedAtUtc ?? occurredAtUtc,
        updatedAtUtc: occurredAtUtc,
      };

      serviceOrders.set(updated.serviceOrderId, updated);
      await ensureDerivedAuditEvents(auditStore, updated);
      await ensureAuditEvent(auditStore, updated, {
        action: "certificate.signed",
        actorUserId: signatory.userId,
        actorLabel: signatory.displayName,
        deviceId: updated.signatureDeviceId,
        certificateNumber: updated.certificateNumber,
        entityLabel: updated.certificateNumber ?? updated.workOrderNumber,
        occurredAtUtc: updated.signedAtUtc ?? occurredAtUtc,
      });
      await ensureAuditEvent(auditStore, updated, {
        action: "certificate.emitted",
        actorUserId: signatory.userId,
        actorLabel: signatory.displayName,
        deviceId: updated.signatureDeviceId,
        certificateNumber: updated.certificateNumber,
        entityLabel: updated.certificateNumber ?? updated.workOrderNumber,
        occurredAtUtc: updated.emittedAtUtc ?? occurredAtUtc,
      });

      return structuredClone(updated);
    },
  };
}

export function createPrismaServiceOrderPersistence(prisma: PrismaClient): ServiceOrderPersistence {
  return {
    async listServiceOrdersByOrganization(organizationId) {
      const records = await prisma.serviceOrder.findMany({
        where: {
          organizationId,
          archivedAt: null,
        },
        include: serviceOrderInclude,
        orderBy: [{ updatedAt: "desc" }, { workOrderNumber: "desc" }],
      });

      return records.map(mapServiceOrderRecord);
    },
    async listEmissionAuditEventsByOrganization(organizationId) {
      const records = await prisma.emissionAuditEvent.findMany({
        where: { organizationId },
        include: {
          serviceOrder: {
            select: {
              workOrderNumber: true,
            },
          },
        },
        orderBy: [{ occurredAt: "desc" }, { createdAt: "desc" }],
      });

      return records.map((record) => ({
        eventId: record.id,
        organizationId: record.organizationId,
        serviceOrderId: record.serviceOrderId,
        workOrderNumber: record.serviceOrder.workOrderNumber,
        actorUserId: record.actorUserId ?? undefined,
        actorLabel: record.actorLabel,
        action: record.action,
        entityLabel: record.entityLabel,
        deviceId: record.deviceId ?? undefined,
        certificateNumber: record.certificateNumber ?? undefined,
        prevHash: record.prevHash,
        hash: record.hash,
        occurredAtUtc: record.occurredAt.toISOString(),
      }));
    },
    async saveServiceOrder(input) {
      return prisma.$transaction(async (tx) => {
        const existing = input.serviceOrderId
          ? await tx.serviceOrder.findFirst({
              where: { id: input.serviceOrderId, organizationId: input.organizationId },
              include: serviceOrderInclude,
            })
          : null;
        const references = await resolvePrismaReferences(tx, input);

        const duplicate = await tx.serviceOrder.findFirst({
          where: {
            organizationId: input.organizationId,
            workOrderNumber: input.workOrderNumber.trim(),
            id: input.serviceOrderId ? { not: input.serviceOrderId } : undefined,
          },
        });
        if (duplicate) {
          throw new Error("duplicate_work_order_number");
        }

        const now = new Date();
        const data = {
          customerId: input.customerId,
          equipmentId: input.equipmentId,
          procedureId: input.procedureId,
          primaryStandardId: input.primaryStandardId,
          executorUserId: input.executorUserId,
          reviewerUserId: input.reviewerUserId ?? null,
          signatoryUserId: input.signatoryUserId ?? existing?.signatoryUserId ?? null,
          workOrderNumber: input.workOrderNumber.trim(),
          workflowStatus: input.workflowStatus,
          environmentLabel: input.environmentLabel.trim(),
          curvePointsLabel: input.curvePointsLabel.trim(),
          evidenceLabel: input.evidenceLabel.trim(),
          uncertaintyLabel: input.uncertaintyLabel.trim(),
          conformityLabel: input.conformityLabel.trim(),
          measurementResultValue: input.measurementResultValue ?? existing?.measurementResultValue ?? null,
          measurementExpandedUncertaintyValue:
            input.measurementExpandedUncertaintyValue ??
            existing?.measurementExpandedUncertaintyValue ??
            null,
          measurementCoverageFactor:
            input.measurementCoverageFactor ?? existing?.measurementCoverageFactor ?? null,
          measurementUnit: normalizeOptionalString(input.measurementUnit) ?? existing?.measurementUnit ?? null,
          decisionRuleLabel:
            normalizeOptionalString(input.decisionRuleLabel) ?? existing?.decisionRuleLabel ?? null,
          decisionOutcomeLabel:
            normalizeOptionalString(input.decisionOutcomeLabel) ?? existing?.decisionOutcomeLabel ?? null,
          freeTextStatement:
            normalizeOptionalString(input.freeTextStatement) ?? existing?.freeTextStatement ?? null,
          commentDraft: input.commentDraft.trim(),
          reviewDecision: existing?.reviewDecision ?? "pending",
          reviewDecisionComment: existing?.reviewDecisionComment ?? "",
          reviewDeviceId: existing?.reviewDeviceId ?? null,
          signatureDeviceId: existing?.signatureDeviceId ?? null,
          signatureStatement: existing?.signatureStatement ?? null,
          certificateNumber: existing?.certificateNumber ?? null,
          certificateRevision: existing?.certificateRevision ?? null,
          publicVerificationToken: existing?.publicVerificationToken ?? null,
          documentHash: existing?.documentHash ?? null,
          qrHost: existing?.qrHost ?? null,
        };

        const saved = existing
          ? await tx.serviceOrder.update({
              where: { id: existing.id },
              data: {
                ...data,
                acceptedAt: resolveAcceptedAtDate(existing, input.workflowStatus, now),
                executionStartedAt: resolveExecutionStartedAtDate(existing, input.workflowStatus, now),
                executedAt: resolveExecutedAtDate(existing, input.workflowStatus, now),
                reviewStartedAt: resolveReviewStartedAtDate(existing, input.workflowStatus, now),
                reviewCompletedAt: resolveReviewCompletedAtDate(
                  existing,
                  existing.reviewDecision as ReviewDecision,
                  input.workflowStatus,
                  now,
                ),
                signatureStartedAt: resolveSignatureStartedAtDate(existing, input.workflowStatus, now),
                emittedAt:
                  input.workflowStatus === "emitted"
                    ? existing.emittedAt ?? now
                    : existing.emittedAt ?? null,
              },
              include: serviceOrderInclude,
            })
          : await tx.serviceOrder.create({
              data: {
                organizationId: input.organizationId,
                ...data,
                acceptedAt: resolveAcceptedAtDate(null, input.workflowStatus, now),
                executionStartedAt: resolveExecutionStartedAtDate(null, input.workflowStatus, now),
                executedAt: resolveExecutedAtDate(null, input.workflowStatus, now),
                reviewStartedAt: resolveReviewStartedAtDate(null, input.workflowStatus, now),
                reviewCompletedAt: resolveReviewCompletedAtDate(null, "pending", input.workflowStatus, now),
                signatureStartedAt: resolveSignatureStartedAtDate(null, input.workflowStatus, now),
                emittedAt: input.workflowStatus === "emitted" ? now : null,
              },
              include: serviceOrderInclude,
            });

        const mapped = mapServiceOrderRecord(saved);
        const auditStore = createPrismaAuditStore(tx, input.organizationId);
        await ensureDerivedAuditEvents(auditStore, mapped);
        return mapped;
      });
    },
    async saveServiceOrderWorkflow(input) {
      return prisma.$transaction(async (tx) => {
        const existing = await tx.serviceOrder.findFirst({
          where: { id: input.serviceOrderId, organizationId: input.organizationId },
          include: serviceOrderInclude,
        });
        if (!existing) {
          throw new Error("service_order_not_found");
        }

        if (input.reviewerUserId) {
          const reviewer = await tx.appUser.findFirst({
            where: { id: input.reviewerUserId, organizationId: input.organizationId, status: "active" },
          });
          if (!reviewer) {
            throw new Error("reviewer_not_found");
          }
        }

        if (input.signatoryUserId) {
          const signatory = await tx.appUser.findFirst({
            where: { id: input.signatoryUserId, organizationId: input.organizationId, status: "active" },
          });
          if (!signatory) {
            throw new Error("signatory_not_found");
          }
        }

        const now = new Date();
        const saved = await tx.serviceOrder.update({
          where: { id: existing.id },
          data: {
            reviewerUserId: input.reviewerUserId ?? existing.reviewerUserId ?? null,
            signatoryUserId: input.signatoryUserId ?? existing.signatoryUserId ?? null,
            workflowStatus: input.workflowStatus,
            reviewDecision: input.reviewDecision,
            reviewDecisionComment: input.reviewDecisionComment.trim(),
            reviewDeviceId: normalizeOptionalString(input.reviewDeviceId) ?? null,
            commentDraft: normalizeOptionalString(input.commentDraft) ?? existing.commentDraft,
            reviewStartedAt: existing.reviewStartedAt ?? now,
            reviewCompletedAt:
              input.reviewDecision === "approved" || input.reviewDecision === "rejected"
                ? existing.reviewCompletedAt ?? now
                : existing.reviewCompletedAt,
            signatureStartedAt:
              input.workflowStatus === "awaiting_signature" || input.workflowStatus === "emitted"
                ? existing.signatureStartedAt ?? now
                : existing.signatureStartedAt,
          },
          include: serviceOrderInclude,
        });

        const mapped = mapServiceOrderRecord(saved);
        const auditStore = createPrismaAuditStore(tx, input.organizationId);
        await ensureDerivedAuditEvents(auditStore, mapped);
        return mapped;
      });
    },
    async emitServiceOrder(input) {
      return prisma.$transaction(async (tx) => {
        const existing = await tx.serviceOrder.findFirst({
          where: { id: input.serviceOrderId, organizationId: input.organizationId },
          include: serviceOrderInclude,
        });
        if (!existing) {
          throw new Error("service_order_not_found");
        }

        const signatoryId = input.signatoryUserId ?? existing.signatoryUserId ?? undefined;
        const signatory = signatoryId
          ? await tx.appUser.findFirst({
              where: { id: signatoryId, organizationId: input.organizationId, status: "active" },
            })
          : null;
        if (!signatory) {
          throw new Error("signatory_not_found");
        }

        const now = input.occurredAt;
        const saved = await tx.serviceOrder.update({
          where: { id: existing.id },
          data: {
            signatoryUserId: signatory.id,
            workflowStatus: "emitted",
            reviewDecision: "approved",
            certificateNumber: input.certificateNumber,
            certificateRevision: input.certificateRevision,
            publicVerificationToken: input.publicVerificationToken,
            documentHash: input.documentHash,
            qrHost: input.qrHost,
            signatureStatement: input.signatureStatement.trim(),
            signatureDeviceId: input.signatureDeviceId.trim(),
            signatureStartedAt: existing.signatureStartedAt ?? now,
            signedAt: existing.signedAt ?? now,
            emittedAt: existing.emittedAt ?? now,
          },
          include: serviceOrderInclude,
        });

        const mapped = mapServiceOrderRecord(saved);
        const auditStore = createPrismaAuditStore(tx, input.organizationId);
        await ensureDerivedAuditEvents(auditStore, mapped);
        await ensureAuditEvent(auditStore, mapped, {
          action: "certificate.signed",
          actorUserId: signatory.id,
          actorLabel: signatory.displayName,
          deviceId: input.signatureDeviceId.trim(),
          certificateNumber: input.certificateNumber,
          entityLabel: input.certificateNumber,
          occurredAtUtc: mapped.signedAtUtc ?? now.toISOString(),
        });
        await ensureAuditEvent(auditStore, mapped, {
          action: "certificate.emitted",
          actorUserId: signatory.id,
          actorLabel: signatory.displayName,
          deviceId: input.signatureDeviceId.trim(),
          certificateNumber: input.certificateNumber,
          entityLabel: input.certificateNumber,
          occurredAtUtc: mapped.emittedAtUtc ?? now.toISOString(),
        });

        return mapped;
      });
    },
  };
}

const GENESIS_HASH = "0".repeat(64);

const serviceOrderInclude = {
  customer: true,
  equipment: true,
  procedure: true,
  primaryStandard: true,
  executorUser: true,
  reviewerUser: true,
  signatoryUser: true,
} as const;

async function ensureDerivedAuditEvents(
  auditStore: MutableAuditEventStore,
  record: PersistedServiceOrderRecord,
) {
  if (
    (record.workflowStatus === "awaiting_review" ||
      record.workflowStatus === "awaiting_signature" ||
      record.workflowStatus === "emitted") &&
    record.executedAtUtc
  ) {
    await ensureAuditEvent(auditStore, record, {
      action: "calibration.executed",
      actorUserId: record.executorUserId,
      actorLabel: record.executorName,
      entityLabel: record.workOrderNumber,
      occurredAtUtc: record.executedAtUtc,
    });
  }

  if (
    (record.reviewDecision === "approved" || record.workflowStatus === "awaiting_signature" || record.workflowStatus === "emitted") &&
    record.reviewCompletedAtUtc &&
    record.reviewerUserId &&
    record.reviewerName
  ) {
    await ensureAuditEvent(auditStore, record, {
      action: "technical_review.completed",
      actorUserId: record.reviewerUserId,
      actorLabel: record.reviewerName,
      deviceId: record.reviewDeviceId,
      entityLabel: record.workOrderNumber,
      occurredAtUtc: record.reviewCompletedAtUtc,
    });
  }

  if (record.reviewDecision === "rejected" && record.reviewCompletedAtUtc && record.reviewerName) {
    await ensureAuditEvent(auditStore, record, {
      action: "technical_review.rejected",
      actorUserId: record.reviewerUserId,
      actorLabel: record.reviewerName,
      deviceId: record.reviewDeviceId,
      entityLabel: record.workOrderNumber,
      occurredAtUtc: record.reviewCompletedAtUtc,
    });
  }
}

async function ensureAuditEvent(
  auditStore: MutableAuditEventStore,
  record: PersistedServiceOrderRecord,
  input: {
    action: string;
    actorUserId?: string;
    actorLabel: string;
    entityLabel: string;
    deviceId?: string;
    certificateNumber?: string;
    occurredAtUtc: string;
  },
) {
  const existing = await auditStore.listByServiceOrder(record.serviceOrderId);
  if (existing.some((event) => event.action === input.action)) {
    return;
  }

  await auditStore.append({
    organizationId: record.organizationId,
    serviceOrderId: record.serviceOrderId,
    workOrderNumber: record.workOrderNumber,
    actorUserId: input.actorUserId,
    actorLabel: input.actorLabel,
    action: input.action,
    entityLabel: input.entityLabel,
    deviceId: input.deviceId,
    certificateNumber: input.certificateNumber,
    occurredAtUtc: input.occurredAtUtc,
  });
}

function createPrismaAuditStore(
  tx: Omit<
    PrismaClient,
    "$connect" | "$disconnect" | "$on" | "$transaction" | "$use" | "$extends"
  >,
  organizationId: string,
): MutableAuditEventStore {
  return {
    async listByServiceOrder(serviceOrderId) {
      const records = await tx.emissionAuditEvent.findMany({
        where: { organizationId, serviceOrderId },
        include: {
          serviceOrder: {
            select: {
              workOrderNumber: true,
            },
          },
        },
        orderBy: [{ occurredAt: "asc" }, { createdAt: "asc" }],
      });

      return records.map((record) => ({
        eventId: record.id,
        organizationId: record.organizationId,
        serviceOrderId: record.serviceOrderId,
        workOrderNumber: record.serviceOrder.workOrderNumber,
        actorUserId: record.actorUserId ?? undefined,
        actorLabel: record.actorLabel,
        action: record.action,
        entityLabel: record.entityLabel,
        deviceId: record.deviceId ?? undefined,
        certificateNumber: record.certificateNumber ?? undefined,
        prevHash: record.prevHash,
        hash: record.hash,
        occurredAtUtc: record.occurredAt.toISOString(),
      }));
    },
    async append(input) {
      const existing = await tx.emissionAuditEvent.findMany({
        where: { organizationId, serviceOrderId: input.serviceOrderId },
        orderBy: [{ occurredAt: "asc" }, { createdAt: "asc" }],
      });
      const prevHash = existing.at(-1)?.hash ?? GENESIS_HASH;
      const hash = computeAuditHash(prevHash, buildAuditPayload(input));
      const created = await tx.emissionAuditEvent.create({
        data: {
          organizationId,
          serviceOrderId: input.serviceOrderId,
          actorUserId: input.actorUserId ?? null,
          action: input.action,
          actorLabel: input.actorLabel,
          entityLabel: input.entityLabel,
          deviceId: input.deviceId ?? null,
          certificateNumber: input.certificateNumber ?? null,
          prevHash,
          hash,
          occurredAt: new Date(input.occurredAtUtc),
        },
      });

      return {
        eventId: created.id,
        organizationId,
        serviceOrderId: input.serviceOrderId,
        workOrderNumber: input.workOrderNumber,
        actorUserId: created.actorUserId ?? undefined,
        actorLabel: created.actorLabel,
        action: created.action,
        entityLabel: created.entityLabel,
        deviceId: created.deviceId ?? undefined,
        certificateNumber: created.certificateNumber ?? undefined,
        prevHash: created.prevHash,
        hash: created.hash,
        occurredAtUtc: created.occurredAt.toISOString(),
      };
    },
  };
}

function buildAuditPayload(input: {
  serviceOrderId: string;
  action: string;
  actorUserId?: string;
  actorLabel: string;
  entityLabel: string;
  deviceId?: string;
  certificateNumber?: string;
  occurredAtUtc: string;
}) {
  return {
    action: input.action,
    actorId: input.actorUserId,
    actorLabel: input.actorLabel,
    certificateId: input.serviceOrderId,
    certificateNumber: input.certificateNumber,
    entityLabel: input.entityLabel,
    timestampUtc: input.occurredAtUtc,
    deviceId: input.deviceId,
  };
}

function compareAuditEventsAsc(left: PersistedEmissionAuditEvent, right: PersistedEmissionAuditEvent) {
  if (left.occurredAtUtc !== right.occurredAtUtc) {
    return left.occurredAtUtc.localeCompare(right.occurredAtUtc);
  }

  return left.eventId.localeCompare(right.eventId);
}

function compareAuditEventsDesc(left: PersistedEmissionAuditEvent, right: PersistedEmissionAuditEvent) {
  return compareAuditEventsAsc(right, left);
}

function resolveMemoryReferences(input: {
  input: SaveServiceOrderInput;
  organizationId: string;
  customers: Map<string, ServiceOrderReferenceCustomer>;
  equipment: Map<string, ServiceOrderReferenceEquipment>;
  procedures: Map<string, ServiceOrderReferenceProcedure>;
  standards: Map<string, ServiceOrderReferenceStandard>;
  users: Map<string, ServiceOrderReferenceUser>;
}) {
  const customer = requireReference(
    input.customers.get(input.input.customerId),
    "customer_not_found",
    input.organizationId,
  );
  const equipment = requireReference(
    input.equipment.get(input.input.equipmentId),
    "equipment_not_found",
    input.organizationId,
  );
  const procedure = requireReference(
    input.procedures.get(input.input.procedureId),
    "procedure_not_found",
    input.organizationId,
  );
  const standard = requireReference(
    input.standards.get(input.input.primaryStandardId),
    "standard_not_found",
    input.organizationId,
  );
  const executor = requireActiveUser(
    input.users.get(input.input.executorUserId),
    input.organizationId,
    "executor_not_found",
  );
  const reviewer = input.input.reviewerUserId
    ? requireActiveUser(input.users.get(input.input.reviewerUserId), input.organizationId, "reviewer_not_found")
    : undefined;
  const signatory = input.input.signatoryUserId
    ? requireActiveUser(input.users.get(input.input.signatoryUserId), input.organizationId, "signatory_not_found")
    : undefined;

  validateServiceOrderReferences({
    customerId: input.input.customerId,
    equipment,
    procedureId: input.input.procedureId,
    primaryStandardId: input.input.primaryStandardId,
  });

  if (!standard.hasValidCertificate) {
    throw new Error("standard_certificate_invalid");
  }

  return { customer, equipment, procedure, standard, executor, reviewer, signatory };
}

async function resolvePrismaReferences(
  tx: Omit<
    PrismaClient,
    "$connect" | "$disconnect" | "$on" | "$transaction" | "$use" | "$extends"
  >,
  input: SaveServiceOrderInput,
) {
  const [customer, equipment, procedure, standard, executor, reviewer, signatory] = await Promise.all([
    tx.customer.findFirst({
      where: { id: input.customerId, organizationId: input.organizationId, archivedAt: null },
    }),
    tx.equipment.findFirst({
      where: { id: input.equipmentId, organizationId: input.organizationId, archivedAt: null },
    }),
    tx.procedureRevision.findFirst({
      where: { id: input.procedureId, organizationId: input.organizationId, archivedAt: null },
    }),
    tx.standard.findFirst({
      where: { id: input.primaryStandardId, organizationId: input.organizationId, archivedAt: null },
    }),
    tx.appUser.findFirst({
      where: { id: input.executorUserId, organizationId: input.organizationId, status: "active" },
    }),
    input.reviewerUserId
      ? tx.appUser.findFirst({
          where: { id: input.reviewerUserId, organizationId: input.organizationId, status: "active" },
        })
      : Promise.resolve(null),
    input.signatoryUserId
      ? tx.appUser.findFirst({
          where: { id: input.signatoryUserId, organizationId: input.organizationId, status: "active" },
        })
      : Promise.resolve(null),
  ]);

  if (!customer) {
    throw new Error("customer_not_found");
  }
  if (!equipment) {
    throw new Error("equipment_not_found");
  }
  if (!procedure) {
    throw new Error("procedure_not_found");
  }
  if (!standard) {
    throw new Error("standard_not_found");
  }
  if (!executor) {
    throw new Error("executor_not_found");
  }
  if (input.reviewerUserId && !reviewer) {
    throw new Error("reviewer_not_found");
  }
  if (input.signatoryUserId && !signatory) {
    throw new Error("signatory_not_found");
  }

  validateServiceOrderReferences({
    customerId: input.customerId,
    equipment: {
      equipmentId: equipment.id,
      organizationId: equipment.organizationId,
      customerId: equipment.customerId,
      procedureId: equipment.procedureId ?? undefined,
      primaryStandardId: equipment.primaryStandardId ?? undefined,
      code: equipment.code,
      tagCode: equipment.tagCode,
      serialNumber: equipment.serialNumber,
      typeModelLabel: equipment.typeModelLabel,
    },
    procedureId: input.procedureId,
    primaryStandardId: input.primaryStandardId,
  });

  if (!standard.hasValidCertificate) {
    throw new Error("standard_certificate_invalid");
  }

  return { customer, equipment, procedure, standard, executor, reviewer, signatory };
}

function mapServiceOrderRecord(record: {
  id: string;
  organizationId: string;
  customerId: string;
  equipmentId: string;
  procedureId: string;
  primaryStandardId: string;
  executorUserId: string;
  reviewerUserId: string | null;
  signatoryUserId: string | null;
  workOrderNumber: string;
  workflowStatus: string;
  environmentLabel: string;
  curvePointsLabel: string;
  evidenceLabel: string;
  uncertaintyLabel: string;
  conformityLabel: string;
  measurementResultValue: number | null;
  measurementExpandedUncertaintyValue: number | null;
  measurementCoverageFactor: number | null;
  measurementUnit: string | null;
  decisionRuleLabel: string | null;
  decisionOutcomeLabel: string | null;
  freeTextStatement: string | null;
  commentDraft: string;
  reviewDecision: string;
  reviewDecisionComment: string;
  reviewDeviceId: string | null;
  signatureDeviceId: string | null;
  signatureStatement: string | null;
  certificateNumber: string | null;
  certificateRevision: string | null;
  publicVerificationToken: string | null;
  documentHash: string | null;
  qrHost: string | null;
  createdAt: Date;
  acceptedAt: Date | null;
  executionStartedAt: Date | null;
  executedAt: Date | null;
  reviewStartedAt: Date | null;
  reviewCompletedAt: Date | null;
  signatureStartedAt: Date | null;
  signedAt: Date | null;
  emittedAt: Date | null;
  updatedAt: Date;
  archivedAt: Date | null;
  customer: {
    tradeName: string;
    addressLine1: string;
    addressCity: string;
    addressState: string;
    addressPostalCode: string | null;
    addressCountry: string;
  };
  equipment: {
    code: string;
    tagCode: string;
    serialNumber: string;
    typeModelLabel: string;
  };
  procedure: { code: string; revisionLabel: string };
  primaryStandard: {
    code: string;
    title: string;
    sourceLabel: string;
    certificateLabel: string;
    hasValidCertificate: boolean;
    certificateValidUntil: Date | null;
    measurementValue: { toString(): string };
    applicableRangeMin: { toString(): string };
    applicableRangeMax: { toString(): string };
  };
  executorUser: { displayName: string };
  reviewerUser: { displayName: string } | null;
  signatoryUser: { displayName: string } | null;
}): PersistedServiceOrderRecord {
  return {
    serviceOrderId: record.id,
    organizationId: record.organizationId,
    customerId: record.customerId,
    customerName: record.customer.tradeName,
    customerAddress: {
      line1: record.customer.addressLine1,
      city: record.customer.addressCity,
      state: record.customer.addressState,
      postalCode: record.customer.addressPostalCode ?? undefined,
      country: record.customer.addressCountry,
    },
    equipmentId: record.equipmentId,
    equipmentLabel: `${record.equipment.code} · ${record.equipment.typeModelLabel}`,
    equipmentCode: record.equipment.code,
    equipmentTagCode: record.equipment.tagCode,
    equipmentSerialNumber: record.equipment.serialNumber,
    instrumentType: inferInstrumentType(record.equipment.typeModelLabel),
    procedureId: record.procedureId,
    procedureLabel: `${record.procedure.code} rev.${record.procedure.revisionLabel}`,
    primaryStandardId: record.primaryStandardId,
    standardsLabel: `${record.primaryStandard.code} · ${record.primaryStandard.title}`,
    standardSource: mapStandardSource(record.primaryStandard.sourceLabel),
    standardCertificateReference: record.primaryStandard.certificateLabel,
    standardHasValidCertificate: record.primaryStandard.hasValidCertificate,
    standardCertificateValidUntilUtc: record.primaryStandard.certificateValidUntil?.toISOString(),
    standardMeasurementValue: Number(record.primaryStandard.measurementValue.toString()),
    standardApplicableRange: {
      minimum: Number(record.primaryStandard.applicableRangeMin.toString()),
      maximum: Number(record.primaryStandard.applicableRangeMax.toString()),
    },
    executorUserId: record.executorUserId,
    executorName: record.executorUser.displayName,
    reviewerUserId: record.reviewerUserId ?? undefined,
    reviewerName: record.reviewerUser?.displayName,
    signatoryUserId: record.signatoryUserId ?? undefined,
    signatoryName: record.signatoryUser?.displayName,
    workOrderNumber: record.workOrderNumber,
    workflowStatus: record.workflowStatus as ServiceOrderListItemStatus,
    environmentLabel: record.environmentLabel,
    curvePointsLabel: record.curvePointsLabel,
    evidenceLabel: record.evidenceLabel,
    uncertaintyLabel: record.uncertaintyLabel,
    conformityLabel: record.conformityLabel,
    measurementResultValue: record.measurementResultValue ?? undefined,
    measurementExpandedUncertaintyValue:
      record.measurementExpandedUncertaintyValue ?? undefined,
    measurementCoverageFactor: record.measurementCoverageFactor ?? undefined,
    measurementUnit: record.measurementUnit ?? undefined,
    decisionRuleLabel: record.decisionRuleLabel ?? undefined,
    decisionOutcomeLabel: record.decisionOutcomeLabel ?? undefined,
    freeTextStatement: record.freeTextStatement ?? undefined,
    commentDraft: record.commentDraft,
    reviewDecision: parseReviewDecision(record.reviewDecision),
    reviewDecisionComment: record.reviewDecisionComment,
    reviewDeviceId: record.reviewDeviceId ?? undefined,
    signatureDeviceId: record.signatureDeviceId ?? undefined,
    signatureStatement: record.signatureStatement ?? undefined,
    certificateNumber: record.certificateNumber ?? undefined,
    certificateRevision: record.certificateRevision ?? undefined,
    publicVerificationToken: record.publicVerificationToken ?? undefined,
    documentHash: record.documentHash ?? undefined,
    qrHost: record.qrHost ?? undefined,
    createdAtUtc: record.createdAt.toISOString(),
    acceptedAtUtc: record.acceptedAt?.toISOString(),
    executionStartedAtUtc: record.executionStartedAt?.toISOString(),
    executedAtUtc: record.executedAt?.toISOString(),
    reviewStartedAtUtc: record.reviewStartedAt?.toISOString(),
    reviewCompletedAtUtc: record.reviewCompletedAt?.toISOString(),
    signatureStartedAtUtc: record.signatureStartedAt?.toISOString(),
    signedAtUtc: record.signedAt?.toISOString(),
    emittedAtUtc: record.emittedAt?.toISOString(),
    updatedAtUtc: record.updatedAt.toISOString(),
    archivedAtUtc: record.archivedAt?.toISOString(),
  };
}

function parseReviewDecision(value: string): ReviewDecision {
  if (value === "approved" || value === "rejected") {
    return value;
  }

  return "pending";
}

function requireReference<T extends { organizationId: string }>(
  value: T | undefined,
  message: string,
  organizationId: string,
) {
  if (!value || value.organizationId !== organizationId) {
    throw new Error(message);
  }

  return value;
}

function requireActiveUser(
  value: ServiceOrderReferenceUser | undefined,
  organizationId: string,
  message: string,
) {
  if (!value || value.organizationId !== organizationId || value.status !== "active") {
    throw new Error(message);
  }

  return value;
}

function validateServiceOrderReferences(input: {
  customerId: string;
  equipment: ServiceOrderReferenceEquipment;
  procedureId: string;
  primaryStandardId: string;
}) {
  if (input.equipment.customerId !== input.customerId) {
    throw new Error("equipment_customer_mismatch");
  }

  if (input.equipment.procedureId && input.equipment.procedureId !== input.procedureId) {
    throw new Error("equipment_procedure_mismatch");
  }

  if (
    input.equipment.primaryStandardId &&
    input.equipment.primaryStandardId !== input.primaryStandardId
  ) {
    throw new Error("equipment_standard_mismatch");
  }
}

function resolveAcceptedAtUtc(
  existing: PersistedServiceOrderRecord | undefined,
  _workflowStatus: ServiceOrderListItemStatus,
  nowUtc: string,
) {
  return existing?.acceptedAtUtc ?? nowUtc;
}

function resolveExecutionStartedAtUtc(
  existing: PersistedServiceOrderRecord | undefined,
  workflowStatus: ServiceOrderListItemStatus,
  nowUtc: string,
) {
  return existing?.executionStartedAtUtc ??
    (workflowStatus === "in_execution" ||
    workflowStatus === "awaiting_review" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted" ||
    workflowStatus === "blocked"
      ? nowUtc
      : undefined);
}

function resolveExecutedAtUtc(
  existing: PersistedServiceOrderRecord | undefined,
  workflowStatus: ServiceOrderListItemStatus,
  nowUtc: string,
) {
  return existing?.executedAtUtc ??
    (workflowStatus === "awaiting_review" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted" ||
    workflowStatus === "blocked"
      ? nowUtc
      : undefined);
}

function resolveReviewStartedAtUtc(
  existing: PersistedServiceOrderRecord | undefined,
  workflowStatus: ServiceOrderListItemStatus,
  nowUtc: string,
) {
  return existing?.reviewStartedAtUtc ??
    (workflowStatus === "awaiting_review" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted" ||
    workflowStatus === "blocked"
      ? nowUtc
      : undefined);
}

function resolveReviewCompletedAtUtc(
  existing: PersistedServiceOrderRecord | undefined,
  reviewDecision: ReviewDecision,
  workflowStatus: ServiceOrderListItemStatus,
  nowUtc: string,
) {
  return existing?.reviewCompletedAtUtc ??
    (reviewDecision === "approved" ||
    reviewDecision === "rejected" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted"
      ? nowUtc
      : undefined);
}

function resolveSignatureStartedAtUtc(
  existing: PersistedServiceOrderRecord | undefined,
  workflowStatus: ServiceOrderListItemStatus,
  nowUtc: string,
) {
  return existing?.signatureStartedAtUtc ??
    (workflowStatus === "awaiting_signature" || workflowStatus === "emitted" ? nowUtc : undefined);
}

function resolveAcceptedAtDate(
  existing: { acceptedAt: Date | null } | null,
  _workflowStatus: ServiceOrderListItemStatus,
  now: Date,
) {
  return existing?.acceptedAt ?? now;
}

function resolveExecutionStartedAtDate(
  existing: { executionStartedAt: Date | null } | null,
  workflowStatus: ServiceOrderListItemStatus,
  now: Date,
) {
  return existing?.executionStartedAt ??
    (workflowStatus === "in_execution" ||
    workflowStatus === "awaiting_review" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted" ||
    workflowStatus === "blocked"
      ? now
      : null);
}

function resolveExecutedAtDate(
  existing: { executedAt: Date | null } | null,
  workflowStatus: ServiceOrderListItemStatus,
  now: Date,
) {
  return existing?.executedAt ??
    (workflowStatus === "awaiting_review" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted" ||
    workflowStatus === "blocked"
      ? now
      : null);
}

function resolveReviewStartedAtDate(
  existing: { reviewStartedAt: Date | null } | null,
  workflowStatus: ServiceOrderListItemStatus,
  now: Date,
) {
  return existing?.reviewStartedAt ??
    (workflowStatus === "awaiting_review" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted" ||
    workflowStatus === "blocked"
      ? now
      : null);
}

function resolveReviewCompletedAtDate(
  existing: { reviewCompletedAt: Date | null } | null,
  reviewDecision: ReviewDecision,
  workflowStatus: ServiceOrderListItemStatus,
  now: Date,
) {
  return existing?.reviewCompletedAt ??
    (reviewDecision === "approved" ||
    reviewDecision === "rejected" ||
    workflowStatus === "awaiting_signature" ||
    workflowStatus === "emitted"
      ? now
      : null);
}

function resolveSignatureStartedAtDate(
  existing: { signatureStartedAt: Date | null } | null,
  workflowStatus: ServiceOrderListItemStatus,
  now: Date,
) {
  return existing?.signatureStartedAt ??
    (workflowStatus === "awaiting_signature" || workflowStatus === "emitted" ? now : null);
}

function inferInstrumentType(typeModelLabel: string) {
  const normalized = typeModelLabel.toLowerCase();
  if (normalized.includes("balanca") || normalized.includes("nawi")) {
    return "balanca";
  }
  if (normalized.includes("term")) {
    return "termometro";
  }

  return normalized.replace(/\s+/g, "_");
}

function mapStandardSource(sourceLabel: string): "INM" | "RBC" | "ILAC_MRA" {
  const normalized = sourceLabel.toUpperCase();
  if (normalized.includes("ILAC")) {
    return "ILAC_MRA";
  }
  if (normalized.includes("INM")) {
    return "INM";
  }

  return "RBC";
}

function normalizeOptionalString(value: string | undefined | null) {
  const normalized = value?.trim();
  return normalized ? normalized : undefined;
}
