import { type PrismaClient } from "@prisma/client";

/**
 * SQL para configurar o tenant context no Postgres.
 *
 * Deve ser executado como primeira operação de uma transação,
 * antes de qualquer query multitenant.
 */
export function tenantContextSql(organizationId: string): string {
  return `SELECT set_config('app.current_organization_id', '${organizationId.replace(/'/g, "''")}', true)`;
}

/**
 * Tenant context transacional para RLS.
 *
 * Executa `SET LOCAL app.current_organization_id` dentro de uma transação Prisma,
 * garantindo que as policies RLS do Postgres sejam exercitadas corretamente.
 *
 * Regra: toda operação de leitura/escrita multitenant deve usar este wrapper.
 * Acesso direto ao PrismaClient em persistências multitenant é proibido.
 */
export async function withTenant<T>(
  prisma: PrismaClient,
  organizationId: string,
  fn: (tx: PrismaClient) => Promise<T>,
): Promise<T> {
  return prisma.$transaction(async (tx) => {
    await tx.$executeRawUnsafe(tenantContextSql(organizationId));
    return fn(tx as unknown as PrismaClient);
  });
}

/**
 * Wrapper de persistência que exige tenant context.
 *
 * Usado para bloquear acesso direto ao PrismaClient em camadas de domínio
 * que operam sobre dados multitenant.
 */
export type TenantPrismaClient = PrismaClient;
