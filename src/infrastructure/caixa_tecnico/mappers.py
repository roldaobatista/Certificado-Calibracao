"""Mapper model PG ↔ entidade de domínio (Fatia 1b, T-CT-021 — ADR-0007).

Converte bidirecional:
  model_para_caixa_tecnico / caixa_tecnico_para_campos
  model_para_adiantamento / adiantamento_para_campos
  model_para_despesa / despesa_para_campos
  model_para_prestacao / prestacao_para_campos
  model_para_politica / politica_para_campos
  model_para_consentimento / consentimento_para_campos

Zero I/O — funções puras de conversão.
Molde: ``src/infrastructure/contas_receber/mappers.py``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.domain.caixa_tecnico.entities import (
    Adiantamento,
    CaixaTecnico,
    ConsentimentoGpsColaborador,
    Despesa,
    Politica,
    PrestacaoContas,
)
from src.domain.caixa_tecnico.enums import (
    CategoriaDespesa,
    DirecaoPrestacao,
    EstadoAdiantamento,
    EstadoDespesa,
    MeioEntrega,
    TipoDespesa,
)
from src.domain.caixa_tecnico.value_objects import Coordenada, Periodo
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel

from .models import AdiantamentoCaixa as AdiantamentoCaixaModel
from .models import CaixaTecnico as CaixaTecnicoModel
from .models import ConsentimentoGpsColaborador as ConsentimentoGpsColaboradorModel
from .models import DespesaCaixa as DespesaCaixaModel
from .models import PoliticaCaixa as PoliticaCaixaModel
from .models import PrestacaoContasCaixa as PrestacaoContasCaixaModel

_MOEDA = "BRL"


# ---------------------------------------------------------------------------
# CaixaTecnico
# ---------------------------------------------------------------------------


def model_para_caixa_tecnico(m: CaixaTecnicoModel) -> CaixaTecnico:
    """Model PG → entidade CaixaTecnico."""
    return CaixaTecnico(
        caixa_id=m.id,
        tenant_id=m.tenant_id,
        tecnico_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=None,  # ID concreto não persistido na raiz
            hash_original=m.tecnico_referencia_hash,
            key_id=m.tecnico_key_id,
        ),
        desligado_em=m.desligado_em,
        criado_em=m.criado_em,
        revision=m.revision,
    )


def caixa_tecnico_para_campos(ct: CaixaTecnico) -> dict[str, Any]:
    """Entidade CaixaTecnico → kwargs para ORM."""
    return {
        "tenant_id": ct.tenant_id,
        "tecnico_referencia_hash": ct.tecnico_referencia.hash_original,
        "tecnico_key_id": ct.tecnico_referencia.key_id,
        "desligado_em": ct.desligado_em,
    }


# ---------------------------------------------------------------------------
# Adiantamento
# ---------------------------------------------------------------------------


def model_para_adiantamento(m: AdiantamentoCaixaModel) -> Adiantamento:
    """Model PG → entidade Adiantamento."""
    return Adiantamento(
        adiantamento_id=m.id,
        tenant_id=m.tenant_id,
        caixa_id=m.caixa_id,
        tecnico_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=None,
            hash_original=m.tecnico_referencia_hash,
            key_id=m.tecnico_key_id,
        ),
        valor=Dinheiro(m.valor, _MOEDA),
        estado=EstadoAdiantamento(m.estado),
        meio=MeioEntrega(m.meio),
        solicitado_em=m.solicitado_em,
        aprovado_em=m.aprovado_em,
        entregue_em=m.entregue_em,
        recusado_em=m.recusado_em,
        cancelado_em=m.cancelado_em,
        motivo_recusa=m.motivo_recusa or None,
        justificativa=m.justificativa or None,
        aprovado_por_id=m.aprovado_por_id,
        entregue_por_id=m.entregue_por_id,
        criado_em=m.criado_em,
        revision=m.revision,
    )


def adiantamento_para_campos(a: Adiantamento) -> dict[str, Any]:
    """Entidade Adiantamento → kwargs para ORM."""
    return {
        "tenant_id": a.tenant_id,
        "caixa_id": a.caixa_id,
        "tecnico_referencia_hash": a.tecnico_referencia.hash_original,
        "tecnico_key_id": a.tecnico_referencia.key_id,
        "valor": a.valor.centavos,
        "estado": a.estado.value,
        "meio": a.meio.value,
        "solicitado_em": a.solicitado_em,
        "aprovado_em": a.aprovado_em,
        "entregue_em": a.entregue_em,
        "recusado_em": a.recusado_em,
        "cancelado_em": a.cancelado_em,
        "motivo_recusa": a.motivo_recusa or "",
        "justificativa": a.justificativa or "",
        "aprovado_por_id": a.aprovado_por_id,
        "entregue_por_id": a.entregue_por_id,
    }


# ---------------------------------------------------------------------------
# Despesa
# ---------------------------------------------------------------------------


def model_para_despesa(m: DespesaCaixaModel) -> Despesa:
    """Model PG → entidade Despesa.

    ``km_percorridos``: DecimalField no PG → int no domínio (trunca fração de km).
    ``gps_referencia_pii``: string curta armazenada como hash PII (não VO completo);
    o domínio declara ``ReferenciaPIIAnonimizavel | None`` — reconstruído com
    ``uuid_atual_id=None`` e key_id fixo (Wave A: retençao curta, sem rotação).
    """
    coordenada: Coordenada | None = None
    if m.gps_lat is not None and m.gps_lng is not None:
        coordenada = Coordenada(lat=float(m.gps_lat), lng=float(m.gps_lng))

    # gps_referencia_pii: string armazenada como hash; reconstrói VO se presente
    gps_ref: ReferenciaPIIAnonimizavel | None = None
    if m.gps_referencia_pii:
        gps_ref = ReferenciaPIIAnonimizavel(
            uuid_atual_id=None,
            hash_original=m.gps_referencia_pii,
            key_id="v1",  # Wave A: key fixo; Fatia 3a expande com rotação real
        )

    # km_percorridos: DecimalField → int (domínio usa int — D-CT-9)
    km: int | None = None
    if m.km_percorridos is not None:
        km = int(m.km_percorridos)

    return Despesa(
        despesa_id=m.id,
        tenant_id=m.tenant_id,
        caixa_id=m.caixa_id,
        tecnico_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=None,
            hash_original=m.tecnico_referencia_hash,
            key_id=m.tecnico_key_id,
        ),
        categoria=CategoriaDespesa(m.categoria),
        tipo=TipoDespesa(m.tipo),
        valor=Dinheiro(m.valor, _MOEDA),
        estado=EstadoDespesa(m.estado),
        foto_hash=m.foto_hash,
        foto_url=m.foto_url,
        data=m.data,
        descricao=m.descricao or None,
        km_percorridos=km,
        coordenada=coordenada,
        gps_referencia_pii=gps_ref,
        os_id=m.os_id,
        client_offline_id=m.client_offline_id or None,
        despesa_origem_id=m.despesa_origem_id,
        acima_limite=m.acima_limite,
        motivo_rejeicao=m.motivo_rejeicao or None,
        rejeitado_em=m.rejeitado_em,
        validado_em=m.validado_em,
        cancelado_em=m.cancelado_em,
        criado_em=m.criado_em,
        revision=m.revision,
    )


def despesa_para_campos(d: Despesa) -> dict[str, Any]:
    """Entidade Despesa → kwargs para ORM."""
    # gps_referencia_pii: VO → hash string para persistir
    gps_pii_str = d.gps_referencia_pii.hash_original if d.gps_referencia_pii else ""
    return {
        "tenant_id": d.tenant_id,
        "caixa_id": d.caixa_id,
        "tecnico_referencia_hash": d.tecnico_referencia.hash_original,
        "tecnico_key_id": d.tecnico_referencia.key_id,
        "categoria": d.categoria.value,
        "tipo": d.tipo.value,
        "valor": d.valor.centavos,
        "estado": d.estado.value,
        "foto_hash": d.foto_hash,
        "foto_url": str(d.foto_url),
        "data": d.data,
        "descricao": d.descricao or "",
        "km_percorridos": Decimal(d.km_percorridos) if d.km_percorridos is not None else None,
        "gps_lat": Decimal(str(d.coordenada.lat)) if d.coordenada else None,
        "gps_lng": Decimal(str(d.coordenada.lng)) if d.coordenada else None,
        "gps_referencia_pii": gps_pii_str,
        "os_id": d.os_id,
        "client_offline_id": d.client_offline_id or "",
        "despesa_origem_id": d.despesa_origem_id,
        "acima_limite": d.acima_limite,
        "motivo_rejeicao": d.motivo_rejeicao or "",
        "rejeitado_em": d.rejeitado_em,
        "validado_em": d.validado_em,
        "cancelado_em": d.cancelado_em,
    }


# ---------------------------------------------------------------------------
# PrestacaoContas
# ---------------------------------------------------------------------------


def model_para_prestacao(m: PrestacaoContasCaixaModel) -> PrestacaoContas:
    """Model PG → entidade PrestacaoContas."""
    return PrestacaoContas(
        prestacao_id=m.id,
        tenant_id=m.tenant_id,
        caixa_id=m.caixa_id,
        tecnico_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=None,
            hash_original=m.tecnico_referencia_hash,
            key_id=m.tecnico_key_id,
        ),
        periodo=Periodo(de=m.periodo_de, ate=m.periodo_ate),
        total_adiantado=Dinheiro(m.total_adiantado, _MOEDA),
        total_despesas_validadas=Dinheiro(m.total_despesas_validadas, _MOEDA),
        saldo_final=Dinheiro(m.saldo_final, _MOEDA),
        direcao=DirecaoPrestacao(m.direcao),
        fechada_em=m.fechada_em,
        pdf_url=m.pdf_url or None,
        observacoes=m.observacoes or None,
        criado_em=m.criado_em,
    )


def prestacao_para_campos(p: PrestacaoContas) -> dict[str, Any]:
    """Entidade PrestacaoContas → kwargs para ORM."""
    return {
        "tenant_id": p.tenant_id,
        "caixa_id": p.caixa_id,
        "tecnico_referencia_hash": p.tecnico_referencia.hash_original,
        "tecnico_key_id": p.tecnico_referencia.key_id,
        "periodo_de": p.periodo.de,
        "periodo_ate": p.periodo.ate,
        "total_adiantado": p.total_adiantado.centavos,
        "total_despesas_validadas": p.total_despesas_validadas.centavos,
        "saldo_final": p.saldo_final.centavos,
        "direcao": p.direcao.value,
        "fechada_em": p.fechada_em,
        "pdf_url": str(p.pdf_url) if p.pdf_url else "",
        "observacoes": p.observacoes or "",
    }


# ---------------------------------------------------------------------------
# Politica
# ---------------------------------------------------------------------------


def model_para_politica(m: PoliticaCaixaModel) -> Politica:
    """Model PG → entidade Politica.

    ``tarifa_km``: domínio declara ``Dinheiro`` NOT NULL — usa Dinheiro(0) como
    sentinela quando não configurada (NULL no banco = km automático desabilitado).
    ``alcada_aprovacao``: domínio declara ``dict[str, int] | None`` — armazenado
    como BigIntegerField simples (alçada única Wave A; multi-papel Fatia 3+).
    Mapeado como {"default": centavos} quando presente.
    """
    tarifa = Dinheiro(m.tarifa_km, _MOEDA) if m.tarifa_km is not None else Dinheiro(0, _MOEDA)
    # alcada_aprovacao: BigInt → dict simplificado Wave A
    alcada: dict[str, int] | None = None
    if m.alcada_aprovacao is not None:
        alcada = {"default": m.alcada_aprovacao}
    return Politica(
        politica_id=m.id,
        tenant_id=m.tenant_id,
        tarifa_km=tarifa,
        prazo_prestacao_dias=m.prazo_prestacao_dias,
        exige_gps=m.exige_gps,
        limite_por_categoria=m.limite_por_categoria,
        alcada_aprovacao=alcada,
    )


def politica_para_campos(p: Politica) -> dict[str, Any]:
    """Entidade Politica → kwargs para ORM."""
    # tarifa_km: Dinheiro(0) = sem tarifa configurada (NULL no banco)
    tarifa_km_val: int | None = p.tarifa_km.centavos if p.tarifa_km.centavos > 0 else None
    # alcada_aprovacao: dict → BigInt (pega valor "default" Wave A)
    alcada_val: int | None = None
    if p.alcada_aprovacao:
        alcada_val = p.alcada_aprovacao.get("default")
    return {
        "tenant_id": p.tenant_id,
        "tarifa_km": tarifa_km_val,
        "prazo_prestacao_dias": p.prazo_prestacao_dias,
        "exige_gps": p.exige_gps,
        "limite_por_categoria": p.limite_por_categoria,
        "alcada_aprovacao": alcada_val,
    }


# ---------------------------------------------------------------------------
# ConsentimentoGpsColaborador
# ---------------------------------------------------------------------------


def model_para_consentimento(m: ConsentimentoGpsColaboradorModel) -> ConsentimentoGpsColaborador:
    """Model PG → entidade ConsentimentoGpsColaborador."""
    return ConsentimentoGpsColaborador(
        consentimento_id=m.id,
        tenant_id=m.tenant_id,
        colaborador_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=None,
            hash_original=m.colaborador_referencia_hash,
            key_id=m.colaborador_key_id,
        ),
        vigencia_inicio=m.vigencia_inicio,
        revogado_em=m.revogado_em,
        motivo_revogacao=m.motivo_revogacao or None,
        criado_em=m.criado_em,
    )


def consentimento_para_campos(c: ConsentimentoGpsColaborador) -> dict[str, Any]:
    """Entidade ConsentimentoGpsColaborador → kwargs para ORM."""
    return {
        "tenant_id": c.tenant_id,
        "colaborador_referencia_hash": c.colaborador_referencia.hash_original,
        "colaborador_key_id": c.colaborador_referencia.key_id,
        "vigencia_inicio": c.vigencia_inicio,
        "revogado_em": c.revogado_em,
        "motivo_revogacao": c.motivo_revogacao or "",
    }
