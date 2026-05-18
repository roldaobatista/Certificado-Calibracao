# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** Wave A · **Marco 2 (módulo `equipamentos`)** — PRD STABLE v2 + 16 bloqueadores aplicados.
**Modo:** AUTÔNOMO; ritual orquestrador OBRIGATÓRIO (memória `feedback_ritual_orquestrador`).

## Marco 2 — estado atual (2026-05-18 noite final)

| Etapa do ritual | Status |
|---|---|
| PRD draft → review 4 subagentes → STABLE v2 | ✅ FECHADO |
| INVs novas em REGRAS-INEGOCIAVEIS.md (49, 50, 51, EQP-LOC-001) | ✅ FECHADO |
| ADR-0018 (PWA scanner) + ADR-0019 (resp. agente IA) | ✅ FECHADO (propostas) |
| RAT-EQP-FOTO + matriz retenção + qr-publico-allowlist.md | ✅ FECHADO |
| `/specify` por US (EQP-001..006) | ⏳ PENDENTE |
| `/plan` revisado pelos 4 subagentes | ⏳ PENDENTE |
| `/tasks` por US (T-EQP-NNN) | ⏳ PENDENTE |
| `/implement` das 6 US | ⏳ PENDENTE |
| 3 auditores Família 5 — Marco 2 | ⏳ PENDENTE |

## US do Marco 2 (6 — decisão Roldão "completo ISO 17025")

| US | Tema | Invariantes principais |
|---|---|---|
| US-EQP-001 | Cadastrar equipamento + QR HMAC + snapshot perfil_tenant | INV-049, INV-051, INV-EQP-LOC-001 |
| US-EQP-002 | Editar com versionamento + motivo enum + A3 RT em perfil A | INV-025 |
| US-EQP-003 | Ficha 360° + scan QR dual-mode + PWA + portas stub | INV-051, INV-AUTHZ-001 |
| US-EQP-004 | Transferir intra-tenant com aceite duplo + categoria enum | INV-050, INV-025 |
| US-EQP-005 | Sucatar com notificação ao cliente se cert vigente | RBC B5 |
| US-EQP-006 | Receber equipamento no lab (RecebimentoEquipamento + máquina de estados ≥6 fases + foto perfil A) | ISO 17025 cl. 7.4 |

## Próximo passo

Iniciar `/specify` por US — gerar `planos/US-EQP-NNN.md` (1 por US) seguindo padrão do Marco 1 `clientes`. Reusar adapters e estrutura `src/{domain,application,infrastructure}/suporte_plataforma/equipamentos/`.

## Estado do sistema

- Containers `afere-db` + `afere-app` rodando.
- Banco `afere` + `test_afere` migrados até última migration (clientes.0013, audit.0007, tenant.0002).
- Para parar: `docker compose down`.

## ADRs novas (propostas — aceitar antes de Marco 2 codar)

- ADR-0018 (PWA + BarcodeDetector) — destrava US-EQP-003.
- ADR-0019 (responsabilidade agente IA) — pré-condição contratação apólice (não bloqueia codar Marco 2).

## Pareceres dos 4 subagentes (2026-05-18 — base do PRD v2)

`docs/dominios/suporte-plataforma/modulos/equipamentos/revisoes/PRD-{tech-lead,advogado,corretora,rbc}.md` — total 16 BLOQUEADORES + 23 CONCERNs aplicados.
