"""Orquestração das PORTAS da análise crítica cl. 7.1 (lado sujo) — T-ORC-033.

A função pura ``decidir_analise_critica`` (domínio) recebe resultados já
materializados; este módulo é quem CHAMA as portas (escopos_cmc / procedimentos)
e resolve o perfil regulatório + suspensão server-side (matriz §"Implementação" /
AJUSTE-3). Mantém a view fina e a decisão testável sem banco.

Imports locais (molde precificacao/views) — evita ciclo infra→infra e custo de
import no boot.

Refs: D-ORC-5; analise-critica-matriz.md; ADR-0067 (perfil); ADR-0073/0076.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.domain.comercial.orcamentos.analise_critica import ResultadoItemMensurando
from src.domain.comercial.orcamentos.entities import ItemOrcamento
from src.domain.comercial.orcamentos.enums import TipoAtividadeAlvo


def resolver_perfil_e_suspensao() -> tuple[str, bool]:
    """Resolve (perfil_char, acreditacao_suspensa) server-side (AJUSTE-3).

    Usa só a API pública de ``perfil_tenant_helper``: ``obter_perfil_tenant_corrente``
    (char A/B/C/D/"") + ``tenant_perfil_e({"A"})`` (que já embute a janela de
    suspensão temporária — AC-002-7). Nunca lê perfil de payload.

    Returns:
        ``(perfil, suspensa)`` — ``perfil`` é ``""`` se indeterminado (a view
        retorna 422 PerfilIndeterminado antes de chamar as portas).
    """
    from src.infrastructure.authz.perfil_tenant_helper import (
        obter_perfil_tenant_corrente,
        tenant_perfil_e,
    )

    perfil = obter_perfil_tenant_corrente()
    suspensa = False
    if perfil == "A":
        allowed, reason = tenant_perfil_e({"A"})
        suspensa = (not allowed) and reason.startswith("tenant_acreditacao_suspensa")
    return perfil, suspensa


def avaliar_itens_calibracao(
    itens: list[ItemOrcamento],
    *,
    tenant_id: UUID,
    data: datetime,
) -> list[ResultadoItemMensurando]:
    """Avalia, por item de calibração, CMC + procedimento vigente (portas M6/M7).

    Só itens ``tipo_atividade_alvo == CALIBRACAO`` (os únicos com mensurando
    declarado — D-ORC-5). Itens comerciais e técnicos não-calibração são ignorados.

    Para cada item chama:
      - ``escopos_cmc.query_service.cobre(...) → (cobre_cmc, cmc_reason)``
      - ``procedimentos_calibracao.query_service.cobre_procedimento(...) →
        (procedimento_ok, dict|None)``

    Returns:
        lista de ``ResultadoItemMensurando`` (vazia se não há item de calibração).
    """
    from src.infrastructure.metrologia.escopos_cmc.query_service import cobre
    from src.infrastructure.metrologia.procedimentos_calibracao.query_service import (
        cobre_procedimento,
    )

    resultados: list[ResultadoItemMensurando] = []
    for item in itens:
        if item.tipo_atividade_alvo != TipoAtividadeAlvo.CALIBRACAO:
            continue
        equipamento_id = item.equipamento_id
        faixa_min = item.faixa_solicitada_min
        faixa_max = item.faixa_solicitada_max
        if equipamento_id is None or faixa_min is None or faixa_max is None:
            # Invariante de calibração (ItemOrcamento.__post_init__ +
            # CHECK ck_orc_item_mensurando_calibracao) garante equipamento+faixa.
            # Guarda defensiva de narrowing — ramo morto na prática.
            continue
        grandeza = item.grandeza_solicitada or ""
        unidade = item.unidade_solicitada or ""

        cobre_cmc, cmc_reason = cobre(
            tenant_id=tenant_id,
            grandeza=grandeza,
            faixa_min=faixa_min,
            faixa_max=faixa_max,
            unidade=unidade,
            data=data,
        )
        procedimento_ok, proc = cobre_procedimento(
            tenant_id=tenant_id,
            grandeza=grandeza,
            faixa_min=faixa_min,
            faixa_max=faixa_max,
            unidade=unidade,
            data=data,
        )
        proc = proc or {}
        resultados.append(
            ResultadoItemMensurando(
                equipamento_id=equipamento_id,
                grandeza=grandeza,
                faixa_min=faixa_min,
                faixa_max=faixa_max,
                unidade=unidade,
                cobre_cmc=cobre_cmc,
                cmc_reason=cmc_reason,
                procedimento_ok=procedimento_ok,
                procedimento_id=proc.get("procedimento_id"),
                procedimento_codigo=proc.get("codigo"),
                procedimento_versao=proc.get("versao"),
                procedimento_revisao=proc.get("numero_revisao"),
                procedimento_hash_anexo=proc.get("hash_anexo"),
            )
        )
    return resultados
