"""Constants do aceite LGPD do modulo clientes (US-CLI-001 / T-CLI-101).

Versionamento por hash de texto: cada mudanca de texto vira uma versao nova.
Clientes ja cadastrados preservam a versao que aceitaram (snapshot legal — R2
do advogado).

Pra mostrar texto historico, lookup em TEXTOS_HISTORICOS pela versao gravada
no Cliente.aceite_lgpd_versao.

T-CLI-101 (2026-05-19): enum de bases legais e origens alinhado com a spec
FORWARD do Marco 1 pos-review do advogado (P-CLI-A1 AJUSTADO):
- BASES_LEGAIS_VALIDAS: 5 valores (LGPD art. 7º I/V/II/IX/X)
- ORIGENS_VALIDAS: 3 valores (CADASTRO_DIRETO / IMPORTACAO_LEGADA / MIGRACAO_SISTEMA_ANTERIOR)
- LIA (Teste de Balanceamento, LGPD art. 10) obrigatorio quando LEGITIMO_INTERESSE
"""

from __future__ import annotations

# Versao vigente do texto. INCREMENTE quando o texto mudar.
# Formato sugerido: vMAJOR.MINOR-YYYY-MM-DD.
VERSAO_VIGENTE = "v1.0-2026-05-18"


# Catalogo historico — pra exibir o texto que o cliente realmente aceitou.
# Nunca remover entradas antigas (auditoria juridica).
# Placeholder `[Razão Social do Tenant]` injetado em runtime pela UI (R1 advogado).
TEXTOS_HISTORICOS: dict[str, str] = {
    "v1.0-2026-05-18": (
        "Declaro estar ciente de que [Razão Social do Tenant] tratará meus "
        "dados pessoais (nome, CPF, contato e endereço) para a execução dos "
        "serviços contratados e para o cumprimento de obrigações legais e "
        "regulatórias aplicáveis (fiscais, metrológicas e contratuais), "
        "conforme art. 7º, incisos II e V, da Lei 13.709/2018 (LGPD). "
        "Posso exercer meus direitos de titular (art. 18) pelo canal indicado "
        "em [link: /{tenant_slug}/lgpd]."
    ),
}


# =============================================================
# Origens validas do aceite — T-CLI-101 alinha com spec FORWARD.
# =============================================================
ORIGEM_CADASTRO_DIRETO = "CADASTRO_DIRETO"  # operador no balcao OU titular no portal proprio
ORIGEM_IMPORTACAO_LEGADA = "IMPORTACAO_LEGADA"  # CSV/XLSX sem aceite formal (estado restrito)
ORIGEM_MIGRACAO_SISTEMA_ANTERIOR = "MIGRACAO_SISTEMA_ANTERIOR"  # com aceite do sistema antigo

ORIGENS_VALIDAS = (
    ORIGEM_CADASTRO_DIRETO,
    ORIGEM_IMPORTACAO_LEGADA,
    ORIGEM_MIGRACAO_SISTEMA_ANTERIOR,
)


# Dispensas validas (R3 advogado US-CLI-001 + R1 advogado US-CLI-003).
DISPENSA_PJ_SEM_PF = "pj_sem_pf_associada"
DISPENSA_PJ_COM_PF_ACEITE_DECLARADO = "pj_com_pf_aceite_declarado_pelo_tenant"
DISPENSA_PJ_COM_PF_PENDENTE = "pj_com_pf_pendente_aceite"

DISPENSAS_VALIDAS = (
    DISPENSA_PJ_SEM_PF,
    DISPENSA_PJ_COM_PF_ACEITE_DECLARADO,
    DISPENSA_PJ_COM_PF_PENDENTE,
)


# =============================================================
# Bases legais LGPD — T-CLI-101 / P-CLI-A1 AJUSTADO.
# 5 valores (LGPD art. 7º). LEGITIMO_INTERESSE exige `aceite_lgpd_lia_id`
# (CHECK constraint na migration 0018).
# =============================================================
BASE_LEGAL_CONSENTIMENTO = "CONSENTIMENTO"  # LGPD art. 7º I
BASE_LEGAL_EXECUCAO_CONTRATO = "EXECUCAO_CONTRATO"  # LGPD art. 7º V
BASE_LEGAL_OBRIG_LEGAL = "OBRIG_LEGAL"  # LGPD art. 7º II
BASE_LEGAL_LEGITIMO_INTERESSE = "LEGITIMO_INTERESSE"  # LGPD art. 7º IX + art. 10 (LIA)
BASE_LEGAL_PROTECAO_CREDITO = "PROTECAO_CREDITO"  # LGPD art. 7º X (bloqueio/cobrança)

BASES_LEGAIS_VALIDAS = (
    BASE_LEGAL_CONSENTIMENTO,
    BASE_LEGAL_EXECUCAO_CONTRATO,
    BASE_LEGAL_OBRIG_LEGAL,
    BASE_LEGAL_LEGITIMO_INTERESSE,
    BASE_LEGAL_PROTECAO_CREDITO,
)


# `pf_aceite_origem` aceito no endpoint de importacao (R2 advogado).
# Esses valores convivem com ORIGENS_VALIDAS pois mapeiam pra base legal
# DURANTE a importacao — depois de importado, o Cliente recebe origem
# = IMPORTACAO_LEGADA ou MIGRACAO_SISTEMA_ANTERIOR via mapeamento abaixo.
PF_ORIGEM_CONTRATO = "contrato_preexistente_documentado"
PF_ORIGEM_CONSENTIMENTO_OFFLINE = "consentimento_coletado_offline"
PF_ORIGEM_MIGRACAO = "migracao_sistema_anterior_com_aceite"

PF_ACEITE_ORIGENS_VALIDAS = (
    PF_ORIGEM_CONTRATO,
    PF_ORIGEM_CONSENTIMENTO_OFFLINE,
    PF_ORIGEM_MIGRACAO,
)


# Mapeamento `pf_aceite_origem` -> base legal LGPD (T-CLI-101 / P-CLI-A1).
# IMPORTACAO_LEGADA so aceita EXECUCAO_CONTRATO ou OBRIG_LEGAL (NUNCA
# CONSENTIMENTO — sem prova). Consentimento offline documentado vira
# MIGRACAO_SISTEMA_ANTERIOR (com base CONSENTIMENTO).
PF_ORIGEM_PARA_BASE_LEGAL: dict[str, str] = {
    PF_ORIGEM_CONTRATO: BASE_LEGAL_EXECUCAO_CONTRATO,
    PF_ORIGEM_CONSENTIMENTO_OFFLINE: BASE_LEGAL_CONSENTIMENTO,
    PF_ORIGEM_MIGRACAO: BASE_LEGAL_CONSENTIMENTO,
}


# Mapeamento `pf_aceite_origem` -> origem do cadastro final no Cliente.
# Origem indica de onde veio o cadastro, NAO a base legal — sao eixos distintos.
PF_ORIGEM_PARA_ORIGEM_CADASTRO: dict[str, str] = {
    PF_ORIGEM_CONTRATO: ORIGEM_IMPORTACAO_LEGADA,
    PF_ORIGEM_CONSENTIMENTO_OFFLINE: ORIGEM_MIGRACAO_SISTEMA_ANTERIOR,
    PF_ORIGEM_MIGRACAO: ORIGEM_MIGRACAO_SISTEMA_ANTERIOR,
}
