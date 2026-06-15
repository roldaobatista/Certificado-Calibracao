"""Serializers REST do modulo `orcamentos` (Fatia 2 / Onda 2a).

Entrada: validacao DRF + bifurcacao tecnico/comercial (INV-ORC-EQUIP-ITEM).
Saida: `serializar_orcamento` aplica RBAC de campo — `comissao_prevista` so com
`orcamento.ver_margem` (INV-ORC-MARGEM-OFF / D-ORC-10). O item NUNCA expoe
margem/custo (o snapshot nem os persiste).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from src.domain.comercial.orcamentos.entities import ItemOrcamento, Orcamento
from src.domain.comercial.orcamentos.enums import TipoAtividadeAlvo
from src.domain.operacao.os.value_objects import TipoItemComercial

_TIPO_ATIVIDADE_ALVO_CHOICES = [t.value for t in TipoAtividadeAlvo]
_TIPO_ITEM_COMERCIAL_CHOICES = [t.value for t in TipoItemComercial]
_FORMAS_PAGAMENTO = [
    "dinheiro",
    "pix",
    "cartao_credito",
    "cartao_debito",
    "boleto",
    "transferencia",
    "cheque",
    "a_prazo",
]


class CondicoesPagamentoSerializer(serializers.Serializer):
    """VO CondicoesPagamento (D-ORC / modelo PRD)."""

    parcelas = serializers.IntegerField(min_value=1, default=1)
    forma_pagamento = serializers.ChoiceField(choices=_FORMAS_PAGAMENTO, default="pix")
    dias_vencimento_primeira = serializers.IntegerField(min_value=0, default=0)
    intervalo_dias = serializers.IntegerField(min_value=0, default=30)
    observacoes = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True, default=None
    )


class CriarOrcamentoSerializer(serializers.Serializer):
    """Entrada de `criar_orcamento` (AC-ORC-001)."""

    cliente_id = serializers.UUIDField()
    validade_dias = serializers.IntegerField(min_value=1, max_value=3650, default=30)
    condicoes_pagamento = CondicoesPagamentoSerializer(required=False)
    template_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    tabela_preco_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    observacoes = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    responsavel_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    chamado_origem_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class _ItemBaseSerializer(serializers.Serializer):
    """Campos comuns de adicionar/editar item (bifurcacao INV-ORC-EQUIP-ITEM)."""

    catalogo_item_id = serializers.UUIDField()
    descricao = serializers.CharField(max_length=300)
    quantidade = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001"), default=Decimal("1")
    )
    desconto_pct = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=Decimal("100"),
        default=Decimal("0"),
    )
    km = serializers.DecimalField(
        max_digits=10, decimal_places=4, min_value=Decimal("0"), default=Decimal("0")
    )
    parcelas = serializers.IntegerField(min_value=1, default=1)
    tabela_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    # Bifurcacao tecnico x comercial
    equipamento_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    tipo_atividade_alvo = serializers.ChoiceField(
        choices=_TIPO_ATIVIDADE_ALVO_CHOICES, required=False, allow_null=True, default=None
    )
    tipo_item_comercial = serializers.ChoiceField(
        choices=_TIPO_ITEM_COMERCIAL_CHOICES, required=False, allow_null=True, default=None
    )
    # Mensurando solicitado (D-ORC-5 / consultor-rbc C1-C3): obrigatorio p/ calibracao.
    grandeza_solicitada = serializers.CharField(
        max_length=30, required=False, allow_blank=True, allow_null=True, default=None
    )
    faixa_solicitada_min = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True, default=None
    )
    faixa_solicitada_max = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True, default=None
    )
    unidade_solicitada = serializers.CharField(
        max_length=20, required=False, allow_blank=True, allow_null=True, default=None
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        equipamento_id = attrs.get("equipamento_id")
        tipo_atividade = attrs.get("tipo_atividade_alvo")
        tipo_comercial = attrs.get("tipo_item_comercial")
        if equipamento_id is not None:
            # Item tecnico (calibracao/manutencao/...) — exige tipo_atividade_alvo,
            # nunca tipo_item_comercial (INV-ORC-EQUIP-ITEM / D-ORC-16).
            if not tipo_atividade:
                raise serializers.ValidationError(
                    {"tipo_atividade_alvo": "obrigatorio quando equipamento_id e informado."}
                )
            if tipo_comercial:
                raise serializers.ValidationError(
                    {
                        "tipo_item_comercial": "item tecnico (com equipamento) nao tem tipo comercial."
                    }
                )
        else:
            # Item comercial (deslocamento/taxa/outro) — exige tipo_item_comercial,
            # nunca tipo_atividade_alvo.
            if not tipo_comercial:
                raise serializers.ValidationError(
                    {"tipo_item_comercial": "obrigatorio quando nao ha equipamento_id."}
                )
            if tipo_atividade:
                raise serializers.ValidationError(
                    {
                        "tipo_atividade_alvo": "item comercial (sem equipamento) nao tem tipo de atividade."
                    }
                )
        self._validar_mensurando(attrs, tipo_atividade)
        return attrs

    @staticmethod
    def _validar_mensurando(attrs: dict[str, Any], tipo_atividade: str | None) -> None:
        """Mensurando obrigatorio+valido p/ calibracao; ausente caso contrario (C2/C3)."""
        from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

        grandeza = attrs.get("grandeza_solicitada")
        fmin = attrs.get("faixa_solicitada_min")
        fmax = attrs.get("faixa_solicitada_max")
        unidade = attrs.get("unidade_solicitada")
        presentes = (
            grandeza not in (None, ""),
            fmin is not None,
            fmax is not None,
            unidade not in (None, ""),
        )

        if tipo_atividade == "calibracao":
            if not all(presentes):
                raise serializers.ValidationError(
                    {"mensurando": "item de calibracao exige grandeza/faixa_min/faixa_max/unidade."}
                )
            # Fail-fast (C3): valida grandeza + faixa + unidade contra os VOs do dominio.
            try:
                Grandeza(grandeza)
            except ValueError:
                raise serializers.ValidationError(
                    {"grandeza_solicitada": f"grandeza invalida: {grandeza!r}."}
                ) from None
            try:
                # presentes ja garantiu nao-None; conversao explicita p/ tipagem.
                FaixaMedicao(
                    inferior=Decimal(str(fmin)),
                    superior=Decimal(str(fmax)),
                    unidade=str(unidade),
                )
            except ValueError as exc:
                raise serializers.ValidationError({"faixa_solicitada": str(exc)}) from exc
        elif any(presentes):
            raise serializers.ValidationError(
                {"mensurando": "grandeza/faixa/unidade so sao validos em item de calibracao."}
            )


class AdicionarItemSerializer(_ItemBaseSerializer):
    """Entrada de `adicionar_item` (AC-ORC-004)."""


class EditarItemSerializer(_ItemBaseSerializer):
    """Entrada de `editar_item` (AC-ORC-004)."""


class RecusarOrcamentoSerializer(serializers.Serializer):
    """Entrada de `recusar_orcamento` (AC-ORC-008)."""

    motivo = serializers.CharField(max_length=300, min_length=3)


class CancelarOrcamentoSerializer(serializers.Serializer):
    """Entrada de `cancelar_orcamento` (AC-ORC-008)."""

    motivo = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True, default=None
    )


class AprovarOrcamentoSerializer(serializers.Serializer):
    """Entrada de `aprovar` (interno) — análise crítica cl. 7.1 (AC-ORC-007).

    `regra_decisao_acordada`: nota livre da regra de decisão acordada (ISO 17025
    cl. 7.8.6) carimbada no envelope `orcamento.aprovado` (D-ORC-6). Opcional.
    """

    regra_decisao_acordada = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )


# ---------------------------------------------------------------------------
# Saida
# ---------------------------------------------------------------------------


def _dinheiro(d: Any) -> dict[str, Any]:
    return {"centavos": d.centavos, "moeda": d.moeda}


def serializar_link(link: Any) -> dict[str, Any]:
    """Serializa o LinkPublico para o remetente autenticado (token incluso).

    O token só é devolvido a quem ENVIA (autorizado a compartilhar). O endpoint
    público (Onda 2e) NUNCA ecoa o token de volta.
    """
    return {
        "orcamento_id": str(link.orcamento_id),
        "token": link.token,
        "expira_em": link.expira_em.isoformat(),
        "criado_em": link.criado_em.isoformat(),
    }


def serializar_item(item: ItemOrcamento) -> dict[str, Any]:
    """Serializa um item. NUNCA expoe margem/custo (snapshot nem os tem)."""
    return {
        "id": str(item.id),
        "versao_id": str(item.versao_id),
        "catalogo_item_id": str(item.catalogo_item_id),
        "sequencia": item.sequencia,
        "descricao_snapshot": item.descricao_snapshot,
        "quantidade": str(item.quantidade),
        "preco_final": _dinheiro(item.preco_final),
        "desconto_pct": str(item.desconto_pct),
        "desconto_valor": _dinheiro(item.desconto_valor),
        "total": _dinheiro(item.total),
        "semaforo": item.semaforo,
        "equipamento_id": str(item.equipamento_id) if item.equipamento_id else None,
        "tipo_atividade_alvo": (
            item.tipo_atividade_alvo.value if item.tipo_atividade_alvo else None
        ),
        "tipo_item_comercial": (
            item.tipo_item_comercial.value if item.tipo_item_comercial else None
        ),
        "grandeza_solicitada": item.grandeza_solicitada,
        "faixa_solicitada_min": (
            str(item.faixa_solicitada_min) if item.faixa_solicitada_min is not None else None
        ),
        "faixa_solicitada_max": (
            str(item.faixa_solicitada_max) if item.faixa_solicitada_max is not None else None
        ),
        "unidade_solicitada": item.unidade_solicitada,
    }


def serializar_analise(analise: Any, *, severidade: Any | None = None) -> dict[str, Any]:
    """Serializa a `AnaliseCriticaOrcamento` para a resposta interna (cl. 7.1).

    Devolve o registro probatório (itens_avaliados ricos + snapshot_hash + veredito).
    Não expõe `avaliada_por` (rastro de autoria fica no WORM, não na UI).
    `severidade` vem da decisão (None quando aprovada/reprovada/desabilitada).
    """
    return {
        "id": str(analise.id),
        "veredito": analise.veredito.value,
        "severidade": severidade.value if severidade is not None else None,
        "perfil_no_evento": analise.perfil_no_evento,
        "norma_referencia": analise.norma_referencia,
        "snapshot_hash": analise.snapshot_hash,
        "itens_avaliados": list(analise.itens_avaliados),
        "avaliada_em": analise.avaliada_em.isoformat(),
    }


def serializar_orcamento(
    orcamento: Orcamento,
    *,
    pode_ver_margem: bool,
    itens: list[ItemOrcamento] | None = None,
) -> dict[str, Any]:
    """Serializa o agregado. `comissao_prevista` so com `orcamento.ver_margem`."""
    corpo: dict[str, Any] = {
        "id": str(orcamento.id),
        "numero": orcamento.numero,
        "estado": orcamento.estado.value,
        "cliente_atual_id": (
            str(orcamento.cliente_atual_id) if orcamento.cliente_atual_id else None
        ),
        "validade_inicio": orcamento.validade.inicio.isoformat(),
        "validade_fim": (orcamento.validade.fim.isoformat() if orcamento.validade.fim else None),
        "total_bruto": _dinheiro(orcamento.total_bruto),
        "descontos": _dinheiro(orcamento.descontos),
        "impostos": _dinheiro(orcamento.impostos),
        "liquido": _dinheiro(orcamento.liquido),
        "condicoes_pagamento": {
            "parcelas": orcamento.condicoes_pagamento.parcelas,
            "forma_pagamento": orcamento.condicoes_pagamento.forma_pagamento,
            "dias_vencimento_primeira": orcamento.condicoes_pagamento.dias_vencimento_primeira,
            "intervalo_dias": orcamento.condicoes_pagamento.intervalo_dias,
            "observacoes": orcamento.condicoes_pagamento.observacoes,
        },
        "template_id": str(orcamento.template_id) if orcamento.template_id else None,
        "tabela_preco_id": (str(orcamento.tabela_preco_id) if orcamento.tabela_preco_id else None),
        "observacoes": orcamento.observacoes,
        "responsavel_id": str(orcamento.responsavel_id) if orcamento.responsavel_id else None,
        "criado_em": orcamento.criado_em.isoformat(),
    }
    if pode_ver_margem:
        corpo["comissao_prevista"] = _dinheiro(orcamento.comissao_prevista)
    if itens is not None:
        corpo["itens"] = [serializar_item(i) for i in itens]
    return corpo


# ---------------------------------------------------------------------------
# Template (T-ORC-039 / US-ORC-005 / D-ORC-13)
# ---------------------------------------------------------------------------


class TemplateSerializer(serializers.Serializer):
    """Entrada de criar/editar template (gate `selo_rbc` aplicado server-side — D-ORC-13).

    `selo_rbc` é aceito no payload, mas a permissão é decidida server-side pelo perfil
    do tenant (NUNCA confia no payload pra perfil — só pra intenção do usuário).
    """

    nome = serializers.CharField(max_length=200, min_length=2)
    tipo = serializers.CharField(max_length=60, min_length=2)
    selo_rbc = serializers.BooleanField(default=False)
    itens_default = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )
    condicoes_default = serializers.DictField(required=False, default=dict)


def serializar_template(template: Any) -> dict[str, Any]:
    """Saída de um Template (sem PII; campos de configuração)."""
    return {
        "id": str(template.id),
        "nome": template.nome,
        "tipo": template.tipo,
        "selo_rbc": template.selo_rbc,
        "itens_default": template.itens_default,
        "condicoes_default": template.condicoes_default,
        "criado_em": template.criado_em.isoformat(),
        "deletado_em": template.deletado_em.isoformat() if template.deletado_em else None,
    }
