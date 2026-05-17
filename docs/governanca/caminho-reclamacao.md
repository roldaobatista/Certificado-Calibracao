---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Caminho de reclamação

> **Pra quê:** sem caminho formal, reclamação some no WhatsApp. Cliente externo de SaaS regulado exige canal documentado.
>
> **Estado:** janela atual = dogfooding Balanças Solution; reclamação interna direta com Roldão. Canal externo ativa quando 1º cliente externo aparecer (V2).

---

## 1. Canais (quando ativados)

| Canal | Quem usa | SLA primeira resposta |
|-------|----------|------------------------|
| **E-mail** `reclamacao@<dominio>.com.br` | Cliente externo, parceiro, regulador | 1 dia útil |
| **WhatsApp Business** | Cliente externo (preferência) | 4h em horário comercial |
| **Portal "Fale com a gente"** dentro do app | Tenant logado | 1 dia útil |
| **LinkedIn / Reclame Aqui** | Reclamação pública | 1 dia útil + tratar com cuidado (visibilidade) |
| **ANPD / Procon / órgão regulador** | Caso jurídico | Imediato — passa pra `advogado-saas-regulado` |

---

## 2. Triagem (Aferê)

Reclamação chega → classificada em:

| Tipo | Quem trata | Prazo resolução |
|------|------------|------------------|
| Bug funcional | Subagent + Roldão | Próximo release |
| Bug de segurança | Auditor Segurança + Roldão | Imediato (SEV) |
| Vazamento confirmado | RACI-incidente | 72h (ANPD) |
| Solicitação LGPD art. 18 | Operador (Aferê) → controlador (tenant) | 24h pra tenant; tenant tem 15 dias úteis |
| Pedido de feature | Backlog | Avaliação em status-semanal |
| Insatisfação geral | Roldão | 1 dia útil |
| Spam / abuse | Auto-classificar + bloquear remetente | imediato |

---

## 3. Registro

Toda reclamação vira linha em `governanca/reclamacoes/YYYY-MM-DD-<resumo>.md` (estrutura criada quando 1ª reclamação aparece) com:
- Data + canal + remetente
- Conteúdo (redigido pra remover PII se for arquivar pública)
- Classificação
- Ação tomada
- Tempo até resolução
- Lições aprendidas

Tabela agregada mensal em `status-semanal.md`.

---

## 4. Reabertura

Reclamação resolvida pode ser reaberta se reclamante discorda. Auditor de Produto avalia se ação foi adequada.

---

## 5. Reclamação pública (mídia social, ReclameAqui)

Procedimento:
1. **Identificar autenticidade** (e-mail do cadastro bate?)
2. **Responder publicamente em PT-BR formal** — pedir desculpa se procede, pedir contato privado pra resolver
3. **Levar conversa pra canal privado**
4. **Resolver no canal privado**
5. **Atualizar resposta pública** depois ("resolvido — obrigado pelo feedback")
6. **Postmortem se tiver lição** pra Aferê

Templates em `externos/comunicado-reclamacao.md` (a criar V2).

---

## 6. Casos sensíveis

- **Acusação de vazamento de dados** → para canal público imediato; trata só em canal privado. Acionar `advogado-saas-regulado` + RACI-incidente
- **Acusação de fraude/golpe** → idem
- **Cliente ameaça ação judicial** → para `advogado-saas-regulado`; nada em público
- **Cliente de alto valor furioso** → Roldão atende diretamente (mesmo fora de horário)

---

## 7. Métricas

- Total reclamações/mês (alvo: tendência ↓)
- Tempo médio até primeira resposta
- Tempo médio até resolução
- Taxa de reabertura
- % reclamações que viraram bug confirmado vs misunderstanding

Reportado em `status-semanal.md` mensalmente.

---

## 8. Pendências

- [ ] Criar e-mail `reclamacao@<dominio>` (V2, quando dominio existir)
- [ ] Portal "Fale com a gente" no app (V2)
- [ ] Templates de resposta padrão (V2)
- [ ] Pasta `governanca/reclamacoes/` (criar quando 1ª aparecer)

---

## 9. Referências

- `RACI-incidente-ai.md`
- `lgpd-rat.md` §4 (direitos do titular)
- `status-semanal.md`
- `limites-autonomia.md` (casos-limite onde Roldão decide)
