"""Domínio puro — Agenda (Wave A, Fatia 1a).

Módulo de calendário gerencial multi-técnico: aloca atividades de OS,
bloqueios e eventos nos slots dos técnicos, validando a jornada UMC
(Lei 13.103) por regime (perfil-AGNÓSTICO).

Composto por:
- ``enums.py``       : enums fechados do domínio (TipoEvento, EstadoEvento, …).
- ``entities.py``    : entidades (EventoAgenda, Recorrencia, …).
- ``value_objects.py``: VOs imutáveis (Janela, ResultadoJornada, …).
- ``transicoes.py``  : máquina de estados (Padrão A).
- ``jornada.py``     : predicate puro ``validar_jornada_umc`` (perfil-agnóstico).
- ``recorrencia.py`` : ``materializar_janela`` — puro, determinístico, idempotente.
- ``portas.py``      : Protocols runtime_checkable (portas de DI).
- ``erros.py``       : hierarquia de erros de domínio.

NÃO importar django.* — camada pura.

ADRs ancorando:
- ADR-0023 (OS com Atividades — atividade_id obrigatório quando tipo=os)
- ADR-0033 (bus idempotência consumer)
- ADR-0067 (perfil regulatório — jornada é PERFIL-AGNÓSTICA)
- ADR-0068 (sucessão/substituição RT)

INVs centrais:
- INV-AG-JORNADA-UMC-001  (Lei 13.103 perfil-agnóstica, 5 regras + espera 1/1)
- INV-AG-REGIME-001        (regime server-side; IA nunca grava override)
- INV-AG-OVERLAP-001       (EXCLUDE GIST tenant+tecnico+tstzrange half-open)
- INV-AG-ATIVIDADE-001     (atividade_id NOT NULL quando tipo=os)
- INV-AG-PERFIL-001        (perfil server-side; RT projetado ao slot)
- INV-AG-RECORRENCIA-001   (materialização idempotente)
- INV-AG-CNH-001           (MOTORISTA_UMC com pendencia_cnh bloqueado)
- INV-AG-AUDIT-WORM-001    (EventoAuditoriaAgenda INSERT-only)
- INV-AG-NOSHOW-AR-001     (no-show cobrável publica para contas-receber)
"""
