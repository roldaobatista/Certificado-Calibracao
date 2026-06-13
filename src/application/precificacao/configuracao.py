"""Use cases de configuração da precificação (T-PRC-033 — US-PRC-004).

`configurar_faixas`: replace-all atômico com validação do CONJUNTO 0..100
(INV-PRC-FAIXAS-CONTIGUAS / TL-PRC-16).

`configurar_perfil_composicao`: cria/atualiza PerfilComposicaoPreco por
item-serviço (D-PRC-2).

`configurar_parametros`: nova versão dos ParametrosPrecificacaoTenant
(versionado — replay bit-a-bit AC-PRC-002-3).

`seed_faixas_default`: etapa no `provisionar_tenant` (ADR-0015) +
RunPython para tenants existentes (D-PRC-3 / TL-PRC-15).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.hash_versionado import (
    canonicalizar_payload_para_hmac,
)
from src.domain.precificacao.entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PerfilComposicaoPreco,
)
from src.domain.precificacao.enums import Alcada
from src.domain.precificacao.repository import (
    FaixaRepository,
    ParametrosRepository,
)
from src.domain.precificacao.transicoes import validar_faixas_contiguas
from src.domain.precificacao.value_objects import Percentual

# Faixas default: 0-10% LIVRE / 10-20% GERENTE / 20-100% DONO (D-PRC-3)
FAIXAS_DEFAULT: tuple[tuple[Decimal, Decimal, Alcada], ...] = (
    (Decimal("0"), Decimal("10"), Alcada.LIVRE),
    (Decimal("10"), Decimal("20"), Alcada.GERENTE),
    (Decimal("20"), Decimal("100"), Alcada.DONO),
)


def _hash_conjunto_faixas(faixas: list[FaixaAprovacaoDesconto]) -> str:
    """Hash canônico ADR-0029 do conjunto completo de faixas (fingerprint de versão)."""
    payload = [
        {"pct_de": str(f.pct_de.valor), "pct_ate": str(f.pct_ate.valor), "alcada": f.alcada.value}
        for f in sorted(faixas, key=lambda f: f.pct_de.valor)
    ]
    return hashlib.sha256(  # audit-pii-salt: skip -- hash estrutural de conjunto de faixas publico (nao ha PII aqui; faixas sao config comercial do tenant, nao dado pessoal)
        canonicalizar_payload_para_hmac({"faixas": payload})
    ).hexdigest()


# ---------------------------------------------------------------------------
# configurar_faixas (D-PRC-3 / TL-PRC-16)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FaixaInput:
    pct_de: Decimal
    pct_ate: Decimal
    alcada: Alcada


@dataclass(frozen=True, slots=True)
class ConfigurarFaixasInput:
    tenant_id: UUID
    faixas: tuple[FaixaInput, ...]
    criado_por: UUID
    agora: datetime | None = None  # None = datetime.now(UTC)


def configurar_faixas(
    inp: ConfigurarFaixasInput,
    *,
    repo_faixa: FaixaRepository,
) -> list[FaixaAprovacaoDesconto]:
    """Replace-all atômico das faixas de aprovação (D-PRC-3 / TL-PRC-16).

    Valida o CONJUNTO COMPLETO 0..100 antes de persistir (INV-PRC-FAIXAS-CONTIGUAS).
    Advisory lock por tenant (repo Django — namespace 880_404).
    Caller deve embrulhar em `transaction.atomic`.

    Raises:
      FaixasDescontoInvalidas: conjunto não cobre 0..100 sem buraco/sobreposição.
    """
    # Busca versao_n atual (max) para incrementar
    atuais = repo_faixa.listar(tenant_id=inp.tenant_id)
    versao_n = max((f.versao_n for f in atuais), default=0) + 1

    # Constrói as entidades candidatas (sem hash ainda — hash depende do conjunto)
    candidatas: list[FaixaAprovacaoDesconto] = [
        FaixaAprovacaoDesconto(
            id=uuid4(),
            tenant_id=inp.tenant_id,
            pct_de=Percentual(f.pct_de),
            pct_ate=Percentual(f.pct_ate),
            alcada=f.alcada,
            versao_n=versao_n,
            hash_conjunto="",  # preenchido após validação
            criado_por=inp.criado_por,
        )
        for f in inp.faixas
    ]

    # Valida CONJUNTO completo (INV-PRC-FAIXAS-CONTIGUAS)
    validar_faixas_contiguas(candidatas)

    # Gera hash do conjunto válido
    hash_conjunto = _hash_conjunto_faixas(candidatas)

    # Reconstrói com hash real
    faixas_finais: list[FaixaAprovacaoDesconto] = [
        FaixaAprovacaoDesconto(
            id=f.id,
            tenant_id=f.tenant_id,
            pct_de=f.pct_de,
            pct_ate=f.pct_ate,
            alcada=f.alcada,
            versao_n=versao_n,
            hash_conjunto=hash_conjunto,
            criado_por=inp.criado_por,
        )
        for f in candidatas
    ]

    # Replace-all atômico (DELETE + bulk_create sob advisory lock no repo)
    repo_faixa.substituir_todas(
        tenant_id=inp.tenant_id,
        faixas=faixas_finais,
        criado_por=inp.criado_por,
    )
    return faixas_finais


# ---------------------------------------------------------------------------
# seed_faixas_default (provisionar_tenant ADR-0015 + RunPython tenants existentes)
# ---------------------------------------------------------------------------


def seed_faixas_default(
    *,
    tenant_id: UUID,
    criado_por: UUID,
    repo_faixa: FaixaRepository,
) -> list[FaixaAprovacaoDesconto]:
    """Seed das faixas default no `provisionar_tenant` (D-PRC-3 / TL-PRC-15).

    Chamado na etapa de seed do provisionar_tenant (ADR-0015) e pelo RunPython
    na migration 0008 para tenants existentes sem faixas configuradas.
    Idempotente: se já existem faixas, retorna as existentes sem alterar.
    """
    existentes = repo_faixa.listar(tenant_id=tenant_id)
    if existentes:
        return existentes

    return configurar_faixas(
        ConfigurarFaixasInput(
            tenant_id=tenant_id,
            faixas=tuple(
                FaixaInput(pct_de=de, pct_ate=ate, alcada=alcada)
                for de, ate, alcada in FAIXAS_DEFAULT
            ),
            criado_por=criado_por,
        ),
        repo_faixa=repo_faixa,
    )


# ---------------------------------------------------------------------------
# configurar_perfil_composicao (D-PRC-2)
# ---------------------------------------------------------------------------

# Repository protocol local (evitar import circular; mirror de FaixaRepository)


@dataclass(frozen=True, slots=True)
class ConfigurarPerfilComposicaoInput:
    tenant_id: UUID
    item_servico_id: UUID
    componentes_esperados: tuple[UUID, ...]
    criado_por: UUID
    aviso_texto: str = ""


def configurar_perfil_composicao(
    inp: ConfigurarPerfilComposicaoInput,
    *,
    repo: PerfilComposicaoRepository,
) -> PerfilComposicaoPreco:
    """Cria ou atualiza PerfilComposicaoPreco por item-serviço (D-PRC-2).

    Mutável (ADR-0031 Padrão C — configuração). Upsert por (tenant, item_servico).

    Args:
      inp: dados do perfil.
      repo: repositório de PerfilComposicaoPreco.
    """
    existente = repo.obter_por_item(
        tenant_id=inp.tenant_id, item_servico_id=inp.item_servico_id
    )
    if existente is not None:
        novo = PerfilComposicaoPreco(
            id=existente.id,
            tenant_id=existente.tenant_id,
            item_servico_id=existente.item_servico_id,
            componentes_esperados=inp.componentes_esperados,
            criado_por=inp.criado_por,
            aviso_texto=inp.aviso_texto or None,
        )
        repo.atualizar(novo)
        return novo

    perfil = PerfilComposicaoPreco(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        item_servico_id=inp.item_servico_id,
        componentes_esperados=inp.componentes_esperados,
        criado_por=inp.criado_por,
        aviso_texto=inp.aviso_texto or None,
    )
    repo.salvar(perfil)
    return perfil


# ---------------------------------------------------------------------------
# configurar_parametros (D-PRC-9 — versionado)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConfigurarParametrosInput:
    tenant_id: UUID
    custo_km: Decimal
    taxa_parcelamento_mensal: Decimal
    pct_comissao_prevista: Decimal
    margem_alvo_default: Decimal
    margem_piso_default: Decimal
    criado_por: UUID
    agora: datetime | None = None  # None = datetime.now(UTC)


def configurar_parametros(
    inp: ConfigurarParametrosInput,
    *,
    repo_params: ParametrosRepository,
) -> ParametrosPrecificacaoTenant:
    """Nova versão dos parâmetros de precificação do tenant (D-PRC-9).

    Versionado (versao_n denso) para replay bit-a-bit (AC-PRC-002-3).
    Valores NUNCA em claro em eventos (segredo comercial — INV-PRC-SEGREDO-LOG).

    Args:
      inp: novos parâmetros.
      repo_params: repositório de parâmetros.
    """
    agora = inp.agora if inp.agora is not None else datetime.now(UTC)

    atuais = repo_params.obter_vigentes(tenant_id=inp.tenant_id)
    versao_n = (atuais.versao_n + 1) if atuais is not None else 1

    params = ParametrosPrecificacaoTenant(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        versao_n=versao_n,
        custo_km=inp.custo_km,
        taxa_parcelamento_mensal=Percentual(inp.taxa_parcelamento_mensal),
        pct_comissao_prevista=Percentual(inp.pct_comissao_prevista),
        margem_alvo_default=Percentual(inp.margem_alvo_default),
        margem_piso_default=Percentual(inp.margem_piso_default),
        criado_por=inp.criado_por,
        criado_em=agora,
    )
    repo_params.salvar(params)
    return params


# ---------------------------------------------------------------------------
# Protocol de PerfilComposicaoRepository (local — evitar import circular)
# ---------------------------------------------------------------------------


class PerfilComposicaoRepository(Protocol):
    """Protocol para repositório de PerfilComposicaoPreco."""

    def obter_por_item(
        self, *, tenant_id: UUID, item_servico_id: UUID
    ) -> PerfilComposicaoPreco | None:
        """Retorna o perfil ativo para o item-serviço, ou None."""
        ...

    def salvar(self, perfil: PerfilComposicaoPreco) -> None:
        """Persiste novo perfil."""
        ...

    def atualizar(self, perfil: PerfilComposicaoPreco) -> None:
        """Atualiza perfil existente (mutável — ADR-0031 Padrão C)."""
        ...
