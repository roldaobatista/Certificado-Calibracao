"""Enums de domínio do Tenant — perfil regulatório + direção de mudança.

Origem: ADR-0067 (perfil regulatório do tenant como entidade temporal de 1ª classe).
Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-001 + T-SAN-PERFIL-002.

PRD master `docs/prd.md` §2 declara 4 perfis configuráveis. Esta é a fonte
canônica do enum em domínio puro. Modelos Django (infrastructure) usam
CHAR(1) + CHECK constraint (decisão T8 do plan.md P3 — não usa PG ENUM type
por causa do custo de ALTER TYPE em produção sob carga).
"""

from __future__ import annotations

from enum import Enum


class PerfilRegulatorio(str, Enum):
    """Os 4 perfis regulatórios canônicos (PRD §2 + ADR-0067).

    Valores são CHAR(1) — armazenamento compacto em PG, validado por CHECK.
    Ordem implícita representa progressão da trilha D→C→B→A (BIG-03 do discovery).
    """

    A_ACREDITADO_RBC = "A"
    """Laboratório acreditado RBC/CGCRE com escopo formal.

    Características:
    - Emite certificado RBC com selo CGCRE + número RBC + ILAC-MRA (se aderido).
    - 2ª conferência obrigatória quando regra de decisão != NENHUMA (ADR-0026 + cl. 6.2.5).
    - Validação de software 7.11 completa: URS + IQ + OQ + PQ (ADR-0025).
    - Retenção PII 25a (ISO 17025 cl. 8.4).
    - A3 ICP-Brasil obrigatório em assinaturas (ADR-0009).
    - TSA-ITI qualificado obrigatório em PAdES-LTV (ADR-0047).

    DAP estimado: R$ 1.500-3.000/mês.
    """

    B_RASTREAVEL = "B"
    """Lab rastreável não-acreditado com clientes regulados ocasionais.

    Características:
    - Emite certificado de calibração com bloco "rastreabilidade declarada".
    - 2ª conferência opcional.
    - Validação de software opcional (recomendado URS apenas).
    - Retenção PII 25a recomendada (preparação para A).
    - Perfil núcleo MVP-1 — Balanças Solution (Roldão) é deste perfil.

    DAP estimado: R$ 700-1.500/mês.
    """

    C_EM_PREPARACAO = "C"
    """Lab em preparação para acreditar (trilha D→A).

    Características idênticas a B na operação, mas matriz feature×perfil
    libera URS + OQ parcial como gate da trilha (ADR-0025 + R6 plan.md).
    Subestados C1..C5 da trilha (pré-avaliação → deliberação CGCRE) ficam
    no módulo `licencas-acreditacoes` Wave A (R4).

    DAP estimado: R$ 500-800/mês.
    """

    D_COMERCIAL_PURO = "D"
    """Calibração comercial pura — sem rituais ISO 17025.

    Características:
    - Documento renomeado para "Relatório de Aferição/Verificação"
      (proibido usar palavra "ISO 17025" — hook anti-ISO em Sprint 5).
    - Sem 2ª conferência.
    - Validação de software desabilitada.
    - PII retida 5a (Receita) + anonimização agressiva (LGPD art. 16 III).
    - Eventos WORM hash-chain SEMPRE 25a (INV-HMAC-001..005 invariante; vence
      a retenção PII porque é integridade, não dado pessoal).

    DAP estimado: R$ 300-500/mês.
    """

    @classmethod
    def char(cls, perfil: "PerfilRegulatorio") -> str:
        """Retorna o CHAR(1) usado no banco (A/B/C/D)."""
        return perfil.value

    @classmethod
    def from_char(cls, char: str) -> "PerfilRegulatorio":
        """Constrói o enum a partir do CHAR(1) lido do banco.

        Erro `ValueError` se CHAR inválido (estado impossível pós-CHECK).
        """
        for membro in cls:
            if membro.value == char:
                return membro
        raise ValueError(
            f"PerfilRegulatorio CHAR(1) invalido: {char!r}. "
            f"Esperado: {[m.value for m in cls]}"
        )


