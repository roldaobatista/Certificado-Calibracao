"""Serializers REST do módulo `colaboradores` (T-COL-034).

Choke-point ÚNICO de mascaramento PII (D-COL-7 / INV-COL-PII-MASCARA):
  filtrar_visao_pii(papeis_solicitante, eh_proprio, dados) → dados mascarados.

Regras (spec §3 D-COL-7 / TL-COL-05 / ADV-COL-04):
  CPF       → só DONO (demais: `***.***.***-NN` — últimos 2 dígitos).
  e-mail    → Dono/Gerente/próprio colaborador.
  telefone  → Dono/Gerente/próprio colaborador.
  foto_*    → Dono/Gerente + próprio (por omissão: URL segura se Gerente).
  documentos[] (CTPS/CNH) → Dono + próprio: storage_key/sha256 redigidos para
    quem não é DONO nem próprio (INV-COL-PII-MASCARA / exports.md:40).
  Fail-closed: sem papel reconhecido → campo mascarado.

Serializer `ElegivelDTO` (INV-COL-ELEGIVEIS-MINIMO):
  Allowlist SEPARADA — NUNCA CPF/e-mail/telefone/documentos/comissão/foto.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.domain.rh_frota_qualidade.colaboradores.enums import (
    NivelHabilidade,
    PapelColaborador,
    TipoDocumento,
    Vinculo,
)

# ---------------------------------------------------------------------------
# Matriz de visibilidade PII (D-COL-7 / TL-COL-05 / ADV-COL-04)
# ---------------------------------------------------------------------------

# True → papel pode ver o campo sem mascaramento
# Fail-closed: chave ausente → mascarado
_DONO = PapelColaborador.DONO.value
_GERENTE = PapelColaborador.GERENTE.value
_TECNICO = PapelColaborador.TECNICO.value
_ATENDENTE = PapelColaborador.ATENDENTE.value
_SIGNATARIO = PapelColaborador.SIGNATARIO.value
_QUALIDADE = PapelColaborador.QUALIDADE.value
_MOTORISTA = PapelColaborador.MOTORISTA_UMC.value

# MATRIZ_VISAO_PII[campo][papel] = True se visível (sem ser o próprio)
# Nota: documentos[] com tipo CTPS/CNH são filtrados separadamente em
# filtrar_visao_pii (lógica de lista, não campo escalar).
MATRIZ_VISAO_PII: dict[str, dict[str, bool]] = {
    "cpf": {
        _DONO: True,
    },
    "email": {
        _DONO: True,
        _GERENTE: True,
    },
    "telefone": {
        _DONO: True,
        _GERENTE: True,
    },
    "foto_storage_key": {
        _DONO: True,
        _GERENTE: True,
    },
}

# Tipos de documento restritos a DONO + próprio (INV-COL-PII-MASCARA / D-COL-7)
_TIPOS_DOC_RESTRITOS: frozenset[str] = frozenset({"ctps", "cnh"})

_MASCARA_CPF_DEFAULT = "***.***.***-{ultimos2}"


def _mascarar_cpf(cpf_value: str) -> str:
    """Retorna CPF com últimos 2 dígitos visíveis (D-COL-7)."""
    digits = cpf_value.replace(".", "").replace("-", "")
    ultimos2 = digits[-2:] if len(digits) >= 2 else "**"
    return f"***.***.***-{ultimos2}"


def filtrar_visao_pii(
    papeis_solicitante: set[str],
    *,
    eh_proprio: bool,
    dados: dict[str, Any],
) -> dict[str, Any]:
    """Choke-point único de mascaramento PII (D-COL-7 / INV-COL-PII-MASCARA).

    Aplica MATRIZ_VISAO_PII para decidir o que o solicitante pode ver.
    `eh_proprio=True` quando o solicitante é o próprio colaborador.

    Regras:
    - CPF: só DONO (ou próprio) → `***.***.***-NN` (últimos 2 dígitos).
    - e-mail/telefone: Dono/Gerente/próprio.
    - foto: Dono/Gerente/próprio.
    - documentos[] com tipo CTPS/CNH: DONO ou próprio vêem em claro;
      demais papéis recebem storage_key=None e sha256=None (redigidos).
    - Fail-closed: sem papel reconhecido → mascarado.

    Args:
        papeis_solicitante: set de PapelColaborador.value do usuário autenticado.
        eh_proprio:         True se o solicitante é o próprio colaborador.
        dados:              dict cru de campos do colaborador.

    Returns:
        dict filtrado com PII mascarada conforme papéis.
    """
    resultado = dict(dados)

    for campo, regras_papel in MATRIZ_VISAO_PII.items():
        if campo not in resultado:
            continue

        # Próprio colaborador sempre vê seus próprios dados
        if eh_proprio:
            continue

        # Verifica se algum papel do solicitante permite ver este campo
        pode_ver = any(regras_papel.get(p, False) for p in papeis_solicitante)

        if not pode_ver:
            # Mascaramento específico por campo
            if campo == "cpf":
                valor_original = resultado.get("cpf", "")
                if valor_original and isinstance(valor_original, str):
                    resultado["cpf"] = _mascarar_cpf(valor_original)
                else:
                    resultado["cpf"] = "***.***.***-**"
            else:
                # Campos ocultos viram None
                resultado[campo] = None

    # Filtra documentos[] com tipo CTPS/CNH (INV-COL-PII-MASCARA / exports.md:40).
    # DONO ou próprio colaborador vêem em claro; demais têm storage_key/sha256 redigidos.
    if "documentos" in resultado and isinstance(resultado["documentos"], list):
        pode_ver_docs_restritos = eh_proprio or (_DONO in papeis_solicitante)
        if not pode_ver_docs_restritos:
            documentos_filtrados = []
            for doc in resultado["documentos"]:
                tipo_val = (doc.get("tipo") or "").lower()
                if tipo_val in _TIPOS_DOC_RESTRITOS:
                    # Redige campos sensíveis mas mantém id/tipo/data para auditoria
                    doc = dict(doc)
                    doc["storage_key"] = None
                    doc["sha256"] = None
                documentos_filtrados.append(doc)
            resultado["documentos"] = documentos_filtrados

    return resultado


# ---------------------------------------------------------------------------
# Serializers de entrada
# ---------------------------------------------------------------------------


class ColaboradorCreateSerializer(serializers.Serializer):
    """Serializer de criação de colaborador."""

    nome = serializers.CharField(max_length=200)
    cpf = serializers.CharField(max_length=14, help_text="CPF (11 dígitos ou com pontuação)")
    email = serializers.EmailField(max_length=254)
    telefone = serializers.CharField(max_length=20)
    vinculo = serializers.ChoiceField(choices=[(v.value, v.value) for v in Vinculo])
    data_admissao = serializers.DateField()
    comissao_default_pct = serializers.DecimalField(max_digits=5, decimal_places=2)
    observacao = serializers.CharField(required=False, default="", allow_blank=True)
    usuario_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class ColaboradorUpdateSerializer(serializers.Serializer):
    """Serializer de edição parcial de colaborador (PATCH)."""

    nome = serializers.CharField(max_length=200, required=False)
    email = serializers.EmailField(max_length=254, required=False)
    telefone = serializers.CharField(max_length=20, required=False)
    vinculo = serializers.ChoiceField(choices=[(v.value, v.value) for v in Vinculo], required=False)
    data_admissao = serializers.DateField(required=False)
    comissao_default_pct = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    observacao = serializers.CharField(required=False, allow_blank=True)
    usuario_id = serializers.UUIDField(required=False, allow_null=True)


class DesligarColaboradorSerializer(serializers.Serializer):
    """Serializer de desligamento (destroy = desligamento em D-COL-3)."""

    data_desligamento = serializers.DateField()
    motivo_desligamento = serializers.CharField(max_length=500)


class AtribuirPapelSerializer(serializers.Serializer):
    """Serializer de atribuição de papel."""

    papel = serializers.ChoiceField(choices=[(p.value, p.value) for p in PapelColaborador])
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField(required=False, allow_null=True)
    responsabilidade_tecnica_id = serializers.UUIDField(required=False, allow_null=True)
    tem_cnh = serializers.BooleanField(required=False, default=True)


class RevogarPapelSerializer(serializers.Serializer):
    """Serializer de revogação de papel."""

    papel_id = serializers.UUIDField()


class RegistrarHabilidadeSerializer(serializers.Serializer):
    """Serializer de registro de habilidade."""

    nivel = serializers.ChoiceField(choices=[(n.value, n.value) for n in NivelHabilidade])
    data_avaliacao = serializers.DateField()
    catalogo_id = serializers.UUIDField(required=False, allow_null=True)
    descricao_livre = serializers.CharField(max_length=300, required=False, allow_null=True)
    evidencia_url = serializers.CharField(max_length=500, required=False, allow_null=True)


class AnexarDocumentoSerializer(serializers.Serializer):
    """Serializer de upload de documento (multipart)."""

    tipo = serializers.ChoiceField(choices=[(t.value, t.value) for t in TipoDocumento])
    data_validade = serializers.DateField(required=False, allow_null=True)
    # arquivo via request.FILES['arquivo']


# ---------------------------------------------------------------------------
# Serializers de saída — passam por filtrar_visao_pii
# ---------------------------------------------------------------------------


class PapelColaboradorOutputSerializer(serializers.Serializer):
    """Papel de colaborador — saída (sem PII)."""

    id = serializers.UUIDField()
    papel = serializers.CharField()
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField(allow_null=True)
    revogado_em = serializers.DateTimeField(allow_null=True)
    responsabilidade_tecnica_id = serializers.UUIDField(allow_null=True)
    pendencia_cnh = serializers.BooleanField()


class HabilidadeOutputSerializer(serializers.Serializer):
    """Habilidade — saída (sem PII)."""

    id = serializers.UUIDField()
    nivel = serializers.CharField()
    data_avaliacao = serializers.DateField()
    catalogo_id = serializers.CharField(allow_null=True)
    descricao_livre = serializers.CharField(allow_null=True)
    evidencia_url = serializers.CharField(allow_null=True)


class DocumentoOutputSerializer(serializers.Serializer):
    """Documento — saída (storage_key / sha256 sem PII textual)."""

    id = serializers.UUIDField()
    tipo = serializers.CharField()
    storage_key = serializers.CharField()
    sha256 = serializers.CharField()
    data_upload = serializers.DateTimeField()
    data_validade = serializers.DateField(allow_null=True)


class ColaboradorDetailSerializer(serializers.Serializer):
    """Colaborador detalhado — saída mascarada por filtrar_visao_pii.

    O campo `papeis_solicitante` e `eh_proprio` são passados externamente
    pela view para que filtrar_visao_pii seja aplicado antes de retornar.
    """

    id = serializers.UUIDField()
    tenant_id = serializers.UUIDField()
    nome = serializers.CharField()
    cpf = serializers.CharField()  # mascarado por filtrar_visao_pii
    email = serializers.CharField(allow_null=True)  # mascarado
    telefone = serializers.CharField(allow_null=True)  # mascarado
    vinculo = serializers.CharField()
    data_admissao = serializers.DateField()
    comissao_default_pct = serializers.DecimalField(max_digits=5, decimal_places=2)
    observacao = serializers.CharField()
    usuario_id = serializers.UUIDField(allow_null=True)
    foto_storage_key = serializers.CharField(allow_null=True)  # mascarado
    data_desligamento = serializers.DateField(allow_null=True)
    motivo_desligamento = serializers.CharField(allow_null=True)
    ativo = serializers.BooleanField()
    papeis = PapelColaboradorOutputSerializer(many=True)
    habilidades = HabilidadeOutputSerializer(many=True)
    documentos = DocumentoOutputSerializer(many=True)


# ---------------------------------------------------------------------------
# DTO /elegiveis — allowlist mínima (INV-COL-ELEGIVEIS-MINIMO)
# ---------------------------------------------------------------------------


class HabilidadeElegivelSerializer(serializers.Serializer):
    """Habilidade no DTO de elegível (sem PII)."""

    nivel = serializers.CharField()
    descricao = serializers.CharField()


class ElegivelDTOSerializer(serializers.Serializer):
    """DTO mínimo para /elegiveis (INV-COL-ELEGIVEIS-MINIMO / ADV-COL-04).

    NUNCA incluir: cpf/e-mail/telefone/documentos/comissão/foto/vínculo/observação.
    Allowlist EXPLÍCITA — fail-closed por construção.
    """

    colaborador_id = serializers.UUIDField()
    nome_exibicao = serializers.CharField()
    papel = serializers.CharField(allow_null=True)
    habilidades = HabilidadeElegivelSerializer(many=True)
    ativo = serializers.BooleanField()


class ComissaoVigenteSerializer(serializers.Serializer):
    """Resposta de /comissao-vigente (D-COL-9 / AC-COL-04)."""

    pct_default = serializers.DecimalField(max_digits=5, decimal_places=2)
    vigente_desde = serializers.DateField()
