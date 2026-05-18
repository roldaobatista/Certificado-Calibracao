"""Camada de dominio PURA (sem Django).

Cada bounded context vive em src/domain/<contexto>/ com:
- agregado.py     — entidade(s) + metodos puros
- invariantes.py  — assert_inv_NNN(), referencia IDs do REGRAS-INEGOCIAVEIS.md
- eventos.py      — DomainEvents emitidos pelo bounded context
- repository.py   — Protocol (sem implementacao Django)

Implementacao concreta dos Protocols vive em src/infrastructure/repositories/.

Ver ADR-0007.
"""
