"""Predicate `decisor_tem_competencia_para_atividade` (T-EQP-063 / RBC cl. 6.2).

Usado em:
- US-EQP-002b-6 (aprovacao gestor_qualidade): valida que o decisor de uma
  aprovacao de mudanca de classe metrologica tem competencia DECLARADA
  na grandeza do equipamento.
- Wave A modulo `qualidade/competencias` substitui esta consulta por
  matriz completa (GATE-EQP-4); aqui o predicate ja contrata a interface.

Algoritmo:
1. Receber tenant_id (resolvido pelo chamador via contexto multitenant).
2. Buscar RT do tenant que tenha `usuario_id == decisor_id` e ainda
   vigente (encerrado_em IS NULL).
3. Buscar RTCompetencia(rt=esse_rt, grandeza=informada, vigente_ate IS
   NULL OR vigente_ate >= hoje).
4. Retornar True se existe; False caso contrario.

Nao levanta excecao — fail-soft (predicate retorna booleano; chamador
decide o que fazer com False).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db.models import Q

from .models import ResponsavelTecnicoTenant, RTCompetencia


def decisor_tem_competencia_para_atividade(
    *,
    decisor_id: UUID,
    atividade: str,
    grandeza: str,
    tenant_id: UUID,
    hoje: date | None = None,
) -> bool:
    """Retorna True se o decisor for RT vigente do tenant com competencia
    declarada na grandeza informada.

    `atividade` aceito para compatibilidade futura (Wave A separa por
    categoria de decisao). No Marco 2 o gate e a existencia da
    competencia — atividade nao filtra.
    """
    del atividade  # reservado pra Wave A
    hoje = hoje or date.today()
    rt = (
        ResponsavelTecnicoTenant.objects.filter(
            tenant_id=tenant_id,
            usuario_id=decisor_id,
            encerrado_em__isnull=True,
        )
        .only("id")
        .first()
    )
    if rt is None:
        return False
    grandeza_norm = grandeza.strip().lower()
    return (
        RTCompetencia.objects.filter(
            tenant_id=tenant_id,
            rt_id=rt.id,
            grandeza=grandeza_norm,
            declarado_em__lte=hoje,
        )
        .filter(Q(vigente_ate__isnull=True) | Q(vigente_ate__gte=hoje))
        .exists()
    )
