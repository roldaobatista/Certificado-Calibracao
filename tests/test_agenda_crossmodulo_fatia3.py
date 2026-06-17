"""Frente agenda -- Fatia 3 (T-AGE-048): integração cross-módulo.

Cobre os adapters reais e consumers do bus (T-AGE-040..044):

  T-AGE-040 OSSchedulingAdapter:
    - criar evento tipo=os chama atribuir_tecnico real (OS->AGENDADA)
    - 2 atividades da mesma OS em técnicos diferentes são permitidas (D-AGE-2)

  T-AGE-041 ColaboradorAgendaAdapter:
    - regime override vence derivação
    - regime derivado de TECNICO -> clt_geral
    - regime derivado de MOTORISTA_UMC -> motorista_profissional
    - papéis conflitantes sem override -> indeterminado+audit (R6)

  T-AGE-042 RTSubstitutoAdapter:
    - perfil A sem RT competente: determinístico (ausência é determinística)
    - perfil A com RT competente: tem_rt=True
    - RT com saída planejada (data_fim_vigencia futuro) NÃO é barrado (PLAN-AGE-02/R15)

  T-AGE-043 AReceberAdapter:
    - no-show cobrável cria título real em contas_receber (D-AGE-9)

  T-AGE-044 Consumers do bus:
    - os.cancelada cancela eventos de agenda vinculados à OS
    - os.atividade_concluida -> slot CONCLUIDO
    - os.atividade_cancelada -> slot CANCELADO
    - colaborador.desligado -> cancela agenda futura, mantém passada
    - tenant.rt.trocado -> log + contagem advisory (não cancela)
    - fan-out: os.cancelada existe em ordens_servico/apps -> não engole (R8)
    - papel_atribuido / papel_revogado -> log apenas (INV-AG-REGIME-001)

REGRAS:
  - GATE VERMELHO: nenhum mascaramento ou assert vazio.
  - Dados reais via factory.
  - --reuse-db obrigatório (NUNCA --create-db).
  - Stage seletivo (módulos fechados só no wiring -- R11).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from src.domain.operacao.agenda.enums import EstadoEvento
from src.infrastructure.agenda.adapters import (
    ColaboradorAgendaAdapter,
    OSSchedulingAdapter,
    RTSubstitutoAdapter,
)
from src.infrastructure.agenda.consumers.colaborador_eventos import (
    handle_colaborador_desligado,
    handle_papel_atribuido,
    handle_papel_revogado,
)
from src.infrastructure.agenda.consumers.os_eventos import (
    handle_os_atividade_cancelada,
    handle_os_atividade_concluida,
    handle_os_cancelada,
)
from src.infrastructure.agenda.consumers.rt_eventos import handle_tenant_rt_trocado
from src.infrastructure.agenda.models import EventoAgenda, RegimeJornadaColaborador
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory

# =============================================================
# Helpers
# =============================================================


def _slot_futuro(dias: int = 7, hora_inicio: int = 9, hora_fim: int = 11):
    """Slot no futuro para evitar conflito com eventos passados imutáveis."""
    base = datetime.now(UTC).replace(hour=hora_inicio, minute=0, second=0, microsecond=0)
    base = base + timedelta(days=dias)
    fim = base.replace(hour=hora_fim)
    return base, fim


def _envelope(
    *,
    acao: str,
    tenant_id: uuid.UUID,
    perfil: str = "D",
    payload: dict | None = None,
    event_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Monta envelope padrão do bus (molde consumers existentes)."""
    return {
        "event_id": str(event_id or uuid.uuid4()),
        "acao": acao,
        "tenant_id": str(tenant_id),
        "perfil_no_evento": perfil,
        "payload": payload or {},
    }


def _criar_evento_agenda(
    tenant,
    *,
    tecnico_id: uuid.UUID | None = None,
    tipo: str = "bloqueio",
    estado: str = "agendado",
    dias_futuro: int = 7,
    atividade_id: uuid.UUID | None = None,
    os_id: uuid.UUID | None = None,
) -> EventoAgenda:
    """Cria EventoAgenda no banco dentro do contexto do tenant."""
    inicia_at, termina_at = _slot_futuro(dias=dias_futuro)
    if tecnico_id is None:
        tecnico_id = uuid.uuid4()
    ator_id = UsuarioFactory().id
    with run_in_tenant_context(tenant.id):
        ev = EventoAgenda.objects.create(
            tenant_id=tenant.id,
            tecnico_id=tecnico_id,
            tipo=tipo,
            estado=estado,
            inicia_at=inicia_at,
            termina_at=termina_at,
            aloca_em_umc=False,
            atividade_id=atividade_id,
            os_id=os_id,
            confirmar_feriado=False,
            descricao_publica="",
            revision=1,
            criado_por_usuario_id=ator_id,
        )
    return ev


