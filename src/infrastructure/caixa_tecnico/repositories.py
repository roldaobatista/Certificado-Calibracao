"""Repositórios Django do módulo caixa_tecnico (Fatia 1b, T-CT-021 — ADR-0007).

Implementam os Protocols de domínio (portas) sobre o ORM Django.
Zero lógica de negócio aqui — apenas persistência + consulta.
Molde: ``src/infrastructure/contas_receber/repositories.py``.

Repositórios:
  CaixaTecnicoRepository — CaixaTecnico + CaixaTecnicoPort (esta_referenciado)
  AdiantamentoRepository — Adiantamento
  DespesaRepository      — Despesa
  PrestacaoRepository    — PrestacaoContas
  PoliticaRepository     — Politica
  ConsentimentoRepository — ConsentimentoGpsColaborador
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from django.db.models import F

from src.domain.caixa_tecnico.entities import (
    Adiantamento,
    CaixaTecnico,
    ConsentimentoGpsColaborador,
    Despesa,
    Politica,
    PrestacaoContas,
)
from src.domain.caixa_tecnico.enums import EstadoAdiantamento, EstadoDespesa

from .mappers import (
    adiantamento_para_campos,
    caixa_tecnico_para_campos,
    consentimento_para_campos,
    despesa_para_campos,
    model_para_adiantamento,
    model_para_caixa_tecnico,
    model_para_despesa,
    model_para_politica,
    model_para_prestacao,
    politica_para_campos,
    prestacao_para_campos,
)
from .models import (
    AdiantamentoCaixa as AdiantamentoCaixaModel,
)
from .models import (
    CaixaTecnico as CaixaTecnicoModel,
)
from .models import (
    ConsentimentoGpsColaborador as ConsentimentoGpsColaboradorModel,
)
from .models import (
    DespesaCaixa as DespesaCaixaModel,
)
from .models import (
    PoliticaCaixa as PoliticaCaixaModel,
)
from .models import (
    PrestacaoContasCaixa as PrestacaoContasCaixaModel,
)


class CaixaTecnicoRepository:
    """Adapter do repositório CaixaTecnico."""

    # --- CaixaTecnico ---

    def obter_por_id(self, tenant_id: UUID, caixa_id: UUID) -> CaixaTecnico | None:
        """Retorna CaixaTecnico por ID (scoped por tenant — RLS + defesa-em-profundidade)."""
        try:
            m = CaixaTecnicoModel.objects.get(id=caixa_id, tenant_id=tenant_id)
        except CaixaTecnicoModel.DoesNotExist:
            return None
        return model_para_caixa_tecnico(m)

    def obter_por_hash(self, tenant_id: UUID, tecnico_referencia_hash: str) -> CaixaTecnico | None:
        """Retorna CaixaTecnico pelo hash do técnico."""
        try:
            m = CaixaTecnicoModel.objects.get(
                tenant_id=tenant_id,
                tecnico_referencia_hash=tecnico_referencia_hash,
            )
        except CaixaTecnicoModel.DoesNotExist:
            return None
        return model_para_caixa_tecnico(m)

    def salvar_novo(self, caixa: CaixaTecnico) -> None:
        """INSERT de novo CaixaTecnico."""
        CaixaTecnicoModel.objects.create(
            id=caixa.caixa_id,
            **caixa_tecnico_para_campos(caixa),
        )

    def atualizar(self, tenant_id: UUID, caixa: CaixaTecnico) -> None:
        """UPDATE do CaixaTecnico (desligado_em / revision)."""
        CaixaTecnicoModel.objects.filter(
            id=caixa.caixa_id,
            tenant_id=tenant_id,
        ).update(
            desligado_em=caixa.desligado_em,
            revision=F("revision") + 1,
        )

    def esta_referenciado(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        """Guard de referência — verifica vínculos ativos no caixa_tecnico.

        Implementa ColaboradorReferenciadoPort (D-CT-12 / INV-CT-REF-001).
        Não usa colaborador_id como FK direta — usa busca pelo hash via
        adapter Fatia 3a. Este método serve para o guard cross-módulo;
        a busca por hash fica em ColaboradorCaixaAdapter (Fatia 3a).

        Verifica:
          - CaixaTecnico sem desligado_em (ativo)
          - Despesa pendente ou validada
          - Adiantamento solicitado, aprovado ou entregue
        """
        # CaixaTecnico ativo (sem desligado_em) — via tenant apenas
        # (colaborador_id → hash resolvido pelo adapter Fatia 3a)
        # Aqui verificamos por tenant; o adapter informa o hash
        # Nota: colaborador_id não é FK direta — este método é stub para
        # Fatia 3a completar com resolução hash→id
        raise NotImplementedError(
            "esta_referenciado requer adapter Fatia 3a (ColaboradorCaixaAdapter) "
            "para resolver colaborador_id → tecnico_referencia_hash."
        )

    def esta_referenciado_por_hash(self, tenant_id: UUID, tecnico_hash: str) -> bool:
        """Guard de referência por hash do técnico (usado pelo adapter Fatia 3a).

        Retorna True se existe qualquer vínculo ativo que impede hard-delete.
        """
        caixa_ativo = CaixaTecnicoModel.objects.filter(
            tenant_id=tenant_id,
            tecnico_referencia_hash=tecnico_hash,
            desligado_em__isnull=True,
        ).exists()
        if caixa_ativo:
            return True

        despesa_ativa = DespesaCaixaModel.objects.filter(
            tenant_id=tenant_id,
            tecnico_referencia_hash=tecnico_hash,
            estado__in=[EstadoDespesa.PENDENTE.value, EstadoDespesa.VALIDADA.value],
        ).exists()
        if despesa_ativa:
            return True

        adiantamento_ativo = AdiantamentoCaixaModel.objects.filter(
            tenant_id=tenant_id,
            tecnico_referencia_hash=tecnico_hash,
            estado__in=[
                EstadoAdiantamento.SOLICITADO.value,
                EstadoAdiantamento.APROVADO.value,
                EstadoAdiantamento.ENTREGUE.value,
            ],
        ).exists()
        return adiantamento_ativo


class AdiantamentoRepository:
    """Adapter do repositório Adiantamento."""

    def obter_por_id(self, tenant_id: UUID, adiantamento_id: UUID) -> Adiantamento | None:
        try:
            m = AdiantamentoCaixaModel.objects.get(id=adiantamento_id, tenant_id=tenant_id)
        except AdiantamentoCaixaModel.DoesNotExist:
            return None
        return model_para_adiantamento(m)

    def salvar_novo(self, adiantamento: Adiantamento) -> None:
        AdiantamentoCaixaModel.objects.create(
            id=adiantamento.adiantamento_id,
            **adiantamento_para_campos(adiantamento),
        )

    def atualizar(self, tenant_id: UUID, adiantamento: Adiantamento) -> None:
        AdiantamentoCaixaModel.objects.filter(
            id=adiantamento.adiantamento_id,
            tenant_id=tenant_id,
        ).update(
            estado=adiantamento.estado.value,
            aprovado_em=adiantamento.aprovado_em,
            entregue_em=adiantamento.entregue_em,
            recusado_em=adiantamento.recusado_em,
            cancelado_em=adiantamento.cancelado_em,
            motivo_recusa=adiantamento.motivo_recusa or "",
            aprovado_por_id=adiantamento.aprovado_por_id,
            entregue_por_id=adiantamento.entregue_por_id,
            revision=F("revision") + 1,
        )

    def listar_por_caixa(
        self,
        tenant_id: UUID,
        caixa_id: UUID,
        estado: str | None = None,
    ) -> list[Adiantamento]:
        qs = AdiantamentoCaixaModel.objects.filter(tenant_id=tenant_id, caixa_id=caixa_id)
        if estado:
            qs = qs.filter(estado=estado)
        return [model_para_adiantamento(m) for m in qs.order_by("-solicitado_em")]


class DespesaRepository:
    """Adapter do repositório Despesa."""

    def obter_por_id(self, tenant_id: UUID, despesa_id: UUID) -> Despesa | None:
        try:
            m = DespesaCaixaModel.objects.get(id=despesa_id, tenant_id=tenant_id)
        except DespesaCaixaModel.DoesNotExist:
            return None
        return model_para_despesa(m)

    def salvar_nova(self, despesa: Despesa) -> None:
        DespesaCaixaModel.objects.create(
            id=despesa.despesa_id,
            **despesa_para_campos(despesa),
        )

    def atualizar(self, tenant_id: UUID, despesa: Despesa) -> None:
        """UPDATE da Despesa — trigger WORM bloqueia UPDATE quando estado=validada."""
        DespesaCaixaModel.objects.filter(
            id=despesa.despesa_id,
            tenant_id=tenant_id,
        ).update(
            estado=despesa.estado.value,
            motivo_rejeicao=despesa.motivo_rejeicao or "",
            rejeitado_em=despesa.rejeitado_em,
            validado_em=despesa.validado_em,
            cancelado_em=despesa.cancelado_em,
            acima_limite=despesa.acima_limite,
            gps_lat=despesa_para_campos(despesa)["gps_lat"],
            gps_lng=despesa_para_campos(despesa)["gps_lng"],
            gps_referencia_pii=despesa.gps_referencia_pii.hash_original
            if despesa.gps_referencia_pii
            else "",
            revision=F("revision") + 1,
        )

    def existe_gateway_offline(self, tenant_id: UUID, client_offline_id: str) -> bool:
        """Idempotência offline — verifica se já existe despesa com este client_offline_id."""
        return (
            DespesaCaixaModel.objects.filter(
                tenant_id=tenant_id,
                client_offline_id=client_offline_id,
            )
            .exclude(client_offline_id="")
            .exists()
        )

    def listar_por_caixa(
        self,
        tenant_id: UUID,
        caixa_id: UUID,
        estado: str | None = None,
    ) -> list[Despesa]:
        qs = DespesaCaixaModel.objects.filter(tenant_id=tenant_id, caixa_id=caixa_id)
        if estado:
            qs = qs.filter(estado=estado)
        return [model_para_despesa(m) for m in qs.order_by("-data", "-criado_em")]


class PrestacaoRepository:
    """Adapter do repositório PrestacaoContas."""

    def obter_por_id(self, tenant_id: UUID, prestacao_id: UUID) -> PrestacaoContas | None:
        try:
            m = PrestacaoContasCaixaModel.objects.get(id=prestacao_id, tenant_id=tenant_id)
        except PrestacaoContasCaixaModel.DoesNotExist:
            return None
        return model_para_prestacao(m)

    def salvar_nova(self, prestacao: PrestacaoContas) -> None:
        """INSERT — trigger WORM congela campos financeiros pós-INSERT."""
        PrestacaoContasCaixaModel.objects.create(
            id=prestacao.prestacao_id,
            **prestacao_para_campos(prestacao),
        )

    def listar_por_caixa(self, tenant_id: UUID, caixa_id: UUID) -> list[PrestacaoContas]:
        qs = PrestacaoContasCaixaModel.objects.filter(
            tenant_id=tenant_id,
            caixa_id=caixa_id,
        ).order_by("-fechada_em")
        return [model_para_prestacao(m) for m in qs]

    def existe_prestacao_no_periodo(
        self, tenant_id: UUID, caixa_id: UUID, periodo_de: date, periodo_ate: date
    ) -> bool:
        """Verifica se já existe prestação que cobre o período (INV-CT-PRESTACAO-001)."""
        return PrestacaoContasCaixaModel.objects.filter(
            tenant_id=tenant_id,
            caixa_id=caixa_id,
            periodo_de__lte=periodo_ate,
            periodo_ate__gte=periodo_de,
        ).exists()


class PoliticaRepository:
    """Adapter do repositório Politica."""

    def obter_por_tenant(self, tenant_id: UUID) -> Politica | None:
        """Retorna a política vigente do tenant (última cadastrada)."""
        try:
            m = PoliticaCaixaModel.objects.filter(tenant_id=tenant_id).latest("criado_em")
        except PoliticaCaixaModel.DoesNotExist:
            return None
        return model_para_politica(m)

    def salvar(self, politica: Politica) -> None:
        PoliticaCaixaModel.objects.create(
            id=politica.politica_id,
            **politica_para_campos(politica),
        )

    def atualizar(self, tenant_id: UUID, politica: Politica) -> None:
        PoliticaCaixaModel.objects.filter(
            id=politica.politica_id,
            tenant_id=tenant_id,
        ).update(**politica_para_campos(politica))


class ConsentimentoRepository:
    """Adapter do repositório ConsentimentoGpsColaborador."""

    def opt_in_vigente(
        self,
        tenant_id: UUID,
        colaborador_referencia_hash: str,
        na_data: date | datetime,
    ) -> bool:
        """Verifica se o colaborador tem opt-in GPS ativo na data (D-CT-6).

        Implementa ConsentimentoGpsPort semântica via hash (adapter Fatia 3a
        resolve colaborador_id → hash).
        """
        return ConsentimentoGpsColaboradorModel.objects.filter(
            tenant_id=tenant_id,
            colaborador_referencia_hash=colaborador_referencia_hash,
            vigencia_inicio__lte=na_data,
            revogado_em__isnull=True,
        ).exists()

    def salvar_novo(self, consentimento: ConsentimentoGpsColaborador) -> None:
        """INSERT de novo consentimento (append-only)."""
        ConsentimentoGpsColaboradorModel.objects.create(
            id=consentimento.consentimento_id,
            **consentimento_para_campos(consentimento),
        )
