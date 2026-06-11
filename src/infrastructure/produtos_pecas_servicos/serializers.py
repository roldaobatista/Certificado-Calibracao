"""Serializers DRF da frente `produtos-pecas-servicos` (Fatia 2 — T-PPS-033).

O serializer aceita só input legítimo: `status`/`versao_n`/`origem_sugestao`
NUNCA vêm do payload (derivados no use case). `preco`/`preco_padrao` são
validados pelo VO `Preco` no use case (escala 2 + > 0 — ValueError → 400);
aqui só o shape Decimal. `motivo` de correção exige ≥10 chars (INV-VIG-002).
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.produtos_pecas_servicos.enums import TipoItem

_TIPO_ITEM_CHOICES = [t.value for t in TipoItem]


class CadastrarItemSerializer(serializers.Serializer):
    """US-CAT-001 — item + versão 1 da lista num POST só."""

    codigo_interno = serializers.CharField(max_length=60)
    tipo = serializers.ChoiceField(choices=_TIPO_ITEM_CHOICES)
    nome = serializers.CharField(max_length=200)
    unidade_medida = serializers.CharField(max_length=20)
    preco_padrao = serializers.DecimalField(max_digits=12, decimal_places=2)
    vigencia_inicio = serializers.DateTimeField(required=False, allow_null=True, default=None)
    # None = derivado do tipo (servico/kit -> False) — TL-PPS-12/14
    controla_estoque = serializers.BooleanField(required=False, allow_null=True, default=None)
    codigo_fabricante = serializers.CharField(
        max_length=60, required=False, allow_blank=True, default=""
    )
    descricao = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )
    categoria = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    motivo = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )


class NovaVersaoPrecoSerializer(serializers.Serializer):
    """US-CAT-002 — nova versão de lista (anti-retroativa no use case)."""

    preco_padrao = serializers.DecimalField(max_digits=12, decimal_places=2)
    vigencia_inicio = serializers.DateTimeField(required=False, allow_null=True, default=None)
    # None = herda da versão base
    nome = serializers.CharField(max_length=200, required=False, allow_null=True, default=None)
    unidade_medida = serializers.CharField(
        max_length=20, required=False, allow_null=True, default=None
    )
    descricao = serializers.CharField(
        max_length=2000, required=False, allow_null=True, allow_blank=True, default=None
    )
    categoria = serializers.CharField(
        max_length=100, required=False, allow_null=True, allow_blank=True, default=None
    )
    motivo = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )


class CorrigirVersaoSerializer(serializers.Serializer):
    """D-PPS-8 — revoga+recria; motivo auditado obrigatório."""

    versao_id = serializers.UUIDField()
    motivo = serializers.CharField(max_length=500, min_length=10)
    preco_padrao = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, default=None
    )
    nome = serializers.CharField(max_length=200, required=False, allow_null=True, default=None)
    unidade_medida = serializers.CharField(
        max_length=20, required=False, allow_null=True, default=None
    )
    descricao = serializers.CharField(
        max_length=2000, required=False, allow_null=True, allow_blank=True, default=None
    )
    categoria = serializers.CharField(
        max_length=100, required=False, allow_null=True, allow_blank=True, default=None
    )


class ComponenteKitSerializer(serializers.Serializer):
    item_filho_id = serializers.UUIDField()
    # > 0 validado pelo VO de domínio (KitComposicao — ValueError → 400)
    quantidade = serializers.DecimalField(max_digits=12, decimal_places=3)


class MontarKitSerializer(serializers.Serializer):
    """US-CAT-003 — substitui a composição inteira (estado final)."""

    componentes = ComponenteKitSerializer(many=True, allow_empty=False)


class CriarTabelaSerializer(serializers.Serializer):
    """D-PPS-3 — MVP trava 1 padrão por tenant (UNIQUE parcial)."""

    nome = serializers.CharField(max_length=120)
    eh_padrao = serializers.BooleanField(required=False, default=True)
    descricao = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )


class CriarLinhaSerializer(serializers.Serializer):
    """ADR-0081 — linha de venda; `preco` ausente = default sugerido."""

    item_id = serializers.UUIDField()
    preco = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, default=None
    )
    vigencia_inicio = serializers.DateTimeField(required=False, allow_null=True, default=None)
    vigencia_fim = serializers.DateTimeField(required=False, allow_null=True, default=None)


class CorrigirLinhaSerializer(serializers.Serializer):
    """D-PPS-8 — revoga+recria na MESMA janela."""

    linha_id = serializers.UUIDField()
    preco = serializers.DecimalField(max_digits=12, decimal_places=2)
    motivo = serializers.CharField(max_length=500, min_length=10)


class EncerrarLinhaSerializer(serializers.Serializer):
    """One-shot NULL→data."""

    linha_id = serializers.UUIDField()
    fim = serializers.DateTimeField()


class ImportarCatalogoSerializer(serializers.Serializer):
    """US-CAT-004 — upload CSV (layout fixo; extras descartadas no parse)."""

    arquivo = serializers.FileField()


class AceitarLinhaImportacaoSerializer(serializers.Serializer):
    """Aceite POR LINHA (one-shot; reusa cadastrar_item)."""

    linha_id = serializers.UUIDField()


class RejeitarLinhaImportacaoSerializer(serializers.Serializer):
    """Rejeição manual na conferência (one-shot)."""

    linha_id = serializers.UUIDField()
    motivo = serializers.CharField(max_length=300)
