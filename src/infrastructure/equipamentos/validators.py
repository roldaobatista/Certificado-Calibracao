"""Validators anti-PII para o modulo equipamentos (T-EQP-005).

INV-EQP-LOC-001 (AC-EQP-001-4):
    `localizacao_fisica` e texto livre que NAO PODE conter PII direta —
    nem do tenant nem de terceiros. Razao: o campo aparece em listagem
    operacional e em scan de QR Code (US-EQP-003 ficha 360), visivel
    por tecnicos de campo de outros tenants (cessao temporaria) e por
    clientes finais via portal-cliente.

Padroes detectados (heuristica conservadora — best-effort, NAO
substitui revisao humana; LGPD art. 5º I + INV-EQP-LOC-001):

1. CPF: 11 digitos consecutivos ou com mascara (`123.456.789-01`,
   `12345678901`).
2. CNPJ: 14 digitos consecutivos ou com mascara
   (`12.345.678/0001-90`, `12345678000190`).
3. E-mail: `algo@algo.tld`.
4. Telefone BR: `(11) 9 9999-9999`, `11999999999`, `+5511999999999`.
5. ≥2 nomes proprios capitalizados consecutivos (`Joao Silva`,
   `Maria Santos da Costa`).

Falsos positivos esperados (aceitos como cost da defesa):
- Codigos internos com padrao 14 digitos (`SN-12345678901234`) —
  cliente reformula como `SN-LAB-001`.
- Marcas com capitalizacao (`Toledo Industrial`) — cliente reformula
  como `Sala Toledo` ou `Toledo - SP`.
"""

from __future__ import annotations

import re
from typing import Final

# CPF: 11 digitos com ou sem mascara.
_RE_CPF: Final[re.Pattern[str]] = re.compile(
    r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b"
)

# CNPJ: 14 digitos com ou sem mascara.
_RE_CNPJ: Final[re.Pattern[str]] = re.compile(
    r"\b\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2}\b"
)

# E-mail (RFC simplificado — basta detectar `x@y.z`).
_RE_EMAIL: Final[re.Pattern[str]] = re.compile(
    r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}",
    re.IGNORECASE,
)

# Telefone BR: DDD (2 digitos) + 8 ou 9 digitos. Aceita parenteses,
# espacos, hifens, +55, etc.
_RE_TELEFONE: Final[re.Pattern[str]] = re.compile(
    r"(?:\+?55[\s\-]?)?(?:\(?\d{2}\)?[\s\-]?)?9?\d{4}[\s\-]?\d{4}"
)

# Nomes proprios consecutivos: 2 ou mais palavras comecando com letra
# maiuscula. Aceita preposicoes minusculas (`da`, `de`, `do`, `dos`,
# `das`) entre elas. Limita a janelas de ate 4 palavras pra reduzir
# falso positivo em texto comprido.
_RE_NOMES_CONSECUTIVOS: Final[re.Pattern[str]] = re.compile(
    r"\b[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]{2,}"
    r"(?:\s+(?:da|de|do|dos|das|von|van)\s+)?"
    r"\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]{2,}\b"
)

LIMITE_LOCALIZACAO_FISICA: Final[int] = 200

MENSAGEM_REJEICAO_PII_DIRETA: Final[str] = (
    "LGPD art. 5º I + INV-EQP-LOC-001 — descreva sem nomes/documentos "
    "(detectada PII direta: CPF/CNPJ/e-mail/telefone/nomes próprios "
    "consecutivos)."
)

MENSAGEM_LIMITE_LOCALIZACAO: Final[str] = (
    f"localizacao_fisica nao pode passar de {LIMITE_LOCALIZACAO_FISICA} caracteres."
)

# T-EQP-016 (INV-EQP-VERSAO-001): motivo_detalhe em `EquipamentoVersao`
# rejeita PII direta (mesma regex de INV-EQP-LOC-001). LGPD art. 5º I +
# ISO 17025 cl. 7.5 — campo textual de auditoria nao pode ter dado pessoal.
MOTIVO_DETALHE_MIN_CHARS_QUANDO_OBRIGATORIO: Final[int] = 100

MENSAGEM_REJEICAO_MOTIVO_DETALHE_PII: Final[str] = (
    "LGPD art. 5º I + INV-EQP-VERSAO-001 — motivo_detalhe contem PII direta "
    "(CPF/CNPJ/e-mail/telefone/nomes proprios consecutivos). Reformule sem "
    "dados pessoais."
)


