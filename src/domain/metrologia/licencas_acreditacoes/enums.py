"""Enums fechados do domínio licencas-acreditacoes (M9 Wave A, T-LIC-010).

str-mixin → serialização JSON nativa (mesmo padrão de certificados/escopos_cmc).
Domain NÃO importa Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class TipoDocumentoRegulatorio(str, Enum):
    """Tipo do documento regulatório da empresa (modelo-de-dominio §Entidades).

    A `fronteira_bloqueio` (D-LIC-5) depende do tipo: `ACREDITACAO_CGCRE` vencida
    REBAIXA (não 409 — delegado ao M8 via cache); `ART`/`RRT`/`CERT_DIGITAL_*` do
    signatário vencidos são HARD-block 409 (cl. 6.2 — sem signatário habilitado não
    se assina certificado nenhum)."""

    ACREDITACAO_CGCRE = "ACREDITACAO_CGCRE"
    ALVARA = "ALVARA"
    LICENCA_AMBIENTAL = "LICENCA_AMBIENTAL"
    LICENCA_SANITARIA = "LICENCA_SANITARIA"
    CERTIDAO_NEGATIVA = "CERTIDAO_NEGATIVA"
    ART = "ART"
    RRT = "RRT"
    CERT_DIGITAL_A1 = "CERT_DIGITAL_A1"
    CERT_DIGITAL_A3 = "CERT_DIGITAL_A3"
    AUTORIZACAO_ANVISA = "AUTORIZACAO_ANVISA"
    AUTORIZACAO_INMETRO = "AUTORIZACAO_INMETRO"
    OUTRO = "OUTRO"

    @property
    def e_acreditacao_cgcre(self) -> bool:
        """Acreditação RBC/CGCRE — só perfil A/B/C cadastra (INV-LIC-PERFIL-001);
        vencida REBAIXA RBC→não-RBC no M8 (NÃO 409 — D-LIC-5a)."""
        return self is TipoDocumentoRegulatorio.ACREDITACAO_CGCRE

    @property
    def exige_titular(self) -> bool:
        """ART/RRT e certificados digitais têm titular (CPF/CNPJ) — PII
        anonimizável (ReferenciaPIIAnonimizavel)."""
        return self in (
            TipoDocumentoRegulatorio.ART,
            TipoDocumentoRegulatorio.RRT,
            TipoDocumentoRegulatorio.CERT_DIGITAL_A1,
            TipoDocumentoRegulatorio.CERT_DIGITAL_A3,
        )

    @property
    def bloqueia_assinatura_hard(self) -> bool:
        """Vencido, inviabiliza a assinatura de QUALQUER certificado (RBC ou não) —
        409 hard legítimo (cl. 6.2 / NIT-DICLA-021 — D-LIC-5b). Distinto da
        acreditação CGCRE (que rebaixa, não bloqueia)."""
        return self in (
            TipoDocumentoRegulatorio.ART,
            TipoDocumentoRegulatorio.RRT,
            TipoDocumentoRegulatorio.CERT_DIGITAL_A1,
            TipoDocumentoRegulatorio.CERT_DIGITAL_A3,
        )


class TipoBloqueio(str, Enum):
    """Fronteira de bloqueio por tipo de documento (D-LIC-5 / RBC-M9-01).

    - `REBAIXA_RBC`: documento (acreditação CGCRE) vencido NÃO bloqueia a emissão;
      alimenta o cache que o M8 lê → rebaixamento RBC→não-RBC (perfil A) / no-op
      (B/C/D). Nunca 409.
    - `HARD_409`: documento (ART/RRT/e-CNPJ do signatário) vencido bloqueia hard a
      assinatura de qualquer certificado (cl. 6.2).
    - `NENHUM`: documento não-bloqueante — só alerta (AC-LIC-003-3)."""

    REBAIXA_RBC = "REBAIXA_RBC"
    HARD_409 = "HARD_409"
    NENHUM = "NENHUM"


class StatusDocumento(str, Enum):
    """Status calculado a partir da vigência (modelo-de-dominio §DocumentoRegulatorio).
    NÃO é persistido como verdade — é derivado de `vigencia_fim` vs hoje (+ flag de
    renovação em curso). Persistir só como cache de leitura."""

    VIGENTE = "VIGENTE"
    VENCE_EM_BREVE = "VENCE_EM_BREVE"
    VENCIDO = "VENCIDO"
    EM_RENOVACAO = "EM_RENOVACAO"

    @property
    def operavel(self) -> bool:
        """Documento ainda autoriza a operação dependente (não disparou bloqueio)."""
        return self in (StatusDocumento.VIGENTE, StatusDocumento.VENCE_EM_BREVE)


class MotivoRevisao(str, Enum):
    """Motivo da `RevisaoDocumento` (append-only WORM). `CADASTRO_INICIAL` é a v1;
    `RENOVACAO` estende a vigência; `RETIFICACAO` corrige dado da revisão atual
    (nova revisão — nunca edita a anterior)."""

    CADASTRO_INICIAL = "CADASTRO_INICIAL"
    RENOVACAO = "RENOVACAO"
    RETIFICACAO = "RETIFICACAO"


class CanalAlerta(str, Enum):
    """Canal do alerta de vencimento (US-LIC-002). Envio real de e-mail é diferido
    (ADR-0060 — Wave B); núcleo dispara DASHBOARD + evento."""

    EMAIL = "EMAIL"
    DASHBOARD = "DASHBOARD"
    APP = "APP"


class StatusAlerta(str, Enum):
    """Ciclo do `AlertaVencimento`."""

    PENDENTE = "PENDENTE"
    ENVIADO = "ENVIADO"
    LIDO = "LIDO"
    FALHOU = "FALHOU"


# Janela canônica de alertas (dias antes do vencimento) — VO JanelaAlerta.
JANELAS_ALERTA_DIAS: tuple[int, ...] = (90, 60, 30, 15, 7)

# Janela default de "vence em breve" (status calculado).
DIAS_VENCE_EM_BREVE: int = 30
