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
        """Predicates ABAC do modulo — NENHUM bound (decisao consolidacao 2026-06).

        ADR-0012 (AuthorizationProvider) + ADR-0073 (validacao metrologica no
        USE CASE, nao no permission layer DRF).

        **Remocao coordenada (ADR-0073 §3) executada na consolidacao da porta
        REST do Marco 4** — os 3 predicates ABAC antes registrados aqui foram
        DESVINCULADOS do authz (review tech-lead 2026-06, Opcao A):

          - `cmc_cobre` / `procedimento_vigente_para` (eram: calibracao.configurar
            + iniciar_leituras): a validacao de cobertura metrologica migrou pro
            use case `configurar_calibracao` via portas `escopos_cmc.cobre` /
            `procedimentos_calibracao.cobre_procedimento` (ADR-0073/0074/0076 —
            GATE-CAL-CMC-PREDICATE + GATE-CAL-PROC-VIGENTE-PREDICATE FECHADOS).
            O binding aqui era debito de "remocao coordenada" da ADR-0073 §3:
            como exigia resource {grandeza,faixa,...} que o ViewSet nao alimenta
            (`get_authz_resource -> {}`), retornava `cmc_resource_invalido` =>
            403 espurio, fechando a porta REST de configurar.

          - `pode_aprovar_revisao_2a_conferencia` (era: aprovar_revisao +
            aprovar_2a_conferencia): segregacao de funcoes cl. 6.2.5 exige o
            `executor_id` da Calibracao PERSISTIDA — regra que ADR-0073 §2 manda
            ficar no use case, nao no permission layer. Os use cases
            `aprovar_revisao` / `aprovar_2a_conferencia` JA invocam
            `pode_aprovar_revisao_2a_conferencia` com `executor_id` real
            (FraudeRevisorEhExecutor / FraudeConferenteEhRevisorOuExecutor =>
            422). O binding no authz era redundante e MASCARAVA o 422 correto
            com um 403 (resource invalido).

        Authz dessas acoes = RBAC puro (matriz `authz_perfil_acao`, seeds 0013 +
        0021 + 0022). Os enforcements de negocio (cobertura, competencia,
        segregacao) vivem nos use cases com estado server-side — alinhado a
        ADR-0007 + ADR-0073. As funcoes em `predicates_calibracao.py` seguem:
        `pode_aprovar_revisao_2a_conferencia` continua IMPORTADO pelos use cases;
        `cmc_cobre`/`procedimento_vigente_para` ficam orfaos (debito rastreado
        ADR-0073 §3 — nao remover no mesmo commit do desbind).

        Predicates futuros (Fase 5+) so quando houver regra dependente de
        contexto que NAO exija fetch de estado persistido (senao vai pro use
        case por ADR-0073): clausula_override_vigente, subcontratado_vigente_para.
        """
        # Nenhum predicate ABAC registrado (ver docstring — ADR-0073 Opcao A).
        return
