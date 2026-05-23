"""Dominio puro - operacao (Wave A Marco 3).

Modulos:
- `os/`: Ordens de Servico com N AtividadeDaOS (ADR-0023).

NAO importar django.*. Aqui moram apenas contratos (Protocol),
entidades imutaveis (dataclass frozen=True) e regras de dominio
(transicoes de estado-maquina, validacao de INVs). Implementacao
concreta (adapters Django) vive em `src/infrastructure/operacao/`.
"""
