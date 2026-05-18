"""Service de registro de auditoria com hash chain serializado.

Concorrencia: usa `pg_advisory_xact_lock` global pra serializar inserts.
Outros writers esperam (em ms — auditoria sao operacoes curtas). Sem isso,
2 inserts paralelos podem pegar mesmo `hash_anterior` e quebrar a cadeia.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import connection, transaction

from .canonicalizar import canonicalizar
from .hash_chain import calcular_hash
from .models import Auditoria


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
