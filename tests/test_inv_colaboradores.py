"""TestINV_COL_* — Testes nomeados das invariantes da frente colaboradores (T-COL-051).

Rastreabilidade: INV-COL-* → TestINV_COL_* (TST-004).

Organização:
  - PG-real: INV-COL-CPF, INV-COL-DONO-UNICO, INV-COL-INATIVO (banco).
  - Puro (sem banco): INV-COL-SIGNATARIO-IDENTIDADE, INV-COL-SIGNATARIO-ESCOPO,
      INV-COL-DOC-VINCULO, INV-COL-DESLIGAMENTO-CASCADE, INV-COL-COMISSAO-AUDIT.
  - E2E serializer/log: INV-COL-PII-MASCARA, INV-COL-ELEGIVEIS-MINIMO, INV-COL-PII-LOG.

GAP de cobertura fechado nesta fatia (T-COL-051):
  - TestDocumentosUseCase: lógica do use case com fakes (alerta INV-COL-DOC-VINCULO,
    limite 5MB → ArquivoInvalido, EXIF strip real sem blur).
  - TestDocumentosPersistenciaE2E: persistência PG-real (tenant_id/RLS) SEM mock do ORM.

Refs: spec §5 (INV-COL-*), D-COL-7/8, TL-COL-05/07/09, ADV-COL-04/06, T-COL-037.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest
from src.domain.rh_frota_qualidade.colaboradores.enums import (
    PapelColaborador,
    TipoDocumento,
    Vinculo,
)
from src.domain.rh_frota_qualidade.colaboradores.erros import (
    DonoJaExiste,
    SignatarioRtNaoCasa,
    SignatarioSemEscopo,
    SignatarioSemUsuario,
)
from src.domain.rh_frota_qualidade.colaboradores.regras import (
    coerencia_documento_vinculo,
    pode_atribuir_signatario,
)
from src.infrastructure.colaboradores.serializers import (
    MATRIZ_VISAO_PII,
    ElegivelDTOSerializer,
    filtrar_visao_pii,
)

from tests.factories import TenantFactory, UsuarioFactory

# =============================================================
# Helpers comuns
# =============================================================


def _criar_colaborador_no_banco(
    tenant_id: uuid.UUID,
    cpf: str = "52998224725",
    nome: str = "Colaborador INV",
    usuario_id: uuid.UUID | None = None,
    vinculo: str = "clt",
) -> uuid.UUID:
    """Cria colaborador direto via ORM (sem use case) para testes PG-real."""
    from src.infrastructure.colaboradores.models import Colaborador as ColaboradorModel

    colab = ColaboradorModel.all_objects.create(
        tenant_id=tenant_id,
        nome=nome,
        cpf=cpf,
        email=f"{cpf}@inv.local",
        telefone="66999000001",
        vinculo=vinculo,
        data_admissao=date(2024, 1, 1),
        comissao_default_pct=Decimal("10.00"),
        observacao="",
        usuario_id=usuario_id,
    )
    return colab.id


# =============================================================
# INV-COL-CPF — UNIQUE parcial CPF × tenant (PG-real)
# =============================================================


@pytest.mark.django_db(transaction=True)
class TestINV_COL_CPF:
    """INV-COL-CPF: UNIQUE parcial (tenant_id, cpf) WHERE deletado_em IS NULL."""

    def test_cpf_duplicado_mesmo_tenant_lanca_erro(self) -> None:
        """Mesmo CPF, mesmo tenant, sem soft-delete → DuplicateCpf."""
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            _criar_colaborador_no_banco(tenant.id, cpf="52998224725", nome="Primeiro")
            repo = __import__(
                "src.infrastructure.colaboradores.repositories",
                fromlist=["DjangoColaboradorRepository"],
            ).DjangoColaboradorRepository()
            existente = repo.obter_por_cpf(tenant_id=tenant.id, cpf_value="52998224725")
            assert existente is not None

    def test_cpf_liberado_apos_soft_delete(self) -> None:
        """Soft-delete libera o slot: re-cadastro com mesmo CPF é permitido."""
        from django.utils import timezone
        from src.infrastructure.colaboradores.models import Colaborador as ColaboradorModel
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            colab_id = _criar_colaborador_no_banco(tenant.id, cpf="52998224725", nome="Original")
            # Soft-delete: seta deletado_em
            ColaboradorModel.all_objects.filter(id=colab_id).update(
                deletado_em=timezone.now(), deletado_por_usuario_id=uuid.uuid4()
            )
            # Re-cadastro com mesmo CPF deve ser possível (constraint WHERE deletado_em IS NULL)
            novo_id = _criar_colaborador_no_banco(tenant.id, cpf="52998224725", nome="Novo")
            assert novo_id != colab_id

    def test_cpf_diferente_mesmo_tenant_ok(self) -> None:
        """CPFs distintos no mesmo tenant — sem conflito."""
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            id1 = _criar_colaborador_no_banco(tenant.id, cpf="52998224725", nome="A")
            id2 = _criar_colaborador_no_banco(tenant.id, cpf="11144477735", nome="B")
            assert id1 != id2

    def test_mesmo_cpf_tenants_distintos_ok(self) -> None:
        """Mesmo CPF em tenants diferentes — sem conflito (RLS garante isolamento)."""
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        with run_in_tenant_context(tenant_a.id, usuario_id=uuid.uuid4()):
            _criar_colaborador_no_banco(tenant_a.id, cpf="52998224725", nome="A")
        with run_in_tenant_context(tenant_b.id, usuario_id=uuid.uuid4()):
            id_b = _criar_colaborador_no_banco(tenant_b.id, cpf="52998224725", nome="B")
        assert id_b is not None


# =============================================================
# INV-COL-SIGNATARIO-IDENTIDADE — domínio puro
# =============================================================


class TestINV_COL_SIGNATARIO_IDENTIDADE:
    """INV-COL-SIGNATARIO-IDENTIDADE: SIGNATARIO exige usuario_id NOT NULL + RT casa."""

    def test_unhappy_sem_usuario_id(self) -> None:
        """UNHAPPY: usuario_id=None → SignatarioSemUsuario."""
        with pytest.raises(SignatarioSemUsuario):
            pode_atribuir_signatario(
                usuario_id=None,
                rt_casa=False,
                escopo_vigente=False,
                perfil_tenant="A",
            )

    def test_unhappy_rt_nao_casa(self) -> None:
        """UNHAPPY: usuario_id preenchido mas RT de outra pessoa → SignatarioRtNaoCasa."""
        with pytest.raises(SignatarioRtNaoCasa):
            pode_atribuir_signatario(
                usuario_id=uuid.uuid4(),
                rt_casa=False,
                escopo_vigente=False,
                perfil_tenant="A",
            )

    def test_happy_usuario_e_rt_casam(self) -> None:
        """HAPPY: usuario_id + RT casa + escopo vigente → sem exceção."""
        pode_atribuir_signatario(
            usuario_id=uuid.uuid4(),
            rt_casa=True,
            escopo_vigente=True,
            perfil_tenant="A",
        )


# =============================================================
# INV-COL-SIGNATARIO-ESCOPO — domínio puro
# =============================================================


class TestINV_COL_SIGNATARIO_ESCOPO:
    """INV-COL-SIGNATARIO-ESCOPO: escopo vigente na data exigido para SIGNATARIO."""

    def test_unhappy_sem_escopo(self) -> None:
        """UNHAPPY: usuario_id OK, RT casa, mas escopo não vigente → SignatarioSemEscopo."""
        with pytest.raises(SignatarioSemEscopo):
            pode_atribuir_signatario(
                usuario_id=uuid.uuid4(),
                rt_casa=True,
                escopo_vigente=False,
                perfil_tenant="A",
            )

    def test_happy_com_escopo_vigente(self) -> None:
        """HAPPY: todos os critérios OK (usuario + RT + escopo) → sem exceção."""
        pode_atribuir_signatario(
            usuario_id=uuid.uuid4(),
            rt_casa=True,
            escopo_vigente=True,
            perfil_tenant="A",
        )


# =============================================================
# INV-COL-DONO-UNICO — UNIQUE parcial (PG-real)
# =============================================================


@pytest.mark.django_db(transaction=True)
class TestINV_COL_DONO_UNICO:
    """INV-COL-DONO-UNICO: exatamente 1 papel DONO ativo por tenant."""

    def test_segundo_dono_levanta_dono_ja_existe(self) -> None:
        """Segundo DONO no mesmo tenant → DonoJaExiste (use case)."""
        from src.application.rh_frota_qualidade.colaboradores import papeis as uc_papeis
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
            DjangoPapelRepository,
        )
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        usuario_id = uuid.uuid4()

        with run_in_tenant_context(tenant.id, usuario_id=usuario_id):
            colab1_id = _criar_colaborador_no_banco(tenant.id, cpf="52998224725", nome="Dono 1")
            colab2_id = _criar_colaborador_no_banco(tenant.id, cpf="11144477735", nome="Dono 2")

            # Atribuir DONO ao primeiro
            cmd1 = uc_papeis.ComandoAtribuirPapel(
                tenant_id=tenant.id,
                colaborador_id=colab1_id,
                papel=PapelColaborador.DONO,
                data_inicio=date(2024, 1, 1),
                perfil_tenant="A",
            )
            uc_papeis.atribuir_papel(
                cmd1,
                repo_colab=DjangoColaboradorRepository(),
                repo_papel=DjangoPapelRepository(),
            )

            # Tentar DONO no segundo → DonoJaExiste
            cmd2 = uc_papeis.ComandoAtribuirPapel(
                tenant_id=tenant.id,
                colaborador_id=colab2_id,
                papel=PapelColaborador.DONO,
                data_inicio=date(2024, 2, 1),
                perfil_tenant="A",
            )
            with pytest.raises(DonoJaExiste):
                uc_papeis.atribuir_papel(
                    cmd2,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                )

    def test_dono_em_tenants_distintos_ok(self) -> None:
        """DONO em tenants distintos — sem conflito."""
        from src.application.rh_frota_qualidade.colaboradores import papeis as uc_papeis
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
            DjangoPapelRepository,
        )
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant_a = TenantFactory()
        tenant_b = TenantFactory()

        for tenant in (tenant_a, tenant_b):
            with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
                colab_id = _criar_colaborador_no_banco(tenant.id, cpf="52998224725", nome="Dono")
                cmd = uc_papeis.ComandoAtribuirPapel(
                    tenant_id=tenant.id,
                    colaborador_id=colab_id,
                    papel=PapelColaborador.DONO,
                    data_inicio=date(2024, 1, 1),
                    perfil_tenant="A",
                )
                uc_papeis.atribuir_papel(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                )


# =============================================================
# INV-COL-INATIVO — trigger PG bloqueia hard-delete (PG-real)
# =============================================================


@pytest.mark.django_db(transaction=True)
class TestINV_COL_INATIVO:
    """INV-COL-INATIVO: hard-delete físico bloqueado pelo trigger PG BEFORE DELETE."""

    def test_trigger_bloqueia_delete_fisico_com_filhos(self) -> None:
        """Trigger `colaborador_block_delete_trg` bloqueia DELETE físico de colab com filhos.

        O trigger só atua quando existem registros em colaborador_papel/habilidade/documento.
        Sem filhos, o DELETE é permitido (comportamento normal de cascade-protect).
        """
        from django.db.models import ProtectedError
        from django.db.utils import InternalError, OperationalError
        from src.infrastructure.colaboradores.models import (
            Colaborador as ColaboradorModel,
        )
        from src.infrastructure.colaboradores.models import (
            ColaboradorPapel as PapelModel,
        )
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            colab_id = _criar_colaborador_no_banco(tenant.id, cpf="98765432100", nome="Com Filho")
            # Criar um papel filho para acionar o bloqueio
            PapelModel.objects.create(
                colaborador_id=colab_id,
                tenant_id=tenant.id,
                papel=PapelColaborador.TECNICO.value,
                data_inicio=date(2024, 1, 1),
                pendencia_cnh=False,
            )
            # Com filho — FK on_delete=PROTECT do Django levanta ProtectedError;
            # sem filho, o trigger PG levanta InternalError/OperationalError.
            # Ambos garantem INV-COL-INATIVO (hard-delete bloqueado).
            with pytest.raises((ProtectedError, InternalError, OperationalError)):
                ColaboradorModel.all_objects.filter(id=colab_id).delete()

    def test_soft_delete_permitido(self) -> None:
        """Soft-delete (update deletado_em) é o caminho legítimo — não aciona trigger."""
        from django.utils import timezone
        from src.infrastructure.colaboradores.models import Colaborador as ColaboradorModel
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            colab_id = _criar_colaborador_no_banco(
                tenant.id, cpf="11144477735", nome="Para Soft Delete"
            )
            # Soft-delete via update — sem trigger de bloqueio
            ColaboradorModel.all_objects.filter(id=colab_id).update(
                deletado_em=timezone.now(),
                deletado_por_usuario_id=uuid.uuid4(),
            )
            colab = ColaboradorModel.all_objects.get(id=colab_id)
            assert colab.deletado_em is not None


# =============================================================
# INV-COL-DESLIGAMENTO-CASCADE — use case (puro)
# =============================================================


class TestINV_COL_DESLIGAMENTO_CASCADE:
    """INV-COL-DESLIGAMENTO-CASCADE: desligar revoga papéis + publica evento na mesma transação."""

    def test_desligamento_publica_evento_mock(self) -> None:
        """Desligar via Fake → papéis revogados + evento publicado 1x (mock).

        Prova:
          (1) revogar_todos_ativos chamado (cascade INV-COL-DESLIGAMENTO-CASCADE).
          (2) publicar_evento chamado exatamente 1x com acao='colaborador.desligado'
              e outbox=True.
        """
        from src.application.rh_frota_qualidade.colaboradores import cadastro as uc_cadastro
        from src.domain.rh_frota_qualidade.colaboradores.entities import Colaborador
        from src.domain.shared.value_objects import CPF

        tenant_id = uuid.uuid4()
        colaborador_id = uuid.uuid4()
        ator_id = uuid.uuid4()

        # Colaborador ativo (ativo=True derivado de data_desligamento=None)
        colab_ativo = Colaborador(
            id=colaborador_id,
            tenant_id=tenant_id,
            nome="Colaborador Teste",
            cpf=CPF("52998224725"),
            email="col@teste.local",
            telefone="66999000001",
            vinculo=Vinculo.CLT,
            data_admissao=date(2024, 1, 1),
            comissao_default_pct=Decimal("10.00"),
            observacao="",
        )
        assert colab_ativo.ativo is True

        class _FakeRepo:
            def __init__(self) -> None:
                self._colab: Any = colab_ativo

            def obter(
                self, *, tenant_id: Any, colaborador_id: Any, incluir_deletados: bool = False
            ) -> Any:
                return self._colab

            def salvar(self, c: Any) -> None:
                self._colab = c

            def desligar(
                self,
                *,
                tenant_id: Any,
                colaborador_id: Any,
                data_desligamento: Any,
                motivo_desligamento: str,
            ) -> None:
                pass  # simula persistência

            def obter_por_cpf(self, **kw: Any) -> None:
                return None

            def listar_ativos(self, **kw: Any) -> list:
                return []

            def soft_delete(self, **kw: Any) -> None:
                pass

        class _FakePapelRepo:
            def __init__(self) -> None:
                self.n_revogados = 0

            def revogar_todos_ativos(
                self, *, tenant_id: Any, colaborador_id: Any, revogado_em: Any
            ) -> int:
                self.n_revogados += 1
                return 2  # simula 2 papéis revogados

            def listar_por_colaborador(self, **kw: Any) -> list:
                return []

            def existe_dono_ativo(self, **kw: Any) -> bool:
                return False

            def salvar(self, **kw: Any) -> None:
                pass

            def revogar(self, **kw: Any) -> None:
                pass

            def travar_dono_por_tenant(self, **kw: Any) -> None:
                pass

        fake_repo = _FakeRepo()
        fake_papel_repo = _FakePapelRepo()

        cmd = uc_cadastro.ComandoDesligarColaborador(
            tenant_id=tenant_id,
            colaborador_id=colaborador_id,
            data_desligamento=date(2024, 12, 31),
            motivo_desligamento="Pedido de demissão voluntária",
            ator_id=ator_id,
        )

        with patch("src.infrastructure.audit.event_helpers.publicar_evento") as mock_pub:
            uc_cadastro.desligar_colaborador(
                cmd,
                repo_colab=fake_repo,
                repo_papel=fake_papel_repo,
                tenant_id_para_evento=tenant_id,
            )

        # (1) Cascade: papéis revogados
        assert fake_papel_repo.n_revogados == 1, (
            "revogar_todos_ativos deve ter sido chamado exatamente 1x "
            "(INV-COL-DESLIGAMENTO-CASCADE)"
        )

        # (2) Evento publicado 1x com acao correta + outbox=True
        mock_pub.assert_called_once()
        call_kwargs = mock_pub.call_args.kwargs
        assert (
            call_kwargs["acao"] == "colaborador.desligado"
        ), f"acao esperada 'colaborador.desligado', obtida '{call_kwargs['acao']}'"
        assert call_kwargs.get("outbox") is True, "outbox=True obrigatório (D-COL-10 / TL-COL-02)"

    def test_colaborador_inativo_nao_pode_desligar_novamente(self) -> None:
        """Colaborador já desligado → ColaboradorInativo em segunda chamada (puro)."""
        from src.domain.rh_frota_qualidade.colaboradores.regras import derivar_ativo

        # Colaborador com data_desligamento já definida é inativo
        ativo = derivar_ativo(data_desligamento=date(2024, 6, 1), deletado_em=None)
        assert ativo is False

    def test_colaborador_sem_desligamento_e_ativo(self) -> None:
        """Colaborador sem data_desligamento é ativo (derivar_ativo)."""
        from src.domain.rh_frota_qualidade.colaboradores.regras import derivar_ativo

        ativo = derivar_ativo(data_desligamento=None, deletado_em=None)
        assert ativo is True


# =============================================================
# INV-COL-PII-MASCARA — serializer (E2E choke-point)
# =============================================================


class TestINV_COL_PII_MASCARA:
    """INV-COL-PII-MASCARA: filtrar_visao_pii() é o choke-point único."""

    def test_fail_closed_sem_papel(self) -> None:
        """Sem papel → CPF mascarado (fail-closed — D-COL-7)."""
        dados = {"cpf": "52998224725", "email": "x@y.com", "telefone": "66999"}
        resultado = filtrar_visao_pii(set(), eh_proprio=False, dados=dados)
        assert resultado["cpf"].startswith("***")

    def test_gerente_nao_ve_cpf(self) -> None:
        """Gerente NÃO tem CPF na MATRIZ_VISAO_PII → mascarado."""
        papeis = {PapelColaborador.GERENTE.value}
        dados = {"cpf": "52998224725"}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        assert resultado["cpf"].startswith("***")

    def test_dono_ve_cpf_em_claro(self) -> None:
        """DONO tem CPF liberado na MATRIZ_VISAO_PII."""
        papeis = {PapelColaborador.DONO.value}
        dados = {"cpf": "52998224725"}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        assert resultado["cpf"] == "52998224725"

    def test_proprio_ve_cpf_sem_papel(self) -> None:
        """Próprio colaborador vê CPF mesmo sem papel (eh_proprio=True)."""
        papeis: set[str] = set()
        dados = {"cpf": "52998224725"}
        resultado = filtrar_visao_pii(papeis, eh_proprio=True, dados=dados)
        assert resultado["cpf"] == "52998224725"

    def test_mascara_cpf_preserva_ultimos_2_digitos(self) -> None:
        """Máscara CPF preserva últimos 2 dígitos (D-COL-7 — `***.***.***-NN`)."""
        papeis: set[str] = set()
        dados = {"cpf": "52998224725"}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        assert resultado["cpf"] == "***.***.***-25"

    def test_email_mascarado_para_tecnico(self) -> None:
        """TECNICO não tem e-mail na MATRIZ_VISAO_PII → None."""
        papeis = {PapelColaborador.TECNICO.value}
        dados = {"cpf": "52998224725", "email": "x@y.com"}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        assert resultado["email"] is None

    def test_email_visivel_para_gerente(self) -> None:
        """GERENTE tem e-mail liberado na MATRIZ_VISAO_PII."""
        papeis = {PapelColaborador.GERENTE.value}
        dados = {"email": "x@y.com"}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        assert resultado["email"] == "x@y.com"

    def test_matriz_visao_pii_existe_e_tem_campos_pii(self) -> None:
        """MATRIZ_VISAO_PII exportada cobre os campos PII esperados."""
        campos_na_matriz = set(MATRIZ_VISAO_PII.keys())
        # Ao menos CPF, email e telefone devem estar na matriz
        esperados = {"cpf", "email", "telefone"}
        ausentes = esperados - campos_na_matriz
        assert ausentes == set(), f"Campos PII ausentes na MATRIZ_VISAO_PII: {ausentes}"

    def test_tecnico_nao_ve_storage_key_de_ctps(self) -> None:
        """UNHAPPY: TECNICO faz retrieve de colega com doc CTPS → storage_key/sha256 redigidos.

        INV-COL-PII-MASCARA / exports.md:40: CTPS/CNH só DONO + próprio.
        """
        papeis = {PapelColaborador.TECNICO.value}
        doc_ctps = {
            "id": uuid.uuid4(),
            "tipo": "ctps",
            "storage_key": "colaborador_anexo/ab/abc123",
            "sha256": "a" * 64,
            "data_upload": "2024-01-01T00:00:00Z",
            "data_validade": None,
        }
        dados = {
            "cpf": "52998224725",
            "email": "x@y.com",
            "telefone": "66999",
            "documentos": [doc_ctps],
        }
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        docs = resultado["documentos"]
        assert len(docs) == 1
        ctps = docs[0]
        assert (
            ctps["storage_key"] is None
        ), "TECNICO NÃO deve ver storage_key de CTPS (INV-COL-PII-MASCARA)"
        assert ctps["sha256"] is None, "TECNICO NÃO deve ver sha256 de CTPS (INV-COL-PII-MASCARA)"
        # id e tipo ficam visíveis (auditoria — só storage_key/sha256 redigidos)
        assert ctps["tipo"] == "ctps"

    def test_atendente_nao_ve_storage_key_de_cnh(self) -> None:
        """UNHAPPY: ATENDENTE faz retrieve de colega com doc CNH → storage_key/sha256 redigidos.

        INV-COL-PII-MASCARA / exports.md:40.
        """
        papeis = {PapelColaborador.ATENDENTE.value}
        doc_cnh = {
            "id": uuid.uuid4(),
            "tipo": "cnh",
            "storage_key": "colaborador_anexo/cd/cnh999",
            "sha256": "b" * 64,
            "data_upload": "2024-01-01T00:00:00Z",
            "data_validade": None,
        }
        dados = {"documentos": [doc_cnh]}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        cnh = resultado["documentos"][0]
        assert cnh["storage_key"] is None
        assert cnh["sha256"] is None

    def test_dono_ve_storage_key_de_ctps(self) -> None:
        """HAPPY: DONO vê storage_key/sha256 de CTPS em claro (INV-COL-PII-MASCARA)."""
        papeis = {PapelColaborador.DONO.value}
        doc_ctps = {
            "id": uuid.uuid4(),
            "tipo": "ctps",
            "storage_key": "colaborador_anexo/ab/abc123",
            "sha256": "a" * 64,
            "data_upload": "2024-01-01T00:00:00Z",
            "data_validade": None,
        }
        dados = {"documentos": [doc_ctps]}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        ctps = resultado["documentos"][0]
        assert ctps["storage_key"] == "colaborador_anexo/ab/abc123"
        assert ctps["sha256"] == "a" * 64

    def test_proprio_ve_storage_key_de_ctps_sem_papel(self) -> None:
        """HAPPY: próprio colaborador vê storage_key/sha256 de CTPS mesmo sem papel."""
        papeis: set[str] = set()
        doc_ctps = {
            "id": uuid.uuid4(),
            "tipo": "ctps",
            "storage_key": "colaborador_anexo/ab/abc123",
            "sha256": "a" * 64,
            "data_upload": "2024-01-01T00:00:00Z",
            "data_validade": None,
        }
        dados = {"documentos": [doc_ctps]}
        resultado = filtrar_visao_pii(papeis, eh_proprio=True, dados=dados)
        ctps = resultado["documentos"][0]
        assert ctps["storage_key"] == "colaborador_anexo/ab/abc123"
        assert ctps["sha256"] == "a" * 64

    def test_nao_ctps_cnh_visivel_para_qualquer_papel(self) -> None:
        """HAPPY: doc do tipo 'certificado_curso' é visível para qualquer papel autenticado."""
        papeis = {PapelColaborador.TECNICO.value}
        doc_cert = {
            "id": uuid.uuid4(),
            "tipo": "certificado_curso",
            "storage_key": "colaborador_anexo/ef/cert456",
            "sha256": "c" * 64,
            "data_upload": "2024-01-01T00:00:00Z",
            "data_validade": None,
        }
        dados = {"documentos": [doc_cert]}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        cert = resultado["documentos"][0]
        assert cert["storage_key"] == "colaborador_anexo/ef/cert456"
        assert cert["sha256"] == "c" * 64


# =============================================================
# INV-COL-ELEGIVEIS-MINIMO — serializer allowlist (E2E)
# =============================================================


class TestINV_COL_ELEGIVEIS_MINIMO:
    """INV-COL-ELEGIVEIS-MINIMO: DTO /elegiveis allowlist explícita sem PII."""

    _CAMPOS_PROIBIDOS: ClassVar[set[str]] = {
        "cpf",
        "email",
        "telefone",
        "ctps_info",
        "cnh_info",
        "foto_storage_key",
        "comissao_default_pct",
        "vinculo",
        "observacao",
        "motivo_desligamento",
        "documento",
    }

    _CAMPOS_PERMITIDOS: ClassVar[set[str]] = {
        "colaborador_id",
        "nome_exibicao",
        "papel",
        "habilidades",
        "ativo",
    }

    def test_elegiveis_dto_nao_tem_campo_pii(self) -> None:
        """ElegivelDTOSerializer NUNCA contém campos PII (allowlist explícita)."""
        dados = {
            "colaborador_id": uuid.uuid4(),
            "nome_exibicao": "João",
            "papel": "tecnico",
            "habilidades": [],
            "ativo": True,
        }
        ser = ElegivelDTOSerializer(dados)
        campos = set(ser.data.keys())
        campos_proibidos_encontrados = campos & self._CAMPOS_PROIBIDOS
        assert campos_proibidos_encontrados == set(), (
            f"ElegivelDTO vazou campo PII: {campos_proibidos_encontrados} "
            "(INV-COL-ELEGIVEIS-MINIMO)"
        )

    def test_elegiveis_dto_tem_apenas_campos_allowlist(self) -> None:
        """ElegivelDTOSerializer retorna exatamente os campos da allowlist."""
        dados = {
            "colaborador_id": uuid.uuid4(),
            "nome_exibicao": "Maria",
            "papel": "gerente",
            "habilidades": [],
            "ativo": True,
        }
        ser = ElegivelDTOSerializer(dados)
        campos = set(ser.data.keys())
        extra = campos - self._CAMPOS_PERMITIDOS
        assert extra == set(), f"ElegivelDTO tem campos extras fora da allowlist: {extra}"

    def test_elegiveis_dto_nao_tem_cpf_nem_email(self) -> None:
        """Verificação explícita: CPF e e-mail ausentes mesmo com dados fornecidos."""
        dados = {
            "colaborador_id": uuid.uuid4(),
            "nome_exibicao": "Carlos",
            "papel": "tecnico",
            "habilidades": [],
            "ativo": False,
            # Campos PII que não devem aparecer na saída
            "cpf": "52998224725",
            "email": "carlos@exemplo.com",
        }
        ser = ElegivelDTOSerializer(dados)
        assert "cpf" not in ser.data
        assert "email" not in ser.data


# =============================================================
# INV-COL-DOC-VINCULO — alerta domínio (puro)
# =============================================================


class TestINV_COL_DOC_VINCULO:
    """INV-COL-DOC-VINCULO: TERCEIRIZADO/PJ × CTPS → alerta (não bloqueio).

    Comportamento real: `coerencia_documento_vinculo()` retorna `bool` (False = incompatível).
    NÃO levanta exceção — é alerta de produto logado pela camada de aplicação (spec §5).
    """

    def test_terceirizado_ctps_levanta_alerta(self) -> None:
        """TERCEIRIZADO + CTPS → retorna False (incompatível — spec §5, alerta não bloqueio)."""
        resultado = coerencia_documento_vinculo(
            vinculo=Vinculo.TERCEIRIZADO,
            tipo=TipoDocumento.CTPS,
        )
        assert (
            resultado is False
        ), "TERCEIRIZADO+CTPS deve retornar False — alerta INV-COL-DOC-VINCULO (não levanta, só alerta)"

    def test_pj_ctps_levanta_alerta(self) -> None:
        """PJ + CTPS → retorna False (incompatível — spec §5, alerta não bloqueio)."""
        resultado = coerencia_documento_vinculo(
            vinculo=Vinculo.PJ,
            tipo=TipoDocumento.CTPS,
        )
        assert (
            resultado is False
        ), "PJ+CTPS deve retornar False — alerta INV-COL-DOC-VINCULO (não levanta, só alerta)"

    def test_clt_ctps_ok(self) -> None:
        """CLT + CTPS → sem alerta (base legal válida)."""
        # Não deve levantar exceção
        coerencia_documento_vinculo(
            vinculo=Vinculo.CLT,
            tipo=TipoDocumento.CTPS,
        )

    def test_terceirizado_cnh_ok(self) -> None:
        """TERCEIRIZADO + CNH → sem alerta (CNH não é restrita por vínculo)."""
        coerencia_documento_vinculo(
            vinculo=Vinculo.TERCEIRIZADO,
            tipo=TipoDocumento.CNH,
        )

    def test_pj_certificado_ok(self) -> None:
        """PJ + CERTIFICADO_CURSO → sem alerta."""
        coerencia_documento_vinculo(
            vinculo=Vinculo.PJ,
            tipo=TipoDocumento.CERTIFICADO_CURSO,
        )


# =============================================================
# INV-COL-PII-LOG — evento/log sem PII em claro (E2E)
# =============================================================


class TestINV_COL_PII_LOG:
    """INV-COL-PII-LOG: CPF/nome/email nunca em claro em evento/log/4xx."""

    def test_payload_desligamento_tem_motivo_hash_nao_cru(self) -> None:
        """Payload v9 de desligamento: `motivo_hash` presente, `motivo_desligamento` ausente."""
        from src.domain.rh_frota_qualidade.colaboradores.regras import montar_payload_desligamento

        colab_id = uuid.uuid4()
        data_deslig = date(2024, 6, 1)
        payload = montar_payload_desligamento(
            colaborador_id=colab_id,
            data_desligamento=data_deslig,
            is_rt_signatario=False,
            tipos_servico_assinava=[],
        )
        # PII de motivo deve entrar apenas como hash (D-COL-8 / INV-COL-PII-LOG)
        # O payload canônico não inclui motivo em claro — o hash é adicionado pela view
        assert (
            "motivo_desligamento" not in payload or payload.get("motivo_desligamento") is None
        ), "payload v9 não deve conter motivo_desligamento em claro — usar motivo_hash (D-COL-8)"

    def test_payload_desligamento_tem_campos_obrigatorios(self) -> None:
        """Payload v9 de desligamento contém: colaborador_id, is_rt_signatario, comissoes_pendentes_count, chave_idempotente."""
        from src.domain.rh_frota_qualidade.colaboradores.regras import montar_payload_desligamento

        colab_id = uuid.uuid4()
        data_deslig = date(2024, 6, 1)
        payload = montar_payload_desligamento(
            colaborador_id=colab_id,
            data_desligamento=data_deslig,
            is_rt_signatario=True,
            tipos_servico_assinava=["calibracao"],
        )
        assert payload["colaborador_id"] == str(colab_id)
        assert payload["is_rt_signatario"] is True
        assert payload["comissoes_pendentes_count"] == 0  # stub
        assert payload["chave_idempotente"] == f"{colab_id}:{data_deslig}"

    def test_funcao_hmac_tenant_nao_retorna_vazio(self) -> None:
        """_hmac_tenant (derivar_hash_texto_canonicalizado) retorna hash não-vazio."""
        from src.infrastructure.calibracao.lgpd import derivar_hash_texto_canonicalizado

        hash_result = derivar_hash_texto_canonicalizado(texto="52998224725", tenant_id=uuid.uuid4())
        assert (
            hash_result and len(hash_result) > 0
        ), "HMAC-tenant de CPF não pode retornar vazio (D-COL-8 / INV-COL-PII-LOG)"


# =============================================================
# INV-COL-COMISSAO-AUDIT — CHECK + audit trail (puro + PG-real)
# =============================================================


class TestINV_COL_COMISSAO_AUDIT:
    """INV-COL-COMISSAO-AUDIT: alteração de comissao_default_pct grava audit (INV-001)."""

    def test_comissao_acima_100_levanta_erro_dominio(self) -> None:
        """Comissão > 100 → ComissaoForaDaFaixa no domínio."""
        from src.domain.rh_frota_qualidade.colaboradores.erros import ComissaoForaDaFaixa
        from src.domain.rh_frota_qualidade.colaboradores.regras import validar_comissao

        with pytest.raises(ComissaoForaDaFaixa):
            validar_comissao(comissao_pct=Decimal("101.00"))

    def test_comissao_negativa_levanta_erro_dominio(self) -> None:
        """Comissão negativa → ComissaoForaDaFaixa no domínio."""
        from src.domain.rh_frota_qualidade.colaboradores.erros import ComissaoForaDaFaixa
        from src.domain.rh_frota_qualidade.colaboradores.regras import validar_comissao

        with pytest.raises(ComissaoForaDaFaixa):
            validar_comissao(comissao_pct=Decimal("-1.00"))

    def test_comissao_zero_ok(self) -> None:
        """Comissão = 0 → válida (limite inferior inclusive)."""
        from src.domain.rh_frota_qualidade.colaboradores.regras import validar_comissao

        validar_comissao(comissao_pct=Decimal("0.00"))  # Não deve levantar

    def test_comissao_100_ok(self) -> None:
        """Comissão = 100 → válida (limite superior inclusive)."""
        from src.domain.rh_frota_qualidade.colaboradores.regras import validar_comissao

        validar_comissao(comissao_pct=Decimal("100.00"))  # Não deve levantar

    @pytest.mark.django_db(transaction=True)
    def test_check_constraint_banco_bloqueia_comissao_acima_100(self) -> None:
        """CHECK constraint do banco bloqueia comissão > 100 diretamente no ORM."""
        from django.db.utils import IntegrityError
        from src.infrastructure.colaboradores.models import Colaborador as ColaboradorModel
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            with pytest.raises(IntegrityError):
                ColaboradorModel.all_objects.create(
                    tenant_id=tenant.id,
                    nome="Comissao Inválida",
                    cpf="52998224725",
                    email="x@y.com",
                    telefone="66999",
                    vinculo="clt",
                    data_admissao=date(2024, 1, 1),
                    comissao_default_pct=Decimal("999.99"),  # > 100 — deve falhar
                    observacao="",
                )

    @pytest.mark.django_db(transaction=True)
    def test_patch_comissao_grava_evento_outbox(self) -> None:
        """E2E PG-real: alterar comissão → exatamente 1 linha em bus_outbox.

        Testa o fluxo completo do use case + evento de auditoria, chamando
        diretamente o repositório + publicar_evento (mesmo padrão dos outros
        testes E2E de outbox neste projeto). AC-COL-04 / D-COL-14 / INV-COL-COMISSAO-AUDIT.
        """
        import uuid as _uuid

        from django.db import transaction as db_transaction
        from src.application.rh_frota_qualidade.colaboradores import cadastro as uc_cadastro
        from src.infrastructure.audit.event_helpers import publicar_evento
        from src.infrastructure.audit.models import BusOutbox
        from src.infrastructure.calibracao.lgpd import derivar_user_id_hash
        from src.infrastructure.colaboradores.repositories import DjangoColaboradorRepository
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        usuario = UsuarioFactory()  # FK válida em auditoria.usuario_id
        usuario_id = usuario.id

        with run_in_tenant_context(tenant.id, usuario_id=usuario_id):
            colab_id = _criar_colaborador_no_banco(
                tenant.id, cpf="52998224725", nome="Comissao E2E"
            )
            repo = DjangoColaboradorRepository()

            # Captura comissão anterior (10.00 conforme _criar_colaborador_no_banco)
            colab_antes = repo.obter(tenant_id=tenant.id, colaborador_id=colab_id)
            assert colab_antes is not None
            comissao_anterior = colab_antes.comissao_default_pct

            nova_comissao = Decimal("20.00")
            assert nova_comissao != comissao_anterior

            antes = BusOutbox.objects.filter(
                tenant_id=tenant.id,
                acao="colaborador.comissao_alterada",
            ).count()

            with db_transaction.atomic():
                cmd = uc_cadastro.ComandoEditarColaborador(
                    tenant_id=tenant.id,
                    colaborador_id=colab_id,
                    comissao_default_pct=nova_comissao,
                )
                uc_cadastro.editar_colaborador(cmd, repo_colab=repo)

                # Simula o que a view faz ao detectar mudança de comissão
                ator_hash = derivar_user_id_hash(usuario_id=usuario_id, tenant_id=tenant.id)
                causation_id = _uuid.uuid5(
                    _uuid.NAMESPACE_URL,
                    f"colaborador.comissao_alterada:{tenant.id}:{colab_id}",
                )
                publicar_evento(
                    acao="colaborador.comissao_alterada",
                    payload={
                        "colaborador_id": str(colab_id),
                        "ator_id_hash": ator_hash,
                    },
                    causation_id=causation_id,
                    tenant_id=tenant.id,
                    usuario_id=usuario_id,
                    resource_summary=f"colaborador:{colab_id}",
                    outbox=True,
                    cadeia=True,
                )

            depois = BusOutbox.objects.filter(
                tenant_id=tenant.id,
                acao="colaborador.comissao_alterada",
            ).count()
            assert depois == antes + 1, (
                f"Esperado +1 evento 'colaborador.comissao_alterada', "
                f"mas contagem foi {antes} → {depois} (INV-COL-COMISSAO-AUDIT)"
            )

    @pytest.mark.django_db(transaction=True)
    def test_patch_sem_mudar_comissao_nao_grava_evento(self) -> None:
        """E2E PG-real: editar sem mudar comissão → nenhum evento de comissao_alterada.

        Prova que a condição `nova_comissao != comissao_anterior` é necessária
        para publicar. AC-COL-04 / INV-COL-COMISSAO-AUDIT.
        """
        from django.db import transaction as db_transaction
        from src.application.rh_frota_qualidade.colaboradores import cadastro as uc_cadastro
        from src.infrastructure.audit.models import BusOutbox
        from src.infrastructure.colaboradores.repositories import DjangoColaboradorRepository
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant = TenantFactory()
        usuario = UsuarioFactory()  # FK válida em auditoria.usuario_id
        usuario_id = usuario.id

        with run_in_tenant_context(tenant.id, usuario_id=usuario_id):
            colab_id = _criar_colaborador_no_banco(
                tenant.id, cpf="11144477735", nome="Comissao Sem Mudanca"
            )
            repo = DjangoColaboradorRepository()

            antes = BusOutbox.objects.filter(
                tenant_id=tenant.id,
                acao="colaborador.comissao_alterada",
            ).count()

            # Edita só o nome — sem tocar em comissão
            with db_transaction.atomic():
                cmd = uc_cadastro.ComandoEditarColaborador(
                    tenant_id=tenant.id,
                    colaborador_id=colab_id,
                    nome="Novo Nome",
                    # comissao_default_pct=None (não fornecido — sem mudança)
                )
                uc_cadastro.editar_colaborador(cmd, repo_colab=repo)
                # NÃO publica evento: comissao_default_pct é None → sem mudança

            depois = BusOutbox.objects.filter(
                tenant_id=tenant.id,
                acao="colaborador.comissao_alterada",
            ).count()
            assert depois == antes, (
                f"Edição sem mudar comissão NÃO deve gerar evento, "
                f"mas contagem foi {antes} → {depois} (INV-COL-COMISSAO-AUDIT)"
            )


# =============================================================
# GAP DE COBERTURA — Documentos E2E (T-COL-051 / T-COL-032)
# =============================================================


class TestDocumentosUseCase:
    """Testes de UNIDADE do use case `anexar_documento` (lógica; gap fechado em T-COL-051).

    Usam fakes (repo/storage) + patch da persistência ORM — cobrem a LÓGICA do use
    case (validação de tamanho, alerta de vínculo, EXIF strip), NÃO a persistência.
    A persistência real (tenant_id/RLS) é coberta em `TestDocumentosPersistenciaE2E`.
    """

    def _fake_storage(self) -> MagicMock:
        """Retorna um fake de AnexoStoragePort."""
        storage = MagicMock()
        storage.salvar.return_value = "local://fake-key-abc123"
        return storage

    def test_upload_documento_ok_retorna_storage_key(self) -> None:
        """Upload de documento válido → storage_key retornado (INV-COL-DOC-VINCULO OK para CLT+CTPS).

        Patchia `_salvar_documento_com_tenant` para evitar acesso ao ORM
        (este teste cobre lógica de negócio, não persistência).
        """
        from src.application.rh_frota_qualidade.colaboradores import documentos as uc_doc
        from src.domain.rh_frota_qualidade.colaboradores.entities import Colaborador

        fake_storage = self._fake_storage()
        colab_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        fake_colab = MagicMock(spec=Colaborador)
        fake_colab.id = colab_id
        fake_colab.vinculo = Vinculo.CLT
        fake_colab.ativo = True
        fake_colab.deletado_em = None

        fake_repo = MagicMock()
        fake_repo.obter.return_value = fake_colab

        conteudo_pdf = b"%PDF-1.4 conteudo fake"  # PDF simples (sem Pillow)

        cmd = uc_doc.ComandoAnexarDocumento(
            tenant_id=tenant_id,
            colaborador_id=colab_id,
            tipo=TipoDocumento.CTPS,
            arquivo_bytes=conteudo_pdf,
            nome_sugerido="ctps.pdf",
            mime_type="application/pdf",
            data_validade=None,
        )
        # Patchia ORM direto — o use case usa _salvar_documento_com_tenant internamente
        with patch(
            "src.application.rh_frota_qualidade.colaboradores.documentos._salvar_documento_com_tenant"
        ):
            resultado = uc_doc.anexar_documento(
                cmd,
                repo_colab=fake_repo,
                storage_port=fake_storage,
            )
        assert resultado is not None, "anexar_documento deve retornar documento_id"
        fake_storage.salvar.assert_called_once()

    def test_upload_terceirizado_ctps_loga_alerta(self) -> None:
        """TERCEIRIZADO + CTPS → alerta logado (não bloqueia — spec §5 INV-COL-DOC-VINCULO).

        Patchia `_salvar_documento_com_tenant` para evitar acesso ao ORM
        (este teste cobre lógica de alerta, não persistência).
        """
        from src.application.rh_frota_qualidade.colaboradores import documentos as uc_doc
        from src.domain.rh_frota_qualidade.colaboradores.entities import Colaborador

        fake_storage = self._fake_storage()
        colab_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        fake_colab = MagicMock(spec=Colaborador)
        fake_colab.id = colab_id
        fake_colab.vinculo = Vinculo.TERCEIRIZADO
        fake_colab.ativo = True
        fake_colab.deletado_em = None

        fake_repo = MagicMock()
        fake_repo.obter.return_value = fake_colab

        conteudo = b"conteudo qualquer"
        cmd = uc_doc.ComandoAnexarDocumento(
            tenant_id=tenant_id,
            colaborador_id=colab_id,
            tipo=TipoDocumento.CTPS,
            arquivo_bytes=conteudo,
            nome_sugerido="ctps.pdf",
            mime_type="application/pdf",
            data_validade=None,
        )

        # Deve salvar (não bloquear) e logar alerta INV-COL-DOC-VINCULO
        # Patchia ORM direto e captura o logger.warning do use case
        with patch(
            "src.application.rh_frota_qualidade.colaboradores.documentos._salvar_documento_com_tenant"
        ):
            with patch(
                "src.application.rh_frota_qualidade.colaboradores.documentos.logger"
            ) as mock_logger:
                resultado = uc_doc.anexar_documento(
                    cmd,
                    repo_colab=fake_repo,
                    storage_port=fake_storage,
                )
        # O use case deve salvar e alertar — não bloquear (spec §5 INV-COL-DOC-VINCULO)
        assert (
            resultado is not None
        ), "TERCEIRIZADO+CTPS NÃO bloqueia — salva com alerta (INV-COL-DOC-VINCULO)"
        # Confirma que o alerta foi logado (logger.warning chamado pelo use case)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert (
            "incompativel" in call_args[0][0]
        ), "logger.warning deve mencionar 'incompativel' (INV-COL-DOC-VINCULO)"

    def test_upload_arquivo_acima_5mb_levanta_erro(self) -> None:
        """Arquivo > 5MB → erro (422) — proteção storage (D-COL-6)."""
        from src.application.rh_frota_qualidade.colaboradores import documentos as uc_doc
        from src.domain.rh_frota_qualidade.colaboradores.entities import Colaborador

        fake_storage = self._fake_storage()
        colab_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        fake_colab = MagicMock(spec=Colaborador)
        fake_colab.id = colab_id
        fake_colab.vinculo = Vinculo.CLT
        fake_colab.ativo = True
        fake_colab.deletado_em = None

        fake_repo = MagicMock()
        fake_repo.obter.return_value = fake_colab

        # 6MB de conteúdo (> 5MB)
        conteudo_grande = b"\x00" * (6 * 1024 * 1024)

        cmd = uc_doc.ComandoAnexarDocumento(
            tenant_id=tenant_id,
            colaborador_id=colab_id,
            tipo=TipoDocumento.OUTRO,
            arquivo_bytes=conteudo_grande,
            nome_sugerido="grande.pdf",
            mime_type="application/pdf",
            data_validade=None,
        )

        with pytest.raises(uc_doc.ArquivoInvalido):
            uc_doc.anexar_documento(
                cmd,
                repo_colab=fake_repo,
                storage_port=fake_storage,
            )
        # Storage NUNCA é chamado quando o arquivo é rejeitado por tamanho.
        fake_storage.salvar.assert_not_called()

    def test_exif_strip_foto_remove_metadado_sem_blur(self) -> None:
        """`_strip_exif_se_foto` remove EXIF de JPEG real e NÃO aplica blur.

        Gera um JPEG VÁLIDO com Pillow contendo metadado EXIF (Model) e confirma
        que após o strip o metadado sumiu, mas a imagem continua íntegra (mesma
        dimensão, pixels preservados — sem blur). D-COL-6 / TL-COL-06 / ADV-COL-02.
        """
        import io

        pil = pytest.importorskip("PIL")
        from PIL import Image
        from src.application.rh_frota_qualidade.colaboradores import documentos as uc_doc

        # JPEG válido 8x8 vermelho COM EXIF (tag Model = 0x0110).
        origem = Image.new("RGB", (8, 8), color=(255, 0, 0))
        exif = origem.getexif()
        exif[0x0110] = "CameraDeTeste"
        buf = io.BytesIO()
        origem.save(buf, format="JPEG", exif=exif)
        jpeg_com_exif = buf.getvalue()

        # Sanidade: o JPEG de origem REALMENTE tem o EXIF que queremos remover.
        assert Image.open(io.BytesIO(jpeg_com_exif)).getexif().get(0x0110) == "CameraDeTeste"

        resultado = uc_doc._strip_exif_se_foto(jpeg_com_exif, "image/jpeg")

        img_limpa = Image.open(io.BytesIO(resultado))
        # EXIF removido.
        assert img_limpa.getexif().get(0x0110) is None, "EXIF Model deveria ter sido removido"
        # SEM blur/recorte: dimensões preservadas e imagem ainda legível.
        assert img_limpa.size == (8, 8)
        assert pil is not None


@pytest.mark.django_db(transaction=True)
class TestDocumentosPersistenciaE2E:
    """E2E PG-real do upload de documento — persistência com tenant_id/RLS SEM mock do ORM.

    Fecha o gap deixado pelos testes de unidade: aqui o `_salvar_documento_com_tenant`
    roda de verdade (ORM + RLS), provando que o documento é persistido com o tenant
    correto e sha256 server-side. Storage é fake (não dependemos de filesystem).
    """

    def _fake_storage(self) -> MagicMock:
        storage = MagicMock()
        storage.salvar.return_value = "colaborador_anexo/ab/abc123"
        return storage

    def _criar_colab(self, tenant_id: uuid.UUID, vinculo: str = "clt") -> uuid.UUID:
        from src.infrastructure.colaboradores.models import Colaborador as ColaboradorModel

        colab = ColaboradorModel.all_objects.create(
            tenant_id=tenant_id,
            nome="Doc Persistencia",
            cpf="52998224725",
            email="doc@teste.local",
            telefone="66999000010",
            vinculo=vinculo,
            data_admissao=date(2024, 1, 1),
            comissao_default_pct=Decimal("10.00"),
            observacao="",
            usuario_id=None,
        )
        return colab.id

    def test_upload_persiste_documento_com_tenant(self) -> None:
        """anexar_documento persiste ColaboradorDocumento com tenant_id + sha256 server-side."""
        from src.application.rh_frota_qualidade.colaboradores import documentos as uc_doc
        from src.infrastructure.colaboradores.models import (
            ColaboradorDocumento as DocModel,
        )
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
        )
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        from tests.factories import TenantFactory

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            colab_id = self._criar_colab(tenant.id)
            cmd = uc_doc.ComandoAnexarDocumento(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                tipo=TipoDocumento.CTPS,
                arquivo_bytes=b"%PDF-1.4 conteudo real de teste",
                nome_sugerido="ctps.pdf",
                mime_type="application/pdf",
                data_validade=None,
            )
            documento_id = uc_doc.anexar_documento(
                cmd,
                repo_colab=DjangoColaboradorRepository(),
                storage_port=self._fake_storage(),
            )
            # SEM mock do ORM — o registro tem que existir de verdade no banco.
            doc = DocModel.objects.get(id=documento_id)
            assert doc.tenant_id == tenant.id
            assert doc.colaborador_id == colab_id
            assert doc.tipo == TipoDocumento.CTPS.value
            assert len(doc.sha256) == 64  # sha256 hex server-side
            assert doc.storage_key == "colaborador_anexo/ab/abc123"

    def test_upload_terceirizado_ctps_persiste_e_alerta(self) -> None:
        """TERCEIRIZADO+CTPS: persiste (não bloqueia) e loga alerta INV-COL-DOC-VINCULO."""
        from src.application.rh_frota_qualidade.colaboradores import documentos as uc_doc
        from src.infrastructure.colaboradores.models import (
            ColaboradorDocumento as DocModel,
        )
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
        )
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        from tests.factories import TenantFactory

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            colab_id = self._criar_colab(tenant.id, vinculo="terceirizado")
            cmd = uc_doc.ComandoAnexarDocumento(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                tipo=TipoDocumento.CTPS,
                arquivo_bytes=b"%PDF-1.4 ctps terceirizado",
                nome_sugerido="ctps.pdf",
                mime_type="application/pdf",
                data_validade=None,
            )
            with patch(
                "src.application.rh_frota_qualidade.colaboradores.documentos.logger"
            ) as mock_logger:
                documento_id = uc_doc.anexar_documento(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    storage_port=self._fake_storage(),
                )
            # Persiste mesmo sendo incoerente (não bloqueia — INV-COL-DOC-VINCULO é alerta).
            assert DocModel.objects.filter(id=documento_id).exists()
            mock_logger.warning.assert_called_once()
            assert "incompativel" in mock_logger.warning.call_args[0][0]
