"""T-CLI-103 / INV-CLI-001 — testes de identidade canônica.

Cobertura:

1. test_canonico_default_aponta_para_si — recém-criado: `cliente_canonico_id = id`.
2. test_resolver_cadeia_de_uma_mesclagem — A.canonico = B (vivo) → resolve(A) == B.
3. test_resolver_cadeia_de_duas_mesclagens_com_path_compression — A→B→C: resolve(A) == C
   E após resolução, A.cliente_canonico_id passa a apontar diretamente pra C (hops == 1
   na próxima leitura — materialização preguiçosa AC-CLI-002-5).
4. test_ciclo_dispara_identidade_circular — cadeia bug-introduzida A→B→A levanta exceção.
5. test_cap_excedido_dispara_identidade_circular — cadeia 11 nós levanta exceção.
6. test_property_resolver_sempre_termina_em_vivo_ou_excecao — 100 cadeias geradas
   (corretora-seguros-saas §D — property-based reduzido, fuzz-friendly).
"""

from __future__ import annotations

import pytest
from src.infrastructure.clientes.canonico import (
    CAP_HOPS,
    IdentidadeCanonicaCircular,
    resolver_cliente_canonico,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _criar_cliente_pj(tenant, *, documento: str, nome: str) -> Cliente:
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento=documento,
        nome=nome,
        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
    )


@pytest.mark.django_db(transaction=True)
def test_canonico_default_aponta_para_si():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c = _criar_cliente_pj(tenant, documento="11222333000181", nome="Solo LTDA")
        assert c.cliente_canonico_id == c.id


@pytest.mark.django_db(transaction=True)
def test_resolver_cadeia_de_uma_mesclagem():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        venc = _criar_cliente_pj(tenant, documento="11222333000181", nome="Vencedor")
        perd = _criar_cliente_pj(tenant, documento="33000167000101", nome="Perdedor")
        # simula mesclagem: aponta o canonico do perdedor pro vencedor + soft-delete
        Cliente.all_objects.filter(id=perd.id).update(
            cliente_canonico_id=venc.id,
            deletado_em="2026-05-19T00:00:00Z",
        )
        assert resolver_cliente_canonico(perd.id) == venc.id


@pytest.mark.django_db(transaction=True)
def test_resolver_cadeia_de_duas_mesclagens_com_path_compression():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c_final = _criar_cliente_pj(tenant, documento="11222333000181", nome="C-Final")
        b_meio = _criar_cliente_pj(tenant, documento="22333444000172", nome="B-Meio")
        a_inicio = _criar_cliente_pj(tenant, documento="33000167000101", nome="A-Inicio")

        # cadeia bug-livre: A → B (vivo, depois mesclado) → C (vivo final).
        # Trigger T-CLI-113 exige target vivo no momento do UPDATE de
        # cliente_canonico_id — separar do UPDATE de deletado_em.
        Cliente.all_objects.filter(id=a_inicio.id).update(cliente_canonico_id=b_meio.id)
        Cliente.all_objects.filter(id=a_inicio.id).update(deletado_em="2026-05-19T00:00:00Z")
        Cliente.all_objects.filter(id=b_meio.id).update(cliente_canonico_id=c_final.id)
        Cliente.all_objects.filter(id=b_meio.id).update(deletado_em="2026-05-19T00:00:00Z")

        # primeira resolução percorre 2 hops e dispara path compression
        resultado = resolver_cliente_canonico(a_inicio.id)
        assert resultado == c_final.id

        # path compression: A agora aponta DIRETO pra C
        a_pos = Cliente.all_objects.get(id=a_inicio.id)
        assert a_pos.cliente_canonico_id == c_final.id


