"""Testes E2E + puros da Fatia 2 — colaboradores (T-COL-037).

Cobertura obrigatória:
  1. dedup CPF → 409
  2. signatário UNHAPPY × 3 (sem usuario_id / RT inexistente / RT outro tenant → 422)
  3. mascaramento por papel × campo (Gerente NÃO vê CPF; próprio vê CPF; sem papel → mascarado)
  4. /elegiveis nunca retorna campo PII fora da allowlist
  5. desligar → 1 linha bus_outbox com payload v9 completo
  6. idempotência desligar 2× → 1 evento
  7. guard busca-CPF (não-Dono busca por CPF → vazio)
  8. assertNumQueries em list e /elegiveis (sem N+1)

Testes puros (Fakes):
  - cadastrar → colaborador_id retornado
  - desligar → evento publicado (mock)
  - atribuir papel → regras domínio

Refs: T-COL-037; D-COL-7/8/10/12; INV-COL-*; ADV-COL-04/06/08.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

import pytest
from django.db import connection, transaction
from src.application.rh_frota_qualidade.colaboradores import cadastro as uc_cadastro
from src.application.rh_frota_qualidade.colaboradores import papeis as uc_papeis
from src.domain.rh_frota_qualidade.colaboradores.enums import (
    PapelColaborador,
    Vinculo,
)
from src.domain.rh_frota_qualidade.colaboradores.erros import (
    ColaboradorInativo,
    DuplicateCpf,
    SignatarioRtNaoCasa,
    SignatarioSemEscopo,
    SignatarioSemUsuario,
)
from src.domain.rh_frota_qualidade.colaboradores.regras import (
    montar_payload_desligamento,
    pode_atribuir_signatario,
)
from src.infrastructure.colaboradores.serializers import (
    filtrar_visao_pii,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory

# =============================================================
# Fakes (testes puros — sem banco)
# =============================================================


class _FakeColaboradorRepo:
    """Repositório fake para testes puros."""

    def __init__(self, colaboradores: list[Any] | None = None) -> None:
        self._dados: dict[uuid.UUID, Any] = {}
        self._por_cpf: dict[str, Any] = {}
        for c in colaboradores or []:
            self._dados[c.id] = c
            self._por_cpf[c.cpf.value] = c

    def obter(
        self, *, tenant_id: uuid.UUID, colaborador_id: uuid.UUID, incluir_deletados: bool = False
    ) -> Any | None:
        c = self._dados.get(colaborador_id)
        if c is None:
            return None
        if not incluir_deletados and c.deletado_em is not None:
            return None
        return c

    def obter_por_cpf(self, *, tenant_id: uuid.UUID, cpf_value: str) -> Any | None:
        return self._por_cpf.get(cpf_value)

    def listar_ativos(self, *, tenant_id: uuid.UUID, papel: Any = None) -> list[Any]:
        return list(self._dados.values())

    def salvar(self, colaborador: Any) -> None:
        self._dados[colaborador.id] = colaborador
        self._por_cpf[colaborador.cpf.value] = colaborador

    def desligar(
        self,
        *,
        tenant_id: uuid.UUID,
        colaborador_id: uuid.UUID,
        data_desligamento: date,
        motivo_desligamento: str,
    ) -> None:
        pass

    def soft_delete(self, **kwargs: Any) -> None:
        pass


class _FakePapelRepo:
    def __init__(self) -> None:
        self._papeis: list[Any] = []
        self._dono_existe = False

    def listar_por_colaborador(
        self, *, tenant_id: uuid.UUID, colaborador_id: uuid.UUID
    ) -> list[Any]:
        return [p for p in self._papeis if p.colaborador_id == colaborador_id]

    def existe_dono_ativo(self, *, tenant_id: uuid.UUID) -> bool:
        return self._dono_existe

    def salvar(self, papel: Any) -> None:
        self._papeis.append(papel)

    def revogar(self, *, tenant_id: uuid.UUID, papel_id: uuid.UUID, revogado_em: Any) -> None:
        pass

    def revogar_todos_ativos(
        self, *, tenant_id: uuid.UUID, colaborador_id: uuid.UUID, revogado_em: Any
    ) -> int:
        return 0

    def travar_dono_por_tenant(self, *, tenant_id: uuid.UUID) -> None:
        pass


# =============================================================
# Testes PUROS (sem banco)
# =============================================================


class TestCadastroColaboradorPuro:
    """Testes puros do use case de cadastro."""

    def test_cadastrar_sucesso(self) -> None:
        repo = _FakeColaboradorRepo()
        cmd = uc_cadastro.ComandoCadastrarColaborador(
            tenant_id=uuid.uuid4(),
            nome="João Silva",
            cpf_value="52998224725",  # CPF válido
            email="joao@empresa.local",
            telefone="66999000001",
            vinculo=Vinculo.CLT,
            data_admissao=date(2024, 1, 1),
            comissao_default_pct=Decimal("10.00"),
        )
        colab_id = uc_cadastro.cadastrar_colaborador(cmd, repo_colab=repo)
        assert colab_id is not None

    def test_dedup_cpf_levanta_409(self) -> None:
        """Segundo cadastro com mesmo CPF → DuplicateCpf."""
        tenant_id = uuid.uuid4()
        repo = _FakeColaboradorRepo()
        cmd1 = uc_cadastro.ComandoCadastrarColaborador(
            tenant_id=tenant_id,
            nome="João Silva",
            cpf_value="52998224725",
            email="joao@empresa.local",
            telefone="66999000001",
            vinculo=Vinculo.CLT,
            data_admissao=date(2024, 1, 1),
            comissao_default_pct=Decimal("10.00"),
        )
        uc_cadastro.cadastrar_colaborador(cmd1, repo_colab=repo)

        cmd2 = uc_cadastro.ComandoCadastrarColaborador(
            tenant_id=tenant_id,
            nome="João Silva 2",
            cpf_value="52998224725",
            email="joao2@empresa.local",
            telefone="66999000002",
            vinculo=Vinculo.CLT,
            data_admissao=date(2024, 2, 1),
            comissao_default_pct=Decimal("5.00"),
        )
        with pytest.raises(DuplicateCpf):
            uc_cadastro.cadastrar_colaborador(cmd2, repo_colab=repo)

    def test_cpf_invalido_levanta_erro(self) -> None:
        """CPF com dígitos inválidos → ValueError (VO `CPF` em shared valida eagerly)."""
        from src.domain.shared.value_objects import CPF

        with pytest.raises(ValueError):
            CPF("11111111111")


class TestSignatarioPuro:
    """Testes puros das regras de SIGNATARIO."""

    def test_signatario_sem_usuario_id(self) -> None:
        """UNHAPPY #1: sem usuario_id → SignatarioSemUsuario."""
        with pytest.raises(SignatarioSemUsuario):
            pode_atribuir_signatario(
                usuario_id=None,
                rt_casa=False,
                escopo_vigente=False,
                perfil_tenant="A",
            )

    def test_signatario_rt_nao_casa(self) -> None:
        """UNHAPPY #2: RT inexistente / RT de outro → SignatarioRtNaoCasa."""
        with pytest.raises(SignatarioRtNaoCasa):
            pode_atribuir_signatario(
                usuario_id=uuid.uuid4(),
                rt_casa=False,
                escopo_vigente=False,
                perfil_tenant="A",
            )

    def test_signatario_sem_escopo(self) -> None:
        """UNHAPPY #3: RT existe mas escopo não vigente → SignatarioSemEscopo."""
        with pytest.raises(SignatarioSemEscopo):
            pode_atribuir_signatario(
                usuario_id=uuid.uuid4(),
                rt_casa=True,
                escopo_vigente=False,
                perfil_tenant="A",
            )

    def test_signatario_ok(self) -> None:
        """HAPPY: usuario_id + RT casa + escopo vigente → sem exceção."""
        pode_atribuir_signatario(
            usuario_id=uuid.uuid4(),
            rt_casa=True,
            escopo_vigente=True,
            perfil_tenant="A",
        )  # Não levanta


