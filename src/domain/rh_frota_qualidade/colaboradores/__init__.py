"""Módulo `colaboradores` — cadastro-base de quem trabalha pro tenant.

Domínio puro: sem Django, sem banco, sem I/O.
Pré-requisito DURO de 6 módulos a jusante (agenda, app-tecnico, treinamentos,
SST, frota, comissoes) que referenciam colaborador por UUID opaco.

Refs: spec §1/§4; D-COL-1..14; TL-COL-01..15; ADV-COL-01..08.
"""