@pytest.mark.django_db(transaction=True)
def test_ciclo_dispara_identidade_circular():
    """Resolver Python detecta ciclo mesmo que o banco tenha um (defesa em
    profundidade). Estratégia: construir A→B→A ENQUANTO ambos vivos (trigger
    PG T-CLI-113 valida target vivo a cada UPDATE — passa). Soft-delete depois
    (sem alterar cliente_canonico_id, trigger não dispara). Resolver percorre
    A→B→A e levanta IdentidadeCanonicaCircular."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        a = _criar_cliente_pj(tenant, documento="11222333000181", nome="A")
        b = _criar_cliente_pj(tenant, documento="22333444000172", nome="B")
        # A → B (B vivo): passa pela trigger
        Cliente.all_objects.filter(id=a.id).update(cliente_canonico_id=b.id)
        # B → A (A vivo): passa pela trigger — ciclo formado em runtime
        Cliente.all_objects.filter(id=b.id).update(cliente_canonico_id=a.id)
        # Soft-delete ambos sem mudar cliente_canonico_id
        Cliente.all_objects.filter(id=a.id).update(deletado_em="2026-05-19T00:00:00Z")
        Cliente.all_objects.filter(id=b.id).update(deletado_em="2026-05-19T00:00:00Z")
        with pytest.raises(IdentidadeCanonicaCircular):
            resolver_cliente_canonico(a.id)


@pytest.mark.django_db(transaction=True)
def test_cap_excedido_dispara_identidade_circular():
    """Cadeia com CAP_HOPS+1 nós sem ciclo ainda deve abortar — proteção corretora."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        # CAP_HOPS+1 nós encadeados linearmente, todos soft-deleted exceto o último
        nos: list[Cliente] = []
        for i in range(CAP_HOPS + 1):
            doc = f"{i:014d}"
            n = _criar_cliente_pj(tenant, documento=doc, nome=f"N{i}")
            nos.append(n)
        # encadeia: N0 → N1 → N2 → ... → N{CAP}. Trigger T-CLI-113 valida
        # target vivo — separar UPDATE de cliente_canonico_id do soft-delete.
        for i in range(CAP_HOPS):
            Cliente.all_objects.filter(id=nos[i].id).update(cliente_canonico_id=nos[i + 1].id)
            Cliente.all_objects.filter(id=nos[i].id).update(deletado_em="2026-05-19T00:00:00Z")
        with pytest.raises(IdentidadeCanonicaCircular):
            resolver_cliente_canonico(nos[0].id)


@pytest.mark.django_db(transaction=True)
def test_property_resolver_termina_ou_levanta():
    """Property-based reduzido: 100 cadeias com tamanho aleatório [0..CAP_HOPS+2].
    Cada cadeia OU resolve pra cliente vivo OU levanta IdentidadeCanonicaCircular.
    Nunca trava, nunca retorna id de cliente soft-deleted.
    """
    import secrets

    tenant = TenantFactory()
    sucessos = 0
    excecoes = 0
    # Spec §3 item 10: ≥ 1000 cadeias geradas validando idempotência +
    # ausência de ciclo + cap 10 (corretora §D). 100 era valor reduzido.
    with run_in_tenant_context(tenant.id):
        for caso in range(1000):
            tamanho = secrets.randbelow(CAP_HOPS + 3)  # 0..12
            nos: list[Cliente] = []
            for i in range(tamanho + 1):
                # documento único derivado de (caso, i)
                doc = f"{caso:07d}{i:07d}"
                n = _criar_cliente_pj(tenant, documento=doc, nome=f"c{caso}n{i}")
                nos.append(n)
            # encadeia: n0 → n1 → ... → n{tamanho-1} → n{tamanho} (vivo, canonico
            # de si). Trigger T-CLI-113 exige target vivo no momento do UPDATE de
            # cliente_canonico_id; soft-delete depois (passos separados).
            for i in range(tamanho):
                Cliente.all_objects.filter(id=nos[i].id).update(cliente_canonico_id=nos[i + 1].id)
                Cliente.all_objects.filter(id=nos[i].id).update(deletado_em="2026-05-19T00:00:00Z")
            try:
                resultado = resolver_cliente_canonico(nos[0].id)
            except IdentidadeCanonicaCircular:
                excecoes += 1
                assert tamanho >= CAP_HOPS  # só excede cap quando tamanho real >= CAP
            else:
                sucessos += 1
                # resultado é cliente vivo
                vivo = Cliente.all_objects.get(id=resultado)
                assert vivo.deletado_em is None
                assert vivo.cliente_canonico_id == vivo.id
    # garante diversidade — nem todas exceção, nem todas sucesso (com 100 cadeias
    # de tamanho 0..12 e CAP=10, distribuição esperada ~85% sucesso / ~15% exceção)
    assert sucessos > 0, "property-test degenerou: nenhuma cadeia resolveu"
    assert sucessos + excecoes == 1000
