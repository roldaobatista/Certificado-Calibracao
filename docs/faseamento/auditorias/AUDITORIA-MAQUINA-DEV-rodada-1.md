---
owner: roldao
revisado_em: 2026-05-29
proximo_review: 2026-06-29
status: draft
diataxis: explanation
audiencia: roldao+agente
relacionados:
  - docs/governanca/ritual-orquestrador.md
  - docs/governanca/debitos-ritual.md
  - docs/governanca/catalogo-auditores.md
  - .specify/memory/constitution.md
  - AGENTS.md
  - CLAUDE.md
  - REGRAS-INEGOCIAVEIS.md
---

# Auditoria da MÁQUINA de desenvolvimento — rodada 1 (2026-05-29)

> **Pergunta do Roldão:** "Por que o desenvolvimento demora tanto? Quero mais rápido **sem** perder a qualidade/segurança de não deixar passar erros, problemas e gaps."
>
> **Método:** 10 agentes auditores, cada um numa lente distinta da máquina (fluxo/ritual, 10 auditores Família 5, 56 hooks, doc-heavy/drift, loops de retrabalho, governança ADR/REGRAS/INV, proporcionalidade do gate, fricção operacional, tamanho de lote, cerimônia de fechamento). Cada recomendação passou por um **guardião adversarial** que a classificou em SAFE / TRADEOFF / REJECT contra a restrição dura de qualidade/segurança. Síntese final consolidada. 21 agentes, ~2,07M tokens, 37min.
>
> **Mandato:** auditar a máquina SEM tratar suas próprias regras como sagradas (elas estavam sob auditoria).

---

## Números-âncora (verificados de forma independente pelo orquestrador, 2026-05-29)

| Métrica | Valor medido | Fonte |
|---|---|---|
| Linhas de documentação (.md) | **127.771** (833 arquivos) | `find docs -name '*.md'` |
| Linhas de código (src/.py) | **73.599** (485 arquivos) | `find src -name '*.py'` |
| Razão doc:código | **≈ 1,7:1** (doc domina) | derivado |
| Linhas de teste (tests/.py) | 42.679 (185 arquivos) | medido |
| Hooks ativos | **55** (450 casos no _test-runner) | `ls .claude/hooks/*.sh` |
| Drift: README público diz | "48 hooks / 379 casos / 61 ADRs" | `README.md:19-20` |
| Realidade | **55 hooks / 450 casos / 73 ADRs** | repositório |
| Commits totais | 733 | `git rev-list` |
| → produto (feat/fix) | 230 = **31,4%** | `git log` |
| → documentação (docs) | 139 = 19,0% | `git log` |
| → puro bookkeeping/status/sync | ≥60 = ≥8,2% | `git log` |
| Doc de processo por módulo (M4) | spec 80KB + plan 37KB + tasks 32KB + matriz 20KB + auditoria 20KB ≈ **190KB** | `ls docs/faseamento/M4-calibracao/` |
| Doc de processo por módulo (M5, já fatiado) | ≈ **49KB** | `ls docs/faseamento/M5-padroes/` |
| Retrabalho M4 1ª passada | 2 CRÍTICO + 13 ALTO + 26 MÉDIO = **41 achados** → 6 lotes de conserto → 2ª/4ª passada | `AGENTS.md`, auditoria-familia5.md |
| Retrabalho M5 (fatiado) | **7 achados** no fim (~6x menos) | M5 handoff |

---

# Por que o desenvolvimento demora — e como acelerar sem baixar a guarda

## 1. Veredito em 1 parágrafo — por que demora

O sistema demora **não porque a checagem de qualidade é exagerada, mas porque ela acontece toda no fim e do mesmo jeito para tudo**. Hoje cada módulo é construído inteiro (130 a 160 tarefas de uma vez), e só depois 10 revisores especialistas passam por cima do módulo pronto, achando 40 problemas de uma vez — aí começa um mutirão de conserto de quase 5 horas, e os revisores precisam passar 2, 3, às vezes 4 vezes de novo. Pior: **os mesmos problemas se repetem em todo módulo** (o sistema redescobre o mesmo defeito de um módulo pro outro, porque copia o molde anterior que já tinha o buraco), e **um quarto de tudo que é "salvo no sistema" não produz produto nem proteção — é só anotar contagens à mão** (quantos verificadores existem, quantos testes passaram), o mesmo número copiado a mão em 12 lugares, que já está errado em vários (o resumo público diz "48 verificadores" quando são 55). Some-se a isso a falta de um banco de dados de verdade no ciclo (o que empurra dezenas de itens "pra depois", virando uma fila de re-trabalho garantido) e as armadilhas do ambiente de teste que já consumiram 5 horas de pura briga com a infraestrutura. **A boa notícia: o próprio projeto já começou a se curar** — o último módulo (M5), construído em pedaços com mini-revisão por etapa, chegou ao fim com 7 problemas em vez de 41. A receita é generalizar isso: fatiar, antecipar a revisão, automatizar a contagem e padronizar o ambiente — sem cortar nenhuma das redes que pegam erro de verdade.

