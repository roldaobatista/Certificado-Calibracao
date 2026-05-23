---
owner: roldao
revisado-em: 2026-05-22
proximo-review: 2026-08-22
status: draft
diataxis: reference
audiencia: agente
fase: Foundation F-A — Saneamento
tipo: tarefas-saneamento
relacionados:
  - docs/faseamento/F-A/spec.md
  - docs/faseamento/F-A/auditoria-familia5.md
  - docs/faseamento/F-A/debitos-tecnicos.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/isolamento-multi-tenant.md
  - docs/seguranca/ntp-fonte-confiavel.md
  - docs/seguranca/ciclo-chave-pii.md
  - docs/comum/eventos/acesso-dados-cliente-registrado.md
  - REGRAS-INEGOCIAVEIS.md
---

# Foundation F-A — tarefas de saneamento (Wave A)

> **Para que serve:** consolida em forma executável os achados ALTOS e MÉDIOS levantados pelo Auditor 1 (Família 5) na revisão da Foundation F-A (Onda 2 — 2026-05-22). F-A está **FECHADA** (10/10 PASS ZERO C/A/M). As tarefas listadas aqui **não são regressão**: são débitos que precisam estar resolvidos **antes do 1º tenant externo pago** e que ficam rastreados como gates Wave A (`GATE-FA-N`).
>
> **Origem dos IDs:** auditoria Onda 2 (Auditor 1 — Resolvedor 2/10 do plano "consertar 147 achados").
>
> **Como ler:** cada T-FA-S-NN tem critério de aceitação **binário** (algo está em produção real ou não está). Sem "aceitável", sem "razoável". Onde o critério depender de evidência externa (Backblaze conectado, ANPD reconhecida), o critério explicita.

---

## Tabela canônica

| ID | Origem | Severidade | Título | Critério de aceitação binário | Bloqueia |
|----|--------|-----------|--------|------------------------------|----------|
| T-FA-S-01 | F-A-A1 | ALTO | Export operacional para B2/WORM (GATE-1) | 1ª evidência de export bem-sucedido para bucket Backblaze B2 real do Roldão (não mock, não localstack), com `Object Lock` ativo + `retention period ≥ 5 anos`, validado por download + checksum em ambiente staging. Evidência: artefato `reports/gate-1/2026-MM-DD-export-evidence.txt` (linha de log do worker + hash do objeto + resposta da API B2). | 1º tenant externo pago |
| T-FA-S-02 | F-A-A2 | ALTO | NTP wrapper + fallback no audit (GATE-3) | Trocar todas as ocorrências de `datetime.now()` / `now()` em `src/infrastructure/audit/services.py` (e helpers correlatos) por wrapper `agora_ntp_confiavel()` (a criar em `src/infrastructure/seguranca/clock_ntp.py`) que: (1) consulta servidor NTP autoritativo (`pool.ntp.org` + fallback `a.ntp.br`); (2) tolera deriva ≤ 250ms vs clock local; (3) cai em `time.time()` local **registrando alerta P2 em `audit_trail.eventos` action=`clock.fallback_local`** quando NTP indisponível. PRD em `docs/seguranca/ntp-fonte-confiavel.md`. Teste de regressão obrigatório: simular indisponibilidade NTP — wrapper retorna timestamp local + alerta. | 1º tenant externo pago |
| T-FA-S-03 | F-A-A3 | ALTO | Ciclo de chave PII (GATE-4) | Criar `docs/seguranca/ciclo-chave-pii.md` com (a) calendário anual de rotação (janeiro de cada ano); (b) procedimento operacional de rotação (4 passos: gerar nova chave → re-hash novos registros → manter chave antiga em `PII_HASH_KEYS_RETIRED` → descartar só após crypto-shredding de 100% dos registros gerados sob ela); (c) tabela `PII_HASH_KEYS_RETIRED` (schema + migration de criação prevista). Acordo com matriz de retenção. | 1º tenant externo pago + 1ª auditoria ANPD |
| T-FA-S-04 | F-A-M1 | MÉDIO | Evento `AcessoDadosCliente.Registrado` no catálogo | Schema canônico em `docs/comum/eventos/acesso-dados-cliente-registrado.md` v1 com payload, headers obrigatórios, consumers conhecidos (`job_contagem_diaria_acesso_pii`, `alerta_supressao_acesso_anomalo`). Consumer `job_contagem_diaria_acesso_pii` declarado no `automacoes-catalogo.md` (responsabilidade da Onda 1 — esta tarefa apenas referencia). | Wave A operacional |
| T-FA-S-05 | F-A-M2 | MÉDIO | Glossário PT-EN (referência ADR-0037) | **Não criar glossário nesta onda** — referência cruzada para ADR-0037 que será criado pela Onda 1. Linha registrada em `debitos-tecnicos.md` para garantir que ADR-0037 cubra o vocabulário da F-A (tenant_id, audit_trail, hash chain, RLS, KMS MRK, crypto-shredding). | Documentação completa |
| T-FA-S-06 | F-A-M3 | MÉDIO | `TenantLifecycleEstado` enum | Adicionar enum em `src/domain/shared/value_objects.py` com 7 estados (PROVISIONANDO, ATIVO, SUSPENSO_INADIMPLENCIA, READONLY, BLOQUEADO, CANCELANDO, EXTINTO) + mapa de transições válidas (frozenset). Implementação está **nesta onda** (escopo do Resolvedor 2). Teste em `tests/test_onda2_vos_novos.py`. | Foundation pronta pra Wave A `tenant-lifecycle` |
| T-FA-S-07 | F-A-M4 | MÉDIO | Mapa Zona A/B/C (ADR-0021) dos campos F-A | Adicionar §5 em `docs/conformidade/comum/isolamento-multi-tenant.md` com tabela campo → Zona (A/B/C) cobrindo: `Tenant.id`, `Tenant.slug`, `usuario_id` (em audit), `ip_hash`, `Auditoria.payload`, `AcessoDadosCliente.usuario_id`, `AcessoDadosCliente.recurso`, `AuthorizationDecision.escopo_avaliado`. **Esta tarefa entrega o mapa nesta onda.** | Wave A — qualquer módulo que adicione campo com PII |
| T-FA-S-08 | F-A-M5 | MÉDIO | `event_helpers._obter_correlation_id` — except específico | Trocar `except Exception` (linha ~227) por `except (DatabaseError, OperationalError) as exc:` com `logger.warning("correlation_id indisponível: %s", exc)`. Teste de regressão obrigatório em `tests/test_audit_event_helpers_t_cli_105.py` (ou novo `tests/test_onda2_fa_m5_except_correlation.py`) que provoque `OperationalError` simulado e verifique que o warning é emitido. **Entrega nesta onda.** | Foundation — correção causa-raiz |

