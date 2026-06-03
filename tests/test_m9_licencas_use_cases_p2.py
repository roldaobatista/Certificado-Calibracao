"""M9 Fatia 2 — testes PUROS dos use cases (Fakes, sem Django/PG). TST-004.

Cobre `cadastrar_documento_regulatorio`, `renovar_documento`,
`acionar_modo_emergencial` e `promover_perfil_a` (com Fake da porta
`aplicar_evento_cgcre`). Os Fakes implementam os Protocols de domínio.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.licencas_acreditacoes.acionar_modo_emergencial import (
    AcionarModoEmergencialInput,
    BloqueioAtivoAusenteError,
)
from src.application.metrologia.licencas_acreditacoes.acionar_modo_emergencial import (
    executar as acionar_executar,
)
from src.application.metrologia.licencas_acreditacoes.cadastrar_documento_regulatorio import (
    CadastrarDocumentoInput,
    DocumentoDuplicadoError,
)
from src.application.metrologia.licencas_acreditacoes.cadastrar_documento_regulatorio import (
    executar as cadastrar_executar,
)
from src.application.metrologia.licencas_acreditacoes.promover_perfil_a import (
    PromoverPerfilAInput,
)
from src.application.metrologia.licencas_acreditacoes.promover_perfil_a import (
    executar as promover_executar,
)
from src.application.metrologia.licencas_acreditacoes.renovar_documento import (
    DocumentoNaoEncontradoError,
    RenovarDocumentoInput,
)
from src.application.metrologia.licencas_acreditacoes.renovar_documento import (
    executar as renovar_executar,
)
from src.domain.metrologia.licencas_acreditacoes.entities import (
    BloqueioOperacional,
    DocumentoRegulatorio,
    RevisaoDocumento,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    MotivoRevisao,
    TipoDocumentoRegulatorio,
)
from src.domain.metrologia.licencas_acreditacoes.erros import (
    AnexoObrigatorioError,
    ModoEmergencialInvalidoError,
    PerfilNaoAutorizaCGCREError,
    VigenciaInvalidaError,
)

JUST_OK = "x" * 100


# --- Fakes --------------------------------------------------------------------
class FakeDocRepo:
    def __init__(self) -> None:
        self.docs: dict[UUID, DocumentoRegulatorio] = {}
        self.revisoes: list[RevisaoDocumento] = []

    def salvar_novo(self, documento, revisao_inicial) -> None:
        self.docs[documento.id] = documento
        self.revisoes.append(revisao_inicial)

    def obter_por_id(self, *, tenant_id, documento_id):
        d = self.docs.get(documento_id)
        return d if d and d.tenant_id == tenant_id else None

    def _chave(self, d):
        return (d.tenant_id, d.tipo.value, d.numero, d.orgao_emissor)

    def existe_chave(self, *, tenant_id, tipo, numero, orgao_emissor) -> bool:
        return any(
            self._chave(d) == (tenant_id, tipo, numero, orgao_emissor)
            for d in self.docs.values()
        )

    def obter_por_chave_natural(self, *, tenant_id, tipo, numero, orgao_emissor):
        for d in self.docs.values():
            if self._chave(d) == (tenant_id, tipo, numero, orgao_emissor):
                return d
        return None

    def atualizar_vigencia_cache(
        self, *, tenant_id, documento_id, vigencia_inicio, vigencia_fim
    ) -> None:
        # snapshot é frozen; recria com a nova vigência (mutação simulada).
        from dataclasses import replace

        self.docs[documento_id] = replace(
            self.docs[documento_id],
            vigencia_inicio=vigencia_inicio,
            vigencia_fim=vigencia_fim,
        )


class FakeRevisaoRepo:
    def __init__(self) -> None:
        self.revisoes: list[RevisaoDocumento] = []

    def append(self, revisao) -> None:
        self.revisoes.append(revisao)

    def listar_por_documento(self, *, tenant_id, documento_id):
        return [r for r in self.revisoes if r.documento_id == documento_id]

    def proximo_numero_revisao(self, *, tenant_id, documento_id) -> int:
        nums = [r.numero_revisao for r in self.revisoes if r.documento_id == documento_id]
        return (max(nums) if nums else 0) + 1


class FakeBloqueioRepo:
    def __init__(self, ativo: BloqueioOperacional | None = None) -> None:
        self.ativo = ativo
        self.resolvidos = 0

    def abrir(self, bloqueio) -> None:
        self.ativo = bloqueio

    def resolver_ativos(self, *, tenant_id, documento_id, em) -> int:
        if self.ativo is not None:
            self.ativo = None
            self.resolvidos = 1
        return self.resolvidos

    def obter_ativo(self, *, tenant_id, documento_id):
        return self.ativo


class FakeAlertaRepo:
    def __init__(self) -> None:
        self.cancelados = 0

    def agendar(self, alerta) -> None: ...

    def cancelar_pendentes(self, *, tenant_id, documento_id) -> int:
        self.cancelados = 2
        return self.cancelados


class FakeEventoRepo:
    def __init__(self) -> None:
        self.eventos = []

    def registrar(self, evento) -> None:
        self.eventos.append(evento)


class FakeAplicarEventoCgcre:
    def __init__(self) -> None:
        self.chamadas = []

    def promover(self, **kw) -> None:
        self.chamadas.append(kw)


def _cad_input(**kw):
    base = {
        "tenant_id": uuid4(),
        "tipo": TipoDocumentoRegulatorio.ALVARA,
        "numero": "123",
        "orgao_emissor": "Prefeitura",
        "vigencia_inicio": date(2026, 1, 1),
        "vigencia_fim": date(2027, 1, 1),
        "perfil": "D",
        "anexo_id": uuid4(),
        "anexo_sha256": "a" * 64,
        "criado_por": uuid4(),
        "criado_em": datetime(2026, 1, 1, tzinfo=UTC),
        "correlation_id": uuid4(),
    }
    base.update(kw)
    return CadastrarDocumentoInput(**base)


# --- cadastrar ----------------------------------------------------------------
class TestCadastrar:
    def test_alvara_ok_nao_bloqueante(self) -> None:
        repo = FakeDocRepo()
        out = cadastrar_executar(_cad_input(), repo)
        assert out.documento.bloqueante is False
        assert out.revisao.numero_revisao == 1
        assert out.revisao.motivo is MotivoRevisao.CADASTRO_INICIAL

    def test_art_bloqueante_derivado(self) -> None:
        repo = FakeDocRepo()
        out = cadastrar_executar(
            _cad_input(tipo=TipoDocumentoRegulatorio.ART, numero="ART-1"), repo
        )
        assert out.documento.bloqueante is True

    def test_anexo_vazio_rejeitado(self) -> None:
        repo = FakeDocRepo()
        with pytest.raises(AnexoObrigatorioError):
            cadastrar_executar(_cad_input(anexo_sha256=""), repo)

    def test_cgcre_perfil_d_rejeitado(self) -> None:
        repo = FakeDocRepo()
        with pytest.raises(PerfilNaoAutorizaCGCREError):
            cadastrar_executar(
                _cad_input(
                    tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
                    perfil="D",
                    escopo="massa 0..10kg",
                ),
                repo,
            )

    def test_cgcre_sem_escopo_rejeitado(self) -> None:
        repo = FakeDocRepo()
        with pytest.raises(VigenciaInvalidaError):
            cadastrar_executar(
                _cad_input(
                    tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
                    perfil="A",
                    escopo="",
                ),
                repo,
            )

    def test_cgcre_perfil_a_ok(self) -> None:
        repo = FakeDocRepo()
        out = cadastrar_executar(
            _cad_input(
                tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
                perfil="A",
                escopo="massa 0..10kg",
                numero="CRL-0001",
                numero_cgcre="CRL-0001",
            ),
            repo,
        )
        assert out.documento.bloqueante is True  # REBAIXA_RBC ≠ NENHUM
        assert out.documento.numero_cgcre == "CRL-0001"

    def test_duplicado_rejeitado(self) -> None:
        repo = FakeDocRepo()
        inp = _cad_input()
        cadastrar_executar(inp, repo)
        with pytest.raises(DocumentoDuplicadoError):
            cadastrar_executar(
                _cad_input(
                    tenant_id=inp.tenant_id, numero=inp.numero,
                    orgao_emissor=inp.orgao_emissor,
                ),
                repo,
            )


# --- renovar ------------------------------------------------------------------
class TestRenovar:
    def _seed(self):
        repo = FakeDocRepo()
        out = cadastrar_executar(
            _cad_input(tipo=TipoDocumentoRegulatorio.ART, numero="ART-9"), repo
        )
        return repo, out.documento

    def test_renovacao_cria_v2_e_resolve(self) -> None:
        repo, doc = self._seed()
        rev_repo = FakeRevisaoRepo()
        rev_repo.append(  # simula a revisão v1 já existente
            RevisaoDocumento(
                id=uuid4(), tenant_id=doc.tenant_id, documento_id=doc.id,
                numero_revisao=1, data_emissao=doc.vigencia_inicio,
                data_validade=doc.vigencia_fim, anexo_id=uuid4(),
                anexo_sha256="b" * 64, motivo=MotivoRevisao.CADASTRO_INICIAL,
                criado_em=datetime(2026, 1, 1, tzinfo=UTC), criado_por=uuid4(),
            )
        )
        bloq = FakeBloqueioRepo(
            ativo=BloqueioOperacional(
                id=uuid4(), tenant_id=doc.tenant_id, documento_id=doc.id,
                tipo_documento=TipoDocumentoRegulatorio.ART,
                operacao_bloqueada="assinatura_certificado",
                data_inicio_bloqueio=datetime(2026, 6, 1, tzinfo=UTC),
            )
        )
        alerta = FakeAlertaRepo()
        out = renovar_executar(
            RenovarDocumentoInput(
                tenant_id=doc.tenant_id, documento_id=doc.id,
                nova_vigencia_inicio=date(2027, 1, 1), nova_vigencia_fim=date(2028, 1, 1),
                anexo_id=uuid4(), anexo_sha256="c" * 64,
                motivo=MotivoRevisao.RENOVACAO,
                criado_por=uuid4(), criado_em=datetime(2026, 12, 1, tzinfo=UTC),
                correlation_id=uuid4(),
            ),
            doc_repo=repo, revisao_repo=rev_repo,
            bloqueio_repo=bloq, alerta_repo=alerta,
        )
        assert out.revisao.numero_revisao == 2
        assert out.bloqueios_resolvidos == 1
        assert out.alertas_cancelados == 2
        assert repo.docs[doc.id].vigencia_fim == date(2028, 1, 1)

    def test_documento_inexistente_rejeitado(self) -> None:
        repo = FakeDocRepo()
        with pytest.raises(DocumentoNaoEncontradoError):
            renovar_executar(
                RenovarDocumentoInput(
                    tenant_id=uuid4(), documento_id=uuid4(),
                    nova_vigencia_inicio=date(2027, 1, 1),
                    nova_vigencia_fim=date(2028, 1, 1),
                    anexo_id=uuid4(), anexo_sha256="c" * 64,
                    motivo=MotivoRevisao.RENOVACAO, criado_por=uuid4(),
                    criado_em=datetime(2026, 12, 1, tzinfo=UTC), correlation_id=uuid4(),
                ),
                doc_repo=repo, revisao_repo=FakeRevisaoRepo(),
                bloqueio_repo=FakeBloqueioRepo(), alerta_repo=FakeAlertaRepo(),
            )

    def test_motivo_cadastro_inicial_rejeitado(self) -> None:
        with pytest.raises(ValueError, match="CADASTRO_INICIAL"):
            RenovarDocumentoInput(
                tenant_id=uuid4(), documento_id=uuid4(),
                nova_vigencia_inicio=date(2027, 1, 1), nova_vigencia_fim=date(2028, 1, 1),
                anexo_id=uuid4(), anexo_sha256="c" * 64,
                motivo=MotivoRevisao.CADASTRO_INICIAL, criado_por=uuid4(),
                criado_em=datetime(2026, 12, 1, tzinfo=UTC), correlation_id=uuid4(),
            )


# --- acionar modo emergencial -------------------------------------------------
class TestModoEmergencial:
    def _bloqueio(self, tipo: TipoDocumentoRegulatorio, doc_id: UUID, tenant_id: UUID):
        return BloqueioOperacional(
            id=uuid4(), tenant_id=tenant_id, documento_id=doc_id,
            tipo_documento=tipo, operacao_bloqueada="assinatura_certificado",
            data_inicio_bloqueio=datetime(2026, 6, 1, tzinfo=UTC),
        )

    def _input(self, doc_id, tenant_id, **kw):
        base = {
            "tenant_id": tenant_id, "documento_id": doc_id,
            "operacao_executada": "emissao_nao_rbc", "justificativa": JUST_OK,
            "admin_id": uuid4(), "assinatura_a3_id": uuid4(), "janela_dias": 3,
            "criado_em": datetime(2026, 6, 2, tzinfo=UTC), "correlation_id": uuid4(),
        }
        base.update(kw)
        return AcionarModoEmergencialInput(**base)

    def test_sem_bloqueio_ativo_rejeitado(self) -> None:
        doc_id, tid = uuid4(), uuid4()
        with pytest.raises(BloqueioAtivoAusenteError):
            acionar_executar(
                self._input(doc_id, tid),
                bloqueio_repo=FakeBloqueioRepo(ativo=None),
                evento_repo=FakeEventoRepo(),
            )

    def test_justificativa_curta_rejeitada(self) -> None:
        doc_id, tid = uuid4(), uuid4()
        bloq = FakeBloqueioRepo(
            ativo=self._bloqueio(TipoDocumentoRegulatorio.ART, doc_id, tid)
        )
        with pytest.raises(ModoEmergencialInvalidoError):
            acionar_executar(
                self._input(doc_id, tid, justificativa="curta"),
                bloqueio_repo=bloq, evento_repo=FakeEventoRepo(),
            )

    def test_cgcre_libera_apenas_nao_rbc(self) -> None:
        doc_id, tid = uuid4(), uuid4()
        bloq = FakeBloqueioRepo(
            ativo=self._bloqueio(TipoDocumentoRegulatorio.ACREDITACAO_CGCRE, doc_id, tid)
        )
        evt = FakeEventoRepo()
        out = acionar_executar(
            self._input(doc_id, tid), bloqueio_repo=bloq, evento_repo=evt
        )
        assert out.evento.libera_apenas_nao_rbc is True
        assert len(evt.eventos) == 1
        assert out.evento.justificativa_hash  # hash versionado preenchido

    def test_art_nao_libera_apenas_nao_rbc(self) -> None:
        doc_id, tid = uuid4(), uuid4()
        bloq = FakeBloqueioRepo(
            ativo=self._bloqueio(TipoDocumentoRegulatorio.ART, doc_id, tid)
        )
        out = acionar_executar(
            self._input(doc_id, tid), bloqueio_repo=bloq, evento_repo=FakeEventoRepo()
        )
        assert out.evento.libera_apenas_nao_rbc is False


# --- promover perfil A --------------------------------------------------------
class TestPromover:
    def _input(self, tenant_id, **kw):
        base = {
            "tenant_id": tenant_id, "perfil_atual": "B", "perfil_novo": "A",
            "numero": "CRL-0420", "orgao_emissor": "CGCRE",
            "vigencia_inicio": date(2026, 1, 1), "vigencia_fim": date(2030, 1, 1),
            "escopo": "massa 0..10kg", "numero_cgcre": "CRL-0420",
            "assinatura_a3_id": uuid4(), "motivo": "m" * 100,
            "criado_por": uuid4(), "criado_em": datetime(2026, 1, 1, tzinfo=UTC),
            "correlation_id": uuid4(), "auditor_cgcre": "Fulano CGCRE",
            "anexo_id": uuid4(), "anexo_sha256": "d" * 64,
        }
        base.update(kw)
        return PromoverPerfilAInput(**base)

    def test_promove_cadastra_licenca_e_chama_funcao(self) -> None:
        tid = uuid4()
        repo, porta = FakeDocRepo(), FakeAplicarEventoCgcre()
        out = promover_executar(
            self._input(tid), doc_repo=repo, aplicar_evento_cgcre=porta
        )
        assert out.promovido is True
        assert out.documento.tipo is TipoDocumentoRegulatorio.ACREDITACAO_CGCRE
        assert len(porta.chamadas) == 1
        assert porta.chamadas[0]["perfil_novo"] == "A"
        assert porta.chamadas[0]["documento_cgcre_id"] == out.documento.id
        assert porta.chamadas[0]["vigencia_fim"] == date(2030, 1, 1)

    def test_idempotente_nao_repromove(self) -> None:
        tid = uuid4()
        repo, porta = FakeDocRepo(), FakeAplicarEventoCgcre()
        promover_executar(self._input(tid), doc_repo=repo, aplicar_evento_cgcre=porta)
        # 2ª chamada com a mesma chave natural → no-op.
        out2 = promover_executar(
            self._input(tid), doc_repo=repo, aplicar_evento_cgcre=porta
        )
        assert out2.promovido is False
        assert len(porta.chamadas) == 1  # não re-promoveu

    def test_motivo_curto_rejeitado(self) -> None:
        with pytest.raises(ValueError, match="≥100 chars"):
            self._input(uuid4(), motivo="curto")
