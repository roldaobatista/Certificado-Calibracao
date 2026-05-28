"""Validador de complexidade de senha para conta break-glass (GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA).

Conserto segurança-BAIXO-1 da auditoria F-C1: `criar_admin_recovery` so
checava `len(senha) >= 14`. Conta break-glass tem privilegio MAXIMO
(is_superuser + bypass IP allowlist), entao a senha inicial precisa de
barreira de complexidade + dicionario, MAIS rigida que a politica geral
(INV-AUTH-002, que e Wave A).

Regras (mais rigidas que INV-AUTH-002 por ser break-glass):
- >=14 caracteres (mantem o piso historico do comando).
- AS 4 categorias presentes: minuscula, maiuscula, digito, simbolo.
- Nao conter (case-insensitive, sem acentos) o local-part do email nem
  tokens >=4 chars do nome (anti-senha-obvia).
- Nao ser padrao trivial: caractere unico repetido, sequencia
  alfabetica/numerica/teclado conhecida, ou termo de dicionario fraco.
- Entropia de Shannon estimada >= 50 bits (heuristica anti-padrao-curto).

Escopo: especifico de break-glass. O validador geral INV-AUTH-002
(`validar_politica_senha`) entra em Wave A — quando existir, este modulo
pode delegar a parte comum.
"""

from __future__ import annotations

import math
import unicodedata

_MIN_CHARS = 14
_MIN_ENTROPIA_BITS = 50.0

# Dicionario fraco minimo (anti-senha-obvia). Nao e um dicionario completo —
# severidade BAIXO. Cobre os padroes que aparecem em vazamentos reais.
_TERMOS_FRACOS = frozenset({
    "password", "senha", "admin", "root", "qwerty", "qwertz", "asdfgh",
    "123456", "1234567", "12345678", "123456789", "1234567890",
    "letmein", "welcome", "iloveyou", "monkey", "dragon", "master",
    "breakglass", "break-glass", "recovery", "afere", "balancas",
    "abc123", "password123", "senha123", "mudar123",
})

# Sequencias de teclado/alfabeto/numerica usadas pra detectar trivialidade.
_SEQUENCIAS = (
    "abcdefghijklmnopqrstuvwxyz",
    "01234567890",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
)


def _normalizar(texto: str) -> str:
    """Lower + remove acentos (NFKD) — comparacao case/acento-insensitive."""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _entropia_shannon_bits(senha: str) -> float:
    """Entropia de Shannon (bits) = comprimento * H, H em bits/char.

    Heuristica simples: penaliza senhas com poucos caracteres distintos
    (ex: 'aaaaaaaaaaaaaa' tem H~0 mesmo com 14 chars).
    """
    if not senha:
        return 0.0
    frequencias: dict[str, int] = {}
    for ch in senha:
        frequencias[ch] = frequencias.get(ch, 0) + 1
    n = len(senha)
    h = -sum((c / n) * math.log2(c / n) for c in frequencias.values())
    return h * n


def _tem_sequencia_trivial(senha_norm: str) -> bool:
    """True se a senha contem uma sub-sequencia >=4 de teclado/alfabeto/num."""
    for seq in _SEQUENCIAS:
        for i in range(len(seq) - 3):
            janela = seq[i : i + 4]
            if janela in senha_norm or janela[::-1] in senha_norm:
                return True
    return False


def validar_senha_breakglass(senha: str, *, email: str, nome: str) -> None:
    """Valida a senha inicial da conta break-glass. Levanta ValueError com
    motivo legivel se reprovar; retorna None se aprovar.

    GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA.
    """
    if len(senha) < _MIN_CHARS:
        raise ValueError(
            f"Senha break-glass precisa de >= {_MIN_CHARS} caracteres "
            f"(achou {len(senha)})."
        )

    tem_minuscula = any(c.islower() for c in senha)
    tem_maiuscula = any(c.isupper() for c in senha)
    tem_digito = any(c.isdigit() for c in senha)
    tem_simbolo = any(not c.isalnum() for c in senha)
    categorias = sum([tem_minuscula, tem_maiuscula, tem_digito, tem_simbolo])
    if categorias < 4:
        raise ValueError(
            "Senha break-glass exige as 4 categorias: minuscula, maiuscula, "
            "digito e simbolo (conta de privilegio maximo)."
        )

    senha_norm = _normalizar(senha)

    # Nao conter local-part do email nem tokens >=4 chars do nome.
    local_part = _normalizar(email.split("@", 1)[0])
    if len(local_part) >= 4 and local_part in senha_norm:
        raise ValueError(
            "Senha break-glass nao pode conter o email da conta."
        )
    for token in _normalizar(nome).split():
        if len(token) >= 4 and token in senha_norm:
            raise ValueError(
                "Senha break-glass nao pode conter parte do nome do titular."
            )

    # Dicionario fraco.
    for termo in _TERMOS_FRACOS:
        if termo in senha_norm:
            raise ValueError(
                f"Senha break-glass contem termo de dicionario fraco ('{termo}'). "
                "Use uma passphrase aleatoria (ex: gerador de senha)."
            )

    # Sequencias triviais (1234 / abcd / qwer / etc).
    if _tem_sequencia_trivial(senha_norm):
        raise ValueError(
            "Senha break-glass contem sequencia trivial (ex: 1234/abcd/qwer). "
            "Use caracteres aleatorios."
        )

    # Caractere unico dominante (ex: 'Aaaaaaaaaaaa1!').
    if _entropia_shannon_bits(senha) < _MIN_ENTROPIA_BITS:
        raise ValueError(
            f"Senha break-glass com entropia insuficiente "
            f"(< {_MIN_ENTROPIA_BITS:.0f} bits). Evite repeticao de poucos "
            "caracteres; prefira passphrase aleatoria longa."
        )