---

## 2. Os maiores sumidouros de tempo (ranqueados)

| # | Sumidouro de tempo | Custo | Lentes | Evidência |
|---|---|---|---|---|
| 1 | **Retrabalho em lote: módulo inteiro construído, depois 40 problemas de uma vez → 5-6 rodadas de conserto + 3-4 re-revisões** | Alto (25-35% do tempo de cada módulo) | L1, L5, L7, L9 | M4: 41 problemas → 6 mutirões (S1..S6.1) de 03:22 a 07:52 (4h30); M3: 40 → 5 mutirões. M5 fatiado: 7 (~6x menos) |
| 2 | **Mesmos defeitos repetem módulo a módulo (cópia cega do molde anterior)** | Alto | L5 | Hash de dado pessoal sem proteção: bug M1 → M3 → M4; proteção anti-duplo-clique: M3 (7) → M4 (3); 6 classes de defeito |
| 3 | **Contagens copiadas à mão em 12+ arquivos, em desacordo entre si** | Alto | L1, L4, L6, L9, L10 | "55/450/73" à mão; README diz "48/379/61" (3 módulos atrasado); ~37 salvamentos só pra reconciliar número |
| 4 | **Os 10 revisores rodam sempre, e re-rodam inteiros na 2ª passada** | Alto | L1, L2, L7 | M3: 5 dos 10 deram "nada achado" de primeira; M4: Desempenho e Cadeia-de-Suprimentos re-rodaram só pra dizer "nada mudou" |
| 5 | **Regra "MÉDIO trava igual a CRÍTICO" força re-revisão por achados pequenos** | Alto | L1, L2, L6, L7 | Dos 26 MÉDIOs de M4, 5 eram "pra depois" mesmo; alguns eram "nome de teste fora do padrão" tratado igual a falha de segurança |
| 6 | **Revisor de "descompasso de documentação" trava muito, e ~100% do que acha é número desatualizado** | Alto | L1, L2, L7, L10 | M3: 13 achados; M4: 13; todos "verificadores 312 vs 377", "decisão proposta vs aceita", "status 163 linhas vs 40" |
| 7 | **Sem banco real no ciclo → ~14 itens/módulo viram "pra depois" = fila de re-trabalho garantida** | Médio-Alto | L1, L5, L8 | M4: 5 problemas + 20+ portões adiados; cobertura cai a ~30% sem banco real |
| 8 | **Armadilhas recorrentes do ambiente de teste (5h15 num único dia)** | Médio-Alto | L8 | 24/05: 5h15 só pra destravar testes (3 armadilhas), zero produto; conhecimento só na memória privada do agente |
| 9 | **Cada módulo gera ~190KB de doc de processo, que alimenta o descompasso do seguinte** | Médio | L1, L4, L9, L10 | M4: 190KB; M5 já caiu pra 49KB sem perder rede |
| 10 | **Arquivo "onde paramos" (deveria ser ≤40 linhas) virou muro de 1.491 palavras** | Médio | L1, L4, L9, L10 | Cada sessão relê o muro; o módulo não coube numa sessão |
| 11 | **Registros de auditoria que o ritual exige mas estão mortos (cerimônia-zumbi)** | Baixo | L2, L10 | A trilha de auditoria parou em 18/05 (antes de M2/M3/M4/M5); o ritual ainda manda anotar nela |

**Contradição resolvida (revisor de documentação):** L4/L10 disseram "só pega número"; L2/L7 mostraram que **também** pega "decisão marcada como proposta quando já foi aceita" — e isso **não é cosmético** (um agente lendo status errado pode reabrir decisão fechada ou pular regra). **Veredito:** automatizar a parte numérica (segura), manter a parte semântica humana.

