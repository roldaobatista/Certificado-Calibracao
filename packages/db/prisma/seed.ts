import { createHash, scryptSync } from "node:crypto";

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const ORGANIZATION_ID = "00000000-0000-4000-8000-000000000101";
const ADMIN_ID = "00000000-0000-4000-8000-000000000201";
const SIGNATORY_ID = "00000000-0000-4000-8000-000000000202";
const TECHNICIAN_ID = "00000000-0000-4000-8000-000000000203";
const INVITED_ID = "00000000-0000-4000-8000-000000000204";
const SUSPENDED_ID = "00000000-0000-4000-8000-000000000205";
const EXTERNAL_CLIENT_ID = "00000000-0000-4000-8000-000000000206";
const CUSTOMER_IDS = {
  acme: "00000000-0000-4000-8000-000000000401",
  paoDoce: "00000000-0000-4000-8000-000000000402",
  xyz: "00000000-0000-4000-8000-000000000403",
  pendente: "00000000-0000-4000-8000-000000000404",
};
const STANDARD_IDS = {
  peso1: "00000000-0000-4000-8000-000000000501",
  peso2: "00000000-0000-4000-8000-000000000502",
  peso5: "00000000-0000-4000-8000-000000000503",
  peso10: "00000000-0000-4000-8000-000000000504",
  thermo: "00000000-0000-4000-8000-000000000505",
};
const PROCEDURE_IDS = {
  pt005r04: "00000000-0000-4000-8000-000000000601",
  pt006r02: "00000000-0000-4000-8000-000000000602",
  pt009r02: "00000000-0000-4000-8000-000000000603",
  pg001r01: "00000000-0000-4000-8000-000000000604",
  pt005r03: "00000000-0000-4000-8000-000000000605",
};
const EQUIPMENT_IDS = {
  eq0007: "00000000-0000-4000-8000-000000000701",
  eq0012: "00000000-0000-4000-8000-000000000702",
  eq0011: "00000000-0000-4000-8000-000000000703",
  eq0008: "00000000-0000-4000-8000-000000000704",
  eq0404: "00000000-0000-4000-8000-000000000705",
};
const SERVICE_ORDER_IDS = {
  os142: "00000000-0000-4000-8000-000000000801",
  os141: "00000000-0000-4000-8000-000000000802",
  os147: "00000000-0000-4000-8000-000000000803",
};
const CERTIFICATE_PUBLICATION_IDS = {
  os141r0: "00000000-0000-4000-8000-000000000851",
};
const QUALITY_IDS = {
  nc014: "00000000-0000-4000-8000-000000000861",
  ncw014: "00000000-0000-4000-8000-000000000862",
  audit2026q2: "00000000-0000-4000-8000-000000000863",
  review2026q2: "00000000-0000-4000-8000-000000000864",
  complianceProfile: "00000000-0000-4000-8000-000000000865",
};
const GENESIS_HASH = "0".repeat(64);
const DEFAULT_PASSWORD = "Afere@2026!";

