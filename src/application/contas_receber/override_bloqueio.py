"""Use case: override de bloqueio de inadimplência (Fatia 2b — T-CR-034/override).

D-CR-10 / AC-CR-010-5 / INV-CR-OVERRIDE-WORM / INV-CR-OVERRIDE-ANTI-PII.

Regras:
  - `justificativa` ≥ 100 chars → JustificativaInsuficiente (422).
  - `justificativa` não pode conter PII (CPF/CNPJ/email/telefone) — anti-PII
    via regex do molde `src/infrastructure/clientes/mesclagem.py`
    (INV-CR-OVERRIDE-ANTI-PII / D-CR-20).
  - `novo_prazo_max_dias` ≤ 90 → JustificativaInsuficiente (422) se exceder.
  - Limite 5%/mês dos bloqueios ativos do tenant (R-CR-NOVO-4 / ADR-0043 §3):
    estouro → alerta P1 (log CRITICAL) + OverrideForaDeAlcada.
  - Papel gerente é checado na VIEW (authz) — o use case não recebe request.
  - Grava `OverrideBloqueio` WORM (INSERT-only via trigger 0003).
  - NÃO valida A3 real (Wave A grava `a3_signature_id` como referência — GATE-CR-A3).

Clean arch: NÃO importa DRF. A VIEW traduz para HTTP.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.contas_receber.entities import OverrideBloqueio
from src.domain.contas_receber.erros import (
    JustificativaInsuficiente,
    OverrideForaDeAlcada,
    TituloNaoEncontrado,
)
from src.domain.contas_receber.portas import TituloRepository

logger = logging.getLogger(__name__)

# ---- Constantes ------------------------------------------------------------

_JUSTIFICATIVA_MIN_CHARS = 100
_PRAZO_MAX_DIAS = 90

# Limite de overrides: 5% dos bloqueios do mês (mínimo 1 — não bloqueamos com 0 bloqueios)
# Wave A: usamos contagem de overrides do próprio mês como proxy.
# O cálculo real seria 5% dos ClienteBloqueio do mês, mas CR não tem acesso a clientes.
# Decisão pragmática: 5 overrides/mês como teto absoluto em Wave A.
# GATE-CR-INADIMPLENCIA-RECONCILIA ajustará quando o adapter real de inadimplência existir.
_LIMITE_OVERRIDES_MES = 5

# Anti-PII — mesmos regex do molde `src/infrastructure/clientes/mesclagem.py`.
_RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_RE_CNPJ = re.compile(
    r"\b[A-Z0-9]{2}\.?[A-Z0-9]{3}\.?[A-Z0-9]{3}/?[A-Z0-9]{4}-?\d{2}\b", re.IGNORECASE
)
_RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_RE_TELEFONE = re.compile(r"\b(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b")


def _validar_justificativa_anti_pii(texto: str) -> None:
    """Levanta JustificativaInsuficiente se `texto` contém PII (INV-CR-OVERRIDE-ANTI-PII)."""
    achados: list[str] = []
    if _RE_CPF.search(texto):
        achados.append("CPF")
    if _RE_CNPJ.search(texto):
        achados.append("CNPJ")
    if _RE_EMAIL.search(texto):
        achados.append("e-mail")
    if _RE_TELEFONE.search(texto):
        achados.append("telefone")
    if achados:
        raise JustificativaInsuficiente(
            f"Justificativa do override contém PII ({', '.join(achados)}) — "
            "não é permitido gravar identificadores pessoais em texto WORM "
            "(INV-CR-OVERRIDE-ANTI-PII / D-CR-20)."
        )


# ---- Input / Output --------------------------------------------------------

@dataclass(frozen=True, slots=True)
class OverrideBloqueioInput:
    """Payload do override de bloqueio (D-CR-10 / AC-CR-010-5)."""

    tenant_id: UUID
    titulo_id: UUID
    cliente_id: UUID  # id concreto do cliente (não hash — gerente autenticado)
    novo_prazo_max_dias: int  # ≤ 90
    justificativa: str  # ≥ 100 chars + anti-PII
    a3_signature_id: str  # ref Wave A (sem verificação real — GATE-CR-A3)
    usuario_id: UUID  # quem faz o override (gerente autenticado)
    perfil_no_evento: str  # CHAR(1) snapshot (D-CR-6)


@dataclass(frozen=True, slots=True)
class OverrideBloqueioOutput:
    """Resultado do override."""

    override: OverrideBloqueio


# ---- Use case --------------------------------------------------------------

def executar(
    inp: OverrideBloqueioInput,
    *,
    repo: TituloRepository,
) -> OverrideBloqueioOutput:
    """Cria OverrideBloqueio WORM após validações.

    Levanta:
      - `TituloNaoEncontrado` (→ 404) se título não pertence ao tenant.
      - `JustificativaInsuficiente` (→ 422) se justificativa curta ou com PII.
      - `OverrideForaDeAlcada` (→ 422) se `novo_prazo_max_dias > 90`
        ou se estouro do limite 5%/mês.
    """
    # 1. Valida justificativa ≥ 100 chars.
    if len(inp.justificativa) < _JUSTIFICATIVA_MIN_CHARS:
        raise JustificativaInsuficiente(
            f"Justificativa do override deve ter ao menos {_JUSTIFICATIVA_MIN_CHARS} caracteres "
            f"(recebeu {len(inp.justificativa)}) — D-CR-10 / AC-CR-010-5."
        )

    # 2. Anti-PII (INV-CR-OVERRIDE-ANTI-PII / D-CR-20).
    _validar_justificativa_anti_pii(inp.justificativa)

    # 3. Novo prazo ≤ 90 dias.
    if inp.novo_prazo_max_dias > _PRAZO_MAX_DIAS:
        raise OverrideForaDeAlcada(
            f"novo_prazo_max_dias={inp.novo_prazo_max_dias} excede o máximo de "
            f"{_PRAZO_MAX_DIAS} dias (AC-CR-010-5 / D-CR-10)."
        )

    # 4. Confirma que o título existe e pertence ao tenant (cross-tenant 404).
    titulo = repo.obter_por_id(tenant_id=inp.tenant_id, titulo_id=inp.titulo_id)
    if titulo is None:
        raise TituloNaoEncontrado(
            f"Título {inp.titulo_id} não encontrado para tenant {inp.tenant_id}."
        )

    # 5. Limite 5%/mês (R-CR-NOVO-4 / ADR-0043 §3).
    agora = datetime.now(UTC)
    contagem = repo.contar_overrides_no_mes(
        tenant_id=inp.tenant_id,
        ano=agora.year,
        mes=agora.month,
    )
    if contagem >= _LIMITE_OVERRIDES_MES:
        logger.critical(  # alerta P1
            "contas_receber override_bloqueio estouro limite 5pct/mes",
            extra={
                "tenant_id": str(inp.tenant_id),
                "contagem_mes": contagem,
                "limite": _LIMITE_OVERRIDES_MES,
                "titulo_id": str(inp.titulo_id),
                "usuario_id": str(inp.usuario_id),
            },
        )
        raise OverrideForaDeAlcada(
            f"Limite de {_LIMITE_OVERRIDES_MES} overrides/mês atingido para este tenant. "
            "Consulte o suporte (R-CR-NOVO-4 / ADR-0043 §3)."
        )

    # 6. Cria OverrideBloqueio WORM.
    override = OverrideBloqueio(
        override_id=uuid4(),
        titulo_id=inp.titulo_id,
        cliente_id=inp.cliente_id,
        novo_prazo_max_dias=inp.novo_prazo_max_dias,
        justificativa=inp.justificativa,
        a3_signature_id=inp.a3_signature_id,
        usuario_id=inp.usuario_id,
        perfil_no_evento=inp.perfil_no_evento,
        criado_em=agora,
    )
    repo.salvar_override(tenant_id=inp.tenant_id, override=override)

    return OverrideBloqueioOutput(override=override)
