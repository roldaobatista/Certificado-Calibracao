"""Base legal LGPD por vínculo e categoria de dado (T-COL-012 / ADV-COL-01).

Constante `BASE_LEGAL_POR_VINCULO_E_CATEGORIA` — mapeamento:
  (Vinculo × categoria) → string da base legal LGPD.

Categorias de dado:
  identificacao   → nome, CPF, e-mail, telefone, foto (dado COMUM de identificação).
  ctps            → Carteira de Trabalho e Previdência Social.
  cnh             → Carteira Nacional de Habilitação.
  foto            → foto de identificação (não biométrico — art. 7º V; ADV-COL-02).
  certificado     → certificados de curso/treinamento externo.

**NÃO é RAT** — o RAT completo é congelado até GATE-LGPD-RAT-CONSOLIDACAO
(ADV-COL-01 / spec §9). Esta constante é a FONTE que o RAT fotografa.

Refs: spec §3 D-COL-6/12; ADV-COL-01; LGPD art. 7º; Lei 11.788/2008.
"""

from __future__ import annotations

from .enums import Vinculo

# ---------------------------------------------------------------------------
# Textos canônicos das bases legais (LGPD art. 7º)
# ---------------------------------------------------------------------------

_ART7_II = "LGPD art. 7º II — cumprimento de obrigação legal ou regulatória pelo controlador"
_ART7_V = "LGPD art. 7º V — execução de contrato ou de procedimentos preliminares"
_ART7_V_LEI_11788 = (
    "LGPD art. 7º V c/c Lei 11.788/2008 (Lei do Estágio) — " "execução de contrato de estágio"
)
_ART7_V_SOCIETARIA = (
    "LGPD art. 7º V c/c base societária — "
    "execução de contrato social / direitos e deveres de sócios"
)

# ---------------------------------------------------------------------------
# Mapa principal: (Vinculo, categoria) → base legal
# ---------------------------------------------------------------------------
# Categorias:
#   identificacao | ctps | cnh | foto | certificado

BASE_LEGAL_POR_VINCULO_E_CATEGORIA: dict[tuple[Vinculo, str], str] = {
    # ── CLT: obrigação legal (registro em CTPS é obrigatório por lei) ──────
    (Vinculo.CLT, "identificacao"): _ART7_II,
    (Vinculo.CLT, "ctps"): _ART7_II,
    (Vinculo.CLT, "cnh"): _ART7_II,  # motorista CLT: exigência legal
    (Vinculo.CLT, "foto"): _ART7_II,
    (Vinculo.CLT, "certificado"): _ART7_II,
    # ── PJ: execução de contrato ───────────────────────────────────────────
    # CTPS é incompatível com PJ (INV-COL-DOC-VINCULO) — base legal
    # incluída como alerta; minimização obriga não coletar (ADV-COL-01).
    (Vinculo.PJ, "identificacao"): _ART7_V,
    (Vinculo.PJ, "ctps"): _ART7_V,  # alerta: minimização impede coleta real
    (Vinculo.PJ, "cnh"): _ART7_V,
    (Vinculo.PJ, "foto"): _ART7_V,
    (Vinculo.PJ, "certificado"): _ART7_V,
    # ── ESTAGIARIO: Lei 11.788/2008 ────────────────────────────────────────
    (Vinculo.ESTAGIARIO, "identificacao"): _ART7_V_LEI_11788,
    (Vinculo.ESTAGIARIO, "ctps"): _ART7_V_LEI_11788,
    (Vinculo.ESTAGIARIO, "cnh"): _ART7_V_LEI_11788,
    (Vinculo.ESTAGIARIO, "foto"): _ART7_V_LEI_11788,
    (Vinculo.ESTAGIARIO, "certificado"): _ART7_V_LEI_11788,
    # ── SOCIO: base societária ─────────────────────────────────────────────
    (Vinculo.SOCIO, "identificacao"): _ART7_V_SOCIETARIA,
    (Vinculo.SOCIO, "ctps"): _ART7_V_SOCIETARIA,
    (Vinculo.SOCIO, "cnh"): _ART7_V_SOCIETARIA,
    (Vinculo.SOCIO, "foto"): _ART7_V_SOCIETARIA,
    (Vinculo.SOCIO, "certificado"): _ART7_V_SOCIETARIA,
    # ── TERCEIRIZADO: execução de contrato ────────────────────────────────
    # CTPS incompatível (INV-COL-DOC-VINCULO) — mesmo aviso do PJ.
    (Vinculo.TERCEIRIZADO, "identificacao"): _ART7_V,
    (Vinculo.TERCEIRIZADO, "ctps"): _ART7_V,  # alerta: minimização impede coleta real
    (Vinculo.TERCEIRIZADO, "cnh"): _ART7_V,
    (Vinculo.TERCEIRIZADO, "foto"): _ART7_V,
    (Vinculo.TERCEIRIZADO, "certificado"): _ART7_V,
}

# Conjunto de categorias válidas (para validação externa)
CATEGORIAS_VALIDAS: frozenset[str] = frozenset(
    {
        "identificacao",
        "ctps",
        "cnh",
        "foto",
        "certificado",
    }
)
