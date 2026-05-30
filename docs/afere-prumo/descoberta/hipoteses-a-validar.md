---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 11/17
proximo: docs/descoberta/metricas-chave.md
idioma: pt-BR
limite-linhas: 150
proposito: hipóteses do produto/negócio com critério objetivo de validação.
---

<!--
template: hipoteses-a-validar.md
destino: docs/descoberta/hipoteses-a-validar.md
uso: cada hipótese com critério VERIFICÁVEL de validação. Recomendado (🟡).
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤150 linhas.
-->

# Hipóteses a validar — Aferê Prumo

> Cada hipótese é uma APOSTA. Se errar, muda o produto. Critério de validação tem que ser MENSURÁVEL, com prazo e responsável.

## Formato

```
H-NNN: <hipótese — afirmação testável>
- categoria: problema | solução | mercado | crescimento | pricing
- risco: alto | médio | baixo
- como validar: <experimento concreto>
- critério (mensurável): <número, %, prazo>
- prazo: 2026-05-28
- responsável: <nome>
- status: pendente | em validação | confirmada | refutada
- resultado (após validação): <dado coletado + decisão tomada>
```

## Hipóteses ativas

### H-001: O atendimento + orçamento consome tempo suficiente para justificar a IA como Fase 1
- **Categoria**: problema
- **Risco**: 🔴 alto — define qual frente vira a primeira entrega
- **Como validar**: medir por 2 semanas quanto do tempo do escritório (2 pessoas) vai em responder e montar orçamento.
- **Critério (mensurável)**: dos ~50 atendimentos/semana, medir o tempo médio gasto SÓ em responder/orçar (≠ tempo de execução do serviço, que é 2h–2 dias). Confirmar se soma horas relevantes das 2 pessoas do escritório.
- **Dado confirmado (EE-AUTO-002/003)**: ~50 atendimentos/semana, **~30 são orçamento**; escritório = 2 pessoas.
- **Prazo**: tempo médio por orçamento valida no piloto.
- **Responsável**: Roldão (com o escritório)
- **Status**: ✅ **confirmada** (volume alto e concentrado em orçamento justifica a Onda 1). Só o tempo médio por item fica para o piloto medir.
- **Resultado**: 30 orçamentos/semana manuais nas 2 pessoas do escritório → forte caso para automação assistida de orçamento.

### H-002: Prazos de calibração são perdidos hoje e isso custa contrato/receita recorrente
- **Categoria**: problema
- **Risco**: 🔴 alto — é a dor com maior valor financeiro potencial
- **Como validar**: confirmar com o dono o nível de controle atual de prazos.
- **Critério (mensurável)**: % de prazos controlados/avisados hoje.
- **Responsável**: Roldão
- **Status**: ✅ **confirmada (pior que a hipótese)** — o dono **não controla nenhum prazo → 0% controlado, 100% à mercê do cliente lembrar** (EE-AUTO-003).
- **Resultado**: a Onda de prazos/Metrologia passa a ter **valor financeiro máximo** (sai de 0% de controle); forte candidata a ser priorizada logo após a Onda 1. Quantificar o R$/ano dessa receita recorrente é o próximo número a levantar (não bloqueia arquitetura).

### H-003: Clientes aceitam (e preferem) ser atendidos por IA no WhatsApp
- **Categoria**: solução
- **Risco**: 🟠 médio-alto — adoção do canal pelo cliente externo
- **Como validar**: conversar com ≥5 clientes reais sobre atendimento por WhatsApp com IA + medir taxa de resposta num piloto.
- **Critério (mensurável)**: ≥4 de 5 clientes acham bom desde que possam falar com humano quando quiserem; piloto com ≥70% de conversas resolvidas sem reclamação; **aceitação do atendimento por áudio** (cliente fala, IA entende e responde) com meta **≥70%** (**decisão do dono, 2026-05-29** — espelha o ≥70% de H-001/H-011).
- **Prazo**: **2 semanas após o início do piloto** (conversas com ≥5 clientes antes do piloto).
- **Responsável**: Roldão
- **Status**: pendente
- **Resultado**: —

### H-004: A equipe interna adota a ferramenta (não volta pra planilha/papel)
- **Categoria**: solução
- **Risco**: 🔴 alto — é a objeção nº 1 do comprador (P-C-001)
- **Como validar**: piloto da Fase 1 com a equipe por 30 dias, medindo uso real.
- **Critério (mensurável)**: ≥80% dos orçamentos/OS passando pela ferramenta ao fim de 30 dias (não por fora).
- **Prazo**: após Fase 1
- **Responsável**: Roldão
- **Status**: pendente
- **Resultado**: —

