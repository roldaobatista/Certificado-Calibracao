"""Erros de domínio do caixa_tecnico (Fatia 1a — T-CT-015).

Cada erro carrega ``http_status`` — código HTTP que a camada de aplicação
usa ao mapear para resposta REST. Hierarquia molde ``contas_receber/erros.py``.

Refs: spec §4; plan §2; D-CT-3/4/5/6/7/8/11.
"""

from __future__ import annotations


class CaixaTecnicoDomainError(Exception):
    """Base do domínio caixa_tecnico (mapeada a 4xx pela aplicação)."""

    http_status: int = 422
    reason: str = "caixa_tecnico_erro"


# --- Foto-comprovante (412 / 409) ---


class FotoComprovanteObrigatoria(CaixaTecnicoDomainError):
    """Despesa lançada ou reapresentada sem ``foto_hash`` (INV-CT-FOTO-001 / D-CT-4).

    ``foto_hash`` é NOT NULL — sem foto = 412 FOTO_OBRIGATORIA.
    Levantada no ``Despesa.__post_init__`` (domínio puro) e no use case de
    lançamento antes de chamar o storage.
    """

    http_status = 412
    reason = "FOTO_OBRIGATORIA"


class DespesaValidadaImutavel(CaixaTecnicoDomainError):
    """Tentativa de mutar despesa no estado ``validada`` (INV-CT-IMUT-001 / D-CT-3).

    Despesa validada é WORM — trigger PG bloqueia UPDATE e DELETE.
    Correção = nova ``Despesa(tipo=estorno)`` referenciando a original.
    """

    http_status = 409
    reason = "DESPESA_VALIDADA_IMUTAVEL"


class FotoDuplicada(CaixaTecnicoDomainError):
    """Foto com mesmo ``foto_hash`` já existe para o tenant no estado ativo
    (INV-CT-FOTO-DEDUP-001 / D-CT-4).

    Constraint ``UNIQUE (tenant_id, foto_hash) WHERE status NOT IN ('rejeitada','cancelada')``.
    Fotos idênticas em tenants diferentes coexistem (constraint é por tenant).
    """

    http_status = 409
    reason = "FOTO_DUPLICADA"


# --- GPS / consentimento (403) ---


class GpsConsentimentoAusente(CaixaTecnicoDomainError):
    """Opt-in de GPS ausente ou revogado para o colaborador (INV-LGPD-CONSENT-001 / D-CT-6).

    NÃO bloqueia o lançamento da despesa — a despesa segue sem coordenadas.
    Aplicação retorna 403 no campo GPS mas continua o fluxo principal.
    """

    http_status = 403
    reason = "GPS_CONSENTIMENTO_AUSENTE"


# --- Adiantamento (422) ---


class AdiantamentoNaoCancelavel(CaixaTecnicoDomainError):
    """Tentativa de cancelar adiantamento no estado ``entregue`` (INV-CT-ADIAN-001 / D-CT-7).

    Entregue = irreversível. Acerto via prestação de contas ou devolução (Wave B).
    """

    http_status = 422
    reason = "ADIANTAMENTO_NAO_CANCELAVEL"


# --- Prestação de contas (422) ---


class PeriodoPrestacaoFechado(CaixaTecnicoDomainError):
    """Nova despesa ou adiantamento em período já encerrado por prestação (INV-CT-PRESTACAO-001 / D-CT-8).

    Após fechar a prestação, o período é bloqueado para novos lançamentos.
    """

    http_status = 422
    reason = "PERIODO_PRESTACAO_FECHADO"


# --- Máquina de estados (422) ---


class TransicaoInvalida(CaixaTecnicoDomainError):
    """Transição de estado proibida pela máquina (D-CT-3 / D-CT-7).

    Ex.: ``validada → rejeitada``, ``entregue → aprovado``, mover estado terminal.
    """

    http_status = 422
    reason = "TRANSICAO_INVALIDA"


# --- Batch / lote (413) ---


class LoteExcedido(CaixaTecnicoDomainError):
    """Lote de sync com mais de 20 itens (D-CT-5 / plan R7).

    ``POST /v1/caixa-tecnico/sync/despesas-lote`` valida ``len(itens) <= 20``.
    """

    http_status = 413
    reason = "LOTE_EXCEDIDO"


# --- Caixa desligado (409) ---


class CaixaTecnicoDesligado(CaixaTecnicoDomainError):
    """Lançamento ou solicitação em caixa de técnico desligado (D-CT-11 / consumer).

    ``CaixaTecnico.desligado_em`` preenchido pelo consumer ``colaborador.desligado``
    (fail-closed). Novos lançamentos bloqueados enquanto desligado.
    """

    http_status = 409
    reason = "CAIXA_TECNICO_DESLIGADO"