async function main() {
  const passwordHash = hashSeedPassword(DEFAULT_PASSWORD);

  await prisma.organization.upsert({
    where: { id: ORGANIZATION_ID },
    create: {
      id: ORGANIZATION_ID,
      slug: "lab-demo",
      legalName: "Laboratorio Aferê Demo",
      regulatoryProfile: "type_b",
      normativePackageVersion: "2026-04-20-baseline-v0.1.0",
    },
    update: {
      slug: "lab-demo",
      legalName: "Laboratorio Aferê Demo",
      regulatoryProfile: "type_b",
      normativePackageVersion: "2026-04-20-baseline-v0.1.0",
    },
  });

  await upsertUser({
    id: ADMIN_ID,
    email: "admin@afere.local",
    displayName: "Ana Administradora",
    roles: ["admin", "quality_manager"],
    teamName: "Gestao tecnica",
    status: "active",
    mfaEnforced: true,
    mfaEnrolled: true,
    deviceCount: 2,
    passwordHash,
  });

  await upsertUser({
    id: SIGNATORY_ID,
    email: "signatario@afere.local",
    displayName: "Bruno Signatario",
    roles: ["signatory", "technical_reviewer"],
    teamName: "Metrologia",
    status: "active",
    mfaEnforced: true,
    mfaEnrolled: true,
    deviceCount: 1,
    passwordHash,
  });

  await upsertUser({
    id: TECHNICIAN_ID,
    email: "tecnico@afere.local",
    displayName: "Carla Tecnica",
    roles: ["technician"],
    teamName: "Campo",
    status: "active",
    mfaEnforced: false,
    mfaEnrolled: false,
    deviceCount: 1,
    passwordHash,
  });

  await upsertUser({
    id: INVITED_ID,
    email: "convite@afere.local",
    displayName: "Diego Convite",
    roles: ["technical_reviewer"],
    teamName: "Qualidade",
    status: "invited",
    mfaEnforced: true,
    mfaEnrolled: false,
    deviceCount: 0,
    passwordHash,
  });

  await upsertUser({
    id: SUSPENDED_ID,
    email: "suspenso@afere.local",
    displayName: "Elisa Suspensa",
    roles: ["technician"],
    teamName: "Campo",
    status: "suspended",
    mfaEnforced: false,
    mfaEnrolled: false,
    deviceCount: 0,
    passwordHash,
  });

  await upsertUser({
    id: EXTERNAL_CLIENT_ID,
    email: "marcia@paodoce.com.br",
    displayName: "Marcia Lima",
    roles: ["external_client"],
    teamName: "Cliente",
    status: "active",
    mfaEnforced: false,
    mfaEnrolled: false,
    deviceCount: 1,
    passwordHash,
  });

  await prisma.userCompetency.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.userCompetency.createMany({
    data: [
      {
        id: "00000000-0000-4000-8000-000000000301",
        organizationId: ORGANIZATION_ID,
        userId: SIGNATORY_ID,
        instrumentType: "balanca",
        roleLabel: "Signatario autorizado",
        status: "authorized",
        validUntil: parseDate("2027-04-20"),
      },
      {
        id: "00000000-0000-4000-8000-000000000302",
        organizationId: ORGANIZATION_ID,
        userId: SIGNATORY_ID,
        instrumentType: "balanca",
        roleLabel: "Revisor tecnico",
        status: "authorized",
        validUntil: parseDate("2027-01-20"),
      },
      {
        id: "00000000-0000-4000-8000-000000000303",
        organizationId: ORGANIZATION_ID,
        userId: TECHNICIAN_ID,
        instrumentType: "balanca",
        roleLabel: "Executor de campo",
        status: "authorized",
        validUntil: parseDate("2026-12-20"),
      },
      {
        id: "00000000-0000-4000-8000-000000000304",
        organizationId: ORGANIZATION_ID,
        userId: INVITED_ID,
        instrumentType: "balanca",
        roleLabel: "Revisor em onboarding",
        status: "expiring",
        validUntil: parseDate("2026-06-15"),
      },
      {
        id: "00000000-0000-4000-8000-000000000305",
        organizationId: ORGANIZATION_ID,
        userId: SUSPENDED_ID,
        instrumentType: "balanca",
        roleLabel: "Tecnico suspenso",
        status: "expired",
        validUntil: parseDate("2026-03-01"),
      },
    ],
  });

  await prisma.onboardingState.upsert({
    where: { organizationId: ORGANIZATION_ID },
    create: {
      organizationId: ORGANIZATION_ID,
      startedAt: new Date("2026-04-23T12:00:00.000Z"),
      completedAt: new Date("2026-04-23T12:42:00.000Z"),
      organizationProfileCompleted: true,
      primarySignatoryReady: true,
      certificateNumberingConfigured: true,
      scopeReviewCompleted: true,
      publicQrConfigured: true,
    },
    update: {
      startedAt: new Date("2026-04-23T12:00:00.000Z"),
      completedAt: new Date("2026-04-23T12:42:00.000Z"),
      organizationProfileCompleted: true,
      primarySignatoryReady: true,
      certificateNumberingConfigured: true,
      scopeReviewCompleted: true,
      publicQrConfigured: true,
    },
  });

  await upsertCustomer({
    id: CUSTOMER_IDS.acme,
    legalName: "Lab. Acme Analises Ltda.",
    tradeName: "Lab. Acme",
    documentLabel: "12.345.678/0001-XX",
    segmentLabel: "Laboratorio clinico",
    accountOwnerName: "Joao das Neves",
    accountOwnerEmail: "joao@lab-acme.com.br",
    contractLabel: "Contrato vigente ate 31/12/2026",
    specialConditionsLabel: "Sala climatizada 21+/-2 C, restricao de acesso",
    contactName: "Joao das Neves",
    contactRoleLabel: "Responsavel tecnico",
    contactEmail: "joao@lab-acme.com.br",
    contactPhoneLabel: "(65) 99999-0001",
    addressLine1: "Rua da Calibracao, 100",
    addressCity: "Cuiaba",
    addressState: "MT",
    addressPostalCode: "78000-000",
    addressCountry: "Brasil",
    addressConditionsLabel: "Sala climatizada 21+/-2 C, acesso controlado.",
    archivedAt: null,
  });

  await upsertCustomer({
    id: CUSTOMER_IDS.paoDoce,
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
    archivedAt: null,
  });

  await upsertCustomer({
    id: CUSTOMER_IDS.xyz,
    legalName: "Industria XYZ Alimentos S.A.",
    tradeName: "Industria XYZ",
    documentLabel: "34.567.890/0001-ZZ",
    segmentLabel: "Industria alimenticia",
    accountOwnerName: "Carlos Mendes",
    accountOwnerEmail: "carlos@xyz.com.br",
    contractLabel: "Contrato vigente ate 30/09/2026",
    specialConditionsLabel: "Janela operacional entre 22h e 4h para linhas criticas",
    contactName: "Carlos Mendes",
    contactRoleLabel: "Coordenador de manutencao",
    contactEmail: "carlos@xyz.com.br",
    contactPhoneLabel: "(65) 99999-2201",
    addressLine1: "Distrito Industrial, 2200",
    addressCity: "Varzea Grande",
    addressState: "MT",
    addressPostalCode: "78110-500",
    addressCountry: "Brasil",
    addressConditionsLabel: "Acesso controlado e EPIs obrigatorios.",
    archivedAt: null,
  });

  await upsertCustomer({
    id: CUSTOMER_IDS.pendente,
    legalName: "Cliente sem cadastro completo",
    tradeName: "Cadastro pendente",
    documentLabel: "CNPJ pendente",
    segmentLabel: "Homologacao",
    accountOwnerName: "Responsavel nao confirmado",
    accountOwnerEmail: "pendente@cliente.local",
    contractLabel: "Contrato aguardando formalizacao",
    specialConditionsLabel: "Endereco do equipamento ainda nao validado",
    contactName: "Contato nao confirmado",
    contactRoleLabel: "Ponto focal pendente",
    contactEmail: "pendente@cliente.local",
    contactPhoneLabel: null,
    addressLine1: "Rua Sem CEP, 10",
    addressCity: "Campo Grande",
    addressState: "MS",
    addressPostalCode: null,
    addressCountry: "Brasil",
    addressConditionsLabel: "Confirmacao documental em aberto.",
    archivedAt: null,
  });

  await upsertStandard({
    id: STANDARD_IDS.peso1,
    code: "PESO-001",
    title: "PESO-001 · Peso padrão 1 kg · classe F1",
    kindLabel: "Peso",
    nominalClassLabel: "1 kg · F1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/081",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M1K",
    serialNumberLabel: "9-22-101",
    nominalValueLabel: "1,000 kg",
    classLabel: "F1",
    usageRangeLabel: "Cargas ate 1 kg",
    measurementValue: 1,
    applicableRangeMin: 0,
    applicableRangeMax: 1,
    uncertaintyLabel: "+/- 8 mg",
    correctionFactorLabel: "+0,001 g",
    hasValidCertificate: true,
    certificateValidUntil: parseDate("2026-08-12"),
    archivedAt: null,
  });

  await upsertStandard({
    id: STANDARD_IDS.peso2,
    code: "PESO-002",
    title: "PESO-002 · Peso padrão 2 kg · classe F1",
    kindLabel: "Peso",
    nominalClassLabel: "2 kg · F1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/082",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M2K",
    serialNumberLabel: "9-22-102",
    nominalValueLabel: "2,000 kg",
    classLabel: "F1",
    usageRangeLabel: "Cargas ate 2 kg",
    measurementValue: 2,
    applicableRangeMin: 0,
    applicableRangeMax: 2,
    uncertaintyLabel: "+/- 9 mg",
    correctionFactorLabel: "+0,002 g",
    hasValidCertificate: true,
    certificateValidUntil: parseDate("2026-08-12"),
    archivedAt: null,
  });

  await upsertStandard({
    id: STANDARD_IDS.peso5,
    code: "PESO-005",
    title: "PESO-005 · Peso padrão 5 kg · classe M1",
    kindLabel: "Peso",
    nominalClassLabel: "5 kg · M1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/088",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M5K",
    serialNumberLabel: "9-22-115",
    nominalValueLabel: "5,000 kg",
    classLabel: "M1",
    usageRangeLabel: "Cargas ate 5 kg",
    measurementValue: 5,
    applicableRangeMin: 0,
    applicableRangeMax: 5,
    uncertaintyLabel: "+/- 12 mg",
    correctionFactorLabel: "+0,003 g",
    hasValidCertificate: true,
    certificateValidUntil: parseDate("2026-04-24"),
    archivedAt: null,
  });

  await upsertStandard({
    id: STANDARD_IDS.peso10,
    code: "PESO-010",
    title: "PESO-010 · Peso padrão 10 kg · classe M1",
    kindLabel: "Peso",
    nominalClassLabel: "10 kg · M1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/099",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M10K",
    serialNumberLabel: "9-22-130",
    nominalValueLabel: "10,000 kg",
    classLabel: "M1",
    usageRangeLabel: "Cargas ate 10 kg",
    measurementValue: 10,
    applicableRangeMin: 0,
    applicableRangeMax: 10,
    uncertaintyLabel: "+/- 18 mg",
    correctionFactorLabel: "+0,005 g",
    hasValidCertificate: true,
    certificateValidUntil: parseDate("2026-04-02"),
    archivedAt: null,
  });

  await upsertStandard({
    id: STANDARD_IDS.thermo,
    code: "TH-003",
    title: "TH-003 · Termohigrometro de referencia",
    kindLabel: "Termohigr",
    nominalClassLabel: "-",
    sourceLabel: "RBC-9876",
    certificateLabel: "9876/25/044",
    manufacturerLabel: "Testo",
    modelLabel: "TH-610",
    serialNumberLabel: "TH-610-44",
    nominalValueLabel: "Referencia ambiental",
    classLabel: "Instrumento auxiliar",
    usageRangeLabel: "18C-25C / 30%-70%",
    measurementValue: 22.4,
    applicableRangeMin: 18,
    applicableRangeMax: 25,
    uncertaintyLabel: "+/- 0,2 C / 1,5%",
    correctionFactorLabel: "Compensacao automatica ativa",
    hasValidCertificate: true,
    certificateValidUntil: parseDate("2026-06-30"),
    archivedAt: null,
  });

  await prisma.standardCalibration.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.standardCalibration.createMany({
    data: [
      calibration("00000000-0000-4000-8000-000000000801", STANDARD_IDS.peso1, "2025-08-12", "Lab Cal-1234", "1234/25/081", "RBC", "+/- 8 mg", "2026-08-12"),
      calibration("00000000-0000-4000-8000-000000000802", STANDARD_IDS.peso1, "2024-08-10", "Lab Cal-1234", "1234/24/063", "RBC", "+/- 8 mg", "2025-08-10"),
      calibration("00000000-0000-4000-8000-000000000803", STANDARD_IDS.peso2, "2025-08-12", "Lab Cal-1234", "1234/25/082", "RBC", "+/- 9 mg", "2026-08-12"),
      calibration("00000000-0000-4000-8000-000000000804", STANDARD_IDS.peso5, "2025-04-24", "Lab Cal-1234", "1234/25/088", "RBC", "+/- 12 mg", "2026-04-24"),
      calibration("00000000-0000-4000-8000-000000000805", STANDARD_IDS.peso5, "2024-04-14", "Lab Cal-1234", "1234/24/072", "RBC", "+/- 13 mg", "2025-04-14"),
      calibration("00000000-0000-4000-8000-000000000806", STANDARD_IDS.peso10, "2025-04-02", "Lab Cal-1234", "1234/25/099", "RBC", "+/- 18 mg", "2026-04-02"),
      calibration("00000000-0000-4000-8000-000000000807", STANDARD_IDS.thermo, "2025-06-30", "Lab Cal-9876", "9876/25/044", "RBC", "+/- 0,2 C / 1,5%", "2026-06-30"),
    ],
  });

  await upsertProcedure({
    id: PROCEDURE_IDS.pt005r04,
    code: "PT-005",
    title: "Calibracao IPNA classe III campo",
    typeLabel: "NAWI III",
    revisionLabel: "04",
    effectiveSince: parseDate("2024-03-01"),
    effectiveUntil: null,
    lifecycleLabel: "Vigente",
    usageLabel: "Campo controlado e bancada assistida",
    scopeLabel: "Balancas IPNA classe III em faixa ate 300 kg com 5 pontos de curva.",
    environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
    curvePolicyLabel: "5 pontos com sequencia crescente e decrescente.",
    standardsPolicyLabel: "Peso F1/M1 vigente + auxiliar ambiental TH-003 obrigatorio.",
    approvalLabel: "Aprovado por Ana Costa · vigencia desde 03/2024",
    relatedDocuments: [
      "IT-005-1 · Checklist de campo",
      "FR-021 · Registro bruto da curva",
      "BAL-UNC-IPNA-III · Balanco de incerteza",
    ],
    archivedAt: null,
  });

  await upsertProcedure({
    id: PROCEDURE_IDS.pt006r02,
    code: "PT-006",
    title: "Calibracao IPNA bancada",
    typeLabel: "NAWI",
    revisionLabel: "02",
    effectiveSince: parseDate("2023-11-01"),
    effectiveUntil: null,
    lifecycleLabel: "Vigente",
    usageLabel: "Bancada interna",
    scopeLabel: "Balancas NAWI de bancada com curva reduzida e controle ambiental interno.",
    environmentRangeLabel: "Temp 20C-24C · Umid 40%-60%",
    curvePolicyLabel: "4 pontos com repetibilidade em 50%.",
    standardsPolicyLabel: "Pesos F1/F2 vigentes conforme capacidade da balanca.",
    approvalLabel: "Aprovado por Ana Costa · vigencia desde 11/2023",
    relatedDocuments: ["IT-006-1 · Preparacao de bancada", "FR-022 · Registro de repetibilidade"],
    archivedAt: null,
  });

  await upsertProcedure({
    id: PROCEDURE_IDS.pt009r02,
    code: "PT-009",
    title: "Calibracao IPNA ambiente ampliado",
    typeLabel: "NAWI III especial",
    revisionLabel: "02",
    effectiveSince: parseDate("2024-02-01"),
    effectiveUntil: null,
    lifecycleLabel: "Vigente com revisao pendente",
    usageLabel: "Campo com condicoes variaveis",
    scopeLabel: "Balancas IPNA classe III com janela de ambiente ampliada e conferencia reforcada.",
    environmentRangeLabel: "Temp 18C-25C · Umid 30%-70% · revisao em curso",
    curvePolicyLabel: "5 pontos com checagem adicional de historico.",
    standardsPolicyLabel: "Padroes M1 vigentes e evidencia fotografica obrigatoria.",
    approvalLabel: "Revisao de qualidade aberta para abril/2026",
    relatedDocuments: [
      "IT-009-1 · Lista de desvios controlados",
      "FR-030 · Conferencia de historico",
      "NC-014 · Acao preventiva associada",
    ],
    archivedAt: null,
  });

  await upsertProcedure({
    id: PROCEDURE_IDS.pg001r01,
    code: "PG-001",
    title: "Controle de documentos",
    typeLabel: "Gestao",
    revisionLabel: "01",
    effectiveSince: parseDate("2024-01-01"),
    effectiveUntil: null,
    lifecycleLabel: "Vigente",
    usageLabel: "Governanca da qualidade",
    scopeLabel: "Documentos MQ/PG/PT/IT/FR com controle de vigencia e obsolescencia.",
    environmentRangeLabel: "Nao aplicavel",
    curvePolicyLabel: "Nao aplicavel",
    standardsPolicyLabel: "Nao aplicavel",
    approvalLabel: "Aprovado por Ana Costa · vigencia desde 01/2024",
    relatedDocuments: ["MQ-001 · Manual da qualidade", "IT-DOC-01 · Fluxo de publicacao"],
    archivedAt: null,
  });

  await upsertProcedure({
    id: PROCEDURE_IDS.pt005r03,
    code: "PT-005",
    title: "Calibracao IPNA classe III campo",
    typeLabel: "NAWI III",
    revisionLabel: "03",
    effectiveSince: parseDate("2023-09-01"),
    effectiveUntil: parseDate("2024-03-01"),
    lifecycleLabel: "Obsoleto",
    usageLabel: "Consulta historica apenas",
    scopeLabel: "Revisao mantida apenas para rastreabilidade historica de OS antigas.",
    environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
    curvePolicyLabel: "5 pontos historicos sem os ajustes documentados da rev. 04.",
    standardsPolicyLabel: "Padroes vigentes exigidos somente para consulta de historico.",
    approvalLabel: "Substituido pela rev. 04 em 03/2024",
    relatedDocuments: ["FR-021 rev.03 · Registro historico", "Ata de substituicao da rev. 04"],
    archivedAt: null,
  });

  await upsertEquipment({
    id: EQUIPMENT_IDS.eq0007,
    customerId: CUSTOMER_IDS.acme,
    procedureId: PROCEDURE_IDS.pt005r04,
    primaryStandardId: STANDARD_IDS.peso1,
    code: "EQ-0007",
    tagCode: "BAL-007",
    serialNumber: "SN-300-01",
    typeModelLabel: "NAWI Toledo Prix 3",
    capacityClassLabel: "300 kg · 0,05 kg · III",
    supportingStandardCodes: ["PESO-002", "TH-003"],
    addressLine1: "Rua da Calibracao, 100",
    addressCity: "Cuiaba",
    addressState: "MT",
    addressPostalCode: "78000-000",
    addressCountry: "Brasil",
    addressConditionsLabel: "Sala climatizada 21+/-2 C, acesso controlado.",
    lastCalibrationAt: parseDate("2026-04-18"),
    nextCalibrationAt: parseDate("2026-10-18"),
    archivedAt: null,
  });

  await upsertEquipment({
    id: EQUIPMENT_IDS.eq0012,
    customerId: CUSTOMER_IDS.acme,
    procedureId: PROCEDURE_IDS.pt006r02,
    primaryStandardId: STANDARD_IDS.peso2,
    code: "EQ-0012",
    tagCode: "BAL-012",
    serialNumber: "SN-300-12",
    typeModelLabel: "NAWI Toledo Prix 4",
    capacityClassLabel: "30 kg · 0,01 kg · III",
    supportingStandardCodes: ["TH-003"],
    addressLine1: "Rua da Calibracao, 100",
    addressCity: "Cuiaba",
    addressState: "MT",
    addressPostalCode: "78000-000",
    addressCountry: "Brasil",
    addressConditionsLabel: "Sala climatizada 21+/-2 C, acesso controlado.",
    lastCalibrationAt: parseDate("2026-04-18"),
    nextCalibrationAt: parseDate("2026-10-18"),
    archivedAt: null,
  });

  await upsertEquipment({
    id: EQUIPMENT_IDS.eq0011,
    customerId: CUSTOMER_IDS.paoDoce,
    procedureId: PROCEDURE_IDS.pt006r02,
    primaryStandardId: STANDARD_IDS.peso2,
    code: "EQ-0011",
    tagCode: "PAD-011",
    serialNumber: "SN-PD-011",
    typeModelLabel: "NAWI Urano Pop 30",
    capacityClassLabel: "30 kg · 0,01 kg · III",
    supportingStandardCodes: ["TH-003"],
    addressLine1: "Avenida do Comercio, 45",
    addressCity: "Cuiaba",
    addressState: "MT",
    addressPostalCode: "78005-010",
    addressCountry: "Brasil",
    addressConditionsLabel: "Atendimento antes das 6h para nao interromper a producao.",
    lastCalibrationAt: parseDate("2026-04-17"),
    nextCalibrationAt: parseDate("2026-10-17"),
    archivedAt: null,
  });

  await upsertEquipment({
    id: EQUIPMENT_IDS.eq0008,
    customerId: CUSTOMER_IDS.xyz,
    procedureId: PROCEDURE_IDS.pt009r02,
    primaryStandardId: STANDARD_IDS.peso5,
    code: "EQ-0008",
    tagCode: "BL-X-22",
    serialNumber: "SN-XY-22",
    typeModelLabel: "NAWI Marte L50",
    capacityClassLabel: "50 kg · 0,005 kg · III",
    supportingStandardCodes: ["TH-003"],
    addressLine1: "Distrito Industrial, 2200",
    addressCity: "Varzea Grande",
    addressState: "MT",
    addressPostalCode: "78110-500",
    addressCountry: "Brasil",
    addressConditionsLabel: "Acesso controlado e EPIs obrigatorios.",
    lastCalibrationAt: parseDate("2026-03-02"),
    nextCalibrationAt: parseDate("2026-05-02"),
    archivedAt: null,
  });

  await upsertEquipment({
    id: EQUIPMENT_IDS.eq0404,
    customerId: CUSTOMER_IDS.pendente,
    procedureId: PROCEDURE_IDS.pt009r02,
    primaryStandardId: STANDARD_IDS.peso10,
    code: "EQ-0404",
    tagCode: "BAL-404",
    serialNumber: "SN-C-500",
    typeModelLabel: "Balanca plataforma Marte 500",
    capacityClassLabel: "500 kg · 0,1 kg · III",
    supportingStandardCodes: ["TH-404"],
    addressLine1: "Rua Sem CEP, 10",
    addressCity: "Campo Grande",
    addressState: "MS",
    addressPostalCode: null,
    addressCountry: "Brasil",
    addressConditionsLabel: "Confirmacao documental em aberto.",
    lastCalibrationAt: parseDate("2026-04-19"),
    nextCalibrationAt: null,
    archivedAt: null,
  });

  await prisma.serviceOrder.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await upsertServiceOrder({
    id: SERVICE_ORDER_IDS.os142,
    customerId: CUSTOMER_IDS.acme,
    equipmentId: EQUIPMENT_IDS.eq0007,
    procedureId: PROCEDURE_IDS.pt005r04,
    primaryStandardId: STANDARD_IDS.peso1,
    executorUserId: TECHNICIAN_ID,
    reviewerUserId: SIGNATORY_ID,
    signatoryUserId: SIGNATORY_ID,
    workOrderNumber: "OS-2026-00142",
    workflowStatus: "awaiting_signature",
    environmentLabel: "22,1 C · 48% UR · pressao estavel",
    curvePointsLabel: "5 pontos (10% / 25% / 50% / 75% / 100%)",
    evidenceLabel: "12 evidencias anexadas",
    uncertaintyLabel: "U = 0,12 kg (k=2)",
    conformityLabel: "Aprovado com banda de guarda de 50%",
    measurementResultValue: 100.02,
    measurementExpandedUncertaintyValue: 0.12,
    measurementCoverageFactor: 2,
    measurementUnit: "kg",
    decisionRuleLabel: "ILAC G8 com banda de guarda de 50%",
    decisionOutcomeLabel: "Conforme",
    freeTextStatement: "Resultado apto para seguir para assinatura apos revisao tecnica concluida.",
    commentDraft: "Curva coerente com o historico do equipamento e pronta para revisao tecnica.",
    reviewDecision: "approved",
    reviewDecisionComment: "Checklist aprovado sem ressalvas impeditivas.",
    reviewDeviceId: "device-review-01",
    createdAt: new Date("2026-04-12T12:01:00.000Z"),
    acceptedAt: new Date("2026-04-12T12:15:00.000Z"),
    executionStartedAt: new Date("2026-04-19T14:00:00.000Z"),
    executedAt: new Date("2026-04-19T17:22:00.000Z"),
    reviewStartedAt: new Date("2026-04-23T11:30:00.000Z"),
    reviewCompletedAt: new Date("2026-04-23T11:48:00.000Z"),
    signatureStartedAt: null,
    signedAt: null,
    certificateNumber: null,
    certificateRevision: null,
    publicVerificationToken: null,
    documentHash: null,
    qrHost: null,
    signatureDeviceId: null,
    signatureStatement: null,
    emittedAt: null,
    archivedAt: null,
  });

  await upsertServiceOrder({
    id: SERVICE_ORDER_IDS.os141,
    customerId: CUSTOMER_IDS.paoDoce,
    equipmentId: EQUIPMENT_IDS.eq0011,
    procedureId: PROCEDURE_IDS.pt006r02,
    primaryStandardId: STANDARD_IDS.peso2,
    executorUserId: TECHNICIAN_ID,
    reviewerUserId: SIGNATORY_ID,
    signatoryUserId: SIGNATORY_ID,
    workOrderNumber: "OS-2026-00141",
    workflowStatus: "emitted",
    environmentLabel: "23,0 C · 52% UR · atendimento antes da abertura",
    curvePointsLabel: "4 pontos com repetibilidade em 50%",
    evidenceLabel: "11 evidencias registradas",
    uncertaintyLabel: "U = 0,08 kg (k=2)",
    conformityLabel: "Aprovado sem restricoes adicionais",
    measurementResultValue: 29.998,
    measurementExpandedUncertaintyValue: 0.08,
    measurementCoverageFactor: 2,
    measurementUnit: "kg",
    decisionRuleLabel: "ILAC G8 sem banda de guarda adicional",
    decisionOutcomeLabel: "Conforme",
    freeTextStatement: "Certificado emitido com base em revisao tecnica concluida e assinatura eletronica valida.",
    commentDraft: "Historico estavel e repetibilidade dentro do criterio de aceitacao.",
    reviewDecision: "approved",
    reviewDecisionComment: "Revisao aprovada e liberada para emissao oficial.",
    reviewDeviceId: "device-review-02",
    createdAt: new Date("2026-04-12T11:42:00.000Z"),
    acceptedAt: new Date("2026-04-12T12:03:00.000Z"),
    executionStartedAt: new Date("2026-04-19T13:10:00.000Z"),
    executedAt: new Date("2026-04-19T15:40:00.000Z"),
    reviewStartedAt: new Date("2026-04-20T08:40:00.000Z"),
    reviewCompletedAt: new Date("2026-04-20T09:10:00.000Z"),
    signatureStartedAt: new Date("2026-04-20T09:18:00.000Z"),
    signedAt: new Date("2026-04-20T09:22:00.000Z"),
    certificateNumber: "LABDEMO-000001",
    certificateRevision: "R0",
    publicVerificationToken: "pubtok-os141",
    documentHash: createHash("sha256").update("OS-2026-00141|LABDEMO-000001").digest("hex"),
    qrHost: "lab-demo.afere.local",
    signatureDeviceId: "device-sign-02",
    signatureStatement: "Assinatura eletronica concluida por Bruno Signatario.",
    emittedAt: new Date("2026-04-20T09:23:00.000Z"),
    archivedAt: null,
  });

  await upsertServiceOrder({
    id: SERVICE_ORDER_IDS.os147,
    customerId: CUSTOMER_IDS.pendente,
    equipmentId: EQUIPMENT_IDS.eq0404,
    procedureId: PROCEDURE_IDS.pt009r02,
    primaryStandardId: STANDARD_IDS.peso10,
    executorUserId: TECHNICIAN_ID,
    reviewerUserId: TECHNICIAN_ID,
    signatoryUserId: null,
    workOrderNumber: "OS-2026-00147",
    workflowStatus: "blocked",
    environmentLabel: "Faixa ambiental nao confirmada",
    curvePointsLabel: "Curva interrompida no terceiro ponto",
    evidenceLabel: "4 evidencias parciais",
    uncertaintyLabel: "Calculo bloqueado por padrao vencido",
    conformityLabel: "Bloqueado para revisao e emissao",
    measurementResultValue: null,
    measurementExpandedUncertaintyValue: null,
    measurementCoverageFactor: null,
    measurementUnit: null,
    decisionRuleLabel: "Fluxo fail-closed por padrao vencido e revisor conflitado",
    decisionOutcomeLabel: "Nao conforme",
    freeTextStatement: "OS bloqueada ate regularizacao do padrao principal e segregacao de funcoes.",
    commentDraft: "A OS precisa regularizar revisor segregado e padrao principal antes de prosseguir.",
    reviewDecision: "rejected",
    reviewDecisionComment: "Revisao rejeitada por conflito de papeis e padrao vencido.",
    reviewDeviceId: "device-review-03",
    createdAt: new Date("2026-04-18T11:10:00.000Z"),
    acceptedAt: new Date("2026-04-18T11:28:00.000Z"),
    executionStartedAt: new Date("2026-04-22T13:00:00.000Z"),
    executedAt: new Date("2026-04-22T13:42:00.000Z"),
    reviewStartedAt: new Date("2026-04-23T13:00:00.000Z"),
    reviewCompletedAt: null,
    signatureStartedAt: null,
    signedAt: null,
    certificateNumber: null,
    certificateRevision: null,
    publicVerificationToken: null,
    documentHash: null,
    qrHost: null,
    signatureDeviceId: null,
    signatureStatement: null,
    emittedAt: null,
    archivedAt: null,
  });

  await prisma.certificatePublication.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.certificatePublication.createMany({
    data: [
      {
        id: CERTIFICATE_PUBLICATION_IDS.os141r0,
        organizationId: ORGANIZATION_ID,
        serviceOrderId: SERVICE_ORDER_IDS.os141,
        certificateNumber: "LABDEMO-000001",
        revision: "R0",
        publicVerificationToken: "pubtok-os141",
        documentHash: createHash("sha256").update("OS-2026-00141|LABDEMO-000001").digest("hex"),
        qrHost: "lab-demo.afere.local",
        signedAt: new Date("2026-04-20T09:22:00.000Z"),
        issuedAt: new Date("2026-04-20T09:23:00.000Z"),
        supersededAt: null,
        replacementPublicationId: null,
        previousCertificateHash: null,
        notificationRecipient: null,
        notificationSentAt: null,
        reissueReason: null,
      },
    ],
  });

  await prisma.emissionAuditEvent.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.emissionAuditEvent.createMany({
    data: [
      ...emissionAuditTrail({
        serviceOrderId: SERVICE_ORDER_IDS.os142,
        events: [
          {
            id: "00000000-0000-4000-8000-000000001001",
            actorUserId: TECHNICIAN_ID,
            actorLabel: "Carla Tecnica",
            action: "calibration.executed",
            entityLabel: "OS-2026-00142",
            occurredAt: "2026-04-19T17:22:00.000Z",
          },
          {
            id: "00000000-0000-4000-8000-000000001002",
            actorUserId: SIGNATORY_ID,
            actorLabel: "Bruno Signatario",
            action: "technical_review.completed",
            entityLabel: "OS-2026-00142",
            deviceId: "device-review-01",
            occurredAt: "2026-04-23T11:48:00.000Z",
          },
        ],
      }),
      ...emissionAuditTrail({
        serviceOrderId: SERVICE_ORDER_IDS.os141,
        events: [
          {
            id: "00000000-0000-4000-8000-000000001003",
            actorUserId: TECHNICIAN_ID,
            actorLabel: "Carla Tecnica",
            action: "calibration.executed",
            entityLabel: "OS-2026-00141",
            occurredAt: "2026-04-19T15:40:00.000Z",
          },
          {
            id: "00000000-0000-4000-8000-000000001004",
            actorUserId: SIGNATORY_ID,
            actorLabel: "Bruno Signatario",
            action: "technical_review.completed",
            entityLabel: "OS-2026-00141",
            deviceId: "device-review-02",
            occurredAt: "2026-04-20T09:10:00.000Z",
          },
          {
            id: "00000000-0000-4000-8000-000000001005",
            actorUserId: SIGNATORY_ID,
            actorLabel: "Bruno Signatario",
            action: "certificate.signed",
            entityLabel: "OS-2026-00141",
            deviceId: "device-sign-02",
            certificateNumber: "LABDEMO-000001",
            occurredAt: "2026-04-20T09:22:00.000Z",
          },
          {
            id: "00000000-0000-4000-8000-000000001006",
            actorUserId: SIGNATORY_ID,
            actorLabel: "Bruno Signatario",
            action: "certificate.emitted",
            entityLabel: "OS-2026-00141",
            deviceId: "device-sign-02",
            certificateNumber: "LABDEMO-000001",
            occurredAt: "2026-04-20T09:23:00.000Z",
          },
        ],
      }),
      ...emissionAuditTrail({
        serviceOrderId: SERVICE_ORDER_IDS.os147,
        events: [
          {
            id: "00000000-0000-4000-8000-000000001007",
            actorUserId: TECHNICIAN_ID,
            actorLabel: "Carla Tecnica",
            action: "calibration.executed",
            entityLabel: "OS-2026-00147",
            occurredAt: "2026-04-22T13:42:00.000Z",
          },
          {
            id: "00000000-0000-4000-8000-000000001008",
            actorUserId: TECHNICIAN_ID,
            actorLabel: "Carla Tecnica",
            action: "technical_review.rejected",
            entityLabel: "OS-2026-00147",
            deviceId: "device-review-03",
            occurredAt: "2026-04-23T13:12:00.000Z",
          },
        ],
      }),
    ],
  });

  await prisma.managementReviewMeeting.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.internalAuditCycle.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.nonconformingWorkCase.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.nonconformity.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.qualityIndicatorSnapshot.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.organizationComplianceProfile.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.nonconformity.createMany({
    data: [
      {
        id: QUALITY_IDS.nc014,
        organizationId: ORGANIZATION_ID,
        serviceOrderId: SERVICE_ORDER_IDS.os147,
        ownerUserId: ADMIN_ID,
        title: "NC-014 · Revisor conflitado e padrao vencido na OS bloqueada",
        originLabel: "Revisao tecnica",
        severityLabel: "Critica",
        status: "blocked",
        noticeLabel: "A OS permanece bloqueada ate segregar funcoes e regularizar o padrao principal.",
        rootCauseLabel: "Atribuicao inadequada de papeis somada a uso de padrao fora da validade.",
        containmentLabel: "Suspender qualquer liberacao da OS-2026-00147 e reabrir a designacao de revisor.",
        correctiveActionLabel: "Substituir o revisor, recalibrar o padrao e registrar nova conferencia tecnica.",
        evidenceLabel: "OS-2026-00147, trilha append-only e parecer inicial da Qualidade.",
        blockers: ["Segregacao de funcoes pendente", "Padrao principal vencido"],
        warnings: ["Nao emitir certificado ate fechar a NC."],
        openedAt: new Date("2026-04-23T13:20:00.000Z"),
        dueAt: new Date("2026-04-30T17:00:00.000Z"),
        resolvedAt: null,
      },
    ],
  });

  await prisma.nonconformingWorkCase.createMany({
    data: [
      {
        id: QUALITY_IDS.ncw014,
        organizationId: ORGANIZATION_ID,
        serviceOrderId: SERVICE_ORDER_IDS.os147,
        nonconformityId: QUALITY_IDS.nc014,
        title: "NCW-014 · Contencao da OS-2026-00147",
        classificationLabel: "Contencao preventiva",
        originLabel: "OS bloqueada",
        affectedEntityLabel: "OS-2026-00147",
        status: "blocked",
        noticeLabel: "Liberacao do fluxo bloqueada ate nova evidencia minima.",
        containmentLabel: "Manter a OS congelada e impedir reemissao ou assinatura associada.",
        releaseRuleLabel: "Somente liberar apos NC encerrada e revisor segregado.",
        evidenceLabel: "Registro da NC-014, trilha de revisao rejeitada e anotacao da Qualidade.",
        restorationLabel: "Retomar a OS apenas com novo revisor, padrao valido e checklist refeito.",
        blockers: ["NC-014 aberta", "Fluxo tecnico ainda sem evidencia de restauracao"],
        warnings: ["Nao substituir a contencao por acordo verbal."],
      },
    ],
  });

  await prisma.internalAuditCycle.createMany({
    data: [
      {
        id: QUALITY_IDS.audit2026q2,
        organizationId: ORGANIZATION_ID,
        cycleLabel: "Programa 2026 · Ciclo 2",
        windowLabel: "Q2 2026",
        scopeLabel: "§7.8 Certificados | §8.8 Auditoria interna | §7.10 Trabalho nao conforme",
        auditorLabel: "Ana Administradora",
        auditeeLabel: "Operacoes e Qualidade",
        periodLabel: "Abr-Jun 2026",
        reportLabel: "Relatorio parcial do ciclo 2 em follow-up",
        evidenceLabel: "Checklist do ciclo, NC-014 e trilha da OS-2026-00147.",
        nextReviewLabel: "05/05/2026 13:00 UTC",
        noticeLabel: "O ciclo permanece aberto ate concluir o follow-up da NC critica.",
        status: "attention",
        checklistItems: [
          {
            key: "certificates",
            requirementLabel: "Certificados emitidos e bloqueados com evidencias rastreaveis",
            evidenceLabel: "service_orders + emission_audit_events",
            status: "attention",
          },
          {
            key: "nonconforming-work",
            requirementLabel: "Contencao formal do trabalho nao conforme",
            evidenceLabel: "nonconforming_work_cases + NC-014",
            status: "blocked",
          },
        ],
        findingRefs: [QUALITY_IDS.nc014],
        blockers: ["NC critica ainda sem encerramento"],
        warnings: ["Nao abrir novo ciclo sem concluir o follow-up atual."],
        scheduledAt: new Date("2026-04-24T14:00:00.000Z"),
        completedAt: null,
      },
    ],
  });

  await prisma.managementReviewMeeting.createMany({
    data: [
      {
        id: QUALITY_IDS.review2026q2,
        organizationId: ORGANIZATION_ID,
        titleLabel: "Analise critica Q2 2026",
        status: "attention",
        dateLabel: "30/06/2026",
        outcomeLabel: "Pauta aberta com follow-up de Qualidade",
        noticeLabel: "A ata final depende do fechamento minimo da NC critica e do ciclo de auditoria.",
        nextMeetingLabel: "30/09/2026",
        chairLabel: "Ana Administradora",
        attendeesLabel: "Direcao, Qualidade e Metrologia",
        periodLabel: "Q2 2026",
        ataLabel: "Ata em preparacao",
        evidenceLabel: "Indicadores V5, NC-014, ciclo 2 de auditoria e perfil regulatorio persistido.",
        agendaItems: [
          { key: "agenda-nc", label: "NCs e trabalho nao conforme", status: "attention" },
          { key: "agenda-audit", label: "Follow-up da auditoria interna", status: "attention" },
          { key: "agenda-regulatory", label: "Governanca regulatoria e release-norm V5", status: "ready" },
        ],
        decisions: [
          {
            key: "decision-close-nc",
            label: "Encerrar NC-014 com evidencias minimas",
            ownerLabel: "Ana Administradora",
            dueDateLabel: "05/05/2026",
            status: "attention",
          },
        ],
        blockers: [],
        warnings: ["A ata nao deve ser arquivada antes do follow-up minimo da NC."],
        scheduledFor: new Date("2026-06-30T13:00:00.000Z"),
        heldAt: null,
      },
    ],
  });

  await prisma.qualityIndicatorSnapshot.createMany({
    data: [
      ...indicatorHistorySeed({
        indicatorId: "indicator-emission-completion",
        targetNumeric: 85,
        sourcePrefix: "Fechamento mensal emissao",
        evidenceLabel: "Consolidado gerencial do fluxo emitido.",
        points: [
          ["2025-11-01", 62, "attention"],
          ["2025-12-01", 68, "attention"],
          ["2026-01-01", 72, "attention"],
          ["2026-02-01", 79, "attention"],
          ["2026-03-01", 81, "attention"],
          ["2026-04-01", 84, "attention"],
        ],
      }),
      ...indicatorHistorySeed({
        indicatorId: "indicator-open-nc-pressure",
        targetNumeric: 1,
        sourcePrefix: "Fechamento mensal NC",
        evidenceLabel: "Consolidado mensal de nao conformidades.",
        points: [
          ["2025-11-01", 3, "blocked"],
          ["2025-12-01", 3, "blocked"],
          ["2026-01-01", 2, "attention"],
          ["2026-02-01", 2, "attention"],
          ["2026-03-01", 1, "ready"],
          ["2026-04-01", 1, "ready"],
        ],
      }),
      ...indicatorHistorySeed({
        indicatorId: "indicator-governance-follow-up",
        targetNumeric: 1,
        sourcePrefix: "Fechamento mensal follow-up",
        evidenceLabel: "Consolidado mensal de follow-up gerencial.",
        points: [
          ["2025-11-01", 4, "blocked"],
          ["2025-12-01", 3, "blocked"],
          ["2026-01-01", 3, "blocked"],
          ["2026-02-01", 2, "attention"],
          ["2026-03-01", 2, "attention"],
          ["2026-04-01", 1, "ready"],
        ],
      }),
    ],
  });

  await prisma.organizationComplianceProfile.create({
    data: {
      id: QUALITY_IDS.complianceProfile,
      organizationId: ORGANIZATION_ID,
      organizationCode: "AFERE",
      planLabel: "Enterprise",
      certificatePrefix: "LABDEMO",
      accreditationNumber: "Cgcre CAL-1234",
      accreditationValidUntil: parseDate("2027-09-30"),
      scopeSummary: "Balancas NAWI/IPNA em escopo interno controlado para o tenant demo.",
      cmcSummary: "CMC minima revisada para a familia principal de balancas do tenant.",
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
      lastReviewedAt: new Date("2026-04-23T20:30:00.000Z"),
    },
  });

  await prisma.registryAuditEvent.deleteMany({
    where: { organizationId: ORGANIZATION_ID },
  });

  await prisma.registryAuditEvent.createMany({
    data: [
      auditEvent("00000000-0000-4000-8000-000000000901", "user", ADMIN_ID, "create", "Usuario administrador bootstrapado para o tenant demo.", ADMIN_ID, "2026-04-23T12:05:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000902", "user", SIGNATORY_ID, "update", "Competencia de assinatura revisada para o recorte de balancas.", ADMIN_ID, "2026-04-23T12:18:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000903", "customer", CUSTOMER_IDS.acme, "update", "Endereco operacional e contrato revisados para 2026.", ADMIN_ID, "2026-04-23T13:02:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000904", "customer", CUSTOMER_IDS.xyz, "update", "Janela operacional noturna validada com o responsavel do cliente.", ADMIN_ID, "2026-04-23T13:20:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000905", "customer", CUSTOMER_IDS.pendente, "create", "Cadastro em homologacao aberto com endereco ainda pendente.", ADMIN_ID, "2026-04-23T13:36:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000906", "standard", STANDARD_IDS.peso5, "update", "Padrao entrou em janela preventiva de recalibracao.", SIGNATORY_ID, "2026-04-23T14:10:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000907", "standard", STANDARD_IDS.peso10, "update", "Padrao vencido removido da agenda futura.", SIGNATORY_ID, "2026-04-23T14:22:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000908", "procedure", PROCEDURE_IDS.pt009r02, "update", "Revisao preventiva aberta pela Qualidade.", ADMIN_ID, "2026-04-23T14:44:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000909", "procedure", PROCEDURE_IDS.pt005r03, "archive", "Revisao antiga mantida apenas para consulta historica.", ADMIN_ID, "2026-04-23T14:55:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000910", "equipment", EQUIPMENT_IDS.eq0007, "update", "Vinculo principal com padrao e procedimento confirmado.", TECHNICIAN_ID, "2026-04-23T15:08:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000911", "equipment", EQUIPMENT_IDS.eq0008, "update", "Proxima calibracao entrou em janela de atencao.", TECHNICIAN_ID, "2026-04-23T15:22:00.000Z"),
      auditEvent("00000000-0000-4000-8000-000000000912", "equipment", EQUIPMENT_IDS.eq0404, "create", "Equipamento bloqueado aguardando endereco minimo completo.", TECHNICIAN_ID, "2026-04-23T15:40:00.000Z"),
    ],
  });

  await prisma.appSession.deleteMany({
    where: { organizationId: ORGANIZATION_ID, expiresAt: { lt: new Date() } },
  });
}

