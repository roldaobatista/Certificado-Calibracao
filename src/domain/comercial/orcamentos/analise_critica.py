"""Análise crítica cl. 7.1 ISO 17025 — função PURA de decisão perfil-aware (T-ORC-033).

Núcleo da Onda 2c-2. Implementa a matriz validada pelo subagente
`consultor-rbc-iso17025` em `docs/faseamento/orcamentos/analise-critica-matriz.md`.

Arquitetura (matriz §"Implementação"):
  - As PORTAS (`escopos_cmc.cobre`, `procedimentos.cobre_procedimento`) são chamadas
    na VIEW/infra (lado sujo); os resultados por item viram ``ResultadoItemMensurando``
    e são passados a ``decidir_analise_critica`` — função PURA, testável sem banco.
  - Perfil regulatório (A/B/C/D/"") e suspensão de acreditação são resolvidos
    server-side na view (``obter_perfil_tenant_corrente`` / ``_consultar_suspensao``)
    e passados aqui — NUNCA vindos do payload (AJUSTE-3).

Matriz (por item de calibração, ``item_ok = cobre_cmc and procedimento_ok``):
  - perfil ""   → ``PerfilIndeterminado`` (fail-closed; não grava análise).
  - perfil D    → ``desabilitada`` (não avalia itens; aprova).
  - A/B/C sem item de calibração → ``aprovada`` (nada metrológico — AJUSTE-1).
  - A suspenso  → ``reprovada`` (não emite RBC durante suspensão — AJUSTE-3).
  - A, algum item_ok=False → ``reprovada`` (fail-closed).
  - A, todos item_ok=True  → ``com_ressalva`` (media): padrão NÃO verificável
                             automaticamente (GATE-ORC-PADRAO / TL-ORC-10).
  - B, algum item_ok=False → ``com_ressalva`` (media): POST público exige confirmação.
  - B, todos item_ok=True  → ``aprovada``.
  - C, algum item_ok=False → ``com_ressalva`` (baixa): log interno, sem confirmação.
  - C, todos item_ok=True  → ``aprovada``.

``snapshot_hash`` (ADR-0029): SHA-256 da canonicalização do registro probatório,
formatado com versão — carimbado no envelope ``orcamento.aprovado`` e verificável
offline (INV-ORC-ANALISE-WORM).

Refs:
  D-ORC-5  — análise crítica perfil-aware via portas
  D-ORC-15 — AnaliseCriticaOrcamento WORM (itens_avaliados ricos C1; norma C6)
  ADR-0029 — canonicalização texto probatório
  ADR-0067 — perfil regulatório do tenant (A/B/C/D)

Zero imports Django / infrastructure.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any
from uuid import UUID

from src.domain.comercial.orcamentos.enums import (
    SeveridadeRessalva,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.erros import PerfilIndeterminado
from src.domain.comercial.orcamentos.transicoes import (
    TEXTO_RESSALVA_PADRAO_INDISPONIVEL,
)
from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)

# =====================================================================
# CONSTANTES
# =====================================================================

NORMA_REFERENCIA_CL71: str = "ISO/IEC 17025:2017 cl. 7.1.1"
"""Literal gravado em ``AnaliseCriticaOrcamento.norma_referencia`` (consultor-rbc C6)."""

TEXTO_RESSALVA_ACREDITACAO_SUSPENSA: str = (
    "Acreditação RBC do laboratório está suspensa nesta data. Enquanto perdurar a "
    "suspensão não é possível emitir certificado sob o escopo acreditado nem com "
    "referência à acreditação RBC (o símbolo de acreditação não pode ser ostentado); "
    "a aprovação do orçamento de calibração acreditada fica bloqueada até o "
    "restabelecimento da acreditação, conforme NIT-DICLA-021 e ISO/IEC 17025:2017 "
    "cl. 7.1.1."
)
"""Ressalva verbatim de suspensão de acreditação (AJUSTE-3 / perfil A suspenso).

