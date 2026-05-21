"""SEC-QR-001 + INV-051 + INV-EQP-QR-NUNCA-RECOMPUTA — regressao Marco 2.

Suite anti-regressao da cadeia HMAC-versionada do QR Code de equipamento.
Espelha o pattern de `test_fa_a1_pii_key_versionada.py` (FA-A1) com 3
acoes especificas pra Marco 2:

- HAPPY: helper retorna hash prefixado `qrN:` >=22 chars (>=128 bits).
- ROTACAO: chave antiga (qr1) aposentada continua verificavel via TABELA
  apos qr2 virar ativa. Ponto central — etiqueta fisica nao invalida.
- INV-EQP-QR-NUNCA-RECOMPUTA: verificacao SEMPRE consulta tabela; UPDATE
  do hash bloqueado por trigger PG; hash inexistente retorna None
  (404 indistinguivel anti-enumeracao).
- ANTI-VAZAMENTO: settings nao expoe QR_HMAC_KEY cru; registry redatado.
- ISOLAMENTO RLS: scan QR de tenant A nao retorna registro de tenant B.

Pre-condicoes:
- modelo Equipamento + QRCode em src/infrastructure/equipamentos/models.py
- helper services_qr.gerar_qr_hash_versionado() + verificar_qr_hash_em_tabela()
- settings.QR_HMAC_KEY_REGISTRO via FA-A1 _RegistroChavesPII reusado
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from config.settings.base import _RegistroChavesPII
from django.conf import settings
from django.db.utils import ProgrammingError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, QRCode
from src.infrastructure.equipamentos.services_qr import (
    gerar_qr_hash_versionado,
    verificar_qr_hash_em_tabela,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


@pytest.fixture
def cenario(db):
    tenant_a = TenantFactory(slug=f"qr-a-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"qr-b-{uuid4().hex[:6]}")
    with run_in_tenant_context(tenant_a.id):
        cliente_a = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cli QR Test A",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq_a = Equipamento.objects.create(
            tenant=tenant_a,
            tag="QR-EQ-A",
            numero_serie="NS-A",
            fabricante="F",
            modelo="M",
            cliente_atual=cliente_a,
            perfil_tenant_snapshot={},
        )
    with run_in_tenant_context(tenant_b.id):
        eq_b = Equipamento.objects.create(
            tenant=tenant_b,
            tag="QR-EQ-B",
            numero_serie="NS-B",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
    return {"tenant_a": tenant_a, "tenant_b": tenant_b, "eq_a": eq_a, "eq_b": eq_b}


class TestHelperVersionado:
    def test_hash_gerado_tem_prefixo_qr_versao(self) -> None:
        h = gerar_qr_hash_versionado(uuid4(), uuid4(), datetime.now(UTC))
        prefixo = f"{settings.QR_HMAC_KEY_REGISTRO.ativa_id}:"
        assert h.startswith(prefixo)
        digest = h.split(":", 1)[1]
        # base64url do SHA256 sem padding == 43 chars (>=22 → >=128 bits entropia).
        assert len(digest) >= 22

    def test_payload_canonico_inclui_emitido_em(self) -> None:
        eq_id = uuid4()
        tid = uuid4()
        t1 = datetime(2026, 5, 21, 10, 0, 0, tzinfo=UTC)
        t2 = datetime(2026, 5, 21, 10, 0, 1, tzinfo=UTC)
        h1 = gerar_qr_hash_versionado(eq_id, tid, t1)
        h2 = gerar_qr_hash_versionado(eq_id, tid, t2)
        assert h1 != h2

    def test_inputs_obrigatorios(self) -> None:
        with pytest.raises(ValueError):
            gerar_qr_hash_versionado(None, uuid4(), datetime.now(UTC))  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            gerar_qr_hash_versionado(uuid4(), None, datetime.now(UTC))  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            gerar_qr_hash_versionado(uuid4(), uuid4(), None)  # type: ignore[arg-type]


@pytest.mark.django_db(transaction=True)
class TestVerificacaoViaTabela:
    """INV-EQP-QR-NUNCA-RECOMPUTA: verificacao SEMPRE consulta a tabela."""

    def test_round_trip_hash_existente_retorna_registro(self, cenario):
        emitido = datetime.now(UTC)
        h = gerar_qr_hash_versionado(cenario["eq_a"].id, cenario["tenant_a"].id, emitido)
        with run_in_tenant_context(cenario["tenant_a"].id):
            qr = QRCode.objects.create(
                tenant=cenario["tenant_a"],
                equipamento=cenario["eq_a"],
                hash=h,
                emitido_em=emitido,
            )
            achado = verificar_qr_hash_em_tabela(h)
        assert achado is not None
        assert achado.id == qr.id

    def test_hash_inexistente_retorna_none(self, cenario):
        # 404 indistinguivel de 200 vazio (anti-enumeracao).
        with run_in_tenant_context(cenario["tenant_a"].id):
            ausente = verificar_qr_hash_em_tabela("qr1:" + "a" * 43)
        assert ausente is None

    def test_hash_sem_prefixo_retorna_none(self):
        # Hash invalido (sem `:`) nem chega a query.
        assert verificar_qr_hash_em_tabela("a" * 43) is None
        assert verificar_qr_hash_em_tabela("") is None

    def test_hash_revogado_retorna_none(self, cenario):
        emitido = datetime.now(UTC)
        h = gerar_qr_hash_versionado(cenario["eq_a"].id, cenario["tenant_a"].id, emitido)
        with run_in_tenant_context(cenario["tenant_a"].id):
            qr = QRCode.objects.create(
                tenant=cenario["tenant_a"],
                equipamento=cenario["eq_a"],
                hash=h,
                emitido_em=emitido,
            )
            # Re-emissao revoga: UPDATE no campo MUTAVEL (revogado_em).
            QRCode.all_objects.filter(id=qr.id).update(revogado_em=datetime.now(UTC))
            apos_revogacao = verificar_qr_hash_em_tabela(h)
        assert apos_revogacao is None


@pytest.mark.django_db(transaction=True)
class TestRotacaoChave:
    """O ponto central do SEC-QR-001: rotacao NAO invalida etiqueta impressa.

    Diferente do FA-A1 (PII verifica recomputando), aqui a etiqueta fisica
    armazena o hash inteiro `qrN:...` e a verificacao consulta a tabela —
    rotacao da chave ativa para qr2 nao afeta hash qr1 ja gravado.
    """

    def test_hash_qr1_continua_resolvendo_pos_rotacao_para_qr2(self, cenario):
        emitido = datetime.now(UTC)
        # Estado normal: qr1 ativa, hash gerado e gravado.
        h_antigo = gerar_qr_hash_versionado(cenario["eq_a"].id, cenario["tenant_a"].id, emitido)
        assert h_antigo.startswith(f"{settings.QR_HMAC_KEY_REGISTRO.ativa_id}:")
        with run_in_tenant_context(cenario["tenant_a"].id):
            QRCode.objects.create(
                tenant=cenario["tenant_a"],
                equipamento=cenario["eq_a"],
                hash=h_antigo,
                emitido_em=emitido,
            )

        # Rotacao: qr2 vira ativa; qr1 aposentada mas presente no registry.
        chave_qr2 = b"chave-qr2-com-32-bytes-secret-ok!"
        chave_qr1_atual = settings.QR_HMAC_KEY_REGISTRO.chave_ativa()
        reg_qr2 = _RegistroChavesPII("qr2", {"qr2": chave_qr2, "qr1": chave_qr1_atual})
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(settings, "QR_HMAC_KEY_REGISTRO", reg_qr2)
            # Hash gerado AGORA usa qr2.
            h_novo = gerar_qr_hash_versionado(uuid4(), uuid4(), datetime.now(UTC))
            assert h_novo.startswith("qr2:")
            # Hash antigo CONTINUA resolvendo na tabela (consulta direta).
            with run_in_tenant_context(cenario["tenant_a"].id):
                achado = verificar_qr_hash_em_tabela(h_antigo)
            assert achado is not None


@pytest.mark.django_db(transaction=True)
class TestImutabilidadePosInsert:
    """INV-EQP-QR-NUNCA-RECOMPUTA via trigger PG (defesa em profundidade)."""

    def test_update_hash_bloqueado_por_trigger(self, cenario):
        emitido = datetime.now(UTC)
        h = gerar_qr_hash_versionado(cenario["eq_a"].id, cenario["tenant_a"].id, emitido)
        with run_in_tenant_context(cenario["tenant_a"].id):
            qr = QRCode.objects.create(
                tenant=cenario["tenant_a"],
                equipamento=cenario["eq_a"],
                hash=h,
                emitido_em=emitido,
            )
            with pytest.raises(ProgrammingError, match="INV-EQP-QR-NUNCA-RECOMPUTA"):
                QRCode.all_objects.filter(id=qr.id).update(hash=h + "x")

    def test_update_emitido_em_bloqueado(self, cenario):
        emitido = datetime.now(UTC)
        h = gerar_qr_hash_versionado(cenario["eq_a"].id, cenario["tenant_a"].id, emitido)
        with run_in_tenant_context(cenario["tenant_a"].id):
            qr = QRCode.objects.create(
                tenant=cenario["tenant_a"],
                equipamento=cenario["eq_a"],
                hash=h,
                emitido_em=emitido,
            )
            with pytest.raises(ProgrammingError, match="emitido_em.*imutavel"):
                QRCode.all_objects.filter(id=qr.id).update(emitido_em=datetime.now(UTC))

    def test_update_equipamento_id_bloqueado(self, cenario):
        emitido = datetime.now(UTC)
        h = gerar_qr_hash_versionado(cenario["eq_a"].id, cenario["tenant_a"].id, emitido)
        with run_in_tenant_context(cenario["tenant_a"].id):
            qr = QRCode.objects.create(
                tenant=cenario["tenant_a"],
                equipamento=cenario["eq_a"],
                hash=h,
                emitido_em=emitido,
            )
            with pytest.raises(ProgrammingError, match="equipamento_id.*imutavel"):
                QRCode.all_objects.filter(id=qr.id).update(equipamento_id=uuid4())

    def test_revogado_em_e_unico_campo_mutavel(self, cenario):
        emitido = datetime.now(UTC)
        h = gerar_qr_hash_versionado(cenario["eq_a"].id, cenario["tenant_a"].id, emitido)
        with run_in_tenant_context(cenario["tenant_a"].id):
            qr = QRCode.objects.create(
                tenant=cenario["tenant_a"],
                equipamento=cenario["eq_a"],
                hash=h,
                emitido_em=emitido,
            )
            QRCode.all_objects.filter(id=qr.id).update(revogado_em=datetime.now(UTC))
            qr.refresh_from_db()
        assert qr.revogado_em is not None


@pytest.mark.django_db(transaction=True)
class TestIsolamentoCrossTenant:
    """INV-TENANT-001: scan QR de tenant A nao retorna registro de tenant B."""

    def test_qr_de_b_invisivel_a_partir_de_tenant_a(self, cenario):
        emitido = datetime.now(UTC)
        h_b = gerar_qr_hash_versionado(cenario["eq_b"].id, cenario["tenant_b"].id, emitido)
        with run_in_tenant_context(cenario["tenant_b"].id):
            QRCode.objects.create(
                tenant=cenario["tenant_b"],
                equipamento=cenario["eq_b"],
                hash=h_b,
                emitido_em=emitido,
            )
        # Tenant A escaneia hash que pertence a tenant B — RLS nao retorna.
        with run_in_tenant_context(cenario["tenant_a"].id):
            achado = verificar_qr_hash_em_tabela(h_b)
        assert achado is None


class TestAntiVazamentoSettings:
    """Anti-vazamento: registry redatado + sem chave crua no namespace."""

    def test_settings_nao_tem_qr_hmac_key_cru(self):
        assert not hasattr(settings, "QR_HMAC_KEY")
        assert hasattr(settings, "QR_HMAC_KEY_REGISTRO")

    def test_repr_qr_registry_redatado(self):
        texto = repr(settings.QR_HMAC_KEY_REGISTRO)
        ativa = settings.QR_HMAC_KEY_REGISTRO.chave_ativa()
        assert "redacted" in texto
        # Bytes brutos da chave nao podem aparecer em hex nem latin-1.
        try:
            assert ativa.decode("latin-1") not in texto
        except UnicodeDecodeError:
            pass
        assert ativa.hex() not in texto

    def test_get_safe_settings_nao_vaza_qr(self):
        from django.views.debug import SafeExceptionReporterFilter

        safe = str(SafeExceptionReporterFilter().get_safe_settings())
        ativa = settings.QR_HMAC_KEY_REGISTRO.chave_ativa()
        assert ativa.hex() not in safe


class TestHashBase64Url:
    """INV-051: digest base64url (urlsafe) — sem `+` ou `/` que quebrariam URL."""

    def test_digest_e_urlsafe(self) -> None:
        h = gerar_qr_hash_versionado(uuid4(), uuid4(), datetime.now(UTC))
        digest = h.split(":", 1)[1]
        # base64.urlsafe_b64encode usa - e _ no lugar de + e /.
        assert "+" not in digest
        assert "/" not in digest
        # Sem padding `=` (rstrip aplicado).
        assert "=" not in digest

    def test_digest_decodavel_b64url(self) -> None:
        h = gerar_qr_hash_versionado(uuid4(), uuid4(), datetime.now(UTC))
        digest = h.split(":", 1)[1]
        # base64url decoda com padding restituido.
        padding = "=" * (-len(digest) % 4)
        raw = base64.urlsafe_b64decode(digest + padding)
        assert len(raw) == 32  # SHA-256 produz 32 bytes
