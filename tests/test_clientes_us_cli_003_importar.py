"""US-CLI-003 — testes da importacao 1-clique CSV.

Cobertura por AC + endereca todas as 21 ressalvas (12 tech-lead + 9 advogado).

CPFs validos (algoritmo Receita): 52998224725 (vetor publico).
CNPJs validos: 11222333000181 (Petrobras), 33000167000101 (BB) — vetores publicos.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from src.infrastructure.audit.models import (
    AcessoDadosCliente,
    Auditoria,
    FinalidadeAcessoCliente,
)
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.csv_io import (
    detectar_colunas_cpf_responsavel,
    detectar_colunas_sensiveis,
    ler_csv_normalizado,
    sugerir_mapeamento,
)
from src.infrastructure.clientes.csv_safety import sanitizar_celula_csv
from src.infrastructure.clientes.models import (
    Cliente,
    ClienteImportacaoDeclaracao,
    TipoPessoa,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

CPF_VALIDO_1 = "52998224725"
CNPJ_VALIDO_1 = "11222333000181"
CNPJ_VALIDO_2 = "33000167000101"


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


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"imp-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@imp.local")
    tecnico = UsuarioFactory(email=f"tec-{suffix}@imp.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=tecnico, tenant=tenant, perfil="tecnico")
    invalidate_user_cache(admin.id, tenant.id)
    invalidate_user_cache(tecnico.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "tecnico": tecnico}


def _upload(nome: str, conteudo: bytes, content_type: str = "text/csv") -> SimpleUploadedFile:
    return SimpleUploadedFile(nome, conteudo, content_type=content_type)


def _csv_pj_basico() -> bytes:
    return (
        "CNPJ;Razao Social;E-mail;Telefone\r\n"
        f"{CNPJ_VALIDO_1};Petrobras LTDA;contato@petrobras.com.br;11999999999\r\n"
        f"{CNPJ_VALIDO_2};BB SA;contato@bb.com.br;1133333333\r\n"
    ).encode()


# =============================================================
# Bloco 1: csv_safety (R2 tech-lead)
# =============================================================


class TestCsvSafety:
    def test_celula_com_igual_eh_neutralizada(self):
        assert sanitizar_celula_csv("=cmd|'/c calc'!A1").startswith("'")

    def test_celula_com_arroba_eh_neutralizada(self):
        assert sanitizar_celula_csv("@SUM(1+1)").startswith("'")

    def test_celula_com_mais_eh_neutralizada(self):
        assert sanitizar_celula_csv("+1+1") == "'+1+1"

    def test_celula_com_menos_eh_neutralizada(self):
        assert sanitizar_celula_csv("-3+10") == "'-3+10"

    def test_celula_com_whitespace_inicial_e_gatilho_neutraliza(self):
        # Regressao SANEA-03 (auditoria 10 lentes — Lente 10 D6): o apostrofo
        # TEM que ficar colado no gatilho. "'  =cmd" (apostrofo antes dos
        # espacos) ainda e interpretado como formula pelo Excel. .startswith
        # passava com o bug; aqui exige o resultado exato sem o whitespace.
        assert sanitizar_celula_csv("  =cmd") == "'=cmd"
        assert sanitizar_celula_csv("\t\t@SUM(1+1)") == "'@SUM(1+1)"
        assert sanitizar_celula_csv("  \r\n -3+10") == "'-3+10"

    def test_celula_normal_passa_inalterada(self):
        assert sanitizar_celula_csv("Joao Silva") == "Joao Silva"

    def test_string_vazia_e_none(self):
        assert sanitizar_celula_csv("") == ""
        assert sanitizar_celula_csv(None) == ""


# =============================================================
# Bloco 2: csv_io (R5 tech-lead encoding/delimitador + R9 advogado sensiveis)
# =============================================================


class TestCsvIo:
    def test_ler_csv_utf8_bom_com_ponto_virgula(self):
        bom = "﻿"
        csv_bytes = (bom + "CNPJ;Razao Social\r\n11222333000181;Acme\r\n").encode("utf-8")
        norm = ler_csv_normalizado(csv_bytes)
        assert norm.delimitador == ";"
        assert norm.encoding == "utf-8"
        assert norm.headers == ("CNPJ", "Razao Social")
        assert norm.total_linhas == 1

    def test_ler_csv_utf8_sem_bom_com_virgula(self):
        csv_bytes = b"CNPJ,Nome\nA,B\nC,D\n"
        norm = ler_csv_normalizado(csv_bytes)
        assert norm.delimitador == ","

    def test_ler_csv_latin1_rejeita_com_dica(self):
        csv_bytes_invalido = b"CNPJ;Nome\n11222333000181;Caf\xe9zinho\n"
        from src.infrastructure.clientes.csv_io import ErroCsvIo

        with pytest.raises(ErroCsvIo) as exc:
            ler_csv_normalizado(csv_bytes_invalido)
        assert exc.value.code == "encoding_invalido"
        assert "UTF-8" in str(exc.value)

    def test_ler_csv_excede_limite_linhas(self):
        from src.infrastructure.clientes.csv_io import LIMITE_LINHAS, ErroCsvIo

        linhas = ["CNPJ"] + [f"line-{i}" for i in range(LIMITE_LINHAS + 1)]
        csv_bytes = "\n".join(linhas).encode("utf-8")
        with pytest.raises(ErroCsvIo) as exc:
            ler_csv_normalizado(csv_bytes)
        assert exc.value.code == "linhas_excedem_limite"

    def test_sugerir_mapeamento_header_cpf_cnpj_pra_documento(self):
        headers = ("CPF/CNPJ", "Razao Social", "E-mail", "Telefone")
        mapa = sugerir_mapeamento(headers)
        assert mapa["documento"]["confianca"] == "alta"
        assert mapa["documento"]["coluna"] == "CPF/CNPJ"
        assert mapa["nome"]["coluna"] == "Razao Social"

    def test_sugerir_mapeamento_confianca_baixa_header_desconhecido(self):
        headers = ("XYZ", "ABC")
        mapa = sugerir_mapeamento(headers)
        assert mapa["documento"]["confianca"] == "baixa"

    def test_detectar_colunas_sensiveis(self):
        headers = ("CNPJ", "Razao Social", "Diagnostico", "Religiao")
        sensiveis = detectar_colunas_sensiveis(headers)
        assert "Diagnostico" in sensiveis
        assert "Religiao" in sensiveis
        assert "CNPJ" not in sensiveis

    def test_detectar_colunas_cpf_responsavel(self):
        headers = ("CNPJ", "CPF Responsavel", "Razao Social")
        cpfs = detectar_colunas_cpf_responsavel(headers)
        assert "CPF Responsavel" in cpfs


# =============================================================
# Bloco 3: Preview endpoint (AC-CLI-003-1)
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_preview_devolve_amostra_e_mapeamento_sugerido(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("clientes.csv", _csv_pj_basico())
    response = client.post(
        "/api/v1/clientes/importar-preview/",
        data={"arquivo": arquivo},
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["delimitador_detectado"] == ";"
    assert body["encoding_detectado"] == "utf-8"
    assert len(body["linhas_amostra"]) == 2
    assert body["mapeamento_sugerido"]["documento"]["coluna"] == "CNPJ"
    assert "arquivo_hash" in body


@pytest.mark.django_db(transaction=True)
def test_preview_detecta_coluna_dados_sensiveis(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    csv_bytes = ("CNPJ;Razao Social;Diagnostico\r\n" f"{CNPJ_VALIDO_1};X;hipertensao\r\n").encode()
    arquivo = _upload("sensivel.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-preview/",
        data={"arquivo": arquivo},
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert "Diagnostico" in body["colunas_sensiveis_detectadas"]


# =============================================================
# Bloco 4: Executar — caminho feliz e LGPD
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_executar_cria_pj_em_lote_dispensa_sem_pf(cenario):
    csv_bytes = (
        "CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};Petrobras\r\n" f"{CNPJ_VALIDO_2};BB\r\n"
    ).encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pj.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"Bling 2026-04"}'
            ),
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["totais"]["criados"] == 2
    assert body["totais"]["pj_dispensa_aceite"] == 2
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        assert Cliente.objects.filter(tenant_id=cenario["tenant"].id).count() == 2


@pytest.mark.django_db(transaction=True)
def test_executar_pj_com_email_pessoal_marca_pendente_aceite(cenario):
    csv_bytes = (
        "CNPJ;Razao Social;E-mail\r\n" f"{CNPJ_VALIDO_1};Acme;joao.silva@acme.com\r\n"
    ).encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pj.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social","email":"E-mail"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["totais"]["pj_com_pf_pendente_aceite"] == 1
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        c = Cliente.objects.get(tenant_id=cenario["tenant"].id, documento=CNPJ_VALIDO_1)
        assert c.aceite_lgpd_pendente is True
        assert c.aceite_lgpd_dispensa_motivo == "pj_com_pf_pendente_aceite"


@pytest.mark.django_db(transaction=True)
def test_executar_pf_sem_flag_rejeita_linha(cenario):
    csv_bytes = ("CPF;Nome\r\n" f"{CPF_VALIDO_1};Joao Silva\r\n").encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pf.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CPF","nome":"Nome"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "skip_invalid": "true",
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["totais"]["criados"] == 0
    assert body["totais"]["pf_rejeitadas_por_falta_aceite"] == 1
    motivos = body["rejeitados_motivos_agregados"]
    assert motivos.get("pf_sem_aceite") == 1


@pytest.mark.django_db(transaction=True)
def test_executar_pf_com_flag_contrato_preexistente_cria_com_base_art_7_v(cenario):
    csv_bytes = ("CPF;Nome\r\n" f"{CPF_VALIDO_1};Joao Silva\r\n").encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pf.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CPF","nome":"Nome"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "pf_aceite_origem": "contrato_preexistente_documentado",
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        c = Cliente.objects.get(tenant_id=cenario["tenant"].id, documento=CPF_VALIDO_1)
        assert c.aceite_lgpd_base_legal == "art_7_v"
        assert c.aceite_lgpd_evidencia_externa


@pytest.mark.django_db(transaction=True)
def test_executar_sem_declaracao_completa_retorna_400(cenario):
    csv_bytes = _csv_pj_basico()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pj.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":false,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "declaracao_incompleta"


# =============================================================
# Bloco 5: DoS / Injecao / Limites (R1+R2 tech-lead, R3 advogado)
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_upload_excede_limite_bytes_retorna_413(cenario):
    big = b"CNPJ;Nome\n" + b"x" * (3 * 1024 * 1024)
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("grande.csv", big)
    response = client.post(
        "/api/v1/clientes/importar-preview/",
        data={"arquivo": arquivo},
        format="multipart",
    )
    assert response.status_code in (400, 413), response.status_code


@pytest.mark.django_db(transaction=True)
def test_executar_neutraliza_formula_injection_em_nome(cenario):
    csv_bytes = ("CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};=cmd|'/c calc'!A1\r\n").encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("evil.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        c = Cliente.objects.get(tenant_id=cenario["tenant"].id, documento=CNPJ_VALIDO_1)
        assert c.nome.startswith("'=")


# =============================================================
# Bloco 6: skip_invalid + idempotencia (R7+R9 tech-lead)
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_executar_skip_invalid_false_com_linha_invalida_nao_persiste_nada(cenario):
    csv_bytes = (
        "CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};Boa LTDA\r\n" "12345678901234;Ruim LTDA\r\n"
    ).encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("misto.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "skip_invalid": "false",
        },
        format="multipart",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "linhas_invalidas_e_skip_invalid_false"
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        assert Cliente.objects.filter(tenant_id=cenario["tenant"].id).count() == 0


@pytest.mark.django_db(transaction=True)
def test_executar_documento_ausente_rejeita_linha(cenario):
    """Linha sem coluna documento — rejeita motivo `documento_ausente`."""
    csv_bytes = (
        "CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};Boa LTDA\r\n" ";Sem documento\r\n"
    ).encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("ausente.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "skip_invalid": "true",
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["rejeitados_motivos_agregados"].get("documento_ausente") == 1


@pytest.mark.django_db(transaction=True)
def test_executar_documento_tamanho_invalido_rejeita_linha(cenario):
    """Documento com 13 chars (nem PF nem PJ) — rejeita motivo `documento_tamanho_invalido`."""
    csv_bytes = (
        b"CNPJ;Razao Social\r\n" b"1122233344455;Tamanho errado\r\n"  # 13 chars
    )
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("tamanho.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "skip_invalid": "true",
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["rejeitados_motivos_agregados"].get("documento_tamanho_invalido") == 1


@pytest.mark.django_db(transaction=True)
def test_executar_nome_ausente_rejeita_linha(cenario):
    """Documento valido + nome vazio — rejeita motivo `nome_ausente`."""
    csv_bytes = ("CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};\r\n").encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("nome.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "skip_invalid": "true",
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["rejeitados_motivos_agregados"].get("nome_ausente") == 1


@pytest.mark.django_db(transaction=True)
def test_audit_documento_hash_eh_salgado_por_tenant(cenario):
    """FAIL critico Auditor Seguranca 2026-05-18: hash de PII em audit
    precisa ser salgado por tenant (rainbow-table-proof)."""
    import hashlib

    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        Cliente.objects.create(
            tenant=cenario["tenant"],
            tipo_pessoa=TipoPessoa.PJ,
            documento=CNPJ_VALIDO_1,
            nome="Acme LTDA",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    # Criar via API pra ter audit `cliente.criado`.
    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": CNPJ_VALIDO_2,
            "nome": "BB SA",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        aud = Auditoria.objects.filter(
            tenant_id=cenario["tenant"].id, action="cliente.criado"
        ).first()
    assert aud is not None
    doc_hash = aud.payload_jsonb["documento_hash"]
    # Hash SEM sal (vulneravel) — NAO deve bater. Contra-exemplo intencional.
    hash_sem_sal = hashlib.sha256(
        CNPJ_VALIDO_2.encode("utf-8")
    ).hexdigest()  # audit-pii-salt: skip -- contra-exemplo prova que hash inseguro nao e usado
    assert (
        doc_hash != hash_sem_sal
    ), "Hash em audit precisa ser salgado por tenant (Auditor Seguranca FAIL critico)"
    # SANEA-02: o salt PREVISIVEL antigo (sha256 de string derivavel do
    # tenant_id, que e publico) NAO pode mais reproduzir o hash. Se este
    # assert falhar, alguem so com o tenant_id reconstruiu o hash de CPF.
    hash_salt_previsivel = hashlib.sha256(  # audit-pii-salt: skip -- contra-exemplo prova que salt previsivel nao reproduz
        f"afere-pii-salt:{cenario['tenant'].id}:{CNPJ_VALIDO_2}".encode()
    ).hexdigest()
    assert doc_hash != hash_salt_previsivel, (
        "SANEA-02: hash nao pode ser reproduzivel so com tenant_id (HMAC "
        "com chave de servidor — Lente 05 D1 / 07 R-CLI-05)"
    )
    # Reproducao legitima exige a chave de servidor (settings.PII_HASH_KEY),
    # via a funcao canonica — prova determinismo sem expor a chave no teste.
    from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

    assert doc_hash == hashear_pii_com_salt_tenant(CNPJ_VALIDO_2, cenario["tenant"].id)
    # Separacao por tenant: mesmo documento, tenant diferente => hash diferente.
    import uuid as _uuid

    assert doc_hash != hashear_pii_com_salt_tenant(CNPJ_VALIDO_2, _uuid.uuid4())


@pytest.mark.django_db(transaction=True)
def test_executar_skip_invalid_true_persiste_validas_e_relata_invalidas(cenario):
    csv_bytes = (
        "CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};Boa LTDA\r\n" "12345678901234;Ruim LTDA\r\n"
    ).encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("misto.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "skip_invalid": "true",
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["totais"]["criados"] == 1
    assert body["totais"]["rejeitados"] == 1


@pytest.mark.django_db(transaction=True)
def test_executar_rerun_mesmo_arquivo_eh_idempotente_marca_sem_mudanca(cenario):
    csv_bytes = ("CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};Acme LTDA\r\n").encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo1 = _upload("a.csv", csv_bytes)
    r1 = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo1,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    assert r1.status_code == 200
    assert r1.json()["totais"]["criados"] == 1
    arquivo2 = _upload("a.csv", csv_bytes)
    r2 = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo2,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["totais"]["criados"] == 0
    assert body["totais"]["sem_mudanca"] == 1


# =============================================================
# Bloco 7: Audit sem PII + R5 advogado + R10 tech-lead
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_audit_importacao_nao_contem_pii_cru(cenario):
    csv_bytes = (
        "CNPJ;Razao Social;E-mail;Telefone\r\n"
        f"{CNPJ_VALIDO_1};Petrobras LTDA;contato@petrobras.com.br;11999999999\r\n"
    ).encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pj.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": (
                '{"documento":"CNPJ","nome":"Razao Social","email":"E-mail",'
                '"telefone":"Telefone"}'
            ),
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content

    import json

    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        aud = Auditoria.objects.filter(
            tenant_id=cenario["tenant"].id, action="cliente.importacao_executada"
        ).first()
    assert aud is not None, "Audit `cliente.importacao_executada` nao gravado"
    payload_str = json.dumps(aud.payload_jsonb, ensure_ascii=False)
    assert "Petrobras" not in payload_str
    assert CNPJ_VALIDO_1 not in payload_str
    assert "contato@petrobras.com.br" not in payload_str
    assert "11999999999" not in payload_str


@pytest.mark.django_db(transaction=True)
def test_audit_importacao_eh_evento_unico_por_lote(cenario):
    csv_bytes = ("CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};A\r\n" f"{CNPJ_VALIDO_2};B\r\n").encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("dois.csv", csv_bytes)
    client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        qtd = Auditoria.objects.filter(
            tenant_id=cenario["tenant"].id, action="cliente.importacao_executada"
        ).count()
    assert qtd == 1, f"Esperado 1 audit, obtido {qtd}"


# =============================================================
# Bloco 8: Declaracao de procedencia persiste (R6 advogado)
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_declaracao_de_procedencia_persistida(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pj.csv", _csv_pj_basico())
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"Bling export 2026-04"}'
            ),
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        d = ClienteImportacaoDeclaracao.objects.filter(tenant_id=cenario["tenant"].id).first()
    assert d is not None
    assert d.tem_base_legal is True
    assert d.compromisso_comunicar_titulares is True
    assert d.declara_sem_dados_sensiveis is True
    assert d.procedencia_declarada == "Bling export 2026-04"


# =============================================================
# Bloco 9: Relatorio + INV-013 (R7 advogado)
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_relatorio_imediato_nao_lista_pii_dos_criados(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("pj.csv", _csv_pj_basico())
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": (
                '{"documento":"CNPJ","nome":"Razao Social","email":"E-mail",'
                '"telefone":"Telefone"}'
            ),
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    body = response.json()
    import json

    body_str = json.dumps(body, ensure_ascii=False)
    assert "Petrobras" not in body_str
    assert CNPJ_VALIDO_1 not in body_str


@pytest.mark.django_db(transaction=True)
def test_consulta_historico_importacoes_dispara_inv_013(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    response = client.get("/api/v1/clientes/importacoes/")
    assert response.status_code == 200, response.content
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        qtd = AcessoDadosCliente.objects.filter(
            tenant_id=cenario["tenant"].id,
            finalidade=FinalidadeAcessoCliente.CONSULTA_RELATORIO_IMPORTACAO,
        ).count()
    assert qtd == 1


# =============================================================
# Bloco 10: Authz (T-CLI-049 + T-CLI-056)
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_importar_exige_perfil_admin_tenant(cenario):
    """Tecnico nao pode importar — TL7 least privilege."""
    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])
    arquivo = _upload("pj.csv", _csv_pj_basico())
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
        },
        format="multipart",
    )
    assert response.status_code == 403, response.content


def test_predicate_tenant_nao_suspenso_stub_passa():
    """R4 tech-lead — predicate registrado (stub) ate ADR-0015 entrar."""
    from src.infrastructure.clientes.predicates_authz import tenant_nao_suspenso

    allowed, reason = tenant_nao_suspenso(resource={}, tenant_id=None)
    assert allowed is True
    assert reason == ""


@pytest.mark.django_db(transaction=True)
def test_importar_com_tenant_suspenso_nega_403(cenario):
    """Tenant SUSPENSO -> predicate `tenant_nao_suspenso` retorna denied.

    CONCERN Seguranca 4 (Auditor Familia 5 2026-05-18) — predicate
    deixou de ser stub. Consulta `Tenant.status_lifecycle` de verdade.
    """
    from src.infrastructure.clientes.predicates_authz import tenant_nao_suspenso
    from src.infrastructure.tenant.models import StatusLifecycle

    tenant = cenario["tenant"]
    tenant.status_lifecycle = StatusLifecycle.SUSPENSO
    tenant.save(update_fields=["status_lifecycle"])

    allowed, reason = tenant_nao_suspenso(resource={}, tenant_id=tenant.id)
    assert allowed is False
    assert reason == "tenant_suspenso"


@pytest.mark.django_db(transaction=True)
def test_importar_com_tenant_cancelado_nega(cenario):
    """Tenant CANCELADO -> predicate nega com reason `tenant_cancelado`."""
    from src.infrastructure.clientes.predicates_authz import tenant_nao_suspenso
    from src.infrastructure.tenant.models import StatusLifecycle

    tenant = cenario["tenant"]
    tenant.status_lifecycle = StatusLifecycle.CANCELADO
    tenant.save(update_fields=["status_lifecycle"])

    allowed, reason = tenant_nao_suspenso(resource={}, tenant_id=tenant.id)
    assert allowed is False
    assert reason == "tenant_cancelado"


# =============================================================
# Bloco 11: ja_existe (E risco arquitetural)
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_executar_update_existing_false_rejeita_duplicata(cenario):
    """Documento ja cadastrado + update_existing=false -> rejeita."""
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        Cliente.objects.create(
            tenant=cenario["tenant"],
            tipo_pessoa=TipoPessoa.PJ,
            documento=CNPJ_VALIDO_1,
            nome="Existente",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
    csv_bytes = ("CNPJ;Razao Social\r\n" f"{CNPJ_VALIDO_1};Tentando criar de novo\r\n").encode()
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("dup.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "update_existing": "false",
            "skip_invalid": "true",
        },
        format="multipart",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["totais"]["rejeitados"] == 1
    assert body["rejeitados_motivos_agregados"].get("ja_existe_no_tenant") == 1


@pytest.mark.django_db(transaction=True)
def test_importacao_e_atomica_falha_no_meio_reverte_update(cenario, monkeypatch):
    """SANEA-01 (auditoria 10 lentes — 01 D-01 / 02 SEG-D2).

    Regressao: o advisory_xact_lock + o trabalho de upsert tem que viver na
    MESMA transacao. Antes, o `with transaction.atomic()` fechava logo apos
    o lock e TODO o upsert rodava fora de transacao (autocommit por statement
    em SERIALIZABLE). Consequencia: se o `bulk_create` (clientes novos)
    falhasse, o `.update()` ja aplicado nos clientes EXISTENTES NAO era
    revertido — persistia parcial. Este teste forca o bulk_create a estourar
    no meio e exige que o UPDATE do cliente existente tenha sido revertido.

    Com o codigo ANTERIOR ao conserto este teste FALHA (o nome viria "Novo").
    """
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        Cliente.objects.create(
            tenant=cenario["tenant"],
            tipo_pessoa=TipoPessoa.PJ,
            documento=CNPJ_VALIDO_1,
            nome="Antigo LTDA",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )

    # bulk_create estoura DEPOIS do loop que ja aplicou o .update() no
    # existente. Se a transacao nao englobar tudo, o update vaza.
    def _boom(*args, **kwargs):
        raise RuntimeError("falha simulada no bulk_create (SANEA-01)")

    monkeypatch.setattr(type(Cliente.objects), "bulk_create", _boom)

    csv_bytes = (
        "CNPJ;Razao Social\r\n"
        f"{CNPJ_VALIDO_1};Novo LTDA\r\n"  # vai pro ramo UPDATE
        f"{CNPJ_VALIDO_2};Cliente Novo\r\n"  # vai pro ramo bulk_create -> boom
    ).encode()
    # raise_request_exception=False: o DRF, por padrao, re-levanta excecao
    # nao-tratada no test client. Queremos a resposta 500 real + observar o
    # estado do banco apos o rollback.
    client = APIClient(raise_request_exception=False)
    _autenticar(client, cenario["admin"], cenario["tenant"])
    arquivo = _upload("atomic.csv", csv_bytes)
    response = client.post(
        "/api/v1/clientes/importar-executar/",
        data={
            "arquivo": arquivo,
            "mapeamento": '{"documento":"CNPJ","nome":"Razao Social"}',
            "declaracao": (
                '{"tem_base_legal":true,"compromisso_comunicar_titulares":true,'
                '"declara_sem_dados_sensiveis":true,"procedencia_declarada":"x"}'
            ),
            "update_existing": "true",
            "skip_invalid": "true",
        },
        format="multipart",
    )

    assert response.status_code == 500, response.content
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        existente = Cliente.objects.get(tenant_id=cenario["tenant"].id, documento=CNPJ_VALIDO_1)
        # Atomicidade: o UPDATE foi revertido junto com o bulk_create que falhou.
        assert existente.nome == "Antigo LTDA", (
            "SANEA-01: update do cliente existente NAO foi revertido — "
            "advisory lock/transacao nao englobam o trabalho inteiro"
        )
        # E o cliente novo nunca foi criado.
        assert not Cliente.objects.filter(
            tenant_id=cenario["tenant"].id, documento=CNPJ_VALIDO_2
        ).exists()