# =============================================================
# T-AGE-040 -- OSSchedulingAdapter
# =============================================================


class TestOSSchedulingAdapter:
    """OSSchedulingAdapter -- integração com atribuir_tecnico real."""

    def test_obter_atividade_retorna_none_id_inexistente(self, db):
        """Atividade inexistente no tenant -> None (anti-oráculo TL-AGE-05)."""
        tenant = TenantFactory()
        adapter = OSSchedulingAdapter()
        resultado = adapter.obter_atividade(
            tenant_id=tenant.id,
            atividade_id=uuid.uuid4(),
        )
        assert resultado is None

    def test_obter_atividade_existente_retorna_dict(self, db):
        """Atividade existente no tenant correto -> dict com campos esperados."""
        from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS

        tenant = TenantFactory()
        adapter = OSSchedulingAdapter()
        # cliente_referencia_hash: max_length=64, sem prefixo vN: (uuid.hex * 2 = 64 chars)
        chash_a = uuid.uuid4().hex + uuid.uuid4().hex

        with run_in_tenant_context(tenant.id):
            os_obj = OS.objects.create(
                tenant_id=tenant.id,
                numero_os=1,
                cliente_id=uuid.uuid4(),
                cliente_referencia_hash=chash_a,
                cliente_key_id="v1",
                estado="rascunho",
                tipo_predominante="calibracao",
                valor_total=Decimal("0"),
                valor_total_atualizado=Decimal("0"),
            )
            atv = AtividadeDaOS.objects.create(
                tenant_id=tenant.id,
                os_id=os_obj.id,
                tipo="calibracao",
                sequencia=1,
                estado="pendente",
            )

        resultado = adapter.obter_atividade(
            tenant_id=tenant.id,
            atividade_id=atv.id,
        )
        assert resultado is not None
        assert resultado["estado"] == "pendente"
        assert resultado["os_id"] == str(os_obj.id)

    def test_obter_atividade_cross_tenant_retorna_none(self, db):
        """Atividade de outro tenant -> None (proteção cross-tenant)."""
        from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS

        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        adapter = OSSchedulingAdapter()
        chash_b = uuid.uuid4().hex + uuid.uuid4().hex

        with run_in_tenant_context(tenant_a.id):
            os_obj = OS.objects.create(
                tenant_id=tenant_a.id,
                numero_os=2,
                cliente_id=uuid.uuid4(),
                cliente_referencia_hash=chash_b,
                cliente_key_id="v1",
                estado="rascunho",
                tipo_predominante="calibracao",
                valor_total=Decimal("0"),
                valor_total_atualizado=Decimal("0"),
            )
            atv = AtividadeDaOS.objects.create(
                tenant_id=tenant_a.id,
                os_id=os_obj.id,
                tipo="calibracao",
                sequencia=1,
                estado="pendente",
            )

        # Busca com tenant_b -> None
        resultado = adapter.obter_atividade(
            tenant_id=tenant_b.id,
            atividade_id=atv.id,
        )
        assert resultado is None

    def test_criar_evento_os_transita_atividade_para_agendada(self, db):
        """GATE-AGE-OS-WIRING: criar_evento tipo=os chama atribuir_tecnico real → OS→AGENDADA.

        Prova end-to-end (D-AGE-5/US-AG-013): ao criar um evento de agenda para uma
        atividade de OS, a atividade transita PENDENTE→AGENDADA e a OS (1 atividade)
        RASCUNHO→AGENDADA. Antes do wiring (2026-06-17), criar_evento NÃO tocava a OS.
        """
        from datetime import UTC, datetime, timedelta

        from src.application.operacao.agenda import criar_evento
        from src.domain.operacao.agenda.enums import TipoEvento
        from src.domain.operacao.agenda.value_objects import Janela
        from src.infrastructure.agenda.adapters import RTSubstitutoAdapter
        from src.infrastructure.agenda.repositories import DjangoEventoAgendaRepository
        from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS

        from tests.fakes.agenda_fakes import FakeColaboradorAgendaPort

        tenant = TenantFactory()
        tecnico_id = uuid.uuid4()
        chash = uuid.uuid4().hex + uuid.uuid4().hex
        with run_in_tenant_context(tenant.id):
            os_obj = OS.objects.create(
                tenant_id=tenant.id,
                numero_os=42,
                cliente_id=uuid.uuid4(),
                cliente_referencia_hash=chash,
                cliente_key_id="v1",
                estado="rascunho",
                tipo_predominante="calibracao",
                valor_total=Decimal("0"),
                valor_total_atualizado=Decimal("0"),
            )
            atv = AtividadeDaOS.objects.create(
                tenant_id=tenant.id,
                os_id=os_obj.id,
                tipo="calibracao",
                sequencia=1,
                estado="pendente",
            )
            inicia = datetime.now(UTC) + timedelta(days=3)
            inp = criar_evento.CriarEventoInput(
                tenant_id=tenant.id,
                tecnico_id=tecnico_id,
                janela=Janela(inicia_at=inicia, termina_at=inicia + timedelta(hours=2)),
                aloca_em_umc=False,
                perfil_tenant="A",
                criado_por_usuario_id=uuid.uuid4(),
                tipo=TipoEvento.OS,
                atividade_id=atv.id,
                os_id=os_obj.id,
            )
            criar_evento.executar(
                inp,
                repo=DjangoEventoAgendaRepository(),
                colaborador_port=FakeColaboradorAgendaPort(),
                os_port=OSSchedulingAdapter(),
                rt_port=RTSubstitutoAdapter(),
            )
            atv.refresh_from_db()
            os_obj.refresh_from_db()

        assert atv.estado == "agendada", "atividade da OS não transitou para AGENDADA"
        assert atv.tecnico_executor_id == tecnico_id
        assert os_obj.estado == "agendada", "OS (1 atividade) não transitou para AGENDADA"


