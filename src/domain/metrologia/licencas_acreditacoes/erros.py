"""Erros de domínio do módulo licencas-acreditacoes (M9 Wave A, T-LIC-011).

Mapeiam para HTTP na camada REST (Fatia 2). Sem Django (ADR-0007)."""

from __future__ import annotations


class LicencaError(Exception):
    """Base de todos os erros de domínio do módulo."""


class AnexoObrigatorioError(LicencaError):
    """INV-LIC-ANEXO-001 (formaliza INV-046) — documento regulatório exige anexo
    probatório (sha256 server-side) no cadastro/revisão. → 422 ANEXO_OBRIGATORIO."""


class PerfilNaoAutorizaCGCREError(LicencaError):
    """INV-LIC-PERFIL-001 — cadastro de `ACREDITACAO_CGCRE` exige perfil A/B/C
    (defesa anti-fraude L6). Perfil D → 403 ACREDITACAO_CGCRE_EXIGE_PERFIL_ABC."""


class DocumentoBloqueanteVencidoError(LicencaError):
    """D-LIC-5b — documento do tipo ART/RRT/e-CNPJ do signatário vencido inviabiliza
    a assinatura de qualquer certificado → 409 hard (cl. 6.2 / NIT-DICLA-021).
    NÃO usado para acreditação CGCRE (essa REBAIXA via M8 — D-LIC-5a)."""


class ModoEmergencialInvalidoError(LicencaError):
    """INV-033 / INV-LIC-BLOQUEIO-001 — modo emergencial exige justificativa
    ≥100 chars + a3_id + janela ≤7d; sobre acreditação CGCRE libera só não-RBC."""


class VigenciaInvalidaError(LicencaError):
    """ADR-0030 — `vigencia_inicio <= vigencia_fim` (data_validade > data_emissao)."""


class TransicaoLicencaInvalidaError(LicencaError):
    """WORM — `RevisaoDocumento`/`EventoEmergencial` são append-only; edição/exclusão
    de revisão anterior é proibida (INV-LIC-WORM-001)."""