---

## 3. Ganhos rápidos SEM RISCO (fazer já — classificados SAFE pelo guardião)

### 3.1 — Fonte única e automática para os números (mata sumidouros #3 e #6)
Script que conta sozinho (hooks, testes, ADRs) e escreve em UM lugar; os 12 arquivos apontam "ver status gerado"; um hook trava o salvamento se número à mão divergir do real. **Ganho Alto.** Nenhum desses números é controle de proteção — são metadados; número colado à mão já está errado hoje.

### 3.2 — Fatiar todo módulo em etapas auditáveis numa sessão (mata sumidouro #1)
Oficializar o modelo do M5: fatias de ~20-25 tarefas, cada uma fechando com mini-revisão dos 3-4 revisores da camada. Proibir o módulo "tudo de uma vez" de 130-160 tarefas. **Ganho Alto** (M5: 7 problemas vs 41 do M4). Não corta nenhuma checagem — muda QUANDO disparam.

### 3.3 — Revisão antecipada por fatia, rede inteira só no fim (mata sumidouro #1)
Revisar por fatia + passada completa dos 10 como veredito final. Na re-revisão, rodar só quem falhou + área tocada pelo conserto. **Ganho Alto/Médio.** Pular re-revisão de área não-tocada é seguro: não pode ter regredido se ninguém mexeu nela.

### 3.4 — Comando único e seguro de teste + cheatsheet no projeto (mata sumidouro #8)
Comando memorizável que sempre injeta as opções certas e nunca aceita a que quebra; mover as 3 armadilhas de teste da memória privada para um guia no projeto; corrigir o setup que ensina o comando errado. **Ganho Alto.** Não relaxa teste — impede o erro de digitação.

### 3.5 — Teste-sentinela do catálogo de semente (reduz sumidouro #7)
Transformar a regra que mora só na memória do agente (migrações de "dados-semente" sincronizadas) num teste que falha e diz qual linha falta. **Ganho Alto (preventivo).** AUMENTA a rede.

### 3.6 — Higiene do "onde paramos" e dos registros mortos
Encolher o handoff para ≤40 linhas (histórico vai pro diário); aposentar a trilha de auditoria morta e apontar o registro real por-módulo; 1 salvamento de handoff por etapa. **Ganho Médio.** Nenhum teste/revisor/portão depende desses arquivos.

### 3.7 — Manter (e fortalecer) a revisão profunda do plano antes de codar
Nada se corta; exigir que os 4 especialistas listem explicitamente os defeitos de domínio candidatos. É a MAIOR proteção pelo MENOR custo — pegou 3 erros metrológicos do M5 ANTES de uma linha de código.

---

## 4. Acelerações com TROCA (decisão do Roldão — tocam a política de qualidade)

### 4.1 — Rebaixar MÉDIO de "trava tudo" para "rastreado" — por TIPO de achado, não por área
**Ganho Alto.** Para de travar por achado cosmético. **Risco:** rebaixar "por área" deixa gap regulatório fatiado como "log" escapar (caso provado: a trilha imutável CGCRE foi classificada "MÉDIO de observabilidade" — mas é conformidade ISO dura). **Mitigação:** lista **fechada e explícita** de tipos puramente cosméticos (nome de teste, data sem âncora, contagem, status grande). Qualquer MÉDIO que toque dado pessoal, isolamento entre clientes, permissão de banco, trilha imutável, incerteza, assinatura ou retenção **continua travando, independente de qual revisor achou**. Default = travar; marcar como cosmético exige ação deliberada e auditável.
> **Contradição resolvida:** L6 REJEITOU a versão que dá ao agente poder de decidir "isto é diferível?" (o agente subestima MÉDIO — o bug fundador era um MÉDIO). L1/L7 aprovaram a versão por lista fechada. **Vale a lista fechada, sem julgamento do agente.**

### 4.2 — Rotear revisores por tipo de mudança (não rodar os 10 sempre)
**Ganho Alto.** **Risco:** roteador com bug = revisor que devia rodar fica mudo (vetor do bug fundador). **Mitigação:** roteador **falha-aberto** (na dúvida, RODA); Segurança + Qualidade + Produto + Correção-de-IA + Anti-duplo-clique + revisor de migração-de-dado-pessoal rodam SEMPRE; validar o roteador contra M3/M4 (teria chamado TODOS que acharam problema real) antes de ligar; pular só por extensão inerte (doc, tela), nunca por código.

