"""Q-CAL-04 conserto P5 (2026-05-27) — UUID literal digit-heavy regression.

Cobre TST-006 do prompt do auditor de qualidade: paralelo `Q-OS-04`. Testes
M4 usam `uuid4()` aleatorio; este arquivo carrega UUIDs LITERAIS com muitos
digitos (sem letras) para reproduzir o bug visao-360 RESOLVIDO em 2026-05-19
(memoria `project_flake_visao360_pytest_randomly`).

Bug original (paralelo): `sanitizar_payload_audit` tinha regex PII que
casava UUIDs estruturais digit-heavy (8% dos uuid4 vinham predominantemente
numericos) -> UUID virava `[REDACTED]`. Sanitizador devia isentar UUIDs
estruturais por sufixo `_id/_uuid/_hash` E pelo formato UUID v4 canonico.

`sanitizar_payload_evento_calibracao` (lgpd.py M4 — paralelo ao
sanitizar_payload_audit) precisa nao regredir. Este arquivo passa UUIDs
literais digit-heavy + sufixos canonicos + verifica que NAO sao mascarados.
"""

from __future__ import annotations

from uuid import UUID

from src.infrastructure.calibracao.lgpd import (
    sanitizar_payload_evento_calibracao,
)

# UUIDs literais digit-heavy (formato uuid4 canonico, predominantemente
# numericos — replicam o flake bug visao-360 de 2026-05-19).
UUID_DIGIT_HEAVY_1 = UUID("12345678-9012-4123-8456-789012345678")
UUID_DIGIT_HEAVY_2 = UUID("00000000-0000-4000-8000-000000000001")
UUID_DIGIT_HEAVY_3 = UUID("99999999-9999-4999-8999-999999999999")


class TestINV_CAL_AUD_001_UUID_DIGIT_HEAVY:
    """UUIDs estruturais (sufixo _id/_uuid/_hash) NAO sao mascarados
    pelo sanitizador, mesmo quando predominantemente numericos.

    Reproduz o bug RESOLVIDO no helper de auditoria
    (`sanitizar_payload_audit`) — garante que `sanitizar_payload_evento_calibracao`
    nao regrediu para o mesmo padrao.
    """

    def test_uuid_em_campo_id_passa_intacto(self) -> None:
        payload = {
            "calibracao_id": str(UUID_DIGIT_HEAVY_1),
            "tenant_id": str(UUID_DIGIT_HEAVY_2),
            "correlation_id": str(UUID_DIGIT_HEAVY_3),
            "valor": 42,
        }
        out = sanitizar_payload_evento_calibracao(
            payload, finalidade="regressao_digit_heavy"
        )
        assert out["calibracao_id"] == str(UUID_DIGIT_HEAVY_1)
        assert out["tenant_id"] == str(UUID_DIGIT_HEAVY_2)
        assert out["correlation_id"] == str(UUID_DIGIT_HEAVY_3)
        assert "[REDACTED" not in str(out)

    def test_uuid_em_campo_hash_passa_intacto(self) -> None:
        payload = {
            "cliente_referencia_hash": "v01$abc123",
            "motivo_hash": "v01$def456",
            "actor_user_id_hash": "v01$ghi789",
            # PII real deve ser mascarado:
            "cpf": "12345678901",
        }
        out = sanitizar_payload_evento_calibracao(
            payload, finalidade="regressao_digit_heavy_hash"
        )
        assert out["cliente_referencia_hash"] == "v01$abc123"
        assert out["motivo_hash"] == "v01$def456"
        assert out["actor_user_id_hash"] == "v01$ghi789"
        # PII real ainda eh mascarado:
        assert out["cpf"] == "[REDACTED-PII]"

    def test_lista_aninhada_uuid_digit_heavy_preservada(self) -> None:
        payload = {
            "leituras_ids": [str(UUID_DIGIT_HEAVY_1), str(UUID_DIGIT_HEAVY_2)],
            "componentes": [
                {"componente_id": str(UUID_DIGIT_HEAVY_3), "valor": "0.05"},
            ],
        }
        out = sanitizar_payload_evento_calibracao(
            payload, finalidade="regressao_lista_aninhada"
        )
        assert out["leituras_ids"] == [
            str(UUID_DIGIT_HEAVY_1),
            str(UUID_DIGIT_HEAVY_2),
        ]
        assert out["componentes"][0]["componente_id"] == str(  # type: ignore[index] -- list[dict] tipado dinamicamente
            UUID_DIGIT_HEAVY_3
        )
