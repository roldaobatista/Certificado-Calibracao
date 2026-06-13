"""Enums do módulo `precificacao` (T-PRC-010 — US-PRC-001/004).

str-mixin → serialização JSON nativa (molde `configuracoes_sistema/enums.py`).
Refs: D-PRC-2/3/4/5.
"""

from __future__ import annotations

from enum import Enum


class ModoFormacaoPreco(str, Enum):
    """Modo de formação de preço de uma `RegraFormacaoPreco` (US-PRC-001 / D-PRC-5/6).

    PRECO_FIXO: preço final declarado diretamente na regra.
    MARGEM_ALVO: preço calculado a partir de custo manual + margem desejada.
    COST_PLUS: custo real via `CustoProvider` + margem alvo. Publicação BLOQUEADA
               sob stub (INV-PRC-COSTPLUS-STUB → 422 `CustoRealIndisponivel`).
    """

    PRECO_FIXO = "preco_fixo"
    MARGEM_ALVO = "margem_alvo"
    COST_PLUS = "cost_plus"


class OrigemCusto(str, Enum):
    """Origem do custo usado na formação de preço (D-PRC-5 / INV-PRC-CUSTO-EXPLICITO).

    CUSTO_MANUAL: `custo_manual_declarado` na própria regra (Wave A).
    PROVIDER_REAL: retornado pelo `CustoProvider` real (custeio-real N7).
    INDISPONIVEL: stub ativo sem custo manual — sinaliza ausência EXPLÍCITA de custo
                  (nunca silencioso como 0).
    """

    CUSTO_MANUAL = "custo_manual"
    PROVIDER_REAL = "provider_real"
    INDISPONIVEL = "indisponivel"


class Semaforo(str, Enum):
    """Semáforo de margem exposto ao vendedor (D-PRC-4 — server-side RBAC).

    VERDE: margem estimada >= margem alvo configurada.
    AMARELO: margem estimada entre piso e alvo (zona de atenção).
    VERMELHO: margem estimada < piso ou resultado negativo (prejuízo).
    INDISPONIVEL: custo ausente — semáforo não calculável (TL-PRC-05).
    """

    VERDE = "verde"
    AMARELO = "amarelo"
    VERMELHO = "vermelho"
    INDISPONIVEL = "indisponivel"


class Alcada(str, Enum):
    """Alçada de aprovação de desconto (D-PRC-3 — decisão Roldão: 10%/20%/dono).

    LIVRE: sem necessidade de aprovação (0..10% default).
    GERENTE: requer aprovação de gerente (10..20% default).
    DONO: requer aprovação do dono do negócio (>20% default + cortesia 100%).
    """

    LIVRE = "livre"
    GERENTE = "gerente"
    DONO = "dono"


class ContextoTipo(str, Enum):
    """Contexto de uso do pedido de aprovação (D-PRC-14 / TL-PRC-09).

    ORCAMENTO: pedido vinculado a um orçamento (consumidor #5).
    OS: pedido vinculado a uma ordem de serviço.
    AVULSO: cálculo sem contexto de documento (simulação / configuração).
    """

    ORCAMENTO = "orcamento"
    OS = "os"
    AVULSO = "avulso"


class EstadoPedido(str, Enum):
    """Estado de um `PedidoAprovacaoDesconto` (D-PRC-14 — WORM one-shot).

    SOLICITADO: pedido aberto aguardando decisão.
    APROVADO: desconto aprovado (terminal; one-shot via trigger).
    NEGADO: desconto negado (terminal; one-shot via trigger).
    """

    SOLICITADO = "solicitado"
    APROVADO = "aprovado"
    NEGADO = "negado"


class ModoMontagem(str, Enum):
    """Modo de montagem da cesta de itens (D-PRC-2 — decisão Roldão).

    COMPONENTES_CHECKLIST: deslocamento/hora-técnica/ART são itens do catálogo;
        `PerfilComposicaoPreco` declara componentes esperados; motor emite
        `componentes_faltantes` avaliando a CESTA inteira.
    FECHADO_COM_AVISO: 1 valor fechado; motor emite `aviso_composicao`
        configurável se perfil tiver `aviso_texto`.
    """

    COMPONENTES_CHECKLIST = "componentes_checklist"
    FECHADO_COM_AVISO = "fechado_com_aviso"