### 4.3 — Trocar a parte numérica do revisor de documentação por verificação automática (mantendo a semântica humana)
**Ganho Alto.** **Risco:** se o automatizador virar fonte de verdade e sobrescrever sozinho, mascara descompasso semântico real. **Mitigação:** conta só da fonte direta (arquivos reais, suite real — nunca doc-contra-doc) e **bloqueia se divergir**; o revisor humano continua, focado só em descompasso semântico.

### 4.4 — Enxugar a matriz de reconciliação (gerar esqueleto, julgar status à mão)
**Ganho Médio.** **Risco:** a matriz JÁ pegou 2 erros reais (funcionalidade que dizia "pronto" sem estar exposta; defesa declarada e não implementada). Gerar "pronto" automático REPRODUZ a mentira com cara de automação. **Mitigação:** gerar só colunas factuais; a coluna "protege de verdade?" nasce **PENDENTE-CONFERÊNCIA**, nunca verde automático.

### 4.5 — Antecipar o banco real no ciclo (drena a fila do sumidouro #7)
**Ganho: AUMENTA a rede** (cobertura ~30% → real; fecha ~5 itens/módulo adiados). **Risco:** o jeito de subir o ambiente mascara um bug que o banco real deveria pegar (permissão ausente só aparece com usuário ≠ dono). **Mitigação:** script único padronizado contra as 3 armadilhas + passo separado validando permissões com usuário distinto + item só sai da fila com teste verde de verdade.

### 4.6 — Corrigir a raiz da armadilha do cache de teste (sem mascarar)
**Ganho Baixo.** **Risco:** a "solução" tentadora (cache em memória quando falta o pacote) esconde que a proteção anti-abuso para de funcionar entre processos. **Mitigação:** adicionar o pacote faltante às dependências — NUNCA cache-em-memória silencioso.

### 4.7 — Gerar a tabela de decisões automaticamente (após padronizar cabeçalhos)
**Ganho Alto.** **Risco:** só 57 dos 73 ADRs têm cabeçalho padronizado — gerar cego produz tabela com buracos que parece autoritativa. **Mitigação:** padronizar cabeçalhos primeiro (verificação exige cabeçalho completo); o gerador FALHA se algum estiver incompleto.

---

## 5. NÃO mexer — a rede que realmente protege

- **A revisão profunda do plano pelos 4 especialistas ANTES de codar.** Maior proteção pelo menor custo (pegou funcionalidade fantasma e 3 erros metrológicos antes do código).
- **Os 5 revisores sempre ligados: Segurança, Qualidade, Produto, Correção-de-IA, Anti-duplo-clique.** Concentram os achados graves.
- **A regra "documento de fato gera o código".** Não é volume desperdiçado — é a mitigação obrigatória do risco "o dono é o primeiro cliente".
- **NÃO desligar os ~15 verificadores "dormentes"** (guardião REJEITOU): disparam por caminho+conteúdo, a Wave A vai mexer nessas tabelas, e tirá-los cria "controle que existe mas não roda".
- **NÃO mandar o revisor de Segurança confiar no verificador e não re-checar** (guardião REJEITOU): a redundância revisor×verificador é intencional — o bug fundador passou por um ponto cego de verificador mecânico.
- **NÃO afrouxar o bloqueio dando ao agente o poder de decidir "isto é diferível"** (guardião REJEITOU): o agente subestima MÉDIO.
- **Os 55 verificadores automáticos por salvamento** (<1s, zero tokens, pegam apagamento destrutivo e vazamento de senha) e **a chamada por pertinência dos 4 especialistas**.
- **A suite completa de 450 testes como portão de fim-de-fase** (pode ser paralela/só-diff no dia-a-dia, mas continua veredito de fechamento).

---

## 6. Fluxo enxuto proposto (antes → depois)

