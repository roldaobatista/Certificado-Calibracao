"""Use case `decidir_ponto_reconciliacao` — M8 Fatia 2a (T-CER-040, NC-03).

PRÉ-CONDIÇÃO separada da emissão: o RT decide o destino de um ponto problemático
(fora da declarada / sem CMC / U<CMC) ANTES de `emitir_certificado`. Decisão WORM
(padrão ADR-0070) ligada a `calibracao_id` (existe antes do certificado). Use case
PURO (ADR-0007). Idempotência própria por ponto.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)
from src.domain.metrologia.certificados.entities import AnaliseReconciliacaoCertificado
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
)
from src.domain.metrologia.certificados.erros import (
    CategoriaIncoerenteError,
    JustificativaInsuficienteError,
)
from src.domain.metrologia.certificados.repository import (
    AnaliseReconciliacaoRepository,
)
from src.domain.metrologia.certificados.transicoes import (
    categoria_coerente,
    exigir_ressalva_nao_rbc,
)

_JUSTIFICATIVA_MIN = 20  # chars (cl. 7.10.1 — razão objetiva)


@dataclass(frozen=True, slots=True)
class DecidirPontoInput:
    tenant_id: UUID
    calibracao_id: UUID
    ponto_calibracao: Decimal
    classificacao: ClassificacaoPonto  # da reconciliação mostrada ao RT
    decisao_rt: DecisaoReconciliacaoRT
    categoria_motivo: CategoriaMotivoExclusao
    justificativa: str
    correlation_id: UUID
    criado_em: datetime
    ressalva_nao_rbc: str = ""
    decisor_id_hash: str = ""


def _hash_justificativa(texto: str) -> str:
    digest = hashlib.sha256(
        canonicalizar_payload_para_hmac({"justificativa": texto})
    ).digest()
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, digest)


def decidir_ponto_reconciliacao(
    inp: DecidirPontoInput, *, analise_repo: AnaliseReconciliacaoRepository
) -> AnaliseReconciliacaoCertificado:
    """Crava a decisão WORM do RT para um ponto. Idempotente: se já existe decisão
    para (calibração, ponto), devolve a existente (replay) sem duplicar."""
    if analise_repo.existe_decisao_para_ponto(
        tenant_id=inp.tenant_id,
        calibracao_id=inp.calibracao_id,
        ponto_calibracao=inp.ponto_calibracao,
    ):
        mapa = analise_repo.obter_decisao_por_ponto(
            tenant_id=inp.tenant_id, calibracao_id=inp.calibracao_id
        )
        return mapa[inp.ponto_calibracao]

    if not categoria_coerente(inp.classificacao, inp.categoria_motivo):
        raise CategoriaIncoerenteError(
            f"categoria {inp.categoria_motivo.value} incoerente com classificacao "
            f"{inp.classificacao.value} (cl. 7.10.1)"
        )
    exigir_ressalva_nao_rbc(inp.decisao_rt, inp.ressalva_nao_rbc)

    just = inp.justificativa.strip()
    if len(just) < _JUSTIFICATIVA_MIN:
        raise JustificativaInsuficienteError(
            f"justificativa exige >= {_JUSTIFICATIVA_MIN} chars; recebeu {len(just)}"
        )

    decisao = AnaliseReconciliacaoCertificado(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        calibracao_id=inp.calibracao_id,
        ponto_calibracao=inp.ponto_calibracao,
        decisao_rt=inp.decisao_rt,
        categoria_motivo=inp.categoria_motivo,
        justificativa_canonicalizada=just,
        justificativa_hash=_hash_justificativa(just),
        criado_em=inp.criado_em,
        correlation_id=inp.correlation_id,
        ressalva_nao_rbc=inp.ressalva_nao_rbc,
        decisor_id_hash=inp.decisor_id_hash,
    )
    analise_repo.salvar_decisao(decisao)
    return decisao
