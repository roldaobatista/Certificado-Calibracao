import { scryptSync } from "node:crypto";

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const ORGANIZATION_ID = "00000000-0000-4000-8000-000000000101";
const ADMIN_ID = "00000000-0000-4000-8000-000000000201";
const SIGNATORY_ID = "00000000-0000-4000-8000-000000000202";
const TECHNICIAN_ID = "00000000-0000-4000-8000-000000000203";
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
        validUntil: new Date("2027-04-20T00:00:00.000Z"),
      },
      {
        id: "00000000-0000-4000-8000-000000000302",
        organizationId: ORGANIZATION_ID,
        userId: SIGNATORY_ID,
        instrumentType: "balanca",
        roleLabel: "Revisor tecnico",
        status: "authorized",
        validUntil: new Date("2027-01-20T00:00:00.000Z"),
      },
      {
        id: "00000000-0000-4000-8000-000000000303",
        organizationId: ORGANIZATION_ID,
        userId: TECHNICIAN_ID,
        instrumentType: "balanca",
        roleLabel: "Executor de campo",
        status: "authorized",
        validUntil: new Date("2026-12-20T00:00:00.000Z"),
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
      status: "active",
      teamName: input.teamName,
      mfaEnforced: input.mfaEnforced,
      mfaEnrolled: input.mfaEnrolled,
      deviceCount: input.deviceCount,
      lastLoginAt: new Date("2026-04-23T13:00:00.000Z"),
    },
    update: {
      email: input.email,
      passwordHash: input.passwordHash,
      displayName: input.displayName,
      roles: input.roles,
      status: "active",
      teamName: input.teamName,
      mfaEnforced: input.mfaEnforced,
      mfaEnrolled: input.mfaEnrolled,
      deviceCount: input.deviceCount,
    },
  });
}

function hashSeedPassword(password: string): string {
  const salt = "afere-v1-seed";
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