async function upsertUser(input: {
  id: string;
  email: string;
  displayName: string;
  roles: string[];
  teamName: string;
  status: string;
  mfaEnforced: boolean;
  mfaEnrolled: boolean;
  deviceCount: number;
  passwordHash: string;
}) {
  await prisma.appUser.upsert({
    where: { id: input.id },
    create: {
      id: input.id,
      organizationId: ORGANIZATION_ID,
      email: input.email,
      passwordHash: input.passwordHash,
      displayName: input.displayName,
      roles: input.roles,
      status: input.status,
      teamName: input.teamName,
      mfaEnforced: input.mfaEnforced,
      mfaEnrolled: input.mfaEnrolled,
      deviceCount: input.deviceCount,
      lastLoginAt: input.status === "active" ? new Date("2026-04-23T13:00:00.000Z") : null,
    },
    update: {
      email: input.email,
      passwordHash: input.passwordHash,
      displayName: input.displayName,
      roles: input.roles,
      status: input.status,
      teamName: input.teamName,
      mfaEnforced: input.mfaEnforced,
      mfaEnrolled: input.mfaEnrolled,
      deviceCount: input.deviceCount,
      lastLoginAt: input.status === "active" ? new Date("2026-04-23T13:00:00.000Z") : null,
    },
  });
}

