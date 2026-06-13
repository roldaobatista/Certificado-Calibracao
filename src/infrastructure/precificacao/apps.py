"""Wave A — frente `precificacao` (#3 da cadeia de preço).

Raiz própria `src/infrastructure/precificacao/` (path achatado —
D-PRC-1; ADR-0072 só normatiza metrologia). Motor de formação de
preço por item (PRECO_FIXO/MARGEM_ALVO/COST_PLUS via stub Wave A),
faixas de aprovação de desconto, pedido one-shot WORM e vínculo
cliente→tabela de preço (ADR-0081 / D-PRC-12).
"""

from __future__ import annotations

from django.apps import AppConfig


class PrecificacaoConfig(AppConfig):
    """Frente `precificacao` (D-PRC-1; plano-dependencia-sistema #3)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.precificacao"
    label = "precificacao"
    verbose_name = "Precificação (regras de formação, faixas, aprovação de desconto)"

    def ready(self) -> None:
        """Registra o predicate ABAC `alcada_cobre` (T-PRC-036 / INV-PRC-APROVACAO-INDEPENDENTE).

        O predicate verifica se o papel do decisor (resource["papel_do_decisor"])
        cobre a alçada exigida no pedido (resource["alcada_exigida"]).

        Hierarquia: DONO ≥ GERENTE ≥ LIVRE. Um GERENTE NÃO pode decidir
        pedido que exige DONO (INV-PRC-APROVACAO-INDEPENDENTE).

        Escopo: só ação `precificacao.aprovar_desconto` — não interfere em
        outros predicates do sistema (FB-A1 / T-FB-01).
        """
        from src.domain.precificacao.enums import (
            Alcada,  # -- import local em ready() é padrão Django para evitar importacao prematura antes do registro do app
        )
        from src.infrastructure.authz.predicates import (
            register_predicate,  # -- idem: ready() é o local correto para registrar predicates de authz (molde M3 OS / M6 escopos-cmc)
        )

        _HIERARQUIA_ALCADA: dict[str, int] = {
            Alcada.LIVRE.value: 0,
            Alcada.GERENTE.value: 1,
            Alcada.DONO.value: 2,
        }

        def alcada_cobre(resource: dict) -> tuple[bool, str]:
            """Predicate ABAC: papel_do_decisor deve cobrir alcada_exigida.

            resource esperado:
              {
                "alcada_exigida": "livre"|"gerente"|"dono",
                "papel_do_decisor": "livre"|"gerente"|"dono",
              }

            Retorna (True, "") se papel cobre; (False, "AlcadaInsuficiente:...") caso contrário.
            """
            alcada_exigida = resource.get("alcada_exigida", "livre")
            papel_do_decisor = resource.get("papel_do_decisor", "livre")

            nivel_exigido = _HIERARQUIA_ALCADA.get(alcada_exigida, 0)
            nivel_papel = _HIERARQUIA_ALCADA.get(papel_do_decisor, 0)

            if nivel_papel >= nivel_exigido:
                return True, ""
            return False, (
                f"AlcadaInsuficiente: papel '{papel_do_decisor}' nao cobre alçada "
                f"exigida '{alcada_exigida}' — papel GERENTE nao pode decidir faixa "
                "DONO (INV-PRC-APROVACAO-INDEPENDENTE / T-PRC-036)."
            )

        register_predicate(
            "alcada_cobre",
            alcada_cobre,
            actions=frozenset({"precificacao.aprovar_desconto"}),
        )
