"""Query services M4 P4 Fase 6 — funcoes puras de leitura sobre snapshots.

Padrao M3 OS: cada query recebe snapshots ja carregados pelo caller +
parametros de filtragem; retorna dataclass agregada. Performance budget
documentado em tasks.md mas verificavel apenas com adapter Django (Fase 8).

Queries entregues:
- visao_360: agregado consolidado de UMA Calibracao + suas relacoes
- reclamacoes_abertas: ranking por proximidade do prazo
- fila_revisor_conferente: lista de calibracoes aguardando revisao/2a conf
"""
