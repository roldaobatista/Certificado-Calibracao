"""Anti-regressao INV-OS-ACEITE-BIO-001 (SEG-M3-OS-02 P5 conserto 2026-05-24).

Biometria touch (`AceiteAtividade.biometria_payload_encrypted`) eh dado
sensivel LGPD art. 11 II 'g' (Lei 14.063/2020) — exige chave KMS
DEDICADA por tenant (`BIOMETRIA_KEY_<tenant_id>`), nao a chave geral
de PII do tenant. `valida_consentimento_biometria` aplica:
(a) consentimento_id NOT NULL.
(b) biometria_key_id no formato canonico `BIOMETRIA_KEY_<tenant_id>`.

Validacao trajetoria (>=8 pontos + bbox 30x20px) + watermark HMAC
sao aplicadas no use case `coletar_aceite_atividade` ANTES do
snapshot (exigem dados decifrados). Aqui testamos a camada de dominio.

≥3 testes: happy (sem bio), happy (com bio + chave correta), unhappy
(consent ausente), unhappy (chave generica em vez de dedicada).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from src.domain.operacao.os.entities import AceiteAtividadeSnapshot
from src.domain.operacao.os.regras import valida_consentimento_biometria


def _aceite(
    *,
    biometria: bytes | None = None,
    consentimento_id=None,
    biometria_key_id: str = "",
) -> AceiteAtividadeSnapshot:
    return AceiteAtividadeSnapshot(
        id=uuid4(),
        tenant_id=uuid4(),
        atividade_id=uuid4(),
        consentimento_id=consentimento_id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms",
        texto_canonicalizado="<<<CORPO INICIO>>>\nAceito\n<<<CORPO FIM>>>",
        texto_hash="b" * 64,
        biometria_payload_encrypted=biometria,
        biometria_key_id=biometria_key_id,
        coletado_em=datetime.now(UTC),
        geo_lat=None,
        geo_long=None,
        geo_municipio_hash="",
        criado_em=datetime.now(UTC),
    )


def test_inv_os_aceite_bio_001_happy_sem_biometria_passa():
    """Aceite SEM biometria nao exige consentimento nem chave dedicada."""
    valida_consentimento_biometria(_aceite())  # nao raise


def test_inv_os_aceite_bio_001_happy_bio_com_chave_dedicada_correta():
    """Aceite COM biometria + consentimento + chave dedicada passa."""
    valida_consentimento_biometria(
        _aceite(
            biometria=b"\x01\x02\x03",
            consentimento_id=uuid4(),
            biometria_key_id="BIOMETRIA_KEY_aaaa-bbbb-cccc",
        )
    )  # nao raise


def test_inv_os_aceite_bio_001_unhappy_bio_sem_consentimento_raises():
    """Aceite COM biometria SEM consentimento_id -> ValueError INV-OS-CONSBIO-001."""
    with pytest.raises(ValueError, match="INV-OS-CONSBIO-001"):
        valida_consentimento_biometria(
            _aceite(
                biometria=b"\x01\x02\x03",
                consentimento_id=None,
                biometria_key_id="BIOMETRIA_KEY_xxx",
            )
        )


def test_inv_os_aceite_bio_001_unhappy_bio_sem_chave_dedicada_raises():
    """Aceite COM biometria + chave generica (sem prefixo BIOMETRIA_KEY_) raises."""
    with pytest.raises(ValueError, match="INV-OS-ACEITE-BIO-001"):
        valida_consentimento_biometria(
            _aceite(
                biometria=b"\x01\x02\x03",
                consentimento_id=uuid4(),
                biometria_key_id="kms-geral",  # NAO eh chave dedicada
            )
        )


def test_inv_os_aceite_bio_001_unhappy_bio_chave_vazia_raises():
    """Aceite COM biometria + biometria_key_id vazio raises."""
    with pytest.raises(ValueError, match="INV-OS-ACEITE-BIO-001"):
        valida_consentimento_biometria(
            _aceite(
                biometria=b"\x01\x02\x03",
                consentimento_id=uuid4(),
                biometria_key_id="",
            )
        )