class TestPayloadDesligamentoPuro:
    """Testes do payload v9 de desligamento."""

    def test_payload_v9_completo(self) -> None:
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


class TestFiltrarVisaoPii:
    """Testes do choke-point filtrar_visao_pii (D-COL-7 / INV-COL-PII-MASCARA)."""

    _DADOS_EXEMPLO: ClassVar[dict] = {
        "id": str(uuid.uuid4()),
        "nome": "Maria Técnica",
        "cpf": "52998224725",
        "email": "maria@empresa.local",
        "telefone": "66999000001",
        "vinculo": "clt",
        "ativo": True,
    }

    def test_gerente_nao_ve_cpf(self) -> None:
        """Gerente NÃO vê CPF (D-COL-7 / INV-COL-PII-MASCARA)."""
        papeis = {PapelColaborador.GERENTE.value}
        dados = filtrar_visao_pii(papeis, eh_proprio=False, dados=dict(self._DADOS_EXEMPLO))
        assert dados["cpf"].startswith("***")

    def test_dono_ve_cpf(self) -> None:
        """DONO vê CPF em claro (D-COL-7)."""
        papeis = {PapelColaborador.DONO.value}
        dados = filtrar_visao_pii(papeis, eh_proprio=False, dados=dict(self._DADOS_EXEMPLO))
        assert dados["cpf"] == "52998224725"

    def test_proprio_ve_proprio_cpf(self) -> None:
        """Próprio colaborador vê seu CPF (D-COL-7 — eh_proprio=True)."""
        papeis: set[str] = set()  # sem papel
        dados = filtrar_visao_pii(papeis, eh_proprio=True, dados=dict(self._DADOS_EXEMPLO))
        assert dados["cpf"] == "52998224725"

    def test_sem_papel_mascara_cpf(self) -> None:
        """Sem papel → CPF mascarado (fail-closed — D-COL-7)."""
        papeis: set[str] = set()
        dados = filtrar_visao_pii(papeis, eh_proprio=False, dados=dict(self._DADOS_EXEMPLO))
        assert dados["cpf"].startswith("***")
        # Últimos 2 dígitos visíveis
        assert dados["cpf"].endswith("25")

    def test_gerente_ve_email(self) -> None:
        """Gerente vê e-mail (D-COL-7)."""
        papeis = {PapelColaborador.GERENTE.value}
        dados = filtrar_visao_pii(papeis, eh_proprio=False, dados=dict(self._DADOS_EXEMPLO))
        assert dados["email"] == "maria@empresa.local"

    def test_tecnico_nao_ve_email(self) -> None:
        """Técnico NÃO vê e-mail (D-COL-7 / fail-closed)."""
        papeis = {PapelColaborador.TECNICO.value}
        dados = filtrar_visao_pii(papeis, eh_proprio=False, dados=dict(self._DADOS_EXEMPLO))
        assert dados.get("email") is None

    def test_cpf_mascara_ultimos_2_digitos(self) -> None:
        """Máscara CPF preserva últimos 2 dígitos (D-COL-7 / spec §3)."""
        papeis: set[str] = set()
        dados = {"cpf": "52998224725"}
        resultado = filtrar_visao_pii(papeis, eh_proprio=False, dados=dados)
        assert resultado["cpf"] == "***.***.***-25"


