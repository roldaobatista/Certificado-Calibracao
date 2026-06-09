"""Leitor server-side do vínculo metrológico (Fatia 2 — INV-FIS-002 / D-FIS-5).

Lê o `Certificado.tipo_acreditacao` SNAPSHOTADO pelo M8 a partir do `certificado_id`
— NUNCA do payload da request (defesa anti-fraude L6). O fiscal NÃO reconsulta a
vigência da acreditação do Tenant: confia no que o M8 congelou na emissão do
certificado (INV-CER-CGCRE-VIG-001). Leitura leve (raw SQL escopado por tenant — a
RLS também isola); não monta o `CertificadoSnapshot` completo.

A view injeta esta função; testes E2E podem substituí-la (monkeypatch) para os
cenários de perfil sem precisar materializar um Certificado completo do M8.
"""

from __future__ import annotations

from uuid import UUID

from django.db import connection

from src.domain.fiscal.enums import TipoAcreditacaoVinculo


def ler_tipo_acreditacao(
    *, tenant_id: UUID, certificado_id: UUID
) -> TipoAcreditacaoVinculo | None:
    """Retorna o `tipo_acreditacao` (RBC/NAO_RBC) do certificado, ou `None` se o
    certificado não existe / não tem classificação. Escopado por tenant."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT tipo_acreditacao FROM certificados "
            "WHERE id = %s AND tenant_id = %s",
            [str(certificado_id), str(tenant_id)],
        )
        row = cur.fetchone()
    if not row or not row[0]:
        return None
    try:
        return TipoAcreditacaoVinculo(row[0])
    except ValueError:
        return None
