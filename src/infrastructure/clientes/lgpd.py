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
ORIGEM_BALCAO = "balcao"        # atendente cadastrou no balcao (sem IP do titular)
ORIGEM_PORTAL = "portal"        # titular se cadastrou no portal-cliente (V2)
ORIGEM_IMPORTACAO = "importacao"  # importacao CSV em massa
ORIGEM_API_TERCEIRO = "api_terceiro"  # integracao com sistema legado

ORIGENS_VALIDAS = (
    ORIGEM_BALCAO,
    ORIGEM_PORTAL,
    ORIGEM_IMPORTACAO,
    ORIGEM_API_TERCEIRO,
)


# Dispensas validas (R3 advogado).
DISPENSA_PJ_SEM_PF = "pj_sem_pf_associada"
# Outros motivos surgem com a Wave A (testamento, espolio, etc).

DISPENSAS_VALIDAS = (DISPENSA_PJ_SEM_PF,)
