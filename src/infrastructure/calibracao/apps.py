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
        """Registra predicates ABAC do modulo (T-CAL-061..075 / Fase 4).

        ADR-0012 + spec.md secao 16 + ADR-0063 Opcao A.

        Predicates M4 (14 total — invocados nos use cases de Fase 5):

        - `cmc_cobre`: tenant_id, grandeza, faixa, em_data — INV-002 +
          INV-CAL-CMC-001 (cl. 6.4.10). RBC obrigatorio.
        - `padrao_vigente_no_uso`: padrao_id, em_data — INV-PAD-003 +
          INV-PAD-004 (ADR-0040).
        - `procedimento_vigente_para`: procedimento_id, em_data —
          ADR-0030 vigencia temporal.
        - `regra_decisao_aplicavel`: tenant_id, cliente_id, regra,
          em_data — ADR-0024.
        - `regra_decisao_acordada_cobre`: cliente_id, regra, em_data
          — NOVO P3 (INV-CAL-DEC-006 + cl. 7.1.3). Cobre contrato OU
          aceite avulso.
        - `clausula_override_vigente`: cliente_id, em_data — NOVO P3
          (INV-CAL-DEC-002 + CDC art. 25/51).
        - `subcontratado_vigente_para`: subcontratado_id, grandeza,
          em_data — INV-CAL-SUBC-002 + INV-CAL-SUBC-005 (avaliacao
          periodica vigente).
        - `rt_competencia_cobre`: invocacao ATIVADA em M4 (ADR-0063
          Opcao A — lazy em configurar_calibracao + aprovar_revisao +
          aprovar_2a_conferencia). Predicate ja existe em
          ordens_servico — M4 apenas invoca.
        - `pode_aprovar_revisao`: user_id, calibracao_id — papel RT.
        - `pode_aprovar_2a_conferencia`: user_id, calibracao_id —
          INV-CAL-FRAUDE-CONF-001 + ADR-0026 (4 condicoes
          objetivas).
        - `pode_subcontratar`: user_id, tenant_id — papel
          gerente_qualidade.
        - `pode_marcar_nc_calibracao`: user_id, calibracao_id.
        - `pode_corrigir_leitura`: user_id, leitura_id —
          INV-CAL-FRAUDE-COR-001.
        - `pode_registrar_leitura`: user_id, calibracao_id —
          INV-CAL-FRAUDE-EXEC-001.

        Predicates Fase 4 (T-CAL-061..075) — registro ABAC sera
        plugado quando arquivos predicates_calibracao.py forem
        criados. Por enquanto Fase 1 entrega apenas estrutura
        Django + migrations.
        """
        # T-CAL-061..075 — register_predicate sera adicionado em Fase 4.
        # Estrutura intencional: predicates ficam em
        # src/infrastructure/calibracao/predicates_calibracao.py
        # (a criar em Fase 4).
        return None
