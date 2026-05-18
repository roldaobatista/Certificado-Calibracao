"""Porta `AuthorizationProvider` — defesa #3 da pirâmide (ADR-0012).

Domain layer puro: sem dependência de Django, sem dependência de PG.
Quem implementa esta porta:
- `src.infrastructure.authz.django_provider.DjangoAuthorizationProvider`
  (Foundation F-B em diante).
- futuros adapters (Casbin/OPA) trocam SEM tocar no domínio (ADR-0012
  "Critérios de reversão").

Quem CHAMA esta porta (regra cravada em INV-AUTHZ-001):
- Toda view DRF, view Django regular, signal, queryset filtrado por
  autorização, task Celery/Procrastinate. Sem exceção.

A retornada `AuthDecision` é IMUTÁVEL — não dá pra "negociar" depois.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True)
class AuthDecision:
    """Resultado de uma chamada `can()`.

    `allowed`: porteiro deixa passar ou não.
    `reason`: string curta e ESTÁVEL (não localizada) — usada por logs,
        métricas, mensagens pra usuário. Ex: "rbac_denied", "abac_denied",
        "vinculo_expirado", "feature_disabled", "ok".
    `perfis_aplicados`: lista de codigos de perfil que pesaram (ex:
        ["tecnico"]). Útil pra debug + auditoria.
    `escopo_avaliado`: JSON livre com atributos contextuais usados na
        decisão (ex: {"acreditacao_vigente": false}).
    `audit_id`: UUID do registro em `authz_decisions` — preenchido pelo
        adapter após o COMMIT do log (INV-AUTHZ-002).
    """

    allowed: bool
    reason: str
    perfis_aplicados: tuple[str, ...] = field(default_factory=tuple)
    escopo_avaliado: dict[str, Any] = field(default_factory=dict)
    audit_id: UUID | None = None


@runtime_checkable
class AuthorizationProvider(Protocol):
    """Interface única de autorização. Toda decisão passa por aqui.

    Argumentos:
        usuario_id: quem está pedindo.
        action: string `modulo.acao` (ex: "os.criar", "certificado.emitir").
            Catálogo cresce com a Wave A.
        resource: contexto da ação (ex: {"tipo_instrumento": "balanca"}).
            Usado pelo ABAC (Wave A).
        tenant_id: tenant onde a ação acontece. Pode ser NULL pra ações
            pré-tenant (ex: login, listar tenants do usuário).
        purpose: finalidade LGPD que justifica o acesso. Valores válidos
            ficam no catálogo de finalidades (Wave A); F-B aceita string
            livre + ≥1 caractere.
        at_time: instante de avaliação (default: agora). Útil pra
            simulação ("eu poderia fazer X em 2027-03-15?").

    Retorna sempre `AuthDecision` — nunca levanta `PermissionDenied`. Quem
    chama decide se retorna 403, redireciona, mostra mensagem, etc.

    Contrato firme:
        - SEMPRE grava linha em `authz_decisions` (allowed ou denied) ANTES
          de retornar — mesma transação. Quem implementa rompe isso = bug
          regulatório (INV-AUTHZ-002).
        - SEMPRE retorna `AuthDecision`, nunca `None`.
    """

    def can(
        self,
        usuario_id: UUID,
        action: str,
        resource: dict[str, Any] | None = None,
        tenant_id: UUID | None = None,
        purpose: str = "execucao_contrato",
        at_time: datetime | None = None,
    ) -> AuthDecision:
        ...
