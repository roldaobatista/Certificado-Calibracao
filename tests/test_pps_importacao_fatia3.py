"""Frente `produtos-pecas-servicos` — Fatia 3 (T-PPS-040..043): importação CSV.

Parser puro (dialeto Excel BR `;` + vírgula decimal + BOM; colunas extras
DESCARTADAS; preço ambíguo rejeita — fail-closed) + staging NÃO-auto-persiste
(INV-PPS-IMPORTACAO-STAGING) + aceite por linha one-shot reusando
`cadastrar_item` + TTL 90d idempotente + RLS do staging.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient
from src.domain.produtos_pecas_servicos.extracao_csv import (
    ErroLayoutCsvError,
    parse_preco_br,
    parsear_linhas_catalogo,
)
from src.infrastructure.authz.django_provider import invalidate_user_cache

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

_DBS = ["default", "breaker_writer"]

HEADERS = (
    "codigo_interno",
    "tipo",
    "nome",
    "unidade_medida",
    "preco_padrao",
    "categoria",
)


# === parser puro (T-PPS-040) ===


def test_parse_preco_br_dialeto():
    assert parse_preco_br("1.234,56") == Decimal("1234.56")
    assert parse_preco_br("1234,5") == Decimal("1234.5")
    assert parse_preco_br("R$ 10,00") == Decimal("10.00")
    assert parse_preco_br("123.45") == Decimal("123.45")  # en-US inequívoco


def test_parse_preco_ambiguo_ou_invalido_raise():
    # P9 QUAL-M2: agrupamento de milhar malformado tambem rejeita (fail-closed
    # contra preco errado silencioso — "12.3,45"/"....,55" parseavam antes).
    for ruim in (
        "1.234", "abc", "", "1,2,3", "10.123",
        "12.3,45", "....,55", "1.2.3,45", "10.00,50", ".5,00",
    ):
        with pytest.raises(ValueError):
            parse_preco_br(ruim)


def test_parse_preco_br_milhar_bem_formado_aceita():
    assert parse_preco_br("1.234.567,89") == Decimal("1234567.89")


def test_parser_valida_e_rejeita_por_linha():
    linhas = (
        ("P-001", "peca", "Célula de carga", "un", "1.234,56", "sensores"),
        ("K-001", "kit", "Kit instalação", "un", "10,00", ""),  # kit → rejeita
        ("P-002", "banana", "Tipo errado", "un", "10,00", ""),  # tipo inválido
        ("P-003", "peca", "Preço ambíguo", "un", "1.234", ""),  # milhar sem vírgula
        ("", "peca", "Sem código", "un", "10,00", ""),  # obrigatório vazio
        ("P-001", "peca", "Código repetido", "un", "9,99", ""),  # dup intra-arquivo
        ("S-001", "servico", "Calibração balança", "h", "150,00", "serviços"),
    )
    resultado = parsear_linhas_catalogo(HEADERS, linhas)
    status = [r.status.value for r in resultado]
    assert status == [
        "validada", "rejeitada", "rejeitada", "rejeitada", "rejeitada",
        "rejeitada", "validada",
    ]
    assert resultado[0].preco_padrao == Decimal("1234.56")
    assert resultado[0].linha_numero == 2  # linha 1 = header
    assert "kit" in resultado[1].motivo_rejeicao
    assert "repetido" in resultado[5].motivo_rejeicao


def test_parser_descarta_colunas_extras():
    headers = (*HEADERS, "cpf_do_vendedor")  # coluna fora do layout
    linhas = (("P-001", "peca", "Peça X", "un", "10,00", "geral", "111.222.333-44"),)
    (linha,) = parsear_linhas_catalogo(headers, linhas)
    assert linha.status.value == "validada"
    # nada do conteúdo extra vaza pra estrutura parseada (minimização ADV-PPS-06)
    valores = (
        linha.codigo_interno, linha.nome, linha.unidade_medida,
        linha.categoria, linha.descricao, linha.codigo_fabricante,
    )
    assert all("111" not in v for v in valores)


def test_parser_header_obrigatorio_ausente_raise():
    with pytest.raises(ErroLayoutCsvError, match="preco_padrao"):
        parsear_linhas_catalogo(
            ("codigo_interno", "tipo", "nome", "unidade_medida"), ()
        )


# === E2E (PG real) ===


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario, name="default", defaults={"confirmed": True}
    )
    if not device.confirmed:
        device.confirmed = True
        device.save()
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


def _cenario():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_a=True, slug=f"pps-imp-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@pps.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@pps.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _client(c, papel="admin") -> APIClient:
    client = APIClient()
    _autenticar(client, c[papel], c["tenant"])
    return client


CSV_BR = (
    "﻿codigo_interno;tipo;nome;unidade_medida;preco_padrao;categoria;coluna_extra\n"
    "P-100;peca;Célula de carga 100kg;un;1.234,56;sensores;descartar\n"
    "S-100;servico;Calibração de balança;h;150,00;serviços;descartar\n"
    "K-100;kit;Kit não importa;un;10,00;;descartar\n"
).encode()


def _importar(client, conteudo: bytes = CSV_BR, key=None):
    arquivo = SimpleUploadedFile("catalogo legado.csv", conteudo, content_type="text/csv")
    return client.post(
        "/api/v1/catalogo/importacoes/importar/",
        {"arquivo": arquivo},
        format="multipart",
        HTTP_IDEMPOTENCY_KEY=key or str(uuid4()),
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_importar_cria_staging_e_nao_auto_persiste_item():
    """INV-PPS-IMPORTACAO-STAGING: importar NUNCA cria ItemCatalogo."""
    from src.infrastructure.multitenant.connection import run_in_tenant_context
    from src.infrastructure.produtos_pecas_servicos.models import ItemCatalogo

    c = _cenario()
    client = _client(c)
    r = _importar(client)
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["arquivo_sha256"] == hashlib.sha256(CSV_BR).hexdigest()
    assert body["validadas"] == 2  # P-100 + S-100 (kit rejeitado, BOM tolerado)
    assert body["rejeitadas"] == 1
    linha_ok = next(li for li in body["linhas"] if li["codigo_interno"] == "P-100")
    assert linha_ok["preco_padrao"] == "1234.56"  # vírgula decimal BR parseada
    with run_in_tenant_context(c["tenant"].id):
        assert ItemCatalogo.objects.count() == 0  # staging não persiste item
    g = client.get(f"/api/v1/catalogo/importacoes/{body['id']}/")
    assert g.status_code == 200
    assert len(g.json()["linhas"]) == 3


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_aceitar_linha_cria_item_v1_e_e_one_shot():
    c = _cenario()
    client = _client(c)
    body = _importar(client).json()
    linha = next(li for li in body["linhas"] if li["status"] == "validada")
    url = f"/api/v1/catalogo/importacoes/{body['id']}/aceitar-linha/"
    r = client.post(
        url, {"linha_id": linha["id"]}, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4())
    )
    assert r.status_code == 201, r.content
    assert r.json()["versao"]["versao_n"] == 1
    assert r.json()["codigo_interno"] == linha["codigo_interno"]
    # item resolve no catálogo de verdade (caminho canônico cadastrar_item)
    g = client.get(f"/api/v1/catalogo/itens/{r.json()['id']}/")
    assert g.status_code == 200
    # one-shot: aceitar de novo (nova key) → 409
    r2 = client.post(
        url, {"linha_id": linha["id"]}, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4())
    )
    assert r2.status_code == 409, r2.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_rejeitar_linha_one_shot_e_404_cross_lote():
    c = _cenario()
    client = _client(c)
    body = _importar(client).json()
    linha = next(li for li in body["linhas"] if li["status"] == "validada")
    url = f"/api/v1/catalogo/importacoes/{body['id']}/rejeitar-linha/"
    payload = {"linha_id": linha["id"], "motivo": "duplicado do catálogo atual"}
    r = client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))
    assert r.status_code == 200, r.content
    r2 = client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))
    assert r2.status_code == 409  # one-shot
    # linha de OUTRO lote → 404 (id de lote errado na URL)
    outro = client.post(
        f"/api/v1/catalogo/importacoes/{uuid4()}/rejeitar-linha/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert outro.status_code == 404


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_importa_403_e_cross_tenant_404():
    c = _cenario()
    body = _importar(_client(c)).json()
    atendente = _client(c, "atendente")
    r = _importar(atendente)
    assert r.status_code == 403
    outro_tenant = _client(_cenario())
    g = outro_tenant.get(f"/api/v1/catalogo/importacoes/{body['id']}/")
    assert g.status_code == 404  # RLS


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_csv_sem_coluna_obrigatoria_400():
    client = _client(_cenario())
    csv_ruim = b"codigo_interno;tipo;nome\nP-1;peca;X\n"
    r = _importar(client, conteudo=csv_ruim)
    assert r.status_code == 400, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_ttl_elimina_lotes_antigos_e_preserva_recentes():
    """ADV-PPS-06: staging >90d sai (linhas em cascata); reexecução idempotente."""
    from src.infrastructure.multitenant.connection import run_in_tenant_context
    from src.infrastructure.produtos_pecas_servicos.models import (
        ImportacaoCatalogo,
        ImportacaoCatalogoLinha,
    )

    c = _cenario()
    client = _client(c)
    antigo = _importar(client).json()
    recente = _importar(
        client,
        conteudo=CSV_BR.replace(b"P-100", b"P-200").replace(b"S-100", b"S-200"),
    ).json()
    with run_in_tenant_context(c["tenant"].id):
        ImportacaoCatalogo.objects.filter(id=antigo["id"]).update(
            criado_em=datetime.now(UTC) - timedelta(days=120)
        )
    call_command("limpar_importacoes_expiradas", tenant=str(c["tenant"].id))
    with run_in_tenant_context(c["tenant"].id):
        assert not ImportacaoCatalogo.objects.filter(id=antigo["id"]).exists()
        assert not ImportacaoCatalogoLinha.objects.filter(importacao_id=antigo["id"]).exists()
        assert ImportacaoCatalogo.objects.filter(id=recente["id"]).exists()
    # idempotente: segunda rodada não muda nada
    call_command("limpar_importacoes_expiradas", tenant=str(c["tenant"].id))
    with run_in_tenant_context(c["tenant"].id):
        assert ImportacaoCatalogo.objects.filter(id=recente["id"]).exists()


def test_parser_campo_excede_limite_rejeita_linha_e_trunca_motivo():
    """P9 SEG-M1(b): campo maior que a coluna do staging REJEITA a linha (antes
    estourava DataError 500 no bulk_create); motivo_rejeicao cabe no varchar(300)."""
    nome_gigante = "X" * 250  # coluna nome = 200
    linhas = (
        ("P-001", "peca", nome_gigante, "un", "10,00", ""),
        ("P-002", "peca", "Ok", "un", "Z" * 400, ""),  # preço inválido GIGANTE
    )
    r1, r2 = parsear_linhas_catalogo(HEADERS, linhas)
    assert r1.status.value == "rejeitada"
    assert "excede 200" in r1.motivo_rejeicao
    assert r2.status.value == "rejeitada"
    assert len(r2.motivo_rejeicao) <= 300  # truncado ao limite da coluna


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_ttl_caminho_todos_os_tenants_idempotente():
    """P9 QUAL-B5: o ramo SEM --tenant (iter_tenants_ativos) também elimina."""
    from src.infrastructure.multitenant.connection import run_in_tenant_context
    from src.infrastructure.produtos_pecas_servicos.models import ImportacaoCatalogo

    c = _cenario()
    antigo = _importar(_client(c)).json()
    with run_in_tenant_context(c["tenant"].id):
        ImportacaoCatalogo.objects.filter(id=antigo["id"]).update(
            criado_em=datetime.now(UTC) - timedelta(days=120)
        )
    call_command("limpar_importacoes_expiradas")  # todos os tenants
    with run_in_tenant_context(c["tenant"].id):
        assert not ImportacaoCatalogo.objects.filter(id=antigo["id"]).exists()