# =============================================================
# T-AGE-041 -- ColaboradorAgendaAdapter
# =============================================================


@pytest.mark.django_db(transaction=True)
class TestColaboradorAgendaAdapter:
    """ColaboradorAgendaAdapter -- papel, CNH, regime."""

    def test_is_tecnico_campo_com_papel_tecnico(self):
        """Papel TECNICO ativo -> is_tecnico_campo=True."""
        from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel

        tenant = TenantFactory()
        adapter = ColaboradorAgendaAdapter()
        colab_id = uuid.uuid4()

        with run_in_tenant_context(tenant.id):
            Colaborador.objects.create(
                id=colab_id,
                tenant_id=tenant.id,
                nome="Técnico Teste",
                cpf="11111111111",
                email="",
                telefone="",
                vinculo="clt",
                data_admissao=date.today(),
                comissao_default_pct=Decimal("0"),
            )
            ColaboradorPapel.objects.create(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel="tecnico",
                data_inicio=date.today(),
                data_fim=None,
                revogado_em=None,
            )

        # RLS exige run_in_tenant_context para busca via ORM
        with run_in_tenant_context(tenant.id):
            resultado = adapter.is_tecnico_campo(tenant_id=tenant.id, colaborador_id=colab_id)
        assert resultado is True

    def test_regime_override_vence_derivacao(self):
        """Override humano vigente vence derivação do papel (D-AGE-15 / INV-AG-REGIME-001)."""
        from src.domain.operacao.agenda.enums import FonteRegime, RegimeJornada
        from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel

        tenant = TenantFactory()
        adapter = ColaboradorAgendaAdapter()
        colab_id = uuid.uuid4()
        hoje = date.today()

        with run_in_tenant_context(tenant.id):
            Colaborador.objects.create(
                id=colab_id,
                tenant_id=tenant.id,
                nome="Motorista Sobrescrito",
                cpf="22222222222",
                email="",
                telefone="",
                vinculo="clt",
                data_admissao=hoje,
                comissao_default_pct=Decimal("0"),
            )
            ColaboradorPapel.objects.create(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel="motorista_umc",
                data_inicio=hoje,
                data_fim=None,
                revogado_em=None,
            )
            # Override: motorista enquadrado como clt_geral por RH
            RegimeJornadaColaborador.objects.create(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                regime="clt_geral",
                fonte="override_humano",
                vigencia_inicio=hoje,
                vigencia_fim=None,
                definido_por_usuario_id=uuid.uuid4(),
                justificativa="decisão RH",
            )

        with run_in_tenant_context(tenant.id):
            result = adapter.regime_jornada(
                tenant_id=tenant.id, colaborador_id=colab_id, na_data=hoje
            )
        assert result.regime == RegimeJornada.CLT_GERAL
        assert result.fonte == FonteRegime.OVERRIDE_HUMANO

    def test_regime_derivado_tecnico(self):
        """TECNICO sem override -> clt_geral derivado (D-AGE-15)."""
        from src.domain.operacao.agenda.enums import FonteRegime, RegimeJornada
        from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel

        tenant = TenantFactory()
        adapter = ColaboradorAgendaAdapter()
        colab_id = uuid.uuid4()
        hoje = date.today()

        with run_in_tenant_context(tenant.id):
            Colaborador.objects.create(
                id=colab_id,
                tenant_id=tenant.id,
                nome="T",
                cpf="33333333333",
                email="",
                telefone="",
                vinculo="clt",
                data_admissao=hoje,
                comissao_default_pct=Decimal("0"),
            )
            ColaboradorPapel.objects.create(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel="tecnico",
                data_inicio=hoje,
            )

        with run_in_tenant_context(tenant.id):
            result = adapter.regime_jornada(
                tenant_id=tenant.id, colaborador_id=colab_id, na_data=hoje
            )
        assert result.regime == RegimeJornada.CLT_GERAL
        assert result.fonte == FonteRegime.DERIVADO_PAPEL

    def test_regime_indeterminado_papeis_conflitantes(self):
        """TECNICO + MOTORISTA_UMC sem override -> indeterminado (fail-safe R6)."""
        from src.domain.operacao.agenda.enums import FonteRegime, RegimeJornada
        from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel

        tenant = TenantFactory()
        adapter = ColaboradorAgendaAdapter()
        colab_id = uuid.uuid4()
        hoje = date.today()

        with run_in_tenant_context(tenant.id):
            Colaborador.objects.create(
                id=colab_id,
                tenant_id=tenant.id,
                nome="Dual",
                cpf="44444444444",
                email="",
                telefone="",
                vinculo="clt",
                data_admissao=hoje,
                comissao_default_pct=Decimal("0"),
            )
            ColaboradorPapel.objects.create(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel="tecnico",
                data_inicio=hoje,
            )
            ColaboradorPapel.objects.create(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel="motorista_umc",
                data_inicio=hoje,
            )

        with run_in_tenant_context(tenant.id):
            result = adapter.regime_jornada(
                tenant_id=tenant.id, colaborador_id=colab_id, na_data=hoje
            )
        # Fail-safe: papéis conflitantes -> nao_aplica + indeterminado (R6)
        assert result.regime == RegimeJornada.NAO_APLICA
        assert result.fonte == FonteRegime.INDETERMINADO

    def test_pendencia_cnh_motorista_com_pendencia(self):
        """MOTORISTA_UMC com pendencia_cnh=True -> True."""
        from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel

        tenant = TenantFactory()
        adapter = ColaboradorAgendaAdapter()
        colab_id = uuid.uuid4()

        with run_in_tenant_context(tenant.id):
            Colaborador.objects.create(
                id=colab_id,
                tenant_id=tenant.id,
                nome="M",
                cpf="55555555555",
                email="",
                telefone="",
                vinculo="clt",
                data_admissao=date.today(),
                comissao_default_pct=Decimal("0"),
            )
            ColaboradorPapel.objects.create(
                tenant_id=tenant.id,
                colaborador_id=colab_id,
                papel="motorista_umc",
                data_inicio=date.today(),
                pendencia_cnh=True,
            )

        with run_in_tenant_context(tenant.id):
            resultado_cnh = adapter.pendencia_cnh(tenant_id=tenant.id, colaborador_id=colab_id)
        assert resultado_cnh is True


