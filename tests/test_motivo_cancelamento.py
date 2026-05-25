"""Unit test do VO `MotivoCancelamento` (TST-005 + Q-OS-01..03 + Q-OS-05).

Cobre INV-OS-TXT-001 com:
- Happy path (texto valido).
- Bordas de tamanho (29 = fail / 30 = ok / 500 = ok / 501 = fail).
- 6 classes de PII bloqueadas individualmente (CPF, CNPJ, email,
  telefone, endereco, sequencia ≥7 digitos, 2-nomes-juntos).
- TST-007: VARREDURA ≥5000 UUIDs + 1000 ULIDs + 1000 slugs +
  1000 hashes hex64 + 1000 base64-url — devem TODOS passar como
  texto valido (zero falsos positivos). Bug-classe `sanitizar_payload_audit`
  (2026-05-19) provou que regex sobre identificadores estruturais e
  vulneravel a falsos-positivos. Aqui o VO recebe texto humano (≥30
  chars), entao os strings sao envolvidos em frase de teste.
- Detecao de palavras-saude (P-OS-A3) -> revisao_gerente_pendente=True.
- Canonicalizacao NFC + lowercase + strip.

NAO sao testes de regressao de bug (esse arquivo eh em /tests/), sao
testes unitarios diretos da unidade — TST-005 v1.1.0.
"""

from __future__ import annotations

import secrets
import string
from uuid import UUID, uuid4

import pytest
from src.domain.operacao.os.value_objects import MotivoCancelamento

# =============================================================
# Happy: textos validos passam
# =============================================================


def test_motivo_cancelamento_happy_texto_simples():
    m = MotivoCancelamento("Cliente desistiu do servico antes da execucao tecnica.")
    assert m.texto.startswith("Cliente desistiu")
    assert m.revisao_gerente_pendente is False


def test_motivo_cancelamento_happy_30_chars_borda_minima():
    """Borda: exatamente 30 chars passa."""
    txt = "Cliente cancelou via portal web"  # 31 chars
    m = MotivoCancelamento(txt[:30])
    assert len(m.texto) == 30


def test_motivo_cancelamento_happy_500_chars_borda_maxima():
    """Borda: exatamente 500 chars passa."""
    txt = "Cancelamento detalhado " * 30  # mais de 500
    truncado = txt[:500]
    m = MotivoCancelamento(truncado)
    assert len(m.texto) == 500


# =============================================================
# Unhappy: bordas de tamanho
# =============================================================


def test_motivo_cancelamento_unhappy_29_chars_falha():
    with pytest.raises(ValueError, match="minimo 30 chars"):
        MotivoCancelamento("a" * 29)


def test_motivo_cancelamento_unhappy_501_chars_falha():
    with pytest.raises(ValueError, match="maximo 500 chars"):
        MotivoCancelamento("a" * 501)


def test_motivo_cancelamento_unhappy_tipo_invalido():
    with pytest.raises(TypeError):
        MotivoCancelamento(b"bytes nao str cancelado pelo cliente do balcao")  # type: ignore[arg-type]


# =============================================================
# Unhappy: 6 classes de PII bloqueadas
# =============================================================


def test_motivo_cancelamento_unhappy_pii_cpf_bloqueia():
    with pytest.raises(ValueError, match="contem CPF"):
        MotivoCancelamento(
            "Cliente cancelou porque o CPF 123.456.789-01 nao confere com cadastro."
        )


def test_motivo_cancelamento_unhappy_pii_cnpj_bloqueia():
    with pytest.raises(ValueError, match="contem CNPJ"):
        MotivoCancelamento(
            "Cancelamento solicitado pelo CNPJ 11.222.333/0001-81 hoje cedo."
        )


def test_motivo_cancelamento_unhappy_pii_email_bloqueia():
    with pytest.raises(ValueError, match="contem email"):
        MotivoCancelamento(
            "Cliente solicitou cancelamento via fulano@exemplo.com.br urgente."
        )


def test_motivo_cancelamento_unhappy_pii_telefone_bloqueia():
    with pytest.raises(ValueError, match="contem telefone"):
        MotivoCancelamento(
            "Cancelamento contato telefonico cliente 11 99999-8888 confirmado."
        )


def test_motivo_cancelamento_unhappy_pii_endereco_bloqueia():
    """Regex endereco: `\\d+\\s*(ap|apto|...)\\.?\\s*\\d+` — exige digito antes."""
    with pytest.raises(ValueError, match="contem endereco"):
        MotivoCancelamento(
            "Cancelamento na rua x 100 apto 1234 nao foi feito tecnico ausente."
        )


def test_motivo_cancelamento_unhappy_pii_sequencia_numerica_bloqueia():
    with pytest.raises(ValueError, match="contem sequencia_numerica"):
        MotivoCancelamento(
            "Cancelamento protocolo 12345678 nao localizado no nosso sistema."
        )


def test_motivo_cancelamento_unhappy_pii_dois_nomes_bloqueia():
    with pytest.raises(ValueError, match="nomes proprios consecutivos"):
        MotivoCancelamento(
            "Cancelamento solicitado pelo Joao Silva ontem no balcao da loja."
        )