class DirecaoMudancaPerfil(str, Enum):
    """Direção de uma mudança em TenantPerfilHistorico.

    Origem: ADR-0067 + plan.md P3 §"Bloco A — schema" (R3 + A1).
    7 valores cobrem todos os fluxos regulatórios CGCRE + autonomia tenant.
    """

    PROVISIONAMENTO_INICIAL = "provisionamento_inicial"
    """Tenant nasceu com este perfil. Não há `perfil_anterior` (NULL no schema)."""

    PROMOCAO_REGULATORIA = "promocao_regulatoria"
    """Tenant promovido UP-only monotônico (D→C, C→B, B→A).

    Exige: motivo ≥100 chars + auditor_cgcre + certificado_acreditacao_documento_id
    + assinatura A3 (INV-TENANT-PERFIL-007). Trilha D→A direta NÃO permitida —
    exige 3 promoções separadas.
    """

    SUSPENSAO_TEMPORARIA_CGCRE = "suspensao_temporaria_cgcre"
    """Lab A com supervisão CGCRE em curso (NIT-DICLA-005 §7.4).

    NÃO rebaixa perfil — preserva A no banco mas seta
    `acreditacao_suspensa_em` + `acreditacao_suspensa_ate`. Predicate
    `tenant_perfil_e({"A"})` retorna False enquanto janela ativa.
    Lab pode reabilitar sem nova auditoria CGCRE.
    """

    CANCELAMENTO_CGCRE = "cancelamento_cgcre"
    """Lab perde acreditação CGCRE definitivamente. Rebaixa A→B.

    Trigger D&O notificação (S7 plan.md): consumer prepara reservation
    of rights pra corretora SUSEP em ≤30 dias.
    """

    REDUCAO_ESCOPO_CGCRE = "reducao_escopo_cgcre"
    """Lab A perde grandeza X mas mantém Y.

    NÃO muda perfil. Atualiza escopos no módulo `licencas-acreditacoes`
    (Wave A). Registrado aqui para rastreabilidade temporal.
    """

    CORRECAO_ADMINISTRATIVA = "correcao_administrativa"
    """Correção de erro de cadastro (ex: tenant cadastrado como B mas
    descobre-se que era A desde o início). Exige aprovação Roldão +
    motivo detalhado.
    """

    REBAIXAMENTO_VOLUNTARIO_CLIENTE = "rebaixamento_voluntario_cliente"
    """Cliente pede rebaixamento (ex: B→D para pagar menos — CDC art. 51 IV
    + Lei 14.181/2021 autonomia contratual).

    Restrições (AC-001-9 spec):
    - Cooldown ≥30 dias entre rebaixamentos.
    - Pré-aviso ≥7 dias antes da chamada.
    - Permitido só para BAIXO (B→D, B→C, C→D). Subir = PROMOCAO_REGULATORIA.
    - Histórico WORM preservado por 25a independente do rebaixamento.
    """

    @classmethod
    def exige_documento_cgcre(cls, direcao: "DirecaoMudancaPerfil") -> bool:
        """Retorna True se a direção exige `certificado_acreditacao_documento_id` preenchido."""
        return direcao in {
            cls.PROMOCAO_REGULATORIA,
            cls.SUSPENSAO_TEMPORARIA_CGCRE,
            cls.CANCELAMENTO_CGCRE,
            cls.REDUCAO_ESCOPO_CGCRE,
        }

    @classmethod
    def emite_evento_outbox(cls, direcao: "DirecaoMudancaPerfil") -> bool:
        """Retorna True se a direção emite evento `TenantPerfilAlterado` no outbox
        (INV-TENANT-PERFIL-006). Provisionamento + correção + redução de escopo
        consolidam apenas no relatório trimestral (US-008).
        """
        return direcao in {
            cls.PROMOCAO_REGULATORIA,
            cls.SUSPENSAO_TEMPORARIA_CGCRE,
            cls.CANCELAMENTO_CGCRE,
            cls.REBAIXAMENTO_VOLUNTARIO_CLIENTE,
        }
