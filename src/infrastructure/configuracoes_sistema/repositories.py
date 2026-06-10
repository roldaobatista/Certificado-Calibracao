"""Adapters Django dos Protocols de `configuracoes-sistema` (T-CFG-026 — ADR-0007).

A reserva de número REUSA o motor gap-less do M8 (`proximo_sequencial` + TTL +
advisory lock — TL-02/ADR-0080), sobre a tabela própria
`numero_documento_reservado` (dimensão por série, não por tipo de certificado).
Concorrência:
- GAP_LESS (fatura/certificado): `pg_advisory_xact_lock` por (tenant, serie, ano)
  + trigger de consecutividade (0003) + reserva-TTL 5min. Fluxo reserva →
  confirma (one-shot, na transação do emissor) → expira/libera.
- BURACOS_ACEITOS (os/orcamento/recibo/interno): UPDATE atômico de
  `serie_documento.proximo_numero` (estilo ADR-0056), com reset anual TL-07
  resolvido no MESMO statement (row lock do UPDATE serializa).

NÃO são singletons.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from django.db import connection, transaction
from django.utils import timezone

from src.domain.configuracoes_sistema.entities import (
    Empresa,
    Filial,
    Imposto,
    SerieDocumento,
)
from src.domain.configuracoes_sistema.enums import RegimeNumeracao, TipoImposto
from src.domain.metrologia.certificados.numeracao import TTL_RESERVA, proximo_sequencial
from src.infrastructure.configuracoes_sistema import mappers
from src.infrastructure.configuracoes_sistema.models import (
    Empresa as EmpresaModel,
)
from src.infrastructure.configuracoes_sistema.models import (
    Filial as FilialModel,
)
from src.infrastructure.configuracoes_sistema.models import (
    Imposto as ImpostoModel,
)
from src.infrastructure.configuracoes_sistema.models import (
    NumeroDocumentoReservado,
)
from src.infrastructure.configuracoes_sistema.models import (
    SerieDocumento as SerieDocumentoModel,
)

# Namespace do advisory lock da numeração de documentos (distinto do 880_401 dos
# certificados M8 e dos namespaces de audit/hash-chain). Serializa por
# (tenant, serie, ano).
_ADVISORY_LOCK_NUMERACAO_DOC = 880_402

# Série sem reset anual não tem dimensão de ano — sentinela 0 (ver models).
_SEM_DIMENSAO_ANO = 0


class DjangoEmpresaRepository:
    """Agregado Empresa/Filial (config mutável com auditoria — não-WORM)."""

    def obter(self, *, tenant_id: UUID) -> Empresa | None:
        m = EmpresaModel.objects.filter(tenant_id=tenant_id).first()
        return mappers.empresa_model_para_entidade(m) if m is not None else None

    def salvar(self, empresa: Empresa) -> None:
        EmpresaModel.objects.update_or_create(
            id=empresa.id,
            tenant_id=empresa.tenant_id,
            defaults=mappers.empresa_para_campos(empresa),
        )

    def listar_filiais(self, *, tenant_id: UUID, empresa_id: UUID) -> list[Filial]:
        qs = FilialModel.objects.filter(tenant_id=tenant_id, empresa_id=empresa_id).order_by(
            "criado_em"
        )
        return [mappers.filial_model_para_entidade(m) for m in qs]

    def salvar_filial(self, filial: Filial) -> None:
        FilialModel.objects.update_or_create(
            id=filial.id,
            tenant_id=filial.tenant_id,
            defaults=mappers.filial_para_campos(filial),
        )


class DjangoImpostoRepository:
    """Catálogo tributário versionado (linha imutável — triggers 0003/0004)."""

    def listar(
        self,
        *,
        tenant_id: UUID,
        tipo: TipoImposto | None = None,
        filial_id: UUID | None = None,
    ) -> list[Imposto]:
        qs = ImpostoModel.objects.filter(tenant_id=tenant_id)
        if tipo is not None:
            qs = qs.filter(tipo=tipo.value)
        if filial_id is not None:
            qs = qs.filter(filial_id=filial_id)
        return [
            mappers.imposto_model_para_entidade(m) for m in qs.order_by("tipo", "vigencia_inicio")
        ]

    def salvar_nova_linha(self, imposto: Imposto) -> None:
        """INSERT puro — linha de imposto NUNCA é atualizada (INV-CFG-IMPOSTO-
        IMUTAVEL); sobreposição de vigência estoura na exclusion constraint."""
        ImpostoModel.objects.create(
            id=imposto.id,
            tenant_id=imposto.tenant_id,
            **mappers.imposto_para_campos(imposto),
        )

    def encerrar_vigencia(self, *, tenant_id: UUID, imposto_id: UUID, fim: object) -> None:
        """One-shot NULL→data (D-CFG-3). Só encerra vigência ABERTA e não-revogada;
        rowcount 0 = já encerrada/revogada/inexistente (caller decide o erro)."""
        if not isinstance(fim, datetime):
            raise TypeError(f"fim deve ser datetime, veio {type(fim)!r}")
        atualizadas = ImpostoModel.objects.filter(
            tenant_id=tenant_id,
            id=imposto_id,
            vigencia_fim__isnull=True,
            revogado_em__isnull=True,
        ).update(vigencia_fim=fim)
        if atualizadas != 1:
            raise RuntimeError(
                f"encerrar_vigencia: esperava 1 linha aberta, afetou {atualizadas} "
                f"(imposto {imposto_id})."
            )


class DjangoSerieDocumentoRepository:
    """Séries de numeração local — 2 regimes por tipo (ADR-0080)."""

    def obter(
        self, *, tenant_id: UUID, tipo: object, prefixo: str, filial_id: UUID | None
    ) -> SerieDocumento | None:
        qs = SerieDocumentoModel.objects.filter(
            tenant_id=tenant_id,
            tipo=getattr(tipo, "value", tipo),
            prefixo=prefixo,
        )
        qs = qs.filter(filial__isnull=True) if filial_id is None else qs.filter(filial_id=filial_id)
        m = qs.first()
        return mappers.serie_model_para_entidade(m) if m is not None else None

    def obter_por_id(self, *, tenant_id: UUID, serie_id: UUID) -> SerieDocumento | None:
        m = SerieDocumentoModel.objects.filter(tenant_id=tenant_id, id=serie_id).first()
        return mappers.serie_model_para_entidade(m) if m is not None else None

    def salvar(self, serie: SerieDocumento) -> None:
        SerieDocumentoModel.objects.update_or_create(
            id=serie.id,
            tenant_id=serie.tenant_id,
            defaults=mappers.serie_para_campos(serie),
        )

    # === reserva de número (INV-CFG-NUM-ATOMICA / INV-028) ===

    def reservar_numero(self, *, tenant_id: UUID, serie_id: UUID, ano: int | None = None) -> int:
        """Reserva e retorna o próximo número atômico, conforme o regime da série.

        GAP_LESS: reserva-TTL no `numero_documento_reservado` (densa; precisa de
        `confirmar_numero` na transação do emissor — reserva não-confirmada
        expira e devolve o número). BURACOS_ACEITOS: UPDATE atômico já consome o
        número (buraco por rollback aceito — D-CFG-10).
        """
        serie = SerieDocumentoModel.objects.filter(tenant_id=tenant_id, id=serie_id).first()
        if serie is None:
            raise LookupError(f"serie {serie_id} inexistente para o tenant.")
        if serie.reset_anual and ano is None:
            raise ValueError(f"serie {serie_id} tem reset anual (TL-07): informe o ano.")
        if serie.regime_numeracao == RegimeNumeracao.GAP_LESS.value:
            return self._reservar_gap_less(serie=serie, tenant_id=tenant_id, ano=ano)
        return self._alocar_buracos_aceitos(serie=serie, tenant_id=tenant_id, ano=ano)

    def _ano_dimensao(self, serie: SerieDocumentoModel, ano: int | None) -> int:
        return ano if (serie.reset_anual and ano is not None) else _SEM_DIMENSAO_ANO

    def _reservar_gap_less(
        self, *, serie: SerieDocumentoModel, tenant_id: UUID, ano: int | None
    ) -> int:
        """Motor M8 (TL-02): advisory lock por (tenant, serie, ano) → libera
        expirados → menor sequencial livre → INSERT (trigger valida densidade)."""
        ano_dim = self._ano_dimensao(serie, ano)
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_xact_lock(%s, hashtext(%s));",
                    [_ADVISORY_LOCK_NUMERACAO_DOC, f"{tenant_id}:{serie.id}:{ano_dim}"],
                )
            agora = timezone.now()
            # Libera expirados ANTES de calcular o próximo (reuso → densidade).
            NumeroDocumentoReservado.objects.filter(
                tenant_id=tenant_id,
                serie_id=serie.id,
                ano=ano_dim,
                confirmado=False,
                ttl_expira_em__lt=agora,
            ).delete()
            em_uso = list(
                NumeroDocumentoReservado.objects.filter(
                    tenant_id=tenant_id, serie_id=serie.id, ano=ano_dim
                ).values_list("sequencial", flat=True)
            )
            seq = proximo_sequencial(em_uso)
            NumeroDocumentoReservado.objects.create(
                tenant_id=tenant_id,
                serie_id=serie.id,
                ano=ano_dim,
                sequencial=seq,
                ttl_expira_em=agora + TTL_RESERVA,
                confirmado=False,
            )
            return seq

    def _alocar_buracos_aceitos(
        self, *, serie: SerieDocumentoModel, tenant_id: UUID, ano: int | None
    ) -> int:
        """UPDATE atômico estilo ADR-0056 (row lock serializa); reset anual TL-07
        resolvido no MESMO statement — o trigger INV-028 permite o "decremento"
        apenas quando `ano_corrente` troca junto."""
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE serie_documento SET
                    proximo_numero = CASE
                        WHEN reset_anual AND ano_corrente IS DISTINCT FROM %s THEN 2
                        ELSE proximo_numero + 1
                    END,
                    ano_corrente = CASE WHEN reset_anual THEN %s ELSE ano_corrente END
                WHERE id = %s AND tenant_id = %s
                RETURNING proximo_numero - 1;
                """,
                [ano, ano, serie.id, tenant_id],
            )
            row = cur.fetchone()
        if row is None:
            raise LookupError(f"serie {serie.id} inexistente para o tenant.")
        return int(row[0])

    def confirmar_numero(
        self, *, tenant_id: UUID, serie_id: UUID, sequencial: int, ano: int | None = None
    ) -> bool:
        """One-shot do gap-less: só confirma reserva viva e não-confirmada (caller
        re-reserva se False). Roda DENTRO da `transaction.atomic` do emissor."""
        serie = SerieDocumentoModel.objects.filter(tenant_id=tenant_id, id=serie_id).first()
        if serie is None:
            return False
        agora = timezone.now()
        n = NumeroDocumentoReservado.objects.filter(
            tenant_id=tenant_id,
            serie_id=serie_id,
            ano=self._ano_dimensao(serie, ano),
            sequencial=sequencial,
            confirmado=False,
            ttl_expira_em__gte=agora,
        ).update(confirmado=True)
        return n == 1

    def liberar_expirados(self, *, tenant_id: UUID, serie_id: UUID, ano: int | None = None) -> int:
        """Remove reservas não-confirmadas vencidas (devolve número à sequência)."""
        serie = SerieDocumentoModel.objects.filter(tenant_id=tenant_id, id=serie_id).first()
        if serie is None:
            return 0
        agora = timezone.now()
        total, _ = NumeroDocumentoReservado.objects.filter(
            tenant_id=tenant_id,
            serie_id=serie_id,
            ano=self._ano_dimensao(serie, ano),
            confirmado=False,
            ttl_expira_em__lt=agora,
        ).delete()
        return total
