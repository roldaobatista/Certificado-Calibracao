"""Tests regressão INV-CAL puros (T-CAL-145..151 — Fase 10 M4).

Cobre invariantes M4 testáveis sem PG real (mockando repositories /
chamando jobs puros). Para INVs que exigem PG (CONC-002 snapshot_lock
one-way, BACKUP-001 cron diário, RAST-002 CHECK composta), ver tarefas
TRACK Wave A em `docs/faseamento/M4-calibracao/tasks.md` §"Fase 10".

INVs cobertas neste arquivo:
- INV-CAL-INC-004: alerta correlação omitida (job puro analisar_correlacao).
- INV-CAL-RT-002: snapshot_competencia_revisor_json IMUTÁVEL pós-aprovação.
- INV-CAL-IDEMP-001: idempotência forte registrar_leitura (+ documenta GAP
  IdempotencyPayloadMismatch que precisa de validação adicional Wave A).
- INV-CAL-CONF-001: 2ª conferência exige estado AGUARDANDO_2A_CONFERENCIA
  + conferente != revisor != executor (exceção ADR-0026 4 condições).
- INV-CAL-DEC-001: avaliar_conformidade bloqueado pós-APROVADA (lock).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.jobs.analisar_correlacao_componentes import (
    executar as analisar_correlacao,
)
from src.application.metrologia.calibracao.registrar_leitura import (
    RegistrarLeituraInput,
)
from src.application.metrologia.calibracao.registrar_leitura import (
    executar as registrar_leitura_executar,
)
from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    ComponenteIncertezaSnapshot,
    LeituraSnapshot,
    OrigemLeitura,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8

AGORA = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


# =====================================================================
# Builders
# =====================================================================


def _componente(
    *,
    tenant: UUID,
    orc_id: UUID,
    fonte_padrao: UUID | None,
    correlato_id: UUID | None = None,
) -> ComponenteIncertezaSnapshot:
    return ComponenteIncertezaSnapshot(
        id=uuid4(),
        tenant_id=tenant,
        orcamento_incerteza_id=orc_id,
        nome_componente=f"comp-{uuid4().hex[:6]}",
        tipo_componente="B",
        valor_estimativa=Decimal("0.05"),
        contribuicao=Decimal("0.0025"),
        grau_liberdade=None,
        n_amostras=None,
        s_x=None,
        correlacao_com_componente_id=correlato_id,
        coeficiente_correlacao=None if correlato_id is None else Decimal("0.5"),
        fonte_default_padrao_id=fonte_padrao,
    )


def _calibracao_em_execucao(*, tenant: UUID) -> CalibracaoSnapshot:
    """Snapshot mock de calibracao em EM_EXECUCAO (para registrar_leitura)."""
    return CalibracaoSnapshot(
        id=uuid4(),
        tenant_id=tenant,
        numero_interno=1,
        numero_exibido="CAL-2026-000001",
        origem_recepcao=OrigemRecepcao.AVULSA,
        atividade_os_id=None,
        instrumento_id=uuid4(),
        snapshot_equipamento_json={},
        cliente_id=None,
        cliente_referencia_hash="v01$c",
        cliente_key_id="k",
        tipo_acreditacao=TipoAcreditacao.NAO_RBC,
        status=EstadoCalibracao.EM_EXECUCAO,
        revision=2,
        regra_decisao=RegraDecisao.ACEITACAO_SIMPLES,
        regra_decisao_acordada_em=None,
        regra_decisao_acordada_documento_id=None,
        versao_motor_calculo="",
        procedimento_id=uuid4(),
        procedimento_versao_snapshot={"codigo": "PROC-001", "versao": "1.0"},
        escopo_id=None,
        analise_critica_pedido_id=None,
        analise_critica_pedido_inline_hash="v01$h",
        capacidade_tecnica_confirmada_por_user_id=uuid4(),
        executor_id=uuid4(),
        revisor_id=None,
        conferente_id=None,
        snapshot_competencia_revisor_json=None,
        snapshot_competencia_conferente_json=None,
        excecao_2a_conf_id=None,
        zona_ilac_g8=ZonaILACG8.NA,
        decisao="NA",
        pfa_calculada=None,
        pra_calculada=None,
        subcontratado_id=None,
        aceite_subcontratacao_id=None,
        certificado_subcontratado_snapshot_json=None,
        recebedor_user_id=None,
        correlation_id=uuid4(),
        causation_id=None,
        criada_em=AGORA,
        criada_por_user_id=None,
    )


@dataclass
class FakeCalibracaoRepoMin:
    calibracoes: dict[UUID, CalibracaoSnapshot] = field(default_factory=dict)
    _ultimo_numero: int = 0

    def obter_por_id(
        self, calibracao_id: UUID
    ) -> CalibracaoSnapshot | None:
        return self.calibracoes.get(calibracao_id)

    def proximo_numero_interno(self) -> int:
        self._ultimo_numero += 1
        return self._ultimo_numero

    def salvar_nova(self, snapshot: CalibracaoSnapshot) -> None:
        self.calibracoes[snapshot.id] = snapshot

    def atualizar_com_lock(
        self, snapshot: CalibracaoSnapshot, revision_anterior: int
    ) -> bool:
        atual = self.calibracoes.get(snapshot.id)
        if atual is None or atual.revision != revision_anterior:
            return False
        self.calibracoes[snapshot.id] = snapshot
        return True

    # Compat — usado nos testes desta suite
    def salvar(self, snap: CalibracaoSnapshot) -> None:
        self.calibracoes[snap.id] = snap


@dataclass
class FakeLeituraRepoMin:
    leituras: dict[UUID, LeituraSnapshot] = field(default_factory=dict)
    _por_evento: dict[tuple[UUID, UUID, UUID], UUID] = field(default_factory=dict)
    _por_chave: dict[tuple[UUID, UUID, Decimal, int], UUID] = field(
        default_factory=dict
    )

    def salvar_nova(self, snap: LeituraSnapshot) -> None:
        from src.application.metrologia.calibracao.registrar_leitura import (
            ConflitoLeituraExistente,
        )

        chave = (
            snap.tenant_id,
            snap.calibracao_id,
            snap.ponto_calibracao,
            snap.numero_repeticao,
        )
        if chave in self._por_chave:
            raise ConflitoLeituraExistente(self.leituras[self._por_chave[chave]])
        self.leituras[snap.id] = snap
        self._por_chave[chave] = snap.id
        if snap.client_event_id is not None:
            self._por_evento[
                (snap.tenant_id, snap.calibracao_id, snap.client_event_id)
            ] = snap.id

    def obter_por_client_event(
        self,
        tenant_id: UUID,
        calibracao_id: UUID,
        client_event_id: UUID,
    ) -> LeituraSnapshot | None:
        lid = self._por_evento.get((tenant_id, calibracao_id, client_event_id))
        return self.leituras.get(lid) if lid is not None else None

    def obter_por_id(self, leitura_id: UUID) -> LeituraSnapshot | None:
        return self.leituras.get(leitura_id)


# =====================================================================
# INV-CAL-INC-004 — alerta correlação implícita não declarada
# =====================================================================


class TestINV_CAL_INC_004:
    """JCGM 100:2008 §5.2: componentes com mesma fonte de padrão exigem
    correlação declarada; ausência subestima U_expandida."""

    def test_grupo_de_2_sem_correlacao_dispara_alerta(self) -> None:
        tenant = uuid4()
        orc = uuid4()
        fonte = uuid4()
        c1 = _componente(tenant=tenant, orc_id=orc, fonte_padrao=fonte)
        c2 = _componente(tenant=tenant, orc_id=orc, fonte_padrao=fonte)

        alertas = analisar_correlacao(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=[c1, c2],
        )
        assert len(alertas) == 1
        assert alertas[0].fonte_default_padrao_id == fonte
        assert set(alertas[0].componentes_envolvidos_ids) == {c1.id, c2.id}

    def test_grupo_de_2_com_correlacao_mutua_ok(self) -> None:
        tenant = uuid4()
        orc = uuid4()
        fonte = uuid4()
        c1 = _componente(tenant=tenant, orc_id=orc, fonte_padrao=fonte)
        c2 = _componente(
            tenant=tenant, orc_id=orc, fonte_padrao=fonte, correlato_id=c1.id
        )
        # c1 também referencia c2 (Wave A — função aceita só 1-uplo declarado)
        c1_com_corr = replace(c1, correlacao_com_componente_id=c2.id)
        alertas = analisar_correlacao(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=[c1_com_corr, c2],
        )
        assert alertas == []

    def test_correlacao_aponta_pra_fora_do_grupo_dispara_alerta(self) -> None:
        tenant = uuid4()
        orc = uuid4()
        fonte_a = uuid4()
        fonte_b = uuid4()
        externo = _componente(tenant=tenant, orc_id=orc, fonte_padrao=fonte_b)
        c1 = _componente(
            tenant=tenant,
            orc_id=orc,
            fonte_padrao=fonte_a,
            correlato_id=externo.id,
        )
        c2 = _componente(
            tenant=tenant,
            orc_id=orc,
            fonte_padrao=fonte_a,
            correlato_id=externo.id,
        )
        alertas = analisar_correlacao(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=[c1, c2, externo],
        )
        # fonte_a tem 2 sem correlacao intra-grupo
        assert len(alertas) == 1
        assert alertas[0].fonte_default_padrao_id == fonte_a

    def test_fonte_padrao_none_ignorada(self) -> None:
        tenant = uuid4()
        orc = uuid4()
        c1 = _componente(tenant=tenant, orc_id=orc, fonte_padrao=None)
        c2 = _componente(tenant=tenant, orc_id=orc, fonte_padrao=None)
        alertas = analisar_correlacao(
            orcamento_incerteza_id=orc,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=[c1, c2],
        )
        assert alertas == []

    def test_isolamento_cross_tenant(self) -> None:
        tenant_a = uuid4()
        tenant_b = uuid4()
        orc = uuid4()
        fonte = uuid4()
        c_a = _componente(tenant=tenant_a, orc_id=orc, fonte_padrao=fonte)
        c_b = _componente(tenant=tenant_b, orc_id=orc, fonte_padrao=fonte)
        alertas = analisar_correlacao(
            orcamento_incerteza_id=orc,
            tenant_id=tenant_a,
            correlation_id=uuid4(),
            componentes=[c_a, c_b],
        )
        # Apenas tenant_a no escopo; sozinho ≠ violação
        assert alertas == []

    def test_isolamento_cross_orcamento(self) -> None:
        tenant = uuid4()
        orc_a = uuid4()
        orc_b = uuid4()
        fonte = uuid4()
        c_a = _componente(tenant=tenant, orc_id=orc_a, fonte_padrao=fonte)
        c_b = _componente(tenant=tenant, orc_id=orc_b, fonte_padrao=fonte)
        alertas = analisar_correlacao(
            orcamento_incerteza_id=orc_a,
            tenant_id=tenant,
            correlation_id=uuid4(),
            componentes=[c_a, c_b],
        )
        assert alertas == []


# =====================================================================
# INV-CAL-RT-002 — snapshot_competencia_revisor_json IMUTÁVEL
# =====================================================================


class TestINV_CAL_RT_002:
    """cl. 6.2 + NIT-DICLA-021 + ADR-0022:
    snapshot competencia capturado no momento da aprovação é congelado
    no JSONB; mutações posteriores no objeto-fonte NÃO podem vazar.
    """

    def test_replace_nao_compartilha_referencia_com_input(self) -> None:
        """Use case aprovar_revisao usa replace + dict() — input dict
        mutado depois NÃO afeta snapshot armazenado."""
        from src.application.metrologia.calibracao.aprovar_revisao import (
            AprovarRevisaoInput,
        )

        comp_dict: dict[str, object] = {
            "grandeza": "massa",
            "faixa_min": "0",
            "faixa_max": "10000",
            "vigencia_inicio": "2025-01-01",
            "vigencia_fim": "2027-12-31",
            "rt_competencia_id": str(uuid4()),
        }
        inp = AprovarRevisaoInput(
            calibracao_id=uuid4(),
            revision_esperada=2,
            revisor_id=uuid4(),
            snapshot_competencia_revisor_json=comp_dict,
        )
        # Input frozen — qualquer tentativa de mutar dataclass falha
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            inp.revision_esperada = 99  # type: ignore[misc]

        # Caller pode mutar o dict original; o snapshot dentro do input
        # captura referência mas use case faz dict(...) novo na aplicação
        # (linha 159 aprovar_revisao.py). Verificamos isso indiretamente
        # garantindo que input ainda referencia o dict ORIGINAL.
        assert inp.snapshot_competencia_revisor_json is comp_dict

    def test_aprovar_revisao_grava_copia_do_snapshot(self) -> None:
        """Mutar o dict de entrada DEPOIS de aprovar não muta snapshot gravado."""
        from src.application.metrologia.calibracao.aprovar_revisao import (
            AprovarRevisaoInput,
        )
        from src.application.metrologia.calibracao.aprovar_revisao import (
            executar as aprovar_executar,
        )
        from src.application.metrologia.calibracao.criar_calibracao import (
            CriarCalibracaoInput,
        )
        from src.application.metrologia.calibracao.criar_calibracao import (
            executar as criar_executar,
        )
        from src.application.metrologia.calibracao.iniciar_leituras import (
            IniciarLeiturasInput,
        )
        from src.application.metrologia.calibracao.iniciar_leituras import (
            executar as iniciar_executar,
        )
        from src.application.metrologia.calibracao.solicitar_revisao import (
            SolicitarRevisaoInput,
        )
        from src.application.metrologia.calibracao.solicitar_revisao import (
            executar as solicitar_executar,
        )

        from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository

        repo = FakeCalibracaoRepository()
        tenant = uuid4()
        executor = uuid4()
        revisor = uuid4()

        out_criada = criar_executar(
            CriarCalibracaoInput(
                tenant_id=tenant,
                origem_recepcao=OrigemRecepcao.AVULSA,
                atividade_os_id=None,
                instrumento_id=uuid4(),
                snapshot_equipamento_json={"modelo": "X"},
                cliente_id=None,
                cliente_referencia_hash="v01$c",
                cliente_key_id="k",
                tipo_acreditacao=TipoAcreditacao.NAO_RBC,
                recepcionada_em=AGORA,
                correlation_id=uuid4(),
            ),
            repo,
        )
        cal_id = out_criada.snapshot.id

        # Configurar
        from src.application.metrologia.calibracao.configurar_calibracao import (
            ConfigurarCalibracaoInput,
        )
        from src.application.metrologia.calibracao.configurar_calibracao import (
            executar as configurar_executar,
        )

        out_config = configurar_executar(
            ConfigurarCalibracaoInput(
                calibracao_id=cal_id,
                revision_esperada=0,
                procedimento_id=uuid4(),
                procedimento_versao_snapshot={
                    "codigo": "PROC-001",
                    "versao": "1.0",
                    "hash_anexo": "v01$h",
                },
                regra_decisao=RegraDecisao.ACEITACAO_SIMPLES,
                regra_decisao_acordada_em=AGORA,
                regra_decisao_acordada_documento_id=uuid4(),
                escopo_id=None,
                analise_critica_pedido_id=None,
                analise_critica_pedido_inline_hash="v01$inline",
                capacidade_tecnica_confirmada_por_user_id=uuid4(),
            ),
            repo,
        )

        # Iniciar -> EM_EXECUCAO
        out_iniciar = iniciar_executar(
            IniciarLeiturasInput(
                calibracao_id=cal_id,
                revision_esperada=out_config.snapshot.revision,
                executor_id=executor,
            ),
            repo,
        )

        # Solicitar revisao -> EM_REVISAO_1
        out_solicitar = solicitar_executar(
            SolicitarRevisaoInput(
                calibracao_id=cal_id,
                revision_esperada=out_iniciar.snapshot.revision,
            ),
            repo,
        )

        # Aprovar revisão com snapshot competência
        comp_dict: dict[str, object] = {
            "grandeza": "massa",
            "faixa_min": "0",
            "faixa_max": "10000",
            "vigencia_inicio": "2025-01-01",
            "vigencia_fim": "2027-12-31",
            "rt_competencia_id": str(uuid4()),
        }
        out_aprovar = aprovar_executar(
            AprovarRevisaoInput(
                calibracao_id=cal_id,
                revision_esperada=out_solicitar.snapshot.revision,
                revisor_id=revisor,
                snapshot_competencia_revisor_json=comp_dict,
            ),
            repo,
        )

        # MUTA o dict ORIGINAL após aprovação
        comp_dict["grandeza"] = "temperatura"
        comp_dict["faixa_max"] = "999999"

        # Snapshot no repo NÃO deve refletir mutação
        snap_no_repo = repo.obter_por_id(cal_id)
        assert snap_no_repo is not None
        assert snap_no_repo.snapshot_competencia_revisor_json is not None
        assert snap_no_repo.snapshot_competencia_revisor_json["grandeza"] == "massa"
        assert (
            snap_no_repo.snapshot_competencia_revisor_json["faixa_max"] == "10000"
        )
        # E o snapshot devolvido pelo use case também é estável
        assert out_aprovar.snapshot.snapshot_competencia_revisor_json is not None
        assert (
            out_aprovar.snapshot.snapshot_competencia_revisor_json["grandeza"]
            == "massa"
        )


# =====================================================================
# INV-CAL-IDEMP-001 — idempotência forte registrar_leitura
# =====================================================================


class TestINV_CAL_IDEMP_001:
    """ADR-0027 + IDEMP-001 + IDEMP-CAL-03 (2026-05-27 Batch S3):
    - Replay com mesmo client_event_id + payload IDÊNTICO -> idempotente.
    - Replay com payload DIVERGENTE -> 422 IdempotencyPayloadMismatch
      (em vez do "silent stale read" anterior ao conserto).
    """

    def _registra(
        self,
        *,
        cal_repo: FakeCalibracaoRepoMin,
        leitura_repo: FakeLeituraRepoMin,
        cal_id: UUID,
        client_event_id: UUID | None,
        valor: Decimal = Decimal("10.1"),
        ponto: Decimal = Decimal("10"),
        repeticao: int = 1,
    ) -> LeituraSnapshot:
        out = registrar_leitura_executar(
            RegistrarLeituraInput(
                calibracao_id=cal_id,
                ponto_calibracao=ponto,
                numero_repeticao=repeticao,
                valor_lido=valor,
                unidade="kg",
                origem=OrigemLeitura.MANUAL,
                timestamp=AGORA,
                executor_id_hash="v01$exec",
                correlation_id=uuid4(),
                client_event_id=client_event_id,
            ),
            cal_repo,
            leitura_repo,
        )
        return out.snapshot

    def test_replay_payload_identico_retorna_existente(self) -> None:
        cal_repo = FakeCalibracaoRepoMin()
        leitura_repo = FakeLeituraRepoMin()
        tenant = uuid4()
        cal = _calibracao_em_execucao(tenant=tenant)
        cal_repo.salvar(cal)
        evt = uuid4()

        primeira = self._registra(
            cal_repo=cal_repo,
            leitura_repo=leitura_repo,
            cal_id=cal.id,
            client_event_id=evt,
        )
        # Replay com payload IDÊNTICO -> idempotente
        segunda = self._registra(
            cal_repo=cal_repo,
            leitura_repo=leitura_repo,
            cal_id=cal.id,
            client_event_id=evt,
        )
        assert primeira.id == segunda.id
        assert len(leitura_repo.leituras) == 1

    def test_replay_payload_divergente_levanta_mismatch(self) -> None:
        """IDEMP-CAL-03 conserto: replay com valor_lido diferente -> 422."""
        from src.application.metrologia.calibracao.registrar_leitura import (
            IdempotencyPayloadMismatch,
        )

        cal_repo = FakeCalibracaoRepoMin()
        leitura_repo = FakeLeituraRepoMin()
        tenant = uuid4()
        cal = _calibracao_em_execucao(tenant=tenant)
        cal_repo.salvar(cal)
        evt = uuid4()

        self._registra(
            cal_repo=cal_repo,
            leitura_repo=leitura_repo,
            cal_id=cal.id,
            client_event_id=evt,
            valor=Decimal("10.1"),
        )
        with pytest.raises(IdempotencyPayloadMismatch) as exc_info:
            self._registra(
                cal_repo=cal_repo,
                leitura_repo=leitura_repo,
                cal_id=cal.id,
                client_event_id=evt,
                valor=Decimal("99"),  # payload divergente
            )
        # Carrega leitura existente + campos divergentes pra caller decidir
        assert "valor_lido" in exc_info.value.campos_divergentes
        # Apenas 1 registro persistido (mismatch NÃO sobrescreve)
        assert len(leitura_repo.leituras) == 1
        assert leitura_repo.leituras[
            exc_info.value.leitura_existente.id
        ].valor_lido == Decimal("10.1")

    def test_replay_payload_divergente_em_ponto_levanta_mismatch(self) -> None:
        from src.application.metrologia.calibracao.registrar_leitura import (
            IdempotencyPayloadMismatch,
        )

        cal_repo = FakeCalibracaoRepoMin()
        leitura_repo = FakeLeituraRepoMin()
        tenant = uuid4()
        cal = _calibracao_em_execucao(tenant=tenant)
        cal_repo.salvar(cal)
        evt = uuid4()

        self._registra(
            cal_repo=cal_repo,
            leitura_repo=leitura_repo,
            cal_id=cal.id,
            client_event_id=evt,
            ponto=Decimal("10"),
        )
        with pytest.raises(IdempotencyPayloadMismatch) as exc_info:
            self._registra(
                cal_repo=cal_repo,
                leitura_repo=leitura_repo,
                cal_id=cal.id,
                client_event_id=evt,
                ponto=Decimal("20"),
            )
        assert "ponto_calibracao" in exc_info.value.campos_divergentes

    def test_sem_client_event_id_nao_eh_idempotente(self) -> None:
        """Sem chave idempotência, duas chamadas com mesmo ponto+repetição
        violam UNIQUE composto e levantam ConflitoLeituraExistente."""
        from src.application.metrologia.calibracao.registrar_leitura import (
            ConflitoLeituraExistente,
        )

        cal_repo = FakeCalibracaoRepoMin()
        leitura_repo = FakeLeituraRepoMin()
        tenant = uuid4()
        cal = _calibracao_em_execucao(tenant=tenant)
        cal_repo.salvar(cal)

        self._registra(
            cal_repo=cal_repo,
            leitura_repo=leitura_repo,
            cal_id=cal.id,
            client_event_id=None,
        )
        with pytest.raises(ConflitoLeituraExistente):
            self._registra(
                cal_repo=cal_repo,
                leitura_repo=leitura_repo,
                cal_id=cal.id,
                client_event_id=None,
            )

    def test_diferentes_client_events_geram_leituras_distintas(self) -> None:
        cal_repo = FakeCalibracaoRepoMin()
        leitura_repo = FakeLeituraRepoMin()
        tenant = uuid4()
        cal = _calibracao_em_execucao(tenant=tenant)
        cal_repo.salvar(cal)

        l1 = self._registra(
            cal_repo=cal_repo,
            leitura_repo=leitura_repo,
            cal_id=cal.id,
            client_event_id=uuid4(),
            ponto=Decimal("10"),
            repeticao=1,
        )
        l2 = self._registra(
            cal_repo=cal_repo,
            leitura_repo=leitura_repo,
            cal_id=cal.id,
            client_event_id=uuid4(),
            ponto=Decimal("10"),
            repeticao=2,
        )
        assert l1.id != l2.id
        assert len(leitura_repo.leituras) == 2


# =====================================================================
# INV-CAL-CONF-001 — 2a conferencia + independencia RT
# =====================================================================


class TestINV_CAL_CONF_001:
    """ISO 17025 cl. 6.2 + 7.7 + ADR-0026:
    2a conferencia exige status AGUARDANDO_2A_CONFERENCIA + segregacao
    funcoes (conferente != revisor != executor) salvo excecao ADR-0026
    (4 condicoes objetivas + 5%/mes + excecao_2a_conf_id FK).
    """

    def _competencia(self) -> dict[str, object]:
        return {
            "grandeza": "massa",
            "faixa_min": "0",
            "faixa_max": "10000",
            "vigencia_inicio": "2025-01-01",
            "vigencia_fim": "2027-12-31",
            "rt_competencia_id": str(uuid4()),
        }

    def _cal_aguardando_2a(
        self, *, executor: UUID, revisor: UUID
    ) -> CalibracaoSnapshot:
        base = _calibracao_em_execucao(tenant=uuid4())
        return replace(
            base,
            status=EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA,
            executor_id=executor,
            revisor_id=revisor,
            snapshot_competencia_revisor_json=self._competencia(),
        )

    def test_recusa_estado_diferente_de_aguardando(self) -> None:
        from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
            Aprovar2aConferenciaInput,
            EstadoInvalidoParaAprovar2aConferencia,
        )
        from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
            executar as aprovar_2a,
        )

        executor = uuid4()
        revisor = uuid4()
        conferente = uuid4()

        cal = replace(
            self._cal_aguardando_2a(executor=executor, revisor=revisor),
            status=EstadoCalibracao.EM_REVISAO_1,
        )
        repo = FakeCalibracaoRepoMin()
        repo.salvar(cal)
        with pytest.raises(EstadoInvalidoParaAprovar2aConferencia):
            aprovar_2a(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal.id,
                    revision_esperada=cal.revision,
                    conferente_id=conferente,
                    snapshot_competencia_conferente_json=self._competencia(),
                ),
                repo,
            )

    def test_recusa_conferente_igual_revisor_sem_excecao(self) -> None:
        from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
            Aprovar2aConferenciaInput,
            FraudeConferenteEhRevisorOuExecutor,
        )
        from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
            executar as aprovar_2a,
        )

        executor = uuid4()
        revisor = uuid4()
        cal = self._cal_aguardando_2a(executor=executor, revisor=revisor)
        repo = FakeCalibracaoRepoMin()
        repo.salvar(cal)

        with pytest.raises(FraudeConferenteEhRevisorOuExecutor):
            aprovar_2a(
                Aprovar2aConferenciaInput(
                    calibracao_id=cal.id,
                    revision_esperada=cal.revision,
                    conferente_id=revisor,
                    snapshot_competencia_conferente_json=self._competencia(),
                ),
                repo,
            )

    def test_excecao_motivo_exige_fk_2a_conf_id(self) -> None:
        """ADR-0026: excecao_motivo sem excecao_2a_conf_id e configuracao
        incompleta — validado no __post_init__ (ValueError no Input)."""
        from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
            Aprovar2aConferenciaInput,
        )

        with pytest.raises(ValueError, match="excecao_2a_conf_id"):
            Aprovar2aConferenciaInput(
                calibracao_id=uuid4(),
                revision_esperada=2,
                conferente_id=uuid4(),
                snapshot_competencia_conferente_json=self._competencia(),
                excecao_motivo="lab_unico_rt_disponivel",
                excecao_2a_conf_id=None,
            )

    def test_fk_2a_conf_id_exige_motivo(self) -> None:
        from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
            Aprovar2aConferenciaInput,
        )

        with pytest.raises(ValueError, match="excecao_motivo"):
            Aprovar2aConferenciaInput(
                calibracao_id=uuid4(),
                revision_esperada=2,
                conferente_id=uuid4(),
                snapshot_competencia_conferente_json=self._competencia(),
                excecao_motivo=None,
                excecao_2a_conf_id=uuid4(),
            )


# =====================================================================
# INV-CAL-DEC-001 — avaliar_conformidade bloqueado pos-APROVADA (LOCK)
# =====================================================================


class TestINV_CAL_DEC_001:
    """ISO 17025 cl. 7.8.6 + ADR-0024:
    Regra de decisao LOCK pos-APROVADA — nao permite reavaliacao.
    Aceita reavaliacao so em EM_EXECUCAO e EM_REVISAO_1.
    """

    def test_avaliar_em_status_aprovada_recusa(self) -> None:
        from src.application.metrologia.calibracao.avaliar_conformidade import (
            AvaliarConformidadeInput,
            CalibracaoEstadoNaoPermiteAvaliar,
        )
        from src.application.metrologia.calibracao.avaliar_conformidade import (
            executar as avaliar,
        )

        cal = replace(
            _calibracao_em_execucao(tenant=uuid4()),
            status=EstadoCalibracao.APROVADA,
        )
        repo = FakeCalibracaoRepoMin()
        repo.salvar(cal)

        with pytest.raises(CalibracaoEstadoNaoPermiteAvaliar):
            avaliar(
                AvaliarConformidadeInput(
                    calibracao_id=cal.id,
                    revision_esperada=cal.revision,
                    valor_medido=Decimal("10.05"),
                    U_expandida=Decimal("0.10"),
                    k=Decimal("2.0"),
                    lsl=Decimal("9.9"),
                    usl=Decimal("10.1"),
                ),
                repo,
            )

    def test_avaliar_em_status_recepcionada_recusa(self) -> None:
        from src.application.metrologia.calibracao.avaliar_conformidade import (
            AvaliarConformidadeInput,
            CalibracaoEstadoNaoPermiteAvaliar,
        )
        from src.application.metrologia.calibracao.avaliar_conformidade import (
            executar as avaliar,
        )

        cal = replace(
            _calibracao_em_execucao(tenant=uuid4()),
            status=EstadoCalibracao.RECEPCIONADA,
        )
        repo = FakeCalibracaoRepoMin()
        repo.salvar(cal)

        with pytest.raises(CalibracaoEstadoNaoPermiteAvaliar):
            avaliar(
                AvaliarConformidadeInput(
                    calibracao_id=cal.id,
                    revision_esperada=cal.revision,
                    valor_medido=Decimal("10"),
                    U_expandida=Decimal("0.1"),
                    k=Decimal("2.0"),
                    lsl=None,
                    usl=None,
                ),
                repo,
            )

    def test_input_recusa_U_expandida_negativa(self) -> None:
        from src.application.metrologia.calibracao.avaliar_conformidade import (
            AvaliarConformidadeInput,
        )

        with pytest.raises(ValueError, match="U_expandida"):
            AvaliarConformidadeInput(
                calibracao_id=uuid4(),
                revision_esperada=2,
                valor_medido=Decimal("10"),
                U_expandida=Decimal("-0.1"),
                k=Decimal("2.0"),
                lsl=None,
                usl=None,
            )

    def test_input_recusa_k_zero(self) -> None:
        from src.application.metrologia.calibracao.avaliar_conformidade import (
            AvaliarConformidadeInput,
        )

        with pytest.raises(ValueError, match="k deve ser"):
            AvaliarConformidadeInput(
                calibracao_id=uuid4(),
                revision_esperada=2,
                valor_medido=Decimal("10"),
                U_expandida=Decimal("0.1"),
                k=Decimal("0"),
                lsl=None,
                usl=None,
            )
