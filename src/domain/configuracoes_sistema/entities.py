"""Entidades do domínio `configuracoes-sistema` (Fatia 1a — T-CFG-012).

Frozen (imutáveis no domínio; mutação = nova instância via mapper na infra).
Reusa VOs compartilhados CNPJ/JanelaVigencia. Sem Django (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.domain.shared.value_objects import CNPJ, JanelaVigencia

from .enums import RegimeNumeracao, RegimeTributario, TipoDocumento, TipoImposto
from .value_objects import Aliquota


@dataclass(frozen=True)
class Empresa:
    """Cadastro tributário do tenant (US-CFG-001). INV-036 (CNPJ único por tenant)."""

    id: UUID
    tenant_id: UUID
    razao_social: str
    cnpj: CNPJ
    regime_tributario: RegimeTributario
    inscricao_estadual: str = ""
    endereco: str = ""
    inscricao_municipal: str = ""
    logo_url: str = ""
    site: str = ""
    telefone: str = ""


@dataclass(frozen=True)
class Filial:
    """Filial de uma empresa (US-CFG-001). INV-037 (exatamente 1 matriz)."""

    id: UUID
    tenant_id: UUID
    empresa_id: UUID
    cnpj: CNPJ
    nome: str
    eh_matriz: bool
    endereco: str = ""
    inscricao_estadual: str = ""
    inscricao_municipal: str = ""
    telefone: str = ""


@dataclass(frozen=True)
class Imposto:
    """Linha de catálogo tributário versionada e imutável (US-CFG-003).

    Mudar alíquota = NOVA linha com nova vigência (INV-CFG-IMPOSTO-IMUTAVEL).
    `vigencia` (JanelaVigencia) determina "vigente em D". Figuras fiscais
    (ADV-02/03): `iss_retido_fonte`, `tem_st` (ST do ICMS — não é regime),
    `simples_excedeu_sublimite`.
    """

    id: UUID
    tenant_id: UUID
    tipo: TipoImposto
    aliquota: Aliquota
    vigencia: JanelaVigencia
    filial_id: UUID | None = None
    cfop_padrao: str = ""
    ncm_padrao: str = ""
    iss_retido_fonte: bool = False
    tem_st: bool = False
    simples_excedeu_sublimite: bool = False
    observacoes: str = ""


@dataclass(frozen=True)
class SerieDocumento:
    """Série de numeração local de documento (US-CFG-002; ADR-0080).

    `regime_numeracao` é DERIVADO do tipo (não vem do caller) — ver
    `transicoes.regime_numeracao_do_tipo`. `proximo_numero` nunca diminui
    (INV-028). Chave de unicidade = (tenant, filial, tipo, prefixo).
    `reset_anual` indica contador por (serie, ano) quando o formato usa `{ano}`.
    """

    id: UUID
    tenant_id: UUID
    tipo: TipoDocumento
    prefixo: str
    proximo_numero: int
    regime_numeracao: RegimeNumeracao
    formato: str
    padding: int = 6
    filial_id: UUID | None = None
    reset_anual: bool = False
    ano_corrente: int | None = None
