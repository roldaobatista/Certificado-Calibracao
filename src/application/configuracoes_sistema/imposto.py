"""Use cases `cadastrar_imposto` + `encerrar_vigencia_imposto` — US-CFG-003 (T-CFG-031). PUROS.

Linha de imposto é VERSIONADA e IMUTÁVEL (INV-CFG-IMPOSTO-IMUTAVEL): alíquota
nova = NOVA linha com nova vigência; alterar = nunca. A não-sobreposição tem duas
camadas: defesa no domínio (`ha_sobreposicao_vigencia`, mensagem clara) +
exclusion constraint `btree_gist` no banco (a VERDADE — INV-CFG-IMPOSTO-SEM-
SOBREPOSICAO). INV-026 fecha no CONSUMIDOR (documento emitido snapshota a
alíquota usada — TL-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.configuracoes_sistema.entities import Imposto
from src.domain.configuracoes_sistema.enums import TipoImposto
from src.domain.configuracoes_sistema.erros import ImpostoVigenciaSobrepostaError
from src.domain.configuracoes_sistema.repository import ImpostoRepository
from src.domain.configuracoes_sistema.transicoes import ha_sobreposicao_vigencia
from src.domain.configuracoes_sistema.value_objects import Aliquota
from src.domain.shared.value_objects import JanelaVigencia


@dataclass(frozen=True, slots=True)
class CadastrarImpostoInput:
    tenant_id: UUID
    tipo: TipoImposto
    aliquota: Decimal  # validada pelo VO (0..100) — ValueError → 400
    vigencia_inicio: datetime  # tz-aware (INV-VIG-004)
    vigencia_fim: datetime | None = None  # None = aberta
    filial_id: UUID | None = None  # None = catálogo do tenant inteiro
    cfop_padrao: str = ""
    ncm_padrao: str = ""
    iss_retido_fonte: bool = False
    tem_st: bool = False
    simples_excedeu_sublimite: bool = False
    observacoes: str = ""


def cadastrar_imposto(inp: CadastrarImpostoInput, *, repo: ImpostoRepository) -> Imposto:
    """Nova linha de catálogo (AC-CFG-003-1/2). Sobreposição → 422."""
    imposto = Imposto(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        tipo=inp.tipo,
        aliquota=Aliquota(valor=inp.aliquota),
        vigencia=JanelaVigencia(inicio=inp.vigencia_inicio, fim=inp.vigencia_fim),
        filial_id=inp.filial_id,
        cfop_padrao=inp.cfop_padrao,
        ncm_padrao=inp.ncm_padrao,
        iss_retido_fonte=inp.iss_retido_fonte,
        tem_st=inp.tem_st,
        simples_excedeu_sublimite=inp.simples_excedeu_sublimite,
        observacoes=inp.observacoes,
    )
    existentes = [
        e
        for e in repo.listar(tenant_id=inp.tenant_id, tipo=inp.tipo, filial_id=inp.filial_id)
        if e.vigencia.revogado_em is None  # revogada sai da resolução (0004 WHERE)
    ]
    if ha_sobreposicao_vigencia(existentes, imposto):
        raise ImpostoVigenciaSobrepostaError(
            f"vigência sobrepõe linha existente de {inp.tipo.value} "
            f"(encerre a vigência anterior antes — D-CFG-3)."
        )
    repo.salvar_nova_linha(imposto)
    return imposto


@dataclass(frozen=True, slots=True)
class EncerrarVigenciaInput:
    tenant_id: UUID
    imposto_id: UUID
    fim: datetime  # tz-aware; one-shot NULL→data (D-CFG-3)

    def __post_init__(self) -> None:
        if self.fim.tzinfo is None:
            raise ValueError("encerrar_vigencia: fim exige datetime tz-aware.")


def encerrar_vigencia_imposto(inp: EncerrarVigenciaInput, *, repo: ImpostoRepository) -> None:
    """Encerra a vigência ABERTA da linha (one-shot). Linha já encerrada/
    revogada/inexistente → RuntimeError do repo (view mapeia 409)."""
    repo.encerrar_vigencia(tenant_id=inp.tenant_id, imposto_id=inp.imposto_id, fim=inp.fim)
