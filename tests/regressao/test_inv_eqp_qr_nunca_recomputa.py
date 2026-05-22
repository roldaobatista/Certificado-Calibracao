"""Anti-regressao INV-EQP-QR-NUNCA-RECOMPUTA (T-EQP-093 — SEC-QR-001).

Validacao de hash QR SEMPRE consulta a tabela `equipamentos_qrcode`,
NUNCA recomputa HMAC. Defesa em profundidade contra:
- chave aposentada que poderia validar etiquetas antigas (mas a
  revogacao na tabela bloqueia).
- adulteracao de hash em path de deserializacao.

>=3 testes: happy (hash gravado resolve) + unhappy (hash sem prefixo) +
unhappy (revogado_em preenchido nao resolve).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, QRCode
from src.infrastructure.equipamentos.services_qr import (
    gerar_qr_hash_versionado,
    verificar_qr_hash_em_tabela,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _cenario():
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"qr-rg-{sfx}")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome=f"Cli {sfx}",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"QRRG-{sfx}",
            numero_serie=f"NSQRRG-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return tenant, eq


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_happy_hash_gravado_resolve_pela_tabela(db):
    tenant, eq = _cenario()
    emitido_em = datetime.now(tz=UTC)
    hash_versao = gerar_qr_hash_versionado(
        equipamento_id=eq.id,
        tenant_id=tenant.id,
        emitido_em=emitido_em,
    )
    with run_in_tenant_context(tenant.id):
        QRCode.objects.create(
            tenant=tenant,
            equipamento=eq,
            hash=hash_versao,
            emitido_em=emitido_em,
        )
        resolvido = verificar_qr_hash_em_tabela(hash_versao)
    assert resolvido is not None
    assert resolvido.equipamento_id == eq.id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_hash_sem_prefixo_versao_falha(db):
    tenant, _eq = _cenario()
    with run_in_tenant_context(tenant.id):
        # Sem `:` no hash — formato invalido.
        resolvido = verificar_qr_hash_em_tabela("abcdef0123456789")
    assert resolvido is None


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_hash_revogado_nao_resolve(db):
    tenant, eq = _cenario()
    emitido_em = datetime.now(tz=UTC)
    hash_versao = gerar_qr_hash_versionado(
        equipamento_id=eq.id,
        tenant_id=tenant.id,
        emitido_em=emitido_em,
    )
    with run_in_tenant_context(tenant.id):
        qr = QRCode.objects.create(
            tenant=tenant,
            equipamento=eq,
            hash=hash_versao,
            emitido_em=datetime.now(tz=UTC),
        )
        # Revoga (re-emissao posterior).
        QRCode.objects.filter(id=qr.id).update(
            revogado_em=datetime.now(tz=UTC)
        )
        resolvido = verificar_qr_hash_em_tabela(hash_versao)
    assert resolvido is None
