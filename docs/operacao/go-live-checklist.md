---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Go-live checklist

> ⏸️ **DORMENTE (2026-05-17):** "go-live" depende de Roldão autorizar deploy a servidor — decisão dele, sem prazo. Até lá, Foundation F-A + Wave A construídas em ambiente local. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** lista binária do que precisa estar verde antes do "go-live". "Go-live" = **dogfooding em produção real da Balanças Solution** (não cliente externo nesta janela — esse foi diferido pra V2; ver [[sem-cliente-externo-na-janela-atual]]). Os blocos abaixo distinguem **gate da janela atual** (MVP-1 dogfooding) vs **gate diferido pra V2** (1º cliente externo).

---

## Bloco A — Conformidade (janela atual = dogfooding)

- [ ] `lgpd-rat.md` atualizado com RAT de cada operação ativa (já existe — revisar)
- [ ] `retencao-matriz.md` aprovada pelo Roldão (já existe — revisar)
- [ ] `seguranca-dados.md` revisada (já existe)
- [ ] Se MVP-1 inclui calibração: `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md` cobrindo cláusulas 7.7, 7.8, 7.10, 7.11, 8.3, 8.4, 8.5, 8.6, 8.7

### Diferido pra V2 (quando 1º cliente externo aparecer)
- DPA (Data Processing Agreement) entre Aferê e tenant externo — modelo `docs/conformidade/comum/dpa-modelo.md` (a criar)
- DPO formal designado (Balanças Solution não exige; cliente externo regulado sim)
- Playbook ANPD 72h testado em mesa (drill simulado)
- Termos de Uso + Política de Privacidade pública (advogado licenciado)
- Política de cookies + aviso de privacidade na landing pública

## Bloco B — Segurança

- [ ] Hooks ativos: block-destructive, secrets-scanner, anti-mascaramento, tenant-id-validator, INV-checker, paths-frontmatter-validator
- [ ] 3 Auditores Família 5 ativos: subagent (camada A) + GitHub Action (camada B)
- [ ] CODEOWNERS protegendo 10 paths sensíveis
- [ ] MFA obrigatório para Dono + Gerente + Financeiro
- [ ] TLS 1.3 only confirmado
- [ ] Backup completo testado em VM provisória (drill cenário (b) executado e RTO < 1h)
- [ ] AWS KMS Multi-Region Key funcionando (failover testado: sa-east-1 → us-east-1)
- [ ] Crypto-shredding por tenant testado (chave destruída → backup ilegível)
- [ ] Smoke test cross-tenant: tenant A não vê dado de B em CI
- [ ] SBOM gerada e revisada

## Bloco C — Infraestrutura (janela atual)

- [ ] VPS Hostinger SP provisionada via Ansible
- [ ] Postgres com RLS ativa + INV-TENANT-001..004 enforced
- [ ] pgBackRest configurado (full semanal + diff diário + WAL contínuo)
- [ ] B2 EU Central com Object Lock ativo
- [ ] DNS gerenciado por API (TTL 5min)
- [ ] Certificado TLS automático (Let's Encrypt + cert-manager)
- [ ] Logs / métricas / traces conectados ao Grafana + Axiom
- [ ] Alertas SEV-0/SEV-1 disparam pra Roldão (WhatsApp/SMS testado)

### Diferido pra V2
- Conta em provedor B (Magalu/Oracle/AWS) ativa pra DR cenário (c) — dogfooding aceita downtime > 4h conscientemente
- Apólice cyber + RC profissional contratada (corretora SUSEP) — dogfooding não exige; cliente externo sim

## Bloco D — Produto / Negócio (janela atual = dogfooding)

- [ ] `docs/prd.md` aprovado pelo Roldão
- [ ] `docs/faseamento-modulos.md` aprovado (Wave A = MVP-1)
- [ ] `discovery/sintese-final.md` STABLE via **caminho B** (dogfooding) — ver §"Critério pra fechar definitiva"
- [ ] Balanças Solution pronta operacionalmente pra usar Aferê como sistema principal (não paralelo)
- [ ] Roldão treinado nos fluxos críticos como usuário final (não como dono)

### Diferido pra V2 (1º cliente externo)
- 3 cartas de intenção assinadas
- R-001 ≤ 9 (atualmente em 12, aceito)
- `discovery/sintese-final.md` STABLE caminho A
- Pricing público publicado em landing
- Trial self-service 30 dias funcionando (cadastro → tenant novo)
- Onboarding documentado pro tenant externo (`externos/onboarding-cliente.md`)
- Suporte L1 (Roldão + bot LiteLLM como fallback humano — LEAP F-18)
- Canal de reclamação formal público

## Bloco E — Operação

- [ ] Runbook completo (`runbook.md` + docs vinculados)
- [ ] DR plan testado em drill (cenário b OU c)
- [ ] Watchdog acionamento-agente configurado
- [ ] Postmortem template pronto pra ser usado
- [ ] Capacity planning revisado (`capacity-planning.md`)
- [ ] Maintenance window declarada (sáb 02-05 BRT)
- [ ] Status page ativa (provisória em GitHub Pages aceito)
- [ ] CHANGELOG.md mantido em formato Keep a Changelog 1.1

## Bloco F — Documentação visível pro tenant (DIFERIDO V2)

Tudo deste bloco entra apenas quando 1º cliente externo aparecer:
- Manual do cliente (`externos/manual-cliente.md`)
- FAQ no portal
- Como pedir exclusão (LGPD art. 18) — exposto na UI pública
- Como reportar bug / incidente — canal público
- Como cancelar contrato (sem fidelidade abusiva)

---

## Estado atual (2026-05-17)

**Janela atual = dogfooding Balanças Solution:**
- Bloco A janela: 🟡 (matriz retenção ✅, ISO 17025 ⏳)
- Bloco B: 🟡 (hooks ✅, auditores ✅, infra ⏳)
- Bloco C janela: ⏳ (nada provisionado)
- Bloco D janela: 🟡 (PRD ✅, faseamento ✅, sintese caminho B em andamento)
- Bloco E: 🟡 (runbook ✅, drill ⏳)

**Pronto pra dogfooding Balanças Solution:** NÃO ainda. Falta Foundation completa (F-A a F-H) + Wave A + infra Hostinger.

**Pronto pra 1º cliente externo (V2):** NÃO. Diferido conscientemente.

---

## Drill semestral

Reler este checklist a cada 6 meses; tudo que estava ✅ ainda está? Re-validar.

---

## Referências

- `docs/prd.md`, `docs/faseamento-modulos.md`
- `docs/operacao/dr-plan.md` — drill obrigatório
- `docs/conformidade/comum/*` — bloco A
- `docs/seguranca/*` — bloco B
