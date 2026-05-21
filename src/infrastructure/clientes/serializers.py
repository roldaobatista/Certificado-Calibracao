"""Serializers DRF do modulo Clientes.

US-CLI-001 — aceite LGPD obrigatorio em PF; em PJ, opcional com dispensa.
Versao do texto e capturada automaticamente da constante VERSAO_VIGENTE
(lgpd.py). IP hash e calculado na view e injetado via context.
"""

from __future__ import annotations

from datetime import date

from rest_framework import serializers

from src.domain.shared.value_objects import CNPJ, CPF
from src.infrastructure.clientes.lgpd import (
    DISPENSAS_VALIDAS,
    ORIGENS_VALIDAS,
    VERSAO_VIGENTE,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.clientes.validators_pii_sensivel import (
    MENSAGEM_REJEICAO,
    conter_pii_sensivel,
)


class ClienteSerializer(serializers.ModelSerializer):
    """Cliente — entrada + saida (US-CLI-001 completa).

    Campos LGPD esperados na entrada (POST):
    - PF: `aceite_lgpd_em` (datetime ISO) obrigatorio. `aceite_lgpd_origem`
      default 'CADASTRO_DIRETO' (T-CLI-101). `aceite_lgpd_versao` injetada
      automaticamente.
    - PJ: ou `aceite_lgpd_em` informado OU `aceite_lgpd_dispensa_motivo`
      informado (ex: 'pj_sem_pf_associada').

    O campo `tenant` NAO eh aceito da request — derivado do TenantMiddleware.
    """

    documento = serializers.CharField(max_length=32)
    # ip_hash NUNCA aceito do payload — injetado pela view a partir do request.
    aceite_lgpd_ip_hash = serializers.CharField(read_only=True)
    # versao NUNCA aceita do payload — sempre VERSAO_VIGENTE no momento do POST.
    aceite_lgpd_versao = serializers.CharField(read_only=True)

    class Meta:
        model = Cliente
        fields = [
            "id",
            "tipo_pessoa",
            "documento",
            "nome",
            "nome_fantasia",
            "email",
            "telefone",
            "data_nascimento",
            "observacao",
            "aceite_lgpd_em",
            "aceite_lgpd_versao",
            "aceite_lgpd_ip_hash",
            "aceite_lgpd_origem",
            "aceite_lgpd_dispensa_motivo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "aceite_lgpd_versao",
            "aceite_lgpd_ip_hash",
            "criado_em",
            "atualizado_em",
        ]

    def validate(self, attrs):
        """Normaliza documento + aplica regras LGPD PF/PJ (R3 advogado)."""
        tipo = attrs.get("tipo_pessoa") or getattr(self.instance, "tipo_pessoa", None)
        doc = attrs.get("documento")
        if doc is not None and tipo is not None:
            try:
                if tipo == TipoPessoa.PF:
                    attrs["documento"] = CPF(doc).value
                elif tipo == TipoPessoa.PJ:
                    attrs["documento"] = CNPJ(doc).value
                else:
                    raise serializers.ValidationError({"tipo_pessoa": "Tipo invalido"})
            except ValueError as e:
                raise serializers.ValidationError({"documento": str(e)}) from e

        aceite_em = attrs.get("aceite_lgpd_em")
        dispensa = attrs.get("aceite_lgpd_dispensa_motivo", "")
        origem = attrs.get("aceite_lgpd_origem", "")

        if tipo == TipoPessoa.PF and aceite_em is None:
            raise serializers.ValidationError(
                {"aceite_lgpd_em": "PF exige aceite LGPD (US-CLI-001 AC-2)."}
            )
        if tipo == TipoPessoa.PJ and aceite_em is None and not dispensa:
            raise serializers.ValidationError(
                {
                    "aceite_lgpd_dispensa_motivo": (
                        "PJ sem aceite LGPD exige dispensa "
                        "(ex: 'pj_sem_pf_associada' — R3 advogado)."
                    )
                }
            )
        if origem and origem not in ORIGENS_VALIDAS:
            raise serializers.ValidationError(
                {"aceite_lgpd_origem": f"Origem invalida; use {ORIGENS_VALIDAS}"}
            )
        if dispensa and dispensa not in DISPENSAS_VALIDAS:
            raise serializers.ValidationError(
                {"aceite_lgpd_dispensa_motivo": f"Use {DISPENSAS_VALIDAS}"}
            )

        # Snapshot da versao + origem default CADASTRO_DIRETO (T-CLI-101)
        if aceite_em is not None:
            attrs["aceite_lgpd_versao"] = VERSAO_VIGENTE
            if not attrs.get("aceite_lgpd_origem"):
                attrs["aceite_lgpd_origem"] = "CADASTRO_DIRETO"

        # =====================================================
        # T-CLI-118 (AC-CLI-006-5) — idade >= 18 em CREATE+UPDATE
        # BLOQ-A6 advogado + BLOQ-TL-1 tech-lead.
        # CHECK constraint cobre defesa em profundidade no banco.
        # =====================================================
        data_nasc = attrs.get("data_nascimento")
        if data_nasc is not None:
            hoje = date.today()
            # Cálculo idade sem dateutil: diferença em anos com ajuste
            # se ainda não fez aniversário no ano corrente.
            idade = hoje.year - data_nasc.year
            if (hoje.month, hoje.day) < (data_nasc.month, data_nasc.day):
                idade -= 1
            if idade < 18:
                raise serializers.ValidationError(
                    {
                        "data_nascimento": (
                            "dados de criança/adolescente não são tratados "
                            "no Aferê MVP-1 (LGPD art. 14 + NG-CLI-12)"
                        )
                    }
                )

        # =====================================================
        # T-CLI-117 (AC-CLI-006-4) — anti-PII sensível em `observacao`
        # BLOQ-A1/A3 advogado + BLOQ-TL-2 tech-lead.
        # =====================================================
        obs = attrs.get("observacao", "")
        if obs and conter_pii_sensivel(obs):
            raise serializers.ValidationError({"observacao": MENSAGEM_REJEICAO})

        return attrs


# =============================================================
# US-CLI-003 — serializers de importacao
# =============================================================


class DeclaracaoProcedenciaSerializer(serializers.Serializer):
    """3 checkboxes + procedencia textual (R6 advogado — bloqueante)."""

    tem_base_legal = serializers.BooleanField()
    compromisso_comunicar_titulares = serializers.BooleanField()
    declara_sem_dados_sensiveis = serializers.BooleanField()
    procedencia_declarada = serializers.CharField(max_length=200, allow_blank=False)


class ImportarPreviewSerializer(serializers.Serializer):
    """Entrada do POST /clientes/importar-preview/."""

    arquivo = serializers.FileField()


class ImportarExecutarSerializer(serializers.Serializer):
    """Entrada do POST /clientes/importar-executar/.

    Em multipart, JSON nested vem como string — `declaracao` e `mapeamento` aceitam
    str (sera parseado em `to_internal_value`) ou dict (JSON puro).
    """

    arquivo = serializers.FileField()
    mapeamento = serializers.JSONField(binary=False)
    declaracao = serializers.JSONField(binary=False)
    pf_aceite_origem = serializers.CharField(
        max_length=40, required=False, allow_blank=True, default=""
    )
    cpf_responsavel_destino = serializers.ChoiceField(
        choices=("atributo_pj", "contato_pf_separado", "descartar"),
        default="contato_pf_separado",
    )
    skip_invalid = serializers.BooleanField(default=False)
    update_existing = serializers.BooleanField(default=True)

    def validate_declaracao(self, value):
        """Garante shape do dict + decodifica via DeclaracaoProcedenciaSerializer."""
        decl_ser = DeclaracaoProcedenciaSerializer(data=value)
        decl_ser.is_valid(raise_exception=True)
        return decl_ser.validated_data
