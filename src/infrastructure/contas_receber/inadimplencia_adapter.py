"""Adapter real de `InadimplenciaSource` (Fatia 3b — T-CR-043 / TL-CR-01 / D-CR-9).

Substitui o `SourceListaInterim` do módulo `clientes`: itera `Titulo` com estado
`vencido` aplicando o grace por perfil regulatório do tenant (45/20/30/7 —
`grace_period_por_perfil`). Só entra na lista de inadimplência dura o título cujo
`data_vencimento + grace_do_perfil <= hoje` (D-CR-9 / INV-FIN-GRACE-PERFIL-001).

**PULL, não PUSH** (TL-CR-01 / R1): o job de bloqueio existente em `clientes`
(`job_inadimplencia_alertas`) consome este source via `get_source()` parametrizado
por `settings.INADIMPLENCIA_SOURCE_IMPL = "contas_receber"`. O grace usa o perfil
ATUAL do tenant (D-CR-9 — política corrente de inadimplência, não snapshot).

O método do Protocol chama-se `iter_inadimplentes_90d` por compat (nome legado do
módulo `clientes`); a lógica real é grace-por-perfil, não 90 dias fixos.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from uuid import UUID

from src.domain.comercial.clientes.inadimplencia_source import InadimplenciaItem
from src.domain.contas_receber.grace import grace_period_por_perfil


def grace_period_inadimplencia_por_perfil(tenant_id: UUID) -> int:
    """Grace de inadimplência (dias) do perfil ATUAL do tenant (D-CR-9).

    Wrapper de infra do predicate puro `grace_period_por_perfil` (45/20/30/7).
    Fail-closed: tenant inexistente / perfil inválido → `PerfilIndeterminado`.
    """
    from src.infrastructure.tenant.models import Tenant

    tenant = Tenant.objects.filter(id=tenant_id).only("perfil_regulatorio").first()
    if tenant is None:
        from src.domain.contas_receber.erros import PerfilIndeterminado

        raise PerfilIndeterminado(
            f"grace_period_inadimplencia_por_perfil: tenant {tenant_id} inexistente "
            "— fail-closed."
        )
    return grace_period_por_perfil(tenant.perfil_regulatorio)


class TituloVencidoInadimplenciaSource:
    """Implementa o Protocol `InadimplenciaSource` (clientes) lendo `Titulo` vencido.

    Coleta os items de TODOS os tenants em `run_in_tenant_context` (RLS por tenant)
    e retorna um iterator sobre a lista materializada — NÃO faz `yield` dentro do
    contexto (o job consumidor entra em `run_in_tenant_context` por item depois;
    `yield` dentro do contexto causaria aninhamento proibido pelo worker).
    """

    def iter_inadimplentes_90d(self) -> Iterator[InadimplenciaItem]:
        from src.infrastructure.multitenant.jobs import processar_em_contexto_tenant

        resultados = processar_em_contexto_tenant(self._coletar_do_tenant)
        items: list[InadimplenciaItem] = []
        for lista in resultados.values():
            items.extend(lista)
        return iter(items)

    @staticmethod
    def _coletar_do_tenant(tenant: object) -> list[InadimplenciaItem]:
        from src.infrastructure.contas_receber.models import Titulo as TituloModel

        perfil = tenant.perfil_regulatorio  # type: ignore[attr-defined]
        tenant_id = tenant.id  # type: ignore[attr-defined]
        grace = grace_period_por_perfil(perfil)
        hoje = date.today()
        coletados: list[InadimplenciaItem] = []
        # cliente_atual_id NULL = cliente anonimizado (LGPD) → fora da régua de bloqueio.
        qs = TituloModel.objects.filter(
            estado="vencido", cliente_atual_id__isnull=False
        ).only("id", "cliente_atual_id", "data_vencimento")
        for t in qs:
            cliente_atual_id = t.cliente_atual_id
            if cliente_atual_id is None:  # queryset já filtra; narrowing type-safe + defesa
                continue
            dias_vencido = (hoje - t.data_vencimento).days
            if dias_vencido >= grace:
                coletados.append(
                    InadimplenciaItem(
                        tenant_id=tenant_id,
                        cliente_id=cliente_atual_id,
                        dias_vencido=dias_vencido,
                        causation_titulo_id=t.id,
                        perfil=perfil,
                        grace_perfil=grace,
                    )
                )
        return coletados
