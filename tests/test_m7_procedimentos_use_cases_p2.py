"""M7 Fatia 2 (T-PROC-030..033) — use cases puros (Fake repo, sem PG).

Cadastrar (RASCUNHO) / revisar (nova versão) / publicar (superseção + controle
documental INV-PROC-009) / revogar (one-shot). Molde M6.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.application.metrologia.procedimentos_calibracao import (
    cadastrar_procedimento,
    publicar_procedimento,
    revisar_procedimento,
    revogar_procedimento,
)
from src.application.metrologia.procedimentos_calibracao.anexo_storage import (
    sha256_server_side,
)
from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
)
from src.domain.metrologia.procedimentos_calibracao.enums import (
    EstadoProcedimento,
    TipoMetodo,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

T0 = datetime(2026, 6, 1, tzinfo=UTC)


class _FakeRepo:
    """ProcedimentoRepository em memória (use case puro)."""

    def __init__(self):
        self.store: dict = {}

    def obter_por_id(self, procedimento_id):
        return self.store.get(procedimento_id)

    def existe_chave(self, *, tenant_id, codigo, versao):
        return any(
            s.tenant_id == tenant_id and s.codigo == codigo and s.versao == versao
            for s in self.store.values()
        )

    def proxima_versao(self, *, tenant_id, codigo):
        vs = [s.versao for s in self.store.values() if s.tenant_id == tenant_id and s.codigo == codigo]
        return (max(vs) if vs else 0) + 1

    def salvar_novo(self, snapshot):
        self.store[snapshot.id] = snapshot

    def atualizar_com_lock(self, snapshot, revision_anterior):
        atual = self.store.get(snapshot.id)
        if atual is None or atual.revision != revision_anterior:
            return False
        from dataclasses import replace
        self.store[snapshot.id] = replace(snapshot, revision=revision_anterior + 1)
        return True

    def vigente_anterior(self, *, tenant_id, codigo, grandeza, faixa):
        for s in self.store.values():
            if (
                s.tenant_id == tenant_id
                and s.codigo == codigo
                and s.grandeza == grandeza
                and s.faixa == faixa
                and s.estado is EstadoProcedimento.PUBLICADO
                and s.vigencia_fim is None
                and s.revogado_em is None
            ):
                return s
        return None

    def encerrar_vigencia(self, *, procedimento_id, vigencia_fim, revision_anterior):
        atual = self.store.get(procedimento_id)
        if atual is None or atual.revision != revision_anterior or atual.vigencia_fim is not None:
            return False
        from dataclasses import replace
        self.store[procedimento_id] = replace(
            atual, vigencia_fim=vigencia_fim, revision=revision_anterior + 1
        )
        return True

    def revogar(self, *, procedimento_id, revogado_em, motivo):
        atual = self.store.get(procedimento_id)
        if atual is None or atual.revogado_em is not None:
            return False
        from dataclasses import replace
        self.store[procedimento_id] = replace(
            atual, estado=EstadoProcedimento.REVOGADO, revogado_em=revogado_em, motivo_revogacao=motivo
        )
        return True

    def vigente_em(self, *, tenant_id, grandeza, faixa, em):
        return None


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


def _cadastra(repo, **kw) -> ProcedimentoSnapshot:
    return cadastrar_procedimento.executar(_cadastrar_input(**kw), repo).snapshot


# --------------------------------------------------------------------------
class TestCadastrar:
    def test_cadastra_rascunho_v1(self):
        repo = _FakeRepo()
        out = cadastrar_procedimento.executar(_cadastrar_input(), repo)
        assert out.snapshot.estado is EstadoProcedimento.RASCUNHO
        assert out.snapshot.versao == 1
        assert out.aviso_validacao_metodo is False  # normalizado

    def test_chave_duplicada_bloqueia(self):
        repo = _FakeRepo()
        tid = uuid4()
        _cadastra(repo, tenant_id=tid, codigo="PC-X")
        with pytest.raises(cadastrar_procedimento.CodigoVersaoDuplicadoError):
            _cadastra(repo, tenant_id=tid, codigo="PC-X")

    def test_metodo_nao_normalizado_perfil_a_avisa(self):
        repo = _FakeRepo()
        out = cadastrar_procedimento.executar(
            _cadastrar_input(tipo_metodo=TipoMetodo.NAO_NORMALIZADO, perfil="A"), repo
        )
        assert out.aviso_validacao_metodo is True  # fail-open lazy (não bloqueia)
        assert out.snapshot.estado is EstadoProcedimento.RASCUNHO


class TestPublicar:
    def test_publica_rascunho_exige_controle_documental(self):
        # INV-PROC-009 — sem aprovado_por/numero_revisao não publica
        with pytest.raises(Exception, match="INV-PROC-009"):
            publicar_procedimento.PublicarProcedimentoInput(
                tenant_id=uuid4(), procedimento_id=uuid4(),
                numero_revisao="", aprovado_em=T0, aprovado_por_id=uuid4(), perfil="A",
            )

    def test_publica_e_supersede_anterior(self):
        repo = _FakeRepo()
        tid = uuid4()
        # v1 publicada vigente
        v1 = _cadastra(repo, tenant_id=tid, codigo="PC-S")
        publicar_procedimento.executar(
            publicar_procedimento.PublicarProcedimentoInput(
                tenant_id=tid, procedimento_id=v1.id, numero_revisao="Rev. 01",
                aprovado_em=T0, aprovado_por_id=uuid4(), perfil="A",
            ),
            repo,
        )
        assert repo.store[v1.id].estado is EstadoProcedimento.PUBLICADO
        # revisa -> v2 rascunho
        v2 = revisar_procedimento.executar(
            revisar_procedimento.RevisarProcedimentoInput(
                tenant_id=tid, procedimento_id_atual=v1.id, titulo="Massa rev",
                metodo_norma="OIML R76", tipo_metodo=TipoMetodo.NORMALIZADO,
                vigencia_inicio=datetime(2026, 7, 1, tzinfo=UTC), correlation_id=uuid4(),
            ),
            repo,
        ).nova_versao
        assert v2.versao == 2 and v2.estado is EstadoProcedimento.RASCUNHO
        # publica v2 -> supersede v1 (encerra vigencia_fim da v1)
        out = publicar_procedimento.executar(
            publicar_procedimento.PublicarProcedimentoInput(
                tenant_id=tid, procedimento_id=v2.id, numero_revisao="Rev. 02",
                aprovado_em=datetime(2026, 7, 1, tzinfo=UTC), aprovado_por_id=uuid4(), perfil="A",
            ),
            repo,
        )
        assert out.anterior_encerrada_id == v1.id
        assert repo.store[v1.id].vigencia_fim is not None  # v1 encerrada (WORM, não apagada)
        assert repo.store[v2.id].estado is EstadoProcedimento.PUBLICADO

    def test_publica_primeira_versao_sem_anterior(self):
        repo = _FakeRepo()
        tid = uuid4()
        v1 = _cadastra(repo, tenant_id=tid, codigo="PC-1A")
        out = publicar_procedimento.executar(
            publicar_procedimento.PublicarProcedimentoInput(
                tenant_id=tid, procedimento_id=v1.id, numero_revisao="Rev. 01",
                aprovado_em=T0, aprovado_por_id=uuid4(), perfil="A",
            ),
            repo,
        )
        assert out.anterior_encerrada_id is None


class TestRevogar:
    def test_revoga_one_shot(self):
        repo = _FakeRepo()
        tid = uuid4()
        v1 = _cadastra(repo, tenant_id=tid, codigo="PC-R")
        revogar_procedimento.executar(
            revogar_procedimento.RevogarProcedimentoInput(
                tenant_id=tid, procedimento_id=v1.id,
                motivo="revogado por revisao normativa 2026", revogado_em=T0,
            ),
            repo,
        )
        assert repo.store[v1.id].estado is EstadoProcedimento.REVOGADO
        with pytest.raises(revogar_procedimento.JaRevogadoError):
            revogar_procedimento.executar(
                revogar_procedimento.RevogarProcedimentoInput(
                    tenant_id=tid, procedimento_id=v1.id,
                    motivo="tentativa de revogar de novo aqui", revogado_em=T0,
                ),
                repo,
            )

    def test_motivo_curto_bloqueia(self):
        with pytest.raises(ValueError, match=">= 10"):
            revogar_procedimento.RevogarProcedimentoInput(
                tenant_id=uuid4(), procedimento_id=uuid4(), motivo="curto", revogado_em=T0
            )


class TestAnexoSha256:
    def test_sha256_server_side_deterministico(self):
        h1 = sha256_server_side(b"conteudo do PDF")
        h2 = sha256_server_side(b"conteudo do PDF")
        h3 = sha256_server_side(b"outro conteudo")
        assert h1 == h2 and h1 != h3
        assert len(h1) == 64  # sha256 hex
