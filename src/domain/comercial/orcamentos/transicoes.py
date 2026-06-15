"""Máquina de estados, tradução de enums e montagem de envelope — T-ORC-014.

Arquivo MAIS IMPORTANTE da Fatia 1a:

1. ``TRANSICOES_VALIDAS`` — grafo D-ORC-3 (máquina de estados do orçamento).
2. ``pode_transicionar`` / ``validar_transicao`` — consulta + enforcement.
3. ``traduzir_tipo_atividade_alvo`` — mapa fechado D-ORC-16 (enum comercial → enum OS).
4. ``montar_envelope_orcamento_aprovado`` — função PURA que produz o dict do
   payload ``orcamento.aprovado`` consumido por ``handle_orcamento_aprovado``
   (``src/infrastructure/ordens_servico/consumers/orcamento.py:_parse_input``).

Refs:
  D-ORC-3  — máquina de estados (transições válidas e proibidas)
  D-ORC-6  — envelope exato ``Orcamento.Aprovado`` (equipamento POR ITEM)
  D-ORC-11 — rastro item↔atividade por ``sequencia`` (Wave A)
  D-ORC-16 — tabela de tradução TipoAtividadeAlvo → TipoAtividade
  INV-ORC-CONVERTIDO-TERMINAL — convertido não transiciona
  INV-ORC-APROVADO-ENVELOPE   — envelope testado por contrato
  INV-ORC-EQUIP-ITEM          — item calibração tem equipamento; comercial não

Zero imports Django / infrastructure.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.domain.comercial.orcamentos.entities import (
    AnaliseCriticaOrcamento,
    ItemOrcamento,
    Orcamento,
)
from src.domain.comercial.orcamentos.enums import (
    EstadoOrcamento,
    TipoAtividadeAlvo,
)
from src.domain.comercial.orcamentos.erros import TransicaoProibida
from src.domain.operacao.os.value_objects import TipoAtividade
from src.domain.shared.value_objects import Dinheiro


def _dinheiro_str(d: Dinheiro) -> str:
    """``Dinheiro`` (centavos) → string decimal ``"300.00"`` (formato do envelope).

    O consumer da OS faz ``Decimal(str(valor))`` — esta string precisa ser
    decimal pura (sem prefixo de moeda; ``Dinheiro.__str__`` usa "BRL 300,00").
    """
    sinal = "-" if d.centavos < 0 else ""
    c = abs(d.centavos)
    return f"{sinal}{c // 100}.{c % 100:02d}"


# =====================================================================
# CONSTANTE DE RESSALVA (D-ORC-5 / consultor-rbc C4)
# =====================================================================

TEXTO_RESSALVA_PADRAO_INDISPONIVEL: str = (
    "Padrão de referência não verificado automaticamente para grandeza/faixa deste item. "
    "O RT deve confirmar disponibilidade do padrão de referência antes de agendar a "
    "calibração, conforme ISO/IEC 17025:2017 cl. 7.1.1-b."
)
"""Texto verbatim da ressalva de padrão indisponível (D-ORC-5 / consultor-rbc C4).

Registrada APENAS em perfil A (com_ressalva severidade=media).
Perfis B/C/D não geram esta ressalva.
Campos da ressalva: severidade='media', acao_obrigatoria='confirmacao_rt_antes_agendamento'.
"""

# =====================================================================
# MÁQUINA DE ESTADOS — D-ORC-3
# =====================================================================

TRANSICOES_VALIDAS: dict[EstadoOrcamento, frozenset[EstadoOrcamento]] = {
    # rascunho → pode ser enviado ou cancelado diretamente
    EstadoOrcamento.RASCUNHO: frozenset(
        {
            EstadoOrcamento.ENVIADO,
            EstadoOrcamento.CANCELADO,
        }
    ),
    # enviado → aguarda resposta do cliente
    EstadoOrcamento.ENVIADO: frozenset(
        {
            EstadoOrcamento.APROVADO,
            EstadoOrcamento.RECUSADO,
            EstadoOrcamento.EXPIRADO,
        }
    ),
    # aprovado → entra em estado de pendência de abertura de OS
    # (publicação do evento orcamento.aprovado — D-ORC-6)
    EstadoOrcamento.APROVADO: frozenset(
        {
            EstadoOrcamento.APROVADO_PENDENTE_OS,
        }
    ),
    # aprovado_pendente_os → convertido ao confirmar abertura da OS
    # (consumer handle_os_aberta fecha a saga — D-ORC-14)
    EstadoOrcamento.APROVADO_PENDENTE_OS: frozenset(
        {
            EstadoOrcamento.CONVERTIDO,
        }
    ),
    # Estados terminais — nenhuma transição válida (INV-ORC-CONVERTIDO-TERMINAL)
    EstadoOrcamento.CONVERTIDO: frozenset(),
    EstadoOrcamento.RECUSADO: frozenset(),
    EstadoOrcamento.EXPIRADO: frozenset(),
    EstadoOrcamento.CANCELADO: frozenset(),
}
"""Grafo de transições do orçamento (D-ORC-3).

