"""Mappers model PG <-> snapshot de dominio (M5 — ADR-0007).

Centraliza a serializacao dos VOs metrologicos (Grandeza/FaixaMedicao/
IncertezaExpandida) no shape JSON CANONICO usado nas colunas JSONField de
`PadraoMetrologico` (e no `snapshot_padrao_json` de M4.PadraoUsado). Tanto o
lado de leitura (`query_service`) quanto o de escrita (repositories — P5)
usam estas funcoes — uma fonte unica evita drift de shape (Decimal sempre
serializado como str pra nao perder precisao).

Shape canonico:
- grandezas: list[str]  (Grandeza.value)
- faixas: list[{"inferior": str, "superior": str, "unidade": str}]
- incertezas: list[{"valor": str, "fator_k": str, "nivel_confianca": str,
                    "unidade": str, "graus_liberdade_efetivos": int | None}]
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.domain.metrologia.padroes.entities import (
    PadraoMetrologicoSnapshot,
    PadraoUsadoSnapshot,
)
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    EstadoPadrao,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)


# --------------------------------------------------------------------------
# VO <-> JSON (shape canonico)
# --------------------------------------------------------------------------
def grandezas_para_json(grandezas: tuple[Grandeza, ...]) -> list[str]:
    return [g.value for g in grandezas]


def grandezas_de_json(raw: list[Any]) -> tuple[Grandeza, ...]:
    return tuple(Grandeza.from_string(str(g)) for g in raw)


def faixas_para_json(faixas: tuple[FaixaMedicao, ...]) -> list[dict[str, str]]:
    return [
        {"inferior": str(f.inferior), "superior": str(f.superior), "unidade": f.unidade}
        for f in faixas
    ]


def faixas_de_json(raw: list[dict[str, Any]]) -> tuple[FaixaMedicao, ...]:
    return tuple(
        FaixaMedicao(
            inferior=Decimal(str(d["inferior"])),
            superior=Decimal(str(d["superior"])),
            unidade=str(d["unidade"]),
        )
        for d in raw
    )


def incertezas_para_json(
    incertezas: tuple[IncertezaExpandida, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "valor": str(u.valor),
            "fator_k": str(u.fator_k),
            "nivel_confianca": str(u.nivel_confianca),
            "unidade": u.unidade,
            "graus_liberdade_efetivos": u.graus_liberdade_efetivos,
        }
        for u in incertezas
    ]


def incertezas_de_json(raw: list[dict[str, Any]]) -> tuple[IncertezaExpandida, ...]:
    return tuple(
        IncertezaExpandida(
            valor=Decimal(str(d["valor"])),
            fator_k=Decimal(str(d["fator_k"])),
            nivel_confianca=Decimal(str(d["nivel_confianca"])),
            unidade=str(d["unidade"]),
            graus_liberdade_efetivos=d.get("graus_liberdade_efetivos"),
        )
        for d in raw
    )


# --------------------------------------------------------------------------
# Model -> Snapshot
# --------------------------------------------------------------------------
def model_para_snapshot(model: Any) -> PadraoMetrologicoSnapshot:
    """PadraoMetrologico (Django) -> PadraoMetrologicoSnapshot (dominio)."""
    return PadraoMetrologicoSnapshot(
        id=model.id,
        tenant_id=model.tenant_id,
        numero_serie=model.numero_serie,
        fabricante=model.fabricante,
        modelo=model.modelo,
        subtipo=SubtipoPadrao(model.subtipo),
        grandezas=grandezas_de_json(model.grandezas),
        faixas=faixas_de_json(model.faixas),
        incertezas_certificado=incertezas_de_json(model.incertezas_certificado),
        vinculacao=VinculacaoCadeia(model.vinculacao),
        classe=ClassePadrao(model.classe),
        cert_externo_storage_key=model.cert_externo_storage_key,
        validade_certificado_rastreabilidade=model.validade_certificado_rastreabilidade,
        proximo_recal=model.proximo_recal,
        intervalo_recal_meses=model.intervalo_recal_meses,
        intervalo_vi_meses=model.intervalo_vi_meses,
        criterio_intervalo=model.criterio_intervalo,
        estado=EstadoPadrao(model.estado),
        revision=model.revision,
        rastreabilidade_origem_revogada=model.rastreabilidade_origem_revogada,
        vigencia_inicio=model.vigencia_inicio,
        correlation_id=model.correlation_id,
        descricao=model.descricao,
        localizacao_lab=model.localizacao_lab,
        revogado_em=model.revogado_em,
        motivo_revogacao=model.motivo_revogacao,
    )


def model_para_usado_snapshot(
    model: Any,
    leituras_ambientais: tuple[tuple[Grandeza, Decimal], ...] = (),
) -> PadraoUsadoSnapshot:
    """PadraoMetrologico -> PadraoUsadoSnapshot (VO imutavel consumido por M4).

    `leituras_ambientais` vem dos auxiliares vinculados (C-8) — o query_service
    coleta antes de chamar.
    """
    return PadraoUsadoSnapshot(
        padrao_id=model.id,
        numero_serie=model.numero_serie,
        fabricante=model.fabricante,
        modelo=model.modelo,
        classe=ClassePadrao(model.classe),
        vinculacao=VinculacaoCadeia(model.vinculacao),
        grandezas=grandezas_de_json(model.grandezas),
        faixas=faixas_de_json(model.faixas),
        incertezas_certificado=incertezas_de_json(model.incertezas_certificado),
        validade_certificado_rastreabilidade=model.validade_certificado_rastreabilidade,
        leituras_ambientais_auxiliares=leituras_ambientais,
    )