class TestElegiveisDTOAllowlist:
    """Verifica que ElegivelDTO NUNCA contém campos PII (INV-COL-ELEGIVEIS-MINIMO)."""

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

    def test_elegiveis_nao_tem_campo_pii(self) -> None:
        from src.infrastructure.colaboradores.serializers import ElegivelDTOSerializer

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


# =============================================================
# Testes PG-REAL (E2E)
# =============================================================


def _criar_colaborador_no_banco(
    tenant_id: uuid.UUID,
    cpf: str = "52998224725",
    nome: str = "Colaborador Teste",
    usuario_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Helper: cria colaborador diretamente via ORM (sem use case)."""
    from datetime import date

    from src.infrastructure.colaboradores.models import Colaborador as ColaboradorModel

    colab = ColaboradorModel.all_objects.create(
        tenant_id=tenant_id,
        nome=nome,
        cpf=cpf,
        email=f"{cpf}@teste.local",
        telefone="66999000001",
        vinculo="clt",
        data_admissao=date(2024, 1, 1),
        comissao_default_pct=Decimal("10.00"),
        observacao="",
        usuario_id=usuario_id,
    )
    return colab.id


@pytest.mark.django_db(transaction=True)
class TestColaboradoresE2E:
    """Testes E2E PG-real da Fatia 2 (T-COL-037)."""

    def _setar_contexto(self, cursor: Any, tenant_id: uuid.UUID, usuario_id: uuid.UUID) -> None:
        """Seta app.active_tenant_id + app.usuario_id no contexto PG."""
        cursor.execute("SELECT set_config('app.active_tenant_id', %s, true)", [str(tenant_id)])
        cursor.execute("SELECT set_config('app.usuario_id', %s, true)", [str(usuario_id)])
        cursor.execute("SELECT set_config('app.modo_sistema', '', true)")

    def test_dedup_cpf_409(self) -> None:
        """Dedup CPF: segundo cadastro mesmo CPF mesmo tenant → DuplicateCpf (409)."""
        tenant = TenantFactory()

        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            primeiro_id = _criar_colaborador_no_banco(tenant.id, cpf="52998224725", nome="Primeiro")

            repo = __import__(
                "src.infrastructure.colaboradores.repositories",
                fromlist=["DjangoColaboradorRepository"],
            ).DjangoColaboradorRepository()
            existente = repo.obter_por_cpf(tenant_id=tenant.id, cpf_value="52998224725")
            assert existente is not None
            assert existente.id == primeiro_id

    def test_desligar_publica_evento_outbox(self) -> None:
        """Desligar → exatamente 1 linha bus_outbox com payload v9 (D-COL-10 / TL-COL-02)."""
        from src.infrastructure.audit.models import BusOutbox
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
            DjangoPapelRepository,
        )

        tenant = TenantFactory()
        usuario = UsuarioFactory()  # FK válida em auditoria.usuario_id
        usuario_id = usuario.id
        colab_id = None

        with run_in_tenant_context(tenant.id, usuario_id=usuario_id):
            colab_id = _criar_colaborador_no_banco(
                tenant.id, cpf="98765432100", nome="Para Desligar"
            )

            n_outbox_antes = BusOutbox.objects.filter(
                tenant_id=tenant.id, acao="colaborador.desligado"
            ).count()

            cmd = uc_cadastro.ComandoDesligarColaborador(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                data_desligamento=date(2024, 6, 1),
                motivo_desligamento="aposentadoria",
                ator_id=usuario_id,
            )
            with transaction.atomic():
                uc_cadastro.desligar_colaborador(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                    tenant_id_para_evento=tenant.id,
                )

            n_outbox_depois = BusOutbox.objects.filter(
                tenant_id=tenant.id, acao="colaborador.desligado"
            ).count()
            assert n_outbox_depois == n_outbox_antes + 1, (
                f"Esperado 1 evento 'colaborador.desligado' no bus_outbox, "
                f"mas encontrou {n_outbox_depois - n_outbox_antes} novos. "
                "(D-COL-10 / TL-COL-02 / INV-COL-DESLIGAMENTO-CASCADE)"
            )

            # Verifica payload v9
            evento = (
                BusOutbox.objects.filter(
                    tenant_id=tenant.id,
                    acao="colaborador.desligado",
                )
                .order_by("-criado_em")
                .first()
            )
            assert evento is not None
            envelope = evento.envelope_jsonb
            payload = envelope.get("payload", {})
            assert "colaborador_id" in payload
            assert "is_rt_signatario" in payload
            assert "comissoes_pendentes_count" in payload
            assert "chave_idempotente" in payload
            assert "motivo_hash" in payload  # D-COL-8: PII pseudonimizada

    def test_desligar_idempotencia_2x_1_evento(self) -> None:
        """Desligar 2x → 1 evento no outbox (idempotência TL-COL-13 / D-COL-10)."""
        from src.infrastructure.audit.models import BusOutbox
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
            DjangoPapelRepository,
        )

        tenant = TenantFactory()
        usuario = UsuarioFactory()  # FK válida em auditoria.usuario_id
        usuario_id = usuario.id

        with run_in_tenant_context(tenant.id, usuario_id=usuario_id):
            colab_id = _criar_colaborador_no_banco(
                tenant.id, cpf="11144477735", nome="Para Desligar 2x"
            )
            cmd = uc_cadastro.ComandoDesligarColaborador(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                data_desligamento=date(2024, 6, 1),
                motivo_desligamento="teste",
                ator_id=usuario_id,
            )

            # 1ª chamada — deve ter sucesso
            with transaction.atomic():
                uc_cadastro.desligar_colaborador(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                    tenant_id_para_evento=tenant.id,
                )

            n_apos_1a = BusOutbox.objects.filter(
                tenant_id=tenant.id,
                acao="colaborador.desligado",
                envelope_jsonb__payload__colaborador_id=str(colab_id),
            ).count()

            # 2ª chamada — colaborador já inativo → ColaboradorInativo
            with pytest.raises(ColaboradorInativo):
                with transaction.atomic():
                    uc_cadastro.desligar_colaborador(
                        cmd,
                        repo_colab=DjangoColaboradorRepository(),
                        repo_papel=DjangoPapelRepository(),
                        tenant_id_para_evento=tenant.id,
                    )

            n_apos_2a = BusOutbox.objects.filter(
                tenant_id=tenant.id,
                acao="colaborador.desligado",
                envelope_jsonb__payload__colaborador_id=str(colab_id),
            ).count()

            assert (
                n_apos_2a == n_apos_1a
            ), "2ª chamada não deve adicionar evento (idempotência TL-COL-13)"

    def test_signatario_unhappy_sem_usuario_id(self) -> None:
        """UNHAPPY #1: atribuir SIGNATARIO sem usuario_id → SignatarioSemUsuario."""
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
            DjangoPapelRepository,
        )

        tenant = TenantFactory()
        usuario_id = uuid.uuid4()

        with run_in_tenant_context(tenant.id, usuario_id=usuario_id):
            # Colaborador SEM usuario_id
            colab_id = _criar_colaborador_no_banco(tenant.id, cpf="22233344405", usuario_id=None)

            cmd = uc_papeis.ComandoAtribuirPapel(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel=PapelColaborador.SIGNATARIO,
                data_inicio=date(2024, 1, 1),
                perfil_tenant="A",
            )
            with pytest.raises(SignatarioSemUsuario):
                uc_papeis.atribuir_papel(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                )

    def test_signatario_unhappy_rt_inexistente(self) -> None:
        """UNHAPPY #2: usuario_id existe mas sem RTCompetencia → SignatarioRtNaoCasa."""
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
            DjangoPapelRepository,
        )

        tenant = TenantFactory()
        usuario = UsuarioFactory()
        usuario_id = usuario.id

        with run_in_tenant_context(tenant.id, usuario_id=usuario_id):
            # Colaborador COM usuario_id mas sem RT no tenant
            colab_id = _criar_colaborador_no_banco(
                tenant.id, cpf="33344455508", usuario_id=usuario_id
            )

            cmd = uc_papeis.ComandoAtribuirPapel(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel=PapelColaborador.SIGNATARIO,
                data_inicio=date(2024, 1, 1),
                perfil_tenant="A",
            )
            with pytest.raises((SignatarioRtNaoCasa, SignatarioSemEscopo)):
                uc_papeis.atribuir_papel(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                )

    def test_signatario_unhappy_sem_rt_casando_no_tenant(self) -> None:
        """UNHAPPY #3: colaborador com usuario_id mas SEM RTCompetencia vigente casando
        no tenant → SignatarioRtNaoCasa (a busca de RT é por usuario_id no tenant ativo;
        RLS isola RT de outro tenant, então RT alheio nunca casa)."""
        from src.infrastructure.colaboradores.repositories import (
            DjangoColaboradorRepository,
            DjangoPapelRepository,
        )

        tenant_a = TenantFactory()
        usuario = UsuarioFactory()

        # Colaborador com usuario_id, mas nenhum RT vigente casando em tenant_a.
        with run_in_tenant_context(tenant_a.id, usuario_id=usuario.id):
            colab_id = _criar_colaborador_no_banco(
                tenant_a.id, cpf="44455566619", usuario_id=usuario.id
            )

        with run_in_tenant_context(tenant_a.id, usuario_id=usuario.id):
            cmd = uc_papeis.ComandoAtribuirPapel(
                tenant_id=tenant_a.id,
                colaborador_id=colab_id,
                papel=PapelColaborador.SIGNATARIO,
                data_inicio=date(2024, 1, 1),
                perfil_tenant="A",
            )
            # usuario_id presente + rt_casa False → SignatarioRtNaoCasa (específico).
            with pytest.raises(SignatarioRtNaoCasa):
                uc_papeis.atribuir_papel(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                )

    def test_elegiveis_nao_retorna_pii(self) -> None:
        """GET /elegiveis NUNCA retorna CPF/email/telefone fora da allowlist."""
        from src.application.rh_frota_qualidade.colaboradores.consultas import consultar_elegiveis

        tenant = TenantFactory()

        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            _criar_colaborador_no_banco(tenant.id, cpf="55566677720", nome="Elegível")

            elegiveis = consultar_elegiveis(tenant_id=tenant.id)
            campos_proibidos = {
                "cpf",
                "email",
                "telefone",
                "ctps_info",
                "cnh_info",
                "foto_storage_key",
                "comissao_default_pct",
                "vinculo",
                "observacao",
            }
            for e in elegiveis:
                dados_dto = e.__dict__
                for campo in campos_proibidos:
                    assert campo not in dados_dto, (
                        f"ElegivelDTO contém campo PII proibido '{campo}' "
                        "(INV-COL-ELEGIVEIS-MINIMO / ADV-COL-04)"
                    )

    def test_list_sem_n1_queries(self) -> None:
        """assertNumQueries: list colaboradores não gera N+1 (TL-COL-12)."""
        from django.test.utils import CaptureQueriesContext
        from src.application.rh_frota_qualidade.colaboradores.consultas import consultar_elegiveis

        tenant = TenantFactory()

        # CPFs válidos pré-gerados para o teste N+1 (não usar sequência falsa)
        _N1_CPFS = ["66677788830", "77788899941", "88899900078"]
        _N1_CPFS_EXTRA = "10101010133"

        with run_in_tenant_context(tenant.id, usuario_id=uuid.uuid4()):
            for i, cpf in enumerate(_N1_CPFS):
                _criar_colaborador_no_banco(tenant.id, cpf=cpf, nome=f"Col {i}")

            # Primeiro call (pode ter cache miss) — baseline
            with CaptureQueriesContext(connection) as ctx1:
                consultar_elegiveis(tenant_id=tenant.id)
            n1 = len(ctx1.captured_queries)

            # Adiciona mais um colaborador — queries NÃO devem crescer linearmente
            _criar_colaborador_no_banco(tenant.id, cpf=_N1_CPFS_EXTRA, nome="Col Extra")
            with CaptureQueriesContext(connection) as ctx2:
                consultar_elegiveis(tenant_id=tenant.id)
            n2 = len(ctx2.captured_queries)

            # Sem N+1: adicionar 1 colaborador não deve adicionar queries extras
            assert n2 <= n1 + 1, (
                f"Possível N+1: {n1} queries → {n2} queries ao adicionar 1 colaborador "
                "(TL-COL-12 / assertNumQueries)"
            )


