"""Adapter Django do Protocol `TituloRepository` (Fatia 1b, T-CR-021 — ADR-0007).

Implementa o repository do domínio sobre o ORM. Concorrência garantida pelo
advisory lock da view + triggers one-shot do banco (`data_baixa`/`cancelado_em`),
NÃO por CAS. O trigger WORM permite só transição de `estado`/timestamps/dados
de cobrança; campos probatórios são imutáveis. Consumido pelos use cases (Fatia 2).
NÃO é singleton.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from django.db import models

from src.domain.contas_receber.entities import (
    OverrideBloqueio,
    Pagamento,
    Parcela,
    Titulo,
)
from src.infrastructure.contas_receber import mappers
from src.infrastructure.contas_receber.models import (
    OverrideBloqueio as OverrideBloqueioModel,
)
from src.infrastructure.contas_receber.models import Pagamento as PagamentoModel
from src.infrastructure.contas_receber.models import Parcela as ParcelaModel
from src.infrastructure.contas_receber.models import Titulo as TituloModel


class DjangoTituloRepository:
    """Adapter ORM da raiz Titulo (implementa o Protocol TituloRepository do domínio)."""

    # --- Titulo ---

    def obter_por_id(self, *, tenant_id: UUID, titulo_id: UUID) -> Titulo | None:
        m = TituloModel.objects.filter(tenant_id=tenant_id, id=titulo_id).first()
        return mappers.model_para_titulo(m) if m is not None else None

    def existe_titulo_ativo_para_os(self, *, tenant_id: UUID, os_id: UUID) -> bool:
        """Verifica se já existe título ativo (não cancelado) para a OS (INV-CR-OS-TITULO-UNICO)."""
        return (
            TituloModel.objects.filter(
                tenant_id=tenant_id,
                os_id_origem=os_id,
            )
            .exclude(estado="cancelado")
            .exists()
        )

    def salvar_novo_titulo(self, titulo: Titulo) -> None:
        campos = mappers.titulo_para_campos(titulo)
        TituloModel.objects.create(
            id=titulo.titulo_id,
            tenant_id=titulo.tenant_id,
            **campos,
        )

    def atualizar_titulo(self, *, tenant_id: UUID, titulo: Titulo) -> None:
        """Transição de estado e campos mutáveis. `revision` bumpa por expressão.

        `cancelado_em` NÃO é campo da entidade Titulo (é só-PG); Fatia 2 usa
        SQL direto para gravar estado=cancelado + cancelado_em atomicamente.
        """
        atualizadas = TituloModel.objects.filter(tenant_id=tenant_id, id=titulo.titulo_id).update(
            estado=titulo.estado.value,
            data_baixa=titulo.data_baixa,
            gateway_externo_id=titulo.gateway_externo_id or "",
            linha_digitavel=titulo.linha_digitavel or "",
            qr_code=titulo.qr_code or "",
            tx_id=titulo.tx_id or "",
            revision=models.F("revision") + 1,
        )
        if atualizadas != 1:
            raise RuntimeError(
                f"atualizar_titulo: esperava 1 linha, afetou {atualizadas} "
                f"(titulo {titulo.titulo_id})."
            )

    def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        estado: str | None = None,
        cliente_atual_id: UUID | None = None,
    ) -> list[Titulo]:
        qs = TituloModel.objects.filter(tenant_id=tenant_id)
        if estado is not None:
            qs = qs.filter(estado=estado)
        if cliente_atual_id is not None:
            qs = qs.filter(cliente_atual_id=cliente_atual_id)
        return [mappers.model_para_titulo(m) for m in qs]

    # --- Pagamento ---

    def salvar_pagamento(self, *, tenant_id: UUID, pagamento: Pagamento) -> None:
        campos = mappers.pagamento_para_campos(pagamento)
        PagamentoModel.objects.create(
            id=pagamento.pagamento_id,
            tenant_id=tenant_id,
            titulo_id=pagamento.titulo_id,
            **campos,
        )

    def listar_pagamentos(self, *, tenant_id: UUID, titulo_id: UUID) -> list[Pagamento]:
        qs = PagamentoModel.objects.filter(tenant_id=tenant_id, titulo_id=titulo_id)
        return [mappers.model_para_pagamento(m) for m in qs]

    def existe_gateway_event(self, *, tenant_id: UUID, gateway_event_id: str) -> bool:
        """Idempotência de webhook: verifica se o evento já foi processado (INV-FIN-GW-001)."""
        return PagamentoModel.objects.filter(
            tenant_id=tenant_id,
            gateway_event_id=gateway_event_id,
        ).exists()

    # --- Parcela ---

    def salvar_parcela(self, *, tenant_id: UUID, parcela: Parcela) -> None:
        ParcelaModel.objects.create(
            id=parcela.parcela_id,
            tenant_id=tenant_id,
            titulo_id=parcela.titulo_id,
            numero=parcela.numero,
            valor=parcela.valor.centavos,
            vencimento=parcela.vencimento,
            status=parcela.status,
        )

    # --- OverrideBloqueio ---

    def salvar_override(self, *, tenant_id: UUID, override: OverrideBloqueio) -> None:
        OverrideBloqueioModel.objects.create(
            id=override.override_id,
            tenant_id=tenant_id,
            titulo_id=override.titulo_id,
            cliente_id=override.cliente_id,
            novo_prazo_max_dias=override.novo_prazo_max_dias,
            justificativa=override.justificativa,
            a3_signature_id=override.a3_signature_id,
            usuario_id=override.usuario_id,
            perfil_no_evento=override.perfil_no_evento,
        )

    def atualizar_titulo_cancelado(
        self,
        *,
        tenant_id: UUID,
        titulo: Titulo,
        cancelado_em: datetime,
    ) -> None:
        """Cancela título: estado=cancelado + cancelado_em one-shot (trigger 0003 permite).

        `cancelado_em` é gravado via SQL pois a entidade `Titulo` não carrega esse campo
        (é só-banco, one-shot). O trigger impede sobrescrita se já setado.
        """
        from django.db import connection

        atualizadas = TituloModel.objects.filter(tenant_id=tenant_id, id=titulo.titulo_id).update(
            estado=titulo.estado.value,
            revision=models.F("revision") + 1,
        )
        if atualizadas != 1:
            raise RuntimeError(
                f"atualizar_titulo_cancelado: esperava 1 linha, afetou {atualizadas} "
                f"(titulo {titulo.titulo_id})."
            )
        # Grava cancelado_em via SQL direto (campo one-shot, não na entidade)
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE titulo_receber SET cancelado_em = %s "
                "WHERE id = %s AND tenant_id = %s AND cancelado_em IS NULL",
                [cancelado_em, str(titulo.titulo_id), str(tenant_id)],
            )

    def contar_overrides_no_mes(self, *, tenant_id: UUID, ano: int, mes: int) -> int:
        """Conta overrides do tenant no mês para verificar limite 5%/mês (R-CR-NOVO-4)."""
        return OverrideBloqueioModel.objects.filter(
            tenant_id=tenant_id,
            criado_em__year=ano,
            criado_em__month=mes,
        ).count()
