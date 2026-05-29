"""Use case `cadastrar_padrao` — US-PAD-001 (M5 T-PAD-020).

Cadastra um PadraoMetrologico novo em estado EM_USO. Use case PURO (ADR-0007):
recebe Input frozen + Repository Protocol; valida invariantes de dominio;
monta o snapshot; persiste via `repo.salvar_novo`.

Invariantes aplicadas aqui (camada de aplicacao — defesa antes do banco):
- INV-PAD-001 — UNIQUE (tenant, numero_serie) via `repo.existe_numero_serie`.
- INV-PAD-002 — cadastro exige >=1 grandeza + >=1 faixa + >=1 incerteza +
  valor convencional (NIT-DICLA-030 8.2.6). Lista vazia bloqueia.
- INV-PAD-005 — `vinculacao=RBC` exige tenant perfil A (ADR-0067). O caller
  calcula `tenant_e_perfil_a` via predicate `tenant_perfil_e(["A"])`
  (SAN-PERFIL Sprint 2 — fail-closed) e passa aqui; a verificacao no use case
  e defesa em profundidade (o predicate authz na view e a 1a barreira).
- ADR-0030 — `vigencia_inicio` tz-aware (INV-VIG-004).

NAO chama AuthorizationProvider aqui (caller=guard, use_case=transacao —
mesmo criterio de `criar_calibracao` M4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from src.domain.metrologia.padroes.entities import PadraoMetrologicoSnapshot
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    EstadoPadrao,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.padroes.repository import PadraoRepository
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)


class NumeroSerieDuplicadoError(Exception):
    """INV-PAD-001 — ja existe padrao com este (tenant, numero_serie)."""

    def __init__(self, numero_serie: str) -> None:
        self.numero_serie = numero_serie
        super().__init__(
            f"INV-PAD-001: numero_serie '{numero_serie}' ja cadastrado neste tenant."
        )


class PerfilNaoPermiteRBCError(Exception):
    """INV-PAD-005 — vinculacao=RBC exige tenant perfil A (ADR-0067)."""

    def __init__(self) -> None:
        super().__init__(
            "INV-PAD-005: padrao com vinculacao=RBC exige tenant perfil A "
            "acreditado CGCRE (ADR-0067)."
        )


@dataclass(frozen=True, slots=True)
class CadastrarPadraoInput:
    """Payload de cadastro de padrao metrologico."""

    tenant_id: UUID
    numero_serie: str
    fabricante: str
    modelo: str
    subtipo: SubtipoPadrao
    grandezas: tuple[Grandeza, ...]
    faixas: tuple[FaixaMedicao, ...]
    incertezas_certificado: tuple[IncertezaExpandida, ...]
    vinculacao: VinculacaoCadeia
    classe: ClassePadrao
    cert_externo_storage_key: str
    validade_certificado_rastreabilidade: date
    proximo_recal: date
    intervalo_recal_meses: int
    intervalo_vi_meses: int
    criterio_intervalo: str
    vigencia_inicio: datetime
    correlation_id: UUID
    tenant_e_perfil_a: bool
    descricao: str = ""
    localizacao_lab: str = ""

    def __post_init__(self) -> None:
        # INV-PAD-002 — listas nao-vazias (>=1 cada).
        if not self.grandezas:
            raise ValueError("INV-PAD-002: padrao exige >=1 grandeza.")
        if not self.faixas:
            raise ValueError("INV-PAD-002: padrao exige >=1 faixa de medicao.")
        if not self.incertezas_certificado:
            raise ValueError(
                "INV-PAD-002: padrao exige >=1 incerteza de certificado "
                "(valor convencional + incerteza — NIT-DICLA-030 8.2.6)."
            )
        if not self.criterio_intervalo.strip():
            raise ValueError(
                "C-9: criterio_intervalo obrigatorio (justificativa cl. 6.4.7)."
            )
        if self.intervalo_recal_meses <= 0 or self.intervalo_vi_meses <= 0:
            raise ValueError("Intervalos de recal/VI devem ser > 0 meses.")
        # INV-VIG-004 — vigencia tz-aware
        if self.vigencia_inicio.tzinfo is None:
            raise ValueError(
                "cadastrar_padrao: vigencia_inicio exige datetime tz-aware "
                "(INV-VIG-004 — UTC obrigatorio)."
            )


@dataclass(frozen=True, slots=True)
class CadastrarPadraoOutput:
    snapshot: PadraoMetrologicoSnapshot = field()


def executar(inp: CadastrarPadraoInput, repo: PadraoRepository) -> CadastrarPadraoOutput:
    """Cadastra o padrao em EM_USO apos validar INV-PAD-001/002/005."""
    # INV-PAD-005 — RBC exige perfil A (defesa em profundidade)
    if inp.vinculacao.exige_perfil_a and not inp.tenant_e_perfil_a:
        raise PerfilNaoPermiteRBCError

    # INV-PAD-001 — UNIQUE (tenant, numero_serie)
    if repo.existe_numero_serie(inp.tenant_id, inp.numero_serie):
        raise NumeroSerieDuplicadoError(inp.numero_serie)

    snapshot = PadraoMetrologicoSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        numero_serie=inp.numero_serie,
        fabricante=inp.fabricante,
        modelo=inp.modelo,
        subtipo=inp.subtipo,
        grandezas=inp.grandezas,
        faixas=inp.faixas,
        incertezas_certificado=inp.incertezas_certificado,
        vinculacao=inp.vinculacao,
        classe=inp.classe,
        cert_externo_storage_key=inp.cert_externo_storage_key,
        validade_certificado_rastreabilidade=inp.validade_certificado_rastreabilidade,
        proximo_recal=inp.proximo_recal,
        intervalo_recal_meses=inp.intervalo_recal_meses,
        intervalo_vi_meses=inp.intervalo_vi_meses,
        criterio_intervalo=inp.criterio_intervalo,
        estado=EstadoPadrao.EM_USO,
        revision=0,
        rastreabilidade_origem_revogada=False,
        vigencia_inicio=inp.vigencia_inicio,
        correlation_id=inp.correlation_id,
        descricao=inp.descricao,
        localizacao_lab=inp.localizacao_lab,
    )
    repo.salvar_novo(snapshot)
    return CadastrarPadraoOutput(snapshot=snapshot)
