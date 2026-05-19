"""Service de registro de auditoria com hash chain serializado.

Concorrencia: usa `pg_advisory_xact_lock` global pra serializar inserts.
Outros writers esperam (em ms — auditoria sao operacoes curtas). Sem isso,
2 inserts paralelos podem pegar mesmo `hash_anterior` e quebrar a cadeia.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import connection, transaction

from .canonicalizar import canonicalizar
from .hash_chain import calcular_hash
from .models import (
    AcessoDadosCliente,
    Auditoria,
    CategoriaDadoAcessado,
    FinalidadeAcessoCliente,
)


class ChavePIIIndisponivel(Exception):
    """Versao de chave de um hash de PII nao esta no registry.

    R1 advogado FA-A1: distingue "nao casou" (False) de "NAO POSSO AFIRMAR"
    (esta excecao). Responder False aqui seria afirmar falsamente ao titular/
    ANPD que o dado nao foi acessado (viola dever de exatidao, art. 6 V).
    """


def hashear_pii_com_salt_tenant(valor: str, tenant_id: UUID | str) -> str:
    """HMAC-SHA256 VERSIONADO de PII pra referenciar em audit sem o dado cru.

    SANEA-02 + FA-A1. Pseudonimizacao com chave de servidor (NAO anonimizacao):
    irreversivel sem a chave mesmo conhecendo tenant_id + algoritmo. tenant_id
    na mensagem mantem o hash distinto por tenant (mesmo CPF, tenants
    diferentes => hashes diferentes).

    FA-A1: retorno PREFIXADO `{key_id}:{hexdigest}` (ex.: `v1:ab3f...`). O
    prefixo permite verificar o hash com a chave certa apos rotacao
    (`verificar_pii_hash`) — responde ANPD "quem viu CPF X em data Y" sem
    depender da SECRET_KEY (que pode ser rotacionada). Usa a chave ATIVA do
    `settings.PII_HASH_KEY_REGISTRO`.

    `tenant_id` obrigatorio: sem ele o hash perde separacao por tenant e fica
    cross-tenant correlacionavel. Falha alto (nao silencia com "").
    """
    if not valor:
        return ""
    if tenant_id is None:
        raise ValueError("hashear_pii_com_salt_tenant exige tenant_id (SANEA-02)")
    registro = settings.PII_HASH_KEY_REGISTRO
    msg = f"{tenant_id}:{valor}".encode()
    digest = hmac.new(registro.chave_ativa(), msg, hashlib.sha256).hexdigest()
    return f"{registro.ativa_id}:{digest}"


def verificar_pii_hash(valor: str, tenant_id: UUID | str, hash_armazenado: str) -> bool:
    """Confere se `valor` gera `hash_armazenado` (qualquer versao de chave).

    Resolve a chave pelo prefixo `{key_id}:` no hash armazenado — funciona
    apos rotacao desde que a chave aposentada esteja em PII_HASH_KEYS_RETIRED.
    Comparacao em tempo constante (`hmac.compare_digest`).

    Raises:
        ChavePIIIndisponivel: versao do hash ausente do registry — resposta
            INCONCLUSIVA, NAO negativa (R1 advogado). Hash sem prefixo `vN:`
            tambem cai aqui (entrada invalida, nao "legado silencioso").
    """
    if tenant_id is None:
        raise ValueError("verificar_pii_hash exige tenant_id (SANEA-02)")
    key_id, sep, digest_armazenado = hash_armazenado.partition(":")
    registro = settings.PII_HASH_KEY_REGISTRO
    if not sep or not digest_armazenado or not registro.tem(key_id):
        raise ChavePIIIndisponivel(
            f"versao de chave {key_id!r} ausente do registry — verificacao "
            f"INCONCLUSIVA, nao negativa (FA-A1 R1)"
        )
    msg = f"{tenant_id}:{valor}".encode()
    recalculado = hmac.new(registro.chave(key_id), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(recalculado, digest_armazenado)


# CONCERN Auditor Seguranca 2026-05-18 (US-002 retroativa): sanitizar payload de
# audit antes de devolver na API. Mesmo sendo gerado por nos (nao usuario), eh
# defesa em profundidade — se outro modulo gravar PII por engano no audit,
# timeline da visao 360 nao expoe.
_RE_CPF_AUDIT = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_RE_CNPJ_AUDIT = re.compile(
    r"\b[A-Z0-9]{2}\.?[A-Z0-9]{3}\.?[A-Z0-9]{3}/?[A-Z0-9]{4}-?\d{2}\b", re.IGNORECASE
)
_RE_EMAIL_AUDIT = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_RE_TELEFONE_AUDIT = re.compile(r"\b(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b")

# Chaves de payload conhecidamente sensiveis — denylist explicita.
_CHAVES_PII_DENYLIST = frozenset(
    {
        "nome",
        "nome_fantasia",
        "documento",
        "cpf",
        "cnpj",
        "email",
        "telefone",
        "endereco",
        "justificativa_bruta",
        "motivo_observacao",
        "procedencia_declarada",
    }
)


def sanitizar_payload_audit(payload: Any) -> Any:
    """Remove PII de payload antes de devolver na API.

    Aplicacao: timeline da visao 360, listagem de importacoes, qualquer
    endpoint que devolva `Auditoria.payload_jsonb` ao usuario.

    Comportamento:
    - Chaves em `_CHAVES_PII_DENYLIST` viram `[REDACTED]`.
    - Valores string sao escaneados por regex (CPF/CNPJ/email/telefone);
      match vira `[REDACTED]`.
    - Estruturas aninhadas (dict, list) sao percorridas recursivamente.
    - Tipos primitivos (int, bool, None, float) passam intactos.
    """
    if isinstance(payload, dict):
        return {
            k: ("[REDACTED]" if k in _CHAVES_PII_DENYLIST else sanitizar_payload_audit(v))
            for k, v in payload.items()
        }
    if isinstance(payload, list):
        return [sanitizar_payload_audit(item) for item in payload]
    if isinstance(payload, str):
        if (
            _RE_CPF_AUDIT.search(payload)
            or _RE_CNPJ_AUDIT.search(payload)
            or _RE_EMAIL_AUDIT.search(payload)
            or _RE_TELEFONE_AUDIT.search(payload)
        ):
            return "[REDACTED]"
        return payload
    return payload


# FA-C1: namespace de 2 args pro advisory lock (pg_advisory_xact_lock(int4,
# int4)). 1º arg = classe constante "auditoria" — isola o espaco de locks
# de auditoria de qualquer outro advisory lock no sistema (evita deadlock
# sutil por colisao de hashtext). 2º arg = hashtext(chave por-tenant).
_ADVISORY_LOCK_CLASSE_AUDIT = 0x_AFE_AED  # 'afe aed' — classe de locks de auditoria

# Sentinela: "verificar TODAS as cadeias" (distinto de tenant_id=None, que
# significa a cadeia "sistema").
_TODAS_AS_CADEIAS = object()


def registrar_auditoria(
    *,
    action: str,
    resource_summary: str,
    payload: dict[str, Any],
    tenant_id: UUID | None = None,
    usuario_id: UUID | None = None,
) -> Auditoria:
    """Insere linha imutavel na cadeia hash DO TENANT (FA-C1).

    Cada tenant tem cadeia independente; eventos sem tenant (tenant_id=None)
    formam a cadeia "sistema" (exige run_as_system — modo_sistema='1').
    Encadeia no ultimo elo DO MESMO tenant, ordenado por `sequencia`
    (monotonica; timestamp colide em microssegundo sob o lock).

    Chamadores tipicos: signal post_save, use case, middleware webhook.
    Idempotencia: nao garantida no Marco 4 (F-B adiciona correlation_id).
    """
    payload_canon = canonicalizar(payload)
    chave_cadeia = str(tenant_id) if tenant_id is not None else "SYSTEM"

    with transaction.atomic():
        # Lock POR tenant (nao global): inserts de tenants distintos nao se
        # serializam entre si. Namespace de 2 args isola locks de auditoria.
        with connection.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(%s, hashtext(%s));",
                [_ADVISORY_LOCK_CLASSE_AUDIT, chave_cadeia],
            )

        # Ultimo elo DA CADEIA DESTE tenant (RLS deixa ver as proprias
        # linhas no contexto do request; cadeia sistema sob run_as_system).
        _qs_anterior = Auditoria.objects.order_by("-sequencia")
        anterior = (
            _qs_anterior.filter(tenant_id__isnull=True)
            if tenant_id is None
            else _qs_anterior.filter(tenant_id=tenant_id)
        ).first()
        hash_anterior = anterior.hash_atual if anterior else None
        hash_atual = calcular_hash(hash_anterior, payload_canon)

        return Auditoria.objects.create(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            action=action,
            resource_summary=resource_summary,
            payload_jsonb=payload,
            hash_anterior=hash_anterior,
            hash_atual=hash_atual,
        )


def _verificar_uma_cadeia(tenant_id: UUID | None) -> tuple[bool, int, list[str]]:
    """Recalcula a cadeia de UM tenant (None = cadeia sistema) por `sequencia`.

    Q-02 corrigido: `hash_anterior_esperado = recalc` (encadeia no
    RECALCULADO, nao no salvo). Assim adulteracao no MEIO quebra esse elo
    E TODOS os seguintes — propriedade real de hash chain. A versao
    anterior usava o hash salvo e so acusava o elo adulterado.
    """
    quebrados: list[str] = []
    total = 0
    hash_anterior_esperado: str | None = None

    _qs_cadeia = Auditoria.objects.order_by("sequencia")
    qs = (
        _qs_cadeia.filter(tenant_id__isnull=True)
        if tenant_id is None
        else _qs_cadeia.filter(tenant_id=tenant_id)
    ).iterator(chunk_size=500)
    for linha in qs:
        total += 1
        payload_canon = canonicalizar(linha.payload_jsonb)
        recalc = calcular_hash(hash_anterior_esperado, payload_canon)
        if recalc != linha.hash_atual:
            quebrados.append(str(linha.id))
        hash_anterior_esperado = recalc

    return (len(quebrados) == 0, total, quebrados)


def verificar_integridade_cadeia(
    tenant_id: UUID | None | object = _TODAS_AS_CADEIAS,
) -> dict[str | None, tuple[bool, int, list[str]]]:
    """Verifica a hash chain — uma cadeia INDEPENDENTE por tenant (FA-C1).

    - Sem argumento: verifica TODAS as cadeias (cada tenant de
      `Tenant.objects` + a cadeia "sistema" de tenant NULL).
    - `tenant_id=X`: só a cadeia de X (caso CGCRE — trilha de 1 lab).
    - `tenant_id=None`: só a cadeia "sistema".

    Cada cadeia e lida no seu proprio contexto: tenant via
    `run_in_tenant_context` (RLS deixa ver as linhas do tenant); cadeia
    sistema via `run_as_system` (modo_sistema='1' libera tenant NULL).

    Returns: {tenant_id_str_ou_None: (ok, total, [ids_quebrados])}
    """
    from src.infrastructure.multitenant.connection import (
        run_as_system,
        run_in_tenant_context,
    )
    from src.infrastructure.tenant.models import Tenant

    if tenant_id is _TODAS_AS_CADEIAS:
        alvos: list[UUID | None] = list(Tenant.objects.values_list("id", flat=True))
        alvos.append(None)  # cadeia sistema
    else:
        alvos = [tenant_id]  # type: ignore[list-item]

    resultado: dict[str | None, tuple[bool, int, list[str]]] = {}
    for tid in alvos:
        chave = str(tid) if tid is not None else None
        if tid is None:
            with run_as_system():
                resultado[chave] = _verificar_uma_cadeia(None)
        else:
            with run_in_tenant_context(tenant_id=tid):
                resultado[chave] = _verificar_uma_cadeia(tid)
    return resultado


def registrar_acesso_dados_cliente(
    *,
    tenant_id: UUID,
    usuario_id: UUID | None,
    cliente_id: UUID | None,
    finalidade: str,
    categoria_dado_acessado: str = CategoriaDadoAcessado.PII_IDENTIFICADORA,
    recurso: dict[str, Any] | None = None,
    ip_hash: str = "",
) -> AcessoDadosCliente:
    """INV-013 — log de visualizacao de dados de cliente.

    Tabela INSERT-only com trigger PG anti-mutation. Chamada ANTES de retornar
    response na view (visao 360). R1 advogado: `recurso` JSONB sem PII cru.
    """
    if finalidade not in FinalidadeAcessoCliente.values:
        raise ValueError(f"Finalidade invalida: {finalidade}. Use FinalidadeAcessoCliente.")
    if categoria_dado_acessado not in CategoriaDadoAcessado.values:
        raise ValueError(f"Categoria invalida: {categoria_dado_acessado}.")

    return AcessoDadosCliente.objects.create(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        finalidade=finalidade,
        categoria_dado_acessado=categoria_dado_acessado,
        recurso=recurso or {},
        ip_hash=ip_hash,
    )
