import { Prisma } from "@prisma/client";
import { computeAuditHash } from "@afere/audit-log";

import type { Env } from "../../config/env.js";
import { hashPassword } from "../../domain/auth/password.js";
import { RuntimeReadinessError, type RuntimeReadiness } from "../../infra/runtime-readiness.js";
import type { MembershipRole } from "@afere/contracts";

export const TEST_ENV: Env = {
  NODE_ENV: "test",
  LOG_LEVEL: "fatal",
  HOST: "127.0.0.1",
  PORT: 3000,
  CORS_ORIGINS: [],
  DATABASE_URL: "postgresql://afere:afere@localhost:5432/afere?schema=public",
  REDIS_URL: "redis://localhost:6379",
  ALLOW_SCENARIO_ROUTES: true,
  RATE_LIMIT_MAX: 100,
  RATE_LIMIT_WINDOW_MS: 60000,
  COOKIE_SECRET: "test-cookie-secret-32-chars-long-ok",
  REDIRECT_ALLOWLIST: [
    "/auth/login",
    "/auth/logout",
    "/onboarding",
    "/emission/workspace",
    "/emission/review-signature",
    "/emission/signature-queue",
    "/dashboard",
  ],
};

export function createRuntimeReadinessStub(
  options: { postgresReason?: string; redisReason?: string } = {},
): { runtimeReadiness: RuntimeReadiness; wasClosed: () => boolean } {
  let closed = false;
  return {
    runtimeReadiness: {
      probes: [
        {
          name: "postgres",
          async check() {
            if (options.postgresReason) {
              throw new RuntimeReadinessError("postgres", options.postgresReason);
            }
          },
        },
        {
          name: "redis",
          async check() {
            if (options.redisReason) {
              throw new RuntimeReadinessError("redis", options.redisReason);
            }
          },
        },
      ],
      async close() {
        closed = true;
      },
    },
    wasClosed: () => closed,
  };
}

export function normalizeCookieHeader(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.split(";")[0] ?? "";
  }
  return value?.split(";")[0] ?? "";
}

export function createV1MemorySeed() {
  return {
    users: [
      {
        userId: "user-admin-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "admin@afere.local",
        passwordHash: hashPassword("Afere@2026!", "seed-admin"),
        displayName: "Ana Administradora",
        roles: ["admin", "quality_manager"] as MembershipRole[],
        status: "active" as const,
        teamName: "Gestao tecnica",
        mfaEnforced: true,
        mfaEnrolled: true,
        deviceCount: 2,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Gestao",
            status: "authorized" as const,
            validUntilUtc: "2027-01-01T00:00:00.000Z",
          },
        ],
      },
      {
        userId: "user-reviewer-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "revisora@afere.local",
        passwordHash: hashPassword("Afere@2026!", "seed-reviewer"),
        displayName: "Renata Revisora",
        roles: ["technical_reviewer"] as MembershipRole[],
        status: "active" as const,
        teamName: "Qualidade",
        mfaEnforced: true,
        mfaEnrolled: true,
        deviceCount: 1,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Revisora tecnica",
            status: "authorized" as const,
            validUntilUtc: "2027-03-01T00:00:00.000Z",
          },
        ],
      },
      {
        userId: "user-signatory-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "signatario@afere.local",
        passwordHash: hashPassword("Afere@2026!", "seed-signatory"),
        displayName: "Bruno Signatario",
        roles: ["signatory", "technical_reviewer"] as MembershipRole[],
        status: "active" as const,
        teamName: "Metrologia",
        mfaEnforced: true,
        mfaEnrolled: true,
        deviceCount: 1,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Signatario",
            status: "authorized" as const,
            validUntilUtc: "2027-02-01T00:00:00.000Z",
          },
        ],
      },
    ],
    onboarding: [
      {
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        regulatoryProfile: "type_b",
        normativePackageVersion: "2026-04-20-baseline-v0.1.0",
        startedAtUtc: "2026-04-23T12:00:00.000Z",
        organizationProfileCompleted: true,
        primarySignatoryReady: false,
        certificateNumberingConfigured: false,
        scopeReviewCompleted: false,
        publicQrConfigured: false,
      },
    ],
  };
}