async function upsertCustomer(input: {
  id: string;
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
  archivedAt: Date | null;
}) {
  const { id, ...data } = input;
  await prisma.customer.upsert({
    where: { id },
    create: {
      id,
      organizationId: ORGANIZATION_ID,
      ...data,
    },
    update: {
      ...data,
    },
  });
}

async function upsertStandard(input: {
  id: string;
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
  hasValidCertificate: boolean;
  certificateValidUntil: Date | null;
  archivedAt: Date | null;
}) {
  const { id, ...data } = input;
  await prisma.standard.upsert({
    where: { id },
    create: {
      id,
      organizationId: ORGANIZATION_ID,
      ...data,
    },
    update: {
      ...data,
    },
  });
}

async function upsertProcedure(input: {
  id: string;
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
  archivedAt: Date | null;
}) {
  const { id, ...data } = input;
  await prisma.procedureRevision.upsert({
    where: { id },
    create: {
      id,
      organizationId: ORGANIZATION_ID,
      ...data,
    },
    update: {
      ...data,
    },
  });
}

async function upsertEquipment(input: {
  id: string;
  customerId: string;
  procedureId: string | null;
  primaryStandardId: string | null;
  code: string;
  tagCode: string;
  serialNumber: string;
  typeModelLabel: string;
  capacityClassLabel: string;
  supportingStandardCodes: string[];
  addressLine1: string;
  addressCity: string;
  addressState: string;
  addressPostalCode: string | null;
  addressCountry: string;
  addressConditionsLabel: string | null;
  lastCalibrationAt: Date | null;
  nextCalibrationAt: Date | null;
  archivedAt: Date | null;
}) {
  const { id, ...data } = input;
  await prisma.equipment.upsert({
    where: { id },
    create: {
      id,
      organizationId: ORGANIZATION_ID,
      ...data,
    },
    update: {
      ...data,
    },
  });
}

