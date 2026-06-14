"""Erros de domínio do módulo Orçamentos — T-ORC-013.

Cada erro carrega ``codigo`` (slug único) e ``http_status`` (para a camada
de infrastructure traduzir; o domínio não importa DRF nem Django).

Molde: ``ErroAbrirOS`` de ``src/application/operacao/os/abrir_os_via_orcamento.py``.

Refs:
  spec §4  — lista de erros
  D-ORC-3  — máquina de estados (TransicaoProibida / EstadoInvalido)
  D-ORC-4  — cliente bloqueado
  D-ORC-5  — análise crítica reprovada
  D-ORC-7  — token inválido / expirado
  D-ORC-14 — orçamento já convertido (terminal)
  D-ORC-19 — perfil indeterminado fail-closed

Zero imports Django / infrastructure.
"""

from __future__ import annotations


class ErroOrcamento(Exception):
    """Base dos erros de domínio de Orçamentos."""

    codigo: str = "erro_orcamento"
    http_status: int = 400

    def __init__(self, mensagem: str = "", **contexto: object) -> None:
        self.mensagem = mensagem or self.__class__.__doc__ or self.codigo
        self.contexto = contexto
        super().__init__(self.mensagem)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"codigo={self.codigo!r}, "
            f"http_status={self.http_status}, "
            f"mensagem={self.mensagem!r})"
        )


# =====================================================================
# 422 — Unprocessable Entity (regra de negócio impede a ação)
# =====================================================================


class ClienteBloqueado(ErroOrcamento):
    """Cliente está bloqueado ou inativo e não pode ser associado a orçamentos."""

    codigo = "cliente_bloqueado"
    http_status = 422


class TabelaPrecoExpirada(ErroOrcamento):
    """A tabela de preço referenciada expirou (ADR-0030 — JanelaVigencia).

    O item não pode ser adicionado sem uma tabela vigente.
    """

    codigo = "tabela_preco_expirada"
    http_status = 422


class AnaliseCriticaReprovada(ErroOrcamento):
    """Análise crítica cl. 7.1 reprovada — orçamento não pode ser aprovado.

    Perfil A (ou indeterminado) com item de calibração fora do escopo CMC
    ou sem procedimento vigente → fail-closed (D-ORC-5).
    """

    codigo = "analise_critica_reprovada"
    http_status = 422


class PerfilIndeterminado(ErroOrcamento):
    """Perfil regulatório do tenant não pôde ser determinado.

    Fail-closed: não é possível aprovar sem perfil conhecido (D-ORC-5 / D-ORC-19).
    """

    codigo = "perfil_indeterminado"
    http_status = 422


# =====================================================================
# 409 — Conflict (estado atual impede a transição)
# =====================================================================


class EstadoInvalido(ErroOrcamento):
    """O orçamento está em estado que não permite a operação solicitada."""

    codigo = "estado_invalido"
    http_status = 409


class TransicaoProibida(ErroOrcamento):
    """Transição de estado proibida pela máquina D-ORC-3.

    Exemplos:
      - aprovado → rascunho
      - convertido → qualquer estado
    """

    codigo = "transicao_proibida"
    http_status = 409


class OrcamentoConvertido(ErroOrcamento):
    """Orçamento já foi convertido em OS — estado terminal, sem volta.

    Qualquer tentativa de modificação resulta em 409 (INV-ORC-CONVERTIDO-TERMINAL).
    """

    codigo = "orcamento_convertido"
    http_status = 409


# =====================================================================
# 404 — Not Found / Gone
# =====================================================================


class TokenInvalidoOuExpirado(ErroOrcamento):
    """Token de aprovação pública inválido, inexistente ou expirado.

    404 (não 410/Gone) para não vazar informação sobre existência do link
    (ADV-ORC-08a / D-ORC-19 — pentest pré-tenant-pago).
    """

    codigo = "token_invalido_ou_expirado"
    http_status = 404
