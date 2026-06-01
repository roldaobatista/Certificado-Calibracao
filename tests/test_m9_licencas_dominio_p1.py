"""Testes do domínio puro M9 licencas-acreditacoes — Fatia 1a (T-LIC-015).

Puro (sem Django/PG). Cobre status calculado, tipo×perfil (INV-LIC-PERFIL-001),
anexo obrigatório (INV-LIC-ANEXO-001), fronteira de bloqueio por tipo (D-LIC-5) e
pré-condições do modo emergencial (D-LIC-6/7 / INV-033). TST-004.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from src.domain.metrologia.licencas_acreditacoes.entities import (
    BloqueioOperacional,
    DocumentoRegulatorio,
    RevisaoDocumento,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    MotivoRevisao,
    StatusDocumento,
    TipoBloqueio,
    TipoDocumentoRegulatorio,
)
from src.domain.metrologia.licencas_acreditacoes.erros import (
    AnexoObrigatorioError,
    ModoEmergencialInvalidoError,
    PerfilNaoAutorizaCGCREError,
    VigenciaInvalidaError,
)
from src.domain.metrologia.licencas_acreditacoes.transicoes import (
    calcular_status,
    fronteira_bloqueio,
    validar_anexo,
    validar_modo_emergencial,
    validar_tipo_x_perfil,
)

HOJE = date(2026, 6, 1)


# --- status calculado (4 bordas) -------------------------------------------------
class TestStatusCalculado:
    def test_vigente(self) -> None:
        assert calcular_status(vigencia_fim=date(2027, 1, 1), hoje=HOJE) is StatusDocumento.VIGENTE

    def test_vence_em_breve_dentro_janela(self) -> None:
        assert calcular_status(vigencia_fim=date(2026, 6, 20), hoje=HOJE) is StatusDocumento.VENCE_EM_BREVE

    def test_vence_em_breve_borda_inclusiva_30d(self) -> None:
        assert calcular_status(vigencia_fim=date(2026, 7, 1), hoje=HOJE) is StatusDocumento.VENCE_EM_BREVE

    def test_vencido(self) -> None:
        assert calcular_status(vigencia_fim=date(2026, 5, 31), hoje=HOJE) is StatusDocumento.VENCIDO

    def test_em_renovacao_tem_precedencia(self) -> None:
        # mesmo vencido, se em renovação → EM_RENOVACAO.
        assert (
            calcular_status(vigencia_fim=date(2026, 5, 1), hoje=HOJE, em_renovacao=True)
            is StatusDocumento.EM_RENOVACAO
        )

    def test_status_vigente_e_vence_breve_sao_operaveis(self) -> None:
        assert StatusDocumento.VIGENTE.operavel
        assert StatusDocumento.VENCE_EM_BREVE.operavel
        assert not StatusDocumento.VENCIDO.operavel


# --- tipo × perfil (INV-LIC-PERFIL-001 + RBC-M9-05) ------------------------------
class TestTipoXPerfil:
    @pytest.mark.parametrize("perfil", ["A", "B", "C"])
    def test_cgcre_aceita_abc_com_escopo(self, perfil: str) -> None:
        validar_tipo_x_perfil(
            tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE, perfil=perfil, escopo="Massa 1g-10kg"
        )  # não levanta

    def test_cgcre_perfil_d_rejeitado(self) -> None:
        with pytest.raises(PerfilNaoAutorizaCGCREError):
            validar_tipo_x_perfil(
                tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE, perfil="D", escopo="Massa"
            )

    def test_cgcre_sem_escopo_rejeitado(self) -> None:
        with pytest.raises(VigenciaInvalidaError):
            validar_tipo_x_perfil(
                tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE, perfil="A", escopo="   "
            )

    @pytest.mark.parametrize("perfil", ["A", "B", "C", "D"])
    def test_tipo_nao_cgcre_qualquer_perfil(self, perfil: str) -> None:
        validar_tipo_x_perfil(
            tipo=TipoDocumentoRegulatorio.ALVARA, perfil=perfil, escopo=""
        )  # alvará não exige perfil nem escopo


# --- anexo obrigatório (INV-LIC-ANEXO-001) ---------------------------------------
class TestAnexoObrigatorio:
    def test_anexo_presente_ok(self) -> None:
        validar_anexo(anexo_sha256="a" * 64)

    @pytest.mark.parametrize("vazio", ["", "   "])
    def test_anexo_vazio_rejeitado(self, vazio: str) -> None:
        with pytest.raises(AnexoObrigatorioError):
            validar_anexo(anexo_sha256=vazio)


# --- fronteira de bloqueio por tipo (D-LIC-5 / RBC-M9-01) ------------------------
class TestFronteiraBloqueio:
    def test_acreditacao_cgcre_rebaixa_nunca_409(self) -> None:
        assert fronteira_bloqueio(TipoDocumentoRegulatorio.ACREDITACAO_CGCRE) is TipoBloqueio.REBAIXA_RBC

    @pytest.mark.parametrize(
        "tipo",
        [
            TipoDocumentoRegulatorio.ART,
            TipoDocumentoRegulatorio.RRT,
            TipoDocumentoRegulatorio.CERT_DIGITAL_A3,
        ],
    )
    def test_signatario_vencido_hard_409(self, tipo: TipoDocumentoRegulatorio) -> None:
        assert fronteira_bloqueio(tipo) is TipoBloqueio.HARD_409

    def test_alvara_nenhum(self) -> None:
        assert fronteira_bloqueio(TipoDocumentoRegulatorio.ALVARA) is TipoBloqueio.NENHUM


# --- modo emergencial (INV-033 / D-LIC-6/7) --------------------------------------
class TestModoEmergencial:
    JUST_OK = "x" * 100

    def test_cgcre_libera_apenas_nao_rbc(self) -> None:
        assert (
            validar_modo_emergencial(
                tipo_documento=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
                justificativa=self.JUST_OK,
                assinatura_a3_id=uuid4(),
                janela_dias=7,
            )
            is True
        )

    def test_art_nao_restringe_a_nao_rbc(self) -> None:
        assert (
            validar_modo_emergencial(
                tipo_documento=TipoDocumentoRegulatorio.ART,
                justificativa=self.JUST_OK,
                assinatura_a3_id=uuid4(),
                janela_dias=3,
            )
            is False
        )

    def test_justificativa_curta_rejeitada(self) -> None:
        with pytest.raises(ModoEmergencialInvalidoError):
            validar_modo_emergencial(
                tipo_documento=TipoDocumentoRegulatorio.ART,
                justificativa="curta",
                assinatura_a3_id=uuid4(),
                janela_dias=3,
            )

    def test_sem_a3_rejeitada(self) -> None:
        with pytest.raises(ModoEmergencialInvalidoError):
            validar_modo_emergencial(
                tipo_documento=TipoDocumentoRegulatorio.ART,
                justificativa=self.JUST_OK,
                assinatura_a3_id=None,
                janela_dias=3,
            )

    @pytest.mark.parametrize("janela", [0, 8, 30])
    def test_janela_fora_limite_rejeitada(self, janela: int) -> None:
        with pytest.raises(ModoEmergencialInvalidoError):
            validar_modo_emergencial(
                tipo_documento=TipoDocumentoRegulatorio.ART,
                justificativa=self.JUST_OK,
                assinatura_a3_id=uuid4(),
                janela_dias=janela,
            )


# --- entidades (vigência canônica ADR-0030 + WORM) -------------------------------
class TestEntidades:
    def _doc(self, **kw: object) -> DocumentoRegulatorio:
        base: dict[str, object] = {
            "id": uuid4(), "tenant_id": uuid4(), "tipo": TipoDocumentoRegulatorio.ALVARA,
            "numero": "123", "orgao_emissor": "Prefeitura",
            "vigencia_inicio": date(2026, 1, 1), "vigencia_fim": date(2027, 1, 1),
            "bloqueante": False, "criado_em": datetime(2026, 1, 1, tzinfo=UTC),
            "criado_por": uuid4(),
        }
        base.update(kw)
        return DocumentoRegulatorio(**base)  # type: ignore[arg-type]

    def test_documento_vigencia_invertida_rejeitada(self) -> None:
        with pytest.raises(VigenciaInvalidaError):
            self._doc(vigencia_inicio=date(2027, 1, 1), vigencia_fim=date(2026, 1, 1))

    def test_documento_valido_ok(self) -> None:
        doc = self._doc()
        assert doc.tipo is TipoDocumentoRegulatorio.ALVARA

    def test_revisao_sem_sha256_rejeitada(self) -> None:
        with pytest.raises(VigenciaInvalidaError):
            RevisaoDocumento(
                id=uuid4(), tenant_id=uuid4(), documento_id=uuid4(), numero_revisao=1,
                data_emissao=date(2026, 1, 1), data_validade=date(2027, 1, 1),
                anexo_id=uuid4(), anexo_sha256="", motivo=MotivoRevisao.CADASTRO_INICIAL,
                criado_em=datetime(2026, 1, 1, tzinfo=UTC), criado_por=uuid4(),
            )

    def test_revisao_validade_antes_emissao_rejeitada(self) -> None:
        with pytest.raises(VigenciaInvalidaError):
            RevisaoDocumento(
                id=uuid4(), tenant_id=uuid4(), documento_id=uuid4(), numero_revisao=1,
                data_emissao=date(2027, 1, 1), data_validade=date(2026, 1, 1),
                anexo_id=uuid4(), anexo_sha256="a" * 64,
                motivo=MotivoRevisao.CADASTRO_INICIAL,
                criado_em=datetime(2026, 1, 1, tzinfo=UTC), criado_por=uuid4(),
            )

    def test_bloqueio_ativo_quando_sem_data_fim(self) -> None:
        b = BloqueioOperacional(
            id=uuid4(), tenant_id=uuid4(), documento_id=uuid4(),
            tipo_documento=TipoDocumentoRegulatorio.ART,
            operacao_bloqueada="assinatura_certificado",
            data_inicio_bloqueio=datetime(2026, 6, 1, tzinfo=UTC),
        )
        assert b.ativo
        b2 = BloqueioOperacional(
            id=uuid4(), tenant_id=uuid4(), documento_id=uuid4(),
            tipo_documento=TipoDocumentoRegulatorio.ART,
            operacao_bloqueada="assinatura_certificado",
            data_inicio_bloqueio=datetime(2026, 6, 1, tzinfo=UTC),
            data_fim_bloqueio=datetime(2026, 6, 5, tzinfo=UTC),
        )
        assert not b2.ativo
