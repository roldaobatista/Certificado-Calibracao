"""Adapters Django dos Protocols do módulo precificacao (T-PRC-026 — ADR-0007).

Concorrência (D-PRC-7 / TL-PRC-04): `travar_item` faz `pg_advisory_xact_lock`
(namespace 880_404 — distinto de 880_401 certificados M8, 880_402 numeração
configuracoes, 880_403 catálogo PPS). O use case chama o lock DENTRO de
`transaction.atomic` ANTES de ler regras — densidade `versao_n = max+1` e o
par encerrar-anterior+inserir-nova ficam serializados. A exclusion 0004 é a
verdade no banco contra qualquer caminho que burle o use case.

Faixas (D-PRC-3 / TL-PRC-16): replace-all atômico sob advisory lock por tenant
(mesmo namespace 880_404, chave distinta de item). DELETE de faixas antigas é
legítimo (faixas de CONFIGURAÇÃO, não WORM — molde KitComposicao da PPS).

Revogação/encerramento de regra: UPDATE escopado nos campos one-shot (o trigger
0003 garante one-shot e imutabilidade do resto). NÃO são singletons.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from django.db import connection
from django.db.models import Q

from src.domain.precificacao.entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PedidoAprovacaoDesconto,
    PerfilComposicaoPreco,
    RegraFormacaoPreco,
    VinculoTabelaPrecoCliente,
)
from src.domain.precificacao.enums import EstadoPedido
from src.infrastructure.precificacao import mappers
from src.infrastructure.precificacao.models import (
    FaixaAprovacaoDesconto as FaixaModel,
)
from src.infrastructure.precificacao.models import (
    ParametrosPrecificacaoTenant as ParametrosModel,
)
from src.infrastructure.precificacao.models import (
    PedidoAprovacaoDesconto as PedidoModel,
)
from src.infrastructure.precificacao.models import (
    RegraFormacaoPreco as RegraModel,
)
from src.infrastructure.precificacao.models import (
    VinculoTabelaPrecoCliente as VinculoModel,
)

# Namespace do advisory lock da precificação (serializa publicar/revogar regra
# por item e replace-all de faixas por tenant — namespace novo D-PRC-7).
_ADVISORY_LOCK_PRECIFICACAO = 880_404


def _advisory_lock(chave: str) -> None:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT pg_advisory_xact_lock(%s, hashtext(%s));",
            [_ADVISORY_LOCK_PRECIFICACAO, chave],
        )


class DjangoRegraRepository:
    """Agregado RegraFormacaoPreco (WORM molde Imposto — D-PRC-7)."""

    def obter(self, *, tenant_id: UUID, regra_id: UUID) -> RegraFormacaoPreco | None:
        m = RegraModel.objects.filter(tenant_id=tenant_id, id=regra_id).first()
        return mappers.regra_model_para_entidade(m) if m is not None else None

    def obter_vigente(
        self, *, tenant_id: UUID, item_id: UUID, em: datetime
    ) -> RegraFormacaoPreco | None:
        """Regra vigente em `em` para o item; None se ausente.

        Revogada NUNCA resolve (molde versão vigente PPS — lição M2).
        """
        m = (
            RegraModel.objects.filter(
                tenant_id=tenant_id,
                item_id=item_id,
                vigencia_inicio__lte=em,
                revogado_em__isnull=True,
            )
            .filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gt=em))
            .order_by("-versao_n")
            .first()
        )
        return mappers.regra_model_para_entidade(m) if m is not None else None

    def listar_por_item(
        self, *, tenant_id: UUID, item_id: UUID
    ) -> list[RegraFormacaoPreco]:
        qs = RegraModel.objects.filter(tenant_id=tenant_id, item_id=item_id).order_by(
            "versao_n"
        )
        return [mappers.regra_model_para_entidade(m) for m in qs]

    def listar_vigentes_por_itens(
        self, *, tenant_id: UUID, item_ids: list[UUID], em: datetime
    ) -> dict[UUID, RegraFormacaoPreco]:
        """Batch: devolve dict item_id→regra vigente em `em` para N itens.

        UMA query em vez de N (anti N+1 — TL-PRC-14 / MÉDIO-3 P9).
        Items sem regra vigente simplesmente não aparecem no dict.
        """
        if not item_ids:
            return {}
        qs = (
            RegraModel.objects.filter(
                tenant_id=tenant_id,
                item_id__in=item_ids,
                vigencia_inicio__lte=em,
                revogado_em__isnull=True,
            )
            .filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gt=em))
            .order_by("item_id", "-versao_n")  # mais recente por item
        )
        # Deduplica por item_id: primeiro (mais recente por -versao_n) vence.
        resultado: dict[UUID, RegraFormacaoPreco] = {}
        for m in qs:
            if m.item_id not in resultado:
                resultado[m.item_id] = mappers.regra_model_para_entidade(m)
        return resultado

    def travar_item(self, *, tenant_id: UUID, item_id: UUID) -> None:
        """Advisory lock por (tenant, item) — chamar DENTRO de transaction.atomic."""
        _advisory_lock(f"{tenant_id}:regra:{item_id}")

    def salvar(self, regra: RegraFormacaoPreco) -> None:
        RegraModel.objects.create(
            id=regra.id,
            tenant_id=regra.tenant_id,
            item_id=regra.item_id,
            modo=regra.modo.value,
            versao_n=regra.versao_n,
            preco_fixo=regra.preco_fixo,
            custo_manual_declarado=regra.custo_manual_declarado,
            custo_referencia_em=regra.custo_referencia_em,
            margem_alvo_pct=regra.margem_alvo_pct.valor if regra.margem_alvo_pct is not None else None,
            margem_piso_pct=regra.margem_piso_pct.valor if regra.margem_piso_pct is not None else None,
            vigencia_inicio=regra.vigencia.inicio,
            vigencia_fim=regra.vigencia.fim,
            revogado_em=regra.vigencia.revogado_em,
            motivo_revogacao=regra.vigencia.motivo_revogacao or "",
            criado_por=regra.criado_por,
        )

    def encerrar_vigencia(
        self, *, tenant_id: UUID, regra_id: UUID, fim: datetime
    ) -> None:
        atualizadas = RegraModel.objects.filter(
            tenant_id=tenant_id, id=regra_id, vigencia_fim__isnull=True
        ).update(vigencia_fim=fim)
        if atualizadas == 0:
            raise RuntimeError(f"regra {regra_id} sem vigência aberta pra encerrar.")

    def revogar(
        self, *, tenant_id: UUID, regra_id: UUID, revogado_em: datetime, motivo: str
    ) -> None:
        atualizadas = RegraModel.objects.filter(
            tenant_id=tenant_id, id=regra_id, revogado_em__isnull=True
        ).update(revogado_em=revogado_em, motivo_revogacao=motivo)
        if atualizadas == 0:
            raise RuntimeError(f"regra {regra_id} já revogada ou inexistente.")


class DjangoFaixaRepository:
    """Agregado FaixaAprovacaoDesconto — replace-all atômico (D-PRC-3 / TL-PRC-16)."""

    def listar(self, *, tenant_id: UUID) -> list[FaixaAprovacaoDesconto]:
        qs = FaixaModel.objects.filter(tenant_id=tenant_id).order_by("versao_n", "pct_de")
        return [mappers.faixa_model_para_entidade(m) for m in qs]

    def substituir_todas(
        self,
        *,
        tenant_id: UUID,
        faixas: list[FaixaAprovacaoDesconto],
        criado_por: UUID,
    ) -> None:
        """Replace-all atômico: DELETE + bulk_create sob advisory lock por tenant.

        Advisory lock garante que dois replace-all concorrentes não intercalam
        (namespace 880_404, chave distinta de item — TL-PRC-16).
        """
        _advisory_lock(f"{tenant_id}:faixas")
        FaixaModel.objects.filter(tenant_id=tenant_id).delete()
        FaixaModel.objects.bulk_create(
            FaixaModel(
                id=f.id,
                tenant_id=f.tenant_id,
                pct_de=f.pct_de.valor,
                pct_ate=f.pct_ate.valor,
                alcada=f.alcada.value,
                versao_n=f.versao_n,
                hash_conjunto=f.hash_conjunto,
                criado_por=f.criado_por,
            )
            for f in faixas
        )


class DjangoPedidoRepository:
    """Agregado PedidoAprovacaoDesconto (WORM one-shot — D-PRC-14)."""

    def obter(
        self, *, tenant_id: UUID, pedido_id: UUID
    ) -> PedidoAprovacaoDesconto | None:
        m = PedidoModel.objects.filter(tenant_id=tenant_id, id=pedido_id).first()
        return mappers.pedido_model_para_entidade(m) if m is not None else None

    def listar_pendentes(
        self, *, tenant_id: UUID
    ) -> list[PedidoAprovacaoDesconto]:
        qs = PedidoModel.objects.filter(
            tenant_id=tenant_id, estado=EstadoPedido.SOLICITADO.value
        ).order_by("criado_em")
        return [mappers.pedido_model_para_entidade(m) for m in qs]

    def salvar(self, pedido: PedidoAprovacaoDesconto) -> None:
        PedidoModel.objects.create(
            id=pedido.id,
            tenant_id=pedido.tenant_id,
            contexto_tipo=pedido.contexto_tipo.value,
            contexto_id=pedido.contexto_id,
            pct_solicitado=pedido.pct_solicitado.valor,
            cortesia=pedido.cortesia,
            alcada_exigida=pedido.alcada_exigida.value,
            fingerprint_calculo=pedido.fingerprint_calculo,
            estado=pedido.estado.value,
            solicitante_id=pedido.solicitante_id,
            decisor_id=pedido.decisor_id,
            snapshot_probatorio=pedido.snapshot_probatorio,
            justificativa_hash=pedido.justificativa_hash or "",
            decidido_em=pedido.decidido_em,
        )

    def decidir(
        self,
        *,
        tenant_id: UUID,
        pedido_id: UUID,
        estado: EstadoPedido,
        decisor_id: UUID,
        justificativa_hash: str,
        decidido_em: datetime,
    ) -> None:
        """One-shot SOLICITADO→APROVADO|NEGADO; trigger garante one-shot no banco."""
        atualizadas = PedidoModel.objects.filter(
            tenant_id=tenant_id,
            id=pedido_id,
            estado=EstadoPedido.SOLICITADO.value,
        ).update(
            estado=estado.value,
            decisor_id=decisor_id,
            justificativa_hash=justificativa_hash,
            decidido_em=decidido_em,
        )
        if atualizadas == 0:
            raise RuntimeError(
                f"pedido {pedido_id} não está SOLICITADO ou não existe — decisão é one-shot."
            )


class DjangoVinculoTabelaRepository:
    """Repositório de VinculoTabelaPrecoCliente (D-PRC-12)."""

    def obter_por_cliente(
        self, *, tenant_id: UUID, cliente_id: UUID, em: datetime
    ) -> VinculoTabelaPrecoCliente | None:
        m = (
            VinculoModel.objects.filter(
                tenant_id=tenant_id,
                cliente_id=cliente_id,
                vigencia_inicio__lte=em,
                revogado_em__isnull=True,
            )
            .filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gt=em))
            .first()
        )
        return mappers.vinculo_model_para_entidade(m) if m is not None else None

    def salvar(self, vinculo: VinculoTabelaPrecoCliente) -> None:
        VinculoModel.objects.create(
            id=vinculo.id,
            tenant_id=vinculo.tenant_id,
            tabela_id=vinculo.tabela_id,
            cliente_id=vinculo.cliente_id,
            vigencia_inicio=vinculo.vigencia.inicio,
            vigencia_fim=vinculo.vigencia.fim,
            revogado_em=vinculo.vigencia.revogado_em,
            motivo_revogacao=vinculo.vigencia.motivo_revogacao or "",
            criado_por=vinculo.criado_por,
        )

    def revogar(
        self, *, tenant_id: UUID, vinculo_id: UUID, revogado_em: datetime, motivo: str
    ) -> None:
        atualizadas = VinculoModel.objects.filter(
            tenant_id=tenant_id, id=vinculo_id, revogado_em__isnull=True
        ).update(revogado_em=revogado_em, motivo_revogacao=motivo)
        if atualizadas == 0:
            raise RuntimeError(f"vínculo {vinculo_id} já revogado ou inexistente.")


class DjangoPerfilComposicaoRepository:
    """Repositório de PerfilComposicaoPreco — upsert por (tenant, item_servico) (D-PRC-2)."""

    def obter_por_item(
        self, *, tenant_id: UUID, item_servico_id: UUID
    ) -> PerfilComposicaoPreco | None:
        from src.infrastructure.precificacao.models import (  # -- import local evita ciclo circular models→repositories; padrao consolidado neste modulo
            PerfilComposicaoPreco as PerfilModel,
        )

        m = PerfilModel.objects.filter(
            tenant_id=tenant_id, item_servico_id=item_servico_id, deletado_em__isnull=True
        ).first()
        return mappers.perfil_model_para_entidade(m) if m is not None else None

    def salvar(self, perfil: PerfilComposicaoPreco) -> None:
        from src.infrastructure.precificacao.models import (  # -- idem acima
            PerfilComposicaoPreco as PerfilModel,
        )

        PerfilModel.objects.create(
            id=perfil.id,
            tenant_id=perfil.tenant_id,
            item_servico_id=perfil.item_servico_id,
            componentes_esperados=[str(c) for c in perfil.componentes_esperados],
            criado_por=perfil.criado_por,
            aviso_texto=perfil.aviso_texto or "",
        )

    def atualizar(self, perfil: PerfilComposicaoPreco) -> None:
        from src.infrastructure.precificacao.models import (  # -- idem acima
            PerfilComposicaoPreco as PerfilModel,
        )

        PerfilModel.objects.filter(tenant_id=perfil.tenant_id, id=perfil.id).update(
            componentes_esperados=[str(c) for c in perfil.componentes_esperados],
            criado_por=perfil.criado_por,
            aviso_texto=perfil.aviso_texto or "",
        )


class DjangoParametrosRepository:
    """Repositório de ParametrosPrecificacaoTenant — singleton versionado por tenant."""

    def obter_vigentes(
        self, *, tenant_id: UUID
    ) -> ParametrosPrecificacaoTenant | None:
        m = ParametrosModel.objects.filter(tenant_id=tenant_id).order_by("-versao_n").first()
        return mappers.parametros_model_para_entidade(m) if m is not None else None

    def salvar(self, parametros: ParametrosPrecificacaoTenant) -> None:
        ParametrosModel.objects.create(
            id=parametros.id,
            tenant_id=parametros.tenant_id,
            versao_n=parametros.versao_n,
            custo_km=parametros.custo_km,
            taxa_parcelamento_mensal=parametros.taxa_parcelamento_mensal.valor,
            pct_comissao_prevista=parametros.pct_comissao_prevista.valor,
            margem_alvo_default=parametros.margem_alvo_default.valor,
            margem_piso_default=parametros.margem_piso_default.valor,
            criado_por=parametros.criado_por,
        )
