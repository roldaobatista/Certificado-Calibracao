"""Adapter Django do `ClienteRepository` (ADR-0007).

Implementa o Protocol `src.domain.comercial.clientes.repository.ClienteRepository`
sobre Django ORM. View injeta este adapter no use case.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from src.domain.comercial.clientes.repository import (
    ClienteImportacaoInput,
    ClienteSnapshot,
    LinhaRejeitada,
    ResultadoImportacao,
)
from src.infrastructure.clientes.csv_safety import sanitizar_celula_csv
from src.infrastructure.clientes.models import Cliente


def _to_snapshot(c: Cliente) -> ClienteSnapshot:
    return ClienteSnapshot(
        id=c.id,
        tenant_id=c.tenant_id,
        tipo_pessoa=c.tipo_pessoa,
        documento=c.documento,
        nome=c.nome,
        nome_fantasia=c.nome_fantasia,
        email=c.email,
        telefone=c.telefone,
        aceite_lgpd_em=c.aceite_lgpd_em,
        aceite_lgpd_versao=c.aceite_lgpd_versao,
        aceite_lgpd_ip_hash=c.aceite_lgpd_ip_hash,
        aceite_lgpd_origem=c.aceite_lgpd_origem,
        aceite_lgpd_dispensa_motivo=c.aceite_lgpd_dispensa_motivo,
        deletado_em=c.deletado_em,
    )


class DjangoClienteRepository:
    """Implementa `ClienteRepository` Protocol sobre Django ORM."""

    # Campos do Cliente que aceitam sobrescritas em mesclagem.
    CAMPOS_SOBRESCRITAVEIS = frozenset(
        {
            "nome",
            "nome_fantasia",
            "email",
            "telefone",
        }
    )

    def get_by_id(
        self, cliente_id: UUID, *, incluir_deletados: bool = False
    ) -> ClienteSnapshot | None:
        qs = Cliente.all_objects if incluir_deletados else Cliente.objects
        # Mesclar precisa enxergar perdedor mesmo se ja soft-deleted (regra ja
        # bloqueia em use case), mas aqui o get_by_id sem flag preserva
        # comportamento default (so ativos). Use case pede com incluir_deletados=False;
        # validacao de "perdedor_ja_deletado" verifica snapshot.deletado_em.
        try:
            obj = qs.get(id=cliente_id)
        except Cliente.DoesNotExist:
            # Tenta com all_objects pra capturar perdedor recem soft-deleted (caso raro)
            if not incluir_deletados:
                try:
                    obj = Cliente.all_objects.get(id=cliente_id)
                except Cliente.DoesNotExist:
                    return None
            else:
                return None
        return _to_snapshot(obj)

    def aplicar_sobrescritas(
        self, cliente_id: UUID, sobrescritas: dict[str, Any]
    ) -> ClienteSnapshot:
        invalidos = set(sobrescritas) - self.CAMPOS_SOBRESCRITAVEIS
        if invalidos:
            raise ValueError(
                f"Campos nao-sobrescritaveis: {sorted(invalidos)}. "
                f"Validos: {sorted(self.CAMPOS_SOBRESCRITAVEIS)}"
            )
        # update() em vez de save() pra evitar trigger post_save indesejado
        Cliente.objects.filter(id=cliente_id).update(**sobrescritas)
        obj = Cliente.objects.get(id=cliente_id)
        return _to_snapshot(obj)

    def soft_delete(
        self,
        cliente_id: UUID,
        *,
        motivo_categoria: str,
        usuario_id: UUID | None,
        agora: datetime,
    ) -> ClienteSnapshot:
        Cliente.all_objects.filter(id=cliente_id).update(
            deletado_em=agora,
            deletado_por_usuario_id=usuario_id,
            deletado_motivo_categoria=motivo_categoria,
        )
        obj = Cliente.all_objects.get(id=cliente_id)
        return _to_snapshot(obj)

    # =============================================================
    # US-CLI-003 — bulk_upsert (R3 + R8 tech-lead)
    # SERIALIZABLE isolation + advisory lock por tenant + sanitizacao CSV.
    # =============================================================

    # Campos do Cliente atualizaveis em update_conflicts (Django 5.0).
    BULK_UPDATE_FIELDS = (
        "nome",
        "nome_fantasia",
        "email",
        "telefone",
        "aceite_lgpd_em",
        "aceite_lgpd_versao",
        "aceite_lgpd_origem",
        "aceite_lgpd_dispensa_motivo",
        "aceite_lgpd_base_legal",
        "aceite_lgpd_evidencia_externa",
        "aceite_lgpd_pendente",
        "aceite_lgpd_ip_hash",
        "cpf_responsavel_legal",
    )

    def bulk_upsert(
        self,
        *,
        tenant_id: UUID,
        linhas: list[ClienteImportacaoInput],
        update_existing: bool,
        agora: datetime,
    ) -> ResultadoImportacao:
        """Insere/atualiza em lote dentro de uma transacao SERIALIZABLE (R3 tech-lead).

        Pré-condição: caller (view `importar_executar`) DEVE estar decorado
        com `@transaction.non_atomic_requests` — caso contrario Django
        ATOMIC_REQUESTS abre transacao com READ COMMITTED antes da view
        rodar e `SET TRANSACTION ISOLATION LEVEL` falha.

        Estrategia (SANEA-01 — auditoria 10 lentes corrigiu o D-01: ate entao
        o `transaction.atomic()` fechava logo apos o advisory lock e o
        trabalho rodava SEM transacao; "resolvido" era afirmacao falsa):
        1. `SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL
           SERIALIZABLE` antes de qualquer query (afeta apenas esta sessao
           pelo restante da operacao; reset no `finally`).
        2. `transaction.atomic()` envolve o advisory lock E todo o trabalho
           na MESMA transacao — qualquer erro faz rollback total e o lock
           (transaction-scoped) so e liberado no commit final.
        3. Advisory lock por tenant serializa importacoes simultaneas do
           mesmo tenant (vive ate o fim do trabalho, nao so do SELECT).
        4. Retry em SerializationFailure (max 3 tentativas, backoff 50/200/800ms).

        SERIALIZABLE + advisory lock + UNIQUE INDEX parcial elimina
        lost-update e phantom read.
        """
        if not linhas:
            return ResultadoImportacao(
                criados=0, atualizados=0, sem_mudanca=0, rejeitados=()
            )

        import time

        from psycopg import errors as pg_errors

        MAX_TENTATIVAS = 3
        for tentativa in range(MAX_TENTATIVAS):
            try:
                return self._bulk_upsert_serializable(
                    tenant_id=tenant_id,
                    linhas=linhas,
                    update_existing=update_existing,
                    agora=agora,
                )
            except pg_errors.SerializationFailure:
                if tentativa == MAX_TENTATIVAS - 1:
                    raise
                # Backoff exponencial: 50ms, 200ms, 800ms
                time.sleep(0.05 * (4 ** tentativa))
        # Inalcancavel — loop sempre retorna ou levanta.
        raise RuntimeError("bulk_upsert: estado inalcancavel apos retry")

    def _bulk_upsert_serializable(
        self,
        *,
        tenant_id: UUID,
        linhas: list[ClienteImportacaoInput],
        update_existing: bool,
        agora: datetime,
    ) -> ResultadoImportacao:
        """Executa o bulk_upsert numa transacao SERIALIZABLE — caminho real."""
        rejeitados: list[LinhaRejeitada] = []
        ids_criados: list[UUID] = []
        ids_atualizados: list[UUID] = []
        sem_mudanca = 0

        # SET SESSION CHARACTERISTICS afeta a proxima transacao iniciada
        # nesta conexao. Tem que rodar FORA de transacao ativa (eh comando
        # de configuracao da sessao). Reset depois pra READ COMMITTED.
        # Pre-condicao @transaction.non_atomic_requests garante que estamos
        # em autocommit antes desta linha.
        with connection.cursor() as cur:
            cur.execute(
                "SET SESSION CHARACTERISTICS AS TRANSACTION "
                "ISOLATION LEVEL SERIALIZABLE;"
            )

        try:
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute(
                        "SELECT pg_advisory_xact_lock(hashtext(%s));",
                        [f"importacao_clientes:{tenant_id}"],
                    )

                # SANEA-01 (auditoria 10 lentes — 01 D-01 / 02 SEG-D2 / 09 P1).
                # O advisory_xact_lock e TODO o trabalho de upsert tem que
                # viver na MESMA transacao. Antes o `with transaction.atomic()`
                # fechava logo apos o lock: como pg_advisory_xact_lock e
                # transaction-scoped, era liberado no commit e o upsert inteiro
                # rodava SEM lock e SEM atomicidade — duas importacoes
                # concorrentes do mesmo tenant nao eram serializadas apesar de
                # todo o aparato SERIALIZABLE+advisory lock. Indentado pra
                # dentro do atomic; o lock agora vive ate o commit final.

                # Detectar documentos de clientes soft-deleted (mesclados).
                # P1: 1 query agregada (era N+1 — uma query por linha dentro
                # da transacao SERIALIZABLE, segurando o lock por 1000
                # round-trips em import grande).
                chaves_lote = {(e.tipo_pessoa, e.documento) for e in linhas}
                tipos_lote = list({t for t, _ in chaves_lote})
                docs_lote = list({d for _, d in chaves_lote})
                soft_deletados = set(
                    Cliente.all_objects.filter(
                        tenant_id=tenant_id,
                        tipo_pessoa__in=tipos_lote,
                        documento__in=docs_lote,
                        deletado_em__isnull=False,
                    ).values_list("tipo_pessoa", "documento")
                )

                chaves_validas: list[ClienteImportacaoInput] = []
                for entrada in linhas:
                    if (entrada.tipo_pessoa, entrada.documento) in soft_deletados:
                        rejeitados.append(
                            LinhaRejeitada(
                                linha_numero=entrada.linha_numero,
                                linha_hash=entrada.linha_hash,
                                motivo="documento_pertence_a_cliente_mesclado",
                                motivo_descricao_curta=(
                                    "Documento pertence a cliente soft-deleted "
                                    "(mesclado em outro registro)."
                                ),
                            )
                        )
                        continue
                    chaves_validas.append(entrada)

                # Detecta linhas com update_existing=False + documento ja existe.
                existentes_map: dict[tuple[str, str], Cliente] = {}
                if chaves_validas:
                    pares = [(e.tipo_pessoa, e.documento) for e in chaves_validas]
                    tipos = list({p[0] for p in pares})
                    docs = [p[1] for p in pares]
                    qs = Cliente.objects.filter(
                        tenant_id=tenant_id,
                        tipo_pessoa__in=tipos,
                        documento__in=docs,
                    ).only(
                        "id", "tipo_pessoa", "documento", "nome", "nome_fantasia",
                        "email", "telefone",
                    )
                    for c in qs:
                        existentes_map[(c.tipo_pessoa, c.documento)] = c

                if not update_existing:
                    novas = []
                    for entrada in chaves_validas:
                        chave = (entrada.tipo_pessoa, entrada.documento)
                        if chave in existentes_map:
                            rejeitados.append(
                                LinhaRejeitada(
                                    linha_numero=entrada.linha_numero,
                                    linha_hash=entrada.linha_hash,
                                    motivo="ja_existe_no_tenant",
                                    motivo_descricao_curta=(
                                        "Documento ja cadastrado no tenant."
                                    ),
                                )
                            )
                        else:
                            novas.append(entrada)
                    chaves_validas = novas

                # UNIQUE INDEX parcial (WHERE deletado_em IS NULL) impede usar
                # bulk_create(update_conflicts=True) — postgres exige UNIQUE
                # constraint completa pra ON CONFLICT. Por isso fazemos um loop
                # explicito: existente -> compara + update; novo -> create.
                # Wave A: substituir por COPY temp + MERGE quando volume forcar
                # (alem de 1000 linhas precisa async).
                novos_por_chave: dict[tuple[str, str], Cliente] = {}
                for entrada in chaves_validas:
                    chave = (entrada.tipo_pessoa, entrada.documento)
                    nome_sanit = sanitizar_celula_csv(entrada.nome)
                    nome_fant_sanit = sanitizar_celula_csv(entrada.nome_fantasia)
                    email_sanit = sanitizar_celula_csv(entrada.email)
                    telefone_sanit = sanitizar_celula_csv(entrada.telefone)
                    if chave in existentes_map:
                        existente = existentes_map[chave]
                        igual = (
                            existente.nome == nome_sanit
                            and existente.nome_fantasia == nome_fant_sanit
                            and existente.email == email_sanit
                            and existente.telefone == telefone_sanit
                        )
                        if igual:
                            sem_mudanca += 1
                        else:
                            Cliente.objects.filter(id=existente.id).update(
                                nome=nome_sanit,
                                nome_fantasia=nome_fant_sanit,
                                email=email_sanit,
                                telefone=telefone_sanit,
                                aceite_lgpd_em=entrada.aceite_lgpd_em,
                                aceite_lgpd_versao=entrada.aceite_lgpd_versao,
                                aceite_lgpd_origem=entrada.aceite_lgpd_origem,
                                aceite_lgpd_dispensa_motivo=entrada.aceite_lgpd_dispensa_motivo,
                                aceite_lgpd_base_legal=entrada.aceite_lgpd_base_legal,
                                aceite_lgpd_evidencia_externa=entrada.aceite_lgpd_evidencia_externa,
                                aceite_lgpd_pendente=entrada.aceite_lgpd_pendente,
                                aceite_lgpd_ip_hash=entrada.aceite_lgpd_ip_hash,
                                cpf_responsavel_legal=entrada.cpf_responsavel_legal,
                            )
                            ids_atualizados.append(existente.id)
                    else:
                        novos_por_chave[chave] = Cliente(
                            tenant_id=tenant_id,
                            tipo_pessoa=entrada.tipo_pessoa,
                            documento=entrada.documento,
                            nome=nome_sanit,
                            nome_fantasia=nome_fant_sanit,
                            email=email_sanit,
                            telefone=telefone_sanit,
                            aceite_lgpd_em=entrada.aceite_lgpd_em,
                            aceite_lgpd_versao=entrada.aceite_lgpd_versao,
                            aceite_lgpd_origem=entrada.aceite_lgpd_origem,
                            aceite_lgpd_dispensa_motivo=entrada.aceite_lgpd_dispensa_motivo,
                            aceite_lgpd_base_legal=entrada.aceite_lgpd_base_legal,
                            aceite_lgpd_evidencia_externa=entrada.aceite_lgpd_evidencia_externa,
                            aceite_lgpd_pendente=entrada.aceite_lgpd_pendente,
                            aceite_lgpd_ip_hash=entrada.aceite_lgpd_ip_hash,
                            cpf_responsavel_legal=entrada.cpf_responsavel_legal,
                        )

                if novos_por_chave:
                    Cliente.objects.bulk_create(list(novos_por_chave.values()))
                    for novo in novos_por_chave.values():
                        ids_criados.append(novo.id)

                return ResultadoImportacao(
                    criados=len(ids_criados),
                    atualizados=len(ids_atualizados),
                    sem_mudanca=sem_mudanca,
                    rejeitados=tuple(rejeitados),
                    ids_criados=tuple(ids_criados),
                    ids_atualizados=tuple(ids_atualizados),
                )
        finally:
            # Reset isolation level pra READ COMMITTED — proximas operacoes
            # nesta conexao nao precisam de SERIALIZABLE.
            with connection.cursor() as cur:
                cur.execute(
                    "SET SESSION CHARACTERISTICS AS TRANSACTION "
                    "ISOLATION LEVEL READ COMMITTED;"
                )