async function upsertServiceOrder(input: {
  id: string;
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
  archivedAt: Date | null;
}) {
  const { id, ...data } = input;
  await prisma.serviceOrder.upsert({
    where: { id },
    create: {
      id,
      organizationId: ORGANIZATION_ID,
      ...data,
    },
    update: {
      ...data,
    },
  });
}

function emissionAuditTrail(input: {
  serviceOrderId: string;
  events: Array<{
    id: string;
    actorUserId: string | null;
    actorLabel: string;
    action: string;
    entityLabel: string;
    deviceId?: string;
    certificateNumber?: string;
    occurredAt: string;
  }>;
}) {
  let prevHash = GENESIS_HASH;

  return input.events.map((event) => {
    const payload = {
      action: event.action,
      actorId: event.actorUserId,
      actorLabel: event.actorLabel,
      certificateId: input.serviceOrderId,
      certificateNumber: event.certificateNumber,
      entityLabel: event.entityLabel,
      timestampUtc: event.occurredAt,
      deviceId: event.deviceId,
    };
    const hash = computeSeedAuditHash(prevHash, payload);
    const row = {
      id: event.id,
      organizationId: ORGANIZATION_ID,
      serviceOrderId: input.serviceOrderId,
      actorUserId: event.actorUserId,
      action: event.action,
      actorLabel: event.actorLabel,
      entityLabel: event.entityLabel,
      deviceId: event.deviceId ?? null,
      certificateNumber: event.certificateNumber ?? null,
      prevHash,
      hash,
      occurredAt: new Date(event.occurredAt),
    };

    prevHash = hash;
    return row;
  });
}

