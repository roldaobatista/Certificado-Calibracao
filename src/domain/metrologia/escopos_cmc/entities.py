"""Snapshots imutáveis do domínio escopos-cmc (M6 T-ECMC-002).

Frozen dataclasses que atravessam a fronteira use case <-> repository. Adapter
Django converte Model PG <-> Snapshot (ADR-0007 — use case nunca conhece Django).
VOs reusados de src/domain/metrologia/value_objects.py (NÃO recriar — T-ECMC-003).

Migra o `EscopoCMCSnapshot` que vivia em
src/application/metrologia/calibracao/queries/escopo.py (dataclass de leitura M4
sem persistência) — agora canônico aqui, enriquecido com forma da CMC (ADR-0074),
versionamento (AC-CAL-015-2), estado de extração (decisão N) e VO probatório
`EscopoUsado` (RBC-NC-06).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

from .enums import EstadoEscopo, FormaCMC, OrigemEscopo


@dataclass(frozen=True, slots=True)
class EscopoCMCSnapshot:
    """Linha do escopo de acreditação CGCRE (perfil A) ou capacidade interna
    (perfis B/C/D — `rbc_acreditado=False`, ADR-0075).

    Uma linha = um par (grandeza, faixa) por método/procedimento e versão
    (T-ECMC-007 — granularidade 1 método/linha). Soft-delete Padrão B WORM
    (ADR-0031); vigência canônica (ADR-0030); CAS via `revision`. Só
    `estado=CONFIRMADO` + vigente entra na cobertura (ADR-0073).
    """

    id: UUID
    tenant_id: UUID
    grandeza: Grandeza
    faixa: FaixaMedicao
    cmc_forma: FormaCMC
    cmc_valor: Decimal  # ABSOLUTA: a própria CMC; RELATIVA_LINEAR: termo fixo `a`
    cmc_unidade: str
    rbc_acreditado: bool  # True só perfil A (INV-ECMC-002); forçado False p/ B/C/D
    versao: int
    vigente_a_partir: datetime
    estado: EstadoEscopo
    revision: int
    vigencia_inicio: datetime
    correlation_id: UUID
    cmc_coef_relativo: Decimal | None = None  # `b` (só RELATIVA_LINEAR)
    numero_escopo_cgcre: str = ""  # decisão K — "Nº do escopo CGCRE"
    procedimento_id: UUID | None = None  # FK método (NOT NULL p/ RBC — T-ECMC-007)
    documento_regulatorio_id: UUID | None = None  # FK Licenças (INV-012, NULLABLE)
    origem: OrigemEscopo = OrigemEscopo.MANUAL
    vigencia_fim: datetime | None = None
    revogado_em: datetime | None = None
    motivo_revogacao: str = ""  # >=10 chars quando revogado (ADR-0030)

    def cmc_em(self, ponto: Decimal) -> Decimal:
        """CMC no ponto de medição (ADR-0074 — trata forma ABSOLUTA vs `a+b·X`).

        ABSOLUTA: constante. RELATIVA_LINEAR: `a + b·|X|` (|X| pois o mensurando
        pode ser negativo, ex. temperatura). Resultado na `cmc_unidade`.
        """
        if not isinstance(ponto, Decimal):
            raise ValueError("cmc_em() exige Decimal (sem float — erro metrológico)")
        if self.cmc_forma is FormaCMC.ABSOLUTA:
            return self.cmc_valor
        if self.cmc_coef_relativo is None:
            raise ValueError(
                "CMC RELATIVA_LINEAR exige cmc_coef_relativo (coeficiente `b`)"
            )
        return self.cmc_valor + self.cmc_coef_relativo * abs(ponto)

    def vigente_em(self, em: datetime) -> bool:
        """Vigência temporal canônica (ADR-0030). Revogado a partir de
        `revogado_em` deixa de valer; respeita janela `vigencia_inicio/fim`."""
        if self.revogado_em is not None and em >= self.revogado_em:
            return False
        if em < self.vigencia_inicio:
            return False
        if self.vigencia_fim is not None and em > self.vigencia_fim:
            return False
        return True

    def consultavel(self, em: datetime) -> bool:
        """Entra na cobertura em `em`: CONFIRMADO + vigente (fail-closed)."""
        return self.estado.consultavel_para_cobertura and self.vigente_em(em)


@dataclass(frozen=True, slots=True)
class EscopoUsado:
    """VO probatório congelado na configuração/emissão de uma calibração
    (INV-ECMC-008 / ADR-0014 / RBC-NC-06). Autossuficiente para sustentar
    auditoria CGCRE anos depois — NÃO depende de joins que podem ter mudado.

    Alimenta a coluna `escopos_acreditados_vigentes_no_momento` JSONB de
    `evento_de_calibracao` (já criada SAN-PERFIL Sprint 4).
    """

    escopo_id: UUID
    versao: int
    numero_escopo_cgcre: str
    grandeza: Grandeza
    faixa_escopo: FaixaMedicao
    faixa_solicitada: FaixaMedicao
    cmc_forma: FormaCMC
    cmc_valor: Decimal
    cmc_unidade: str
    rbc_acreditado: bool
    perfil_no_evento: str  # CHAR(1) — perfil do tenant na época (ADR-0067)
    data_referencia: date  # data da calibração usada na resolução de vigência
    vigencia_inicio: datetime
    contido: bool  # resultado da contenção de faixa na época
    cmc_coef_relativo: Decimal | None = None
    procedimento_id: UUID | None = None
    documento_regulatorio_id: UUID | None = None
    vigencia_fim: datetime | None = None
    rt_competente_id_hash: str = ""  # RT/signatário que lastreava na época
    # Preenchidos só na EMISSÃO (U existe; ADR-0074 condição 2):
    u_reportada: Decimal | None = None
    cmc_no_ponto: Decimal | None = None
    u_atende_cmc: bool | None = None


@dataclass(frozen=True, slots=True)
class LinhaEscopoExtraida:
    """Linha candidata extraída do PDF da CGCRE (decisão N — Fatia 4).

    Texto CRU (pode não bater no enum/whitelist) — a conferência humana
    normaliza antes de virar EscopoCMC CONFIRMADO. `confianca` 0..1 sinaliza
    células de baixa certeza para a tela de conferência destacar.
    """

    grandeza_texto: str
    unidade: str
    cmc_texto: str  # texto cru (pode vir "a + b·X")
    faixa_min: Decimal | None = None
    faixa_max: Decimal | None = None
    metodo_texto: str = ""
    confianca: Decimal = Decimal("1")


@dataclass(frozen=True, slots=True)
class EscopoExtraido:
    """Staging da extração de PDF (decisão N / TL-C-08). Tabela separada,
    mutável, NÃO WORM — nunca persiste vigente sem confirmação (INV-ECMC-007).
    Ao confirmar, cada linha aprovada vira uma linha CONFIRMADA em `escopo_cmc`.
    """

    id: UUID
    tenant_id: UUID
    origem_pdf_storage_key: str
    numero_escopo_cgcre: str
    extraido_em: datetime
    linhas: tuple[LinhaEscopoExtraida, ...] = field(default_factory=tuple)
    confirmado_em: datetime | None = None
    confirmado_por_id_hash: str = ""
