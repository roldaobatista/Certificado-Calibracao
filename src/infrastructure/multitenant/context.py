"""ContextVars com a lista de tenants permitidos + tenant ativo do request.

ContextVar (PEP 567) substitui thread-local em Python moderno — funciona
em codigo async tambem (preparacao Wave A com ASGI). Cada request copia
o contexto; nao vaza entre requests.

ADR-0002 v2 §3: middleware seta LISTA `tenant_ids` mesmo pra usuario com
1 tenant unico. Suporta perfis cross-tenant (marketplace, matriz+filiais,
auditor RBC visitante) sem violar defesa em profundidade.
"""

from __future__ import annotations

from contextvars import ContextVar
from uuid import UUID

# Lista de tenants permitidos pra este request (resolvida no middleware
# consultando UsuarioPerfilTenant).
tenant_ids_context: ContextVar[list[UUID]] = ContextVar("tenant_ids_context", default=[])

# Tenant onde a acao ATUAL acontece. Sempre subset de tenant_ids_context.
# INSERT/UPDATE gravam tenant_id = active_tenant_id (manager forca isso).
active_tenant_context: ContextVar[UUID | None] = ContextVar("active_tenant_context", default=None)

# Identidade do usuario logado neste request. Usada por:
# - policy RLS de UsuarioPerfilTenant (usuario_id = current_setting('app.usuario_id'))
# - audit trail (Marco 4)
usuario_id_context: ContextVar[UUID | None] = ContextVar("usuario_id_context", default=None)

# FA-M3: `limpar_contexto()` foi REMOVIDA (armadilha plantada). Fazia
# `.set([])` num `finally` — padrão ERRADO pra ContextVar em fronteira de
# request: cria um valor "limpo" no contexto atual em vez de restaurar o
# anterior, e em pool de threads/async o próximo request herdaria esse
# valor como se tivesse sido setado (não o default da var). O padrão
# correto — capturar o token de `.set()` e `reset(token)` no `finally` —
# já é usado pelo middleware (middleware.py:97-111) e por
# connection.py (run_in_tenant_context/run_as_system). Não recriar.