function computeSeedAuditHash(prevHash: string, payload: unknown) {
  return createHash("sha256").update(prevHash).update(canonicalJson(payload)).digest("hex");
}

function canonicalJson(value: unknown) {
  return JSON.stringify(canonicalize(value));
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => canonicalize(item));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, item]) => [key, canonicalize(item)]),
    );
  }

  return value;
}

function indicatorHistorySeed(input: {
  indicatorId: string;
  targetNumeric: number;
  sourcePrefix: string;
  evidenceLabel: string;
  points: Array<[monthStart: string, valueNumeric: number, status: "ready" | "attention" | "blocked"]>;
}) {
  return input.points.map(([monthStart, valueNumeric, status], index) => ({
    id: `00000000-0000-4000-8000-${createHash("sha256")
      .update(`${input.indicatorId}:${monthStart}:${index}`)
      .digest("hex")
      .slice(0, 12)}`,
    organizationId: ORGANIZATION_ID,
    indicatorId: input.indicatorId,
    monthStart: parseDate(monthStart),
    valueNumeric,
    targetNumeric: input.targetNumeric,
    status,
    sourceLabel: `${input.sourcePrefix} ${monthStart.slice(5, 7)}/${monthStart.slice(0, 4)}`,
    evidenceLabel: input.evidenceLabel,
  }));
}

