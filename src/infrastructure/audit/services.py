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


def hashear_pii_com_salt_tenant(valor: str, tenant_id: UUID | str) -> str:
    """HMAC-SHA256 de PII pra referenciar em audit sem expor o dado cru.

    SANEA-02 (auditoria 10 lentes — Lente 05 D1 / 07 R-CLI-05). A versao
    anterior fazia sha256("afere-pii-salt:{tenant_id}:{valor}"). O tenant_id
    e publico (aparece em URLs/payloads), entao o "sal" era reconstruivel por
    qualquer um => rainbow-table de CPF/CNPJ de volta. Agora usa HMAC com
    `settings.PII_HASH_KEY` (chave de servidor, nao derivavel do tenant_id):
    irreversivel sem a chave mesmo conhecendo tenant_id + algoritmo. O
    tenant_id continua na mensagem pra manter o hash distinto por tenant
    (mesmo CPF em tenants diferentes => hashes diferentes).

    `tenant_id` e obrigatorio: sem ele o hash perde a separacao por tenant e
    fica cross-tenant correlacionavel. Falha alto (nao silencia com "").
    """
    if not valor:
        return ""
    if tenant_id is None:
        raise ValueError("hashear_pii_com_salt_tenant exige tenant_id (SANEA-02)")
    msg = f"{tenant_id}:{valor}".encode("utf-8")
    return hmac.new(settings.PII_HASH_KEY, msg, hashlib.sha256).hexdigest()


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


# Chave estavel do advisory lock — qualquer int64. hashtext() gera o mesmo
# id em qualquer maquina, then deriva o lock.
_ADVISORY_LOCK_KEY = 0x_AFE_AED17_AED17_0  # "afere audit" memoseado


def registrar_auditoria(
    *,
    action: str,
    resource_summary: str,
    payload: dict[str, Any],
    tenant_id: UUID | None = None,
    usuario_id: UUID | None = None,
) -> Auditoria:
    """Insere linha imutavel na trilha. Calcula hash_atual encadeando com a anterior.

    Chamadores tipicos:
    - signal post_save (UsuarioPerfilTenant criada/modificada)
    - use case (`emitir_certificado`, `cancelar_os`)
    - middleware de webhook (recebimento NFS-e)

    Idempotencia: nao garantida no Marco 4. Marco F-B vai adicionar
    `correlation_id` UNIQUE pra dedupe.
    """
    payload_canon = canonicalizar(payload)

    with transaction.atomic():
        # Serializa inserts da trilha — outros writers esperam ate commit
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s);", [_ADVISORY_LOCK_KEY])

        anterior = Auditoria.objects.order_by("-timestamp").first()
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


def verificar_integridade_cadeia(limit: int | None = None) -> tuple[bool, int, list[str]]:
    """Recalcula todos os hashes em ordem e compara com `hash_atual` salvo.

    Roda no Marco 8 (drill final F-A) + auditoria interna periodica.

    Returns:
        (ok, total_verificado, [ids_quebrados])
    """
    qs = Auditoria.objects.order_by("timestamp")
    if limit is not None:
        qs = qs[:limit]

    quebrados: list[str] = []
    total = 0
    hash_anterior_esperado: str | None = None

    for linha in qs.iterator(chunk_size=500):
        total += 1
        payload_canon = canonicalizar(linha.payload_jsonb)
        recalc = calcular_hash(hash_anterior_esperado, payload_canon)
        if recalc != linha.hash_atual:
            quebrados.append(str(linha.id))
        # Cadeia segue mesmo se quebrou — quero detectar TODOS os elos ruins,
        # nao parar no primeiro. Mas hash_anterior_esperado pega o SALVO (nao
        # o recalculado) porque queremos saber onde a divergencia comecou.
        hash_anterior_esperado = linha.hash_atual

    return (len(quebrados) == 0, total, quebrados)


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
        raise ValueError(
            f"Finalidade invalida: {finalidade}. Use FinalidadeAcessoCliente."
        )
    if categoria_dado_acessado not in CategoriaDadoAcessado.values:
        raise ValueError(
            f"Categoria invalida: {categoria_dado_acessado}."
        )

    return AcessoDadosCliente.objects.create(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        finalidade=finalidade,
        categoria_dado_acessado=categoria_dado_acessado,
        recurso=recurso or {},
        ip_hash=ip_hash,
    )
