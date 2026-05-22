"""Enum canonico de acoes de evento de dominio (BLOQ-A1 advogado).

Lista mantida em sincronia com o conjunto de eventos publicados via
`publicar_evento`. CHECK constraint do banco (`bus_outbox_acao_enum
_semantico`) garante o formato slug `dominio.entidade.op[.var]`; este
modulo garante o conjunto FECHADO de valores permitidos.

Cada modulo Wave A adiciona suas acoes com PR revisado pelo tech-lead
e auditor de seguranca. Manter ordenado por dominio.entidade.

Por que aqui (e nao no dominio): a tabela `bus_outbox` mora em F-A
(infrastructure/audit) — manter o enum aqui evita dependencia reversa
infrastructure -> domain.
"""

from __future__ import annotations

from typing import Final

# Marco 1 `clientes` — US-CLI-001..006.
ACOES_CLIENTES: Final[frozenset[str]] = frozenset(
    {
        "cliente.criado",
        "cliente.atualizado",
        "cliente.mesclado",
        "cliente.bloqueado",
        "cliente.desbloqueado",
        "cliente.importado_csv",
        "cliente.consentimento_revogado",
        "cliente.dados_eliminados",
        "cliente.dados_anonimizados",
        "cliente.dados_exportados",
        # T-CLI-119 (US-CLI-006 AC-006-6) — incidente PII (Res. ANPD 15/2024)
        "cliente.pii.incidente_detectado",
    }
)

# Eventos sistema (modo_sistema=1) — sem tenant_id.
ACOES_SISTEMA: Final[frozenset[str]] = frozenset(
    {
        "sistema.tenant_provisionado",
        "sistema.tenant_offboarded",
        "sistema.outbox_envenenado",
        # T-CLI-104 — circuit breaker observado AcessoDadosCliente
        "sistema.breaker_acesso_pii.disparado",
        "sistema.breaker_acesso_pii.normalizado",
        # T-EQP-027 (AC-EQP-003-4) — lockout 24h disparado por excesso de
        # 4xx no QR publico (>=100 4xx em 1h por IP). Payload sanitizado:
        # ip_hash, janela_temporal, contagem_4xx, lockout_ate.
        "sistema.qr_lockout_disparado",
        # T-EQP-032 (AC-EQP-003-9 / P-EQP-S2) — rate-limit global por
        # tenant excedido em /v1/qr/* (cross-tenant ou anonimo).
        # Payload sanitizado: tenant_id, janela_dia, contagem_requests,
        # limite_calculado, n_equipamentos_ativos.
        "sistema.qr_scraping_suspeito",
    }
)

# Marco 2 `responsavel_tecnico` (US-EQP-007 / P-EQP-R10) — gestao do RT do tenant.
ACOES_RT: Final[frozenset[str]] = frozenset(
    {
        "tenant.rt.cadastrado",
        "tenant.rt.encerrado",
        "tenant.rt.trocado",
        "tenant.rt.competencia_declarada",
    }
)

# Marco 2 `equipamentos` (US-EQP-001..006).
ACOES_EQUIPAMENTOS: Final[frozenset[str]] = frozenset(
    {
        "equipamento.criado",
        # T-EQP-009 (AC-EQP-001-7b / P-EQP-T4) - promocao D<C<B<A do
        # perfil_tenant_snapshot via SECURITY DEFINER. 25a WORM (RBC).
        "equipamento.perfil_promovido",
        # T-EQP-017 (AC-EQP-002-6 / INV-EQP-VERSAO-002) - versao criada
        # de campo descritivo. Payload sanitizado (5 campos positivos,
        # 7 proibidos). 25a WORM (RBC + ISO 17025 cl. 8.4).
        "equipamento.versao_criada",
        # T-EQP-022 (US-EQP-002b AC-EQP-002b-5) - 3 transicoes terminais
        # da Aprovacao gestor_qualidade. Cadeia auditavel ISO 17025
        # cl. 6.2 (segregacao de funcoes) + RBC. 25a WORM.
        "equipamento.versao_aprovada",
        "equipamento.versao_rejeitada",
        "equipamento.versao_expirada",
        # T-EQP-040 (US-EQP-004 AC-EQP-004-7) - efetivacao de
        # transferencia de equipamento entre clientes (mesmo tenant).
        # Payload sanitizado: cedente_id_hash + cessionario_id_hash +
        # transferencia_id + motivo_categoria + texto_termo_versao_id.
        "equipamento.transferido",
        # T-EQP-039 (US-EQP-004 AC-EQP-004-6 / P-EQP-R6) - consentimento
        # granular do cedente sobre visualizacao do historico pos-
        # transferencia. Payload sanitizado: equipamento_id +
        # transferencia_id + consentimento_id + nivel + cedente_id_hash +
        # via_concessao + concedido_em. 25a WORM (LGPD art. 8).
        "equipamento.consentimento_historico_concedido",
        # T-EQP-041 (US-EQP-004 AC-EQP-004-8 / P-EQP-R6) - revogacao
        # posterior do consentimento. Payload sanitizado: equipamento_id
        # + consentimento_id + cedente_id_hash + justificativa_hash +
        # via_revogacao + revogado_em. 25a WORM.
        "equipamento.consentimento_historico_revogado",
    }
)

ACOES_CANONICAS: Final[frozenset[str]] = (
    ACOES_CLIENTES | ACOES_SISTEMA | ACOES_RT | ACOES_EQUIPAMENTOS
)


def assert_acao_canonica(acao: str) -> None:
    """Helper pra chamador validar antes de `publicar_evento`.

    O banco tambem valida via CHECK; aqui eh fail-fast em camada Python
    (mensagem clara) — defesa em profundidade.
    """
    if acao not in ACOES_CANONICAS:
        raise ValueError(
            f"acao '{acao}' nao esta em acoes_canonicas.ACOES_CANONICAS. "
            "Cada acao nova exige PR + revisao do tech-lead + auditor de "
            "seguranca (BLOQ-A1 advogado)."
        )
