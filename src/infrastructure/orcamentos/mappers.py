"""Mappers model<->entidade do modulo Orcamentos — T-ORC-026.

Traduz entre os models Django (`models.py`) e as entidades de dominio frozen
(`src/domain/comercial/orcamentos/entities.py`). Mantem o dominio livre de Django.

Convencoes de mapeamento (decisoes de schema da Fatia 1b):
  - Dinheiro: `<campo>_centavos` (BigInteger) + `moeda` -> `Dinheiro(centavos, moeda)`.
  - JanelaVigencia: `validade_inicio` + `validade_fim` -> `JanelaVigencia(inicio, fim)`.
  - CondicoesPagamento: jsonb dict <-> VO.
  - PrecoResolvido: jsonb (tipos JSON-safe: UUID->str, Decimal->str, datetime->isoformat,
    enum->value) <-> VO aninhado (Preco / OrigemPreco / ComponenteResolvido).
  - tipo_atividade_alvo / tipo_item_comercial: '' <-> None; senao enum(value).

Zero logica de negocio aqui — so traducao 1:1.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.domain.comercial.orcamentos.entities import (
    AnaliseCriticaOrcamento,
    Aprovacao,
    ItemOrcamento,
    LinkPublico,
    Orcamento,
    Template,
    VersaoOrcamento,
)
from src.domain.comercial.orcamentos.enums import (
    CanalAprovacao,
    EstadoOrcamento,
    TipoAtividadeAlvo,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.produtos_pecas_servicos.entities import (
    ComponenteResolvido,
    PrecoResolvido,
)
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import Dinheiro, JanelaVigencia
from src.infrastructure.orcamentos import models as m

# =====================================================================
# PrecoResolvido <-> jsonb (snapshot probatorio — D-ORC-1)
# =====================================================================


def serializar_preco_resolvido(pr: PrecoResolvido) -> dict[str, Any]:
    """PrecoResolvido (VO aninhado) -> dict JSON-safe para o campo jsonb."""
    return {
        "item_id": str(pr.item_id),
        "item_versao_n": pr.item_versao_n,
        "linha_tabela_id": str(pr.linha_tabela_id),
        "tabela_id": str(pr.tabela_id),
        "preco": str(pr.preco.valor),
        "data_referencia": pr.data_referencia.isoformat(),
        "origem_preco": pr.origem_preco.value,
        "composicao_resolvida": [
            {
                "item_filho_id": str(c.item_filho_id),
                "quantidade": str(c.quantidade),
                "versao_n": c.versao_n,
                "preco_unitario": str(c.preco_unitario.valor),
            }
            for c in pr.composicao_resolvida
        ],
    }


def desserializar_preco_resolvido(d: dict[str, Any]) -> PrecoResolvido:
    """dict jsonb -> PrecoResolvido (reconstroi VOs aninhados)."""
    return PrecoResolvido(
        item_id=UUID(d["item_id"]),
        item_versao_n=int(d["item_versao_n"]),
        linha_tabela_id=UUID(d["linha_tabela_id"]),
        tabela_id=UUID(d["tabela_id"]),
        preco=Preco(Decimal(str(d["preco"]))),
        data_referencia=datetime.fromisoformat(d["data_referencia"]),
        origem_preco=OrigemPreco(d["origem_preco"]),
        composicao_resolvida=tuple(
            ComponenteResolvido(
                item_filho_id=UUID(c["item_filho_id"]),
                quantidade=Decimal(str(c["quantidade"])),
                versao_n=int(c["versao_n"]),
                preco_unitario=Preco(Decimal(str(c["preco_unitario"]))),
            )
            for c in d.get("composicao_resolvida", [])
        ),
    )


# =====================================================================
# CondicoesPagamento <-> jsonb
# =====================================================================


def serializar_condicoes(cp: CondicoesPagamento) -> dict[str, Any]:
    return {
        "parcelas": cp.parcelas,
        "forma_pagamento": cp.forma_pagamento,
        "dias_vencimento_primeira": cp.dias_vencimento_primeira,
        "intervalo_dias": cp.intervalo_dias,
        "observacoes": cp.observacoes,
    }


def desserializar_condicoes(d: dict[str, Any]) -> CondicoesPagamento:
    return CondicoesPagamento(
        parcelas=int(d["parcelas"]),
        forma_pagamento=str(d["forma_pagamento"]),
        dias_vencimento_primeira=int(d.get("dias_vencimento_primeira", 0)),
        intervalo_dias=int(d.get("intervalo_dias", 30)),
        observacoes=d.get("observacoes"),
    )


# =====================================================================
# model -> entidade
# =====================================================================


def to_orcamento(o: m.Orcamento) -> Orcamento:
    moeda = o.moeda
    return Orcamento(
        id=o.id,
        tenant_id=o.tenant_id,
        cliente_atual_id=o.cliente_atual_id,
        cliente_referencia_hash=o.cliente_referencia_hash,
        cliente_key_id=o.cliente_key_id,
        numero=o.numero,
        estado=EstadoOrcamento(o.estado),
        validade=JanelaVigencia(inicio=o.validade_inicio, fim=o.validade_fim),
        total_bruto=Dinheiro(o.total_bruto_centavos, moeda),
        descontos=Dinheiro(o.descontos_centavos, moeda),
        impostos=Dinheiro(o.impostos_centavos, moeda),
        liquido=Dinheiro(o.liquido_centavos, moeda),
        comissao_prevista=Dinheiro(o.comissao_prevista_centavos, moeda),
        condicoes_pagamento=desserializar_condicoes(o.condicoes_pagamento),
        criado_em=o.criado_em,
        criado_por=o.criado_por,
        template_id=o.template_id,
        tabela_preco_id=o.tabela_preco_id,
        observacoes=o.observacoes or None,
        responsavel_id=o.responsavel_id,
        chamado_origem_id=o.chamado_origem_id,
    )


def to_versao(v: m.VersaoOrcamento) -> VersaoOrcamento:
    return VersaoOrcamento(
        id=v.id,
        orcamento_id=v.orcamento_id,
        tenant_id=v.tenant_id,
        numero_versao=v.numero_versao,
        snapshot=v.snapshot,
        criada_em=v.criada_em,
        criada_por=v.criada_por,
        revogado_em=v.revogado_em,
        motivo_revogacao=v.motivo_revogacao or None,
    )


def to_item(i: m.ItemOrcamento) -> ItemOrcamento:
    moeda = i.moeda
    return ItemOrcamento(
        id=i.id,
        versao_id=i.versao_id,
        tenant_id=i.tenant_id,
        catalogo_item_id=i.catalogo_item_id,
        sequencia=i.sequencia,
        preco_resolvido=desserializar_preco_resolvido(i.preco_resolvido),
        preco_final=Dinheiro(i.preco_final_centavos, moeda),
        desconto_pct=i.desconto_pct,
        desconto_valor=Dinheiro(i.desconto_valor_centavos, moeda),
        quantidade=i.quantidade,
        total=Dinheiro(i.total_centavos, moeda),
        semaforo=i.semaforo,
        descricao_snapshot=i.descricao_snapshot,
        equipamento_id=i.equipamento_id,
        tipo_atividade_alvo=(
            TipoAtividadeAlvo(i.tipo_atividade_alvo) if i.tipo_atividade_alvo else None
        ),
        tipo_item_comercial=(
            TipoItemComercial(i.tipo_item_comercial) if i.tipo_item_comercial else None
        ),
        grandeza_solicitada=i.grandeza_solicitada or None,
        faixa_solicitada_min=i.faixa_solicitada_min,
        faixa_solicitada_max=i.faixa_solicitada_max,
        unidade_solicitada=i.unidade_solicitada or None,
    )


def to_link(link: m.LinkPublico) -> LinkPublico:
    return LinkPublico(
        id=link.id,
        orcamento_id=link.orcamento_id,
        tenant_id=link.tenant_id,
        token=link.token,
        expira_em=link.expira_em,
        criado_em=link.criado_em,
        revogado_em=link.revogado_em,
        motivo_revogacao=link.motivo_revogacao or None,
    )


def to_aprovacao(a: m.Aprovacao) -> Aprovacao:
    return Aprovacao(
        id=a.id,
        orcamento_id=a.orcamento_id,
        versao_id=a.versao_id,
        tenant_id=a.tenant_id,
        aprovado_em=a.aprovado_em,
        canal=CanalAprovacao(a.canal),
        nome_aprovador_hash=a.nome_aprovador_hash,
        email_aprovador_hash=a.email_aprovador_hash,
        lgpd_aceite_versao_termo=a.lgpd_aceite_versao_termo,
        lgpd_aceite_texto_hash=a.lgpd_aceite_texto_hash,
        ip_hash=a.ip_hash,
        user_agent=a.user_agent,
        ressalvas_aceitas=a.ressalvas_aceitas,
        aprovado_por=a.aprovado_por,
    )


def to_analise(an: m.AnaliseCriticaOrcamento) -> AnaliseCriticaOrcamento:
    return AnaliseCriticaOrcamento(
        id=an.id,
        orcamento_id=an.orcamento_id,
        versao_id=an.versao_id,
        tenant_id=an.tenant_id,
        perfil_no_evento=an.perfil_no_evento,
        veredito=VeredictoAnaliseCritica(an.veredito),
        norma_referencia=an.norma_referencia,
        itens_avaliados=tuple(an.itens_avaliados),
        snapshot_hash=an.snapshot_hash,
        avaliada_em=an.avaliada_em,
        avaliada_por=an.avaliada_por,
    )


def to_template(t: m.Template) -> Template:
    return Template(
        id=t.id,
        tenant_id=t.tenant_id,
        nome=t.nome,
        tipo=t.tipo,
        itens_default=t.itens_default,
        condicoes_default=t.condicoes_default,
        selo_rbc=t.selo_rbc,
        criado_em=t.criado_em,
        criado_por=t.criado_por,
        deletado_em=t.deletado_em,
        deletado_por=t.deletado_por,
    )
