"""Guardiao de drift dominio <-> model M4 calibracao (GATE-CAL-DOMAIN-MODEL-DRIFT).

Motivacao (2026-05-28): a auditoria 10 lentes pre-Wave A detectou que snapshots
"enxutos" do dominio NAO carregavam campos que o model Django exige NOT NULL —
o que so passava com FakeRepository; persistir no PG real violaria NOT NULL/CHECK
(ex: ComponenteIncertezaSnapshot sem tipo_origem/distribuicao/divisor/formula;
AvaliacaoPeriodicaSubcontratadoSnapshot sem avaliado_por_user_id_hash/
criterios_aplicados_json/parecer_*).

Este guardiao introspecta cada par (model, snapshot) e exige que TODO campo do
model obrigatorio para INSERT (NOT NULL, sem default, nao-auto) tenha um campo
correspondente no snapshot do dominio. Pega a classe do bug original e qualquer
regressao futura (campo NOT NULL novo no model sem campo-irmao no snapshot).

NAO precisa de DB — usa apenas introspeccao de `model._meta.fields` + dataclasses.
"""

from __future__ import annotations

from dataclasses import fields as dataclass_fields

import pytest
from src.domain.metrologia.calibracao.entities import (
    AvaliacaoPeriodicaSubcontratadoSnapshot,
    ComponenteIncertezaSnapshot,
    OrcamentoIncertezaSnapshot,
)
from src.infrastructure.calibracao.models import (
    AvaliacaoPeriodicaSubcontratado,
    ComponenteIncerteza,
    OrcamentoIncerteza,
)

# Pares (model_django, snapshot_dominio) que devem permanecer reconciliados.
PARES = [
    (ComponenteIncerteza, ComponenteIncertezaSnapshot),
    (OrcamentoIncerteza, OrcamentoIncertezaSnapshot),
    (AvaliacaoPeriodicaSubcontratado, AvaliacaoPeriodicaSubcontratadoSnapshot),
]


def _campos_obrigatorios_para_insert(model) -> list:
    """Campos do model exigidos no INSERT: NOT NULL, sem default, nao-auto.

    - pk auto / auto_now / auto_now_add: preenchidos pelo PG/Django — nao exigem
      campo no snapshot.
    - has_default(): tem valor implicito — opcional no snapshot.
    - null=True: aceita ausencia.
    """
    obrigatorios = []
    for f in model._meta.fields:
        if f.primary_key:
            continue
        if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
            continue
        if f.has_default():
            continue
        if f.null:
            continue
        obrigatorios.append(f)
    return obrigatorios


@pytest.mark.parametrize("model, snapshot", PARES, ids=lambda x: getattr(x, "__name__", str(x)))
def test_snapshot_cobre_campos_obrigatorios_do_model(model, snapshot) -> None:
    """Todo campo NOT NULL-sem-default do model tem campo-irmao no snapshot."""
    nomes_snapshot = {f.name for f in dataclass_fields(snapshot)}
    faltando = []
    for f in _campos_obrigatorios_para_insert(model):
        # FK: snapshot pode usar attname (`tenant_id`) ou o name (`tenant`).
        candidatos = {f.attname, f.name}
        if not (candidatos & nomes_snapshot):
            faltando.append(f.attname)
    assert not faltando, (
        f"DRIFT dominio<->model em {model.__name__}: campos NOT NULL sem "
        f"correspondente em {snapshot.__name__}: {faltando}. "
        f"Persistir esse snapshot no PG real violaria NOT NULL — "
        f"adicione os campos ao snapshot (GATE-CAL-DOMAIN-MODEL-DRIFT)."
    )