PROVISÓRIA — texto sujeito a revisão humana RBC pré-1º tenant A externo
(GATE-ORC-CMC-PREENCHIDO / rastrear C-ORC-SUSPENSAO). Não bloqueia codar.
"""

_PERFIS_VALIDOS = frozenset({"A", "B", "C", "D"})


# =====================================================================
# ENTRADA — resultado das portas por item de calibração (resolvido na infra)
# =====================================================================


@dataclass(frozen=True, slots=True)
class ResultadoItemMensurando:
    """Resultado das portas de análise crítica para UM item de calibração.

    Montado na VIEW/infra a partir de ``escopos_cmc.cobre`` +
    ``procedimentos.cobre_procedimento`` (matriz §"Matriz de decisão"). A função
    pura de decisão consome esta estrutura — nunca chama as portas diretamente.

    ``cmc_reason``: ``""`` se cobre; senão ``"cmc_fora_do_escopo"``/``"erro_interno"``
    (retorno literal de ``cobre``). Os campos ``procedimento_*`` vêm do dict de
    ``cobre_procedimento`` (``procedimento_id``/``codigo``/``versao``/
    ``numero_revisao``/``hash_anexo``) — ``None`` quando nenhum procedimento cobre.
    """

    equipamento_id: UUID
    grandeza: str
    faixa_min: Decimal
    faixa_max: Decimal
    unidade: str
    cobre_cmc: bool
    cmc_reason: str
    procedimento_ok: bool
    procedimento_id: str | None = None
    procedimento_codigo: str | None = None
    procedimento_versao: str | None = None
    procedimento_revisao: str | None = None
    procedimento_hash_anexo: str | None = None

    @property
    def item_ok(self) -> bool:
        """Viabilidade técnica do item: CMC cobre E procedimento vigente existe."""
        return self.cobre_cmc and self.procedimento_ok


# =====================================================================
# SAÍDA — decisão da análise crítica
# =====================================================================


@dataclass(frozen=True, slots=True)
class DecisaoAnaliseCritica:
    """Resultado da função pura de decisão da análise crítica cl. 7.1.

    ``bloqueia``: True quando ``veredito == reprovada`` — o orçamento NÃO transiciona
    para aprovado (422 ``AnaliseCriticaReprovada``); a análise WORM ainda é gravada.

    ``exige_confirmacao_ressalvas``: True quando ``com_ressalva`` com
    ``severidade=media`` — o POST público (Onda 2e) exige ``ressalvas_confirmadas``
    (cl. 7.1.1-d / D-ORC-7 C2). Irrelevante no canal interno.

    ``itens_avaliados``: registro probatório por item (C1) — JSON-safe, pronto para
    persistir em ``AnaliseCriticaOrcamento.itens_avaliados`` e para o snapshot_hash.
    """

    perfil_normalizado: str  # "A"|"B"|"C"|"D" (validado)
    veredito: VeredictoAnaliseCritica
    severidade: SeveridadeRessalva | None
    itens_avaliados: tuple[dict[str, Any], ...]
    bloqueia: bool
    exige_confirmacao_ressalvas: bool


# =====================================================================
# REGISTRO PROBATÓRIO POR ITEM (C1 / AJUSTE-2)
# =====================================================================


def _ressalvas_de_falha(r: ResultadoItemMensurando) -> list[str]:
    """Ressalvas textuais explicando POR QUE o item não é viável (cl. 7.1.1-a)."""
    ressalvas: list[str] = []
    if not r.cobre_cmc:
        ressalvas.append(
            f"CMC: grandeza {r.grandeza} faixa {r.faixa_min}..{r.faixa_max} "
            f"{r.unidade} fora do escopo acreditado "
            f"({r.cmc_reason or 'cmc_fora_do_escopo'})."
        )
    if not r.procedimento_ok:
        ressalvas.append(
            f"Procedimento de calibração vigente não encontrado para "
            f"{r.grandeza} {r.faixa_min}..{r.faixa_max} {r.unidade}."
        )
    return ressalvas


def _item_avaliado_dict(r: ResultadoItemMensurando, ressalvas: list[str]) -> dict[str, Any]:
    """Dict JSON-safe do registro probatório de um item (AJUSTE-2 / C1).

    ``cmc_codigo_ref`` fica ``None`` em Wave A: a porta ``cobre`` devolve só o
    veredito + motivo, não o código do escopo que cobriu (GATE-ORC-CMC-PREENCHIDO).
    """
    return {
        "equipamento_id": str(r.equipamento_id),
        "grandeza": r.grandeza,
        "faixa_min": str(r.faixa_min),
        "faixa_max": str(r.faixa_max),
        "unidade": r.unidade,
        "cobre_cmc": r.cobre_cmc,
        "cmc_codigo_ref": None,
        "cmc_reason": r.cmc_reason,
        "procedimento_ok": r.procedimento_ok,
        "procedimento_id": r.procedimento_id,
        "procedimento_codigo": r.procedimento_codigo,
        "procedimento_versao": r.procedimento_versao,
        "procedimento_revisao": r.procedimento_revisao,
        "procedimento_hash_anexo": r.procedimento_hash_anexo,
        "ressalvas": list(ressalvas),
    }


# =====================================================================
# FUNÇÃO PURA DE DECISÃO — matriz A/B/C/D
# =====================================================================


def decidir_analise_critica(
    *,
    perfil: str,
    acreditacao_suspensa: bool,
    resultados: Sequence[ResultadoItemMensurando],
) -> DecisaoAnaliseCritica:
    """Decide o veredito da análise crítica cl. 7.1 (matriz perfil-aware D-ORC-5).

    Função PURA: sem I/O, sem Django. Recebe perfil + suspensão + resultados das
    portas (já resolvidos na infra) e devolve a decisão completa.

    Args:
        perfil: char regulatório do tenant ("A"/"B"/"C"/"D"); ``""`` = indeterminado.
        acreditacao_suspensa: True se a acreditação RBC está suspensa nesta data
            (só relevante para perfil A — AJUSTE-3).
        resultados: avaliação por item de calibração (vazio = sem item metrológico
            ou perfil D que não avalia).

    Returns:
        ``DecisaoAnaliseCritica`` com veredito, severidade, itens_avaliados ricos,
        ``bloqueia`` (reprovada) e ``exige_confirmacao_ressalvas`` (público).

    Raises:
        PerfilIndeterminado: perfil vazio ou desconhecido (fail-closed — D-ORC-19).
    """
    perfil_norm = (perfil or "").strip().upper()
    if perfil_norm not in _PERFIS_VALIDOS:
        raise PerfilIndeterminado(
            f"perfil regulatório do tenant indeterminado ({perfil_norm or 'vazio'!r}) — "
            "fail-closed (D-ORC-5 / D-ORC-19).",
            perfil=perfil_norm,
        )

    # Perfil D: análise crítica desabilitada (não avalia itens) — aprova.
    if perfil_norm == "D":
        return DecisaoAnaliseCritica(
            perfil_normalizado=perfil_norm,
            veredito=VeredictoAnaliseCritica.DESABILITADA,
            severidade=None,
            itens_avaliados=(),
            bloqueia=False,
            exige_confirmacao_ressalvas=False,
        )

    # A/B/C sem item de calibração: nada metrológico a avaliar (AJUSTE-1) — aprova.
    if not resultados:
        return DecisaoAnaliseCritica(
            perfil_normalizado=perfil_norm,
            veredito=VeredictoAnaliseCritica.APROVADA,
            severidade=None,
            itens_avaliados=(),
            bloqueia=False,
            exige_confirmacao_ressalvas=False,
        )

    algum_falho = any(not r.item_ok for r in resultados)

    if perfil_norm == "A":
        return _decidir_perfil_a(resultados, algum_falho=algum_falho, suspensa=acreditacao_suspensa)
    if perfil_norm == "B":
        return _decidir_perfil_b(resultados, algum_falho=algum_falho)
    # perfil_norm == "C"
    return _decidir_perfil_c(resultados, algum_falho=algum_falho)


def _decidir_perfil_a(
    resultados: Sequence[ResultadoItemMensurando],
    *,
    algum_falho: bool,
    suspensa: bool,
) -> DecisaoAnaliseCritica:
    """Perfil A (acreditado RBC): fail-closed. Padrão nunca verificável → ressalva."""
    if suspensa:
        # Acreditação suspensa: reprova (não emite RBC durante suspensão — AJUSTE-3).
        itens = tuple(
            _item_avaliado_dict(r, [TEXTO_RESSALVA_ACREDITACAO_SUSPENSA]) for r in resultados
        )
        return DecisaoAnaliseCritica(
            perfil_normalizado="A",
            veredito=VeredictoAnaliseCritica.REPROVADA,
            severidade=None,
            itens_avaliados=itens,
            bloqueia=True,
            exige_confirmacao_ressalvas=False,
        )
    if algum_falho:
        # Fail-closed: algum item fora do escopo CMC ou sem procedimento → reprova.
        itens = tuple(_item_avaliado_dict(r, _ressalvas_de_falha(r)) for r in resultados)
        return DecisaoAnaliseCritica(
            perfil_normalizado="A",
            veredito=VeredictoAnaliseCritica.REPROVADA,
            severidade=None,
            itens_avaliados=itens,
            bloqueia=True,
            exige_confirmacao_ressalvas=False,
        )
    # Todos viáveis, mas o padrão de referência NÃO é verificável automaticamente
    # (GATE-ORC-PADRAO / TL-ORC-10) → com_ressalva media, sempre.
    itens = tuple(_item_avaliado_dict(r, [TEXTO_RESSALVA_PADRAO_INDISPONIVEL]) for r in resultados)
    return DecisaoAnaliseCritica(
        perfil_normalizado="A",
        veredito=VeredictoAnaliseCritica.COM_RESSALVA,
        severidade=SeveridadeRessalva.MEDIA,
        itens_avaliados=itens,
        bloqueia=False,
        exige_confirmacao_ressalvas=True,
    )


def _decidir_perfil_b(
    resultados: Sequence[ResultadoItemMensurando],
    *,
    algum_falho: bool,
) -> DecisaoAnaliseCritica:
    """Perfil B (capacidade interna declarada): fail-open lazy com ressalva media."""
    if algum_falho:
        itens = tuple(_item_avaliado_dict(r, _ressalvas_de_falha(r)) for r in resultados)
        return DecisaoAnaliseCritica(
            perfil_normalizado="B",
            veredito=VeredictoAnaliseCritica.COM_RESSALVA,
            severidade=SeveridadeRessalva.MEDIA,
            itens_avaliados=itens,
            bloqueia=False,
            exige_confirmacao_ressalvas=True,
        )
    itens = tuple(_item_avaliado_dict(r, []) for r in resultados)
    return DecisaoAnaliseCritica(
        perfil_normalizado="B",
        veredito=VeredictoAnaliseCritica.APROVADA,
        severidade=None,
        itens_avaliados=itens,
        bloqueia=False,
        exige_confirmacao_ressalvas=False,
    )


def _decidir_perfil_c(
    resultados: Sequence[ResultadoItemMensurando],
    *,
    algum_falho: bool,
) -> DecisaoAnaliseCritica:
    """Perfil C (parcial/warning): ressalva baixa, log interno, sem confirmação."""
    if algum_falho:
        itens = tuple(_item_avaliado_dict(r, _ressalvas_de_falha(r)) for r in resultados)
        return DecisaoAnaliseCritica(
            perfil_normalizado="C",
            veredito=VeredictoAnaliseCritica.COM_RESSALVA,
            severidade=SeveridadeRessalva.BAIXA,
            itens_avaliados=itens,
            bloqueia=False,
            exige_confirmacao_ressalvas=False,
        )
    itens = tuple(_item_avaliado_dict(r, []) for r in resultados)
    return DecisaoAnaliseCritica(
        perfil_normalizado="C",
        veredito=VeredictoAnaliseCritica.APROVADA,
        severidade=None,
        itens_avaliados=itens,
        bloqueia=False,
        exige_confirmacao_ressalvas=False,
    )


# =====================================================================
# SNAPSHOT HASH — ADR-0029 (carimbado no envelope orcamento.aprovado)
# =====================================================================


def calcular_snapshot_hash_analise(
    *,
    orcamento_id: UUID,
    versao_id: UUID,
    perfil: str,
    veredito: VeredictoAnaliseCritica,
    norma_referencia: str,
    itens_avaliados: tuple[dict[str, Any], ...],
    avaliada_em: datetime,
    avaliada_por: str,
) -> str:
    """Hash versionado (ADR-0029) do registro probatório da análise crítica.

    ``sha256(canonicalizar_payload_para_hmac(payload)).digest()`` formatado com
    ``VERSAO_HMAC_ATUAL``. Determinístico e verificável offline — o mesmo hash vai
    no envelope ``orcamento.aprovado`` (``analise_critica_snapshot_hash``) e prova o
    que foi avaliado (INV-ORC-ANALISE-WORM).
    """
    payload = {
        "orcamento_id": str(orcamento_id),
        "versao_id": str(versao_id),
        "perfil_no_evento": perfil,
        "veredito": veredito.value,
        "norma_referencia": norma_referencia,
        "itens_avaliados": list(itens_avaliados),
        "avaliada_em": avaliada_em.isoformat(),
        "avaliada_por": avaliada_por,
    }
    digest = sha256(canonicalizar_payload_para_hmac(payload)).digest()
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, digest)
