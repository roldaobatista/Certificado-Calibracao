# Discovery — Validação ativa

> **Artefato Rodada 0** (Auditor 6 v2 — NOVO). Smoke test + Willingness-to-Pay test + cartas de intenção. Auto-reportado em entrevista MENTE sistematicamente (viés de cortesia). Validação ativa = dinheiro / compromisso real no jogo.

---

## Por que validação ativa

Em entrevistas, 80% dos respondentes dizem "sim, eu compraria" — e 5% efetivamente compram. Diferença = viés de cortesia + auto-engano. Validação ativa força a pessoa a colocar algo no jogo:

- **Smoke test:** dinheiro de marketing num anúncio com call-to-action
- **Fake-door:** landing page com botão "Comprar" que coleta e-mail
- **WTP test:** pergunta de preço SEM dar a opção "qualquer preço serve" (forçar escolha)
- **Carta de intenção:** documento físico assinado prometendo compra se produto X for entregue

---

## Plano

### 1. Smoke test
- **Veículo:** Google Ads ou LinkedIn Ads ou meta Ads
- **Orçamento:** R$ 200–500 pra primeiro teste
- **Targeting:** assistências técnicas BR com mais de 5 funcionários
- **CTA:** "Conheça o Aferê — ERP integrado pra assistência técnica + calibração ISO 17025"
- **Landing:** página simples com mockup + formulário "quero saber mais"
- **Métrica:** taxa de conversão clique → e-mail. Benchmark: >2% é forte.
- **Status:** ⏳ a executar

### 2. Fake-door test (variante mais agressiva)
- Landing com botão "Quero contratar agora" — clica → "estamos em beta, qual seu e-mail pra avisar lançamento?"
- Métrica: cliques no botão (mostra intenção real)

### 3. WTP (Willingness-to-Pay)
- Pergunta nas entrevistas: "Quanto vocês pagariam por isso?" — sem sugerir faixa.
- Variante Van Westendorp (4 perguntas pra triangular):
  - "Em que preço você acha caro DEMAIS pra considerar?"
  - "Em que preço você acha CARO mas ainda compraria?"
  - "Em que preço você acha BARATO?"
  - "Em que preço você acha BARATO DEMAIS — que faria suspeitar da qualidade?"
- Cruza as 4 → faixa ótima de preço.

### 4. Carta de intenção
- Documento físico que cliente assina prometendo:
  - "Se Aferê entregar [features X, Y, Z] até [data], eu (empresa) me comprometo a contratar plano de R$ Y/mês por 6 meses."
- Não tem força jurídica forte mas tem força MORAL alta.
- Meta: **3 cartas assinadas antes da `sintese-final.md` travar MVP**.

### 5. Pré-venda com sinal monetário (variante mais agressiva)
- Cobrar R$ 1 (simbólico) de "reserva" pra entrar na lista do beta.
- Métrica: % das cartas de intenção que viram pagamento de R$ 1.

---

## Resultados (a preencher)

### Smoke test
- Veículo: ...
- Período: ...
- Investimento: R$ ...
- Cliques: ...
- E-mails: ...
- Taxa conversão: ...
- **Conclusão:** ...

### WTP
- Amostra: NN entrevistas com pergunta de pricing
- Caro demais (mediana): R$ ...
- Caro mas compraria: R$ ...
- Barato: R$ ...
- Barato demais (suspeita): R$ ...
- **Faixa ótima sugerida:** R$ ... – R$ .../mês

### Cartas de intenção
- Cartas obtidas: N de meta de 3
- Empresas:
  1. ...
  2. ...
  3. ...

### Pré-venda R$ 1
- N pessoas pagaram R$ 1: ...

---

## Critério de OK pra travar MVP

A `sintese-final.md` SÓ trava MVP-1 quando:
- ✅ Smoke test mostra >2% conversão OU evidência equivalente
- ✅ WTP cruza com pricing de mercado de `precificacao-mercado.md`
- ✅ ≥3 cartas de intenção assinadas
- ✅ (opcional) ≥3 pré-vendas de R$ 1

Sem esses 4 OKs, MVP-1 é especulação cara.

---

## Anti-padrão

❌ Confiar em "achei que era bom em entrevista" sem teste com dinheiro
❌ Pular validação ativa por economia de tempo curto — preço alto pago em meses de produto errado
❌ Modificar smoke test pra "ajudar" conversão (vira marketing de empresa que não existe ainda — distorce sinal)