---

## Estado das tarefas (snapshot Onda 2 — 2026-05-22)

| ID | Estado | Observação |
|----|--------|-----------|
| T-FA-S-01 | aberto / aguarda B2 do Roldão | Pré-requisito: Roldão habilitar conta Backblaze + Object Lock. |
| T-FA-S-02 | aberto / pendente Wave A | PRD `docs/seguranca/ntp-fonte-confiavel.md` criado nesta onda. Implementação fica para Wave A. |
| T-FA-S-03 | aberto / doc criado | `docs/seguranca/ciclo-chave-pii.md` criado nesta onda; primeira rotação operacional acontece em janeiro do ano-calendário do 1º tenant pago. |
| T-FA-S-04 | aberto / schema criado | `docs/comum/eventos/acesso-dados-cliente-registrado.md` criado nesta onda; declaração no catálogo cabe à Onda 1. |
| T-FA-S-05 | rastreado em débitos | Não toca nesta onda. |
| T-FA-S-06 | **FEITO nesta onda** | Enum + transições válidas + teste. |
| T-FA-S-07 | **FEITO nesta onda** | §5 adicionada em `isolamento-multi-tenant.md`. |
| T-FA-S-08 | **FEITO nesta onda** | except específico + teste de regressão (a escrever junto). |

---

## Critério de fechamento das tarefas

- Cada `T-FA-S-NN` só vira `feito` com (a) artefato físico no repositório (código, doc, teste) **e** (b) evidência executável (teste verde, hook verde, log de export real). Suposição não fecha tarefa (memória `feedback_resolver_nao_documentar`).
- T-FA-S-01..03 dependem de mundo externo (B2 ativo, NTP confiável, rotação anual) → ficam abertas mesmo com PRDs prontos.
- T-FA-S-04 fica metade-feita nesta onda (schema). Onda 1 fecha (consumer no catálogo).
- T-FA-S-06..08 fecham 100% nesta onda.

---

## Referências

- `docs/faseamento/F-A/spec.md` — spec forward F-A
- `docs/faseamento/F-A/auditoria-familia5.md` — auditoria que originou os ALTOs/MÉDIOs
- `docs/faseamento/F-A/debitos-tecnicos.md` — BAIXOs rastreados (irmão deste arquivo)
- `REGRAS-INEGOCIAVEIS.md` — INV-FA-001..003 (a criar abaixo se aplicável)