### H-005: A IA monta orçamento confiável a partir da base de preços/serviços
- **Categoria**: solução
- **Risco**: 🟠 médio — risco de orçamento errado dado ao cliente
- **Como validar**: rodar a IA em modo "rascunho para revisão humana" e comparar com orçamento manual em ≥30 casos.
- **Critério (mensurável)**: ≥90% dos rascunhos aprovados pela equipe com ajuste mínimo; nenhum erro de preço enviado direto ao cliente sem revisão.
- **Prazo**: durante Fase 1
- **Responsável**: equipe de atendimento
- **Status**: pendente
- **Resultado**: —

### Novas hipóteses (da análise de concorrentes, 2026-05-28) — formato compacto

> Risco/critério resumidos; expandir para o formato completo quando entrarem em validação.

- **H-006** (solução, 🔴): existe um critério numérico de **aprovação-sem-edição (≥X% por Y semanas, por categoria)** que permite subir um TIPO de resposta do Nível 1 para auto-envio de classes seguras (FAQ pura/horário), mantendo orçamento/cobrança/certificado **sempre travados**. *Validar X e quais categorias no piloto.*
- **H-007** (solução, 🔴): o modelo 100%-humano-no-loop **não vira o novo gargalo** no volume real (50/sem, ~30 orçamentos). *Validar ergonomia da Inbox (tempo×volume) + delegação/lote/reatribuição para as 2 pessoas do escritório quando o Roldão está em campo.* **Critério-gate (proposta minha, refinar no piloto):** uma pessoa **limpa a fila de um dia (~30 itens) em <20 min** (≈40s/item, alinhado à métrica de Inbox em `metricas-chave.md §3`); **reatribuição/lote** funciona quando o dono está em campo; nenhum item fica **>4h** sem ser tocado. Ataca a dor central (dono-gargalo). Prazo: piloto. Responsável: Roldão.
- **H-008** (solução, 🟠): um banco de **50-100 casos de teste** mede, FORA de produção, se a IA escolhe a ação certa e escala quando deve. *Critério numérico **APROVADO pelo dono (2026-05-29)**: **≥85% de acerto na classificação da intenção; ≥80% de precisão no que foi escalado; 0% de erro crítico** (caso de valor alto ou cliente irritado NÃO escalado) numa amostra de 30; resposta < 2s. **Pré-requisito do piloto** — se falhar, não fala com cliente (reduz R-003/R-008/R-016).* Prazo: antes do piloto. Responsável: Roldão. **Status: critério fechado.**
- **H-009** (solução, 🔴): o técnico (P-002, fluência média-baixa) preenche OS + 3 fotos + assinatura **offline** e sincroniza **sem ajuda**. **Critério-gate (proposta minha, refinar no piloto):** conclui a OS em **< 5 min**, com **< 10% de OS incompletas** (campos críticos faltando) e **sincroniza sozinho** ao voltar ao sinal, sem reabrir o caso. *Se falhar, a equipe volta pro papel (R-002).* Prazo: piloto da onda de campo. Responsável: Roldão (com 1 técnico).
- **H-010** (problema, 🟠): há **volume repetível** suficiente no atendimento para a IA economizar tempo (vs cada conversa ser única). *Plano de coleta: amostra de **200 atendimentos** do histórico (incl. os áudios já transcritos); critério: **≥50% dos assuntos repetíveis**. De quebra produz a taxonomia de intenções do roteador e o tempo médio real de H-001.* Prazo: antes/início do piloto. Responsável: Roldão.
- **H-011** (refina H-003, 🟡): **citar a fonte** na resposta + escape fácil para humano **aumenta a aceitação** do cliente externo. *Validar no piloto.*
- **H-012** (solução, 🟠): a **extração de documento com conferência humana por confiança** (certificados antigos, OS em papel, comprovantes) resolve a carga inicial de dados da Onda 0 a custo aceitável. *Critério numérico (sugerido): **≥95% dos campos críticos extraídos corretos em ≥70% dos documentos; no máximo 30% cai para revisão humana**; custo por documento aceitável. Se **<60% carrega automático**, a hipótese falha e a carga inicial precisa ser redesenhada.* Prazo: Onda 0 (pré-piloto). Responsável: Roldão.