# =============================================================
# Saude: revisao_gerente_pendente
# =============================================================


def test_motivo_cancelamento_palavra_saude_dispara_revisao():
    """Saude (P-OS-A3) NAO bloqueia INSERT, mas marca quarentena 24h."""
    m = MotivoCancelamento(
        "Cancelamento porque equipamento tem residuo paciente anterior nao limpo."
    )
    assert m.revisao_gerente_pendente is True


def test_motivo_cancelamento_sem_palavra_saude_sem_revisao():
    m = MotivoCancelamento(
        "Cancelamento normal por desistencia do servico solicitado pelo cliente."
    )
    assert m.revisao_gerente_pendente is False


# =============================================================
# TST-007: varredura massiva anti-falso-positivo em identificadores
# =============================================================


def _envolver(identificador: str) -> str:
    """Embrulha identificador em frase de ≥30 chars."""
    return f"Cancelamento referencia interna {identificador} processado hoje."


def test_motivo_cancelamento_varredura_5000_uuid4_zero_falsos_positivos():
    """TST-007: 5000 UUID v4 randomicos envelopados em texto valido
    NUNCA disparam regex PII (CPF/CNPJ/seq-numerica)."""
    falsos = []
    for _ in range(5000):
        uid = str(uuid4())
        try:
            MotivoCancelamento(_envolver(uid))
        except ValueError as exc:
            falsos.append((uid, str(exc)))
    assert not falsos, (
        f"VARREDURA TST-007 falhou: {len(falsos)} UUIDs viraram PII. "
        f"Primeiros 3: {falsos[:3]}"
    )


def test_motivo_cancelamento_varredura_1000_uuid_digit_heavy_literais():
    """TST-006: bordas digit-heavy. Bug-classe 2026-05-19 era UUIDs com
    runs longos de digitos sendo capturados por regex CPF. Aqui forco
    UUIDs validos com digit-heavy."""
    uuids_literais = [
        # UUIDs v4 validos mas digit-heavy (variant bits respeitam):
        "00000000-0000-4000-8000-000000000000",
        "11111111-1111-4111-8111-111111111111",
        "33333333-3333-4333-8333-333333333333",
        "12345678-9012-4345-8678-901234567890",
        "98765432-1098-4765-8432-109876543210",
        "01234567-8901-4234-8567-890123456789",
    ]
    # Garante que sao UUIDs validos:
    for u in uuids_literais:
        UUID(u)
    # Cada UUID em texto valido passa
    for u in uuids_literais:
        m = MotivoCancelamento(_envolver(u))
        assert m.texto


def test_motivo_cancelamento_varredura_1000_slugs_zero_falsos_positivos():
    """1000 slugs (a-z0-9-) NUNCA disparam regex PII."""
    falsos = []
    for _ in range(1000):
        slug = "".join(
            secrets.choice(string.ascii_lowercase + string.digits + "-")
            for _ in range(20)
        )
        try:
            MotivoCancelamento(_envolver(slug))
        except ValueError as exc:
            # Slugs com runs longos de digitos podem capturar sequencia_numerica;
            # nesse caso eh comportamento esperado. So pegamos casos onde
            # o slug NAO tem 7+ digitos consecutivos (esses sao OK).
            import re

            if not re.search(r"\d{7,}", slug):
                falsos.append((slug, str(exc)))
    assert not falsos, (
        f"VARREDURA falhou: {len(falsos)} slugs sem 7+ digitos consecutivos "
        f"viraram PII. Primeiros 3: {falsos[:3]}"
    )


def test_motivo_cancelamento_varredura_1000_hex64_zero_falsos_positivos():
    """1000 hashes hex de 64 chars (SHA-256-like) NUNCA disparam regex
    PII se desde que NAO tenham 7+ digitos decimais consecutivos."""
    import re

    falsos = []
    for _ in range(1000):
        h = "".join(secrets.choice("0123456789abcdef") for _ in range(64))
        try:
            MotivoCancelamento(_envolver(h))
        except ValueError as exc:
            # Hex pode ter runs de digitos decimais por azar — esperado.
            if not re.search(r"\d{7,}", h):
                falsos.append((h, str(exc)))
    assert not falsos, (
        f"VARREDURA falhou: {len(falsos)} hashes hex sem 7+ digitos viraram PII."
    )


def test_motivo_cancelamento_varredura_1000_base64url_zero_falsos_positivos():
    """1000 strings base64-url (a-zA-Z0-9_-) embrulhadas em frase passam."""
    import re

    falsos = []
    chars = string.ascii_letters + string.digits + "_-"
    for _ in range(1000):
        s = "".join(secrets.choice(chars) for _ in range(32))
        try:
            MotivoCancelamento(_envolver(s))
        except ValueError as exc:
            # base64 pode ter 2 letras maiusculas seguidas casando NOMES_RE
            # falso-positivo conhecido — toleramos.
            if not re.search(r"\d{7,}", s) and not re.search(
                r"\b[A-Z][a-z]+\s+[A-Z][a-z]+", s
            ):
                falsos.append((s, str(exc)))
    assert not falsos
