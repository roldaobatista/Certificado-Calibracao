"""Enums do domínio Orçamentos — T-ORC-010.

Refs:
  D-ORC-3  — máquina de estados EstadoOrcamento (8 estados)
  D-ORC-16 — TipoAtividadeAlvo enum COMERCIAL → traduz para TipoAtividade da OS
  D-ORC-5  — VeredictoAnaliseCritica perfil-aware
  D-ORC-7  — CanalAprovacao

Zero imports Django / infrastructure.
"""

from __future__ import annotations

from enum import Enum


class EstadoOrcamento(str, Enum):
    """Máquina de estados do Orçamento (D-ORC-3).

    Transições válidas em `transicoes.TRANSICOES_VALIDAS`.
    `convertido` é terminal (INV-ORC-CONVERTIDO-TERMINAL).
    """

    RASCUNHO = "rascunho"
    ENVIADO = "enviado"
    APROVADO = "aprovado"
    APROVADO_PENDENTE_OS = "aprovado_pendente_os"
    CONVERTIDO = "convertido"
    RECUSADO = "recusado"
    EXPIRADO = "expirado"
    CANCELADO = "cancelado"

    @property
    def terminal(self) -> bool:
        """True se o estado não admite mais transições (INV-ORC-CONVERTIDO-TERMINAL)."""
        return self in {
            EstadoOrcamento.CONVERTIDO,
            EstadoOrcamento.RECUSADO,
            EstadoOrcamento.EXPIRADO,
            EstadoOrcamento.CANCELADO,
        }


class TipoAtividadeAlvo(str, Enum):
    """Tipo de atividade do ponto de vista COMERCIAL (D-ORC-16).

    NÃO tem ``outro`` — itens sem tipo_atividade_alvo são itens comerciais
    (deslocamento/taxa/outro) que viram ``ItemComercialOS`` na OS.

    Mapa fechado para ``TipoAtividade`` da OS em ``transicoes.traduzir_tipo_atividade_alvo``.
    """

    CALIBRACAO = "calibracao"
    MANUTENCAO = "manutencao"       # → TipoAtividade.MANUTENCAO_CORRETIVA (default D-ORC-16)
    INSTALACAO = "instalacao"
    VERIFICACAO = "verificacao"     # → TipoAtividade.VERIFICACAO_INMETRO
    VISTORIA = "vistoria"


class VeredictoAnaliseCritica(str, Enum):
    """Veredito da análise crítica cl. 7.1 ISO 17025 (D-ORC-5 / D-ORC-15).

    - ``aprovada``    — todos os itens de calibração cobertos (CMC + procedimento).
    - ``reprovada``   — fail-closed (perfil A ou indeterminado): não pode aprovar.
    - ``com_ressalva``— aprovado com ressalva registrada em Aprovacao WORM.
    - ``desabilitada``— perfil D (sem análise crítica); perfil C usa ``com_ressalva``
                        com ``severidade=baixa``.
    """

    APROVADA = "aprovada"
    REPROVADA = "reprovada"
    COM_RESSALVA = "com_ressalva"
    DESABILITADA = "desabilitada"


class CanalAprovacao(str, Enum):
    """Canal pelo qual a aprovação foi registrada (D-ORC-7).

    - ``interno``      — aprovador autenticado via API interna (funcionário do tenant).
    - ``link_publico`` — aprovador externo via token opaco (cliente final).
    """

    INTERNO = "interno"
    LINK_PUBLICO = "link_publico"


class SeveridadeRessalva(str, Enum):
    """Severidade de uma ressalva da análise crítica (D-ORC-5).

    - ``baixa`` — perfil C: log interno, sem confirmação do cliente.
    - ``media`` — perfil B/A padrão indisponível: ressalva apresentada e confirmada
                  pelo cliente (``ressalvas_confirmadas`` obrigatório no POST público).
    """

    BAIXA = "baixa"
    MEDIA = "media"
