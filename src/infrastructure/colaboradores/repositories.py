"""Adapters Django dos Protocols do módulo colaboradores (T-COL-028 — ADR-0007).

Concorrência (D-COL-4 / ADR-0065): `travar_dono_por_tenant` faz
`pg_advisory_xact_lock` (namespace 880_405 — distinto de 880_401 certificados M8,
880_402 numeração configuracoes, 880_403 catálogo PPS, 880_404 precificacao).
O use case chama o lock DENTRO de `transaction.atomic` ANTES de verificar DONO
ativo — serializa atribuições concorrentes para o mesmo tenant.
O índice parcial uq_col_papel_dono_unico (0001_initial) é a verdade no banco
contra qualquer caminho que burle o use case.

catalogo_habilidade: repositório read-only — sem advisory lock, sem transação.
Tabela global sem RLS (TL-COL-10); app_user tem SELECT apenas.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from django.db import connection

from src.domain.rh_frota_qualidade.colaboradores.entities import (
    CatalogoHabilidade,
    Colaborador,
    Documento,
    Habilidade,
    PapelColaboradorAtribuido,
)
from src.domain.rh_frota_qualidade.colaboradores.enums import PapelColaborador
from src.infrastructure.colaboradores import mappers
from src.infrastructure.colaboradores.models import (
    CatalogoHabilidade as CatalogoModel,
)
from src.infrastructure.colaboradores.models import (
    Colaborador as ColaboradorModel,
)
from src.infrastructure.colaboradores.models import (
    ColaboradorDocumento as DocumentoModel,
)
from src.infrastructure.colaboradores.models import (
    ColaboradorHabilidade as HabilidadeModel,
)
from src.infrastructure.colaboradores.models import (
    ColaboradorPapel as PapelModel,
)

# Namespace do advisory lock (serializa troca de DONO — ADR-0065 / D-COL-4).
# Distinto de todos os outros namespaces do projeto.
_ADVISORY_LOCK_COLABORADORES = 880_405


def _advisory_lock_dono(tenant_id: UUID) -> None:
    """Advisory lock para troca de DONO (serializa por tenant — ADR-0065)."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT pg_advisory_xact_lock(%s, hashtext(%s));",
            [_ADVISORY_LOCK_COLABORADORES, str(tenant_id)],
        )


# =============================================================
# DjangoColaboradorRepository
# =============================================================


class DjangoColaboradorRepository:
    """Agregado raiz Colaborador (D-COL-3 / ADR-0007)."""

    def obter(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        incluir_deletados: bool = False,
    ) -> Colaborador | None:
        """Retorna o colaborador; None se inexistente.

        Soft-deleted retorna apenas se `incluir_deletados=True`.
        """
        manager = ColaboradorModel.all_objects if incluir_deletados else ColaboradorModel.objects
        m = manager.filter(tenant_id=tenant_id, id=colaborador_id).first()
        return mappers.colaborador_model_para_entidade(m) if m is not None else None

    def obter_por_cpf(
        self,
        *,
        tenant_id: UUID,
        cpf_value: str,
    ) -> Colaborador | None:
        """Retorna colaborador ativo com o CPF; None se inexistente.

        Usa manager `objects` (filtra deletado_em IS NULL).
        """
        m = ColaboradorModel.objects.filter(tenant_id=tenant_id, cpf=cpf_value).first()
        return mappers.colaborador_model_para_entidade(m) if m is not None else None

    def listar_ativos(
        self,
        *,
        tenant_id: UUID,
        papel: PapelColaborador | None = None,
    ) -> list[Colaborador]:
        """Lista colaboradores ativos, opcionalmente filtrados por papel."""
        qs = ColaboradorModel.ativos.filter(tenant_id=tenant_id)
        if papel is not None:
            qs = qs.filter(
                papeis__papel=papel.value,
                papeis__data_fim__isnull=True,
                papeis__revogado_em__isnull=True,
            )
        return [mappers.colaborador_model_para_entidade(m) for m in qs.distinct()]

    def salvar(self, colaborador: Colaborador) -> None:
        """Insere ou atualiza o colaborador (upsert por id)."""
        ColaboradorModel.all_objects.update_or_create(
            id=colaborador.id,
            defaults={
                "tenant_id": colaborador.tenant_id,
                "nome": colaborador.nome,
                "cpf": colaborador.cpf.value,
                "email": colaborador.email,
                "telefone": colaborador.telefone,
                "vinculo": colaborador.vinculo.value,
                "data_admissao": colaborador.data_admissao,
                "comissao_default_pct": colaborador.comissao_default_pct,
                "observacao": colaborador.observacao,
                "usuario_id": colaborador.usuario_id,
                "foto_storage_key": colaborador.foto_storage_key,
                "data_desligamento": colaborador.data_desligamento,
                "motivo_desligamento": colaborador.motivo_desligamento,
                "deletado_em": colaborador.deletado_em,
                "deletado_por_usuario_id": colaborador.deletado_por_usuario_id,
                "deletado_motivo": colaborador.deletado_motivo,
            },
        )

    def desligar(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        data_desligamento: date,
        motivo_desligamento: str,
    ) -> None:
        """Registra desligamento: preenche data_desligamento + motivo."""
        ColaboradorModel.objects.filter(tenant_id=tenant_id, id=colaborador_id).update(
            data_desligamento=data_desligamento,
            motivo_desligamento=motivo_desligamento,
        )

    def soft_delete(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        deletado_em: datetime,
        deletado_por_usuario_id: UUID,
        deletado_motivo: str,
    ) -> None:
        """Soft-delete Padrão C (D-COL-3): preenche deletado_em + auditoria."""
        ColaboradorModel.objects.filter(tenant_id=tenant_id, id=colaborador_id).update(
            deletado_em=deletado_em,
            deletado_por_usuario_id=deletado_por_usuario_id,
            deletado_motivo=deletado_motivo,
        )


