"""Repository protocol pra Clientes — camada DOMINIO puro (ADR-0007).

NAO importar django.* nem psycopg. Aqui mora apenas o CONTRATO; a
implementacao concreta (adapter Django) vive em
`src/infrastructure/clientes/repositories.py`.

Use cases (`src/application/comercial/clientes/`) consomem este Protocol e
nunca conhecem Django.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True)
class ClienteSnapshot:
    """Snapshot de Cliente — DTO imutavel pra atravessar fronteiras de camada.

    Reflete o que o domain precisa saber. Adapter Django converte Model <-> Snapshot.
    """

    id: UUID
    tenant_id: UUID
    tipo_pessoa: str  # "PF" | "PJ"
    documento: str
    nome: str
    nome_fantasia: str
    email: str
    telefone: str
    aceite_lgpd_em: datetime | None
    aceite_lgpd_versao: str
    aceite_lgpd_ip_hash: str
    aceite_lgpd_origem: str
    aceite_lgpd_dispensa_motivo: str
    deletado_em: datetime | None


@runtime_checkable
class ClienteRepository(Protocol):
    """Contrato de persistencia do agregado Cliente.

    Use cases recebem isso via DI. Adapter Django (`DjangoClienteRepository`)
    implementa. Em Wave C+ pode haver adapter pra outro storage.
    """

    def get_by_id(
        self, cliente_id: UUID, *, incluir_deletados: bool = False
    ) -> ClienteSnapshot | None:
        """Busca por id. Soft-deleted retorna apenas se `incluir_deletados=True`."""
        ...

    def aplicar_sobrescritas(
        self, cliente_id: UUID, sobrescritas: dict[str, Any]
    ) -> ClienteSnapshot:
        """Aplica dict de campos no vencedor + retorna snapshot pos-update."""
        ...

    def soft_delete(
        self,
        cliente_id: UUID,
        *,
        motivo_categoria: str,
        usuario_id: UUID | None,
        agora: datetime,
    ) -> ClienteSnapshot:
        """Marca cliente como soft-deleted; retorna snapshot pos-delete."""
        ...

    def bulk_upsert(
        self,
        *,
        tenant_id: UUID,
        linhas: list[ClienteImportacaoInput],
        update_existing: bool,
        agora: datetime,
    ) -> ResultadoImportacao:
        """Insere/atualiza em lote (US-CLI-003 R3/R8 tech-lead).

        Implementacao concreta deve:
        - Setar TRANSACTION ISOLATION LEVEL SERIALIZABLE.
        - Usar `pg_advisory_xact_lock` por tenant pra serializar importacoes
          simultaneas do mesmo tenant.
        - Aplicar UNIQUE INDEX parcial (tenant, tipo_pessoa, documento) WHERE
          deletado_em IS NULL pra dedup com clientes ativos.
        - Detectar documento que pertence a cliente soft-deleted (mesclado) e
          relatar como `LinhaRejeitada(motivo='documento_pertence_a_cliente_mesclado')`.
        - Sanitizar contra CSV injection na escrita (csv_safety.sanitizar_celula_csv).
        """
        ...


# =============================================================
# DTOs de importacao (US-CLI-003)
# =============================================================


@dataclass(frozen=True)
class ClienteImportacaoInput:
    """Linha pre-processada que vai pra `bulk_upsert`.

    Imutavel; gerada pelo use case `importar_clientes` apos validar +
    classificar PJ/PF/dispensa.
    """

    linha_numero: int
    linha_hash: str  # HMAC(linha original, chave servidor) — referencia sem PII
    tipo_pessoa: str  # "PF" | "PJ"
    documento: str
    nome: str
    nome_fantasia: str
    email: str
    telefone: str
    aceite_lgpd_em: datetime | None
    aceite_lgpd_versao: str
    aceite_lgpd_origem: str
    aceite_lgpd_dispensa_motivo: str
    aceite_lgpd_base_legal: str
    aceite_lgpd_evidencia_externa: str
    aceite_lgpd_pendente: bool
    cpf_responsavel_legal: str
    aceite_lgpd_ip_hash: str = ""


@dataclass(frozen=True)
class LinhaRejeitada:
    """Linha que nao passou no pre-processamento ou bate em integridade."""

    linha_numero: int
    linha_hash: str
    motivo: str
    motivo_descricao_curta: str = ""


@dataclass(frozen=True)
class ResultadoImportacao:
    """Resultado da `bulk_upsert`. Use case empacota relatorio final + audit."""

    criados: int
    atualizados: int
    sem_mudanca: int
    rejeitados: tuple[LinhaRejeitada, ...] = field(default_factory=tuple)
    ids_criados: tuple[UUID, ...] = field(default_factory=tuple)
    ids_atualizados: tuple[UUID, ...] = field(default_factory=tuple)

