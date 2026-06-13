"""Entidades do módulo `colaboradores` (T-COL-011 — frozen dataclasses).

5 entidades frozen refletindo o modelo de domínio (spec §4 / D-COL-1..14):
  Colaborador, PapelColaboradorAtribuido, Habilidade, Documento, CatalogoHabilidade.

Regras aplicadas aqui (domínio puro):
  - CPF imutável pós-criação (spec §4 / D-COL-2).
  - `ativo` derivado via property — não campo persistido.
  - Papel: campos soltos data_inicio/data_fim/revogado_em (NÃO reusar JanelaVigencia
    em row mutável — D-COL-4 / TL-COL-09).
  - Habilidade: catalogo_id XOR descricao_livre (D-COL-5).
  - Soft-delete Padrão C: deletado_em / deletado_por_usuario_id / deletado_motivo.

Zero `Any` / `object` de escape. Tipagem completa (lição M1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from src.domain.shared.value_objects import CPF

from .enums import NivelHabilidade, PapelColaborador, TipoDocumento, Vinculo


@dataclass(frozen=True)
class Colaborador:
    """Agregado raiz — identidade e estado de um colaborador do tenant (spec §4).

    `ativo` é derivado via property (não coluna) a partir de `data_desligamento`
    e `deletado_em` (D-COL-3 / `derivar_ativo` em `regras.py`).

    `usuario_id` é opcional (D-COL-2): colaboradores sem login (terceirizados/PJ)
    não têm `usuario_id`. Exceção: SIGNATARIO EXIGE `usuario_id` NOT NULL
    (INV-COL-SIGNATARIO-IDENTIDADE / D-COL-11).

    `comissao_default_pct` em escala 5,2 (CHECK 0..100 — D-COL-9).
    Alteração grava trilha auditável (INV-001 / D-COL-14).

    Soft-delete Padrão C (D-COL-3 / TL-COL-04):
      deletado_em             → marcador de deleção lógica (correção de cadastro).
      deletado_por_usuario_id → quem deletou (auditoria).
      deletado_motivo         → motivo da deleção (texto livre).

    Desligamento de negócio (D-COL-3):
      data_desligamento   → data efetiva de encerramento do vínculo.
      motivo_desligamento → motivo do desligamento (texto livre).
    """

    id: UUID
    tenant_id: UUID
    nome: str
    cpf: CPF
    email: str
    telefone: str
    vinculo: Vinculo
    data_admissao: date
    comissao_default_pct: Decimal
    observacao: str
    # Opcional: login associado (D-COL-2)
    usuario_id: UUID | None = None
    # Foto em storage (D-COL-6 / TL-COL-06)
    foto_storage_key: str | None = None
    # Desligamento de negócio (D-COL-3)
    data_desligamento: date | None = None
    motivo_desligamento: str | None = None
    # Soft-delete Padrão C (D-COL-3)
    deletado_em: datetime | None = None
    deletado_por_usuario_id: UUID | None = None
    deletado_motivo: str | None = None

    @property
    def ativo(self) -> bool:
        """True se o colaborador não foi desligado nem soft-deletado.

        Derivado: não persiste no banco; calculado a partir de `data_desligamento`
        e `deletado_em` (D-COL-3 / `derivar_ativo` em `regras.py`).
        """
        return self.data_desligamento is None and self.deletado_em is None


@dataclass(frozen=True)
class PapelColaboradorAtribuido:
    """Papel de negócio atribuído a um colaborador (D-COL-4 / spec §4).

    Entidade filha mutável com revogação auditada (TL-COL-09).
    Campos de vigência são SOLTOS (NÃO usa JanelaVigencia — D-COL-4):
      data_inicio → início da vigência do papel.
      data_fim    → fim programado (opcional).
      revogado_em → revogação administrativa (não apaga a linha — audit).

    SIGNATARIO: `responsabilidade_tecnica_id` referencia o RTCompetencia vigente
    que casa com `colaborador.usuario_id` (INV-COL-SIGNATARIO-IDENTIDADE).

    MOTORISTA_UMC: `pendencia_cnh=True` quando colaborador não tem CNH válida
    (R-COL-1 — salva com pendência, sem levantar erro; bloqueio real = alocação).

    DONO: único por tenant ativo (INV-COL-DONO-UNICO — partial unique WHERE
    papel='DONO' AND data_fim IS NULL AND revogado_em IS NULL).
    """

    id: UUID
    colaborador_id: UUID
    papel: PapelColaborador
    data_inicio: date
    data_fim: date | None = None
    revogado_em: datetime | None = None
    # Referência ao RTCompetencia (só quando papel=SIGNATARIO — D-COL-11)
    responsabilidade_tecnica_id: UUID | None = None
    # Pendência de CNH (só relevante para MOTORISTA_UMC — R-COL-1)
    pendencia_cnh: bool = False


@dataclass(frozen=True)
class Habilidade:
    """Habilidade registrada para um colaborador (D-COL-5 / spec §4).

    `catalogo_id` XOR `descricao_livre` — exatamente um deve ser não-None
    (CHECK na migration, validação em `regras.py`).

    `nivel` segue `NivelHabilidade` (APRENDIZ/CAPACITADO/MESTRE).
    `evidencia_url` aponta para documento comprobatório (opcional).
    `data_avaliacao` data em que o nível foi avaliado/registrado.
    """

    id: UUID
    colaborador_id: UUID
    nivel: NivelHabilidade
    data_avaliacao: date
    # Exatamente um dos dois deve ser não-None (D-COL-5)
    catalogo_id: UUID | None = None
    descricao_livre: str | None = None
    evidencia_url: str | None = None


@dataclass(frozen=True)
class Documento:
    """Documento anexado ao colaborador (D-COL-6 / spec §4).

    `tipo` enum sem ASO (R-COL-2 — dado de saúde, dono = SST).
    `storage_key` referencia o arquivo no storage (AnexoStoragePort — D-COL-6).
    `sha256` calculado server-side ao receber o arquivo (integridade).
    `data_validade` opcional: CNH tem validade; certificados podem ter.
    """

    id: UUID
    colaborador_id: UUID
    tipo: TipoDocumento
    storage_key: str
    sha256: str
    data_upload: datetime
    data_validade: date | None = None


@dataclass(frozen=True)
class CatalogoHabilidade:
    """Habilidade do catálogo global read-only (D-COL-5 / TL-COL-10).

    Entidade global — sem tenant_id (sem RLS por tenant).
    Seed literal na migration da frente (RunPython molde global authz/0003).
    Lista de grandezas literal no arquivo de seed — sem import de `metrologia`
    (quebra aresta runtime com calibracao — objetivo gap #4).

    Tenant não edita o catálogo; pode registrar habilidade livre
    (Habilidade.descricao_livre sem catalogo_id).

    `grandeza` opcional: identifica a grandeza metrológica associada
    (ex: "massa", "temperatura", "pressão") quando a habilidade é técnica.
    """

    codigo: str
    descricao: str
    grandeza: str | None = None