# =============================================================
# DjangoPapelRepository
# =============================================================


class DjangoPapelRepository:
    """Repositório de PapelColaboradorAtribuido (D-COL-4 / ADR-0007)."""

    def listar_por_colaborador(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> list[PapelColaboradorAtribuido]:
        """Retorna todos os papéis do colaborador (incluindo revogados — audit)."""
        qs = PapelModel.objects.filter(tenant_id=tenant_id, colaborador_id=colaborador_id).order_by(
            "criado_em"
        )
        return [mappers.papel_model_para_entidade(m) for m in qs]

    def existe_dono_ativo(self, *, tenant_id: UUID) -> bool:
        """True se já existe papel DONO ativo no tenant (INV-COL-DONO-UNICO)."""
        return PapelModel.objects.filter(
            tenant_id=tenant_id,
            papel=PapelColaborador.DONO.value,
            data_fim__isnull=True,
            revogado_em__isnull=True,
        ).exists()

    def salvar(self, papel: PapelColaboradorAtribuido) -> None:
        """Insere um novo papel atribuído."""
        PapelModel.objects.update_or_create(
            id=papel.id,
            defaults={
                "colaborador_id": papel.colaborador_id,
                "tenant_id": None,  # preenchido abaixo via tenant externo no use case
                "papel": papel.papel.value,
                "data_inicio": papel.data_inicio,
                "data_fim": papel.data_fim,
                "revogado_em": papel.revogado_em,
                "responsabilidade_tecnica_id": papel.responsabilidade_tecnica_id,
                "pendencia_cnh": papel.pendencia_cnh,
            },
        )

    def revogar(
        self,
        *,
        tenant_id: UUID,
        papel_id: UUID,
        revogado_em: datetime,
    ) -> None:
        """Revogação: seta revogado_em; nunca apaga a linha (audit)."""
        PapelModel.objects.filter(tenant_id=tenant_id, id=papel_id).update(revogado_em=revogado_em)

    def revogar_todos_ativos(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        revogado_em: datetime,
    ) -> int:
        """Revoga todos os papéis ativos do colaborador.

        Retorna a quantidade de papéis revogados.
        """
        updated = PapelModel.objects.filter(
            tenant_id=tenant_id,
            colaborador_id=colaborador_id,
            revogado_em__isnull=True,
        ).update(revogado_em=revogado_em)
        return updated

    def travar_dono_por_tenant(self, *, tenant_id: UUID) -> None:
        """Advisory lock para troca de DONO (namespace 880_405 — ADR-0065)."""
        _advisory_lock_dono(tenant_id)


# =============================================================
# DjangoHabilidadeRepository
# =============================================================


class DjangoHabilidadeRepository:
    """Repositório de Habilidade (D-COL-5 / ADR-0007)."""

    def listar_por_colaborador(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> list[Habilidade]:
        qs = HabilidadeModel.objects.filter(
            tenant_id=tenant_id, colaborador_id=colaborador_id
        ).order_by("criado_em")
        return [mappers.habilidade_model_para_entidade(m) for m in qs]

    def salvar(self, habilidade: Habilidade) -> None:
        HabilidadeModel.objects.update_or_create(
            id=habilidade.id,
            defaults={
                "colaborador_id": habilidade.colaborador_id,
                "nivel": habilidade.nivel.value,
                "data_avaliacao": habilidade.data_avaliacao,
                "descricao_livre": habilidade.descricao_livre,
                "evidencia_url": habilidade.evidencia_url,
            },
        )

    def remover(
        self,
        *,
        tenant_id: UUID,
        habilidade_id: UUID,
    ) -> None:
        HabilidadeModel.objects.filter(tenant_id=tenant_id, id=habilidade_id).delete()


# =============================================================
# DjangoDocumentoRepository
# =============================================================


class DjangoDocumentoRepository:
    """Repositório de Documento (D-COL-6 / ADR-0007)."""

    def listar_por_colaborador(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> list[Documento]:
        qs = DocumentoModel.objects.filter(
            tenant_id=tenant_id, colaborador_id=colaborador_id
        ).order_by("criado_em")
        return [mappers.documento_model_para_entidade(m) for m in qs]

    def salvar(self, documento: Documento) -> None:
        DocumentoModel.objects.update_or_create(
            id=documento.id,
            defaults={
                "colaborador_id": documento.colaborador_id,
                "tipo": documento.tipo.value,
                "storage_key": documento.storage_key,
                "sha256": documento.sha256,
                "data_upload": documento.data_upload,
                "data_validade": documento.data_validade,
            },
        )

    def remover(
        self,
        *,
        tenant_id: UUID,
        documento_id: UUID,
    ) -> None:
        DocumentoModel.objects.filter(tenant_id=tenant_id, id=documento_id).delete()


# =============================================================
# DjangoCatalogoHabilidadeRepository
# =============================================================


class DjangoCatalogoHabilidadeRepository:
    """Repositório de CatalogoHabilidade global read-only (D-COL-5 / TL-COL-10).

    Sem tenant_id — tabela global sem RLS. INSERT exclusivo via seed.
    """

    def listar(self) -> list[CatalogoHabilidade]:
        """Lista todas as habilidades do catálogo global."""
        return [
            mappers.catalogo_model_para_entidade(m)
            for m in CatalogoModel.objects.all().order_by("codigo")
        ]

    def obter_por_codigo(self, *, codigo: str) -> CatalogoHabilidade | None:
        """Busca por código; None se inexistente."""
        m = CatalogoModel.objects.filter(codigo=codigo).first()
        return mappers.catalogo_model_para_entidade(m) if m is not None else None
