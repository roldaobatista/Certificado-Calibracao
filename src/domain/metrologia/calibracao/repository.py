"""Repository Protocol para Calibracao — DOMINIO puro (ADR-0007).

Domain layer NAO importa django.* nem psycopg. Aqui mora apenas o
CONTRATO; a implementacao concreta (adapter Django) vai em
src/infrastructure/calibracao/repositories.py.

Use cases (src/application/metrologia/calibracao/) consomem este Protocol
e nunca conhecem Django/PG.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    CalibracaoSnapshot,
    ComponenteIncertezaSnapshot,
    EventoDeCalibracaoSnapshot,
    LeituraCorrecaoSnapshot,
    LeituraSnapshot,
    NaoConformidadeSnapshot,
    OrcamentoIncertezaSnapshot,
    OrcamentoPorPontoSnapshot,
    ReclamacaoCalibracaoSnapshot,
)
from .enums import EstadoNaoConformidade, EstadoReclamacao


@runtime_checkable
class CalibracaoRepository(Protocol):
    """Repository de Calibracao — read + write operations.

    Implementacao concreta: DjangoCalibracaoRepository
    (src/infrastructure/calibracao/repositories.py).

    Convencao:
    - Metodos `obter_*` retornam snapshot ou None (sem levantar excecao).
    - Metodos `salvar_*` inserem/atualizam via Django ORM com lock CAS
      (ADR-0065 — UPDATE ... WHERE revision = old_revision).
    - Snapshots sao imutaveis; mutacao = criar novo snapshot + chamar
      `salvar_*`.
    """

    def obter_por_id(self, calibracao_id: UUID) -> CalibracaoSnapshot | None:
        """Retorna snapshot da Calibracao se existir no tenant ativo (RLS)."""
        ...

    def proximo_numero_interno(self) -> int:
        """Reserva proximo numero da sequence global calibracao_numero_seq_global.

        Chama nextval() — consome o numero mesmo se transacao rollback
        (ADR-0056 — buracos por rollback sao aceitos por design para
        evitar serializacao single-row).
        """
        ...

    def salvar_nova(self, snapshot: CalibracaoSnapshot) -> None:
        """INSERT da Calibracao + trigger PG preenche numero_exibido.

        Levanta:
          - IntegrityError se tenant_id != app.active_tenant_id (RLS).
          - IntegrityError em violacao de UNIQUE constraint.
        """
        ...

    def atualizar_com_lock(
        self, snapshot: CalibracaoSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE com lock CAS (ADR-0065 — INV-CAL-CONC-001).

        UPDATE ... SET revision = revision + 1, ... WHERE id = %s
        AND revision = revision_anterior

        Retorna:
          True  - update aplicou (linhas afetadas == 1).
          False - update perdeu race (linhas afetadas == 0).

        Caller decide:
          - retry com obter_por_id + recomputar (default optimistic).
          - falhar com 409 Conflict (em endpoints POST sem idempotencia).
        """
        ...


@runtime_checkable
class LeituraRepository(Protocol):
    """Repository de Leituras (1:N de Calibracao).

    Imutaveis pos-INSERT — trigger PG bloqueia UPDATE/DELETE
    (INV-CAL-WORM-001). Por isso so ha `salvar_nova` + `obter_*`.
    Correcoes acontecem via LeituraCorrecao (rasura digital cl. 7.5).
    """

    def salvar_nova(self, snapshot: LeituraSnapshot) -> None:
        """INSERT da Leitura.

        Levanta:
          - IntegrityError em violacao da UNIQUE composta
            (tenant, calibracao, ponto, repeticao) — INV-CAL-CONC-001.
            Caller traduz para 409 Conflict (corrida ADR-0065).
          - IntegrityError em violacao da UNIQUE client_event_id (sync
            mobile ADR-0027) — caller trata como idempotencia (200/OK).
        """
        ...

    def obter_por_id(self, leitura_id: UUID) -> LeituraSnapshot | None:
        """Retorna snapshot da Leitura (RLS aplicado)."""
        ...

    def obter_por_client_event(
        self,
        tenant_id: UUID,
        calibracao_id: UUID,
        client_event_id: UUID,
    ) -> LeituraSnapshot | None:
        """Idempotencia sync mobile (ADR-0027): se client_event_id ja existe,
        retorna leitura existente em vez de levantar IntegrityError."""
        ...


@runtime_checkable
class LeituraCorrecaoRepository(Protocol):
    """Repository de rasuras digitais (cl. 7.5 — append-only WORM).

    Sem UPDATE/DELETE — trigger PG bloqueia mutacao.
    """

    def salvar_nova(self, snapshot: LeituraCorrecaoSnapshot) -> None:
        """INSERT da LeituraCorrecao.

        Levanta IntegrityError em violacoes de tenant/RLS — caller
        traduz pra 404/403.
        """
        ...

    def obter_por_id(self, correcao_id: UUID) -> LeituraCorrecaoSnapshot | None:
        ...

    def listar_por_leitura(self, leitura_id: UUID) -> list[LeituraCorrecaoSnapshot]:
        """Ordem: corrigido_em ASC (cronologia da rasura)."""
        ...


