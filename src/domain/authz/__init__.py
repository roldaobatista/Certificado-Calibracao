"""Camada de domínio de autorização — porta + value object.

NÃO IMPORTAR DJANGO AQUI. Esta camada é a única que aplicações + adapters
diferentes podem reusar quando trocar de stack.
"""

from .provider import AuthDecision, AuthorizationProvider

__all__ = ["AuthDecision", "AuthorizationProvider"]
