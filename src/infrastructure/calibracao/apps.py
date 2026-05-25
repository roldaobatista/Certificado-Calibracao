"""Marco 4 — nucleo metrologico (Calibracao ISO/IEC 17025)."""

from __future__ import annotations

from django.apps import AppConfig


class CalibracaoConfig(AppConfig):
    """Wave A Marco 4 — modulo `calibracao` (metrologia/calibracao)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.calibracao"
    label = "calibracao"
    verbose_name = "Calibracao Metrologica (ISO 17025)"

    def ready(self) -> None:
        """Registra predicates ABAC do modulo (T-CAL-069..075 / Fase 4 Batch B).

        ADR-0012 (AuthorizationProvider) + ADR-0024 + ADR-0026 + ADR-0063.

        Predicates registrados nesta release (Fase 2 Batch C + Fase 4):
          - `cmc_cobre` — calibracao.configurar + iniciar_leituras
            (RBC tenant tem CMC cobrindo grandeza+faixa).
          - `procedimento_vigente_para` — calibracao.configurar
            (cl. 7.2 — procedimento tecnico vigente na data).
          - `pode_aprovar_revisao_2a_conferencia` —
            calibracao.aprovar_revisao + calibracao.aprovar_2a_conferencia
            (segregacao funcoes cl. 6.2.5 + INV-CAL-FRAUDE-REV-001 +
            INV-CAL-FRAUDE-CONF-001 + ADR-0026 excecao 4 condicoes).

        Predicates pendentes pra Fase 5+ (use cases que carregam payload
        ainda nao existem; sao stubs ou diferidos):
          - `padrao_vigente_no_uso` (INV-PAD-003 + INV-PAD-004 — modulo
            metrologia/padroes Wave A separado, ADR-0040).
          - `regra_decisao_acordada_cobre` (cliente_id+regra na data —
            consulta AceiteRegraDecisao; use case `configurarCalibracao`
            instancia, predicate puro em Fase 5).
          - `clausula_override_vigente` (NOVO P-CAL-A3 advogado).
          - `subcontratado_vigente_para` (avaliacao periodica em dia).
          - `pode_marcar_nc_calibracao`, `pode_corrigir_leitura`,
            `pode_registrar_leitura`, `pode_subcontratar` — papeis
            operacionais; mapeados na matriz authz_perfil_acao (seed
            0013) e RBAC ja cobre. ABAC predicate so quando houver
            regra dependente de contexto alem do perfil.
        """
        from src.infrastructure.authz.predicates import register_predicate
        from src.infrastructure.calibracao.predicates_calibracao import (
            cmc_cobre,
            pode_aprovar_revisao_2a_conferencia,
            procedimento_vigente_para,
        )

        # cmc_cobre — escopo: configurar + iniciar_leituras (CMC vigente
        # na data da configuracao + persiste cobertura ate execucao).
        register_predicate(
            "cmc_cobre",
            cmc_cobre,
            actions={"calibracao.configurar", "calibracao.iniciar_leituras"},
        )

        # procedimento_vigente_para — escopo: configurar
        # (cl. 7.2 — procedimento documentado vigente NA configuracao;
        # depois cravado em snapshot de Calibracao).
        register_predicate(
            "procedimento_vigente_para",
            procedimento_vigente_para,
            actions={"calibracao.configurar"},
        )

        # pode_aprovar_revisao_2a_conferencia — escopo: aprovar_revisao +
        # aprovar_2a_conferencia (segregacao funcoes cl. 6.2.5).
        register_predicate(
            "pode_aprovar_revisao_2a_conferencia",
            pode_aprovar_revisao_2a_conferencia,
            actions={
                "calibracao.aprovar_revisao",
                "calibracao.aprovar_2a_conferencia",
            },
        )
