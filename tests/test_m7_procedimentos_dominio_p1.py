"""M7 Fatia 1a (T-PROC-010..014) — domínio puro procedimentos-calibracao.

Cobre enums + entities + transições + Protocol, sem Django/PG. Molde
`test_m6_escopos_cmc_dominio_p1.py`.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
    ProcedimentoUsado,
)
from src.domain.metrologia.procedimentos_calibracao.enums import (
    EstadoProcedimento,
    TipoMetodo,
)
from src.domain.metrologia.procedimentos_calibracao.repository import (
    ProcedimentoRepository,
)
from src.domain.metrologia.procedimentos_calibracao.transicoes import (
    ControleDocumentalIncompletoError,
    metodo_exige_validacao_pendente,
    pode_transicionar,
    validar_controle_documental,
    validar_motivo_revogacao,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

T0 = datetime(2026, 6, 1, tzinfo=UTC)


def _proc(**kw) -> ProcedimentoSnapshot:
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


# --------------------------------------------------------------------------
class TestEnums:
    def test_estado_propriedades(self):
        assert EstadoProcedimento.PUBLICADO.consultavel_para_resolucao
        assert not EstadoProcedimento.RASCUNHO.consultavel_para_resolucao
        assert not EstadoProcedimento.REVOGADO.consultavel_para_resolucao
        assert EstadoProcedimento.RASCUNHO.editavel
        assert not EstadoProcedimento.PUBLICADO.editavel
        assert EstadoProcedimento.RASCUNHO.publicavel
        assert EstadoProcedimento.REVOGADO.terminal

    def test_tipo_metodo_exige_validacao(self):
        assert not TipoMetodo.NORMALIZADO.exige_validacao
        assert TipoMetodo.NAO_NORMALIZADO.exige_validacao
        assert TipoMetodo.MODIFICADO.exige_validacao


class TestProcedimentoSnapshot:
    def test_vigente_em_janela(self):
        p = _proc(vigencia_inicio=T0)
        assert p.vigente_em(datetime(2026, 6, 2, tzinfo=UTC))
        assert not p.vigente_em(datetime(2026, 5, 1, tzinfo=UTC))  # antes

    def test_revogado_sai_da_vigencia(self):
        p = _proc(revogado_em=T0)
        assert not p.vigente_em(datetime(2026, 6, 2, tzinfo=UTC))

    def test_consultavel_so_publicado(self):
        em = datetime(2026, 6, 2, tzinfo=UTC)
        assert _proc(estado=EstadoProcedimento.PUBLICADO).consultavel(em)
        assert not _proc(estado=EstadoProcedimento.RASCUNHO).consultavel(em)
        assert not _proc(estado=EstadoProcedimento.REVOGADO).consultavel(em)

    def test_cobre_faixa_contencao_total(self):
        p = _proc(faixa=FaixaMedicao(Decimal("0"), Decimal("1000"), "g"))
        assert p.cobre_faixa(FaixaMedicao(Decimal("10"), Decimal("20"), "g"))
        assert not p.cobre_faixa(FaixaMedicao(Decimal("900"), Decimal("2000"), "g"))
        assert not p.cobre_faixa(FaixaMedicao(Decimal("10"), Decimal("20"), "kg"))

    def test_snapshot_imutavel(self):
        p = _proc()
        with pytest.raises(FrozenInstanceError):
            campo = "codigo"
            setattr(p, campo, "X")


class TestProcedimentoUsado:
    def _usado(self) -> ProcedimentoUsado:
        return ProcedimentoUsado(
            procedimento_id=uuid4(),
            codigo="PC-MASSA-001",
            versao=2,
            numero_revisao="Rev. 04",
            titulo="Massa",
            grandeza=Grandeza.MASSA,
            faixa_procedimento=FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
            faixa_solicitada=FaixaMedicao(Decimal("10"), Decimal("20"), "g"),
            metodo_norma="OIML R76",
            tipo_metodo=TipoMetodo.NORMALIZADO,
            anexo_pdf_sha256="deadbeef",
            perfil_no_evento="A",
            data_referencia=date(2026, 6, 1),
            vigencia_inicio=T0,
            contido=True,
        )

    def test_snapshot_minimo_bate_contrato_m4(self):
        # M4 ConfigurarCalibracaoInput exige {codigo, versao, hash_anexo}
        m = self._usado().snapshot_minimo()
        assert set(m) == {"codigo", "versao", "hash_anexo"}
        assert m["codigo"] == "PC-MASSA-001"
        assert m["versao"] == "2"
        assert m["hash_anexo"] == "deadbeef"

    def test_vo_imutavel(self):
        u = self._usado()
        with pytest.raises(FrozenInstanceError):
            campo = "versao"
            setattr(u, campo, 9)


class TestTransicoes:
    def test_matriz_transicoes(self):
        E = EstadoProcedimento
        assert pode_transicionar(E.RASCUNHO, E.PUBLICADO)
        assert pode_transicionar(E.RASCUNHO, E.REVOGADO)
        assert pode_transicionar(E.PUBLICADO, E.REVOGADO)
        assert not pode_transicionar(E.PUBLICADO, E.RASCUNHO)
        assert not pode_transicionar(E.REVOGADO, E.PUBLICADO)
        assert not pode_transicionar(E.REVOGADO, E.REVOGADO)

    def test_motivo_revogacao_curto_levanta(self):
        with pytest.raises(ValueError, match=">= 10"):
            validar_motivo_revogacao("curto")
        validar_motivo_revogacao("revogado por revisao normativa 2026")  # ok

    def test_controle_documental_incompleto_bloqueia(self):
        # INV-PROC-009 — falta aprovado_em
        with pytest.raises(ControleDocumentalIncompletoError, match="aprovado_em"):
            validar_controle_documental(
                numero_revisao="Rev. 03", aprovado_em=None, aprovado_por_id=uuid4()
            )
        # falta numero_revisao
        with pytest.raises(ControleDocumentalIncompletoError, match="numero_revisao"):
            validar_controle_documental(
                numero_revisao="  ", aprovado_em=T0, aprovado_por_id=uuid4()
            )
        # completo passa
        validar_controle_documental(
            numero_revisao="Rev. 03", aprovado_em=T0, aprovado_por_id=uuid4()
        )

    def test_metodo_exige_validacao_pendente_fail_open_lazy(self):
        # perfil A + não-normalizado sem registro -> pendente (aviso, não bloqueia)
        assert metodo_exige_validacao_pendente(
            tipo_metodo=TipoMetodo.NAO_NORMALIZADO, perfil="A", registro_validacao_id=None
        )
        # com registro -> não pende
        assert not metodo_exige_validacao_pendente(
            tipo_metodo=TipoMetodo.NAO_NORMALIZADO, perfil="A", registro_validacao_id=uuid4()
        )
        # normalizado -> nunca pende
        assert not metodo_exige_validacao_pendente(
            tipo_metodo=TipoMetodo.NORMALIZADO, perfil="A", registro_validacao_id=None
        )
        # B/C/D -> nunca pende (não-acreditado)
        assert not metodo_exige_validacao_pendente(
            tipo_metodo=TipoMetodo.NAO_NORMALIZADO, perfil="D", registro_validacao_id=None
        )


class TestProtocol:
    def test_fake_satisfaz_protocol(self):
        class _Fake:
            def obter_por_id(self, procedimento_id): ...
            def existe_chave(self, *, tenant_id, codigo, versao): ...
            def proxima_versao(self, *, tenant_id, codigo): ...
            def salvar_novo(self, snapshot): ...
            def atualizar_com_lock(self, snapshot, revision_anterior): ...
            def vigente_anterior(self, *, tenant_id, codigo, grandeza, faixa): ...
            def encerrar_vigencia(self, *, procedimento_id, vigencia_fim, revision_anterior): ...
            def revogar(self, *, procedimento_id, revogado_em, motivo): ...
            def vigente_em(self, *, tenant_id, grandeza, faixa, em): ...

        assert isinstance(_Fake(), ProcedimentoRepository)