# =====================================================================
# T-EQP-013 (INV-025 / AC-EQP-002-2 / P-EQP-A3) — textos canonicos 422
# de rejeicao em mutacao pos-certificado emitido.
#
# Fonte unica: docs/conformidade/equipamentos/textos-rejeicao-422.md
# (revisado pelo advogado-saas-regulado; mudar texto exige PR + bump
# `versao_canonica` no frontmatter do doc + revisao pelo advogado).
#
# `versao_canonica` PRECISA bater com o frontmatter do doc — drift
# auditavel via auditor-drift-docs.
# =====================================================================

TEXTOS_REJEICAO_422_VERSAO_CANONICA: Final[str] = "1.0.0"

TEXTO_T1_TAG: Final[str] = (
    "A TAG operacional nao pode ser alterada porque ja existe certificado "
    "emitido para este equipamento. A TAG aparece no documento tecnico "
    "assinado, e ISO/IEC 17025 cl. 8.4 exige imutabilidade do registro "
    "tecnico pos-emissao. Crie uma nova versao do equipamento (mudanca "
    "controlada documentada) ou registre o caso como anomalia de "
    "identificacao no recebimento."
)

TEXTO_T2_NUMERO_SERIE: Final[str] = (
    "O numero de serie nao pode ser alterado porque ja existe certificado "
    "emitido referenciando este numero. ISO/IEC 17025 cl. 8.4 exige que "
    "a identificacao inequivoca do equipamento no certificado seja "
    "imutavel apos emissao. Se o numero gravado fisicamente esta incorreto "
    "e foi descoberto agora, registre o caso como nao conformidade (NC) "
    "no fluxo do laboratorio — o certificado existente seguira "
    "referenciando o numero ANTERIOR, e o novo numero entrara a partir "
    "da proxima calibracao."
)

TEXTO_T3_FABRICANTE: Final[str] = (
    "O fabricante nao pode ser alterado porque ja existe certificado "
    "emitido referenciando este equipamento. O fabricante aparece no "
    "documento tecnico assinado e altera a rastreabilidade metrologica "
    "(NIT-DICLA-030). Correcao de fabricante apos emissao de certificado "
    "e tratada como nao conformidade (NC) — registre no fluxo do "
    "laboratorio; o certificado existente seguira referenciando o "
    "fabricante ANTERIOR."
)

TEXTO_T4_FALLBACK_GENERICO: Final[str] = (
    "Este campo do equipamento nao pode ser alterado porque ja existe "
    "certificado emitido referenciando-o. ISO/IEC 17025 cl. 8.4 exige "
    "imutabilidade do registro tecnico pos-emissao. Crie uma nova versao "
    "do equipamento (mudanca controlada documentada) ou registre o caso "
    "como nao conformidade no fluxo do laboratorio."
)

TEXTO_T5_DELETE_VERSAO: Final[str] = (
    "Versoes de equipamento nao podem ser excluidas. Cada versao "
    "registrada em `EquipamentoVersao` representa uma mudanca controlada "
    "e auditavel exigida por ISO/IEC 17025 cl. 8.4 (registros tecnicos "
    "retidos). Se a versao foi criada por engano, registre uma nova "
    "versao de correcao citando a versao errada — o historico continua "
    "integro."
)

# Mapeamento campo -> chave T*. Lista FECHADA — mudar exige PR +
# advogado.
_CAMPO_PARA_CHAVE_REJEICAO: Final[dict[str, str]] = {
    "tag": "T1",
    "numero_serie": "T2",
    "fabricante": "T3",
}

_CHAVE_PARA_TEXTO: Final[dict[str, str]] = {
    "T1": TEXTO_T1_TAG,
    "T2": TEXTO_T2_NUMERO_SERIE,
    "T3": TEXTO_T3_FABRICANTE,
    "T4": TEXTO_T4_FALLBACK_GENERICO,
    "T5": TEXTO_T5_DELETE_VERSAO,
}


