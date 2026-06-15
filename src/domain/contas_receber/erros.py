"""Erros de domínio de contas-receber (Fatia 1a — T-CR-015).

Cada erro carrega `reason` — código estável que a aplicação mapeia para HTTP 4xx.
Hierarquia molde `src/domain/fiscal/erros.py`.
"""

from __future__ import annotations


class ContasReceberDomainError(Exception):
    """Base do domínio contas-receber (mapeada a 4xx/5xx pela aplicação)."""

    reason = "contas_receber_erro"


# --- Validação de cliente (422) ---


class ClienteObrigatorio(ContasReceberDomainError):
    """Título criado sem cliente vinculado (D-CR-16 — campo obrigatório).
    Cliente (uuid ou hash) é obrigatório para rastreabilidade fiscal."""

    reason = "CLIENTE_OBRIGATORIO"


# --- Perfil regulatório (403) ---


class CategoriaReceitaExigePerfilA(ContasReceberDomainError):
    """Categoria `CALIBRACAO_RBC` exige tenant com perfil 'A' (acreditado RBC).
    Mismatch → 403 + evento `contas_receber.categoria_receita_bloqueada`
    (INV-FIN-PERFIL-001 / D-CR-5)."""

    reason = "CATEGORIA_RECEITA_EXIGE_PERFIL_A"


# --- Gateway (503 / 422) ---


class GatewayIndisponivel(ContasReceberDomainError):
    """Provider estourou timeout/rede em `criar_cobranca`/`criar_recorrencia`.
    NÃO é estado do título — nenhum `Titulo` é persistido; aplicação faz 503 +
    publica `contas_receber.gateway_indisponivel` (D-CR-7)."""

    reason = "GATEWAY_INDISPONIVEL"


class ConvenioPixAusente(ContasReceberDomainError):
    """`meio=pix_recorrente` exige `convenio_pix_id NOT NULL` (INV-FIN-GW-002).
    Emissão sem convênio → 422."""

    reason = "CONVENIO_PIX_AUSENTE"


# --- Não encontrado (404) ---


class TituloNaoEncontrado(ContasReceberDomainError):
    """Título inexistente para o `(tenant_id, titulo_id)` informado (cross-tenant via RLS).
    Aplicação mapeia para 404 anti-oráculo. Erro de domínio — a camada application NÃO
    importa o framework web (DRF); a view traduz para HTTP."""

    reason = "TITULO_NAO_ENCONTRADO"


# --- Máquina de estados (409) ---


class TransicaoProibida(ContasReceberDomainError):
    """Transição de estado proibida pela máquina (D-CR-3).
    Ex.: tentar cancelar título já `pago`, ou mover terminal."""

    reason = "TRANSICAO_PROIBIDA"


class EstadoInvalido(ContasReceberDomainError):
    """Estado não reconhecido pelo domínio."""

    reason = "ESTADO_INVALIDO"


class TituloComPagamentoParcial(ContasReceberDomainError):
    """Tentativa de cancelar título com pagamento parcial registrado (D-CR-3).
    `cancelado` só é permitido quando não há `Pagamento` inserido."""

    reason = "TITULO_COM_PAGAMENTO_PARCIAL"


# --- Webhook / segurança (401) ---


class WebhookHMACInvalido(ContasReceberDomainError):
    """HMAC do payload do webhook inválido ou ausente (D-CR-8 / INV-FIN-GW-001).
    Resposta é 401 + incidente `seguranca.webhook_hmac_invalido` (anti-oráculo —
    gateway_id inexistente ≡ HMAC inválido = 401 indistinguível)."""

    reason = "WEBHOOK_HMAC_INVALIDO"


# --- Perfil indeterminado (422 fail-closed) ---


class PerfilIndeterminado(ContasReceberDomainError):
    """`perfil_no_evento` chegou None no consumer (D-CR-6 fail-closed).
    Consumer PROIBIDO de reler `obter_perfil_tenant_corrente()` no worker —
    perfil deve vir do envelope. None → fail-closed → dead-letter."""

    reason = "PERFIL_INDETERMINADO"


# --- Override de bloqueio (422 / 403) ---


class OverrideForaDeAlcada(ContasReceberDomainError):
    """Override solicitado por papel sem autorização (`gerente_financeiro`/`admin_tenant`
    exigidos — D-CR-10)."""

    reason = "OVERRIDE_FORA_DE_ALCADA"


class JustificativaInsuficiente(ContasReceberDomainError):
    """Justificativa do override com menos de 100 caracteres (D-CR-10 / AC-CR-010-5)
    ou bloqueada pelo filtro anti-PII (INV-CR-OVERRIDE-ANTI-PII)."""

    reason = "JUSTIFICATIVA_INSUFICIENTE"


# --- Tenant suspenso (dead-letter) ---


class TenantSuspensoEmissaoBloqueada(ContasReceberDomainError):
    """Consumer NÃO cria título quando tenant está suspenso (PRD §10 / ADR-0035 /
    R-CR-NOVO-3). Mensagem vai para dead-letter e reprocessa ao reativar."""

    reason = "TENANT_SUSPENSO_EMISSAO_BLOQUEADA"
