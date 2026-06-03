"""Use cases do módulo `metrologia/licencas-acreditacoes` (M9 Wave A, Fatia 2).

Camada de aplicação PURA (ADR-0007): Inputs frozen + Repository Protocols. O perfil
regulatório vem SEMPRE server-side (ADR-0067 — nunca payload; defesa L6). A promoção
de perfil A (`promover_perfil_a`) é a única que toca o cache `Tenant.acreditacao_*` —
e SÓ via `aplicar_evento_cgcre` (ADR-0079 / INV-LIC-VIG-SYNC-001).
"""
