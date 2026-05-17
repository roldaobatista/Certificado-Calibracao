# Discovery — Síntese final ⭐

> **Artefato Rodada 0** (agente + Roldão). **DESTRAVA TODAS AS OUTRAS RODADAS.** Conclusões da discovery em formato de DECISÃO.

---

## Status: ⏳ A PREENCHER APÓS ONDAS 1+2+3 + VALIDAÇÃO ATIVA

Sem esta síntese fechada, NADA da Rodada 1+ deve começar. Esta é a porta.

---

## Critério de "pronto pra sintetizar"

A síntese só pode ser fechada quando TODOS os 6 critérios valem:

- [ ] Onda 1 completa (3 entrevistas com donos de outras empresas) + síntese cruzada
- [ ] Onda 2 completa (6 entrevistas com operadores)
- [ ] Onda 3 completa (3 entrevistas de validação com protótipo)
- [ ] Saturação documentada (3 entrevistas seguidas sem insight novo)
- [ ] Todos leap-of-faith de `assumption-map.md` validados ou descartados
- [ ] `validacao-ativa.md` mostra ≥3 cartas de intenção assinadas + WTP triangulado

---

## Saídas obrigatórias da síntese

### 1. CLIENTE IDEAL (ICP — Ideal Customer Profile)
**A preencher:**
- Tipo (empresa de assistência técnica? laboratório RBC? híbrido?):
- Tamanho (porte):
- Geografia (BR todo? regional?):
- Tech proficiency:
- Dores agudas que pagaria pra resolver:
- Sinais de "este NÃO é o ICP":

### 2. N MÓDULOS TOTAL
**A preencher:**
- Lista FINAL dos módulos confirmados pela discovery (pode ser 6, 11, 21 ou 50)
- Cada módulo com 1 frase de propósito
- Agrupamento em domínios (Comercial / Operação / Financeiro / Metrologia / Suporte / outros)

### 3. PLANO DE FASEAMENTO
**A preencher:**
- Ordem em que os N módulos entram em produção
- Justificativa de cada posição (dor + diferencial + dependência)
- Estimativa de tempo por fase (com banda de incerteza)
- Critério "pronto pra próxima fase"

> ⚠️ Detalhe vai em `docs/faseamento-modulos.md`. Aqui só o resumo executivo.

### 4. MVP-1 (PRIMEIRO MÓDULO EM PRODUÇÃO)
**A preencher:**
- Qual módulo:
- Razão da escolha (cruzar com `dores-mapeadas.md`, `opportunity-solution-tree.md`):
- Escopo mínimo (top 3 features):
- Non-goals do MVP-1:
- Estimativa de tempo até 1º deploy:
- Cliente piloto: Roldão (founder is customer) + ___ confirmados

### 5. MODELO DE NEGÓCIO
**A preencher:**
- SaaS multi-tenant / on-premise / híbrido?
- Pricing (modelo + faixa, vem de `precificacao-mercado.md`)
- Estimativa de TAM × SAM × SOM
- Canal de aquisição prioritário (inbound? outbound? indicação?)
- Estimativa de CAC × LTV

### 6. STACK CANDIDATE (entra na ADR-0001)
**A preencher:**
- Linguagem principal:
- Framework backend:
- Framework frontend / UI:
- Banco principal:
- Banco/cache auxiliar:
- Modelo de tenancy escolhido (entra na ADR-0002):
- Mobile (entra na ADR-0003):
- CI/CD:
- Provedor fiscal (Focus NFe / NFE.io / próprio):
- Provedor bancário (Pluggy / Belvo / próprio):
- Observabilidade (Grafana Cloud + Axiom já confirmados):

### 7. EQUIPE OPERACIONAL
**A preencher:**
- Roldão (já confirmado): dono não-técnico, 1º cliente, signatário?
- Signatário técnico de calibração (RBC NIT-DICLA-021): ___ (Roldão se habilitado? terceirizar?)
- DPO (LGPD em larga escala): ___ (Roldão? consultor?)
- Contador / consultoria fiscal: ___ (necessário pra NF-e)

### 8. RISCOS RESIDUAIS APÓS DISCOVERY
**A preencher:**
- Quais riscos de `riscos.md` foram MITIGADOS pela discovery?
- Quais permanecem? Plano de mitigação contínua?

---

## Recomendações pra Rodadas 1+

(A preencher — saída direta da síntese)

- Rodada 1 deve começar imediatamente com: [...]
- Próximo módulo (Fase 2) será: [...]
- Reavaliar síntese após 1º deploy do MVP-1

---

## Aprovação

- [ ] Auditor de Produto leu e aprovou
- [ ] Auditor de Segurança identificou riscos não cobertos
- [ ] Roldão leu e aprovou (decisão dele)
- [ ] Atualizou `painel-do-dono.md` com novo status "discovery concluída"
- [ ] Atualizou `documentos-do-projeto.md` com plano de faseamento real

---

## Histórico de revisões

| Data | Mudança | Quem |
|---|---|---|
| 2026-05-16 | Criação do template | Agente |
| | | |
