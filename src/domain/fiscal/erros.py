"""Erros de domínio da frente fiscal/NFS-e (Fatia 1a).

Cada erro carrega `reason` — código estável que a aplicação mapeia para HTTP 4xx
e que os hooks da Fatia 3 protegem. Distinção de regimes:
  - `*PerfilError` → trava metrológica (INV-FIS-001/002) — 422/403 fail-closed.
  - `TransicaoInvalidaError` → máquina de estados (INV-FIS-004) — 409/422.
  - `ProviderTimeoutError` → transporte (D-FIS-3) — NENHUMA persistência + 503/504.
"""

from __future__ import annotations


class FiscalDomainError(Exception):
    """Base do domínio fiscal (mapeada a 4xx pela aplicação)."""

    reason = "fiscal_erro"


# --- Trava metrológica por perfil (INV-FIS-001/002) ---


class DocMetrologicoObrigatorioError(FiscalDomainError):
    """NFS-e de calibração sem o documento metrológico exigido pelo perfil
    (perfil A/B/C sem `certificado_id`; D sem `declaracao_id`). Fail-closed."""

    reason = "DOC_METROLOGICO_OBRIGATORIO"


class DocIncompativelComPerfilError(FiscalDomainError):
    """Documento referenciado é incompatível com o perfil do tenant — ex.: perfil
    B/C referencia certificado que saiu `tipo_acreditacao=RBC` (perfil não-A não
    emite RBC). Defesa anti-fraude documental L6 (AC-FIS-001-8)."""

    reason = "DOC_INCOMPATIVEL_COM_PERFIL"


# --- Máquina de estados (INV-FIS-004) ---


class TransicaoInvalidaError(FiscalDomainError):
    """Transição de estado proibida (ex.: cancelar nota REJECTED, ou re-emitir
    nota terminal). A linha reflete o estado atual; correção só por nova nota."""

    reason = "TRANSICAO_INVALIDA"


class MotivoCancelamentoInvalidoError(FiscalDomainError):
    """Cancelamento sem motivo ≥30 caracteres (AC-FIS-003-1)."""

    reason = "MOTIVO_CANCELAMENTO_INVALIDO"


# --- Transporte (D-FIS-3) ---


class ProviderTimeoutError(FiscalDomainError):
    """Provider estourou timeout/rede em `emit_invoice`. NÃO é estado da nota:
    nenhuma `NotaFiscalServico` é persistida; a aplicação faz `falhar_chave` e
    responde 503/504. A contingência real (AC-FIS-001-3) é diferida."""

    reason = "PROVIDER_TIMEOUT"
