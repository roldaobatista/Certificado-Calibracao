"""Constants do aceite LGPD do modulo clientes (US-CLI-001).

T-CLI-001 do plano docs/dominios/comercial/modulos/clientes/planos/US-CLI-001.md.

Versionamento por hash de texto: cada mudanca de texto vira uma versao nova.
Clientes ja cadastrados preservam a versao que aceitaram (snapshot legal — R2
do advogado).

Pra mostrar texto historico, lookup em TEXTOS_HISTORICOS pela versao gravada
no Cliente.aceite_lgpd_versao.
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


# Origens validas do aceite (R2 advogado + TL2 tech-lead).
ORIGEM_BALCAO = "balcao"  # atendente cadastrou no balcao (sem IP do titular)
ORIGEM_PORTAL = "portal"  # titular se cadastrou no portal-cliente (V2)
ORIGEM_IMPORTACAO = "importacao"  # importacao CSV em massa
ORIGEM_API_TERCEIRO = "api_terceiro"  # integracao com sistema legado

ORIGENS_VALIDAS = (
    ORIGEM_BALCAO,
    ORIGEM_PORTAL,
    ORIGEM_IMPORTACAO,
    ORIGEM_API_TERCEIRO,
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


# Bases legais (R2 advogado US-CLI-003) — usadas quando aceite veio de fora
# (importacao com flag `pf_aceite_origem`). Valor None/vazio = aceite gerado
# pelo proprio Afere (origem balcao/portal).
BASE_LEGAL_ART_7_V = "art_7_v"  # execucao de contrato
BASE_LEGAL_ART_7_I = "art_7_i"  # consentimento

BASES_LEGAIS_VALIDAS = (BASE_LEGAL_ART_7_V, BASE_LEGAL_ART_7_I)


# `pf_aceite_origem` aceito no endpoint de importacao (R2 advogado).
PF_ORIGEM_CONTRATO = "contrato_preexistente_documentado"
PF_ORIGEM_CONSENTIMENTO_OFFLINE = "consentimento_coletado_offline"
PF_ORIGEM_MIGRACAO = "migracao_sistema_anterior_com_aceite"

PF_ACEITE_ORIGENS_VALIDAS = (
    PF_ORIGEM_CONTRATO,
    PF_ORIGEM_CONSENTIMENTO_OFFLINE,
    PF_ORIGEM_MIGRACAO,
)


# Mapeamento `pf_aceite_origem` -> base legal LGPD (R2 advogado).
PF_ORIGEM_PARA_BASE_LEGAL: dict[str, str] = {
    PF_ORIGEM_CONTRATO: BASE_LEGAL_ART_7_V,
    PF_ORIGEM_CONSENTIMENTO_OFFLINE: BASE_LEGAL_ART_7_I,
    PF_ORIGEM_MIGRACAO: BASE_LEGAL_ART_7_I,
}