export function createV2RegistrySeed() {
  return {
    customers: [
      {
        customerId: "customer-001",
        organizationId: "org-1",
        legalName: "Lab. Acme Analises Ltda.",
        tradeName: "Lab. Acme",
        documentLabel: "12.345.678/0001-XX",
        segmentLabel: "Laboratorio clinico",
        accountOwnerName: "Joao das Neves",
        accountOwnerEmail: "joao@lab-acme.com.br",
        contractLabel: "Contrato vigente ate 31/12/2026",
        specialConditionsLabel: "Sala climatizada 21 +/- 2 C",
        contactName: "Joao das Neves",
        contactRoleLabel: "Responsavel tecnico",
        contactEmail: "joao@lab-acme.com.br",
        contactPhoneLabel: "(65) 99999-0001",
        addressLine1: "Rua da Calibracao, 100",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-000",
        addressCountry: "Brasil",
        addressConditionsLabel: "Acesso controlado",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    standards: [
      {
        standardId: "standard-001",
        organizationId: "org-1",
        code: "PESO-001",
        title: "Peso padrao 1 kg",
        kindLabel: "Peso",
        nominalClassLabel: "1 kg · F1",
        sourceLabel: "RBC-1234",
        certificateLabel: "1234/25/081",
        manufacturerLabel: "Coelmatic",
        modelLabel: "M1K",
        serialNumberLabel: "9-22-101",
        nominalValueLabel: "1,000 kg",
        classLabel: "F1",
        usageRangeLabel: "0 kg ate 1 kg",
        measurementValue: 1,
        applicableRangeMin: 0,
        applicableRangeMax: 1,
        uncertaintyLabel: "+/- 8 mg",
        correctionFactorLabel: "+0,001 g",
        hasValidCertificate: true,
        certificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
        calibrations: [
          {
            calibratedAtUtc: "2025-08-12T00:00:00.000Z",
            laboratoryLabel: "Lab Cal-1234",
            certificateLabel: "1234/25/081",
            sourceLabel: "RBC",
            uncertaintyLabel: "+/- 8 mg",
            validUntilUtc: "2026-08-12T00:00:00.000Z",
          },
        ],
      },
    ],
    procedures: [
      {
        procedureId: "procedure-001",
        organizationId: "org-1",
        code: "PT-005",
        title: "Calibracao IPNA classe III campo",
        typeLabel: "NAWI III",
        revisionLabel: "04",
        effectiveSinceUtc: "2026-03-01T00:00:00.000Z",
        lifecycleLabel: "Vigente",
        usageLabel: "Campo controlado",
        scopeLabel: "Balancas IPNA classe III ate 300 kg.",
        environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
        curvePolicyLabel: "5 pontos com subida e descida",
        standardsPolicyLabel: "Peso F1 ou M1 vigente",
        approvalLabel: "Aprovado por Ana Administradora",
        relatedDocuments: ["IT-005", "FR-021"],
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    equipment: [
      {
        equipmentId: "equipment-001",
        organizationId: "org-1",
        customerId: "customer-001",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-0007",
        tagCode: "BAL-007",
        serialNumber: "SN-300-01",
        typeModelLabel: "NAWI Toledo Prix 3",
        capacityClassLabel: "300 kg · 0,05 kg · III",
        supportingStandardCodes: ["PESO-001"],
        addressLine1: "Rua da Calibracao, 100",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-000",
        addressCountry: "Brasil",
        addressConditionsLabel: "Sala climatizada",
        lastCalibrationAtUtc: "2026-04-18T00:00:00.000Z",
        nextCalibrationAtUtc: "2026-10-18T00:00:00.000Z",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    auditEvents: [
      {
        entityType: "customer" as const,
        entityId: "customer-001",
        action: "update",
        summary: "Cadastro do cliente Lab. Acme revisado na V2.",
        createdAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
  };
}

export function createV3CoreSeed() {
  const seed = createV1MemorySeed();
  return {
    ...seed,
    onboarding: seed.onboarding.map((record) => ({
      ...record,
      primarySignatoryReady: true,
      certificateNumberingConfigured: true,
      scopeReviewCompleted: true,
      publicQrConfigured: true,
    })),
  };
}

export function createV3ServiceOrderSeed() {
  return {
    users: [
      { userId: "user-admin-1", organizationId: "org-1", displayName: "Ana Administradora", status: "active" as const },
      { userId: "user-reviewer-1", organizationId: "org-1", displayName: "Renata Revisora", status: "active" as const },
      { userId: "user-signatory-1", organizationId: "org-1", displayName: "Bruno Signatario", status: "active" as const },
    ],
    customers: [
      {
        customerId: "customer-001",
        organizationId: "org-1",
        tradeName: "Lab. Acme",
        addressLine1: "Rua da Calibracao, 100",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-000",
        addressCountry: "Brasil",
      },
    ],
    equipment: [
      {
        equipmentId: "equipment-001",
        organizationId: "org-1",
        customerId: "customer-001",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-0007",
        tagCode: "BAL-007",
        serialNumber: "SN-300-01",
        typeModelLabel: "NAWI Toledo Prix 3",
        metrologyProfile: buildEquipmentMetrologyProfileFixture({
          instrumentKind: "nawi",
          maximumCapacityValue: 300,
          readabilityValue: 0.05,
          verificationScaleIntervalValue: 0.05,
          normativeClass: "iii",
          effectiveRangeMaxValue: 300,
        }),
      },
    ],
    procedures: [
      { procedureId: "procedure-001", organizationId: "org-1", code: "PT-005", revisionLabel: "04" },
    ],
    standards: [
      {
        standardId: "standard-001",
        organizationId: "org-1",
        code: "PESO-001",
        title: "Peso padrao 1 kg",
        sourceLabel: "RBC-1234",
        certificateLabel: "1234/25/081",
        hasValidCertificate: true,
        certificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        measurementValue: 1,
        applicableRangeMin: 0,
        applicableRangeMax: 1,
        metrologyProfile: buildStandardMetrologyProfileFixture({
          expandedUncertaintyValue: 0.000008,
          conventionalMassErrorValue: 0.000001,
        }),
      },
    ],
    serviceOrders: [
      {
        serviceOrderId: "service-order-00142",
        organizationId: "org-1",
        customerId: "customer-001",
        customerName: "Lab. Acme",
        customerAddress: {
          line1: "Rua da Calibracao, 100",
          city: "Cuiaba",
          state: "MT",
          postalCode: "78000-000",
          country: "Brasil",
        },
        equipmentId: "equipment-001",
        equipmentLabel: "EQ-0007 · NAWI Toledo Prix 3",
        equipmentCode: "EQ-0007",
        equipmentTagCode: "BAL-007",
        equipmentSerialNumber: "SN-300-01",
        instrumentType: "balanca",
        procedureId: "procedure-001",
        procedureLabel: "PT-005 rev.04",
        primaryStandardId: "standard-001",
        standardsLabel: "PESO-001 · Peso padrao 1 kg",
        equipmentMetrologySnapshot: buildEquipmentMetrologyProfileFixture({
          instrumentKind: "nawi",
          maximumCapacityValue: 300,
          readabilityValue: 0.05,
          verificationScaleIntervalValue: 0.05,
          normativeClass: "iii",
          effectiveRangeMaxValue: 300,
        }),
        standardMetrologySnapshot: buildStandardMetrologyProfileFixture({
          expandedUncertaintyValue: 0.000008,
          conventionalMassErrorValue: 0.000001,
        }),
        standardSource: "RBC" as const,
        standardCertificateReference: "1234/25/081",
        standardHasValidCertificate: true,
        standardCertificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        standardMeasurementValue: 1,
        standardApplicableRange: { minimum: 0, maximum: 1 },
        executorUserId: "user-admin-1",
        executorName: "Ana Administradora",
        reviewerUserId: "user-reviewer-1",
        reviewerName: "Renata Revisora",
        signatoryUserId: "user-signatory-1",
        signatoryName: "Bruno Signatario",
        workOrderNumber: "OS-2026-00142",
        workflowStatus: "awaiting_review" as const,
        environmentLabel: "22,1 C · 48% UR · pressao estavel",
        curvePointsLabel: "5 pontos (10% / 25% / 50% / 75% / 100%)",
        evidenceLabel: "12 evidencias anexadas",
        uncertaintyLabel: "U = 0,12 kg (k=2)",
        conformityLabel: "Aprovado com banda de guarda de 50%",
        measurementResultValue: 152.48,
        measurementExpandedUncertaintyValue: 0.12,
        measurementCoverageFactor: 2,
        measurementUnit: "kg",
        measurementRawData: buildMeasurementRawDataFixture("kg", 15),
        decisionRuleLabel: "ILAC G8 com banda de guarda",
        decisionOutcomeLabel: "Conforme",
        freeTextStatement: "Resultado dentro da faixa operacional declarada.",
        commentDraft: "Curva coerente com o historico do equipamento e pronta para revisao tecnica.",
        reviewDecision: "pending" as const,
        reviewDecisionComment: "",
        createdAtUtc: "2026-04-12T12:01:00.000Z",
        acceptedAtUtc: "2026-04-12T12:15:00.000Z",
        executionStartedAtUtc: "2026-04-19T14:00:00.000Z",
        executedAtUtc: "2026-04-19T17:22:00.000Z",
        reviewStartedAtUtc: "2026-04-23T11:30:00.000Z",
        updatedAtUtc: "2026-04-23T11:30:00.000Z",
      },
    ],
  };
}

export function createV4CoreSeed() {
  const seed = createV3CoreSeed();
  return {
    ...seed,
    users: [
      ...seed.users,
      {
        userId: "user-external-client-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "marcia@paodoce.com.br",
        passwordHash: hashPassword("Afere@2026!", "seed-external-client"),
        displayName: "Marcia Lima",
        roles: ["external_client"] as MembershipRole[],
        status: "active" as const,
        teamName: "Cliente",
        mfaEnforced: false,
        mfaEnrolled: false,
        deviceCount: 1,
        competencies: [],
      },
    ],
  };
}

export function createV4RegistrySeed() {
  const seed = createV2RegistrySeed();
  return {
    ...seed,
    customers: [
      ...seed.customers,
      {
        customerId: "customer-002",
        organizationId: "org-1",
        legalName: "Padaria Pao Doce Comercio Ltda.",
        tradeName: "Padaria Pao Doce",
        documentLabel: "23.456.789/0001-YY",
        segmentLabel: "Panificacao",
        accountOwnerName: "Marcia Lima",
        accountOwnerEmail: "marcia@paodoce.com.br",
        contractLabel: "Contrato vigente ate 30/11/2026",
        specialConditionsLabel: "Atendimento antes da abertura da loja",
        contactName: "Marcia Lima",
        contactRoleLabel: "Responsavel administrativa",
        contactEmail: "marcia@paodoce.com.br",
        contactPhoneLabel: "(65) 99999-1101",
        addressLine1: "Avenida do Comercio, 45",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78005-010",
        addressCountry: "Brasil",
        addressConditionsLabel: "Atendimento antes das 6h para nao interromper a producao.",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    equipment: [
      ...seed.equipment,
      {
        equipmentId: "equipment-00141",
        organizationId: "org-1",
        customerId: "customer-002",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-00141",
        tagCode: "BAL-141",
        serialNumber: "SN-141-02",
        typeModelLabel: "Balanca Prix 4 Uno 30 kg",
        capacityClassLabel: "30 kg · 0,005 kg · III",
        supportingStandardCodes: ["PESO-001"],
        addressLine1: "Avenida do Comercio, 45",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78005-010",
        addressCountry: "Brasil",
        addressConditionsLabel: "Atendimento antes da abertura.",
        lastCalibrationAtUtc: "2026-04-20T00:00:00.000Z",
        nextCalibrationAtUtc: "2026-10-20T00:00:00.000Z",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    auditEvents: [
      ...seed.auditEvents,
      {
        entityType: "equipment" as const,
        entityId: "equipment-00141",
        action: "update",
        summary: "Equipamento da carteira do portal vinculado ao cliente externo seed.",
        createdAtUtc: "2026-04-23T13:00:00.000Z",
      },
    ],
  };
}

export function createV4ServiceOrderSeed() {
  const seed = createV3ServiceOrderSeed();
  return {
    ...seed,
    customers: [
      ...seed.customers,
      {
        customerId: "customer-002",
        organizationId: "org-1",
        tradeName: "Padaria Pao Doce",
        addressLine1: "Avenida do Comercio, 45",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78005-010",
        addressCountry: "Brasil",
      },
    ],
    equipment: [
      ...seed.equipment,
      {
        equipmentId: "equipment-00141",
        organizationId: "org-1",
        customerId: "customer-002",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-00141",
        tagCode: "BAL-141",
        serialNumber: "SN-141-02",
        typeModelLabel: "Balanca Prix 4 Uno 30 kg",
        metrologyProfile: buildEquipmentMetrologyProfileFixture({
          instrumentKind: "nawi",
          maximumCapacityValue: 30,
          readabilityValue: 0.005,
          verificationScaleIntervalValue: 0.005,
          normativeClass: "iii",
          effectiveRangeMaxValue: 30,
        }),
      },
    ],
    serviceOrders: [
      ...seed.serviceOrders,
      {
        serviceOrderId: "service-order-00141",
        organizationId: "org-1",
        customerId: "customer-002",
        customerName: "Padaria Pao Doce",
        customerAddress: {
          line1: "Avenida do Comercio, 45",
          city: "Cuiaba",
          state: "MT",
          postalCode: "78005-010",
          country: "Brasil",
        },
        equipmentId: "equipment-00141",
        equipmentLabel: "EQ-00141 · Balanca Prix 4 Uno 30 kg",
        equipmentCode: "EQ-00141",
        equipmentTagCode: "BAL-141",
        equipmentSerialNumber: "SN-141-02",
        instrumentType: "balanca",
        procedureId: "procedure-001",
        procedureLabel: "PT-005 rev.04",
        primaryStandardId: "standard-001",
        standardsLabel: "PESO-001 · Peso padrao 1 kg",
        equipmentMetrologySnapshot: buildEquipmentMetrologyProfileFixture({
          instrumentKind: "nawi",
          maximumCapacityValue: 30,
          readabilityValue: 0.005,
          verificationScaleIntervalValue: 0.005,
          normativeClass: "iii",
          effectiveRangeMaxValue: 30,
        }),
        standardMetrologySnapshot: buildStandardMetrologyProfileFixture({
          expandedUncertaintyValue: 0.000008,
          conventionalMassErrorValue: 0.000001,
        }),
        standardSource: "RBC" as const,
        standardCertificateReference: "1234/25/081",
        standardHasValidCertificate: true,
        standardCertificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        standardMeasurementValue: 1,
        standardApplicableRange: { minimum: 0, maximum: 1 },
        executorUserId: "user-admin-1",
        executorName: "Ana Administradora",
        reviewerUserId: "user-reviewer-1",
        reviewerName: "Renata Revisora",
        signatoryUserId: "user-signatory-1",
        signatoryName: "Bruno Signatario",
        workOrderNumber: "OS-2026-00141",
        workflowStatus: "emitted" as const,
        environmentLabel: "23,0 C · 52% UR · atendimento antes da abertura",
        curvePointsLabel: "4 pontos com repetibilidade em 50%",
        evidenceLabel: "11 evidencias registradas",
        uncertaintyLabel: "U = 0,08 kg (k=2)",
        conformityLabel: "Aprovado sem restricoes adicionais",
        measurementResultValue: 29.998,
        measurementExpandedUncertaintyValue: 0.08,
        measurementCoverageFactor: 2,
        measurementUnit: "kg",
        measurementRawData: buildMeasurementRawDataFixture("kg", 15),
        decisionRuleLabel: "ILAC G8 sem banda de guarda adicional",
        decisionOutcomeLabel: "Conforme",
        freeTextStatement: "Certificado emitido com base em revisao tecnica concluida e assinatura valida.",
        commentDraft: "Historico estavel e repetibilidade dentro do criterio de aceitacao.",
        reviewDecision: "approved" as const,
        reviewDecisionComment: "Revisao aprovada e liberada para emissao oficial.",
        reviewDeviceId: "device-review-02",
        signatureDeviceId: "device-sign-02",
        signatureStatement: "Assinatura eletronica concluida por Bruno Signatario.",
        certificateNumber: "LABPERSISTID-000141",
        certificateRevision: "R0",
        publicVerificationToken: "pubtok-os141",
        documentHash: "1411411411411411411411411411411411411411411411411411411411411411",
        qrHost: "lab-persistido.afere.local",
        createdAtUtc: "2026-04-12T11:42:00.000Z",
        acceptedAtUtc: "2026-04-12T12:03:00.000Z",
        executionStartedAtUtc: "2026-04-19T13:10:00.000Z",
        executedAtUtc: "2026-04-19T15:40:00.000Z",
        reviewStartedAtUtc: "2026-04-20T08:40:00.000Z",
        reviewCompletedAtUtc: "2026-04-20T09:10:00.000Z",
        signatureStartedAtUtc: "2026-04-20T09:18:00.000Z",
        signedAtUtc: "2026-04-20T09:22:00.000Z",
        emittedAtUtc: "2026-04-20T09:23:00.000Z",
        updatedAtUtc: "2026-04-20T09:23:00.000Z",
      },
    ],
    certificatePublications: [
      {
        publicationId: "publication-00141-r0",
        organizationId: "org-1",
        serviceOrderId: "service-order-00141",
        customerId: "customer-002",
        customerName: "Padaria Pao Doce",
        equipmentId: "equipment-00141",
        equipmentLabel: "EQ-00141 · Balanca Prix 4 Uno 30 kg",
        equipmentTagCode: "BAL-141",
        equipmentSerialNumber: "SN-141-02",
        workOrderNumber: "OS-2026-00141",
        certificateNumber: "LABPERSISTID-000141",
        revision: "R0",
        publicVerificationToken: "pubtok-os141",
        documentHash: "1411411411411411411411411411411411411411411411411411411411411411",
        qrHost: "lab-persistido.afere.local",
        signedAtUtc: "2026-04-20T09:22:00.000Z",
        issuedAtUtc: "2026-04-20T09:23:00.000Z",
        createdAtUtc: "2026-04-20T09:23:00.000Z",
        updatedAtUtc: "2026-04-20T09:23:00.000Z",
      },
    ],
    emissionAuditEvents: buildSeedEmissionAuditTrail("service-order-00141", [
      { eventId: "audit-00141-0", action: "calibration.executed", actorUserId: "user-admin-1", actorLabel: "Ana Administradora", entityLabel: "OS-2026-00141", occurredAtUtc: "2026-04-19T15:40:00.000Z" },
      { eventId: "audit-00141-1", action: "technical_review.completed", actorUserId: "user-reviewer-1", actorLabel: "Renata Revisora", entityLabel: "OS-2026-00141", deviceId: "device-review-02", occurredAtUtc: "2026-04-20T09:10:00.000Z" },
      { eventId: "audit-00141-2", action: "certificate.signed", actorUserId: "user-signatory-1", actorLabel: "Bruno Signatario", entityLabel: "OS-2026-00141", deviceId: "device-sign-02", certificateNumber: "LABPERSISTID-000141", occurredAtUtc: "2026-04-20T09:22:00.000Z" },
      { eventId: "audit-00141-3", action: "certificate.emitted", actorUserId: "user-signatory-1", actorLabel: "Bruno Signatario", entityLabel: "OS-2026-00141", deviceId: "device-sign-02", certificateNumber: "LABPERSISTID-000141", occurredAtUtc: "2026-04-20T09:23:00.000Z" },
    ]),
  };
}

export function buildMeasurementRawDataFixture(unit: string, loadValue: number) {
  return {
    captureMode: "manual" as const,
    environment: {
      temperatureStartC: 22.1,
      temperatureEndC: 22.3,
      relativeHumidityPercent: 48,
      atmosphericPressureHpa: 1013,
    },
    repeatabilityRuns: [
      {
        loadValue,
        unit,
        indications: [loadValue, loadValue + 0.001, loadValue, loadValue + 0.001, loadValue],
      },
    ],
    eccentricityPoints: [
      { positionLabel: "centro", loadValue, indicationValue: loadValue, unit },
      { positionLabel: "frontal", loadValue, indicationValue: loadValue + 0.002, unit },
    ],
    linearityPoints: [
      { pointLabel: "50%", sequence: "ascending" as const, appliedLoadValue: loadValue, referenceValue: loadValue, indicationValue: loadValue + 0.001, unit },
    ],
    evidenceAttachments: [
      { attachmentId: "evidence-seed-001", label: "Foto do ensaio", kind: "photo", mediaType: "image/jpeg" },
    ],
  };
}

export function buildEquipmentMetrologyProfileFixture(input: {
  instrumentKind: "nawi" | "platform_scale" | "analytical_balance" | "precision_balance" | "vehicle_scale";
  maximumCapacityValue: number;
  readabilityValue: number;
  verificationScaleIntervalValue: number;
  normativeClass?: "i" | "ii" | "iii" | "iiii";
  effectiveRangeMaxValue?: number;
}) {
  return {
    instrumentKind: input.instrumentKind,
    measurementUnit: "kg",
    maximumCapacityValue: input.maximumCapacityValue,
    readabilityValue: input.readabilityValue,
    verificationScaleIntervalValue: input.verificationScaleIntervalValue,
    normativeClass: input.normativeClass,
    minimumCapacityValue: 0,
    minimumLoadValue: 0,
    effectiveRangeMinValue: 0,
    effectiveRangeMaxValue: input.effectiveRangeMaxValue ?? input.maximumCapacityValue,
  };
}

export function buildStandardMetrologyProfileFixture(input: {
  expandedUncertaintyValue: number;
  conventionalMassErrorValue?: number;
}) {
  return {
    quantityKind: "mass" as const,
    measurementUnit: "kg",
    traceabilitySource: "rbc" as const,
    certificateIssuer: "Lab Cal-1234",
    expandedUncertaintyValue: input.expandedUncertaintyValue,
    coverageFactorK: 2,
    conventionalMassErrorValue: input.conventionalMassErrorValue,
    densityKgPerM3: 8000,
  };
}

export function createV5QualitySeed() {
  return {
    nonconformities: [
      {
        ncId: "nc-014",
        organizationId: "org-1",
        serviceOrderId: "service-order-00147",
        workOrderNumber: "OS-2026-00147",
        ownerUserId: "user-admin-1",
        ownerLabel: "Ana Administradora",
        title: "NC-014 · Revisor conflitado e padrao vencido na OS bloqueada",
        originLabel: "Revisao tecnica",
        severityLabel: "Critica",
        status: "blocked" as const,
        noticeLabel: "A OS permanece bloqueada ate segregar funcoes e regularizar o padrao principal.",
        rootCauseLabel: "Atribuicao inadequada de papeis somada a uso de padrao fora da validade.",
        containmentLabel: "Suspender qualquer liberacao da OS-2026-00147.",
        correctiveActionLabel: "Substituir o revisor, recalibrar o padrao e registrar nova conferencia.",
        evidenceLabel: "OS-2026-00147 e trilha append-only.",
        blockers: ["Segregacao de funcoes pendente", "Padrao principal vencido"],
        warnings: ["Nao emitir certificado ate fechar a NC."],
        openedAtUtc: "2026-04-23T13:20:00.000Z",
        dueAtUtc: "2026-04-30T17:00:00.000Z",
      },
    ],
    nonconformingWork: [
      {
        caseId: "ncw-014",
        organizationId: "org-1",
        serviceOrderId: "service-order-00147",
        workOrderNumber: "OS-2026-00147",
        nonconformityId: "nc-014",
        title: "NCW-014 · Contencao da OS-2026-00147",
        classificationLabel: "Contencao preventiva",
        originLabel: "OS bloqueada",
        affectedEntityLabel: "OS-2026-00147",
        status: "blocked" as const,
        noticeLabel: "Liberacao do fluxo bloqueada ate nova evidencia minima.",
        containmentLabel: "Manter a OS congelada.",
        releaseRuleLabel: "Somente liberar apos NC encerrada.",
        evidenceLabel: "Registro da NC-014 e trilha de revisao.",
        restorationLabel: "Retomar apenas com novo revisor e padrao valido.",
        blockers: ["NC-014 aberta"],
        warnings: ["Nao substituir a contencao por acordo verbal."],
        createdAtUtc: "2026-04-23T14:00:00.000Z",
        updatedAtUtc: "2026-04-23T14:10:00.000Z",
      },
    ],
    internalAuditCycles: [
      {
        cycleId: "audit-cycle-2026-q2",
        organizationId: "org-1",
        cycleLabel: "Programa 2026 · Ciclo 2",
        windowLabel: "Q2 2026",
        scopeLabel: "§7.8 Certificados | §7.10 Trabalho nao conforme",
        auditorLabel: "Ana Administradora",
        auditeeLabel: "Operacoes e Qualidade",
        periodLabel: "Abr-Jun 2026",
        reportLabel: "Relatorio parcial do ciclo 2 em follow-up",
        evidenceLabel: "Checklist do ciclo, NC-014 e trilha da OS-2026-00147.",
        nextReviewLabel: "05/05/2026 13:00 UTC",
        noticeLabel: "O ciclo permanece aberto ate concluir o follow-up da NC critica.",
        status: "attention" as const,
        checklist: [
          { key: "certificates", requirementLabel: "Certificados emitidos e bloqueados com evidencias rastreaveis", evidenceLabel: "service_orders + emission_audit_events", status: "attention" as const },
          { key: "nonconforming-work", requirementLabel: "Contencao formal do trabalho nao conforme", evidenceLabel: "nonconforming_work_cases + NC-014", status: "blocked" as const },
        ],
        findingRefs: ["nc-014"],
        blockers: ["NC critica ainda sem encerramento"],
        warnings: ["Nao abrir novo ciclo sem concluir o follow-up atual."],
        scheduledAtUtc: "2026-04-24T14:00:00.000Z",
      },
    ],
    managementReviewMeetings: [
      {
        meetingId: "review-2026-q2",
        organizationId: "org-1",
        titleLabel: "Analise critica Q2 2026",
        status: "attention" as const,
        dateLabel: "23/04/2026",
        outcomeLabel: "Pauta aberta com follow-up de Qualidade",
        noticeLabel: "A ata final depende do fechamento minimo da NC critica e do ciclo de auditoria.",
        nextMeetingLabel: "30/09/2026",
        chairLabel: "Ana Administradora",
        attendeesLabel: "Direcao, Qualidade e Metrologia",
        periodLabel: "Q2 2026",
        ataLabel: "Ata em preparacao",
        evidenceLabel: "Indicadores V5, NC-014, auditoria e perfil regulatorio persistido.",
        agendaItems: [
          { key: "agenda-nc", label: "NCs e trabalho nao conforme", status: "attention" as const },
          { key: "agenda-audit", label: "Follow-up da auditoria interna", status: "attention" as const },
        ],
        decisions: [
          { key: "decision-close-nc", label: "Encerrar NC-014 com evidencias minimas", ownerLabel: "Ana Administradora", dueDateLabel: "05/05/2026", status: "attention" as const },
        ],
        blockers: [],
        warnings: ["A ata nao deve ser arquivada antes do follow-up minimo da NC."],
        scheduledForUtc: "2026-04-23T13:00:00.000Z",
        heldAtUtc: "2026-04-23T14:10:00.000Z",
      },
    ],
    qualityIndicatorSnapshots: buildV5IndicatorHistorySeed(),
    complianceProfiles: [
      {
        complianceProfileId: "compliance-profile-v5",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        regulatoryProfile: "type_b",
        normativePackageVersion: "2026-04-20-baseline-v0.1.0",
        organizationCode: "AFERE",
        planLabel: "Enterprise",
        certificatePrefix: "LABDEMO",
        accreditationNumber: "Cgcre CAL-1234",
        accreditationValidUntilUtc: "2027-09-30T00:00:00.000Z",
        scopeSummary: "Escopo demo controlado para balancas.",
        cmcSummary: "CMC demo revisada para o tenant persistido.",
        scopeItemCount: 4,
        cmcItemCount: 4,
        legalOpinionStatus: "approved_reference",
        legalOpinionReference: "compliance/legal-opinions/2026-04-21-signature-auditability-opinion.md",
        dpaReference: "compliance/legal-opinions/dpa-template.md",
        normativeGovernanceStatus: "active",
        normativeGovernanceOwner: "product-governance",
        normativeGovernanceReference: "compliance/release-norm/pre-go-live-normative-governance.yaml",
        releaseNormVersion: "v5",
        releaseNormStatus: "pending_local_validation",
        lastReviewedAtUtc: "2026-04-23T20:30:00.000Z",
      },
    ],
  };
}

function buildV5IndicatorHistorySeed() {
  return [
    ...buildIndicatorHistorySeed({
      indicatorId: "indicator-emission-completion",
      targetNumeric: 85,
      points: [
        ["2025-11-01T00:00:00.000Z", 62, "attention"],
        ["2025-12-01T00:00:00.000Z", 68, "attention"],
        ["2026-01-01T00:00:00.000Z", 72, "attention"],
        ["2026-02-01T00:00:00.000Z", 79, "attention"],
        ["2026-03-01T00:00:00.000Z", 81, "attention"],
        ["2026-04-01T00:00:00.000Z", 84, "attention"],
      ],
      sourcePrefix: "Fechamento mensal emissao",
      evidenceLabel: "Consolidado gerencial do fluxo emitido.",
    }),
    ...buildIndicatorHistorySeed({
      indicatorId: "indicator-open-nc-pressure",
      targetNumeric: 1,
      points: [
        ["2025-11-01T00:00:00.000Z", 3, "blocked"],
        ["2025-12-01T00:00:00.000Z", 3, "blocked"],
        ["2026-01-01T00:00:00.000Z", 2, "attention"],
        ["2026-02-01T00:00:00.000Z", 2, "attention"],
        ["2026-03-01T00:00:00.000Z", 1, "ready"],
        ["2026-04-01T00:00:00.000Z", 1, "ready"],
      ],
      sourcePrefix: "Fechamento mensal NC",
      evidenceLabel: "Consolidado mensal de nao conformidades.",
    }),
    ...buildIndicatorHistorySeed({
      indicatorId: "indicator-governance-follow-up",
      targetNumeric: 1,
      points: [
        ["2025-11-01T00:00:00.000Z", 4, "blocked"],
        ["2025-12-01T00:00:00.000Z", 3, "blocked"],
        ["2026-01-01T00:00:00.000Z", 3, "blocked"],
        ["2026-02-01T00:00:00.000Z", 2, "attention"],
        ["2026-03-01T00:00:00.000Z", 2, "attention"],
        ["2026-04-01T00:00:00.000Z", 1, "ready"],
      ],
      sourcePrefix: "Fechamento mensal follow-up",
      evidenceLabel: "Consolidado mensal de follow-up gerencial.",
    }),
  ];
}

function buildIndicatorHistorySeed(input: {
  indicatorId: string;
  targetNumeric: number;
  points: Array<[monthStartUtc: string, valueNumeric: number, status: "ready" | "attention" | "blocked"]>;
  sourcePrefix: string;
  evidenceLabel: string;
}) {
  return input.points.map(([monthStartUtc, valueNumeric, status], index) => ({
    snapshotId: `${input.indicatorId}-${monthStartUtc.slice(0, 7)}`,
    organizationId: "org-1",
    indicatorId: input.indicatorId,
    monthStartUtc,
    valueNumeric: new Prisma.Decimal(valueNumeric),
    targetNumeric: new Prisma.Decimal(input.targetNumeric),
    status,
    sourceLabel: `${input.sourcePrefix} ${monthStartUtc.slice(5, 7)}/${monthStartUtc.slice(0, 4)}`,
    evidenceLabel: input.evidenceLabel,
    createdAtUtc: new Date(Date.parse(monthStartUtc) + 24 * 60 * 60 * 1000).toISOString(),
    updatedAtUtc: new Date(Date.parse(monthStartUtc) + (index + 2) * 24 * 60 * 60 * 1000).toISOString(),
  }));
}

export function buildSeedEmissionAuditTrail(
  serviceOrderId: string,
  events: Array<{
    eventId: string;
    action: string;
    actorUserId?: string;
    actorLabel: string;
    entityLabel: string;
    deviceId?: string;
    certificateNumber?: string;
    occurredAtUtc: string;
  }>,
) {
  let prevHash = "0".repeat(64);
  return events.map((event) => {
    const hash = computeAuditHash(prevHash, {
      action: event.action,
      actorId: event.actorUserId,
      actorLabel: event.actorLabel,
      certificateId: serviceOrderId,
      certificateNumber: event.certificateNumber,
      entityLabel: event.entityLabel,
      timestampUtc: event.occurredAtUtc,
      deviceId: event.deviceId,
    });
    const row = {
      eventId: event.eventId,
      organizationId: "org-1",
      serviceOrderId,
      workOrderNumber: event.entityLabel,
      actorUserId: event.actorUserId,
      actorLabel: event.actorLabel,
      action: event.action,
      entityLabel: event.entityLabel,
      deviceId: event.deviceId,
      certificateNumber: event.certificateNumber,
      prevHash,
      hash,
      occurredAtUtc: event.occurredAtUtc,
    };
    prevHash = hash;
    return row;
  });
}
