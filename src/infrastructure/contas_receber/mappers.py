"""Mapper model PG ↔ entidade de domínio contas-receber (Fatia 1b, T-CR-021 — ADR-0007).

Colunas tipadas → mapeamento campo-a-campo. O use case nunca conhece Django — só
as entidades de domínio. Enums reconstruídos a partir do `.value`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.contas_receber.entities import (
    OverrideBloqueio,
    Pagamento,
    Parcela,
    Titulo,
)
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemPagamento,
    OrigemTitulo,
)
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel

if TYPE_CHECKING:
    from src.infrastructure.contas_receber.models import (
        OverrideBloqueio as OverrideBloqueioModel,
    )
    from src.infrastructure.contas_receber.models import Pagamento as PagamentoModel
    from src.infrastructure.contas_receber.models import Parcela as ParcelaModel
    from src.infrastructure.contas_receber.models import Titulo as TituloModel

# Moeda padrão (centavos BRL)
_MOEDA = "BRL"


def model_para_titulo(m: TituloModel) -> Titulo:
    """Model PG → entidade de domínio `Titulo` (leitura)."""
    return Titulo(
        titulo_id=m.id,
        tenant_id=m.tenant_id,
        cliente_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=m.cliente_atual_id,
            hash_original=m.cliente_referencia_hash,
            key_id=str(m.cliente_key_id),
        ),
        valor_original=Dinheiro(centavos=m.valor_original, moeda=_MOEDA),
        data_emissao=m.data_emissao,
        data_vencimento=m.data_vencimento,
        data_baixa=m.data_baixa,
        estado=EstadoTitulo(m.estado),
        meio=MeioCobranca(m.meio),
        categoria_receita=CategoriaReceita(m.categoria_receita),
        perfil_no_evento=m.perfil_no_evento,
        origem=OrigemTitulo(m.origem),
        os_id_origem=m.os_id_origem,
        nfse_id_origem=m.nfse_id_origem,
        gateway_externo_id=m.gateway_externo_id or None,
        convenio_pix_id=m.convenio_pix_id or None,
        linha_digitavel=m.linha_digitavel or None,
        qr_code=m.qr_code or None,
        tx_id=m.tx_id or None,
        desconto_pontualidade_pct=m.desconto_pontualidade_pct,
        numero_sequencial_tenant=m.numero_sequencial_tenant,
        revision=m.revision,
        criado_em=m.criado_em,
    )


def titulo_para_campos(t: Titulo) -> dict[str, Any]:
    """Entidade `Titulo` → kwargs do Model (escrita). `id`/`tenant_id` vão por fora."""
    ref = t.cliente_referencia
    return {
        "cliente_atual_id": ref.uuid_atual_id,
        "cliente_referencia_hash": ref.hash_original,
        "cliente_key_id": ref.key_id,
        "valor_original": t.valor_original.centavos,
        "data_emissao": t.data_emissao,
        "data_vencimento": t.data_vencimento,
        "data_baixa": t.data_baixa,
        "estado": t.estado.value,
        "meio": t.meio.value,
        "categoria_receita": t.categoria_receita.value,
        "perfil_no_evento": t.perfil_no_evento,
        "origem": t.origem.value,
        "os_id_origem": t.os_id_origem,
        "nfse_id_origem": t.nfse_id_origem,
        "gateway_externo_id": t.gateway_externo_id or "",
        "convenio_pix_id": t.convenio_pix_id or "",
        "linha_digitavel": t.linha_digitavel or "",
        "qr_code": t.qr_code or "",
        "tx_id": t.tx_id or "",
        "desconto_pontualidade_pct": t.desconto_pontualidade_pct,
        "numero_sequencial_tenant": t.numero_sequencial_tenant,
    }


def model_para_pagamento(m: PagamentoModel) -> Pagamento:
    """Model PG → entidade de domínio `Pagamento` (leitura)."""
    return Pagamento(
        pagamento_id=m.id,
        titulo_id=m.titulo_id,
        valor=Dinheiro(centavos=m.valor, moeda=_MOEDA),
        data=m.data,
        origem=OrigemPagamento(m.origem),
        valor_atualizado_snapshot_em_pagamento=Dinheiro(
            centavos=m.valor_atualizado_snapshot_em_pagamento,
            moeda=_MOEDA,
        ),
        gateway_event_id=m.gateway_event_id or None,
        comprovante_url=m.comprovante_url or None,
        criado_em=m.criado_em,
    )


def pagamento_para_campos(p: Pagamento) -> dict[str, Any]:
    """Entidade `Pagamento` → kwargs do Model (escrita). `id`/`tenant_id`/`titulo_id` por fora."""
    return {
        "valor": p.valor.centavos,
        "data": p.data,
        "origem": p.origem.value,
        "valor_atualizado_snapshot_em_pagamento": p.valor_atualizado_snapshot_em_pagamento.centavos,
        "gateway_event_id": p.gateway_event_id or "",
        "comprovante_url": p.comprovante_url or "",
    }


def model_para_parcela(m: ParcelaModel) -> Parcela:
    """Model PG → entidade de domínio `Parcela` (leitura)."""
    return Parcela(
        parcela_id=m.id,
        titulo_id=m.titulo_id,
        numero=m.numero,
        valor=Dinheiro(centavos=m.valor, moeda=_MOEDA),
        vencimento=m.vencimento,
        status=m.status,
    )


def model_para_override(m: OverrideBloqueioModel) -> OverrideBloqueio:
    """Model PG → entidade de domínio `OverrideBloqueio` (leitura)."""
    return OverrideBloqueio(
        override_id=m.id,
        titulo_id=m.titulo_id,
        cliente_id=m.cliente_id,
        novo_prazo_max_dias=m.novo_prazo_max_dias,
        justificativa=m.justificativa,
        a3_signature_id=m.a3_signature_id,
        usuario_id=m.usuario_id,
        perfil_no_evento=m.perfil_no_evento,
        criado_em=m.criado_em,
    )
