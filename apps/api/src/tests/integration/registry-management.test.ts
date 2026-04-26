import assert from "node:assert/strict";
import { test } from "node:test";

import {
  auditTrailCatalogSchema,
  authSessionSchema,
  certificatePreviewCatalogSchema,
  complaintRegistryCatalogSchema,
  customerRegistryCatalogSchema,
  emissionDryRunCatalogSchema,
  emissionWorkspaceCatalogSchema,
  managementReviewCatalogSchema,
  nonconformingWorkCatalogSchema,
  nonconformityRegistryCatalogSchema,
  offlineSyncCatalogSchema,
  equipmentRegistryCatalogSchema,
  internalAuditCatalogSchema,
  onboardingCatalogSchema,
  organizationSettingsCatalogSchema,
  portalDashboardCatalogSchema,
  portalCertificateCatalogSchema,
  portalEquipmentCatalogSchema,
  procedureRegistryCatalogSchema,
  publicCertificateCatalogSchema,
  qualityDocumentRegistryCatalogSchema,
  qualityHubCatalogSchema,
  qualityIndicatorRegistryCatalogSchema,
  riskRegisterCatalogSchema,
  reviewSignatureCatalogSchema,
  serviceOrderReviewCatalogSchema,
  selfSignupCatalogSchema,
  signatureQueueCatalogSchema,
  standardRegistryCatalogSchema,
  userDirectoryCatalogSchema,
} from "@afere/contracts";

