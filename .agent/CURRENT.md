# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** Wave A · **Marco 2 (módulo `equipamentos`)** — `/specify` + `/plan` (revisado pelos 2 subagentes) FECHADOS.
**Modo:** AUTÔNOMO; ritual orquestrador OBRIGATÓRIO (memória `feedback_ritual_orquestrador`).

## Marco 2 — estado atual (2026-05-18 noite final)

| Etapa do ritual | Status |
|---|---|
| PRD draft → review 4 subagentes → STABLE v2 | ✅ FECHADO |
| INVs novas (049/050/051 + EQP-LOC-001 + VERSAO-001/002 + ANOM-001/002 + PROV-001) | ✅ FECHADO (9 INVs) |
| ADR-0018 (PWA) + ADR-0019 (resp. agente IA) | ✅ FECHADO (propostas) |
| RAT-EQP-FOTO + matriz retenção + qr-publico-allowlist + controles-compensatorios + transferencia-aceite-presencial | ✅ FECHADO |
| Redis no docker-compose + settings (decisão Roldão) | ✅ FECHADO |
| `/specify` por US (EQP-001..006 + 002b) | ✅ FECHADO (7 planos) |
| `/plan` revisado pelos 2 subagentes (12 reviews) | ✅ FECHADO (3 decisões Roldão: Redis+002b+RecebimentoProvisorio) |
| `/tasks` por US (T-EQP-NNN) | ⏳ PENDENTE |
| `/implement` das 7 US | ⏳ PENDENTE |
| 3 auditores Família 5 — Marco 2 | ⏳ PENDENTE |

## US do Marco 2 (7 US — após fatiar 002 + 002b)

| US | Tema | Invariantes principais |
|---|---|---|
| US-EQP-001 | Cadastrar + QR HMAC + snapshot perfil_tenant | INV-049, INV-051, INV-EQP-LOC-001 |
| US-EQP-002 | Editar com versionamento + motivo enum + A3 RT | INV-025, INV-EQP-VERSAO-001/002 |
| US-EQP-002b | Workflow gestor_qualidade aprovando motivo=outros | INV-EQP-VERSAO-001/002 + ISO 17025 cl. 6.2 |
| US-EQP-003 | Ficha 360° + scan dual-mode + PWA + Redis | INV-051, INV-AUTHZ-001 |
| US-EQP-004 | Transferir intra-tenant com aceite duplo | INV-050, INV-025 |
| US-EQP-005 | Sucatar com notificação | RBC B5 |
| US-EQP-006 | Receber no lab (+ RecebimentoProvisorio) | INV-EQP-ANOM-001/002, INV-EQP-PROV-001, ISO 17025 cl. 7.4 |

## Próximo passo

`/tasks` por US — gerar `tasks/US-EQP-NNN.md` com lista atômica de T-EQP-NNN seguindo padrão Marco 1 clientes.

## Estado do sistema

- Containers `afere-db` + `afere-app` rodando (Redis ainda não subido — ao começar /implement, rebuilde docker-compose).
- Banco `afere` + `test_afere` migrados até última migration (clientes.0013, audit.0007, tenant.0002).
- Hooks 113/113 verdes.

## ADRs novas (propostas — aceitar antes de Marco 2 codar)

- ADR-0018 (PWA + BarcodeDetector) — destrava US-EQP-003.
- ADR-0019 (responsabilidade agente IA) — pré-condição apólice.

## Pareceres dos subagentes (16 total — 4 PRD + 12 US)

`docs/dominios/suporte-plataforma/modulos/equipamentos/revisoes/` — 16 pareceres aplicados, todos `stable`.