def texto_rejeicao_422_pos_cert(campo: str) -> str:
    """Retorna o texto canonico T1-T5 pra um campo afetado.

    `campo` = nome do atributo do `Equipamento` (`tag`, `numero_serie`,
    `fabricante`) OU a chave especial `"_delete_versao"` para T5.
    Campos criticos nao listados caem em T4 (fallback generico —
    defesa em profundidade pra futuros campos promovidos a criticos).

    Nunca compor texto inline; nunca passar por LLM. Lista FECHADA —
    AC-EQP-002-2 + P-EQP-A3.
    """
    if campo == "_delete_versao":
        return _CHAVE_PARA_TEXTO["T5"]
    chave = _CAMPO_PARA_CHAVE_REJEICAO.get(campo, "T4")
    return _CHAVE_PARA_TEXTO[chave]


# T-EQP-021 (INV-EQP-VERSAO-001 reuso) — parecer_gestor_texto em
# `AprovacaoPendenteEquipamentoVersao` rejeita PII direta + exige
# >=30 chars (decisao auditavel).
PARECER_GESTOR_MIN_CHARS: Final[int] = 30

MENSAGEM_REJEICAO_PARECER_PII: Final[str] = (
    "LGPD art. 5º I + INV-EQP-VERSAO-001 — parecer_gestor_texto contem "
    "PII direta (CPF/CNPJ/e-mail/telefone/nomes proprios consecutivos). "
    "Reformule sem dados pessoais."
)


def validar_parecer_gestor_texto(valor: str | None) -> None:
    """Valida `parecer_gestor_texto` da Aprovacao (AC-EQP-002b-4).

    - Exige >=30 chars (decisao auditavel ISO 17025 cl. 6.2).
    - SEMPRE anti-PII (mesma regex INV-EQP-VERSAO-001 / INV-EQP-LOC-001).
    """
    texto = (valor or "").strip()
    if len(texto) < PARECER_GESTOR_MIN_CHARS:
        raise ValueError(
            f"parecer_gestor_texto exige >={PARECER_GESTOR_MIN_CHARS} chars "
            f"(atual={len(texto)}). ISO 17025 cl. 6.2 — decisao auditavel."
        )
    if conter_pii_direta(texto):
        raise ValueError(MENSAGEM_REJEICAO_PARECER_PII)


def validar_motivo_detalhe(
    valor: str | None,
    *,
    motivo_obriga_detalhe: bool,
) -> None:
    """Valida `motivo_detalhe` de `EquipamentoVersao` (INV-EQP-VERSAO-001).

    - Quando `motivo_obriga_detalhe=True` (motivos `outros`,
      `substituicao_componente_critico`, `atualizacao_firmware`): exige
      >=100 chars.
    - Quando vazio/None com `motivo_obriga_detalhe=False`: OK (skip).
    - SEMPRE anti-PII se preenchido.
    """
    texto = (valor or "").strip()
    if motivo_obriga_detalhe and len(texto) < MOTIVO_DETALHE_MIN_CHARS_QUANDO_OBRIGATORIO:
        raise ValueError(
            f"motivo_detalhe exige >={MOTIVO_DETALHE_MIN_CHARS_QUANDO_OBRIGATORIO} "
            f"chars quando motivo_mudanca obriga aprovacao (atual={len(texto)})."
        )
    if texto and conter_pii_direta(texto):
        raise ValueError(MENSAGEM_REJEICAO_MOTIVO_DETALHE_PII)


def conter_pii_direta(texto: str) -> bool:
    """True se o texto contiver CPF, CNPJ, e-mail, telefone ou >=2 nomes
    proprios consecutivos.

    Best-effort — heuristica conservadora documentada acima. NAO substitui
    revisao humana de PII em campo livre (LGPD art. 5º I).
    """
    if not texto:
        return False
    if _RE_CPF.search(texto):
        return True
    if _RE_CNPJ.search(texto):
        return True
    if _RE_EMAIL.search(texto):
        return True
    if _RE_TELEFONE.search(texto):
        return True
    if _RE_NOMES_CONSECUTIVOS.search(texto):
        return True
    return False


def validar_localizacao_fisica(valor: str) -> None:
    """Levanta ValueError com mensagem canonica se invalido.

    Usado em DRF serializer (.validate_localizacao_fisica) e em qualquer
    grava direta no modelo (Wave A pode usar em management commands).
    """
    if len(valor) > LIMITE_LOCALIZACAO_FISICA:
        raise ValueError(MENSAGEM_LIMITE_LOCALIZACAO)
    if conter_pii_direta(valor):
        raise ValueError(MENSAGEM_REJEICAO_PII_DIRETA)
