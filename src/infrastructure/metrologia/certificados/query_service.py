"""Read-path da emissão de certificado (M8 Fatia 2b, T-CER-044 read-adapters).

Adapters Django concretos dos Protocols `LeituraOrcamentoPorPontoPort` e
`CmcParaPort` (`domain/.../certificados/portas.py`) + leitura das `Leitura`
agrupadas por ponto → `PontoMedido`. A LÓGICA vive no domínio (ADR-0072 aninhado);
aqui só a travessia PG.

Defesa em profundidade (molde M5/M6/M7): TODA query filtra `tenant_id` EXPLÍCITO
além da RLS. A travessia até a calibração usa `orcamento_incerteza__calibracao_id`
(FK real `OrcamentoIncerteza.calibracao`); NÃO há FK direta calibracao em
`OrcamentoPorPonto`. A média das repetições é calculada em `Decimal` puro (NUNCA
`Avg` do PostgreSQL, que retorna float e perde dígitos — NIT-DICLA-030).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.entities import OrcamentoPorPontoSnapshot
from src.domain.metrologia.calibracao.enums import LeiEscalonamento, MetodoTipoAPonto
from src.domain.metrologia.certificados.reconciliacao import PontoMedido
from src.domain.metrologia.value_objects import Grandeza
from src.infrastructure.calibracao.models import Leitura, OrcamentoPorPonto
from src.infrastructure.metrologia.escopos_cmc.query_service import (
    cmc_para as _cmc_para_escopo,
)


def cmc_para_adapter(
    *, tenant_id: UUID, grandeza: Grandeza, ponto: Decimal, data: date
) -> Decimal | None:
    """Adapter `CmcParaPort`: ponte com `escopos_cmc.query_service.cmc_para`.

    Converte `Grandeza → .value` e `date → datetime` aware UTC (a porta declara
    `date`; o query service de escopos espera `datetime` para filtrar vigência —
    aware evita o fail silencioso naive×aware). `None` = ponto sem CMC RBC vigente
    (fail-closed; o domínio classifica como não-RBC). Injetar SÓ quando o perfil A
    está acreditado-vigente (senão o use case passa `cmc_para=None`)."""
    return _cmc_para_escopo(
        tenant_id=tenant_id,
        grandeza=grandeza.value,
        ponto=ponto,
        data=datetime.combine(data, time.min, tzinfo=UTC),
    )


def _req_decimal(v: Decimal | None, *, campo: str, ponto: Decimal) -> Decimal:
    """Fail-closed: campo probatório por ponto ausente ⇒ orçamento incompleto não
    reconcilia. Os campos `nivel_confianca`/`grau_liberdade_efetivo`/`n_repeticoes`
    são `null=True` no schema (aditividade da migration 0018) mas obrigatórios no
    contrato ADR-0077 (NIT-DICLA-030 §8.2.6) — NULL é dado corrompido, não emite."""
    if v is None:
        raise ValueError(
            f"OrcamentoPorPonto(ponto={ponto}) com '{campo}' ausente — orçamento "
            f"incompleto não reconcilia (fail-closed; ADR-0077/NIT-DICLA-030 §8.2.6)"
        )
    return v


def _req_int(v: int | None, *, campo: str, ponto: Decimal) -> int:
    if v is None:
        raise ValueError(
            f"OrcamentoPorPonto(ponto={ponto}) com '{campo}' ausente — orçamento "
            f"incompleto não reconcilia (fail-closed; ADR-0077/NIT-DICLA-030 §8.2.6)"
        )
    return v


def _orcamento_por_ponto_to_snapshot(m: OrcamentoPorPonto) -> OrcamentoPorPontoSnapshot:
    """Model → `OrcamentoPorPontoSnapshot` (inverte o `bulk_create` do M4; ADR-0077).
    Reconstrói os enums a partir das strings persistidas. Campos probatórios
    `null=True` no schema mas obrigatórios no contrato → fail-closed (`_req_*`)."""
    p = m.ponto_calibracao
    return OrcamentoPorPontoSnapshot(
        id=m.id,
        tenant_id=m.tenant_id,
        orcamento_incerteza_id=m.orcamento_incerteza_id,
        ponto_calibracao=p,
        u_combinada_no_ponto=m.u_combinada_no_ponto,
        U_expandida_no_ponto=m.U_expandida_no_ponto,
        k_no_ponto=m.k_no_ponto,
        nivel_confianca_no_ponto=_req_decimal(
            m.nivel_confianca_no_ponto, campo="nivel_confianca_no_ponto", ponto=p
        ),
        grau_liberdade_efetivo_no_ponto=_req_decimal(
            m.grau_liberdade_efetivo_no_ponto,
            campo="grau_liberdade_efetivo_no_ponto",
            ponto=p,
        ),
        replay_determinismo_hash_no_ponto=m.replay_determinismo_hash_no_ponto,
        metodo_tipo_a_ponto=MetodoTipoAPonto(m.metodo_tipo_a_ponto),
        n_repeticoes_ponto=_req_int(
            m.n_repeticoes_ponto, campo="n_repeticoes_ponto", ponto=p
        ),
        lei_escalonamento_aplicada=LeiEscalonamento(m.lei_escalonamento_aplicada),
        tipo_a_insuficiente=m.tipo_a_insuficiente,
        s_tipo_a_no_ponto=m.s_tipo_a_no_ponto,
    )


def listar_orcamentos_por_ponto(
    *, tenant_id: UUID, calibracao_id: UUID
) -> list[OrcamentoPorPontoSnapshot]:
    """Adapter `LeituraOrcamentoPorPontoPort`: TODOS os `OrcamentoPorPonto` da
    calibração (lookup 1:1 por ponto é responsabilidade do domínio —
    `reconciliar_pontos` detecta duplicidade/ausência fail-closed). Ordenado por
    `ponto_calibracao` ASC (INV-CER-RECONCILIA-004). `tenant_id` explícito + RLS."""
    qs = OrcamentoPorPonto.objects.filter(
        tenant_id=tenant_id, orcamento_incerteza__calibracao_id=calibracao_id
    ).order_by("ponto_calibracao")
    return [_orcamento_por_ponto_to_snapshot(m) for m in qs]


def listar_pontos_medidos(
    *, tenant_id: UUID, calibracao_id: UUID
) -> list[PontoMedido]:
    """`Leitura` agrupada por `ponto_calibracao` → `PontoMedido` (um por ponto
    distinto). `valor_reportado` = média das repetições em `Decimal` puro (sem
    `Avg`/float — preserva dígitos significativos, NIT-DICLA-030). Ordenado por
    ponto ASC. `tenant_id` explícito + RLS."""
    leituras = Leitura.objects.filter(
        tenant_id=tenant_id, calibracao_id=calibracao_id
    ).values("ponto_calibracao", "valor_lido", "unidade")

    valores: dict[Decimal, list[Decimal]] = defaultdict(list)
    unidades: dict[Decimal, str] = {}
    for row in leituras:
        ponto = row["ponto_calibracao"]
        valores[ponto].append(row["valor_lido"])
        unidades[ponto] = row["unidade"]

    resultado: list[PontoMedido] = []
    for ponto in sorted(valores):
        vals = valores[ponto]
        media = sum(vals, Decimal(0)) / Decimal(len(vals))
        resultado.append(
            PontoMedido(
                ponto_calibracao=ponto,
                valor_reportado=media,
                unidade=unidades[ponto],
            )
        )
    return resultado
