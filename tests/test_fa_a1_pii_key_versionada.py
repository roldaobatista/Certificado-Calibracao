"""FA-A1 + FA-M2 — chave de hash de PII versionada + hardening/gate de prod.

Prova:
- helper retorna hash PREFIXADO `v1:...` (nenhum hash sem prefixo nasce).
- `verificar_pii_hash` round-trip com chave ativa; adulterado = False.
- ROTAÇÃO: hash gerado com v1 ainda verifica True depois que ativa vira v2
  (v1 em PII_HASH_KEYS_RETIRED) — o objetivo central do FA-A1.
- versão desconhecida / sem prefixo → ChavePIIIndisponivel (UNHAPPY: resposta
  INCONCLUSIVA, não negativa — R1 advogado).
- anti-vazamento (T1 tech-lead): registry não expõe segredo em repr/str e
  settings NÃO tem `PII_HASH_KEY` cru no namespace.
- gate de prod (FA-M2/T2): sem PII_HASH_KEY → ImproperlyConfigured; com
  envs mínimos → importa + flags de hardening ligadas.
- PII_HASH_KEYS_RETIRED malformado → erro no import (nunca silêncio).
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import uuid

import pytest
from config.settings.base import (
    _parse_chaves_aposentadas,
    _RegistroChavesPII,
)
from django.conf import settings
from src.infrastructure.audit.services import (
    ChavePIIIndisponivel,
    hashear_pii_com_salt_tenant,
    verificar_pii_hash,
)

TID = uuid.uuid4()


class TestHelperVersionado:
    def test_helper_retorna_hash_prefixado(self) -> None:
        h = hashear_pii_com_salt_tenant("12345678901", TID)
        assert h.startswith(f"{settings.PII_HASH_KEY_REGISTRO.ativa_id}:")
        assert len(h.split(":", 1)[1]) == 64  # sha256 hexdigest

    def test_valor_vazio_continua_string_vazia(self) -> None:
        assert hashear_pii_com_salt_tenant("", TID) == ""

    def test_tenant_id_none_levanta(self) -> None:
        with pytest.raises(ValueError):
            hashear_pii_com_salt_tenant("x", None)  # type: ignore[arg-type]


class TestVerificacao:
    def test_round_trip_chave_ativa(self) -> None:
        h = hashear_pii_com_salt_tenant("99988877766", TID)
        assert verificar_pii_hash("99988877766", TID, h) is True

    def test_valor_diferente_nao_casa(self) -> None:
        h = hashear_pii_com_salt_tenant("99988877766", TID)
        assert verificar_pii_hash("00000000000", TID, h) is False

    def test_digest_adulterado_no_ultimo_char_nao_casa(self) -> None:
        h = hashear_pii_com_salt_tenant("99988877766", TID)
        kid, dig = h.split(":", 1)
        viciado = f"{kid}:{dig[:-1]}{'0' if dig[-1] != '0' else '1'}"
        assert verificar_pii_hash("99988877766", TID, viciado) is False

    def test_versao_desconhecida_levanta_inconclusiva(self) -> None:
        with pytest.raises(ChavePIIIndisponivel):
            verificar_pii_hash("x", TID, "v999:" + "a" * 64)

    def test_hash_sem_prefixo_levanta_nao_false(self) -> None:
        # legado silencioso seria afirmar falsamente "não casou" (R1).
        with pytest.raises(ChavePIIIndisponivel):
            verificar_pii_hash("x", TID, "a" * 64)

    def test_rotacao_v1_ainda_verifica_apos_v2_ativa(self) -> None:
        """O ponto do FA-A1: rotacionar não invalida hash retroativo."""
        chave_v1 = b"chave-secreta-v1-com-32-bytes-ok!"
        chave_v2 = b"chave-secreta-v2-com-32-bytes-ok!"
        reg_v1 = _RegistroChavesPII("v1", {"v1": chave_v1})
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(settings, "PII_HASH_KEY_REGISTRO", reg_v1)
            h_antigo = hashear_pii_com_salt_tenant("55544433322", TID)
            assert h_antigo.startswith("v1:")

        # Rotação: v2 vira ativa, v1 aposentada (continua no registry).
        reg_v2 = _RegistroChavesPII("v2", {"v2": chave_v2, "v1": chave_v1})
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(settings, "PII_HASH_KEY_REGISTRO", reg_v2)
            assert verificar_pii_hash("55544433322", TID, h_antigo) is True
            novo = hashear_pii_com_salt_tenant("55544433322", TID)
            assert novo.startswith("v2:")
            assert novo != h_antigo


class TestRegistryAntiVazamento:
    def test_repr_e_str_nao_expoem_bytes(self) -> None:
        seg = b"SEGREDO-SUPER-SECRETO-32-bytes!!"
        reg = _RegistroChavesPII("v1", {"v1": seg})
        for texto in (repr(reg), str(reg), f"{reg}"):
            assert "SEGREDO" not in texto
            assert seg.decode() not in texto
            assert "redacted" in texto

    def test_settings_nao_tem_pii_hash_key_cru(self) -> None:
        # T1: só o objeto registry no namespace; nenhum bytes cru pra vazar.
        assert not hasattr(settings, "PII_HASH_KEY")
        assert hasattr(settings, "PII_HASH_KEY_REGISTRO")

    def test_get_safe_settings_nao_vaza(self) -> None:
        from django.views.debug import SafeExceptionReporterFilter

        safe = str(SafeExceptionReporterFilter().get_safe_settings())
        ativa = settings.PII_HASH_KEY_REGISTRO.chave_ativa()
        assert ativa.hex() not in safe
        assert ativa.decode("latin-1") not in safe


class TestParseChavesAposentadas:
    def test_vazio_retorna_dict_vazio(self) -> None:
        assert _parse_chaves_aposentadas("") == {}

    def test_parse_ok(self) -> None:
        r = _parse_chaves_aposentadas("v0:seg0,v-1:segX")
        assert r == {"v0": b"seg0", "v-1": b"segX"}

    @pytest.mark.parametrize("ruim", ["v0", "v0:", ":seg", "v0:seg,,v1:s"])
    def test_malformado_levanta(self, ruim: str) -> None:
        with pytest.raises(ValueError):
            _parse_chaves_aposentadas(ruim)


def _rodar_prod(env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Importa config.settings.prod em subprocesso com env controlado."""
    code = textwrap.dedent(
        """
        import django
        try:
            django.setup()
            from django.conf import settings
            print("OK:" + str(settings.SECURE_SSL_REDIRECT))
        except Exception as e:
            print(type(e).__name__ + ":" + str(e))
        """
    )
    base_env = {
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "DJANGO_DEBUG": "False",
        "DJANGO_ALLOWED_HOSTS": "afere.example.com",
        "DATABASE_URL": "postgres://app_user:x@db:5432/afere",
        "DATABASE_MIGRATOR_URL": "postgres://app_migrator:x@db:5432/afere",
    }
    base_env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-c", code],  # noqa: S603 -- executavel do proprio interpretador + codigo literal fixo, sem input externo
        capture_output=True,
        text=True,
        env=base_env,
        cwd="/app",
        check=False,
    )