Transições PROIBIDAS explícitas (exemplos):
  - aprovado → rascunho       (não reedita após aprovação)
  - convertido → qualquer     (INV-ORC-CONVERTIDO-TERMINAL)
  - recusado → enviado        (sem reabertura; criar novo orçamento)
"""


def pode_transicionar(de: EstadoOrcamento, para: EstadoOrcamento) -> bool:
    """Retorna True se a transição ``de`` → ``para`` é válida (D-ORC-3)."""
    return para in TRANSICOES_VALIDAS.get(de, frozenset())


def validar_transicao(de: EstadoOrcamento, para: EstadoOrcamento) -> None:
    """Levanta ``TransicaoProibida`` se a transição for inválida (D-ORC-3).

    Use case chama antes de persistir novo estado.
    """
    if not pode_transicionar(de, para):
        raise TransicaoProibida(
            f"Transição proibida: {de.value!r} → {para.value!r} (D-ORC-3).",
            estado_atual=de.value,
            estado_alvo=para.value,
        )


# =====================================================================
# TRADUÇÃO DE ENUM — D-ORC-16
# =====================================================================

_MAPA_TIPO_ATIVIDADE: dict[TipoAtividadeAlvo, TipoAtividade] = {
    TipoAtividadeAlvo.CALIBRACAO: TipoAtividade.CALIBRACAO,
    TipoAtividadeAlvo.MANUTENCAO: TipoAtividade.MANUTENCAO_CORRETIVA,  # default D-ORC-16
    TipoAtividadeAlvo.INSTALACAO: TipoAtividade.INSTALACAO,
    TipoAtividadeAlvo.VERIFICACAO: TipoAtividade.VERIFICACAO_INMETRO,
    TipoAtividadeAlvo.VISTORIA: TipoAtividade.VISTORIA,
}
"""Mapa fechado D-ORC-16: enum comercial → enum da OS.