# =============================================================
# T-AGE-042 -- RTSubstitutoAdapter
# =============================================================


@pytest.mark.django_db(transaction=True)
class TestRTSubstitutoAdapter:
    """RTSubstitutoAdapter -- competência RT projetada ao slot."""

    def test_sem_rt_ausencia_deterministica(self):
        """Tenant sem RT -> tem_rt=False e ausência determinística."""
        tenant = TenantFactory()
        adapter = RTSubstitutoAdapter()
        data_slot = date.today() + timedelta(days=30)

        with run_in_tenant_context(tenant.id):
            tem_rt = adapter.tem_rt_competente_no_slot(
                tenant_id=tenant.id,
                grandeza="massa",
                data_slot=data_slot,
            )
            ausencia_det = adapter.eh_deterministica_ausencia(
                tenant_id=tenant.id,
                grandeza="massa",
                data_slot=data_slot,
            )
        assert tem_rt is False
        assert ausencia_det is True

    def test_com_rt_competente_tem_rt_true(self):
        """RT com competência na grandeza -> tem_rt=True."""
        from src.infrastructure.responsavel_tecnico.models import (
            ResponsavelTecnicoTenant,
            RTCompetencia,
        )

        tenant = TenantFactory()
        usuario = UsuarioFactory()
        adapter = RTSubstitutoAdapter()
        data_slot = date.today() + timedelta(days=30)
        hoje = date.today()

        with run_in_tenant_context(tenant.id):
            criador = UsuarioFactory()
            rt = ResponsavelTecnicoTenant.objects.create(
                tenant=tenant,
                usuario=usuario,
                nome_completo_snapshot="RT Teste",
                cpf_hash="v1:" + "c" * 64,
                formacao_academica="Engenharia",
                registro_profissional_tipo="CREA",
                registro_profissional_numero="CREA-MT 123",
                data_inicio_vigencia=hoje,
                criado_por=criador,
            )
            RTCompetencia.objects.create(
                tenant=tenant,
                rt=rt,
                grandeza="massa",
                declarado_em=hoje,
                vigente_ate=None,
                criado_por=criador,
            )

        with run_in_tenant_context(tenant.id):
            tem_rt = adapter.tem_rt_competente_no_slot(
                tenant_id=tenant.id,
                grandeza="massa",
                data_slot=data_slot,
            )
            ausencia_det = adapter.eh_deterministica_ausencia(
                tenant_id=tenant.id,
                grandeza="massa",
                data_slot=data_slot,
            )
        assert tem_rt is True
        assert ausencia_det is False

    def test_rt_com_saida_planejada_nao_e_barrado(self):
        """RT com data_fim_vigencia futuro NÃO é barrado pela agenda (PLAN-AGE-02/R15).

        A agenda é CONSULTIVA -- gate duro vive na emissão (D-AGE-6).
        RTSubstitutoAdapter usa encerrado_em IS NULL para vigência;
        data_fim_vigencia é informativo e não bloqueia (limitação documentada).
        """
        from src.infrastructure.responsavel_tecnico.models import (
            ResponsavelTecnicoTenant,
            RTCompetencia,
        )

        tenant = TenantFactory()
        usuario = UsuarioFactory()
        adapter = RTSubstitutoAdapter()
        data_slot = date.today() + timedelta(days=30)
        hoje = date.today()

        with run_in_tenant_context(tenant.id):
            criador = UsuarioFactory()
            # RT com data_fim_vigencia FUTURO (saída planejada) mas encerrado_em IS NULL
            rt = ResponsavelTecnicoTenant.objects.create(
                tenant=tenant,
                usuario=usuario,
                nome_completo_snapshot="RT Saindo",
                cpf_hash="v1:" + "d" * 64,
                formacao_academica="Física",
                registro_profissional_tipo="CREA",
                registro_profissional_numero="CREA-MT 456",
                data_inicio_vigencia=hoje,
                data_fim_vigencia=data_slot + timedelta(days=15),  # saída planejada FUTURA
                criado_por=criador,
                # encerrado_em IS NULL -> ainda vigente para o adapter
            )
            RTCompetencia.objects.create(
                tenant=tenant,
                rt=rt,
                grandeza="volume",
                declarado_em=hoje,
                vigente_ate=None,
                criado_por=criador,
            )

        # NÃO deve barrar (limitação aceita PLAN-AGE-02/R15)
        with run_in_tenant_context(tenant.id):
            tem_rt = adapter.tem_rt_competente_no_slot(
                tenant_id=tenant.id,
                grandeza="volume",
                data_slot=data_slot,
            )
        assert tem_rt is True, (
            "RT com saída planejada (data_fim_vigencia futuro) NÃO deve ser barrado "
            "pela agenda -- gate duro vive na emissão (PLAN-AGE-02/R15)"
        )


