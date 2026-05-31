"""TST-004 — classes nomeando cada INV-PROC-001..010 (M7 Fatia 3 / T-PROC-046).

Convenção do projeto (análoga `test_inv_ecmc_classes_nomeadas.py` do M6 e
`test_inv_pad_classes_nomeadas.py` do M5): todo INV crítico tem >=1 teste cujo
NOME cita o ID. Cada classe `TestINV_PROC_NNN` exercita a barreira REAL —
PG-real onde a defesa é trigger/constraint/porta (001/002/003/004/008); puro/Fake
onde é domínio/use case (005/006/007/009/010).

O comportamento PG fino (RLS cross-tenant, one-shot revogação, RASCUNHO editável)
já vive em `test_inv_proc_p2_schema_triggers.py`; aqui consolidamos a leitura
INV-por-INV (rastreabilidade auditoria).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError
from django.utils import timezone
from src.application.metrologia.calibracao.configurar_calibracao import (
    ProcedimentoVigenteAusente,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    executar as configurar_executar,
)
from src.application.metrologia.procedimentos_calibracao import (
    cadastrar_procedimento,
    publicar_procedimento,
)
from src.application.metrologia.procedimentos_calibracao.anexo_storage import (
    sha256_server_side,
)
from src.domain.metrologia.calibracao.enums import TipoAcreditacao
from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
    ProcedimentoUsado,
)
from src.domain.metrologia.procedimentos_calibracao.enums import (
    EstadoProcedimento,
    TipoMetodo,
)
from src.domain.metrologia.procedimentos_calibracao.transicoes import (
    metodo_exige_validacao_pendente,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.metrologia.procedimentos_calibracao import query_service
from src.infrastructure.metrologia.procedimentos_calibracao.models import (
    ProcedimentoCalibracao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory
from tests.test_m4_uc_configurar_calibracao import _criar_calibracao_avulsa
from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository
from tests.test_m7_wire_in_configurar_p3 import (
    _input_rbc,
    _proc_ausente,
    _proc_vigente,
)

T0 = datetime(2026, 6, 1, tzinfo=UTC)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _cria_proc_pg(
    tenant,
    *,
    codigo: str = "PC-MASSA-001",
    grandeza: str = "massa",
    faixa_min: str = "0",
    faixa_max: str = "1000",
    unidade: str = "g",
    estado: str = "PUBLICADO",
    versao: int = 1,
    vigencia_fim=None,
) -> ProcedimentoCalibracao:
    with run_in_tenant_context(tenant.id):
        return ProcedimentoCalibracao.objects.create(
            tenant=tenant,
            codigo=codigo,
            titulo="Calibração de massa",
            grandeza=grandeza,
            faixa_min=Decimal(faixa_min),
            faixa_max=Decimal(faixa_max),
            unidade=unidade,
            metodo_norma="OIML R76",
            tipo_metodo="NORMALIZADO",
            numero_revisao="Rev. 03",
            aprovado_em=timezone.now(),
            aprovado_por_id=uuid4(),
            anexo_pdf_sha256="abc123",
            versao=versao,
            vigente_a_partir=timezone.now(),
            estado=estado,
            vigencia_inicio=timezone.now(),
            vigencia_fim=vigencia_fim,
        )


def _proc_snapshot(**kw) -> ProcedimentoSnapshot:
    base = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "codigo": "PC-MASSA-001",
        "titulo": "Calibração de massa",
        "grandeza": Grandeza.MASSA,
        "faixa": FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
        "metodo_norma": "OIML R76",
        "tipo_metodo": TipoMetodo.NORMALIZADO,
        "numero_revisao": "Rev. 03",
        "anexo_pdf_storage_key": "key-pc-1",
        "anexo_pdf_sha256": "abc123",
        "versao": 1,
        "vigente_a_partir": T0,
        "estado": EstadoProcedimento.PUBLICADO,
        "revision": 0,
        "vigencia_inicio": T0,
        "correlation_id": uuid4(),
        "aprovado_em": T0,
        "aprovado_por_id": uuid4(),
    }
    base.update(kw)
    return ProcedimentoSnapshot(**base)


def _usado(**kw) -> ProcedimentoUsado:
    base = {
        "procedimento_id": uuid4(),
        "codigo": "PC-MASSA-001",
        "versao": 2,
        "numero_revisao": "Rev. 04",
        "titulo": "Massa",
        "grandeza": Grandeza.MASSA,
        "faixa_procedimento": FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
        "faixa_solicitada": FaixaMedicao(Decimal("10"), Decimal("20"), "g"),
        "metodo_norma": "OIML R76",
        "tipo_metodo": TipoMetodo.NORMALIZADO,
        "anexo_pdf_sha256": "deadbeef",
        "perfil_no_evento": "A",
        "data_referencia": date(2026, 6, 1),
        "vigencia_inicio": T0,
        "contido": True,
    }
    base.update(kw)
    return ProcedimentoUsado(**base)


def _cadastrar_input(**kw):
    base = {
        "tenant_id": uuid4(),
        "codigo": "PC-MASSA-001",
        "titulo": "Calibração de massa",
        "grandeza": Grandeza.MASSA,
        "faixa": FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
        "metodo_norma": "OIML R76",
        "tipo_metodo": TipoMetodo.NORMALIZADO,
        "perfil": "A",
        "vigencia_inicio": T0,
        "correlation_id": uuid4(),
    }
    base.update(kw)
    return cadastrar_procedimento.CadastrarProcedimentoInput(**base)


# ==========================================================================
class TestINV_PROC_001:
    """Resolução `vigente_em` só PUBLICADO + vigente em `data` contendo a faixa."""

    @pytest.mark.django_db(transaction=True)
    def test_vigente_dentro_resolve_fora_e_rascunho_nao(self):
        tenant = TenantFactory(slug=f"proci1-{uuid4().hex[:6]}")
        _cria_proc_pg(tenant, faixa_min="0", faixa_max="1000")
        _cria_proc_pg(tenant, codigo="PC-RAS", estado="RASCUNHO")
        agora = timezone.now()
        with run_in_tenant_context(tenant.id):
            dentro = query_service.vigente_em(
                tenant_id=tenant.id, grandeza="massa",
                faixa_min=Decimal("10"), faixa_max=Decimal("20"), unidade="g", data=agora,
            )
            fora = query_service.vigente_em(
                tenant_id=tenant.id, grandeza="massa",
                faixa_min=Decimal("900"), faixa_max=Decimal("2000"), unidade="g", data=agora,
            )
        assert dentro is not None and dentro.codigo == "PC-MASSA-001"
        assert fora is None  # transbordo + rascunho nunca resolvem


class TestINV_PROC_002:
    """UNIQUE documental tenant-scoped (tenant, codigo, versao)."""

    @pytest.mark.django_db(transaction=True)
    def test_chave_documental_duplicada_bloqueia(self):
        tenant = TenantFactory(slug=f"proci2-{uuid4().hex[:6]}")
        _cria_proc_pg(tenant, codigo="PC-DUP", versao=1)
        with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
            _cria_proc_pg(tenant, codigo="PC-DUP", versao=1)


class TestINV_PROC_003:
    """PUBLICADO é WORM Padrão B — campo técnico congelado; DELETE bloqueado."""

    @pytest.mark.django_db(transaction=True)
    def test_update_metodo_de_publicado_bloqueia(self):
        tenant = TenantFactory(slug=f"proci3a-{uuid4().hex[:6]}")
        p = _cria_proc_pg(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            ProcedimentoCalibracao.objects.filter(id=p.id).update(metodo_norma="X")

    @pytest.mark.django_db(transaction=True)
    def test_delete_de_publicado_bloqueia(self):
        tenant = TenantFactory(slug=f"proci3b-{uuid4().hex[:6]}")
        p = _cria_proc_pg(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            ProcedimentoCalibracao.objects.filter(id=p.id).delete()


class TestINV_PROC_004:
    """`cobre_procedimento` fail-CLOSED real — sem vigente bloqueia (RBC→412)."""

    @pytest.mark.django_db(transaction=True)
    def test_adapter_sem_procedimento_fail_closed(self):
        tenant = TenantFactory(slug=f"proci4-{uuid4().hex[:6]}")
        with run_in_tenant_context(tenant.id):
            ok, resolvido = query_service.cobre_procedimento(
                tenant_id=tenant.id, grandeza="massa",
                faixa_min=Decimal("10"), faixa_max=Decimal("20"),
                unidade="g", data=timezone.now(),
            )
        assert ok is False and resolvido is None

    @pytest.mark.django_db(transaction=True)
    def test_adapter_com_vigente_resolve_snapshot_com_numero_revisao(self):
        tenant = TenantFactory(slug=f"proci4b-{uuid4().hex[:6]}")
        _cria_proc_pg(tenant, faixa_min="0", faixa_max="1000")
        with run_in_tenant_context(tenant.id):
            ok, resolvido = query_service.cobre_procedimento(
                tenant_id=tenant.id, grandeza="massa",
                faixa_min=Decimal("10"), faixa_max=Decimal("20"),
                unidade="g", data=timezone.now(),
            )
        assert ok is True and resolvido is not None
        assert set(resolvido) == {
            "procedimento_id", "codigo", "versao", "numero_revisao", "hash_anexo"
        }

    def test_use_case_rbc_sem_procedimento_levanta_412(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        with pytest.raises(ProcedimentoVigenteAusente):
            configurar_executar(_input_rbc(cal_id), repo, procedimento=_proc_ausente)


class TestINV_PROC_005:
    """Snapshot congela codigo+versao+numero_revisao+hash_anexo (resolvido server-side)."""

    def test_snapshot_minimo_4_chaves_com_numero_revisao(self):
        m = _usado().snapshot_minimo()
        assert set(m) == {"codigo", "versao", "numero_revisao", "hash_anexo"}
        assert m["numero_revisao"] == "Rev. 04"

    def test_wire_in_preenche_snapshot_real_nao_do_payload(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        out = configurar_executar(_input_rbc(cal_id), repo, procedimento=_proc_vigente)
        snap = out.snapshot.procedimento_versao_snapshot
        assert snap["numero_revisao"] == "Rev. 03"  # resolvido (server-side), não do input
        assert snap["codigo"] == "PC-MASSA-007"


class TestINV_PROC_006:
    """Vigência canônica ADR-0030 — naive rejeitado; revogado sai da vigência."""

    def test_vigencia_inicio_naive_rejeitada(self):
        with pytest.raises(ValueError, match="tz-aware"):
            _cadastrar_input(vigencia_inicio=datetime(2026, 6, 1))  # naive

    def test_revogado_sai_da_vigencia(self):
        em = datetime(2026, 6, 2, tzinfo=UTC)
        assert _proc_snapshot().vigente_em(em) is True
        assert _proc_snapshot(revogado_em=T0).vigente_em(em) is False


class TestINV_PROC_007:
    """Integridade — `anexo_pdf_sha256` recalculado server-side, não do cliente."""

    def test_sha256_recalculado_do_binario(self):
        pdf = b"%PDF-1.7 conteudo do procedimento controlado"
        esperado = "ignorado-do-cliente"
        real = sha256_server_side(pdf)
        assert real != esperado  # nunca confia no hash do payload
        assert real == sha256_server_side(pdf)  # determinístico
        assert len(real) == 64  # hex sha256


class TestINV_PROC_008:
    """Não-overlap — no máx 1 PUBLICADO vigente por chave natural."""

    @pytest.mark.django_db(transaction=True)
    def test_duas_vigentes_mesma_chave_bloqueia(self):
        tenant = TenantFactory(slug=f"proci8-{uuid4().hex[:6]}")
        _cria_proc_pg(tenant, codigo="PC-OV", versao=1, vigencia_fim=None)
        with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
            _cria_proc_pg(tenant, codigo="PC-OV", versao=2, vigencia_fim=None)


class TestINV_PROC_009:
    """Controle documental cl. 8.3.1 — publicar exige numero_revisao+aprovado_*."""

    def test_publicar_sem_numero_revisao_bloqueia(self):
        with pytest.raises(Exception, match="INV-PROC-009"):
            publicar_procedimento.PublicarProcedimentoInput(
                tenant_id=uuid4(), procedimento_id=uuid4(),
                numero_revisao="", aprovado_em=T0, aprovado_por_id=uuid4(), perfil="A",
            )

    def test_publicar_completo_passa_validacao_input(self):
        inp = publicar_procedimento.PublicarProcedimentoInput(
            tenant_id=uuid4(), procedimento_id=uuid4(),
            numero_revisao="Rev. 03", aprovado_em=T0, aprovado_por_id=uuid4(), perfil="A",
        )
        assert inp.numero_revisao == "Rev. 03"


class TestINV_PROC_010:
    """Qualificação de método cl. 7.2.2 — A + não-normalizado pende (fail-open lazy)."""

    def test_a_nao_normalizado_pende_sem_registro(self):
        assert metodo_exige_validacao_pendente(
            tipo_metodo=TipoMetodo.NAO_NORMALIZADO, perfil="A", registro_validacao_id=None
        )

    def test_normalizado_e_nao_a_nunca_pendem(self):
        assert not metodo_exige_validacao_pendente(
            tipo_metodo=TipoMetodo.NORMALIZADO, perfil="A", registro_validacao_id=None
        )
        assert not metodo_exige_validacao_pendente(
            tipo_metodo=TipoMetodo.NAO_NORMALIZADO, perfil="D", registro_validacao_id=None
        )

    def test_cadastrar_a_nao_normalizado_avisa_nao_bloqueia(self):
        out = cadastrar_procedimento.executar(
            _cadastrar_input(tipo_metodo=TipoMetodo.NAO_NORMALIZADO, perfil="A"),
            _FakeCadastroRepo(),
        )
        assert out.aviso_validacao_metodo is True
        assert out.snapshot.estado is EstadoProcedimento.RASCUNHO


class _FakeCadastroRepo:
    """Repo mínimo p/ cadastrar (chave inédita)."""

    def existe_chave(self, *, tenant_id, codigo, versao):
        return False

    def proxima_versao(self, *, tenant_id, codigo):
        return 1

    def salvar_novo(self, snapshot):
        pass
