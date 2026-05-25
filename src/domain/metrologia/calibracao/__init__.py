"""Dominio puro do submodulo metrologia/calibracao (Marco 4 P4 Fase 2).

Sem Django, sem PG, sem IO. Apenas regras de negocio + value objects +
predicates puros. Use cases (Fase 5) chamam adapters de infrastructure
para persistir; aqui ficam invariantes que NAO podem regredir entre
camadas.

Estrutura:
    value_objects.py - VOs novos M4 (VersaoMotorCalculo, EscoreZ,
        ZonaILACG8, HashVersionadoV0, IncertezaCombinada).
    hash_versionado.py - Helpers parsing/formatting do formato
        v<NN>$<base64> (ADR-0064 + INV-HMAC-001..005).
    entities.py - Dataclasses frozen mapeando 23 entidades PG.
    predicates.py - Funcoes puras (cmc_cobre, procedimento_vigente_para,
        rt_competencia_cobre).
"""
