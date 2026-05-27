---
adr: 0061
titulo: Canal do titular + DPO + INV-DPO-001..003 (rota /privacidade + prazo 15 dias + RIPD + retenção)
owner: roldao
revisado-em: 2026-05-27
status: reservada
data: 2026-05-23
reservado-em: 2026-05-23 (Onda 0 plano-v2 — antecipada da Onda 5 por auditoria LGPD)
arquivo-fisico-criado-em: 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A — resolve drift estrutural §11 AGENTS)
ativacao-em: antes 1º cliente final da Balanças Solution ser cadastrado com dado real (interim) / antes 1º tenant externo pago (formal)
bloqueia-fase: 1º dogfooding profundo com dados reais (titulares clientes da Balanças) + 1º tenant externo
depende-de: ADR-0021 (anonimização vs retenção LGPD), ADR-0067 (perfil regulatório do tenant)
---

# ADR-0061 — Canal do titular + DPO + INV-DPO-001..003

> **Status:** **RESERVADA** — esqueleto criado em 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A) pra resolver drift de §11 AGENTS.md. Auditoria L2 (advogado) classificou como CRÍTICO LGPD-002 + LGPD-005. **Promover ANTES de 1º dogfooding com dado real.**
>
> **Não bloqueia desenvolvimento ainda.** Mitigação interim aceita pelo Roldão: canal `dpo@balancassolution.com.br` responde manualmente com SLA 15 dias em planilha, enquanto base de titulares = só clientes da Balanças (~centenas).

## Escopo previsto (a detalhar)

- **Rota `/privacidade`** (página pública sem login) com formulário de solicitação titular cobrindo os 9 direitos LGPD art. 18:
  1. Confirmação de existência do tratamento
  2. Acesso aos dados
  3. Correção de dados incompletos/inexatos
  4. Anonimização, bloqueio ou eliminação
  5. Portabilidade
  6. Eliminação dos dados (sujeito a retenção legal)
  7. Informação sobre uso compartilhado
  8. Revogação do consentimento
  9. Revisão de decisão automatizada

- **Modelo `SolicitacaoTitular`** com `tenant_id` (qual tenant trata), `titular_email`/`titular_cpf_hash`, `direito_invocado`, `recebido_em`, `prazo_resposta` (D+15), `status`, `resposta_dpo`.

- **Watchdog SLA:** alerta D+10 e D+15 (INV-DIR-TIT-002 do REGRAS-INEGOCIÁVEIS) — escalation se DPO não responder.

- **Fan-out síncrono** nos módulos com PII (clientes ✅, equipamentos 🛠, OS 🛠, calibração 🛠, certificados 🛠, app-tecnico, acesso-seguranca) via consumer `Privacidade.SolicitacaoTitular.Recebida`.

- **RIPD (Relatório de Impacto à Proteção de Dados):** documento canônico em `docs/conformidade/comum/ripd.md` que descreve cada tratamento + base legal + retenção + risco + mitigação.

- **Designação formal DPO:** ata declarando DPO (Roldão interino agora; humano externo pré-produção).

- **INV-DPO-001:** rota `/privacidade` sempre acessível (ENABLED em todos os tenants — não pode desabilitar via feature-flag).
- **INV-DPO-002:** solicitação cria entrada em `SolicitacaoTitular` antes de qualquer outra ação (audit trail).
- **INV-DPO-003:** prazo de resposta calculado em dias úteis (15) + watchdog D+10 e D+15.

- **Matriz feature×perfil ADR-0067:**
  - Perfil A/B/C/D: rota `/privacidade` igual em todos (LGPD não diferencia por perfil regulatório).
  - Mas matriz de retenção LGPD vs Receita vs ISO aplica por perfil — perfil A 25a ISO; perfil D 5a Receita.

## Quando promover

**Antes do 1º dogfooding com dado real de cliente final da Balanças** (não os funcionários da Balanças — esses são titulares colaboradores cobertos pelo `acesso-seguranca` Wave A). Mitigação interim já documentada acima.

## Why reservada hoje

Memória `project_sem_contratacoes_externas_ate_producao` — sem cliente externo agora, mitigação manual aceita. Promover a aceito requer:
1. Decisão Roldão de "vamos cadastrar primeiro cliente final real da Balanças no Aferê" OU "vamos abrir pra 1º tenant externo".
2. Endpoint `POST /privacidade/titular/solicitar` implementado (módulo `direitos-titular` — Sprint 6 SAN-PERFIL).
3. RIPD redigido (módulo `direitos-titular` ou `conformidade/comum`).
4. DPO formal designado (Roldão interino OU contratação Wave B/produção).
