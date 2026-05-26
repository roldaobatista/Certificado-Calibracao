"""Testes use case corrigir_leitura (P4 Fase 5 Batch D — T-CAL-088).

Cl. 7.5 ISO 17025 — rasura digital preservando valor_original.
INV-CAL-WORM-001 + INV-CAL-FRAUDE-COR-001.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.configurar_calibracao import (
    ConfigurarCalibracaoInput,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    executar as configurar_executar,
)
from src.application.metrologia.calibracao.corrigir_leitura import (
    CalibracaoEstadoNaoPermiteCorrigir,
    CorrigirLeituraInput,
    LeituraNaoEncontrada,
    executar,
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
from src.application.metrologia.calibracao.registrar_leitura import (
    RegistrarLeituraInput,
)
from src.application.metrologia.calibracao.registrar_leitura import (
    executar as registrar_executar,
)
from src.domain.metrologia.calibracao.entities import (
    LeituraCorrecaoSnapshot,
    OrigemLeitura,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)

from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository
from tests.test_m4_uc_registrar_leitura import FakeLeituraRepository

# =====================================================================
# FakeLeituraCorrecaoRepository
# =====================================================================


@dataclass
class FakeLeituraCorrecaoRepository:
    correcoes: dict[UUID, LeituraCorrecaoSnapshot] = field(default_factory=dict)

    def salvar_nova(self, snapshot: LeituraCorrecaoSnapshot) -> None:
        if snapshot.id in self.correcoes:
            raise ValueError(f"duplicate id {snapshot.id}")
        self.correcoes[snapshot.id] = snapshot

    def obter_por_id(self, correcao_id: UUID) -> LeituraCorrecaoSnapshot | None:
        return self.correcoes.get(correcao_id)

    def listar_por_leitura(self, leitura_id: UUID) -> list[LeituraCorrecaoSnapshot]:
        return sorted(
            (c for c in self.correcoes.values() if c.leitura_id == leitura_id),
            key=lambda c: c.corrigido_em,
        )


# =====================================================================
# Helpers
# =====================================================================


def _setup_com_leitura(
    cal_repo: FakeCalibracaoRepository,
    leit_repo: FakeLeituraRepository,
) -> tuple[UUID, UUID]:
    """Cria calibracao em EM_EXECUCAO + 1 leitura. Retorna (cal_id, leit_id)."""
    criada = criar_executar(
        CriarCalibracaoInput(
            tenant_id=uuid4(),
            origem_recepcao=OrigemRecepcao.AVULSA,
            atividade_os_id=None,
            instrumento_id=uuid4(),
            snapshot_equipamento_json={"nome": "Balanca"},
            cliente_id=uuid4(),
            cliente_referencia_hash="v01$aGVsbG8=",
            cliente_key_id="cliente-key-v1",
            tipo_acreditacao=TipoAcreditacao.NAO_RBC,
            recepcionada_em=datetime(2026, 5, 25, 14, 0, tzinfo=UTC),
            correlation_id=uuid4(),
        ),
        cal_repo,
    )
    cal_id = criada.snapshot.id
    configurar_executar(
        ConfigurarCalibracaoInput(
            calibracao_id=cal_id,
            revision_esperada=0,
            procedimento_id=uuid4(),
            procedimento_versao_snapshot={
                "codigo": "PRO-CAL-MASSA",
                "versao": "1.0.0",
                "hash_anexo": "v01$abc=",
            },
            regra_decisao=RegraDecisao.BANDA_GUARDA_30,
            regra_decisao_acordada_em=datetime(2026, 5, 25, 15, 0, tzinfo=UTC),
            regra_decisao_acordada_documento_id=uuid4(),
            escopo_id=None,
            analise_critica_pedido_id=None,
            analise_critica_pedido_inline_hash="v01$" + "a" * 16,
            capacidade_tecnica_confirmada_por_user_id=uuid4(),
        ),
        cal_repo,
    )
    iniciar_executar(
        IniciarLeiturasInput(
            calibracao_id=cal_id, revision_esperada=1, executor_id=uuid4()
        ),
        cal_repo,
    )
    out = registrar_executar(
        RegistrarLeituraInput(
            calibracao_id=cal_id,
            ponto_calibracao=Decimal("10.000"),
            numero_repeticao=1,
            valor_lido=Decimal("10.001"),
            unidade="kg",
            origem=OrigemLeitura.MANUAL,
            timestamp=datetime(2026, 5, 25, 16, 0, tzinfo=UTC),
            executor_id_hash="v01$" + "e" * 16,
            correlation_id=uuid4(),
        ),
        cal_repo,
        leit_repo,
    )
    return cal_id, out.snapshot.id


def _input_correcao(leitura_id: UUID, **overrides: object) -> CorrigirLeituraInput:
    defaults: dict[str, object] = {
        "leitura_id": leitura_id,
        "valor_corrigido": Decimal("10.005"),
        "razao_correcao_canonicalizada": (
            "Erro de digitacao confirmado por re-leitura do instrumento. "
            "Operador confirmou leitura correta como 10.005 kg."
        ),
        "razao_correcao_hash": "v01$" + "r" * 16,
        "corretor_id_hash": "v01$" + "c" * 16,
        "corrigido_em": datetime(2026, 5, 25, 17, 0, tzinfo=UTC),
        "correlation_id": uuid4(),
    }
    defaults.update(overrides)
    return CorrigirLeituraInput(**defaults)  # type: ignore[arg-type]


# =====================================================================
# Happy path
# =====================================================================


class TestHappyPath:
    def test_corrige_em_em_execucao(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        _, leit_id = _setup_com_leitura(cal_repo, leit_repo)
        out = executar(
            _input_correcao(leit_id), cal_repo, leit_repo, corr_repo
        )
        assert out.snapshot.leitura_id == leit_id
        # Valor original preservado (snapshot da Leitura antes da rasura)
        assert out.snapshot.valor_original == Decimal("10.001")
        assert out.snapshot.valor_corrigido == Decimal("10.005")

    def test_leitura_nao_eh_mutada(self) -> None:
        """INV-CAL-WORM-001 — leitura original mantida intacta."""
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        _, leit_id = _setup_com_leitura(cal_repo, leit_repo)
        leitura_original = leit_repo.obter_por_id(leit_id)
        assert leitura_original is not None
        executar(_input_correcao(leit_id), cal_repo, leit_repo, corr_repo)
        leitura_pos = leit_repo.obter_por_id(leit_id)
        # NAO muta
        assert leitura_pos == leitura_original

    def test_multiplas_correcoes_acumuladas(self) -> None:
        """Cl. 7.5 permite multiplas rasuras — historia preservada."""
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        _, leit_id = _setup_com_leitura(cal_repo, leit_repo)
        # 3 correcoes (todas referenciam o valor_original=10.001 que foi
        # registrado na Leitura — INV-CAL-WORM-001 nao deixa Leitura mutar)
        for i in range(3):
            executar(
                _input_correcao(
                    leit_id,
                    valor_corrigido=Decimal(f"10.{i + 2:03d}"),
                    razao_correcao_canonicalizada=(
                        f"Correcao numero {i + 1} — leitura re-conferida apos calibracao. "
                        f"Operador validou valor."
                    ),
                ),
                cal_repo,
                leit_repo,
                corr_repo,
            )
        assert len(corr_repo.listar_por_leitura(leit_id)) == 3


# =====================================================================
# Validacoes input
# =====================================================================


class TestValidacoesInput:
    def test_rejeita_valor_float(self) -> None:
        with pytest.raises(TypeError, match="valor_corrigido deve ser Decimal"):
            _input_correcao(uuid4(), valor_corrigido=10.5)

    def test_rejeita_razao_curta(self) -> None:
        with pytest.raises(ValueError, match=">= 30"):
            _input_correcao(uuid4(), razao_correcao_canonicalizada="curto")

    def test_rejeita_razao_hash_vazio(self) -> None:
        with pytest.raises(ValueError, match="razao_correcao_hash"):
            _input_correcao(uuid4(), razao_correcao_hash="")

    def test_rejeita_corretor_hash_vazio(self) -> None:
        with pytest.raises(ValueError, match="corretor_id_hash"):
            _input_correcao(uuid4(), corretor_id_hash="")

    def test_rejeita_corrigido_em_sem_tz(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            _input_correcao(uuid4(), corrigido_em=datetime(2026, 5, 25, 17, 0))


# =====================================================================
# Validacoes estado + integridade
# =====================================================================


class TestEstadoEIntegridade:
    def test_leitura_nao_encontrada(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        with pytest.raises(LeituraNaoEncontrada):
            executar(_input_correcao(uuid4()), cal_repo, leit_repo, corr_repo)

    def test_valor_igual_recusa(self) -> None:
        """Rasura inocua (valor identico) proibida — INV-CAL-WORM-001."""
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        _, leit_id = _setup_com_leitura(cal_repo, leit_repo)
        # Tenta corrigir com mesmo valor (10.001)
        with pytest.raises(ValueError, match="rasura inocua"):
            executar(
                _input_correcao(leit_id, valor_corrigido=Decimal("10.001")),
                cal_repo,
                leit_repo,
                corr_repo,
            )

    def test_estado_em_revisao_1_recusa(self) -> None:
        """Apos EM_REVISAO_1 nao pode corrigir — abrir NC formal."""
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        cal_id, leit_id = _setup_com_leitura(cal_repo, leit_repo)
        # Forca calibracao pra EM_REVISAO_1 mutando direto o fake
        snap = cal_repo.snapshots[cal_id]
        from dataclasses import replace
        cal_repo.snapshots[cal_id] = replace(snap, status=EstadoCalibracao.EM_REVISAO_1)
        with pytest.raises(CalibracaoEstadoNaoPermiteCorrigir, match="AC-CAL-004-7"):
            executar(_input_correcao(leit_id), cal_repo, leit_repo, corr_repo)

    def test_estado_aprovada_recusa(self) -> None:
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        cal_id, leit_id = _setup_com_leitura(cal_repo, leit_repo)
        snap = cal_repo.snapshots[cal_id]
        from dataclasses import replace
        cal_repo.snapshots[cal_id] = replace(snap, status=EstadoCalibracao.APROVADA)
        with pytest.raises(CalibracaoEstadoNaoPermiteCorrigir):
            executar(_input_correcao(leit_id), cal_repo, leit_repo, corr_repo)

    def test_estado_configurada_permite(self) -> None:
        """CONFIGURADA tambem permite correcao (AC-CAL-004-7)."""
        cal_repo = FakeCalibracaoRepository()
        leit_repo = FakeLeituraRepository()
        corr_repo = FakeLeituraCorrecaoRepository()
        cal_id, leit_id = _setup_com_leitura(cal_repo, leit_repo)
        # Volta status pra CONFIGURADA (fake direto)
        snap = cal_repo.snapshots[cal_id]
        from dataclasses import replace
        cal_repo.snapshots[cal_id] = replace(snap, status=EstadoCalibracao.CONFIGURADA)
        out = executar(_input_correcao(leit_id), cal_repo, leit_repo, corr_repo)
        assert out.snapshot.valor_corrigido == Decimal("10.005")


def test_repository_protocol_compativel() -> None:
    """FakeLeituraCorrecaoRepository implementa o Protocol."""
    from src.domain.metrologia.calibracao.repository import LeituraCorrecaoRepository

    repo = FakeLeituraCorrecaoRepository()
    assert isinstance(repo, LeituraCorrecaoRepository)