@runtime_checkable
class OrcamentoIncertezaRepository(Protocol):
    """Repository do orcamento de incerteza (1:1 ou 1:N de Calibracao —
    ha cenarios onde a Calibracao tem orcamento global + orcamento por
    ponto). Aqui cobrimos o orcamento global (snapshot agregado).

    Imutavel pos-EM_REVISAO_1 — trigger PG bloqueia mutacao.
    Persistencia atomica: orcamento + componentes em mesma transacao;
    caller envolve em transaction.atomic.
    """

    def salvar_orcamento_com_componentes(
        self,
        orcamento: OrcamentoIncertezaSnapshot,
        componentes: list[ComponenteIncertezaSnapshot],
        pontos: tuple[OrcamentoPorPontoSnapshot, ...] = (),
    ) -> None:
        """INSERT atomico do orcamento + N componentes (1:N) + N pontos (ADR-0077).

        `pontos` default `()` preserva as 3 chamadas legadas (path flat). No modo
        por-ponto persiste tambem os OrcamentoPorPonto na MESMA transacao atomica
        (caller envolve em transaction.atomic). No modo por-ponto, `componentes`
        carrega SO os Tipo B (decisao tech-lead opcao (a) — Tipo A vive na linha
        do ponto, preservando o CHECK ck_componente_tipo_a_n_min intacto).

        Levanta IntegrityError em violacoes (RLS / CHECK Tipo A n>=6 /
        FK self-correlacao circular).
        """
        ...

    def obter_por_id(
        self, orcamento_id: UUID
    ) -> OrcamentoIncertezaSnapshot | None:
        ...

    def listar_componentes(
        self, orcamento_id: UUID
    ) -> list[ComponenteIncertezaSnapshot]:
        ...


@runtime_checkable
class NaoConformidadeRepository(Protocol):
    """Repository de Nao-Conformidade (cl. 7.10 + cl. 8.7 CAPA).

    Use cases consomem este Protocol; adapter Django concreto vive em
    src/infrastructure/calibracao/repositories.py.

    Convencao:
    - Metodos `obter_*` retornam snapshot ou None (sem levantar excecao).
    - `salvar_novo` insere em estado inicial (CONTIDA).
    - `transitar_estado` faz UPDATE atomico WHERE estado=esperado;
      rowcount=0 -> estado mudou concorrentemente (caller decide 409).
    """

    def obter_por_id(self, nc_id: UUID) -> NaoConformidadeSnapshot | None:
        """Retorna snapshot da NC se existir no tenant ativo (RLS aplicado)."""
        ...

    def salvar_novo(self, snapshot: NaoConformidadeSnapshot) -> None:
        """INSERT em estado CONTIDA.

        Levanta IntegrityError em violacao XOR origem (CHECK migration 0002)
        ou em violacao de tenant RLS.
        """
        ...

    def transitar_estado(
        self,
        snapshot: NaoConformidadeSnapshot,
        estado_anterior: EstadoNaoConformidade,
    ) -> bool:
        """UPDATE atomico com guard de estado.

        UPDATE nao_conformidade
          SET <campos do snapshot> ...
          WHERE id = %s AND estado = estado_anterior.value

        Retorna:
          True  - update aplicou (linhas afetadas == 1).
          False - estado mudou concorrentemente OU id nao existe.
        """
        ...


@runtime_checkable
class EventoDeCalibracaoRepository(Protocol):
    """Repository de EventoDeCalibracao — trilha WORM hash-chain (OBS-CAL-01).

    Cobre OBS-CAL-01 (ALTO) 1a passada Familia 5: tabela `evento_de_calibracao`
    declarada em migration 0009 mas nunca emitida pelos 16 use cases M4.

    Convencao:
    - `salvar_em_cadeia` faz advisory lock (`pg_advisory_xact_lock`) por
      `(tenant_id, calibracao_id)` ADR-0065, SELECT MAX(sequencia_local) +1,
      calcula `evento_hash` HMAC versionado ADR-0064 e INSERT — TUDO dentro
      do atomic do CALLER (use case envolvedor mantem rollback unificado).
    - `obter_ultimo_hash` retorna hash do ultimo elo (string vazia = sem
      eventos ainda). Usado por validador de cadeia (replay determinístico).
    """

    def salvar_em_cadeia(
        self, snapshot: EventoDeCalibracaoSnapshot
    ) -> EventoDeCalibracaoSnapshot:
        """Append-only WORM dentro de advisory lock por calibracao.

        Caller passa snapshot com `sequencia_local=None`, `evento_anterior_hash=""`,
        `evento_hash=""` — adapter preenche os 3 dentro do lock e retorna
        snapshot final encadeado. Levanta IntegrityError em violacao RLS
        ou UPDATE/DELETE (trigger PG bloqueia).
        """
        ...

    def obter_ultimo_hash(
        self, *, tenant_id: UUID, calibracao_id: UUID
    ) -> str:
        """Retorna hash do ultimo elo encadeado da calibracao.

        Returns:
          String vazia se nao ha eventos ainda; senao evento_hash do
          ultimo elo (ordem por sequencia_local DESC).
        """
        ...


@runtime_checkable
class ReclamacaoCalibracaoRepository(Protocol):
    """Repository de ReclamacaoCalibracao (US-CAL-018 + cl. 7.9 + CDC art. 26).

    Estado-maquina: RECEBIDA -> EM_ANALISE -> RESPONDIDA / ARQUIVADA.

    Convencao:
    - `obter_*` retorna snapshot ou None.
    - `salvar_nova` insere em RECEBIDA.
    - `transitar_estado` UPDATE atomico WHERE estado=esperado.
    """

    def obter_por_id(
        self, reclamacao_id: UUID
    ) -> ReclamacaoCalibracaoSnapshot | None:
        ...

    def salvar_nova(self, snapshot: ReclamacaoCalibracaoSnapshot) -> None:
        """INSERT em estado RECEBIDA. Levanta IntegrityError em violacao RLS."""
        ...

    def transitar_estado(
        self,
        snapshot: ReclamacaoCalibracaoSnapshot,
        estado_anterior: EstadoReclamacao,
    ) -> bool:
        """UPDATE atomico com guard de estado. Retorna False se mudou concorrentemente."""
        ...
