"""Use cases de emissão de cobrança (Fatia 2b — T-CR-031).

`emitir_boleto` e `emitir_pix_recorrente` são as portas de emissão de cobrança:
chamam `PaymentGatewayProvider` e atualizam o título com os dados do gateway.

Clean arch: a camada APPLICATION não importa DRF. Cada erro de domínio levantado
aqui é traduzido para HTTP pela VIEW.

Regras (D-CR-7 / spec §3):
  - Carrega título pelo `(tenant_id, titulo_id)` — 404 se ausente.
  - Valida estado: só `emitido` ou `vencido` aceitam emissão de cobrança.
  - `pix_recorrente` exige `convenio_pix_id NOT NULL` → ConvenioPixAusente (422).
  - `GatewayIndisponivel` propaga para a view (→ 503 + evento `gateway_indisponivel`).
  - NÃO publica evento — a VIEW publica (clean arch: use case devolve resultado, view
    decide o que publicar e em qual transação).
  - Atualiza `gateway_externo_id` + `linha_digitavel`/`qr_code`/`tx_id` via `repo`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.erros import (
    ConvenioPixAusente,
    TituloNaoEncontrado,
    TransicaoProibida,
)
from src.domain.contas_receber.portas import PaymentGatewayProvider, TituloRepository
from src.domain.contas_receber.value_objects import CobrancaCriada, RecorrenciaCriada

# ---- Inputs ----------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class EmitirBoletoInput:
    """Payload de emissão de boleto (US-CR-002 / T-CR-031)."""

    tenant_id: UUID
    titulo_id: UUID
    vencimento_override: date | None = None  # se None, usa o data_vencimento do título


@dataclass(frozen=True, slots=True)
class EmitirBoletoOutput:
    """Resultado da emissão de boleto — título atualizado + dados de cobrança."""

    titulo: Titulo
    cobranca: CobrancaCriada


@dataclass(frozen=True, slots=True)
class EmitirPixRecorrenteInput:
    """Payload de emissão PIX recorrente (US-CR-002 / T-CR-031 / INV-FIN-GW-002)."""

    tenant_id: UUID
    titulo_id: UUID
    convenio_pix_id: str  # NOT NULL obrigatório; validado no use case


@dataclass(frozen=True, slots=True)
class EmitirPixRecorrenteOutput:
    """Resultado da emissão PIX recorrente — título atualizado + dados da recorrência."""

    titulo: Titulo
    recorrencia: RecorrenciaCriada


# ---- Use cases -------------------------------------------------------------

def emitir_boleto(
    inp: EmitirBoletoInput,
    *,
    repo: TituloRepository,
    provider: PaymentGatewayProvider,
) -> EmitirBoletoOutput:
    """Emite cobrança de boleto via `PaymentGatewayProvider`.

    Levanta:
      - `TituloNaoEncontrado` (→ 404) se título ausente/cross-tenant.
      - `TransicaoProibida` (→ 409) se título já pago/cancelado (estados terminais).
      - `GatewayIndisponivel` (→ 503) se provider falhar — propaga sem capturar.
    """
    titulo = repo.obter_por_id(tenant_id=inp.tenant_id, titulo_id=inp.titulo_id)
    if titulo is None:
        raise TituloNaoEncontrado(
            f"Título {inp.titulo_id} não encontrado para tenant {inp.tenant_id}."
        )

    if titulo.e_terminal:
        raise TransicaoProibida(
            f"Título {inp.titulo_id} em estado terminal ({titulo.estado.value}) — "
            "não é possível emitir cobrança."
        )

    vencimento = inp.vencimento_override or titulo.data_vencimento

    # Levanta GatewayIndisponivel se provider falhar (propaga para view → 503).
    cobranca = provider.criar_cobranca(
        titulo_id=inp.titulo_id,
        valor=titulo.valor_original,
        vencimento=vencimento,
        meio=titulo.meio.value,
    )

    # Atualiza título com dados do gateway (campos mutáveis — trigger WORM permite).
    from dataclasses import replace

    titulo_atualizado = replace(
        titulo,
        gateway_externo_id=cobranca.gateway_id,
        linha_digitavel=cobranca.linha_digitavel,
        qr_code=cobranca.qr_code,
        tx_id=cobranca.tx_id,
    )
    repo.atualizar_titulo(tenant_id=inp.tenant_id, titulo=titulo_atualizado)

    return EmitirBoletoOutput(titulo=titulo_atualizado, cobranca=cobranca)


def emitir_pix_recorrente(
    inp: EmitirPixRecorrenteInput,
    *,
    repo: TituloRepository,
    provider: PaymentGatewayProvider,
) -> EmitirPixRecorrenteOutput:
    """Emite convênio PIX recorrente via `PaymentGatewayProvider` (TL-CR-09).

    Wave A emite só o 1º título; geração dos subsequentes = Wave B.

    Levanta:
      - `TituloNaoEncontrado` (→ 404) se título ausente/cross-tenant.
      - `ConvenioPixAusente` (→ 422) se `convenio_pix_id` vazio (INV-FIN-GW-002).
      - `TransicaoProibida` (→ 409) se título em estado terminal.
      - `GatewayIndisponivel` (→ 503) se provider falhar — propaga sem capturar.
    """
    if not inp.convenio_pix_id or not inp.convenio_pix_id.strip():
        raise ConvenioPixAusente(
            "meio=pix_recorrente exige convenio_pix_id NOT NULL (INV-FIN-GW-002)."
        )

    titulo = repo.obter_por_id(tenant_id=inp.tenant_id, titulo_id=inp.titulo_id)
    if titulo is None:
        raise TituloNaoEncontrado(
            f"Título {inp.titulo_id} não encontrado para tenant {inp.tenant_id}."
        )

    if titulo.e_terminal:
        raise TransicaoProibida(
            f"Título {inp.titulo_id} em estado terminal ({titulo.estado.value}) — "
            "não é possível emitir recorrência."
        )

    # Levanta GatewayIndisponivel se provider falhar.
    recorrencia = provider.criar_recorrencia(
        titulo_id=inp.titulo_id,
        convenio_pix_id=inp.convenio_pix_id,
        valor=titulo.valor_original,
        primeiro_vencimento=titulo.data_vencimento,
    )

    from dataclasses import replace

    titulo_atualizado = replace(
        titulo,
        gateway_externo_id=recorrencia.gateway_id,
        convenio_pix_id=recorrencia.convenio_id,  # id de convênio retornado pelo gateway
        qr_code=None,  # recorrente não emite QR no 1º título (Wave A)
    )
    repo.atualizar_titulo(tenant_id=inp.tenant_id, titulo=titulo_atualizado)

    return EmitirPixRecorrenteOutput(titulo=titulo_atualizado, recorrencia=recorrencia)
