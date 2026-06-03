"""M9 Fatia 3 — testes PUROS (Fakes, sem Django/PG). TST-004.

Cobre:
  - T-LIC-050: sync `Licenca`(CGCRE) → cache no `renovar_documento` (porta Fake;
    dispara só CGCRE + perfil A; ignora demais tipos/perfis; erro de config sem porta).
  - T-LIC-051: função pura `verificar_alertas_licencas` (janelas D-90/60/30/15/7,
    revogado ignorado, destinatário) + refino do job perfil A (vigência real do cache).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.licencas_acreditacoes.cadastrar_documento_regulatorio import (
    executar as cadastrar_executar,
)
from src.application.metrologia.licencas_acreditacoes.jobs.verificar_alertas_licencas import (
    DocumentoAlertaSnapshot,
    verificar_alertas_licencas,
)
from src.application.metrologia.licencas_acreditacoes.renovar_documento import (
    RenovarDocumentoInput,
    SincronizacaoCgcreAusenteError,
)
from src.application.metrologia.licencas_acreditacoes.renovar_documento import (
    executar as renovar_executar,
)
from src.application.tenant.jobs.verificar_vigencia_acreditacao_perfil_a import (
    TenantPerfilASnapshot,
    verificar_vigencia_acreditacao_perfil_a,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    JANELAS_ALERTA_DIAS,
    CanalAlerta,
    MotivoRevisao,
    StatusAlerta,
    TipoDocumentoRegulatorio,
)

from tests.test_m9_licencas_use_cases_p2 import (
    FakeAlertaRepo,
    FakeBloqueioRepo,
    FakeDocRepo,
    FakeRevisaoRepo,
    _cad_input,
)


# --- Fake da porta de sincronização CGCRE ------------------------------------
class FakeCgcreSync:
    def __init__(self) -> None:
        self.chamadas: list[dict] = []

    def renovar_vigencia(self, *, tenant_id, vigencia_fim, motivo) -> None:
        assert len(motivo) >= 100  # CHECK da função aplicar_evento_cgcre
        self.chamadas.append(
            {"tenant_id": tenant_id, "vigencia_fim": vigencia_fim, "motivo": motivo}
        )


def _seed_cgcre(tenant_id: UUID, perfil: str = "A"):
    repo = FakeDocRepo()
    out = cadastrar_executar(
        _cad_input(
            tenant_id=tenant_id,
            tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
            numero="CRL-0001",
            orgao_emissor="CGCRE",
            perfil=perfil,
            escopo="massa 0..10kg",
            numero_cgcre="CRL-0001",
        ),
        repo,
    )
    return repo, out.documento


def _renovar_input(tenant_id, doc_id, **kw):
    base = {
        "tenant_id": tenant_id,
        "documento_id": doc_id,
        "nova_vigencia_inicio": date(2027, 1, 1),
        "nova_vigencia_fim": date(2031, 1, 1),
        "anexo_id": uuid4(),
        "anexo_sha256": "c" * 64,
        "motivo": MotivoRevisao.RENOVACAO,
        "criado_por": uuid4(),
        "criado_em": datetime(2026, 12, 1, tzinfo=UTC),
        "correlation_id": uuid4(),
    }
    base.update(kw)
    return RenovarDocumentoInput(**base)


class TestSyncRenovarCgcre:
    def test_cgcre_perfil_a_dispara_sync(self) -> None:
        tid = uuid4()
        repo, doc = _seed_cgcre(tid, perfil="A")
        sync = FakeCgcreSync()
        renovar_executar(
            _renovar_input(tid, doc.id, perfil="A"),
            doc_repo=repo, revisao_repo=FakeRevisaoRepo(),
            bloqueio_repo=FakeBloqueioRepo(), alerta_repo=FakeAlertaRepo(),
            cgcre_sync=sync,
        )
        assert len(sync.chamadas) == 1
        assert sync.chamadas[0]["tenant_id"] == tid
        assert sync.chamadas[0]["vigencia_fim"] == date(2031, 1, 1)

    def test_cgcre_sem_porta_erro_de_config(self) -> None:
        tid = uuid4()
        repo, doc = _seed_cgcre(tid, perfil="A")
        with pytest.raises(SincronizacaoCgcreAusenteError):
            renovar_executar(
                _renovar_input(tid, doc.id, perfil="A"),
                doc_repo=repo, revisao_repo=FakeRevisaoRepo(),
                bloqueio_repo=FakeBloqueioRepo(), alerta_repo=FakeAlertaRepo(),
            )

    def test_cgcre_perfil_b_nao_dispara(self) -> None:
        # B cadastra CGCRE (em evolução), mas renovação NÃO renova o cache do perfil A.
        tid = uuid4()
        repo, doc = _seed_cgcre(tid, perfil="B")
        sync = FakeCgcreSync()
        renovar_executar(
            _renovar_input(tid, doc.id, perfil="B"),
            doc_repo=repo, revisao_repo=FakeRevisaoRepo(),
            bloqueio_repo=FakeBloqueioRepo(), alerta_repo=FakeAlertaRepo(),
            cgcre_sync=sync,
        )
        assert sync.chamadas == []

    def test_art_nao_dispara_sync(self) -> None:
        tid = uuid4()
        repo = FakeDocRepo()
        out = cadastrar_executar(
            _cad_input(tenant_id=tid, tipo=TipoDocumentoRegulatorio.ART, numero="ART-1"),
            repo,
        )
        sync = FakeCgcreSync()
        renovar_executar(
            _renovar_input(tid, out.documento.id, perfil="A"),
            doc_repo=repo, revisao_repo=FakeRevisaoRepo(),
            bloqueio_repo=FakeBloqueioRepo(), alerta_repo=FakeAlertaRepo(),
            cgcre_sync=sync,
        )
        assert sync.chamadas == []


class TestVerificarAlertasLicencas:
    def _snap(self, vig_fim: date, **kw):
        base = {
            "documento_id": uuid4(),
            "tenant_id": uuid4(),
            "vigencia_fim": vig_fim,
        }
        base.update(kw)
        return DocumentoAlertaSnapshot(**base)

    def test_fora_de_qualquer_janela_nao_alerta(self) -> None:
        agora = date(2026, 1, 1)
        snap = self._snap(date(2026, 6, 1))  # ~151 dias > 90
        assert verificar_alertas_licencas([snap], agora=agora) == []

    def test_janela_90_dispara_uma(self) -> None:
        agora = date(2026, 1, 1)
        snap = self._snap(agora.replace(month=3))  # ~59 dias → <=90 e <=60
        alertas = verificar_alertas_licencas([snap], agora=agora)
        janelas = sorted(a.janela_dias for a in alertas)
        assert janelas == [60, 90]

    def test_vencido_cobre_todas_as_janelas(self) -> None:
        agora = date(2026, 6, 1)
        snap = self._snap(date(2026, 5, 1))  # vencido
        alertas = verificar_alertas_licencas([snap], agora=agora)
        assert sorted(a.janela_dias for a in alertas) == sorted(JANELAS_ALERTA_DIAS)
        assert all(a.status is StatusAlerta.PENDENTE for a in alertas)

    def test_revogado_ignorado(self) -> None:
        agora = date(2026, 6, 1)
        snap = self._snap(date(2026, 6, 10), revogado=True)
        assert verificar_alertas_licencas([snap], agora=agora) == []

    def test_destinatario_responsavel_ou_dashboard(self) -> None:
        agora = date(2026, 6, 1)
        resp = uuid4()
        com_resp = self._snap(date(2026, 6, 5), responsavel_id=resp)
        sem_resp = self._snap(date(2026, 6, 5))
        a1 = verificar_alertas_licencas([com_resp], agora=agora)
        a2 = verificar_alertas_licencas([sem_resp], agora=agora)
        assert all(a.destinatario_id == resp for a in a1)
        assert all(a.destinatario_id == UUID(int=0) for a in a2)
        assert all(a.canal is CanalAlerta.DASHBOARD for a in a1)


class TestRefinoJobPerfilA:
    def _snap(self, **kw):
        base = {
            "tenant_id": uuid4(),
            "slug": "lab-x",
            "perfil_regulatorio": "A",
            "acreditacao_cgcre_numero": "CRL-0001",
            "acreditacao_suspensa_em": None,
            "acreditacao_suspensa_ate": None,
        }
        base.update(kw)
        return TenantPerfilASnapshot(**base)

    def test_vigencia_vencida_critico(self) -> None:
        agora = date(2026, 6, 1)
        snap = self._snap(acreditacao_vigencia_fim=date(2026, 5, 1))
        alertas = verificar_vigencia_acreditacao_perfil_a([snap], agora=agora)
        assert len(alertas) == 1
        assert alertas[0].severidade == "CRITICO"

    def test_vigencia_em_janela_aviso(self) -> None:
        agora = date(2026, 6, 1)
        snap = self._snap(acreditacao_vigencia_fim=date(2026, 7, 1))  # 30 dias <=60
        alertas = verificar_vigencia_acreditacao_perfil_a([snap], agora=agora)
        assert len(alertas) == 1
        assert alertas[0].severidade == "AVISO"

    def test_vigencia_plena_sem_alerta(self) -> None:
        agora = date(2026, 1, 1)
        snap = self._snap(acreditacao_vigencia_fim=date(2030, 1, 1))
        assert verificar_vigencia_acreditacao_perfil_a([snap], agora=agora) == []

    def test_vigencia_none_cai_no_caminho_legado(self) -> None:
        # Tenant A legado sem licença → vigencia_fim None; sem suspensão = OK.
        agora = date(2026, 1, 1)
        snap = self._snap(acreditacao_vigencia_fim=None)
        assert verificar_vigencia_acreditacao_perfil_a([snap], agora=agora) == []