function calibration(
  id: string,
  standardId: string,
  calibratedAt: string,
  laboratoryLabel: string,
  certificateLabel: string,
  sourceLabel: string,
  uncertaintyLabel: string,
  validUntil: string,
) {
  return {
    id,
    organizationId: ORGANIZATION_ID,
    standardId,
    calibratedAt: parseDate(calibratedAt),
    laboratoryLabel,
    certificateLabel,
    sourceLabel,
    uncertaintyLabel,
    validUntil: parseDate(validUntil),
  };
}

function auditEvent(
  id: string,
  entityType: string,
  entityId: string,
  action: string,
  summary: string,
  actorUserId: string | null,
  createdAt: string,
) {
  return {
    id,
    organizationId: ORGANIZATION_ID,
    entityType,
    entityId,
    action,
    actorUserId,
    summary,
    createdAt: new Date(createdAt),
  };
}

function parseDate(value: string) {
  return new Date(`${value}T00:00:00.000Z`);
}

function hashSeedPassword(password: string): string {
  const salt = "afere-v2-seed";
  const derived = scryptSync(password, salt, 64, {
    N: 16384,
    r: 8,
    p: 1,
    maxmem: 64 * 1024 * 1024,
  }).toString("base64url");

  return `scrypt:v1:16384:8:1:${salt}:${derived}`;
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });
