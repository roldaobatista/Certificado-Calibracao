---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos Export — Módulo Suporte SaaS

---

## Exports

### Export 1: Histórico de Tickets do Tenant (CSV)

**Propósito:** Tenant solicita relatório de tickets para auditoria interna.
**Formato:** CSV UTF-8.
**Regulado?:** não.
**Campos:** `protocolo`, `categoria`, `prioridade`, `status`, `aberto_em`, `resolvido_em`, `tempo_resolucao_min`, `sla_cumprido` (bool), `csat`, `aberto_por_usuario`.
**Retenção:** alinhada ao ticket (60 dias pós-fechamento default; configurável por plano).

**Exemplo:**
```csv
protocolo,categoria,prioridade,status,aberto_em,resolvido_em,tempo_resolucao_min,sla_cumprido,csat,aberto_por
SUP-2026-000123,bug,P2,resolvido,2026-05-10T09:00:00Z,2026-05-10T11:30:00Z,150,true,5,user@tenant
```

---

### Export 2: Trilha de Acesso Remoto (CSV)

**Propósito:** Auditoria — comprovar que todo acesso teve consentimento + foi logado.
**Formato:** CSV.
**Regulado?:** atende LGPD art. 37 (registro de tratamento).
**Campos:** `sessao_id`, `tenant_id`, `solicitante`, `autorizado_por`, `motivo`, `iniciada_em`, `encerrada_em`, `recursos_acessados[]`.
**Imutabilidade:** `INV-001`.
**Retenção:** 5 anos (compliance LGPD).

---

### Export 3: Relatório de SLA por Plano (XLSX)

**Propósito:** Gestão SaaS — performance por plano comercial.
**Formato:** XLSX com abas (Free, Pro, Enterprise).
**Campos por aba:** mês, tickets recebidos, % SLA cumprido, CSAT médio, tempo médio primeira resposta, tempo médio resolução.

---

### Export 4: Roadmap Público (JSON / RSS)

**Propósito:** Tenants/parceiros consomem programaticamente.
**Formato:** JSON (preferencial) ou RSS para integrações simples.
**Visibilidade:** apenas itens públicos.
**Estrutura JSON:**
```json
{
  "trimestres": [
    {"trimestre": "2026-Q3", "itens": [{"id":"...","titulo":"...","status":"em_construcao","votos":42}]}
  ]
}
```

---

### Export 5: Histórico de Manutenções (CSV)

**Propósito:** Comprovação de janelas comunicadas + cumpridas (insumo a relatórios de SLA contratual).
**Formato:** CSV.
**Campos:** `comunicado_id`, `titulo`, `tipo`, `inicio_agendado`, `fim_agendado`, `inicio_real`, `fim_real`, `status_final`, `tenants_afetados_count`.

---

### Export 6: CSAT por Categoria (XLSX)

**Propósito:** Identificar onde o produto está falhando.
**Campos:** categoria, mês, qtd avaliações, média, nota mínima.

---

### Export 7: Pacote de Resposta LGPD para Usuário SaaS (ZIP)

**Propósito:** Usuário do tenant exerce direito do titular sobre dados de suporte (tickets que ele abriu).
**Formato:** ZIP.
**Conteúdo:** tickets dele + mensagens + anexos + avaliações + sugestões + votos.
**Regulado:** LGPD art. 18.
**Retenção do pedido:** 5 anos.

---

## Exports inter-módulos

- Tickets categoria "bug" → integração com tracker interno (módulo `release-management/`).
- Sugestões aprovadas → itens do roadmap em `release-management/`.
- Sessão de acesso remoto → trilha consolidada em `comum/auditoria/`.

## Versionamento

JSON do roadmap versionado por header `Accept: application/vnd.afere.roadmap+json;v=1`.

## Como evolui

Export novo → adicionar. Mudança regulada → ADR. Descontinuação → `@deprecated`.
