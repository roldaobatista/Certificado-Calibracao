"""Entidades do domínio Orçamentos — T-ORC-012.

Dataclasses frozen, sem Django, sem infrastructure.

Hierarquia:
  Orcamento (raiz)
    └─ VersaoOrcamento (Padrão B imutável — D-ORC-8)
         └─ ItemOrcamento (carimbo PrecoResolvido SEM margem — INV-ORC-MARGEM-OFF)
  LinkPublico    (1 ativo por orçamento — INV-ORC-LINK-TOKEN)
  Aprovacao      (WORM Padrão B — INV-ORC-APROVACAO-WORM)
  AnaliseCriticaOrcamento  (WORM Padrão B — D-ORC-15 / INV-ORC-ANALISE-WORM)
  Template       (Padrão C soft-delete — D-ORC-13)

REGRA CRÍTICA INV-ORC-MARGEM-OFF:
  ItemOrcamento NUNCA tem campo de margem, custo ou comissão.
  Esses campos vivem APENAS em ``ItemCalculado`` do módulo ``precificacao``
  (visível só para quem tem ``orcamento.ver_margem`` — D-ORC-10/TL-ORC-06).

Refs:
  spec §4  — modelo completo
  D-ORC-1  — PrecoResolvido (carimbo imutável de preço)
  D-ORC-3  — EstadoOrcamento (máquina de estados)
  D-ORC-4  — ReferenciaPIIAnonimizavel (cliente)
  D-ORC-7  — Aprovacao WORM (aceite rico + LGPD)
  D-ORC-8  — VersaoOrcamento imutável (Padrão B)
  D-ORC-13 — Template com gate selo RBC
  D-ORC-15 — AnaliseCriticaOrcamento WORM (probatório cl. 7.1)
  D-ORC-16 — TipoAtividadeAlvo / TipoItemComercial por item
  D-ORC-17 — HMAC aprovador Wave A (KMS difere para GATE-ORC-KMS-APROVADOR)
  INV-ORC-MARGEM-OFF — snapshot sem margem/custo
  INV-ORC-EQUIP-ITEM — item calibração tem equipamento_id; comercial não
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.domain.comercial.orcamentos.enums import (
    CanalAprovacao,
    EstadoOrcamento,
    TipoAtividadeAlvo,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.shared.value_objects import Dinheiro, JanelaVigencia

# =====================================================================
# AGREGADO RAIZ
# =====================================================================


@dataclass(frozen=True)
class Orcamento:
    """Agregado raiz do módulo Orçamentos (spec §4 / D-ORC-2).

    ``estado`` segue máquina D-ORC-3 (``transicoes.py``).
    ``validade`` é ``JanelaVigencia`` (ADR-0030) — ``vigente_em`` decide expiração.
    Valores monetários usam o VO ``Dinheiro`` (centavos+moeda, aritmética segura —
    D-ORC-1; evita mistura de escala Decimal×centavos).
    """

    id: UUID
    tenant_id: UUID

    # Cliente via ReferenciaPIIAnonimizavel (D-ORC-4 / ADR-0032)
    cliente_atual_id: UUID | None          # FK SET_NULL quando cliente for anonimizado
    cliente_referencia_hash: str           # HMAC NOT NULL — referência permanente pós-anonimização
    cliente_key_id: str                    # versão da chave KMS (rotação)

    numero: int                            # sequencial gap-less por tenant (D-ORC-18)
    estado: EstadoOrcamento

    validade: JanelaVigencia               # ``vigente_em`` determina expiração (ADR-0030)

    # Totais como ``Dinheiro`` VO (D-ORC-1) — compostos por ``calcular_precos`` (D-ORC-10)
    total_bruto: Dinheiro
    descontos: Dinheiro
    impostos: Dinheiro
    liquido: Dinheiro

    comissao_prevista: Dinheiro            # só visível com ``orcamento.ver_margem``

    condicoes_pagamento: CondicoesPagamento

    criado_em: datetime
    criado_por: UUID                       # user_id

    # Opcionais
    template_id: UUID | None = None
    tabela_preco_id: UUID | None = None
    observacoes: str | None = None
    responsavel_id: UUID | None = None
    chamado_origem_id: UUID | None = None


# =====================================================================
# VERSÃO DO ORÇAMENTO (Padrão B — imutável)
# =====================================================================


@dataclass(frozen=True)
class VersaoOrcamento:
    """Snapshot imutável de uma versão do orçamento (D-ORC-8 / Padrão B).

    V1 gerada ao enviar (``enviar_orcamento``).
    V2/V3 + comparação = Wave B (US-ORC-003).
    ``revogado_em`` + ``motivo_revogacao`` permitem "anular" sem DELETE.
    ``snapshot`` = jsonb — contém itens+condições+totais congelados.
    """

    id: UUID
    orcamento_id: UUID
    tenant_id: UUID
    numero_versao: int                     # começa em 1
    snapshot: dict[str, Any]              # jsonb imutável após INSERT (trigger WORM D-ORC-8)
    criada_em: datetime
    criada_por: UUID

    # Revogação (Padrão B — soft-revoke, não DELETE)
    revogado_em: datetime | None = None
    motivo_revogacao: str | None = None


# =====================================================================
# ITEM DO ORÇAMENTO
# =====================================================================


@dataclass(frozen=True)
class ItemOrcamento:
    """Item de uma versão do orçamento.

    Bifurcação central (INV-ORC-EQUIP-ITEM / D-ORC-16):
      - ``equipamento_id`` preenchido  → item técnico (calibração/manutenção/…)
                                         vira ``AtividadeDaOS``.
      - ``equipamento_id`` None        → item comercial (deslocamento/taxa/outro)
                                         vira ``ItemComercialOS`` na OS.

    REGRA CRÍTICA INV-ORC-MARGEM-OFF:
      NÃO há campos ``margem``, ``custo``, ``custo_unitario`` ou similares.
      O carimbo de preço é ``preco_resolvido`` (PrecoResolvido — D-ORC-1).
    """

    id: UUID
    versao_id: UUID
    tenant_id: UUID
    catalogo_item_id: UUID                 # FK ao catálogo (pps)
    sequencia: int                         # 1-based; rastro item↔atividade (D-ORC-11)

    # Carimbo de preço IMUTÁVEL (INV-ORC-PRECO-001 / D-ORC-1)
    preco_resolvido: PrecoResolvido        # snapshot probatório completo

    preco_final: Dinheiro                  # preço unitário final após desconto (Dinheiro VO)
    desconto_pct: Decimal                  # percentual de desconto (0..100) — não é dinheiro
    desconto_valor: Dinheiro               # valor de desconto (Dinheiro VO)
    quantidade: Decimal                    # quantidade (pode ser fracionária) — não é dinheiro
    total: Dinheiro                        # preco_final * quantidade (Dinheiro VO)

    semaforo: str                          # 'verde' | 'amarelo' | 'vermelho' (precificacao)
    descricao_snapshot: str               # descrição do item congelada no momento

    # Bifurcação técnico × comercial (INV-ORC-EQUIP-ITEM / D-ORC-16)
    equipamento_id: UUID | None = None
    """Preenchido apenas em itens técnicos (calibração/manutenção/etc.).
    None indica item comercial (deslocamento, taxa, outro)."""

    tipo_atividade_alvo: TipoAtividadeAlvo | None = None
    """Tipo de atividade para itens técnicos. None para itens comerciais."""

    tipo_item_comercial: TipoItemComercial | None = None
    """Preenchido apenas para itens comerciais (quando equipamento_id is None)."""

    def __post_init__(self) -> None:
        # Consistência interna: item técnico tem equipamento; comercial não
        if self.equipamento_id is not None and self.tipo_atividade_alvo is None:
            raise ValueError(
                "ItemOrcamento: equipamento_id preenchido exige tipo_atividade_alvo "
                "(INV-ORC-EQUIP-ITEM)."
            )
        if self.equipamento_id is None and self.tipo_atividade_alvo is not None:
            raise ValueError(
                "ItemOrcamento: tipo_atividade_alvo só é válido quando equipamento_id "
                "está preenchido (INV-ORC-EQUIP-ITEM)."
            )


# =====================================================================
# LINK PÚBLICO (token de aprovação)
# =====================================================================


@dataclass(frozen=True)
class LinkPublico:
    """Token de acesso público para aprovação do orçamento (D-ORC-7 / INV-ORC-LINK-TOKEN).

    Apenas 1 link ativo por orçamento (partial unique WHERE revogado_em IS NULL).
    Token = ``secrets.token_urlsafe(32)`` ≥128 bits (ADV-ORC-08a).
    Expiração checada no GET e no POST do endpoint público.
    """

    id: UUID
    orcamento_id: UUID
    tenant_id: UUID
    token: str                             # opaco, ≥128 bits
    expira_em: datetime
    criado_em: datetime

    revogado_em: datetime | None = None
    motivo_revogacao: str | None = None

    @property
    def ativo(self) -> bool:
        """True se o link não foi revogado (ignora expiração — checar separado)."""
        return self.revogado_em is None


# =====================================================================
# APROVAÇÃO (WORM Padrão B)
# =====================================================================


@dataclass(frozen=True)
class Aprovacao:
    """Registro imutável de aprovação do orçamento (D-ORC-7 / INV-ORC-APROVACAO-WORM).

    WORM Padrão B: INSERT-only; trigger PG bloqueia UPDATE/DELETE (INV-001).

    PII do aprovador: HMAC Wave A (D-ORC-17).
    Exibição do nome/email = GATE-ORC-KMS-APROVADOR (cifragem KMS-tenant difere para Wave B).

    ``lgpd_aceite_versao_termo`` + ``lgpd_aceite_texto_hash`` = prova probatória
    do consentimento (ADV-ORC-04 — não apenas booleano).

    ``ressalvas_aceitas`` (bool): True quando análise crítica = ``com_ressalva``
    e aprovador confirmou explicitamente (cl. 7.1.1-d / D-ORC-7 C2).
    """

    id: UUID
    orcamento_id: UUID
    versao_id: UUID
    tenant_id: UUID

    aprovado_em: datetime
    canal: CanalAprovacao

    # Identificação do aprovador (HMAC — D-ORC-17)
    nome_aprovador_hash: str               # HMAC(nome, chave_tenant)
    email_aprovador_hash: str             # HMAC(email, chave_tenant)

    # Aceite LGPD rico (ADV-ORC-04)
    lgpd_aceite_versao_termo: str         # ex.: "v2026-01"
    lgpd_aceite_texto_hash: str           # hash do texto exibido (prova do consentido)

    # Forense
    ip_hash: str                           # HMAC(ip_real, chave_servidor)
    user_agent: str

    # Confirmação de ressalvas (cl. 7.1.1-d / D-ORC-7)
    ressalvas_aceitas: bool = False

    # Aprovação interna: user_id do aprovador logado
    aprovado_por: UUID | None = None


# =====================================================================
# ANÁLISE CRÍTICA (WORM Padrão B — D-ORC-15)
# =====================================================================


@dataclass(frozen=True)
class AnaliseCriticaOrcamento:
    """Registro imutável de análise crítica cl. 7.1 ISO 17025 (D-ORC-15).

    WORM Padrão B: INSERT-only; trigger PG anti-mutação (INV-ORC-ANALISE-WORM).

    ``itens_avaliados``: lista de dicts com registro probatório por item
    de calibração (cl. 7.1.1-a / C1):
      {
        equipamento_id: str,
        grandeza: str,
        faixa_min: str,
        faixa_max: str,
        unidade: str,
        cobre_cmc: bool,
        cmc_codigo_ref: str | None,
        procedimento_ok: bool,
        procedimento_id: str | None,
        procedimento_codigo: str | None,   # ex.: "POP-CAL-0042 rev.3"
        procedimento_versao: str | None,
        ressalvas: list[str],
      }

    ``snapshot_hash``: hash de canonicalização ADR-0029 — carimbado no
    envelope ``orcamento.aprovado`` (D-ORC-6) e verificável offline.

    ``avaliada_por``:
      - Aprovação interna → ``user_id`` do aprovador.
      - Aprovação pública → ``"SISTEMA/AUTO:<aprovacao_id>"`` (C5 / cl. 7.5.1-b).

    ``norma_referencia``: literal ``"ISO/IEC 17025:2017 cl. 7.1.1"`` (C6).
    """

    id: UUID
    orcamento_id: UUID
    versao_id: UUID
    tenant_id: UUID

    perfil_no_evento: str                 # snapshot do perfil no momento: "A"|"B"|"C"|"D"
    veredito: VeredictoAnaliseCritica
    norma_referencia: str                 # "ISO/IEC 17025:2017 cl. 7.1.1" (C6)

    itens_avaliados: tuple[dict[str, Any], ...]  # registro probatório por item (C1)

    snapshot_hash: str                    # canonicalização ADR-0029
    avaliada_em: datetime                 # server-side (nunca client-supplied)
    avaliada_por: str                     # user_id str OU "SISTEMA/AUTO:<aprovacao_id>"


# =====================================================================
# TEMPLATE (Padrão C — soft-delete)
# =====================================================================


@dataclass(frozen=True)
class Template:
    """Template de orçamento reutilizável (D-ORC-13 / US-ORC-005).

    ``selo_rbc``: se True, só pode ser salvo em perfil A (gate no hook —
    ``D-ORC-13``). Perfil ≠ A com ``selo_rbc=True`` → hook bloqueia.

    ``itens_default``: jsonb com itens pré-carregados (catálogo_item_id + qty).
    ``condicoes_default``: jsonb com CondicoesPagamento default.

    Padrão C: ``deletado_em`` permite soft-delete sem perda de histórico.
    """

    id: UUID
    tenant_id: UUID
    nome: str
    tipo: str                              # ex.: "calibracao_balanca", "manutencao_preventiva"
    itens_default: list[dict[str, Any]]   # [{catalogo_item_id, quantidade, ...}]
    condicoes_default: dict[str, Any]     # serialização de CondicoesPagamento
    selo_rbc: bool
    criado_em: datetime
    criado_por: UUID

    deletado_em: datetime | None = None
    deletado_por: UUID | None = None

    @property
    def ativo(self) -> bool:
        return self.deletado_em is None
