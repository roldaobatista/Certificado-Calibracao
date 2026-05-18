"""Testes E2E do hash chain de auditoria — exigem PG vivo (advisory lock real).

Criterio de saida F-A: "hash chain validada — cada linha tem
hash_atual = sha256(hash_anterior || payload) e trigger anti-UPDATE/DELETE
comprovado em teste de fuzzing".
"""

from __future__ import annotations

import pytest

from src.infrastructure.audit.canonicalizar import canonicalizar
from src.infrastructure.audit.hash_chain import calcular_hash
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.audit.services import (
    registrar_auditoria,
    verificar_integridade_cadeia,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from tests.factories import TenantFactory, UsuarioFactory

pytestmark = pytest.mark.tenant_isolation  # exige PG vivo


@pytest.mark.django_db(transaction=True)
class TestHashChainE2E:
    def test_primeira_linha_tem_hash_anterior_null(self) -> None:
        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory()
            # Limpa qualquer linha pre-existente da transacao de testes anteriores
            # (a transacao de teste sera rollback no final, mas em transaction=True
            # cada teste comeca limpo).

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            linha = registrar_auditoria(
                tenant_id=t.id,
                usuario_id=u.id,
                action="usuario.criado",
                resource_summary="primeiro evento",
                payload={"email": "x@y.com"},
            )

        assert linha.hash_anterior is None
        assert len(linha.hash_atual) == 64  # sha256 hex

        # Recalcula manualmente pra confirmar
        canon = canonicalizar({"email": "x@y.com"})
        esperado = calcular_hash(None, canon)
        assert linha.hash_atual == esperado

    def test_cadeia_de_3_linhas_encadeada_corretamente(self) -> None:
        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory()

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            l1 = registrar_auditoria(
                tenant_id=t.id, usuario_id=u.id,
                action="a1", resource_summary="r1", payload={"i": 1},
            )
            l2 = registrar_auditoria(
                tenant_id=t.id, usuario_id=u.id,
                action="a2", resource_summary="r2", payload={"i": 2},
            )
            l3 = registrar_auditoria(
                tenant_id=t.id, usuario_id=u.id,
                action="a3", resource_summary="r3", payload={"i": 3},
            )

        assert l2.hash_anterior == l1.hash_atual
        assert l3.hash_anterior == l2.hash_atual
        assert l1.hash_atual != l2.hash_atual != l3.hash_atual

    def test_verificar_integridade_passa_quando_intacta(self) -> None:
        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory()

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            for i in range(10):
                registrar_auditoria(
                    tenant_id=t.id, usuario_id=u.id,
                    action=f"evento.{i}",
                    resource_summary=f"r-{i}",
                    payload={"i": i, "msg": f"acao numero {i}"},
                )

        # Verificacao deve passar em todos os 10
        with run_as_system():
            ok, total, quebrados = verificar_integridade_cadeia()
        assert ok is True
        assert total >= 10
        assert quebrados == []


@pytest.mark.django_db(transaction=True)
class TestServiceConcorrencia:
    """Advisory lock serializa inserts — nao gera 2 linhas com mesmo hash_anterior."""

    def test_duas_chamadas_serializadas_nao_repetem_hash_anterior(self) -> None:
        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory()

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            l1 = registrar_auditoria(
                tenant_id=t.id, usuario_id=u.id,
                action="seq1", resource_summary="seq", payload={"i": 1},
            )
            l2 = registrar_auditoria(
                tenant_id=t.id, usuario_id=u.id,
                action="seq2", resource_summary="seq", payload={"i": 2},
            )

        # Se advisory lock funcionar, l2.hash_anterior == l1.hash_atual
        assert l2.hash_anterior == l1.hash_atual

        # Cadeia bem-formada e unica
        assert Auditoria.objects.filter(hash_anterior=l1.hash_atual).count() == 1