Não adicionar entradas sem ADR.
manutencao → MANUTENCAO_CORRETIVA (padrão; PREVENTIVA é agenda interna).
NÃO existe TipoAtividadeAlvo.OUTRO — itens comerciais não têm tipo_atividade_alvo.
"""


def traduzir_tipo_atividade_alvo(alvo: TipoAtividadeAlvo) -> TipoAtividade:
    """Traduz enum comercial para enum da OS (mapa fechado D-ORC-16).

    Levanta ``KeyError`` se o enum não estiver mapeado (não deve ocorrer —
    mapa cobre todos os valores de ``TipoAtividadeAlvo``).
    """
    try:
        return _MAPA_TIPO_ATIVIDADE[alvo]
    except KeyError as exc:
        raise KeyError(
            f"TipoAtividadeAlvo {alvo!r} sem mapeamento em _MAPA_TIPO_ATIVIDADE (D-ORC-16). "
            "Adicionar sem ADR é proibido (INV-OS-ATIV-003)."
        ) from exc


# =====================================================================
# ENVELOPE orcamento.aprovado — D-ORC-6 / INV-ORC-APROVADO-ENVELOPE
# =====================================================================

# PLACEHOLDER — GATE-ORC-ITEMCOMERCIAL-DESCRICAO
#
# Itens comerciais (equipamento_id=None) viram ItemComercialOS na OS com
# tipo=TipoItemComercial.OUTRO. Em Wave A o campo ``tipo`` do item no envelope
# usa "vistoria" como placeholder para não quebrar o parser da OS
# (``_parse_input`` espera um valor de TipoAtividade válido; esses itens
# são detectados pela AUSÊNCIA de equipamento_id, não pelo tipo).
#
# O campo ``descricao`` é ADITIVO (a OS ignora hoje — Wave A). Quando
# GATE-ORC-ITEMCOMERCIAL-DESCRICAO for implementado, a OS lerá esse campo
# para preencher ``descricao_publica`` do ItemComercialOS (TL-ORC MÉDIO-2).
_PLACEHOLDER_TIPO_ITEM_COMERCIAL = "vistoria"


def montar_envelope_orcamento_aprovado(
    *,
    orcamento: Orcamento,
    itens: list[ItemOrcamento],
    analise_critica: AnaliseCriticaOrcamento | None,
    regra_decisao_acordada: str = "",
    abertura_at: datetime | None = None,
    criada_por_user_id: UUID | None = None,
) -> dict[str, Any]:
    """Monta o payload ``orcamento.aprovado`` para publicação no bus (D-ORC-6).

    Função PURA: recebe snapshots já persistidos e devolve dict.
    Sem side effects, testável isoladamente (INV-ORC-APROVADO-ENVELOPE).

    O dict retornado é o ``payload`` que ``publicar_evento`` (audit.event_helpers)
    persiste no outbox. O consumer ``handle_orcamento_aprovado``
    (``infrastructure/ordens_servico/consumers/orcamento.py``) lê via ``_parse_input``.

    Estrutura gerada:
    ─────────────────
    {
      "orcamento_id": str,
      "tenant_id": str,
      "cliente_id": str | None,        ← cliente_atual_id (pode ser None se anonimizado)
      "cliente_referencia_hash": str,
      "cliente_key_id": str,
      "equipamento_id": None,          ← header legado v1; orçamento v2 NÃO usa (D-ORC-6)
      "equipamento_recebimento_id": None,  ← Wave A = None (GATE futuro)
      "analise_critica_id": str | None,
      "analise_critica_snapshot_hash": str,
      "regra_decisao_acordada": str,
      "valor_total": str,              ← Decimal como str (evita float)
      "abertura_at": str,              ← ISO 8601 UTC
      "criada_por_user_id": str | None,
      "itens": [
        # Item técnico (equipamento_id preenchido) → vira AtividadeDaOS:
        {
          "tipo": str,                 ← TipoAtividade.value traduzido (D-ORC-16)
          "sequencia": int,
          "valor_unitario": str,       ← Decimal como str
          "requer_recebimento": bool,
          "equipamento_id": str,       ← UUID como str
        },
        # Item comercial (equipamento_id=None) → vira ItemComercialOS (tipo=OUTRO):
        {
          "tipo": "vistoria",          ← PLACEHOLDER (ver GATE-ORC-ITEMCOMERCIAL-DESCRICAO)
          "sequencia": int,
          "valor_unitario": str,
          "requer_recebimento": false,
          "equipamento_id": None,
          "descricao": str,            ← ADITIVO (OS ignora hoje; Wave A)
        },
      ]
    }

    Args:
        orcamento: agregado raiz (fonte dos campos de header).
        itens: lista de ``ItemOrcamento`` da versão ativa (em ordem de ``sequencia``).
        analise_critica: se houver; None para perfil D ou sem calibração.
        regra_decisao_acordada: string livre (ref. ISO 17025 cl. 7.8.6; pode ser "").
        abertura_at: momento de publicação; usa ``datetime.now(UTC)`` se omitido.
        criada_por_user_id: user_id do aprovador interno; None para aprovação pública.

    Returns:
        dict pronto para ``publicar_evento(acao="orcamento.aprovado", payload=<retorno>)``.
    """
    agora = abertura_at or datetime.now(UTC)

    itens_payload: list[dict[str, Any]] = []
    for item in itens:
        valor_unitario = _dinheiro_str(item.preco_final)

        if item.equipamento_id is not None:
            # Item técnico — vira AtividadeDaOS na OS (D-ORC-6 / INV-ORC-EQUIP-ITEM)
            tipo_atividade = traduzir_tipo_atividade_alvo(
                item.tipo_atividade_alvo  # type: ignore[arg-type]
                # Garantido não-None pela validação do ItemOrcamento.__post_init__
            )
            itens_payload.append(
                {
                    "tipo": tipo_atividade.value,
                    "sequencia": item.sequencia,
                    "valor_unitario": valor_unitario,
                    "requer_recebimento": False,  # Wave A; GATE-OS-BANCADA controla
                    "equipamento_id": str(item.equipamento_id),
                }
            )
        else:
            # Item comercial — vira ItemComercialOS (tipo=OUTRO) na OS (D-ORC-6)
            # PLACEHOLDER: "tipo" usa "vistoria" porque _parse_input espera TipoAtividade válido.
            # A ausência de equipamento_id é que determina ItemComercialOS (D-OSME-3).
            # O campo "descricao" é ADITIVO — OS ignora hoje (GATE-ORC-ITEMCOMERCIAL-DESCRICAO).
            itens_payload.append(
                {
                    "tipo": _PLACEHOLDER_TIPO_ITEM_COMERCIAL,
                    "sequencia": item.sequencia,
                    "valor_unitario": valor_unitario,
                    "requer_recebimento": False,
                    "equipamento_id": None,
                    "descricao": item.descricao_snapshot,  # campo aditivo Wave A
                }
            )

    payload: dict[str, Any] = {
        # Header
        "orcamento_id": str(orcamento.id),
        "tenant_id": str(orcamento.tenant_id),
        "cliente_id": str(orcamento.cliente_atual_id) if orcamento.cliente_atual_id else None,
        "cliente_referencia_hash": orcamento.cliente_referencia_hash,
        "cliente_key_id": orcamento.cliente_key_id,
        # Legado v1: header equipamento_id = None em orçamentos v2 (D-ORC-6)
        "equipamento_id": None,
        # Recebimento = Wave A None (GATE futuro)
        "equipamento_recebimento_id": None,
        # Análise crítica
        "analise_critica_id": str(analise_critica.id) if analise_critica else None,
        "analise_critica_snapshot_hash": (analise_critica.snapshot_hash if analise_critica else ""),
        "regra_decisao_acordada": regra_decisao_acordada,
        # Valor total como str decimal (Dinheiro VO — evita float no JSON)
        "valor_total": _dinheiro_str(orcamento.liquido),
        # Timestamp ISO 8601 UTC
        "abertura_at": agora.isoformat(),
        # Aprovador (None para aprovação pública — D-ORC-7)
        "criada_por_user_id": str(criada_por_user_id) if criada_por_user_id else None,
        # Itens (equipamento POR ITEM — ADR-0082 / D-ORC-6)
        "itens": itens_payload,
    }

    return payload
