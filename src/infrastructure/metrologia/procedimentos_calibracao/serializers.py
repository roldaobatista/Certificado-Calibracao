"""Serializers DRF do M7 procedimentos-calibracao (T-PROC-035).

Validam o payload das actions do ProcedimentoCalibracaoViewSet. O perfil
regulatório do tenant NUNCA vem do payload (ADR-0067); `anexo_pdf_base64` é
opcional e o `sha256` é recalculado SERVER-SIDE (INV-PROC-007 — nunca do cliente).
Rótulos cliente ("Procedimento técnico"/"Código"/"Norma de referência") são da
camada de apresentação.
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.metrologia.procedimentos_calibracao.enums import TipoMetodo
from src.domain.metrologia.value_objects import Grandeza

_GRANDEZA_CHOICES = [g.value for g in Grandeza]
_TIPO_METODO_CHOICES = [t.value for t in TipoMetodo]


class CadastrarProcedimentoSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=60)
    titulo = serializers.CharField(max_length=200)
    grandeza = serializers.ChoiceField(choices=_GRANDEZA_CHOICES)
    faixa_min = serializers.DecimalField(max_digits=30, decimal_places=12)
    faixa_max = serializers.DecimalField(max_digits=30, decimal_places=12)
    unidade = serializers.CharField(max_length=20)
    metodo_norma = serializers.CharField(max_length=120)
    tipo_metodo = serializers.ChoiceField(
        choices=_TIPO_METODO_CHOICES, default=TipoMetodo.NORMALIZADO.value
    )
    registro_validacao_id = serializers.UUIDField(required=False, allow_null=True)
    anexo_pdf_base64 = serializers.CharField(required=False, allow_blank=True, default="")
    correlation_id = serializers.UUIDField()


class RevisarProcedimentoSerializer(serializers.Serializer):
    """Revisão preserva a chave natural (codigo/grandeza/faixa) da versão atual —
    só titulo/metodo/tipo/anexo mudam (procedimento_id vem da URL)."""

    titulo = serializers.CharField(max_length=200)
    metodo_norma = serializers.CharField(max_length=120)
    tipo_metodo = serializers.ChoiceField(
        choices=_TIPO_METODO_CHOICES, default=TipoMetodo.NORMALIZADO.value
    )
    registro_validacao_id = serializers.UUIDField(required=False, allow_null=True)
    anexo_pdf_base64 = serializers.CharField(required=False, allow_blank=True, default="")
    correlation_id = serializers.UUIDField()


class PublicarProcedimentoSerializer(serializers.Serializer):
    """Controle documental cl. 8.3.1 (INV-PROC-009). `aprovado_por_id` é o RT/
    gestor; o nome é snapshot. `aprovado_em` é a data do ato de aprovação."""

    numero_revisao = serializers.CharField(max_length=40, min_length=1)
    aprovado_por_id = serializers.UUIDField()
    aprovado_por_nome_snapshot = serializers.CharField(
        max_length=160, required=False, allow_blank=True, default=""
    )


class RevogarProcedimentoSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=2000, min_length=10)
