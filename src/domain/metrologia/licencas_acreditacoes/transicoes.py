"""Regras puras de status, perfil, anexo e bloqueio (M9 Wave A, T-LIC-013).

Sem Django (ADR-0007). Concentra as decisões que os use cases (Fatia 2) consomem:
status calculado (modelo-de-dominio), validação tipo×perfil (INV-LIC-PERFIL-001 +
D-LIC-10), anexo obrigatório (INV-LIC-ANEXO-001), fronteira de bloqueio por tipo
(D-LIC-5 — REBAIXA vs HARD-409) e pré-condições do modo emergencial (D-LIC-6/7).
"""

from __future__ import annotations

from datetime import date

from .enums import (
    DIAS_VENCE_EM_BREVE,
    StatusDocumento,
    TipoBloqueio,
    TipoDocumentoRegulatorio,
)
from .erros import (
    AnexoObrigatorioError,
    ModoEmergencialInvalidoError,
    PerfilNaoAutorizaCGCREError,
    VigenciaInvalidaError,
)

# Perfis que podem cadastrar acreditação CGCRE (INV-LIC-PERFIL-001 — B/C evoluem p/
# A; D rejeitado — defesa anti-fraude L6).
_PERFIS_CGCRE = frozenset({"A", "B", "C"})
_PERFIL_ACREDITADO = "A"
_MIN_JUSTIFICATIVA_EMERGENCIAL = 100  # chars (INV-033 reconciliado p/ ≥100 — D-LIC-7)
_MAX_JANELA_EMERGENCIAL_DIAS = 7


def calcular_status(
    *,
    vigencia_fim: date,
    hoje: date,
    em_renovacao: bool = False,
    dias_vence_em_breve: int = DIAS_VENCE_EM_BREVE,
) -> StatusDocumento:
    """Status calculado do documento (modelo-de-dominio §DocumentoRegulatorio).

    Precedência: `EM_RENOVACAO` (revisão nova pendente de confirmação) > `VENCIDO`
    (`vigencia_fim < hoje`) > `VENCE_EM_BREVE` (dentro da janela) > `VIGENTE`.
    Não persiste como verdade — é derivado; persistir só como cache de leitura."""
    if em_renovacao:
        return StatusDocumento.EM_RENOVACAO
    if vigencia_fim < hoje:
        return StatusDocumento.VENCIDO
    if (vigencia_fim - hoje).days <= dias_vence_em_breve:
        return StatusDocumento.VENCE_EM_BREVE
    return StatusDocumento.VIGENTE


def validar_tipo_x_perfil(
    *, tipo: TipoDocumentoRegulatorio, perfil: str, escopo: str
) -> None:
    """INV-LIC-PERFIL-001 + D-LIC-10. Cadastro de `ACREDITACAO_CGCRE` exige
    `perfil ∈ {A,B,C}` (server-side — defesa L6) E `escopo` preenchido (RBC-M9-05).
    Perfil D → `PerfilNaoAutorizaCGCREError` (403). Demais tipos: qualquer perfil."""
    if not tipo.e_acreditacao_cgcre:
        return
    if perfil not in _PERFIS_CGCRE:
        raise PerfilNaoAutorizaCGCREError(
            f"perfil {perfil!r} não autoriza cadastro de acreditação CGCRE "
            f"(exige A/B/C — promova via admin Aferê)"
        )
    if not escopo.strip():
        raise VigenciaInvalidaError(
            "acreditação CGCRE exige `escopo` (grandezas/faixas) — RBC-M9-05"
        )


def validar_anexo(*, anexo_sha256: str) -> None:
    """INV-LIC-ANEXO-001 (formaliza INV-046) — todo documento regulatório exige
    anexo probatório com sha256 server-side. Vazio → `AnexoObrigatorioError` (422)."""
    if not anexo_sha256 or not anexo_sha256.strip():
        raise AnexoObrigatorioError(
            "documento regulatório exige anexo probatório (sha256) — evidência de auditoria"
        )


def fronteira_bloqueio(tipo: TipoDocumentoRegulatorio) -> TipoBloqueio:
    """D-LIC-5 / RBC-M9-01 — fronteira de bloqueio por TIPO de documento:

    - `ACREDITACAO_CGCRE` → `REBAIXA_RBC`: vencida NÃO bloqueia (não 409); alimenta o
      cache que o M8 lê → rebaixamento RBC→não-RBC (perfil A) / no-op (B/C/D).
    - `ART`/`RRT`/`CERT_DIGITAL_*` → `HARD_409`: do signatário, vencido inviabiliza a
      assinatura de qualquer certificado (cl. 6.2 / NIT-DICLA-021).
    - demais → `NENHUM` (só alerta)."""
    if tipo.e_acreditacao_cgcre:
        return TipoBloqueio.REBAIXA_RBC
    if tipo.bloqueia_assinatura_hard:
        return TipoBloqueio.HARD_409
    return TipoBloqueio.NENHUM


def validar_modo_emergencial(
    *,
    tipo_documento: TipoDocumentoRegulatorio,
    justificativa: str,
    assinatura_a3_id: object | None,
    janela_dias: int,
) -> bool:
    """INV-033 / INV-LIC-BLOQUEIO-001 (D-LIC-6/7). Pré-condições do modo emergencial:
    justificativa ≥100 chars + `assinatura_a3_id` presente (existência exigida;
    validação criptográfica DIFERIDA — GATE-LIC-EMERGENCIAL-A3-CRIPTO) + janela ≤7d.

    Retorna `libera_apenas_nao_rbc`: para `ACREDITACAO_CGCRE`, o emergencial libera
    APENAS emissão NÃO-RBC — nunca contorna o rebaixamento do M8 (cl. 8.1.3 — RBC-M9-02).
    """
    if len(justificativa.strip()) < _MIN_JUSTIFICATIVA_EMERGENCIAL:
        raise ModoEmergencialInvalidoError(
            f"justificativa exige ≥{_MIN_JUSTIFICATIVA_EMERGENCIAL} chars "
            f"(recebido {len(justificativa.strip())}) — INV-033"
        )
    if assinatura_a3_id is None:
        raise ModoEmergencialInvalidoError(
            "modo emergencial exige assinatura A3 do admin (INV-033)"
        )
    if not 0 < janela_dias <= _MAX_JANELA_EMERGENCIAL_DIAS:
        raise ModoEmergencialInvalidoError(
            f"janela do modo emergencial deve ser 1..{_MAX_JANELA_EMERGENCIAL_DIAS} dias "
            f"(recebido {janela_dias})"
        )
    return tipo_documento.e_acreditacao_cgcre
