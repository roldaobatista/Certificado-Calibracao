"""Enums fechados do domínio contas-receber (Fatia 1a — T-CR-010).

str-mixin → serialização JSON nativa (mesmo padrão de `fiscal/enums.py`).
Domínio NÃO importa Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class EstadoTitulo(str, Enum):
    """Estado do título a receber — máquina de estados (D-CR-3).

    Transições válidas (spec §4):
        emitido            → pago | parcialmente_pago | vencido | cancelado
        vencido            → pago | parcialmente_pago | cancelado
        parcialmente_pago  → pago | vencido | cancelado
        pago               → (terminal)
        cancelado          → (terminal)

    `cobranca_emitida` é DERIVADO de `gateway_externo_id NOT NULL` (não estado).
    `em_disputa` = Wave B.
    `cancelado` só sem pagamento parcial (D-CR-3 / `pode_cancelar`).
    """

    EMITIDO = "emitido"
    PAGO = "pago"
    PARCIALMENTE_PAGO = "parcialmente_pago"
    VENCIDO = "vencido"
    CANCELADO = "cancelado"


class MeioCobranca(str, Enum):
    """Canal de cobrança (D-CR-7 / US-CR-002).

    `pix_recorrente` exige `convenio_pix_id NOT NULL` (INV-FIN-GW-002).
    `cartao_recorrente` = Wave B.
    """

    BOLETO = "boleto"
    PIX = "pix"
    PIX_RECORRENTE = "pix_recorrente"
    CARTAO = "cartao"
    CARTAO_RECORRENTE = "cartao_recorrente"


class CategoriaReceita(str, Enum):
    """Categoria da receita — perfil-aware (D-CR-5 / INV-FIN-PERFIL-001).

    Predicate da matriz (spec §3.1 D-CR-5):
      - `CALIBRACAO_RBC` exige `perfil='A'` → mismatch = 403.
      - Derivação automática pelo `perfil_no_evento`:
          A  → CALIBRACAO_RBC
          B/C → CALIBRACAO_NAO_RBC
          D  → CALIBRACAO_BASICA
    """

    CALIBRACAO_RBC = "CALIBRACAO_RBC"
    CALIBRACAO_NAO_RBC = "CALIBRACAO_NAO_RBC"
    CALIBRACAO_BASICA = "CALIBRACAO_BASICA"
    MANUTENCAO_CORRETIVA = "MANUTENCAO_CORRETIVA"
    MANUTENCAO_PREVENTIVA = "MANUTENCAO_PREVENTIVA"
    PECA_REVENDA = "PECA_REVENDA"
    DESLOCAMENTO = "DESLOCAMENTO"
    OUTROS = "OUTROS"


class OrigemTitulo(str, Enum):
    """Fato gerador do título (D-CR-12).

    `os`       — OS concluída (gatilho canônico Wave A).
    `nfse`     — NF-e emitida (GATE-CR-NFSE, Wave B).
    `contrato` — recorrência por contrato (Wave B).
    `manual`   — lançamento manual pelo financeiro (piso garantido do núcleo).
    """

    OS = "os"
    NFSE = "nfse"
    CONTRATO = "contrato"
    MANUAL = "manual"


class OrigemPagamento(str, Enum):
    """Como o pagamento foi confirmado (D-CR-8 / US-CR-003).

    `webhook_gateway` — confirmado via webhook do gateway (HMAC idempotente).
    `manual`          — baixa manual pelo operador.
    `pix_direto`      — PIX Direto / Open Finance (Wave B).
    """

    WEBHOOK_GATEWAY = "webhook_gateway"
    MANUAL = "manual"
    PIX_DIRETO = "pix_direto"
