"""TST-004 — classes nomeando cada INV-LIC (M9 Fatia 4 / T-LIC-061).

Convenção do projeto (análoga `test_inv_cer_classes_nomeadas.py` do M8 e
`test_inv_proc_classes_nomeadas.py` do M7): todo INV crítico tem >=1 teste cujo
NOME cita o ID. Cada classe `TestINV_LIC_*` exercita a barreira REAL — puro/Fake
onde a defesa é domínio/use case; PG-real onde é trigger/função/cache.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from django.db import DatabaseError
from src.application.metrologia.licencas_acreditacoes.verificar_signatario import (
    DocumentoSignatarioSnapshot,
    signatario_apto,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    TipoBloqueio,
    TipoDocumentoRegulatorio,
)
from src.domain.metrologia.licencas_acreditacoes.erros import (
    AnexoObrigatorioError,
    PerfilNaoAutorizaCGCREError,
)
from src.domain.metrologia.licencas_acreditacoes.transicoes import (
    fronteira_bloqueio,
    validar_anexo,
    validar_tipo_x_perfil,
)

_MOTIVO = "renovacao anual da acreditacao CGCRE conforme cronograma de supervisao " + "x" * 40


class TestINV_LIC_PERFIL_001:
    """Cadastro de ACREDITACAO_CGCRE exige perfil A/B/C server-side (D → 403)."""

    def test_perfil_d_rejeitado(self) -> None:
        with pytest.raises(PerfilNaoAutorizaCGCREError):
            validar_tipo_x_perfil(
                tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
                perfil="D", escopo="massa 0..10kg",
            )

    def test_perfil_a_aceito(self) -> None:
        validar_tipo_x_perfil(
            tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
            perfil="A", escopo="massa 0..10kg",
        )


class TestINV_LIC_ANEXO_001:
    """Documento regulatório exige anexo sha256 server-side (→ 422)."""

    def test_anexo_vazio_rejeitado(self) -> None:
        with pytest.raises(AnexoObrigatorioError):
            validar_anexo(anexo_sha256="")

    def test_anexo_presente_ok(self) -> None:
        validar_anexo(anexo_sha256="a" * 64)


class TestINV_LIC_VIG_SYNC_001:
    """Cache `Tenant.acreditacao_vigencia_fim` mantido SÓ via aplicar_evento_cgcre."""

    @pytest.mark.django_db
    def test_renovar_vigencia_seta_cache(self) -> None:
        from src.infrastructure.metrologia.licencas_acreditacoes.eventos_cgcre import (
            DjangoAplicarEventoCgcre,
        )
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        from tests.factories import TenantFactory

        tenant = TenantFactory(perfil_a=True)
        nova = date(2032, 12, 31)
        with run_in_tenant_context(tenant.id):
            DjangoAplicarEventoCgcre().renovar_vigencia(
                tenant_id=tenant.id, vigencia_fim=nova, motivo=_MOTIVO
            )
        tenant.refresh_from_db()
        assert tenant.acreditacao_vigencia_fim == nova
        assert tenant.perfil_regulatorio == "A"  # renovação não muda perfil


class TestINV_LIC_WORM_001:
    """RevisaoDocumento append-only (WORM Padrão B) — UPDATE bloqueado por trigger."""

    @pytest.mark.django_db
    def test_revisao_update_bloqueado(self) -> None:
        from src.infrastructure.metrologia.licencas_acreditacoes.models import (
            DocumentoRegulatorio,
            RevisaoDocumento,
        )
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        from tests.factories import TenantFactory

        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id):
            doc = DocumentoRegulatorio.objects.create(
                tenant=tenant, tipo="ALVARA", numero="WORM-1",
                orgao_emissor="Prefeitura", vigencia_inicio=date(2026, 1, 1),
                vigencia_fim=date(2027, 1, 1), bloqueante=False, criado_por=uuid4(),
            )
            rev = RevisaoDocumento.objects.create(
                tenant=tenant, documento=doc, numero_revisao=1,
                data_emissao=date(2026, 1, 1), data_validade=date(2027, 1, 1),
                anexo_id=uuid4(), anexo_sha256="a" * 64, motivo="CADASTRO_INICIAL",
                criado_por=uuid4(),
            )
        with run_in_tenant_context(tenant.id), pytest.raises(
            DatabaseError, match="append-only"
        ):
            RevisaoDocumento.objects.filter(id=rev.id).update(
                data_validade=date(2099, 1, 1)
            )


class TestINV_LIC_BLOQUEIO_001:
    """Duas fronteiras (D-LIC-5): CGCRE REBAIXA; ART/RRT/cert HARD-409."""

    def test_cgcre_rebaixa_nao_hard(self) -> None:
        assert (
            fronteira_bloqueio(TipoDocumentoRegulatorio.ACREDITACAO_CGCRE)
            is TipoBloqueio.REBAIXA_RBC
        )

    def test_art_hard_409(self) -> None:
        assert fronteira_bloqueio(TipoDocumentoRegulatorio.ART) is TipoBloqueio.HARD_409
        assert fronteira_bloqueio(TipoDocumentoRegulatorio.RRT) is TipoBloqueio.HARD_409

    def test_signatario_inapto_com_art_vencida(self) -> None:
        snaps = [
            DocumentoSignatarioSnapshot(
                documento_id=uuid4(), tipo=TipoDocumentoRegulatorio.ART,
                numero="ART-1", vigencia_fim=date(2020, 1, 1),
            )
        ]
        assert signatario_apto(snaps, data=date(2026, 1, 1)) is False

    def test_alvara_nao_bloqueia_hard(self) -> None:
        assert fronteira_bloqueio(TipoDocumentoRegulatorio.ALVARA) is TipoBloqueio.NENHUM
