"""T-CLI-117 + T-CLI-118 (US-CLI-006) — testes dos validadores LGPD.

Cobertura:

T-CLI-117 (AC-CLI-006-4 — LGPD art. 11 + NG-CLI-11):
1. test_pii_sensivel_diabetes_rejeitada
2. test_pii_sensivel_palavras_isoladas_rejeitadas (10 termos da denylist)
3. test_pii_sensivel_substring_interna_NAO_rejeitada — golden BLOQ-A3/TL-2:
   "transformador" / "geração" / "votação" NÃO casam (word-boundary)
4. test_pii_sensivel_case_insensitive — "DIABETES", "Cancer" rejeitados
5. test_pii_sensivel_vazio_passa
6. test_pii_sensivel_serializer_rejeita_observacao_400

T-CLI-118 (AC-CLI-006-5 — LGPD art. 14 + NG-CLI-12):
7. test_idade_menor_18_rejeitada_no_serializer (CREATE)
8. test_idade_menor_18_rejeitada_em_UPDATE — golden BLOQ-A6/TL-1
9. test_idade_18_exatamente_aceita
10. test_idade_null_aceita_PJ
11. test_check_constraint_no_banco_rejeita_idade_menor_18 — defesa profundidade
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.db import IntegrityError, connection
from rest_framework.exceptions import ValidationError
from src.infrastructure.clientes.serializers import ClienteSerializer
from src.infrastructure.clientes.validators_pii_sensivel import (
    conter_pii_sensivel,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

# =============================================================
# T-CLI-117 — anti-PII sensível
# =============================================================


def test_pii_sensivel_diabetes_rejeitada():
    assert conter_pii_sensivel("paciente com diabetes") is True


@pytest.mark.parametrize(
    "termo",
    [
        "cliente tem cancer",
        "histórico de hipertensão",
        "trabalha com biometria",
        "religião evangelica",
        "lgbtq friendly",
        "questão racial",
        "filiado ao sindicato",
        "esquerda política",
        "grávida há 3 meses",
        "tratamento psiquiatrico",
    ],
)
def test_pii_sensivel_palavras_isoladas_rejeitadas(termo):
    assert conter_pii_sensivel(termo) is True


@pytest.mark.parametrize(
    "termo_legitimo",
    [
        "Transformadora Brasil Ltda",  # não casa "trans" (substring)
        "Geração de Energia Eólica",  # não casa "gen"
        "votação interna do conselho",  # não casa "vot"
        "patenteado em 2020",  # não casa "pt"
        "placa de identificação",  # não casa "pl"
        "fascinante experiência",  # não casa "fasc"
        "comuniquei o cliente",  # não casa "comuni"
    ],
)
def test_pii_sensivel_substring_interna_NAO_rejeitada(termo_legitimo):
    """Golden BLOQ-A3/TL-2: ERP metrológico precisa cadastrar
    "Transformadora", "Geração", etc — sem falsos positivos fatais."""
    assert conter_pii_sensivel(termo_legitimo) is False


@pytest.mark.parametrize("termo", ["DIABETES", "Cancer", "EvangElIcA"])
def test_pii_sensivel_case_insensitive(termo):
    assert conter_pii_sensivel(termo) is True


def test_pii_sensivel_vazio_passa():
    assert conter_pii_sensivel("") is False
    assert conter_pii_sensivel("   ") is False


@pytest.mark.django_db(transaction=True)
def test_pii_sensivel_serializer_rejeita_observacao_400():
    """Serializer rejeita observação com PII sensível."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        serializer = ClienteSerializer(
            data={
                "tipo_pessoa": "PF",
                "documento": "11144477735",
                "nome": "Foo",
                "aceite_lgpd_em": "2026-05-20T10:00:00Z",
                "observacao": "paciente com cancer agressivo",
            }
        )
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "observacao" in str(exc_info.value)