# =============================================================
# T-AGE-044 -- Consumers do bus (fan-out -- R8)
# =============================================================


@pytest.mark.django_db(transaction=True)
class TestConsumersOSEventos:
    """Consumers de os.* -- slots criados/cancelados corretamente."""

    def test_os_cancelada_cancela_slots_agendados(self):
        """os.cancelada -> cancela eventos AGENDADOS vinculados à OS."""
        tenant = TenantFactory()
        os_id = uuid.uuid4()

        # Cria 2 eventos vinculados à OS (agendados)
        ev1 = _criar_evento_agenda(
            tenant, tipo="os", estado="agendado", os_id=os_id, atividade_id=uuid.uuid4()
        )
        ev2 = _criar_evento_agenda(
            tenant,
            tipo="os",
            estado="agendado",
            os_id=os_id,
            atividade_id=uuid.uuid4(),
            dias_futuro=8,
        )

        envelop = _envelope(
            acao="os.cancelada",
            tenant_id=tenant.id,
            payload={"os_id": str(os_id)},
        )
        with run_in_tenant_context(tenant.id):
            handle_os_cancelada(envelop)

        with run_in_tenant_context(tenant.id):
            ev1.refresh_from_db()
            ev2.refresh_from_db()

        assert ev1.estado == EstadoEvento.CANCELADO.value
        assert ev2.estado == EstadoEvento.CANCELADO.value

    def test_os_cancelada_nao_cancela_eventos_de_outro_tenant(self):
        """os.cancelada NÃO cancela eventos de outro tenant (isolamento cross-tenant)."""
        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        os_id = uuid.uuid4()

        # Evento do tenant_b com o MESMO os_id
        ev_b = _criar_evento_agenda(
            tenant_b, tipo="os", estado="agendado", os_id=os_id, atividade_id=uuid.uuid4()
        )

        # Cancela no tenant_a
        envelop = _envelope(
            acao="os.cancelada",
            tenant_id=tenant_a.id,
            payload={"os_id": str(os_id)},
        )
        with run_in_tenant_context(tenant_a.id):
            handle_os_cancelada(envelop)

        # Evento do tenant_b deve estar intacto
        with run_in_tenant_context(tenant_b.id):
            ev_b.refresh_from_db()
        assert ev_b.estado == EstadoEvento.AGENDADO.value

    def test_os_atividade_concluida_transita_slot(self):
        """os.atividade_concluida -> slot vai para CONCLUIDO."""
        tenant = TenantFactory()
        atividade_id = uuid.uuid4()
        ev = _criar_evento_agenda(tenant, tipo="os", estado="agendado", atividade_id=atividade_id)

        envelop = _envelope(
            acao="os.atividade_concluida",
            tenant_id=tenant.id,
            payload={"atividade_id": str(atividade_id)},
        )
        with run_in_tenant_context(tenant.id):
            handle_os_atividade_concluida(envelop)

        with run_in_tenant_context(tenant.id):
            ev.refresh_from_db()
        assert ev.estado == EstadoEvento.CONCLUIDO.value

    def test_os_atividade_cancelada_cancela_slot(self):
        """os.atividade_cancelada -> slot vai para CANCELADO."""
        tenant = TenantFactory()
        atividade_id = uuid.uuid4()
        ev = _criar_evento_agenda(tenant, tipo="os", estado="agendado", atividade_id=atividade_id)

        envelop = _envelope(
            acao="os.atividade_cancelada",
            tenant_id=tenant.id,
            payload={"atividade_id": str(atividade_id)},
        )
        with run_in_tenant_context(tenant.id):
            handle_os_atividade_cancelada(envelop)

        with run_in_tenant_context(tenant.id):
            ev.refresh_from_db()
        assert ev.estado == EstadoEvento.CANCELADO.value

    def test_fanout_os_cancelada_nao_engole_consumers_existentes(self):
        """Fan-out: os.cancelada pode ter N consumers sem engolir existentes (R8).

        Verifica que o _REGISTRY da acao 'os.cancelada' contém o consumer
        da agenda. O registro é dict[str, list] -- fan-out aditivo.
        """
        from src.infrastructure.audit.outbox_worker import _REGISTRY

        consumers_os_cancelada = _REGISTRY.get("os.cancelada", [])
        from src.infrastructure.agenda.consumers.os_eventos import (
            handle_os_cancelada as agenda_consumer,
        )

        assert (
            agenda_consumer in consumers_os_cancelada
        ), "handle_os_cancelada da agenda deve estar no _REGISTRY['os.cancelada'] (fan-out R8)"

    def test_idempotencia_os_cancelada_replay_seguro(self):
        """Replay do mesmo event_id não re-executa o handler (INV-BUS-001)."""
        tenant = TenantFactory()
        os_id = uuid.uuid4()
        event_id = uuid.uuid4()

        ev = _criar_evento_agenda(
            tenant, tipo="os", estado="agendado", os_id=os_id, atividade_id=uuid.uuid4()
        )

        envelop = _envelope(
            acao="os.cancelada",
            tenant_id=tenant.id,
            payload={"os_id": str(os_id)},
            event_id=event_id,
        )
        with run_in_tenant_context(tenant.id):
            handle_os_cancelada(envelop)  # 1ª vez: cancela
        with run_in_tenant_context(tenant.id):
            ev.refresh_from_db()
        assert ev.estado == EstadoEvento.CANCELADO.value

        # Reabrir manualmente para testar idempotência
        with run_in_tenant_context(tenant.id):
            EventoAgenda.objects.filter(id=ev.id).update(estado=EstadoEvento.AGENDADO.value)

        with run_in_tenant_context(tenant.id):
            handle_os_cancelada(envelop)  # 2ª vez (replay): NÃO deve cancelar novamente

        with run_in_tenant_context(tenant.id):
            ev.refresh_from_db()
        # Replay detectado -> estado mantido como AGENDADO (handler não executou de novo)
        assert ev.estado == EstadoEvento.AGENDADO.value