class TestGateProd:
    SECRET_OK = "x" * 60

    def test_sem_pii_hash_key_falha_duro(self) -> None:
        out = _rodar_prod({"DJANGO_SECRET_KEY": self.SECRET_OK}).stdout
        assert "ImproperlyConfigured" in out
        assert "PII_HASH_KEY" in out

    def test_secret_key_curta_falha_duro(self) -> None:
        out = _rodar_prod({"DJANGO_SECRET_KEY": "curta", "PII_HASH_KEY": "y" * 40}).stdout
        assert "ImproperlyConfigured" in out
        assert "SECRET_KEY" in out

    def test_sem_qr_hmac_key_falha_duro(self) -> None:
        # SEC-QR-001: prod sem QR_HMAC_KEY dedicada nao pode subir.
        out = _rodar_prod(
            {
                "DJANGO_SECRET_KEY": self.SECRET_OK,
                "PII_HASH_KEY": "y" * 40,
                "PII_HASH_KEY_ID": "v1",
            }
        ).stdout
        assert "ImproperlyConfigured" in out
        assert "QR_HMAC_KEY" in out

    def test_qr_hmac_key_igual_pii_hash_key_falha_duro(self) -> None:
        # SEC-QR-001: chaves DEVEM ser distintas (politica de rotacao diferente).
        out = _rodar_prod(
            {
                "DJANGO_SECRET_KEY": self.SECRET_OK,
                "PII_HASH_KEY": "y" * 40,
                "PII_HASH_KEY_ID": "v1",
                "QR_HMAC_KEY": "y" * 40,  # IDENTICA -> deve quebrar
                "QR_HMAC_KEY_ID": "qr1",
            }
        ).stdout
        assert "ImproperlyConfigured" in out
        assert "identica" in out.lower() or "distintas" in out.lower()

    def test_envs_minimos_importa_e_hardening_ligado(self) -> None:
        # SEC-QR-001 (Marco 2): prod.py exige QR_HMAC_KEY dedicada (>=32
        # chars) distinta de PII_HASH_KEY.
        # MEDIO-1 P5 auditor-seguranca (d6ba200): prod.py tambem exige
        # QR_IP_RATELIMIT_SALT (>=32 chars) distinta das outras chaves —
        # salt do HMAC de ip_hash do rate-limit do QR publico (corretora
        # RAT-EQP-QR). Suite de gate absorve a nova exigencia.
        out = _rodar_prod(
            {
                "DJANGO_SECRET_KEY": self.SECRET_OK,
                "PII_HASH_KEY": "y" * 40,
                "PII_HASH_KEY_ID": "v1",
                "QR_HMAC_KEY": "z" * 40,
                "QR_HMAC_KEY_ID": "qr1",
                "QR_IP_RATELIMIT_SALT": "w" * 40,
            }
        ).stdout
        # `in` (nao startswith): sob pytest-cov o subprocesso pode emitir
        # linha de coverage no stdout antes do nosso print — flake removido.
        assert "OK:True" in out, out
        assert "ImproperlyConfigured" not in out, out