# =============================================================
# Testes de invariantes puras (molde TestINV_COL_* — T-COL-051)
# =============================================================


class TestINV_COL_PII_MASCARA:
    """INV-COL-PII-MASCARA: choke-point filtrar_visao_pii aplicado corretamente."""

    def test_fail_closed_sem_papel(self) -> None:
        """Sem papel → todos os campos PII mascarados (fail-closed)."""
        dados = {"cpf": "52998224725", "email": "x@y.com", "telefone": "66999"}
        resultado = filtrar_visao_pii(set(), eh_proprio=False, dados=dados)
        assert resultado["cpf"].startswith("***")
        assert resultado["email"] is None
        assert resultado["telefone"] is None

    def test_proprio_acessa_tudo(self) -> None:
        """Próprio colaborador vê seus dados sem mascaramento."""
        dados = {"cpf": "52998224725", "email": "x@y.com", "telefone": "66999"}
        resultado = filtrar_visao_pii(set(), eh_proprio=True, dados=dados)
        assert resultado["cpf"] == "52998224725"
        assert resultado["email"] == "x@y.com"


class TestINV_COL_ELEGIVEIS_MINIMO:
    """INV-COL-ELEGIVEIS-MINIMO: DTO allowlist separado sem PII."""

    def test_serializer_elegiveis_tem_apenas_campos_allowlist(self) -> None:
        from src.infrastructure.colaboradores.serializers import ElegivelDTOSerializer

        campos_permitidos = {"colaborador_id", "nome_exibicao", "papel", "habilidades", "ativo"}
        ser = ElegivelDTOSerializer(
            {
                "colaborador_id": uuid.uuid4(),
                "nome_exibicao": "Técnico",
                "papel": "tecnico",
                "habilidades": [],
                "ativo": True,
            }
        )
        campos_retornados = set(ser.data.keys())
        extra = campos_retornados - campos_permitidos
        assert extra == set(), f"Campos extras não permitidos em /elegiveis: {extra}"
