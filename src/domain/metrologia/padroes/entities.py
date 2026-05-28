# ruff: noqa: RUF001, RUF002, RUF003 — simbolo grego canonico (σ) na notacao estatistica
"""Snapshots imutaveis do dominio padroes (M5 T-PAD-002).

Frozen dataclasses que atravessam a fronteira use case <-> repository. Adapter
Django converte Model PG <-> Snapshot (ADR-0007 — use case nunca conhece Django).
VOs reusados de src/domain/metrologia/value_objects.py (NAO recriar — T-PAD-003).

Convencoes de PII (INV-CAL-AUD-001 pattern + revisao advogado C-13): user_id de
funcionario viaja como `*_id_hash` (HMAC-tenant ADR-0064) nos snapshots que
alimentam eventos WORM; textos livres canonicalizados + hash (ADR-0029).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)

from .enums import (
    ClassePadrao,
    DecisaoRTCarta,
    EstadoPadrao,
    RegraWesternElectric,
    ResultadoPT,
    ResultadoVI,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)


@dataclass(frozen=True, slots=True)
class PadraoMetrologicoSnapshot:
    """Agregado raiz — padrao metrologico do laboratorio do tenant (ADR-0040).

    Soft-delete padrao B WORM (ADR-0031); vigencia canonica (ADR-0030); CAS via
    `revision` (plan D-PAD-1). `rastreabilidade_origem_revogada` (C-5 FURO-4)
    bloqueia uso independente do estado. `incertezas_certificado` so muta via
    fluxo de recal (INV-PAD-006). Intervalos configuraveis + `criterio_intervalo`
    justificado (C-9 — NAO cravar 'intervalo R111').
    """

    id: UUID
    tenant_id: UUID
    numero_serie: str  # UNIQUE por tenant (INV-PAD-001) — imutavel pos 1o uso
    fabricante: str
    modelo: str
    subtipo: SubtipoPadrao
    grandezas: tuple[Grandeza, ...]  # >=1
    faixas: tuple[FaixaMedicao, ...]  # >=1
    incertezas_certificado: tuple[IncertezaExpandida, ...]  # >=1 (so via recal)
    vinculacao: VinculacaoCadeia
    classe: ClassePadrao
    cert_externo_storage_key: str  # chave opaca (binario cifrado KMS tenant — C-14)
    validade_certificado_rastreabilidade: date
    proximo_recal: date
    intervalo_recal_meses: int  # configuravel (C-9)
    intervalo_vi_meses: int  # configuravel (C-9)
    criterio_intervalo: str  # justificativa cl. 6.4.7 (C-9)
    estado: EstadoPadrao
    revision: int
    rastreabilidade_origem_revogada: bool  # C-5 FURO-4
    vigencia_inicio: datetime
    correlation_id: UUID
    descricao: str = ""  # <=500 chars anti-PII
    localizacao_lab: str = ""  # <=200 chars anti-PII (nao logar em claro)
    revogado_em: datetime | None = None
    motivo_revogacao: str = ""  # >=10 chars quando revogado (ADR-0030)


@dataclass(frozen=True, slots=True)
class RecalExternoPadraoSnapshot:
    """Recal externo (envio -> retorno -> aprovacao RT). Imutavel pos retorno.

    Estado `RECAL_RETORNADO_PENDENTE_APROVACAO` do padrao (C-4 FURO-1): apos
    `retornado_em`, so a aprovacao do RT (`aprovado_rt_em`) libera EM_USO.
    """

    id: UUID
    tenant_id: UUID
    padrao_id: UUID
    enviado_em: datetime
    lab_externo: str  # nome do lab (sem PII direta)
    responsavel_envio_id_hash: str  # HashVersionado (ADR-0064) — funcionario
    status: StatusRecal
    numero_protocolo_lab_externo: str = ""
    retornado_em: datetime | None = None
    cert_externo_novo_storage_key: str = ""
    incertezas_novas: tuple[IncertezaExpandida, ...] = ()
    validade_nova: date | None = None
    valor_convencional_novo: Decimal | None = None
    aprovado_rt_em: datetime | None = None  # C-4
    aprovado_rt_id_hash: str = ""  # C-4 — RT que aprovou a analise critica


@dataclass(frozen=True, slots=True)
class VerificacaoIntermediariaSnapshot:
    """VI periodica (cl. 6.4.10 — INV-022). WORM."""

    id: UUID
    tenant_id: UUID
    padrao_id: UUID
    data_vi: datetime
    executor_id_hash: str  # HashVersionado (ADR-0064)
    metodo_canonicalizado: str  # <=500 chars anti-PII (ADR-0029)
    metodo_hash: str
    resultado: ResultadoVI
    criado_em: datetime
    desvio_observado: Decimal | None = None
    acao_corretiva_canonicalizada: str = ""  # >=30 chars se REPROVADO
    acao_corretiva_hash: str = ""


@dataclass(frozen=True, slots=True)
class IntercomparacaoPTSnapshot:
    """Intercomparacao / PT (cl. 6.6 — INV-023, perfil A). WORM."""

    id: UUID
    tenant_id: UUID
    padrao_id: UUID
    lab_organizador: str
    protocolo: str
    data_inicio: datetime
    resultado: ResultadoPT | None = None
    data_resultado: datetime | None = None
    zeta_score: Decimal | None = None
    relatorio_pt_storage_key: str = ""
    nao_conformidade_id: UUID | None = None  # ref modulo nao-conformidades (Wave B+)


@dataclass(frozen=True, slots=True)
class AnaliseCartaControleSnapshot:
    """Registro WORM congelado da decisao derivada da carta Shewhart (ADR-0070).

    Snapshot dos LIMITES vigentes no instante da decisao (LC/UCL/LCL/σ) +
    `versao_motor_shewhart` (cl. 7.11) + decisao do RT — para reconstruir a
    decisao metrologica em auditoria CGCRE (cl. 8.4). NAO copia os pontos
    (vivem WORM nas VIs/recals — `pontos_referenciados_ids` aponta pra elas).
    INV-PAD-010.
    """

    id: UUID
    tenant_id: UUID
    padrao_id: UUID
    regra_violada: RegraWesternElectric
    pontos_referenciados_ids: tuple[UUID, ...]  # FKs VIs/recals (sem copiar valor)
    linha_central: Decimal
    ucl: Decimal
    lcl: Decimal
    sigma: Decimal
    n_pontos: int
    janela_meses: int
    versao_motor_shewhart: str
    decisao_rt: DecisaoRTCarta
    justificativa_canonicalizada: str  # ADR-0029
    justificativa_hash: str
    criado_em: datetime
    assinatura_a3_rt_id: UUID | None = None  # NULL ate A3 plugar (Wave A)


@dataclass(frozen=True, slots=True)
class VinculoAuxiliarSnapshot:
    """Vinculo temporal N:N padrao principal <-> auxiliar (cl. 6.4.5 — C-8).

    Carrega a grandeza de influencia que o auxiliar monitora (temp/umidade/
    pressao) — usada pra snapshotar a leitura ambiental no momento do uso do
    principal (PadraoUsadoSnapshot). Temporal (ADR-0030).
    """

    id: UUID
    tenant_id: UUID
    padrao_principal_id: UUID
    padrao_auxiliar_id: UUID
    grandeza_influencia: Grandeza
    vigencia_inicio: datetime
    revogado_em: datetime | None = None


@dataclass(frozen=True, slots=True)
class PadraoUsadoSnapshot:
    """VO imutavel do padrao no momento da selecao numa calibracao
    (INV-CAL-SNAP-001). Consumido pelo Marco 4 via porta (plan D-PAD-5).

    Inclui leitura ambiental dos auxiliares vinculados (C-8) pra compor o
    balanco de incerteza do certificado. A adequacao faixa/grandeza<->ponto eh
    decidida no M4 (C-15 — delegacao explicita); aqui expomos os dados.
    """

    padrao_id: UUID
    numero_serie: str
    fabricante: str
    modelo: str
    classe: ClassePadrao
    vinculacao: VinculacaoCadeia
    grandezas: tuple[Grandeza, ...]
    faixas: tuple[FaixaMedicao, ...]
    incertezas_certificado: tuple[IncertezaExpandida, ...]
    validade_certificado_rastreabilidade: date
    leituras_ambientais_auxiliares: tuple[tuple[Grandeza, Decimal], ...] = field(
        default_factory=tuple
    )
