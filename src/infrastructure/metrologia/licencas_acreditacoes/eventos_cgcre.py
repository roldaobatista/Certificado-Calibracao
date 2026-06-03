"""Adapter Django da porta `AplicarEventoCgcrePort` (M9 T-LIC-041 / D-LIC-4).

Invoca a função SECURITY DEFINER `aplicar_evento_cgcre` (migration tenant/0012,
direção `promocao_regulatoria`) via raw cursor — única forma de mutar
`Tenant.perfil`/`acreditacao_*` (INV-LIC-VIG-SYNC-001). Roda DENTRO do
`transaction.atomic` aberto pelo caller (a função faz advisory lock por tenant). O
14º parâmetro `p_acreditacao_vigencia_fim` grava o cache que o M8 lê (D-LIC-2 →
fecha GATE-CER-CGCRE-VIG-DATA-POPULAR). Named params (`=>`) — backward-compat.

# audit-immutability: skip -- caminho oficial ADR-0067 de mutação de perfil (função
# SECURITY DEFINER canônica); não altera trilha de auditoria, apenas a invoca.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db import connection


class DjangoAplicarEventoCgcre:
    """Implementa `AplicarEventoCgcrePort.promover` (D-LIC-4) e
    `RenovarVigenciaCgcrePort.renovar_vigencia` (D-LIC-3 / T-LIC-050) via
    `aplicar_evento_cgcre`."""

    def renovar_vigencia(
        self, *, tenant_id: UUID, vigencia_fim: date, motivo: str
    ) -> None:
        """Direção `renovacao_vigencia_cgcre` — avança o cache
        `Tenant.acreditacao_vigencia_fim` SEM mudar o perfil (permanece A). Não emite
        outbox (consolida no relatório trimestral). Roda na transação do caller."""
        with connection.cursor() as cur:
            cur.execute(
                "SELECT aplicar_evento_cgcre("
                "p_direcao => %s, p_tenant_id => %s, p_perfil_novo => %s, "
                "p_motivo => %s, p_acreditacao_vigencia_fim => %s)",
                [
                    "renovacao_vigencia_cgcre",
                    str(tenant_id),
                    "A",
                    motivo,
                    vigencia_fim,
                ],
            )

    def promover(
        self,
        *,
        tenant_id: UUID,
        perfil_novo: str,
        motivo: str,
        documento_cgcre_id: UUID,
        assinatura_a3_id: UUID,
        registrado_por_id: UUID,
        auditor_cgcre: str | None,
        numero_rbc: str,
        ilac_mra_aderido: bool,
        vigencia_fim: date,
    ) -> None:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT aplicar_evento_cgcre("
                "p_direcao => %s, p_tenant_id => %s, p_perfil_novo => %s, "
                "p_motivo => %s, p_auditor_cgcre => %s, p_documento_cgcre_id => %s, "
                "p_registrado_por_id => %s, p_assinatura_a3_id => %s, "
                "p_numero_rbc => %s, p_ilac_mra_aderido => %s, "
                "p_acreditacao_vigencia_fim => %s)",
                [
                    "promocao_regulatoria",
                    str(tenant_id),
                    perfil_novo,
                    motivo,
                    auditor_cgcre,
                    str(documento_cgcre_id),
                    str(registrado_por_id),
                    str(assinatura_a3_id),
                    numero_rbc or None,
                    ilac_mra_aderido,
                    vigencia_fim,
                ],
            )
