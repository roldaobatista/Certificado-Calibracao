"""Snapshots imutáveis do domínio procedimentos-calibracao (M7 — T-PROC-011).

Frozen dataclasses que atravessam a fronteira use case <-> repository. Adapter
Django converte Model PG <-> Snapshot (ADR-0007). VOs reusados de
src/domain/metrologia/value_objects.py + geometria de src/domain/metrologia/
faixa_cobertura.py (NÃO recriar — T-PROC-012).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from src.domain.metrologia.faixa_cobertura import faixa_contida
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

from .enums import EstadoProcedimento, TipoMetodo


@dataclass(frozen=True, slots=True)
class ProcedimentoSnapshot:
    """Versão de um procedimento técnico documentado controlado (cl. 7.2.1).

    Uma linha = um (codigo, versao). `codigo` é a identidade do documento
    controlado (cl. 8.3); cobre UMA grandeza + faixa contígua (D-PROC-2).
    Soft-delete Padrão B WORM (ADR-0031); vigência canônica (ADR-0030); CAS via
    `revision`. Só `estado=PUBLICADO` + vigente entra na resolução `vigente_em`.
    """

    id: UUID
    tenant_id: UUID
    codigo: str
    titulo: str
    grandeza: Grandeza
    faixa: FaixaMedicao
    metodo_norma: str
    tipo_metodo: TipoMetodo
    numero_revisao: str  # "Rev. 03" — cl. 8.3.2c (distinto de versao)
    anexo_pdf_storage_key: str
    anexo_pdf_sha256: str  # sha256 server-side do binário (NÃO HMAC)
    versao: int
    vigente_a_partir: datetime
    estado: EstadoProcedimento
    revision: int
    vigencia_inicio: datetime
    correlation_id: UUID
    registro_validacao_id: UUID | None = None  # evidência cl. 7.2.2 (NULL=lazy)
    aprovado_em: datetime | None = None  # ato de aprovação ≠ vigência (cl. 8.3.1)
    aprovado_por_id: UUID | None = None
    aprovado_por_nome_snapshot: str = ""
    vigencia_fim: datetime | None = None
    revogado_em: datetime | None = None
    motivo_revogacao: str = ""  # >=10 chars quando revogado (ADR-0030)

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
        """Entra na resolução em `em`: PUBLICADO + vigente (fail-closed)."""
        return self.estado.consultavel_para_resolucao and self.vigente_em(em)

    def cobre_faixa(self, solicitada: FaixaMedicao) -> bool:
        """A faixa solicitada está CONTIDA na faixa do procedimento (geometria
        compartilhada — INV-PROC-001). Erro de domínio distinto do escopo."""
        return faixa_contida(solicitada=solicitada, escopo=self.faixa)


@dataclass(frozen=True, slots=True)
class ProcedimentoUsado:
    """VO probatório congelado na configuração de uma calibração (INV-PROC-005 /
    AC-CAL-016-3). Autossuficiente para sustentar auditoria CGCRE anos depois —
    NÃO depende de joins que podem ter mudado. Alimenta o campo já existente
    `Calibracao.procedimento_versao_snapshot` (M4 P4).
    """

    procedimento_id: UUID
    codigo: str
    versao: int
    numero_revisao: str
    titulo: str
    grandeza: Grandeza
    faixa_procedimento: FaixaMedicao
    faixa_solicitada: FaixaMedicao
    metodo_norma: str
    tipo_metodo: TipoMetodo
    anexo_pdf_sha256: str
    perfil_no_evento: str  # CHAR(1) — perfil do tenant na época (ADR-0067)
    data_referencia: date  # data da calibração usada na resolução de vigência
    vigencia_inicio: datetime
    contido: bool  # resultado da contenção de faixa na época
    aprovado_em: datetime | None = None
    aprovado_por_id_hash: str = ""  # quem aprovou (HMAC server-side — sem PII crua)
    vigencia_fim: datetime | None = None

    def snapshot_minimo(self) -> dict[str, str]:
        """Campos que o `procedimento_versao_snapshot` (M4) congela na configuração
        (INV-PROC-005): `{codigo, versao, numero_revisao, hash_anexo}`. `numero_revisao`
        (cl. 8.3.2c) é o marcador de revisão do documento controlado, distinto de
        `versao` interna — entra no snapshot pra reconstituição CGCRE sem joins."""
        return {
            "codigo": self.codigo,
            "versao": str(self.versao),
            "numero_revisao": self.numero_revisao,
            "hash_anexo": self.anexo_pdf_sha256,
        }