### Hipóteses da virada de escopo (produto vendido por assinatura, 2026-05-28)

- **H-013** (pricing/mercado, 🔴): os **assinantes do Aferê estão dispostos a pagar** pelo add-on de IA na faixa por perfil proposta (D-PROD-011), e o preço cobre o custo de IA por tenant com margem. *Validar com early adopters do Aferê + medir custo real de IA por tenant no piloto. É a aposta comercial central.*
- **H-014** (solução, 🟠): os **defaults por perfil A/B/C/D + configuração** atendem portes muito diferentes (de 1 pessoa a empresa com vários técnicos) **sem ficar pobre pro grande nem complexo pro pequeno**. *Validar com ≥1 cliente de cada porte antes de abrir comercialmente (R-015).* **Critério por perfil (proposta minha, refinar no piloto):** cada porte conclui o fluxo principal (atender → orçar → aprovar) **só com os agentes/parâmetros da sua faixa** — o pequeno não esbarra em função que não tem, o grande não fica limitado — **sem precisar de ajuda técnica pra configurar** e **sem reclamar de excesso de telas/opções**. **Quando testar:** perfil **B** (Balanças Solution) já no piloto; **A/C/D** em ≥1 cliente cada **antes** da abertura comercial. Responsável: Roldão.
- **H-015** (mercado, 🟠): o **dogfooding na Balanças Solution** gera um **case convincente** que destrava a venda para os demais assinantes. *Validar: depois do piloto, ≥X assinantes do Aferê ligam o add-on ao ver o resultado.*

### Hipóteses abertas pela auditoria de gaps (2026-05-29)

- **H-016** (problema, 🟠): a **equipe atual** absorve o volume de ~30 orçamentos/semana com a IA assistindo. **Confirmado pelo dono (2026-05-29): 2 pessoas no escritório** fazem atendimento/orçamento + **time de campo** (técnicos). *Resta validar no piloto se as 2 pessoas, com a IA assistindo, dão conta sem virar gargalo (liga a H-007).* Responsável: Roldão. **Status: confirmada (composição) / validar capacidade no piloto.**
- **H-017** (pricing/produto, 🟡): manter a IA **conservadora no desconto (≤3%, teto fixado pelo dono em 2026-05-29)** e escalar o resto ao dono **não custa vendas** de forma relevante. *Validar no piloto: medir quantos negócios escalados por desconto fecham e o tempo de resposta. Dados Auvo mostram 16,5% dos itens com desconto, média 26% (decisão humana). Liga a R-021 e D-PROD-012.* Prazo: piloto. Responsável: Roldão.
- **H-018** (solução/financeiro, 🔴): o **custo de IA por cliente por perfil** (LLM + WhatsApp + transcrição + infra) cabe na mensalidade da faixa com margem ≥ alvo (≥40%). *Validar: estimativa inicial já feita (`estimativa-custo-viabilidade.md`); medir tokens/mensagens/minutos REAIS no piloto → R$/atendimento → extrapolar por perfil. Liga a H-013, R-012, R-019, G-005.* **Status: em validação** (custo fixo base = **~R$ 5 mil/mês**, dono 2026-05-29 → equilíbrio **~13 clientes**; falta só medir tokens/minutos reais no piloto). **Prazo: antes de fechar preço (meta: durante o piloto).** Responsável: Roldão. **Mitiga: R-012, R-019.**

## Hipóteses confirmadas (histórico)

| ID | Hipótese | Validada em | Como | Decisão |
|---|---|---|---|---|
| H-X | <...> | 2026-05-28 | <experimento> | <feature aprovada/escopo mantido> |

## Hipóteses refutadas (histórico — IMPORTANTE)

> Erros são aprendizado. Não apagar — mover pra cá com motivo.

| ID | Hipótese | Refutada em | Por quê | Decisão (mudança de rumo) |
|---|---|---|---|---|
| H-Y | <...> | 2026-05-28 | <dado coletado> | <feature removida / pivot / etc.> |

## Critério para promover de `draft` para `stable`

- [ ] ≥3 hipóteses ativas, sendo ≥1 de risco 🔴 alto.
- [ ] Cada hipótese tem critério numérico (não "validar com o time").
- [ ] Cada hipótese tem responsável + prazo.
- [ ] Cruzar hipóteses arriscadas com `business-model-canvas.md` (cada bloco do BMC com risco alto vira H-NNN aqui).
