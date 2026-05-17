# Tutorial — como ler o status semanal

> Tutorial Diátaxis. Audiência: Roldão na primeira vez recebendo `governanca/status-semanal.md`.

---

## O que você vai aprender

1. Como o status semanal é gerado
2. Como ler cada seção
3. Como agir em cima das prioridades destacadas

---

## De onde vem o status semanal

`docs/governanca/status-semanal.md` é **auto-gerado pelos agentes** toda segunda-feira (ou frequência a definir). Contém:

1. O que entregamos na semana passada
2. O que travou e por quê
3. O que decidimos sem te consultar (com link pra trilha)
4. **O que precisa de você essa semana** (escolha forçada, no topo)

---

## Como ler cada seção

### 1. "Essa semana precisa de você por X" (topo)

**Esta é a única seção que exige sua ação.** Lista em ordem de urgência:
- 🚨 Decisões irreversíveis (Caso 1–5 de `limites-autonomia.md`)
- 📋 Aprovação de spec/PRD
- 💰 Aprovação de gasto

**Você lê e responde em PT no terminal.** Pode demorar até 1 dia útil; bloqueio cresce depois.

### 2. "Entregamos na semana passada"

Lista de US/features completas. Cada linha cita ID rastreável.

Exemplo:
- ✅ `US-CRM-003`: cliente pode segmentar contatos por tag (3 dias)
- ✅ `US-CALIB-001`: emissão básica de certificado RBC (5 dias)

**Você lê** pra confirmar que entregou o que você pediu. Se NÃO foi o que pediu → reportar no `caminho-reclamacao.md`.

### 3. "Travou"

Bloqueios técnicos ou aguardando você.

Exemplo:
- 🟡 `US-FIN-002`: emissão NF-e bloqueada — aguardando você escolher provedor (Focus NFe vs NFE.io). Custo R$ 150/mês ou R$ 99/mês.
- 🟡 `US-OS-005`: aguardando decisão de mobile (PWA vs React Native). Bloqueia 3 outras US.

**Você decide** OU autoriza agente a decidir baseado em critério dado.

### 4. "Decidimos sem te consultar"

Decisões autônomas dentro dos `limites-autonomia.md`. Lista resumida; link pra `auditoria-decisoes-autonomas.md` pra detalhe.

Exemplo:
- 🤖 Adotamos PostgreSQL 16 (ADR-0001) — confirmado pela auditoria como melhor pra multi-tenant + RBC.
- 🤖 Mudamos timeout default de 30s pra 60s no Pluggy — rate limit atingido.

**Você lê pra estar informado.** NÃO precisa agir, mas pode discordar — discordância vira ADR de reversão.

### 5. Métricas (rodapé)

Saúde da operação:
- Tokens consumidos/semana
- Taxa de retrabalho
- Cobertura de teste
- Veto dos auditores (PASS/CONCERNS/FAIL)
- Tempo médio de entrega de US

---

## Frequência ideal de leitura

**Segunda de manhã, 5 minutos.** Não precisa de mais.

Se aparecer 🚨 vermelho → responde no mesmo dia.

Se não aparecer 🚨 → você não precisa fazer nada.

---

## O que NÃO está no status semanal

- Detalhe técnico de implementação (vê em `CHANGELOG.md` se quiser)
- Discussão de discovery (vê em `discovery/` durante a Rodada 0)
- Resposta a reclamação de cliente (vê em `caminho-reclamacao.md`)

---

## Próximo tutorial

`aprovar-mudanca-irreversivel.md` — como funciona o pop-up de aprovação CODEOWNERS.