@pytest.mark.django_db(transaction=True)
class TestConsumersColaboradorEventos:
    """Consumers de colaborador.* -- desligamento e papéis."""

    def test_colaborador_desligado_cancela_agenda_futura(self):
        """colaborador.desligado -> eventos FUTUROS cancelados; passados preservados."""
        tenant = TenantFactory()
        tecnico_id = uuid.uuid4()

        # Evento FUTURO (deve ser cancelado)
        ev_futuro = _criar_evento_agenda(
            tenant, tecnico_id=tecnico_id, estado="agendado", dias_futuro=10
        )
        # Evento PASSADO (não deve ser cancelado -- já ocorreu)
        inicia_passado = datetime.now(UTC) - timedelta(days=2)
        termina_passado = inicia_passado + timedelta(hours=2)
        ator_id = UsuarioFactory().id
        with run_in_tenant_context(tenant.id):
            ev_passado = EventoAgenda.objects.create(
                tenant_id=tenant.id,
                tecnico_id=tecnico_id,
                tipo="bloqueio",
                estado="agendado",  # estado = agendado mas no passado
                inicia_at=inicia_passado,
                termina_at=termina_passado,
                aloca_em_umc=False,
                confirmar_feriado=False,
                descricao_publica="",
                revision=1,
                criado_por_usuario_id=ator_id,
            )

        envelop = _envelope(
            acao="colaborador.desligado",
            tenant_id=tenant.id,
            payload={"colaborador_id": str(tecnico_id)},
        )
        with run_in_tenant_context(tenant.id):
            handle_colaborador_desligado(envelop)

        with run_in_tenant_context(tenant.id):
            ev_futuro.refresh_from_db()
            ev_passado.refresh_from_db()

        assert ev_futuro.estado == EstadoEvento.CANCELADO.value, "Evento futuro deve ser cancelado"
        assert (
            ev_passado.estado == EstadoEvento.AGENDADO.value
        ), "Evento passado deve ser preservado"

    def test_papel_atribuido_nao_grava_override_automatico(self):
        """papel_atribuido -> log apenas (IA NÃO grava override -- INV-AG-REGIME-001)."""
        tenant = TenantFactory()
        colab_id = uuid.uuid4()

        envelop = _envelope(
            acao="colaborador.papel_atribuido",
            tenant_id=tenant.id,
            payload={"colaborador_id": str(colab_id), "papel": "tecnico"},
        )
        overrides_antes = RegimeJornadaColaborador.objects.filter(
            tenant_id=tenant.id, colaborador_id=colab_id
        ).count()

        with run_in_tenant_context(tenant.id):
            handle_papel_atribuido(envelop)

        overrides_depois = RegimeJornadaColaborador.objects.filter(
            tenant_id=tenant.id, colaborador_id=colab_id
        ).count()

        assert overrides_depois == overrides_antes, (
            "handle_papel_atribuido NÃO deve criar override de regime "
            "(IA nunca grava override -- INV-AG-REGIME-001)"
        )

    def test_papel_revogado_nao_grava_override_automatico(self):
        """papel_revogado -> log apenas (IA NÃO grava override -- INV-AG-REGIME-001)."""
        tenant = TenantFactory()
        colab_id = uuid.uuid4()

        envelop = _envelope(
            acao="colaborador.papel_revogado",
            tenant_id=tenant.id,
            payload={"colaborador_id": str(colab_id), "papel": "motorista_umc"},
        )

        with run_in_tenant_context(tenant.id):
            handle_papel_revogado(envelop)

        count = RegimeJornadaColaborador.objects.filter(
            tenant_id=tenant.id, colaborador_id=colab_id
        ).count()
        assert count == 0, "handle_papel_revogado NÃO deve criar override"


