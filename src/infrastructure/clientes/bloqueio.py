"""Constants do bloqueio comercial de cliente (US-CLI-004).

5 motivos (R2 advogado) + 4 causation_types (TL4 tech-lead).

Justificativa minima de chars exigida no boundary (R3 implicito).
"""

from __future__ import annotations


# Motivos do bloqueio (R2 advogado)
MOTIVO_MANUAL_INADIMPLENCIA = "manual_inadimplencia"
MOTIVO_MANUAL_QUEBRA_CONFIANCA = "manual_quebra_confianca"
MOTIVO_MANUAL_SOLICITACAO_JURIDICO = "manual_solicitacao_juridico"
MOTIVO_MANUAL_OUTRO = "manual_outro"
MOTIVO_AUTOMATICO_INADIMPLENCIA_90D = "automatico_inadimplencia_90d"

MOTIVOS_VALIDOS: tuple[str, ...] = (
    MOTIVO_MANUAL_INADIMPLENCIA,
    MOTIVO_MANUAL_QUEBRA_CONFIANCA,
    MOTIVO_MANUAL_SOLICITACAO_JURIDICO,
    MOTIVO_MANUAL_OUTRO,
    MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
)

MOTIVOS_MANUAIS: frozenset[str] = frozenset(
    {
        MOTIVO_MANUAL_INADIMPLENCIA,
        MOTIVO_MANUAL_QUEBRA_CONFIANCA,
        MOTIVO_MANUAL_SOLICITACAO_JURIDICO,
        MOTIVO_MANUAL_OUTRO,
    }
)


# causation_type (TL4)
CAUSATION_TITULO_VENCIDO = "titulo_vencido"
CAUSATION_IMPORTACAO_BATCH = "importacao_batch"
CAUSATION_POLITICA_INADIMPLENCIA = "politica_inadimplencia"
CAUSATION_MANUAL_DECISAO_ADMIN = "manual_decisao_admin"

CAUSATION_TYPES_VALIDOS: tuple[str, ...] = (
    CAUSATION_TITULO_VENCIDO,
    CAUSATION_IMPORTACAO_BATCH,
    CAUSATION_POLITICA_INADIMPLENCIA,
    CAUSATION_MANUAL_DECISAO_ADMIN,
)


# Justificativa minima (PRD AC-CLI-004-1)
JUSTIFICATIVA_MIN_CHARS = 30
