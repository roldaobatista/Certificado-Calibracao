"""Mapper model PG ↔ entidade de domínio `configuracoes-sistema` (T-CFG-026 — ADR-0007).

Colunas tipadas → mapeamento campo-a-campo. O use case nunca conhece Django — só
as entidades do domínio. Enums/VOs reconstruídos a partir dos valores persistidos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.configuracoes_sistema.entities import (
    Empresa,
    Filial,
    Imposto,
    SerieDocumento,
)
from src.domain.configuracoes_sistema.enums import (
    RegimeNumeracao,
    RegimeTributario,
    TipoDocumento,
    TipoImposto,
)
from src.domain.configuracoes_sistema.value_objects import Aliquota
from src.domain.shared.value_objects import CNPJ, JanelaVigencia

if TYPE_CHECKING:
    from src.infrastructure.configuracoes_sistema.models import (
        Empresa as EmpresaModel,
    )
    from src.infrastructure.configuracoes_sistema.models import (
        Filial as FilialModel,
    )
    from src.infrastructure.configuracoes_sistema.models import (
        Imposto as ImpostoModel,
    )
    from src.infrastructure.configuracoes_sistema.models import (
        SerieDocumento as SerieDocumentoModel,
    )


# === Empresa ===


def empresa_model_para_entidade(m: EmpresaModel) -> Empresa:
    return Empresa(
        id=m.id,
        tenant_id=m.tenant_id,
        razao_social=m.razao_social,
        cnpj=CNPJ(value=m.cnpj),
        regime_tributario=RegimeTributario(m.regime_tributario),
        inscricao_estadual=m.inscricao_estadual,
        endereco=m.endereco,
        inscricao_municipal=m.inscricao_municipal,
        logo_url=m.logo_url,
        site=m.site,
        telefone=m.telefone,
    )


def empresa_para_campos(e: Empresa) -> dict[str, Any]:
    """Entidade → kwargs do Model (escrita). `id`/`tenant_id` vão por fora."""
    return {
        "razao_social": e.razao_social,
        "cnpj": e.cnpj.value,
        "regime_tributario": e.regime_tributario.value,
        "inscricao_estadual": e.inscricao_estadual,
        "inscricao_municipal": e.inscricao_municipal,
        "endereco": e.endereco,
        "logo_url": e.logo_url,
        "site": e.site,
        "telefone": e.telefone,
    }


# === Filial ===


def filial_model_para_entidade(m: FilialModel) -> Filial:
    return Filial(
        id=m.id,
        tenant_id=m.tenant_id,
        empresa_id=m.empresa_id,
        cnpj=CNPJ(value=m.cnpj),
        nome=m.nome,
        eh_matriz=m.eh_matriz,
        endereco=m.endereco,
        inscricao_estadual=m.inscricao_estadual,
        inscricao_municipal=m.inscricao_municipal,
        telefone=m.telefone,
    )


def filial_para_campos(f: Filial) -> dict[str, Any]:
    return {
        "empresa_id": f.empresa_id,
        "cnpj": f.cnpj.value,
        "nome": f.nome,
        "eh_matriz": f.eh_matriz,
        "endereco": f.endereco,
        "inscricao_estadual": f.inscricao_estadual,
        "inscricao_municipal": f.inscricao_municipal,
        "telefone": f.telefone,
    }


# === Imposto ===


def imposto_model_para_entidade(m: ImpostoModel) -> Imposto:
    return Imposto(
        id=m.id,
        tenant_id=m.tenant_id,
        tipo=TipoImposto(m.tipo),
        aliquota=Aliquota(valor=m.aliquota),
        vigencia=JanelaVigencia(
            inicio=m.vigencia_inicio,
            fim=m.vigencia_fim,
            revogado_em=m.revogado_em,
            motivo_revogacao=m.motivo_revogacao or None,
        ),
        filial_id=m.filial_id,
        cfop_padrao=m.cfop_padrao,
        ncm_padrao=m.ncm_padrao,
        iss_retido_fonte=m.iss_retido_fonte,
        tem_st=m.tem_st,
        simples_excedeu_sublimite=m.simples_excedeu_sublimite,
        observacoes=m.observacoes,
    )


def imposto_para_campos(i: Imposto) -> dict[str, Any]:
    return {
        "tipo": i.tipo.value,
        "aliquota": i.aliquota.valor,
        "vigencia_inicio": i.vigencia.inicio,
        "vigencia_fim": i.vigencia.fim,
        "revogado_em": i.vigencia.revogado_em,
        "motivo_revogacao": i.vigencia.motivo_revogacao or "",
        "filial_id": i.filial_id,
        "cfop_padrao": i.cfop_padrao,
        "ncm_padrao": i.ncm_padrao,
        "iss_retido_fonte": i.iss_retido_fonte,
        "tem_st": i.tem_st,
        "simples_excedeu_sublimite": i.simples_excedeu_sublimite,
        "observacoes": i.observacoes,
    }


# === SerieDocumento ===


def serie_model_para_entidade(m: SerieDocumentoModel) -> SerieDocumento:
    return SerieDocumento(
        id=m.id,
        tenant_id=m.tenant_id,
        tipo=TipoDocumento(m.tipo),
        prefixo=m.prefixo,
        proximo_numero=m.proximo_numero,
        regime_numeracao=RegimeNumeracao(m.regime_numeracao),
        formato=m.formato,
        padding=m.padding,
        filial_id=m.filial_id,
        reset_anual=m.reset_anual,
        ano_corrente=m.ano_corrente,
    )


def serie_para_campos(s: SerieDocumento) -> dict[str, Any]:
    return {
        "filial_id": s.filial_id,
        "tipo": s.tipo.value,
        "prefixo": s.prefixo,
        "proximo_numero": s.proximo_numero,
        "regime_numeracao": s.regime_numeracao.value,
        "formato": s.formato,
        "padding": s.padding,
        "reset_anual": s.reset_anual,
        "ano_corrente": s.ano_corrente,
    }