# =============================================================
# T-CLI-118 — idade >= 18 anos
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_idade_menor_18_rejeitada_no_serializer():
    """CREATE com data_nascimento < 18 anos → ValidationError."""
    tenant = TenantFactory()
    com_17_anos = date.today() - timedelta(days=365 * 17)
    with run_in_tenant_context(tenant.id):
        serializer = ClienteSerializer(
            data={
                "tipo_pessoa": "PF",
                "documento": "11144477735",
                "nome": "Foo",
                "aceite_lgpd_em": "2026-05-20T10:00:00Z",
                "data_nascimento": com_17_anos.isoformat(),
            }
        )
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "data_nascimento" in str(exc_info.value)


@pytest.mark.django_db(transaction=True)
def test_idade_menor_18_rejeitada_em_UPDATE():
    """Golden BLOQ-A6/TL-1: UPDATE rebaixando idade < 18 também rejeita."""
    from src.infrastructure.clientes.models import Cliente

    tenant = TenantFactory()
    com_30_anos = date.today() - timedelta(days=365 * 30)
    com_17_anos = date.today() - timedelta(days=365 * 17)
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa="pf",
            documento="11144477735",
            nome="Foo",
            aceite_lgpd_em="2026-05-20T10:00:00Z",
            aceite_lgpd_versao="v1",
            data_nascimento=com_30_anos,
            aceite_lgpd_base_legal="EXECUCAO_CONTRATO",
        )
        serializer = ClienteSerializer(
            cliente, data={"data_nascimento": com_17_anos.isoformat()}, partial=True
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db(transaction=True)
def test_idade_18_exatamente_aceita():
    tenant = TenantFactory()
    com_18_anos = date.today().replace(year=date.today().year - 18)
    with run_in_tenant_context(tenant.id):
        serializer = ClienteSerializer(
            data={
                "tipo_pessoa": "PF",
                "documento": "11144477735",
                "nome": "Foo",
                "aceite_lgpd_em": "2026-05-20T10:00:00Z",
                "data_nascimento": com_18_anos.isoformat(),
            }
        )
        assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db(transaction=True)
def test_idade_null_aceita_PJ():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        serializer = ClienteSerializer(
            data={
                "tipo_pessoa": "PJ",
                "documento": "11222333000181",
                "nome": "Empresa X",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            }
        )
        assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db(transaction=True)
def test_check_constraint_no_banco_rejeita_idade_menor_18():
    """Defesa em profundidade: CHECK constraint no PG bloqueia mesmo
    bypassing o serializer (ex: bulk_update, raw SQL)."""
    tenant = TenantFactory()
    com_17_anos = date.today() - timedelta(days=365 * 17)
    with run_in_tenant_context(tenant.id):
        with pytest.raises(IntegrityError, match="ck_cliente_idade_minima_18"):
            with connection.cursor() as cur:
                cur.execute(
                    "INSERT INTO clientes "
                    "(id, tenant_id, tipo_pessoa, documento, nome, "
                    "aceite_lgpd_em, aceite_lgpd_versao, aceite_lgpd_origem, "
                    "aceite_lgpd_dispensa_motivo, aceite_lgpd_base_legal, "
                    "aceite_lgpd_pendente, aceite_lgpd_evidencia_externa, "
                    "aceite_lgpd_ip_hash, "
                    "nome_fantasia, email, telefone, cpf_responsavel_legal, "
                    "observacao, data_nascimento, "
                    "cliente_canonico_id, deletado_motivo_categoria, "
                    "criado_em, atualizado_em) "
                    "VALUES (gen_random_uuid(), %s, 'pf', '11144477735', 'Foo', "
                    "'2026-05-20T10:00:00Z', 'v1', 'CADASTRO_DIRETO', "
                    "'', 'EXECUCAO_CONTRATO', false, '', '', "
                    "'', '', '', '', '', %s, "
                    "gen_random_uuid(), '', now(), now())",
                    [str(tenant.id), com_17_anos.isoformat()],
                )
