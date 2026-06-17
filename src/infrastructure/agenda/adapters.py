"""Adapters reais das 4 portas cross-módulo (Fatia 3a — T-AGE-040..043).

Cada adapter implementa o Protocol do domínio agenda usando APENAS APIs públicas
dos módulos fechados (OS/colaboradores/RT/contas_receber):
  - OSSchedulingAdapter   → application/operacao/os/atribuir_tecnico (D-AGE-5/TL-AGE-04)
  - ColaboradorAgendaAdapter → leitura via ColaboradorPapel ORM (D-AGE-7/12/15)
  - RTSubstitutoAdapter   → rt_competencia_cobre projetado à data do slot (D-AGE-6)
  - AReceberAdapter       → criar_titulo_manual + DjangoTituloRepository (D-AGE-9)

Regras:
  - NÃO importa ORM de OS/colaboradores em nível de use case; cada adapter é CONCRETO
    em infra da agenda (TL-AGE-04).
  - NÃO usa SQL cru nos schemas de módulos fechados (TL-AGE-05).
  - Regime de jornada é resolvido fail-safe (fail-closed para indeterminado = nao_aplica).
  - IA NUNCA grava override de regime (INV-AG-REGIME-001).

Débito documentado (RBC-AGE-04 / PLAN-AGE-02):
  RTSubstituicao (ADR-0068 §2.2) NÃO existe no banco ainda — o modelo
  ``RTSubstituicao`` não foi criado em Wave A. O adapter consulta:
  1. RT substituto via coluna ``usuario_id`` em ``ResponsavelTecnicoTenant``
     (substituto com encerrado_em IS NULL e data_inicio_vigencia <= data_slot).
  2. Se existir, verifica competência na grandeza via ``RTCompetencia``.
  O predicate ``rt_competencia_cobre`` existente SÓ cobre o titular ativo
  (encerrado_em IS NULL). Para projetar à data futura E atravessar substituição
  formal (modelo RTSubstituicao separado da ADR-0068), um novo modelo de domínio
  é necessário. GATE-RTSUBSTITUICAO-FORMAL criado abaixo como comentário.
  LIMITAÇÃO ACEITA (R15): não projeta vínculo do titular (encerrado_em futuro).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.operacao.agenda.enums import FonteRegime, RegimeJornada
from src.domain.operacao.agenda.value_objects import RegimeJornadaResolvido

logger = logging.getLogger(__name__)


# =============================================================
# T-AGE-040 — OSSchedulingAdapter
# =============================================================


class OSSchedulingAdapter:
    """Adapter real de OSSchedulingPort — chama atribuir_tecnico (TL-AGE-04/05).

    Escrita: usa ``application/operacao/os/atribuir_tecnico.atribuir_tecnico``
    (OS PENDENTE→AGENDADA). Leitura: repositório Django de OS sem SQL cru.
    """

    def atribuir_tecnico(
        self,
        *,
        tenant_id: UUID,
        atividade_id: UUID,
        tecnico_id: UUID,
        agendada_para: datetime,
        actor_usuario_id: UUID,
    ) -> None:
        """Atribui técnico à atividade via use case atribuir_tecnico (D-AGE-5).

        Transita atividade PENDENTE→AGENDADA. OS transita RASCUNHO→AGENDADA
        quando todas as atividades estiverem no estado >= AGENDADA.
        """
        # Import tardio — evita circular em loading de apps
        from src.application.operacao.os.atribuir_tecnico import (
            AtribuicaoAtividade,
            AtribuirTecnicoInput,
            atribuir_tecnico,
        )
        from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

        repo = DjangoOSRepository()
        payload = AtribuirTecnicoInput(
            os_id=self._obter_os_id_por_atividade(
                tenant_id=tenant_id, atividade_id=atividade_id, repo=repo
            ),
            atribuicoes=(
                AtribuicaoAtividade(
                    atividade_id=atividade_id,
                    tecnico_executor_id=tecnico_id,
                    agendada_para=agendada_para,
                ),
            ),
            correlation_id=uuid4(),
            solicitada_em=datetime.now(UTC),
            solicitada_por_user_id=actor_usuario_id,
        )
        atribuir_tecnico(payload=payload, repository=repo)
        logger.info(
            "OSSchedulingAdapter.atribuir_tecnico: atividade=%s tecnico=%s",
            atividade_id,
            tecnico_id,
        )

    def obter_atividade(
        self,
        *,
        tenant_id: UUID,
        atividade_id: UUID,
    ) -> dict[str, object] | None:
        """Lê dados da atividade via repositório público da OS (TL-AGE-05).

        Não usa SQL cru no schema de ordens_servico.
        RLS enforça cross-tenant via tenant_id no contexto do request.
        """
        from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

        repo = DjangoOSRepository()
        atv = repo.get_atividade_by_id(atividade_id)
        if atv is None or atv.tenant_id != tenant_id:
            # Cross-tenant → None (anti-oráculo)
            return None
        return {
            "id": str(atv.id),
            "tenant_id": str(atv.tenant_id),
            "os_id": str(atv.os_id),
            "tipo": atv.tipo.value if atv.tipo else None,
            "estado": atv.estado.value if atv.estado else None,
            "tecnico_executor_id": str(atv.tecnico_executor_id)
            if atv.tecnico_executor_id
            else None,
            "agendada_para": atv.agendada_para.isoformat() if atv.agendada_para else None,
        }

    @staticmethod
    def _obter_os_id_por_atividade(
        *,
        tenant_id: UUID,
        atividade_id: UUID,
        repo: object,
    ) -> UUID:
        """Busca os_id a partir da atividade_id via repositório público (TL-AGE-05).

        Usa get_atividade_by_id do DjangoOSRepository (não SQL cru).
        Valida que a atividade pertence ao tenant (cross-tenant protection).
        """
        from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

        os_repo = DjangoOSRepository()
        atividade = os_repo.get_atividade_by_id(atividade_id)
        if atividade is None or atividade.tenant_id != tenant_id:
            raise ValueError(f"Atividade {atividade_id} não encontrada no tenant {tenant_id}")
        return atividade.os_id


# =============================================================
# T-AGE-041 — ColaboradorAgendaAdapter
# =============================================================

_PAPEL_TECNICO = "tecnico"
_PAPEL_MOTORISTA = "motorista_umc"
_PAPEIS_CAMPO = frozenset({_PAPEL_TECNICO, _PAPEL_MOTORISTA})


class ColaboradorAgendaAdapter:
    """Adapter real de ColaboradorAgendaPort (D-AGE-7/12/15 / TL-AGE-03).

    Lê ColaboradorPapel diretamente (zero extensão do modelo colaboradores — D-AGE-12).
    Regime de jornada fail-safe: override → papel → indeterminado (R6 / INV-AG-REGIME-001).
    IA NUNCA grava override; só humano (RH/gerente) via enquadrar_regime.
    """

    def is_tecnico_campo(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> bool:
        """True se o colaborador tem papel ativo TECNICO ou MOTORISTA_UMC."""
        from src.infrastructure.colaboradores.models import ColaboradorPapel

        return ColaboradorPapel.objects.filter(
            tenant_id=tenant_id,
            colaborador_id=colaborador_id,
            papel__in=list(_PAPEIS_CAMPO),
            data_fim__isnull=True,
            revogado_em__isnull=True,
        ).exists()

    def pendencia_cnh(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> bool:
        """True se MOTORISTA_UMC com pendência de CNH (vencida/irregular — R-COL-1).

        Legível via PapelColaboradorOutputSerializer / campo ColaboradorPapel.pendencia_cnh.
        Zero extensão de colaboradores (D-AGE-12).
        """
        from src.infrastructure.colaboradores.models import ColaboradorPapel

        return ColaboradorPapel.objects.filter(
            tenant_id=tenant_id,
            colaborador_id=colaborador_id,
            papel=_PAPEL_MOTORISTA,
            data_fim__isnull=True,
            revogado_em__isnull=True,
            pendencia_cnh=True,
        ).exists()

    def regime_jornada(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        na_data: date,
    ) -> RegimeJornadaResolvido:
        """Regime fail-safe na data:
        1. Override humano vigente (RegimeJornadaColaborador — tabela da AGENDA) → vence.
        2. Deriva do papel: MOTORISTA_UMC→motorista_profissional, TECNICO→clt_geral.
        3. Papéis de campo conflitantes simultâneos sem override → nao_aplica + indeterminado.
        IA NUNCA grava override (INV-AG-REGIME-001).
        """
        # 1. Busca override vigente na tabela da AGENDA (não de colaboradores)
        from django.db.models import Q

        from src.infrastructure.agenda.models import (
            RegimeJornadaColaborador as RegimeJornadaColaboradorModel,
        )

        override = (
            RegimeJornadaColaboradorModel.objects.filter(
                tenant_id=tenant_id,
                colaborador_id=colaborador_id,
                vigencia_inicio__lte=na_data,
            )
            .filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=na_data))
            .order_by("-vigencia_inicio")
            .first()
        )
        if override is not None:
            return RegimeJornadaResolvido(
                regime=RegimeJornada(override.regime),
                fonte=FonteRegime.OVERRIDE_HUMANO,
            )

        # 2. Deriva do papel ativo
        from src.infrastructure.colaboradores.models import ColaboradorPapel

        papeis_campo = list(
            ColaboradorPapel.objects.filter(
                tenant_id=tenant_id,
                colaborador_id=colaborador_id,
                papel__in=list(_PAPEIS_CAMPO),
                data_fim__isnull=True,
                revogado_em__isnull=True,
            ).values_list("papel", flat=True)
        )

        papeis_unicos = set(papeis_campo)

        if len(papeis_unicos) == 0:
            # Sem papel de campo → nao_aplica
            return RegimeJornadaResolvido(
                regime=RegimeJornada.NAO_APLICA,
                fonte=FonteRegime.DERIVADO_PAPEL,
            )

        if len(papeis_unicos) == 1:
            papel = next(iter(papeis_unicos))
            if papel == _PAPEL_MOTORISTA:
                return RegimeJornadaResolvido(
                    regime=RegimeJornada.MOTORISTA_PROFISSIONAL,
                    fonte=FonteRegime.DERIVADO_PAPEL,
                )
            else:
                # TECNICO → clt_geral
                return RegimeJornadaResolvido(
                    regime=RegimeJornada.CLT_GERAL,
                    fonte=FonteRegime.DERIVADO_PAPEL,
                )

        # 3. Papéis de campo conflitantes (TECNICO + MOTORISTA_UMC) sem override → indeterminado
        logger.warning(
            "ColaboradorAgendaAdapter: papéis de campo conflitantes "
            "para colaborador=%s tenant=%s papéis=%s — regime indeterminado (R6)",
            colaborador_id,
            tenant_id,
            sorted(papeis_unicos),
        )
        return RegimeJornadaResolvido(
            regime=RegimeJornada.NAO_APLICA,
            fonte=FonteRegime.INDETERMINADO,
        )


# =============================================================
# T-AGE-042 — RTSubstitutoAdapter
# =============================================================


class RTSubstitutoAdapter:
    """Adapter real de RTSubstitutoPort — competência do RT projetada ao slot (D-AGE-6).

    DÉBITO DOCUMENTADO (RBC-AGE-04 / PLAN-AGE-02):
      ADR-0068 §2.2 especifica RTSubstituicao como entidade separada para
      declarar substitutos formais de RT. Esse modelo NÃO existe ainda em Wave A.
      GATE-RTSUBSTITUICAO-FORMAL: quando o módulo for criado, este adapter deve
      ser atualizado para consultar RTSubstituicao.vigente_na_data(data_slot)
      ANTES de buscar o titular.

    Implementação atual: consulta todos os RTs vigentes do tenant na data do slot
    (encerrado_em IS NULL). "Vigente na data" = data_inicio_vigencia <= data_slot.
    Limitação aceita (R15/PLAN-AGE-02): não projeta encerrado_em futuro do titular.
    """

    def tem_rt_competente_no_slot(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        data_slot: date,
    ) -> bool:
        """True se há RT vigente no tenant com competência na grandeza na data do slot."""
        return self._checar_competencia(
            tenant_id=tenant_id,
            grandeza=grandeza,
            data_slot=data_slot,
        )

    def eh_deterministica_ausencia(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        data_slot: date,
    ) -> bool:
        """True se a ausência de RT é determinística (nenhum RT com competência e vigência).

        Wave A: a ausência é determinística quando nenhum RT vigente tem competência
        declarada na grandeza para a data do slot. A incerteza (retorno False + sem RT)
        não ocorre nesta implementação — ou há RT competente ou não há.
        """
        return not self._checar_competencia(
            tenant_id=tenant_id,
            grandeza=grandeza,
            data_slot=data_slot,
        )

    @staticmethod
    def _checar_competencia(
        *,
        tenant_id: UUID,
        grandeza: str,
        data_slot: date,
    ) -> bool:
        """Consulta RT + competência projetados à data_slot (PLAN-AGE-01).

        GATE-RTSUBSTITUICAO-FORMAL: quando RTSubstituicao existir, consultar
        substitutos ANTES do titular (ADR-0068 §2.2).
        """
        from django.db.models import Q

        from src.infrastructure.responsavel_tecnico.models import (
            ResponsavelTecnicoTenant,
            RTCompetencia,
        )

        # RTs vigentes do tenant: encerrado_em IS NULL E data_inicio_vigencia <= data_slot
        rts_vigentes = list(
            ResponsavelTecnicoTenant.objects.filter(
                tenant_id=tenant_id,
                encerrado_em__isnull=True,
                data_inicio_vigencia__lte=data_slot,
            )
            .only("id")
            .values_list("id", flat=True)
        )
        if not rts_vigentes:
            return False

        grandeza_norm = grandeza.strip().lower()
        cobre = RTCompetencia.objects.filter(
            tenant_id=tenant_id,
            rt_id__in=rts_vigentes,
            grandeza=grandeza_norm,
            declarado_em__lte=data_slot,
        ).filter(Q(vigente_ate__isnull=True) | Q(vigente_ate__gt=data_slot))

        return cobre.exists()


# =============================================================
# T-AGE-043 — AReceberAdapter
# =============================================================


class AReceberAdapter:
    """Adapter real de AReceberPort — no-show cobrável cria título em CR (D-AGE-9).

    Monta CriarTituloManualInput (cliente como ReferenciaPIIAnonimizavel +
    perfil_no_evento server-side) + DjangoTituloRepository + executar
    (PLAN-AGE-03/R2/INV-AG-NOSHOW-AR-001).
    """

    def criar_titulo_manual(
        self,
        *,
        tenant_id: UUID,
        cliente_id: UUID,
        valor: object,
        descricao: str,
        perfil_no_evento: str,
        referencia_evento_id: UUID,
    ) -> UUID:
        """Cria título manual em contas-receber via use case público (D-AGE-9).

        `valor` é Dinheiro (centavos int) ou objeto com `.centavos`.
        `perfil_no_evento` vem server-side (ContextVar via obter_perfil_tenant_corrente).
        `cliente_id` é resolvido para ReferenciaPIIAnonimizavel via hash do cliente.
        """
        from datetime import date as date_type
        from datetime import timedelta

        from src.application.contas_receber.criar_titulo_manual import (
            CriarTituloManualInput,
            executar,
        )
        from src.domain.contas_receber.enums import MeioCobranca, OrigemTitulo
        from src.infrastructure.contas_receber.repositories import DjangoTituloRepository

        # Resolve centavos
        centavos: int
        if isinstance(valor, int):
            centavos = valor
        elif hasattr(valor, "centavos"):
            centavos = int(valor.centavos)
        else:
            centavos = int(str(valor))

        # Busca hash do cliente para ReferenciaPIIAnonimizavel
        cliente_hash, cliente_key_id = self._obter_hash_cliente(
            tenant_id=tenant_id, cliente_id=cliente_id
        )

        repo = DjangoTituloRepository()
        inp = CriarTituloManualInput(
            tenant_id=tenant_id,
            cliente_referencia_hash=cliente_hash,
            cliente_key_id=cliente_key_id,
            cliente_atual_id=cliente_id,
            valor_centavos=centavos,
            data_vencimento=date_type.today() + timedelta(days=30),
            meio=MeioCobranca.PIX,
            perfil_no_evento=perfil_no_evento,
            # GATE-NO-SHOW-AGENDA: OrigemTitulo ainda não tem NO_SHOW_AGENDA.
            # Usar MANUAL com metadata discriminante até Wave B adicionar o valor.
            origem=OrigemTitulo.MANUAL,
            metadata={
                "origem_real": "no_show_agenda",
                "referencia_evento_id": str(referencia_evento_id),
                "descricao": descricao,
            },
        )
        out = executar(inp, repo=repo)
        logger.info(
            "AReceberAdapter.criar_titulo_manual: titulo=%s evento=%s",
            out.titulo.titulo_id,
            referencia_evento_id,
        )
        return out.titulo.titulo_id

    @staticmethod
    def _obter_hash_cliente(
        *,
        tenant_id: UUID,
        cliente_id: UUID,
    ) -> tuple[str, str]:
        """Obtém (cliente_referencia_hash, cliente_key_id) via hashear_pii_com_salt_tenant.

        O modelo Cliente não armazena hash pré-computado — o hash PII é gerado via
        ``hashear_pii_com_salt_tenant(str(cliente_id), tenant_id)`` (SANEA-02 / FA-A1).
        Esse padrão é o mesmo usado em OS/clientes ao gravar referências cross-módulo.
        """
        from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

        hash_completo = hashear_pii_com_salt_tenant(str(cliente_id), tenant_id)
        # hash_completo = "vN:64hex" — separar key_id do digest
        partes = hash_completo.split(":", 1)
        if len(partes) != 2:
            raise ValueError(
                f"hashear_pii_com_salt_tenant retornou formato inesperado: {hash_completo!r}"
            )
        key_id, digest = partes
        # Reconstrói no formato esperado por ReferenciaPIIAnonimizavel
        return hash_completo, key_id
