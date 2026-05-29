"""Use case `registrar_verificacao_intermediaria` — US-PAD-003 (M5 T-PAD-024).

Grava uma VI (cl. 6.4.10) WORM. TODOS os perfis fazem VI. Se o tenant e perfil
A (INV-PAD-008 — cartas Shewhart exclusivas perfil A), o use case constroi a
serie de desvios (historico + a VI nova), calcula os limites de controle e
detecta violacoes Western Electric (ADR-0070 read-model). As violacoes
detectadas voltam no Output como SINAL — o RT decide e registra a
`AnaliseCartaControle` WORM em `registrar_analise_carta_controle` (T-PAD-026);
ate la o uso fica bloqueado pela porta `padrao_bloqueado_para_uso` (P4 —
INV-PAD-010). Este use case NAO muta o estado do padrao.

Use case PURO. `acao_corretiva` obrigatoria quando REPROVADO (cl. 7.10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.metrologia.padroes import shewhart
from src.domain.metrologia.padroes.entities import VerificacaoIntermediariaSnapshot
from src.domain.metrologia.padroes.enums import ResultadoVI
from src.domain.metrologia.padroes.repository import (
    PadraoRepository,
    VerificacaoIntermediariaRepository,
)

from .registrar_recal_envio import PadraoNaoEncontradoError

# Minimo de pontos pra calcular limites de controle (sigma amostral n-1).
_MIN_PONTOS_CARTA = 2


class AcaoCorretivaObrigatoriaError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "VI REPROVADO exige acao_corretiva canonicalizada + hash (cl. 7.10)."
        )


@dataclass(frozen=True, slots=True)
class RegistrarVIInput:
    tenant_id: UUID
    padrao_id: UUID
    data_vi: datetime
    executor_id_hash: str
    metodo_canonicalizado: str
    metodo_hash: str
    resultado: ResultadoVI
    tenant_e_perfil_a: bool
    desvio_observado: Decimal | None = None
    acao_corretiva_canonicalizada: str = ""
    acao_corretiva_hash: str = ""

    def __post_init__(self) -> None:
        if self.data_vi.tzinfo is None:
            raise ValueError("data_vi exige datetime tz-aware (INV-VIG-004).")
        if not self.executor_id_hash:
            raise ValueError("executor_id_hash obrigatorio (HashVersionado ADR-0064).")
        if self.resultado == ResultadoVI.REPROVADO and (
            not self.acao_corretiva_canonicalizada or not self.acao_corretiva_hash
        ):
            raise AcaoCorretivaObrigatoriaError
        if self.desvio_observado is not None and not isinstance(
            self.desvio_observado, Decimal
        ):
            raise TypeError("desvio_observado deve ser Decimal (erro metrologico).")


@dataclass(frozen=True, slots=True)
class RegistrarVIOutput:
    vi: VerificacaoIntermediariaSnapshot
    # SINAL Shewhart (so perfil A com >=2 pontos): violacoes + limites + a ordem
    # das VIs na serie (pra mapear indices -> FKs em registrar_analise_carta).
    violacoes: tuple[shewhart.ViolacaoWesternElectric, ...] = ()
    limites: shewhart.LimitesControle | None = None
    serie_vi_ids: tuple[UUID, ...] = field(default_factory=tuple)


def executar(
    inp: RegistrarVIInput,
    repo_padrao: PadraoRepository,
    repo_vi: VerificacaoIntermediariaRepository,
) -> RegistrarVIOutput:
    padrao = repo_padrao.obter_por_id(inp.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(inp.padrao_id)

    vi = VerificacaoIntermediariaSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        padrao_id=inp.padrao_id,
        data_vi=inp.data_vi,
        executor_id_hash=inp.executor_id_hash,
        metodo_canonicalizado=inp.metodo_canonicalizado,
        metodo_hash=inp.metodo_hash,
        resultado=inp.resultado,
        criado_em=inp.data_vi,
        desvio_observado=inp.desvio_observado,
        acao_corretiva_canonicalizada=inp.acao_corretiva_canonicalizada,
        acao_corretiva_hash=inp.acao_corretiva_hash,
    )
    repo_vi.salvar_nova(vi)

    # INV-PAD-008 — Shewhart so perfil A.
    if not inp.tenant_e_perfil_a or inp.desvio_observado is None:
        return RegistrarVIOutput(vi=vi)

    # Serie cronologica de desvios (historico + nova VI). listar_por_padrao
    # vem ordenado por data_vi (Protocol). Mapeia indice -> vi_id.
    historico = repo_vi.listar_por_padrao(inp.padrao_id)
    serie: list[Decimal] = []
    serie_ids: list[UUID] = []
    for v in historico:
        if v.id == vi.id:
            continue  # adapter pode ja ter persistido; evita duplicar
        if v.desvio_observado is not None:
            serie.append(v.desvio_observado)
            serie_ids.append(v.id)
    serie.append(inp.desvio_observado)
    serie_ids.append(vi.id)

    if len(serie) < _MIN_PONTOS_CARTA:
        return RegistrarVIOutput(vi=vi)

    limites = shewhart.calcular_limites(serie)
    violacoes = shewhart.detectar_violacoes(serie, limites)
    return RegistrarVIOutput(
        vi=vi,
        violacoes=tuple(violacoes),
        limites=limites,
        serie_vi_ids=tuple(serie_ids),
    )