import { buildApp } from "../../app.js";
import { createMemoryCorePersistence } from "../../domain/auth/core-persistence.js";
import { createMemoryServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { createMemoryQualityPersistence } from "../../domain/quality/quality-persistence.js";
import { createMemoryRegistryPersistence } from "../../domain/registry/registry-persistence.js";

import {
  TEST_ENV,
  createRuntimeReadinessStub,
  normalizeCookieHeader,
  createV1MemorySeed,
  createV2RegistrySeed,
  createV3CoreSeed,
  createV3ServiceOrderSeed,
  createV4CoreSeed,
  createV4RegistrySeed,
  createV4ServiceOrderSeed,
  createV5QualitySeed,
  buildMeasurementRawDataFixture,
  buildEquipmentMetrologyProfileFixture,
  buildStandardMetrologyProfileFixture,
  buildSeedEmissionAuditTrail,
} from "./helpers.js";

test("allows admins to manage persisted users and v2 registry records", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
  });

  try {
    const login = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: {
        email: "admin@afere.local",
        password: "Afere@2026!",
      },
    });

    const cookie = normalizeCookieHeader(login.headers["set-cookie"]);
    assert.ok(cookie);

    const saveUser = await app.inject({
      method: "POST",
      url: "/auth/users/manage",
      headers: { cookie },
      payload: {
        action: "save",
        email: "tecnico2@afere.local",
        password: "Afere@2026!",
        displayName: "Teresa Tecnica",
        roles: ["technician"],
        status: "active",
        teamName: "Campo",
        mfaEnforced: false,
        mfaEnrolled: false,
        deviceCount: 1,
        competenciesText: "balanca|Tecnica de campo|2027-06-01",
      },
    });
    assert.equal(saveUser.statusCode, 204);

    const saveStandard = await app.inject({
      method: "POST",
      url: "/registry/standards/manage",
      headers: { cookie },
      payload: {
        action: "save",
        code: "PESO-050",
        title: "Peso padrao 50 kg",
        kindLabel: "Peso",
        nominalClassLabel: "50 kg · M1",
        sourceLabel: "RBC-5050",
        certificateLabel: "5050/26/001",
        manufacturerLabel: "Coelmatic",
        modelLabel: "M50K",
        serialNumberLabel: "50K-001",
        nominalValueLabel: "50,000 kg",
        classLabel: "M1",
        usageRangeLabel: "0 kg ate 50 kg",
        measurementValue: 50,
        applicableRangeMin: 0,
        applicableRangeMax: 50,
        uncertaintyLabel: "+/- 0,020 kg",
        correctionFactorLabel: "+0,001 kg",
        quantityKind: "mass",
        measurementUnit: "kg",
        traceabilitySource: "rbc",
        certificateIssuer: "Lab Cal-5050",
        conventionalMassErrorValue: 0.0012,
        expandedUncertaintyValue: 0.02,
        coverageFactorK: 2,
        densityKgPerM3: 8000,
        hasValidCertificate: true,
        certificateValidUntilUtc: "2027-04-23",
      },
    });
    assert.equal(saveStandard.statusCode, 204);

    const saveProcedure = await app.inject({
      method: "POST",
      url: "/registry/procedures/manage",
      headers: { cookie },
      payload: {
        action: "save",
        code: "PT-050",
        title: "Calibracao de plataforma pesada",
        typeLabel: "NAWI pesada",
        revisionLabel: "01",
        effectiveSinceUtc: "2026-04-23",
        lifecycleLabel: "Vigente",
        usageLabel: "Campo controlado",
        scopeLabel: "Balancas plataforma ate 500 kg.",
        environmentRangeLabel: "Temp 18C-26C",
        curvePolicyLabel: "5 pontos com subida e descida",
        standardsPolicyLabel: "Padrao de massa M1 vigente",
        approvalLabel: "Aprovado por Ana Administradora",
        relatedDocuments: ["IT-050", "FR-050"],
      },
    });
    assert.equal(saveProcedure.statusCode, 204);

    const standardsResponse = await app.inject({
      method: "GET",
      url: "/registry/standards",
      headers: { cookie },
    });
    const standardsPayload = standardRegistryCatalogSchema.parse(standardsResponse.json());
    const createdStandard = standardsPayload.scenarios[0]?.items.find(
      (item) => item.certificateLabel === "5050/26/001",
    );
    assert.ok(createdStandard);

    const createdStandardDetailResponse = await app.inject({
      method: "GET",
      url: `/registry/standards?standard=${createdStandard?.standardId}`,
      headers: { cookie },
    });
    const createdStandardDetailPayload = standardRegistryCatalogSchema.parse(
      createdStandardDetailResponse.json(),
    );
    assert.equal(
      createdStandardDetailPayload.scenarios[0]?.detail.metrologyProfile?.certificateIssuer,
      "Lab Cal-5050",
    );
    assert.equal(
      createdStandardDetailPayload.scenarios[0]?.detail.metrologyProfile?.coverageFactorK,
      2,
    );

    const proceduresResponse = await app.inject({
      method: "GET",
      url: "/registry/procedures",
      headers: { cookie },
    });
    const proceduresPayload = procedureRegistryCatalogSchema.parse(proceduresResponse.json());
    const createdProcedure = proceduresPayload.scenarios[0]?.items.find(
      (item) => item.code === "PT-050",
    );
    assert.ok(createdProcedure);

    const saveEquipment = await app.inject({
      method: "POST",
      url: "/registry/equipment/manage",
      headers: { cookie },
      payload: {
        action: "save",
        customerId: "customer-001",
        procedureId: createdProcedure?.procedureId,
        primaryStandardId: createdStandard?.standardId,
        code: "EQ-050",
        tagCode: "PLAT-050",
        serialNumber: "SN-050",
        typeModelLabel: "Balanca plataforma 500 kg",
        capacityClassLabel: "500 kg · 0,1 kg · III",
        instrumentKind: "platform_scale",
        measurementUnit: "kg",
        maximumCapacityValue: 500,
        minimumCapacityValue: 0,
        readabilityValue: 0.1,
        verificationScaleIntervalValue: 0.1,
        normativeClass: "iii",
        effectiveRangeMinValue: 5,
        effectiveRangeMaxValue: 500,
        supportingStandardCodes: ["PESO-001", "PESO-002"],
        addressLine1: "Rua da Calibracao, 500",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-500",
        addressCountry: "Brasil",
        addressConditionsLabel: "Area coberta",
        lastCalibrationAtUtc: "2026-04-10",
        nextCalibrationAtUtc: "2026-10-10",
      },
    });
    assert.equal(saveEquipment.statusCode, 204);

    const saveCustomer = await app.inject({
      method: "POST",
      url: "/registry/customers/manage",
      headers: { cookie },
      payload: {
        action: "save",
        legalName: "Cliente Campo Ltda.",
        tradeName: "Cliente Campo",
        documentLabel: "55.555.555/0001-55",
        segmentLabel: "Industria",
        accountOwnerName: "Marta Operacoes",
        accountOwnerEmail: "marta@clientecampo.com.br",
        contractLabel: "Contrato vigente ate 12/2026",
        specialConditionsLabel: "Atendimento em janela noturna",
        contactName: "Marta Operacoes",
        contactRoleLabel: "Coordenadora",
        contactEmail: "marta@clientecampo.com.br",
        contactPhoneLabel: "(65) 99999-5050",
        addressLine1: "Distrito Industrial, 505",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78010-505",
        addressCountry: "Brasil",
        addressConditionsLabel: "Acesso controlado",
      },
    });
    assert.equal(saveCustomer.statusCode, 204);

    const directoryResponse = await app.inject({
      method: "GET",
      url: "/auth/users",
      headers: { cookie },
    });
    const directoryPayload = userDirectoryCatalogSchema.parse(directoryResponse.json());
    assert.equal(
      directoryPayload.scenarios[0]?.users.some((user) => user.email === "tecnico2@afere.local"),
      true,
    );

    const customersResponse = await app.inject({
      method: "GET",
      url: "/registry/customers",
      headers: { cookie },
    });
    const customersPayload = customerRegistryCatalogSchema.parse(customersResponse.json());
    assert.equal(
      customersPayload.scenarios[0]?.customers.some((customer) => customer.tradeName === "Cliente Campo"),
      true,
    );

    const equipmentResponse = await app.inject({
      method: "GET",
      url: "/registry/equipment",
      headers: { cookie },
    });
    const equipmentPayload = equipmentRegistryCatalogSchema.parse(equipmentResponse.json());
    const createdEquipment = equipmentPayload.scenarios[0]?.items.find((item) => item.code === "EQ-050");
    assert.ok(createdEquipment);

    const createdEquipmentDetailResponse = await app.inject({
      method: "GET",
      url: `/registry/equipment?equipment=${createdEquipment?.equipmentId}`,
      headers: { cookie },
    });
    const createdEquipmentDetailPayload = equipmentRegistryCatalogSchema.parse(
      createdEquipmentDetailResponse.json(),
    );
    assert.equal(
      createdEquipmentDetailPayload.scenarios[0]?.detail.metrologyProfile?.instrumentKind,
      "platform_scale",
    );
    assert.equal(
      createdEquipmentDetailPayload.scenarios[0]?.detail.metrologyProfile?.verificationScaleIntervalValue,
      0.1,
    );

    const archiveEquipment = await app.inject({
      method: "POST",
      url: "/registry/equipment/manage",
      headers: { cookie },
      payload: {
        action: "archive",
        equipmentId: createdEquipment?.equipmentId,
      },
    });
    assert.equal(archiveEquipment.statusCode, 204);

    const archivedEquipmentResponse = await app.inject({
      method: "GET",
      url: `/registry/equipment?equipment=${createdEquipment?.equipmentId}`,
      headers: { cookie },
    });
    const archivedEquipmentPayload = equipmentRegistryCatalogSchema.parse(
      archivedEquipmentResponse.json(),
    );
    assert.equal(archivedEquipmentPayload.scenarios[0]?.detail.status, "blocked");
  } finally {
    await app.close();
  }
});

