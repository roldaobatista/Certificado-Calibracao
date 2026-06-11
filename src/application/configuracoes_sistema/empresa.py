"""Use cases `atualizar_empresa` + `adicionar_filial` + `editar_filial` —
US-CFG-001 (T-CFG-030 + conserto M6 da auditoria P9). PUROS.

Empresa é singleton por tenant (cadastro tributário): `atualizar_empresa` faz
upsert preservando o id existente. `adicionar_filial`/`editar_filial` validam
CNPJ próprio (AC-CFG-001-2) e o INV-037 (exatamente 1 matriz) no conjunto
RESULTANTE antes de persistir — a metade "≤1" também é garantida pelo UNIQUE
parcial no banco. `editar_filial` faz troca atômica de matriz: marcar
`eh_matriz=True` desmarca a anterior na MESMA transação (a view embrulha em
`transaction.atomic`; a ordem desmarcar→marcar respeita o UNIQUE parcial).

Eventos `Config.EmpresaAtualizada`/`Config.FilialAdicionada`/
`Config.FilialEditada` são publicados pela VIEW (payload antes/depois
sanitizado pelo helper — D-CFG-7).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID, uuid4

from src.domain.configuracoes_sistema.entities import Empresa, Filial
from src.domain.configuracoes_sistema.enums import RegimeTributario
from src.domain.configuracoes_sistema.repository import EmpresaRepository
from src.domain.configuracoes_sistema.transicoes import validar_uma_matriz
from src.domain.shared.value_objects import CNPJ


class EmpresaAusenteError(Exception):
    """Filial exige empresa cadastrada antes — 422."""

    reason = "EMPRESA_AUSENTE"


class FilialAusenteError(Exception):
    """Filial a editar não existe no tenant — 404."""

    reason = "FILIAL_AUSENTE"


@dataclass(frozen=True, slots=True)
class AtualizarEmpresaInput:
    tenant_id: UUID
    razao_social: str
    cnpj: str  # validado pelo VO (ADR-0017) — ValueError → 400
    regime_tributario: RegimeTributario
    inscricao_estadual: str = ""
    inscricao_municipal: str = ""
    endereco: str = ""
    logo_url: str = ""
    site: str = ""
    telefone: str = ""


@dataclass(frozen=True, slots=True)
class AtualizarEmpresaOutput:
    empresa: Empresa
    criada: bool
    antes: Empresa | None  # payload "antes" do evento (None na criação)


def atualizar_empresa(
    inp: AtualizarEmpresaInput, *, repo: EmpresaRepository
) -> AtualizarEmpresaOutput:
    """Upsert do cadastro tributário (AC-CFG-001-1)."""
    if not inp.razao_social.strip():
        raise ValueError("razao_social obrigatória.")
    cnpj = CNPJ(value=inp.cnpj)
    antes = repo.obter(tenant_id=inp.tenant_id)
    empresa = Empresa(
        id=antes.id if antes is not None else uuid4(),
        tenant_id=inp.tenant_id,
        razao_social=inp.razao_social.strip(),
        cnpj=cnpj,
        regime_tributario=inp.regime_tributario,
        inscricao_estadual=inp.inscricao_estadual,
        endereco=inp.endereco,
        inscricao_municipal=inp.inscricao_municipal,
        logo_url=inp.logo_url,
        site=inp.site,
        telefone=inp.telefone,
    )
    repo.salvar(empresa)
    return AtualizarEmpresaOutput(empresa=empresa, criada=antes is None, antes=antes)


@dataclass(frozen=True, slots=True)
class AdicionarFilialInput:
    tenant_id: UUID
    cnpj: str  # CNPJ PRÓPRIO da filial (AC-CFG-001-2)
    nome: str
    eh_matriz: bool
    endereco: str = ""
    inscricao_estadual: str = ""
    inscricao_municipal: str = ""
    telefone: str = ""


def adicionar_filial(inp: AdicionarFilialInput, *, repo: EmpresaRepository) -> Filial:
    """Adiciona filial validando INV-037 no conjunto RESULTANTE (exatamente 1
    matriz). `MatrizInvalidaError` → 422; banco reforça ≤1 via UNIQUE parcial."""
    if not inp.nome.strip():
        raise ValueError("nome da filial obrigatório.")
    empresa = repo.obter(tenant_id=inp.tenant_id)
    if empresa is None:
        raise EmpresaAusenteError("cadastre a empresa antes de adicionar filiais (US-CFG-001).")
    filial = Filial(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        empresa_id=empresa.id,
        cnpj=CNPJ(value=inp.cnpj),
        nome=inp.nome.strip(),
        eh_matriz=inp.eh_matriz,
        endereco=inp.endereco,
        inscricao_estadual=inp.inscricao_estadual,
        inscricao_municipal=inp.inscricao_municipal,
        telefone=inp.telefone,
    )
    existentes = repo.listar_filiais(tenant_id=inp.tenant_id, empresa_id=empresa.id)
    validar_uma_matriz([*existentes, filial])  # INV-037 — MatrizInvalidaError
    repo.salvar_filial(filial)
    return filial


@dataclass(frozen=True, slots=True)
class EditarFilialInput:
    tenant_id: UUID
    filial_id: UUID
    cnpj: str  # CNPJ PRÓPRIO da filial (AC-CFG-001-2)
    nome: str
    eh_matriz: bool
    endereco: str = ""
    inscricao_estadual: str = ""
    inscricao_municipal: str = ""
    telefone: str = ""


@dataclass(frozen=True, slots=True)
class EditarFilialOutput:
    filial: Filial
    antes: Filial  # payload "antes" do evento
    ex_matriz: Filial | None  # desmarcada na troca atômica (None se não houve)


def editar_filial(inp: EditarFilialInput, *, repo: EmpresaRepository) -> EditarFilialOutput:
    """Edita filial existente (conserto M6 — spec §3 "adicionar/EDITAR filial").

    INV-037 no conjunto RESULTANTE: marcar `eh_matriz=True` DESMARCA a matriz
    anterior na mesma transação (troca atômica — desmarca antes de marcar, por
    causa do UNIQUE parcial); desmarcar a ÚNICA matriz → `MatrizInvalidaError`
    (422 — o tenant trocaria a matriz, nunca ficaria sem).
    """
    if not inp.nome.strip():
        raise ValueError("nome da filial obrigatório.")
    empresa = repo.obter(tenant_id=inp.tenant_id)
    if empresa is None:
        raise EmpresaAusenteError("cadastre a empresa antes de editar filiais (US-CFG-001).")
    existentes = repo.listar_filiais(tenant_id=inp.tenant_id, empresa_id=empresa.id)
    antes = next((f for f in existentes if f.id == inp.filial_id), None)
    if antes is None:
        raise FilialAusenteError(f"filial {inp.filial_id} inexistente no tenant.")

    editada = Filial(
        id=antes.id,
        tenant_id=antes.tenant_id,
        empresa_id=antes.empresa_id,
        cnpj=CNPJ(value=inp.cnpj),
        nome=inp.nome.strip(),
        eh_matriz=inp.eh_matriz,
        endereco=inp.endereco,
        inscricao_estadual=inp.inscricao_estadual,
        inscricao_municipal=inp.inscricao_municipal,
        telefone=inp.telefone,
    )

    # Troca atômica: virou matriz → a anterior (se outra) é desmarcada junto.
    ex_matriz: Filial | None = None
    if editada.eh_matriz:
        anterior = next(
            (f for f in existentes if f.eh_matriz and f.id != editada.id), None
        )
        if anterior is not None:
            ex_matriz = replace(anterior, eh_matriz=False)

    resultante = [
        editada
        if f.id == editada.id
        else (ex_matriz if ex_matriz is not None and f.id == ex_matriz.id else f)
        for f in existentes
    ]
    validar_uma_matriz(resultante)  # INV-037 — MatrizInvalidaError (422)

    # Ordem: desmarcar a ex-matriz ANTES de salvar a nova (UNIQUE parcial
    # uq_cfg_filial_uma_matriz não é deferrable).
    if ex_matriz is not None:
        repo.salvar_filial(ex_matriz)
    repo.salvar_filial(editada)
    return EditarFilialOutput(filial=editada, antes=antes, ex_matriz=ex_matriz)