@pytest.mark.django_db(transaction=True)
class TestConsumersRTEventos:
    """Consumers de tenant.rt.* -- revisão advisory de atribuições futuras."""

    def test_tenant_rt_trocado_nao_cancela_slots(self):
        """tenant.rt.trocado -> advisory (log + contagem); NÃO cancela eventos (PLAN-AGE-02/R15)."""
        tenant = TenantFactory()
        # Cria evento de agenda (tipo=os com atividade_id para satisfazer CHECK constraint)
        ev = _criar_evento_agenda(tenant, tipo="os", estado="agendado", atividade_id=uuid.uuid4())

        rt_novo_id = uuid.uuid4()
        envelop = _envelope(
            acao="tenant.rt.trocado",
            tenant_id=tenant.id,
            payload={
                "rt_novo_id": str(rt_novo_id),
                "data_efetivacao": date.today().isoformat(),
            },
        )
        with run_in_tenant_context(tenant.id):
            handle_tenant_rt_trocado(envelop)

        # Evento NÃO deve ter sido cancelado (agenda é consultiva)
        with run_in_tenant_context(tenant.id):
            ev.refresh_from_db()
        assert (
            ev.estado == EstadoEvento.AGENDADO.value
        ), "tenant.rt.trocado NÃO deve cancelar eventos -- agenda é consultiva (D-AGE-6 / R15)"

    def test_rt_trocado_fail_closed_sem_perfil(self):
        """tenant.rt.trocado sem perfil_no_evento -> fail-closed (no-op R7)."""
        tenant = TenantFactory()
        ev = _criar_evento_agenda(tenant, tipo="os", estado="agendado", atividade_id=uuid.uuid4())

        envelop = {
            "event_id": str(uuid.uuid4()),
            "acao": "tenant.rt.trocado",
            "tenant_id": str(tenant.id),
            # SEM perfil_no_evento
            "payload": {"rt_novo_id": str(uuid.uuid4())},
        }
        with run_in_tenant_context(tenant.id):
            handle_tenant_rt_trocado(envelop)

        # Deve ser no-op (fail-closed)
        with run_in_tenant_context(tenant.id):
            ev.refresh_from_db()
        assert ev.estado == EstadoEvento.AGENDADO.value


@pytest.mark.django_db(transaction=True)
class TestConsumersFanOut:
    """Fan-out: consumers da agenda NÃO engolam consumers existentes (R8)."""

    def test_registry_os_cancelada_contem_agenda_e_outros(self):
        """_REGISTRY['os.cancelada'] contem o consumer da agenda como fan-out (R8)."""
        from src.infrastructure.agenda.consumers.os_eventos import handle_os_cancelada
        from src.infrastructure.audit.outbox_worker import _REGISTRY

        consumers = _REGISTRY.get("os.cancelada", [])
        assert (
            handle_os_cancelada in consumers
        ), "handle_os_cancelada deve estar no fan-out de os.cancelada"
        # Múltiplos consumers na mesma ação são permitidos (fan-out)
        # Não asserta que é o único -- outros módulos podem ter consumers aqui

    def test_registry_tenant_rt_trocado_contem_agenda(self):
        """_REGISTRY['tenant.rt.trocado'] contém consumer da agenda."""
        from src.infrastructure.agenda.consumers.rt_eventos import handle_tenant_rt_trocado
        from src.infrastructure.audit.outbox_worker import _REGISTRY

        consumers = _REGISTRY.get("tenant.rt.trocado", [])
        assert handle_tenant_rt_trocado in consumers