### ATUAL (por módulo)
```
Especificar (190KB de doc à mão)
  → revisão dos 4 especialistas no plano  [OK — etapa boa]
  → Implementar TUDO (130-160 tarefas, sem banco real)
  → [só agora] 10 revisores sobre o módulo inteiro → 40-41 problemas de uma vez
  → 5-6 mutirões de conserto (~4h30 seguidas)
  → 2ª passada: os 10 INTEIROS de novo (alguns só pra dizer "nada mudou")
  → 3ª/4ª passada SÓ para fechar números de documentação
  → fechar: editar à mão o mesmo status em 7-9 arquivos
  → ~14 itens "pra depois" viram fila de re-trabalho
  → handoff: muro de 1.491 palavras; módulo não cabe na sessão
```

### PROPOSTO (por módulo)
```
Especificar incremental por fatia (M5: 49KB no lugar de 190KB)
  → revisão dos 4 especialistas no plano  [MANTIDA — a etapa de ouro]
  → Para CADA fatia de ~20-25 tarefas:
       Implementar (com banco real no ciclo)
       → mini-revisão dos 3-4 revisores da camada (achado pego cedo, barato)
       → bloqueio aplicado sobre ~20 tarefas (causa-raiz rastreável)
  → passada final dos 10 revisores SOBRE O MÓDULO  [MANTIDA — veredito]
       → ~7 problemas em vez de 41
  → números de status: gerados por script
  → matriz: esqueleto gerado, só "protege de verdade?" conferido à mão
  → handoff: ≤40 linhas; histórico no diário
```

**Impacto estimado:** retrabalho pós-implementação cai de ~40 problemas / 5-6 mutirões / 3-4 re-passadas (M3-M4) para ~7 problemas / 1 passada final (padrão M5 já medido — **~6x menos retrabalho**). Re-revisão cai de 10 para ~5 revisores. Fechamento deixa de tocar 7-9 arquivos à mão. **Nada disso remove um único controle que pegou erro real — só muda o quando e o como.**

---

## 7. Plano de ação

### Faço sozinho (SAFE — agente executa, não precisa decisão)
1. Script único de status que conta sozinho + trava que bloqueia salvamento se número à mão divergir. Remover contagens à mão dos 12 arquivos. *(mata #3, #6)*
2. Comando seguro único de teste + mover as 3 armadilhas pra guia no projeto + corrigir o setup que ensina o comando errado. *(mata #8)*
3. Teste-sentinela do catálogo de semente. *(reduz #7)*
4. Encolher "onde paramos" pra ≤40 linhas + aviso automático de verdade quando passar do teto + casos de teste do aviso.
5. Aposentar a trilha de auditoria morta + corrigir o ritual pra apontar o registro real por-módulo. 1 handoff por etapa.
6. Reforçar no roteiro dos 4 especialistas a listagem explícita de defeitos de domínio candidatos.

### Precisa decisão do Roldão (TRADEOFF — toca a política de qualidade)
7. **Política de bloqueio: separar MÉDIO "cosmético" de MÉDIO "duro"** por lista fechada (sem julgamento do agente). **Recomendação: aprovar.** *(4.1)*
8. **Fatiar todo módulo (modelo M5) como padrão obrigatório** + revisão antecipada por fatia + 2ª passada incremental. Maior ganho (~6x). **Recomendação: aprovar e cravar como invariante.** *(3.2, 3.3)*
9. **Roteamento dos revisores por tipo de mudança** (roteador falha-aberto + 6 essenciais fixos + validado contra M3/M4). **Recomendação: aprovar com as travas.** *(4.2)*
10. **Antecipar banco real no ciclo** (validação separada de permissões + trava anti-mascaramento). **Recomendação: aprovar.** *(4.5)*

### Estrutural, depois dos quick wins
11. Gerar a tabela de decisões (após padronizar os 16 cabeçalhos faltantes). *(4.7)*
12. Enxugar a matriz de reconciliação (esqueleto gerado, status PENDENTE-CONFERÊNCIA). *(4.4)*
13. Redefinir o revisor de documentação para só o semântico. *(4.3)*
14. Adicionar o pacote de cache faltante às dependências. *(4.6)*

**Honestidade final:** a lentidão NÃO vem da rede de qualidade ser exagerada — vem de ela rodar **tarde**, **igual pra tudo**, e de um quarto do esforço ser anotação manual de número. Itens 1-6 dão ganho imediato sem decisão. Itens 7-10 são onde mora o maior ganho (o retrabalho em lote), e por mexerem na política que protege contra erro regulatório/segurança é que vão à mesa do Roldão — todos com mitigação que captura o ganho sem abrir buraco.
