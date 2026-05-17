# Discovery — Dores mapeadas

> **Artefato Rodada 0** (agente sintetiza, a partir das entrevistas). Dores ranqueadas por **6 dimensões** (Auditor 6 v2):
>
> **Versão pré-entrevistas, baseada em síntese.** Esta primeira passagem cruza `jornada-atual-sem-produto.md` (4 ciclos + 14 dores D-NNN + custo R$ 35-50k/mês), `jobs-to-be-done.md` (~109 JTBDs + 12 Big Jobs), `personas-detalhadas.md` (14 personas) e `riscos.md` (57 riscos R-NNN). **Nenhuma entrevista real ainda foi feita.** Tudo abaixo é inferência rastreada a evidência interna (ciclo/passo da jornada + JTBD + risco). **Top dores serão re-rankeadas após Onda 1 com citações literais.**

---

## Métrica de priorização

Cada dor é avaliada em 6 dimensões:

| Dimensão | Pergunta | Escala |
|---|---|---|
| **Agudez** | Quão grave quando acontece? | 1 (incomoda) – 5 (paralisa empresa) |
| **Frequência** | Quantas vezes por mês? | <1 / 1–4 / 5–20 / >20 |
| **Disposição a pagar** | Cliente pagaria pra resolver? Quanto? | R$/mês auto-reportado (deflacionar 50%) |
| **Solvability** | Quão caro pra a gente resolver? | 1 (POC em 1 dia) – 5 (rewrite de meses) |
| **Reach** | Quantos clientes do TAM têm essa dor? | % estimado da amostra |
| **Evitabilidade** | Existe workaround manual aceitável hoje? | sim (baixa urgência) / não (alta urgência) |

**Score sugerido:** (Agudez × Frequência × Reach × DAP) ÷ (Solvability × Evitabilidade)

> **Convenções deste documento:**
> - Frequência convertida em número (≈) pra entrar na fórmula: <1 → 0,5 ; 1–4 → 2 ; 5–20 → 10 ; >20 → 30.
> - Reach convertido em fração decimal (0,40 = 40% do TAM).
> - DAP em centenas de R$ (deflacionado 50% do auto-reportado-inferido) — ex: DAP "150" = R$ 150/mês.
> - Evitabilidade "sim" = 2 (workaround existe), "não" = 1 (não existe ou viola norma).
> - Score: (A × F × R × DAP) ÷ (S × E) — divisão usa Solvability como custo de implementação e Evitabilidade como urgência inversa.
> - **Marcação `[INFERÊNCIA — validar em onda 1]`:** dor cuja existência é razoavelmente garantida pela jornada, mas cujos números (frequência, DAP, reach) são palpite. **Toda dor abaixo está marcada porque não temos entrevista real ainda** — a marcação distingue "inferência forte com 3+ fontes internas" de "inferência fraca com 1 fonte".

Ranking não é cego ao score — sempre justificar com citação literal da entrevista (a vir).

---

## Dores ranqueadas (20 dores — pré-entrevistas)

> **Cobertura por ciclo:** 4 dores no Ciclo Comercial · 5 dores no Ciclo Operacional · 5 dores no Ciclo Metrológico · 3 dores no Ciclo Financeiro · 3 dores transversais.
> **Cobertura por decisão fundadora:** Frota+UMC+Caixa do Técnico (Dor #08, #16) · Comissões Configuráveis (Dor #15) · Cliente 360°+Automações (Dor #02, #05, #20) · Estoque com lacre/selo INMETRO (Dor #18).

---

### Dor #01: Cadastro de cliente digitado 4 a 6 vezes em sistemas que não conversam
- **Origem (jornada):** Ciclo Comercial §4.8 — "MESMO DADO digitado de 4 a 6 vezes... pior ponto de duplicação da jornada" + violação silenciosa de §6.bis (LGPD art. 33 — sem DPA entre Bling/Cali/Drive)
- **Sintoma observável:** atendente Letícia leva 20 a 45 minutos por cliente novo, criando o mesmo CNPJ em planilha "Clientes.xlsx" + Bling + Cali/Metroex + planilha de OS + grupo WhatsApp; erro de digitação trava NFS-e dias depois, endereço diferente entre sistemas manda técnico pro lugar errado
- **Personas mais afetadas:** Letícia (atendente, sente todos os dias), Cláudia (financeiro, herda o erro fiscal), Roldão (dono, paga horas perdidas), Sandra (RT, perde rastreabilidade), Bruno (técnico, vai pra endereço errado)
- **Dimensões:**
  - **Agudez 3/5** — não paralisa empresa mas drena 1-3h por cadastro novo + erros caros depois
  - **Frequência >20/mês** — 5 a 15 clientes novos/mês × 4-6 sistemas; atualizações de dado existente diárias
  - **DAP 200/mês inferido** (auto-reportado-estimado R$ 400 → deflacionado R$ 200) — dor universal mas mal-quantificada pelo dono ("é assim mesmo")
  - **Solvability 2/5** — modelo de dados com cliente como entidade única + integração com NFS-e (BaaS Focus/PlugNotas) é viável em poucos sprints
  - **Reach 90%** — observado em jornada §2.2 como característica de "100% das empresas BR" do ICP
  - **Evitabilidade não (=1)** — workaround é o problema; planilha não substitui integração
- **Score:** (3 × 30 × 0,90 × 200) ÷ (2 × 1) = **8.100**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §4.8 "MESMO DADO digitado de 4 a 6 vezes — pior ponto de duplicação da jornada" + Persona Letícia §"O que a deixa louca": "Cliente é cadastrado 4 vezes — em 4 telas diferentes — e ainda assim quando vou achar, sumiu" + JTBD-054 + D-001 + BIG-07 (promovido a Big Job)
- **Implicação pra MVP:** ENTRA (foundation — Cliente 360° começa aqui)
- **Módulo provável:** Cliente / Cadastros base
- **Vínculo com JTBD:** JTBD-054, BIG-07, BIG-10 (Cliente 360°)

---

### Dor #02: Esquecimento de lembrar cliente da próxima calibração (recalibração perdida 30-50%)
- **Origem (jornada):** Ciclo Metrológico §6.12 — "NÃO é sistemático. Empresa-modelo perde 30-50% das recalibrações por esquecimento" + Ciclo Comercial §4.11 (contrato anual farma sem lembrete automático)
- **Sintoma observável:** planilha "Validades.xlsx" + Google Calendar; Rogério (vendedor) e Letícia (atendente) "quando lembram" mandam mensagem manual; cliente final recebe lembrete do concorrente antes; empresa perde 30-50% das recalibrações que tinha direito a renovar
- **Personas mais afetadas:** Roldão (perde receita recorrente), Rogério (perde comissão de renovação), Sandra (não fecha ciclo de qualidade), João (cliente final fica sem certificado válido)
- **Dimensões:**
  - **Agudez 5/5** — receita perdida direta; dor canônica do setor de calibração
  - **Frequência 10-30/mês** — 60-180 certificados/mês × 30-50% esquecimento → ~30 oportunidades perdidas/mês na empresa-modelo
  - **DAP 400/mês inferido** (auto-reportado-estimado R$ 800 → deflacionado R$ 400) — alto porque o dono SENTE a receita perdida quando contam pra ele
  - **Solvability 2/5** — calendário de recalibração + WhatsApp template aprovado + automação simples
  - **Reach 95%** — universal em calibração; observado em Jornada §1 e §8 como R$ 8-12k/mês de receita perdida
  - **Evitabilidade não (=1)** — workaround atual (planilha) é exatamente o que falha
- **Score:** (5 × 30 × 0,95 × 400) ÷ (2 × 1) = **28.500**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §1 "30-50% das recalibrações são perdidas por esquecimento" + Jornada §8 "Receita perdida em recalibração R$ 8.000 a R$ 12.000/mês" + JTBD-084 (renovação automática) + JTBD-044 (alerta 60-90 dias) + D-002 + BIG-10/BIG-11
- **Implicação pra MVP:** ENTRA (uma das duas vendas-engatilho do produto — junto com NFS-e)
- **Módulo provável:** CRM (BIG-10) + Automações (BIG-11)
- **Vínculo com JTBD:** JTBD-084, JTBD-044, JTBD-089 (link agendamento), BIG-10, BIG-11

---

### Dor #03: Certificado emitido sem campo obrigatório do NIT-DICLA-030 (rejeição em auditoria Cgcre)
- **Origem (jornada):** Ciclo Metrológico §6.8 — "Template Word frequentemente desalinhado com NIT-DICLA-021... PDF sem assinatura digital ICP-Brasil → cliente farma rejeita" + Riscos R-018 score 25
- **Sintoma observável:** Marcos (signatário) usa template Word "Certificado padrão.docx" que perdeu campo (rastreabilidade explícita, k=2, condições ambientais, versão do software); auditor Cgcre encontra na supervisão; perfil A perde acreditação ou recebe NC grave; cliente farma reprova lote
- **Personas mais afetadas:** Marcos (responsabilidade legal — CRQ em risco), Roldão (acreditação em risco = negócio em risco), Sandra (RT defende NC), Patrícia (cliente farma reprova)
- **Dimensões:**
  - **Agudez 5/5** — CATASTRÓFICA quando acontece (perda de acreditação destrói o negócio)
  - **Frequência 1-4/mês** (=2) — não acontece toda hora mas existe latente sempre; auditoria Cgcre é a cada 12-18 meses (A) ou 4 anos (B) com supervisões
  - **DAP 600/mês inferido** (auto-reportado-estimado R$ 1.200 → deflacionado R$ 600) — dor onde o dono PAGA pra dormir tranquilo
  - **Solvability 2/5** — template estruturado + hook de validação de campo obrigatório + INV-002 (bloqueio sem cadeia) é POC em semanas
  - **Reach 80%** — quase universal em perfil A + B; alguns perfis B ignoram porque "não auditam"
  - **Evitabilidade não (=1)** — workaround atual é exatamente "esperar não dar problema"; auditor encontra no primeiro relance
- **Score:** (5 × 2 × 0,80 × 600) ÷ (2 × 1) = **2.400**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §6.8 risco regulatório explícito + R-018 score 25 (o maior risco do projeto) + Persona Roldão §"O que o deixa louco": "Tô em auditoria Cgcre e o auditor pede 'me mostre o histórico de calibração desse padrão' — vou na planilha, na pasta de PDFs, no e-mail e em 2 cadernos físicos" + INV-002 + D-007 + BIG-02
- **Implicação pra MVP:** ENTRA (hook bloqueia emissão sem cadeia — sobrevivência do produto)
- **Módulo provável:** Metrologia (emissão de certificado)
- **Vínculo com JTBD:** JTBD-028 (cadeia rastreabilidade), JTBD-031 (validação software), JTBD-051 (assinar sem ansiedade), BIG-02

---

### Dor #04: Word/Excel/macros pra cálculo de incerteza = NC permanente cláusula 7.11 (violação silenciosa)
- **Origem (jornada):** Ciclo Metrológico §6.5 + §6.bis (Violações regulatórias silenciosas) — "Planilha Excel personalizada com macros pra incerteza, SEM validação documentada (especificação + teste + aprovação) = NC permanente da cláusula 7.11. Não é 'macro vai quebrar' — é não conformidade ATIVA enquanto o lab usa"
- **Sintoma observável:** lab usa planilha herdada "Incerteza.xlsx" há anos, sem dossiê de validação (especificação + teste + aprovação documentada); descobre só em auditoria Cgcre OU quando cliente farma audita fornecedor; lote do cliente farma é reprovado por "cálculo não-validado"; lab paga R$ 50k a R$ 500k de indenização
- **Personas mais afetadas:** Marcos (responsabilidade direta — assinou), Sandra (RT defende), Roldão (negócio em risco), Patrícia (cliente farma como auditora)
- **Dimensões:**
  - **Agudez 5/5** — NC ativa permanente (não "vai dar problema" — JÁ É problema)
  - **Frequência >20/mês** (=30) — todo certificado emitido com a planilha materializa a NC
  - **DAP 300/mês inferido** (auto-reportado-estimado R$ 600 → deflacionado R$ 300) — alto entre quem já tomou susto; baixo entre quem nunca foi auditado a fundo (ignorância do risco)
  - **Solvability 3/5** — exige software validado com dossiê (especificação + teste de aceitação + aprovação RT) e change log com hash; não é trivial, mas é vendável
  - **Reach 55%** (planilha Excel + macros 25-30%) + (Cali/Metroex sem dossiê de validação do próprio 25%) — Jornada §13 confirma 25-30% só de planilha + parte dos labs Cali não tem dossiê documentado
  - **Evitabilidade não (=1)** — workaround atual é precisamente "rezar"
- **Score:** (5 × 30 × 0,55 × 300) ÷ (3 × 1) = **8.250**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §6.5 + §6.bis (cláusula 7.11) + JTBD-027 (rotina pré-validada por grandeza/faixa) + JTBD-031 (provar validação quando auditor pede) + D-011 + INV-004a/b/c + R-023 score 15
- **Implicação pra MVP:** ENTRA (pitch real do Aferê per Jornada §6.5 — "tirar o lab da NC, não 'facilitar o cálculo'")
- **Módulo provável:** Metrologia (cálculo de incerteza)
- **Vínculo com JTBD:** JTBD-027, JTBD-031, BIG-02

---

### Dor #05: Status de OS perguntado o tempo todo pelo cliente (10-30 perguntas/dia)
- **Origem (jornada):** Ciclo Operacional §5.8 — "Atendente recebe 10-30 perguntas/dia sobre status, todas respondíveis se tivesse portal. Tempo perdido enorme."
- **Sintoma observável:** Letícia interrompida 10-30x/dia ("cadê meu certificado?", "vocês foram lá?", "quando emite?"); cada consulta toma 5-10 min porque ela precisa abrir 3 sistemas + perguntar no grupo WhatsApp interno; cliente fica com sensação de "não dão satisfação"
- **Personas mais afetadas:** Letícia (drenagem direta — primeira voz do cliente), João (cliente final ansioso), Roldão (paga horas de atendente perdidas), Bruna (segunda técnica também é interrompida no campo)
- **Dimensões:**
  - **Agudez 3/5** — drenante e desumanizante; Letícia "vira digitadora"
  - **Frequência >20/mês** (=30) — 10-30 perguntas/dia × 20 dias úteis = 200-600/mês
  - **DAP 150/mês inferido** (auto-reportado-estimado R$ 300 → deflacionado R$ 150) — moderado; dono frequentemente subestima essa dor
  - **Solvability 2/5** — portal cliente + envio WhatsApp template "OS XPTO está na fase Y" é POC simples; já existe em Cali WEB embora "feio que ninguém usa"
  - **Reach 85%** — universal em PME 5-10 pessoas; pode cair em perfil D pequeno
  - **Evitabilidade sim (=2)** — workaround atual (responder manualmente) é cansativo mas funciona
- **Score:** (3 × 30 × 0,85 × 150) ÷ (2 × 2) = **2.869**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §5.8 explicitamente "10-30 perguntas/dia" + Persona Letícia §"O que a deixa louca": "10 vezes por dia: 'cadê o orçamento que mandei segunda?'. Eu não sei. Procuro no e-mail, na pasta, no WhatsApp do Roldão" + JTBD-017 (responder cadê certificado sem levantar) + JTBD-091 (Cliente 360° em 1 tela) + D-005
- **Implicação pra MVP:** ENTRA (portal cliente lite + automação de notificação de mudança de status — quick win)
- **Módulo provável:** Portal do cliente + Automações
- **Vínculo com JTBD:** JTBD-017, JTBD-091, JTBD-089, BIG-10

---

### Dor #06: Padrão usado com calibração vencida (certificado nulo + risco perda acreditação)
- **Origem (jornada):** Ciclo Operacional §5.4 + Ciclo Metrológico §6.3 — "Padrão VENCIDO levado → certificado emitido é NULO em auditoria Cgcre" + "Esquecimento de verificar validade é falha comum"
- **Sintoma observável:** Bruno (técnico) sai pra campo com massa-padrão F1 cuja calibração-pai venceu há 2 meses; ninguém checou; certificado emitido vira nulo; auditor Cgcre encontra na supervisão → NC grave + reauditoria + risco real de perder acreditação; lab pode ter que refazer 50-300 certificados retroativos
- **Personas mais afetadas:** Marcos (signatário responde legalmente), Bruno (executou), Sandra (RT defende), Roldão (negócio em risco)
- **Dimensões:**
  - **Agudez 5/5** — catastrófica quando descoberto (R-018 + INV-011)
  - **Frequência 1-4/mês** (=2) — não rotineiro, mas "1 vez é catastrófico"; estimativa setorial: 1 padrão vencido usado a cada 3-6 meses na empresa-modelo
  - **DAP 400/mês inferido** (auto-reportado-estimado R$ 800 → deflacionado R$ 400) — dor onde dono pagaria pra ter alerta + bloqueio
  - **Solvability 1/5** — calendário de validade de padrão + hook de bloqueio de emissão se padrão vencido (INV-011) é POC em 1-2 dias
  - **Reach 75%** — alta em qualquer perfil que emite certificado rastreável (A, B, C); irrelevante em D puro
  - **Evitabilidade não (=1)** — workaround atual ("olhar etiqueta no armário") é precisamente o que falha
- **Score:** (5 × 2 × 0,75 × 400) ÷ (1 × 1) = **3.000**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §5.4 + §6.3 risco regulatório explícito + INV-011 (padrão vencido bloqueia emissão) + JTBD-028 + JTBD-032 (dashboard padrões com validade) + R-018 + D-003
- **Implicação pra MVP:** ENTRA (invariante INV-011 — bloqueio na emissão é core do BIG-02)
- **Módulo provável:** Metrologia (gestão de padrões + emissão)
- **Vínculo com JTBD:** JTBD-028, JTBD-032, BIG-02

---

### Dor #07: Signatário-gargalo (pilha de certificados; férias = emissão para)
- **Origem (jornada):** Ciclo Metrológico §6.9 — "Signatário é gargalo. Empilha 20 certificados e demora 2-3 dias. Assina em massa sem reler — descumpre supervisão da cláusula 6.2. Escopo de assinatura não controlado pelo sistema → assina fora do escopo = NC grave"
- **Sintoma observável:** Marcos (única pessoa autorizada pra escopo X) vai de férias → emissão para por 7-10 dias; OU Marcos volta de viagem e tem 30 certificados empilhados → assina em massa sem reler → assina 1 fora de escopo → NC cláusula 6.2; OU Marcos pede demissão → receita despenca
- **Personas mais afetadas:** Marcos (sobrecarga + ansiedade), Roldão (bus factor + receita parada), Sandra (RT testemunha), Letícia (precisa contar pro cliente que atrasou)
- **Dimensões:**
  - **Agudez 4/5** — alta crônica; pode escalar pra 5 (sai da empresa)
  - **Frequência 5-20/mês** (=10) — 1-3 vezes/semana acontece "espera o Marcos" no fluxo
  - **DAP 300/mês inferido** (auto-reportado-estimado R$ 600 → deflacionado R$ 300) — alto entre quem já viveu férias do signatário
  - **Solvability 3/5** — matriz competência × escopo × signatário + workflow de revisão "4 olhos" + assinatura digital ICP-Brasil — moderado
  - **Reach 75%** — universal em PME pequena onde signatário é gargalo crônico (1 pessoa); irrelevante só em lab grande com 3+ signatários
  - **Evitabilidade não (=1)** — workaround atual ("torcer pra ele não faltar") não funciona
- **Score:** (4 × 10 × 0,75 × 300) ÷ (3 × 1) = **3.000**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §6.9 explicitamente "signatário é gargalo... assina em massa sem reler" + Persona Marcos §"O que o deixa louco" (a confirmar mas sinal forte) + JTBD-030 (assinar sem ritual chato) + JTBD-051 (assinar 20 com checklist verde) + JTBD-056 (matriz competência × signatário × grandeza) + R-015 score 15 + D-004
- **Implicação pra MVP:** ENTRA parcial (matriz competência INV-003 + assinatura digital — sim; "4 olhos" pode ficar MVP-2)
- **Módulo provável:** Qualidade (competências) + Metrologia (assinatura)
- **Vínculo com JTBD:** JTBD-030, JTBD-051, JTBD-056, JTBD-004 (não-depender-de-uma-pessoa), BIG-02

---

### Dor #08: Roteirização de técnico no escuro + 2ª visita por padrão/peça faltando
- **Origem (jornada):** Ciclo Operacional §5.3 + §5.4 — "Técnico A vai pra zona norte de manhã e zona sul à tarde, técnico B faz o oposto — 2x combustível e 2x tempo" + "Padrão errado levado (não cobre faixa) → técnico chega e não consegue calibrar → 2ª visita = prejuízo"
- **Sintoma observável:** Roldão escolhe agenda do dia "de cabeça" + WhatsApp; combustível dobrado; padrão errado/vencido detectado no cliente → técnico volta sem fazer o serviço; 2ª visita custa R$ 3-6k/mês conforme Jornada §8
- **Personas mais afetadas:** Roldão (custo escondido), Bruno (frustrado), Bruna (também), Carlos (motorista UMC — diesel + diária dobrada), Sandra (gerente reorganiza)
- **Dimensões:**
  - **Agudez 4/5** — custo direto + impacto na percepção do cliente
  - **Frequência 5-20/mês** (=10) — 1-3 retornos por semana é estimativa setorial
  - **DAP 250/mês inferido** (auto-reportado-estimado R$ 500 → deflacionado R$ 250) — moderado a alto; dono sente combustível
  - **Solvability 4/5** — roteirização de verdade exige geocodificação + heurística + integração com Google Maps; verificação de padrão pré-saída é simples; cobertura completa exige UX cuidadosa
  - **Reach 80%** — universal em qualquer operação com 2+ técnicos de campo; sobe pra 100% em quem opera UMC
  - **Evitabilidade sim (=2)** — workaround atual (WhatsApp + cabeça) funciona mal mas funciona
- **Score:** (4 × 10 × 0,80 × 250) ÷ (4 × 2) = **1.000**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §5.3 + §5.4 + §8 (combustível + 2ª visita R$ 3-6k/mês) + JTBD-021 (saber tudo da OS antes de chegar) + JTBD-009 (saber onde técnico está) + JTBD-065 (qual veículo disponível) + D-006 + R-044/R-046
- **Implicação pra MVP:** ENTRA parcial (checklist pré-saída + agenda visível MVP-1; otimização geográfica = MVP-2)
- **Módulo provável:** Operação (agenda + OS) + Frota+UMC (BIG-08)
- **Vínculo com JTBD:** JTBD-009, JTBD-021, JTBD-065, BIG-08

---

### Dor #09: Conciliação financeira manual (extrato vs NFS-e vs OS) — 4h/semana
- **Origem (jornada):** Ciclo Financeiro §7.4 — "Sem integração bancária = trabalho manual enorme. PIX recebido com identificador errado → não bate com NFS-e → conciliação manual. 30 min a 3 horas por semana"
- **Sintoma observável:** Cláudia (financeiro) baixa OFX do internet banking, abre Bling, abre planilha "Inadimplência.xlsx", abre planilha de OS, e bate linha por linha; PIX sem identificador exige caça ao cliente; boleto pago parcial vira nota mental; "fechar a semana" toma 1 dia útil; surge erro caro (cobrar cliente que já pagou — D-018-quase)
- **Personas mais afetadas:** Cláudia (dor direta — esgotamento mensal), Roldão (paga horas), Letícia (cobra cliente errado — risco JTBD-018)
- **Dimensões:**
  - **Agudez 3/5** — drenante mas não catastrófico; potencial de virar 4 quando erro caro acontece
  - **Frequência >20/mês** (=30) — diário/semanal contínuo
  - **DAP 250/mês inferido** (auto-reportado-estimado R$ 500 → deflacionado R$ 250) — moderado-alto entre quem já contratou Conta Azul/Omie justamente por isso
  - **Solvability 3/5** — integração Open Finance + match por txid PIX + nosso número de boleto é trabalho real (Bacen 4.658/2018) mas com BaaS bancário fica viável
  - **Reach 85%** — universal entre quem emite NFS-e + recebe PIX/boleto (todos)
  - **Evitabilidade sim (=2)** — Conta Azul/Omie já resolvem parcial; workaround Bling existe
- **Score:** (3 × 30 × 0,85 × 250) ÷ (3 × 2) = **3.187**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §7.4 explicitamente "30 min a 3 horas/semana" + JTBD-035 (conciliar PIX/boleto sem virar Excel) + D-008
- **Implicação pra MVP:** ENTRA (financeiro de alto nível = MVP-1 confirmado pelas decisões fundadoras)
- **Módulo provável:** Financeiro
- **Vínculo com JTBD:** JTBD-035, JTBD-039 (fluxo caixa 30 dias), BIG-04 (NFS-e dependente)

---

### Dor #10: NFS-e municipal — cutover Padrão Nacional 01/09/2026 + 26 prefeituras diferentes
- **Origem (jornada):** Ciclo Financeiro §7.1 — "Cutover NFS-e Padrão Nacional 01/09/2026 (R-016) muda layout" + Riscos R-016 score 20 + R-017 (Porto Alegre desliga local em 01/07/2026)
- **Sintoma observável:** Cláudia digita dados do cliente DE NOVO no Bling/Omie pra emitir NFS-e (porque cadastro não conversa — Dor #01); descrição genérica "calibração" sem detalhar instrumento → cliente questiona; código de serviço municipal errado → ISS errado; 01/09/2026 chega e layout muda (Res. CGSN 189/2026) → emissão para
- **Personas mais afetadas:** Cláudia (toda emissão), Roldão (preocupação com fisco), Patrícia (cliente farma exige NFS-e com detalhamento técnico)
- **Dimensões:**
  - **Agudez 5/5** — cutover obrigatório com data; quem não migrar não fatura; multa fiscal
  - **Frequência >20/mês** (=30) — 60-180 NFS-e/mês na empresa-modelo
  - **DAP 350/mês inferido** (auto-reportado-estimado R$ 700 → deflacionado R$ 350) — alto; já pagam Bling/Omie/Conta Azul justamente pra isso
  - **Solvability 3/5** — BaaS fiscal (Focus, PlugNotas, TecnoSpeed) resolve a parte BR; integração com OS é nossa
  - **Reach 100%** — universal: toda empresa do ICP emite NFS-e
  - **Evitabilidade sim (=2)** — Bling/Omie já fazem; gap é integrar com OS de calibração
- **Score:** (5 × 30 × 1,00 × 350) ÷ (3 × 2) = **8.750**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §7.1 (R-016) + Concorrentes §3-4 "GAP CONFIRMADO" — nenhum dos 14 concorrentes nacionais (Cali, Metroex, Calibre, Q-MAN, ConfLab, etc.) tem NFS-e nativa; FP2 cobre só Santa Maria/RS + JTBD-034 + BIG-04 + D-021 + R-016 score 20
- **Implicação pra MVP:** ENTRA (uma das duas vendas-engatilho — junto com Dor #02; tese central do produto per Concorrentes §6)
- **Módulo provável:** Fiscal/NFS-e (BIG-04)
- **Vínculo com JTBD:** JTBD-034, BIG-04

---

### Dor #11: Inadimplência tratada pessoalmente pelo dono (cobrança constrangedora)
- **Origem (jornada):** Ciclo Financeiro §7.5 + §7.6 — "Cobrança vira problema pessoal do dono. Cliente inadimplente é também cliente operacional ativo → conflito interno: cobrar e perder cliente OU atender e nunca receber"
- **Sintoma observável:** Cláudia identifica boleto vencido na planilha "Inadimplentes.xlsx"; manda WhatsApp constrangedor pro cliente; cliente nega ("já paguei!"); escala pro Roldão que liga pessoalmente; Letícia abre nova OS pra cliente bloqueado porque ninguém avisou; receita continua sendo entregue sem entrar
- **Personas mais afetadas:** Roldão (peso emocional), Cláudia (drenagem + sentir-se "chata"), Letícia (erro por desinformação), Rogério (vendedor descobre tarde)
- **Dimensões:**
  - **Agudez 4/5** — alta — emocional + financeira
  - **Frequência 5-20/mês** (=10) — média de 5-15 inadimplências ativas por mês na empresa-modelo
  - **DAP 250/mês inferido** (auto-reportado-estimado R$ 500 → deflacionado R$ 250)
  - **Solvability 2/5** — régua de cobrança com escalada (WhatsApp template + e-mail + bloqueio de novo orçamento) é trabalho moderado; Asaas/Cobre Fácil têm referências
  - **Reach 80%** — universal em PME
  - **Evitabilidade sim (=2)** — Asaas resolve parcial; workaround pessoal "funciona"
- **Score:** (4 × 10 × 0,80 × 250) ÷ (2 × 2) = **2.000**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §7.5-7.6 + JTBD-036 (cobrar sem ficar mal) + JTBD-053 (não ser chata) + JTBD-088 (régua com escalada) + JTBD-095 (bloquear orçamento pra inadimplente) + D-009 + BIG-11
- **Implicação pra MVP:** ENTRA parcial (bloqueio de novo orçamento pra inadimplente — JTBD-095 — MVP-1; régua completa = MVP-2)
- **Módulo provável:** Financeiro + Automações (BIG-11)
- **Vínculo com JTBD:** JTBD-036, JTBD-053, JTBD-088, JTBD-095, BIG-11

---

### Dor #12: Dono opera no dia (apaga incêndio) sem visão estratégica
- **Origem (jornada):** Ciclo Financeiro §7.8 + transversal — "Dono vê DRE com 30-45 dias de atraso → decide com info defasada. Sem visão de margem por serviço/cliente/grandeza → não sabe o que é rentável" + §8 "2-4h/dia do dono apagando incêndio"
- **Sintoma observável:** Roldão chega 7h, abre 40 WhatsApps da madrugada, atende fornecedor + cliente irritado + financeiro + técnico com dúvida; à noite "fecha caixa" no extrato bancário contra planilha do financeiro; trabalha 60-70h/semana; toma decisão de aceitar contrato sem saber margem; descobre prejuízo invisível no fim do trimestre
- **Personas mais afetadas:** Roldão (burnout iminente — R-011 score 15 + R-029 score 15), família, sócio se houver
- **Dimensões:**
  - **Agudez 5/5** — burnout = perda do produto inteiro; bus factor catastrófico
  - **Frequência >20/mês** (=30) — diário
  - **DAP 200/mês inferido** (auto-reportado-estimado R$ 400 → deflacionado R$ 200) — moderado porque o dono geralmente não SABE o tamanho do problema (ele "é assim")
  - **Solvability 3/5** — dashboard com "1 número do dia" + lista de ações pendentes (JTBD-097) é viável; análise de margem por OS é trabalho moderado (depende de BIG-08+BIG-09 integrados)
  - **Reach 90%** — universal entre donos de PME 5-10 pessoas
  - **Evitabilidade sim (=2)** — workaround é "viver assim"
- **Score:** (5 × 30 × 0,90 × 200) ÷ (3 × 2) = **4.500**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §1 + §8 "2 a 4 horas/dia do dono apagando incêndio" + Persona Roldão §"Dia típico" (manhã 7-12h + tarde 13-18h + fim de dia 18-20h + noite/fim-de-semana) + JTBD-001 (1 número do dia) + JTBD-097 (1 número + lista de ações) + JTBD-080 (rentabilidade por OS) + D-010 + R-011 + R-029
- **Implicação pra MVP:** ENTRA (Painel do Dono — diferencial assumido por decisão fundadora; dashboard MVP-1, análise de margem MVP-2)
- **Módulo provável:** Painel do Dono (transversal)
- **Vínculo com JTBD:** JTBD-001, JTBD-097, JTBD-013, JTBD-080, BIG-10

---

### Dor #13: Auditoria de cliente farma sem aviso (modo emergência) + reclamação formal cláusula 7.9 sem registro
- **Origem (jornada):** §11 (Pontos de inflexão #11, #12, #14) + Ciclo Operacional §5.10 + §6.bis — "Auditor externo chega sem aviso pra auditoria de fornecedor — lab precisa apresentar evidência de rastreabilidade, validação de software, autorização de signatário NA HORA. Status quo trava" + "Reclamação formal cláusula 7.9 com prazo regulatório pra responder — status quo não tem workflow"
- **Sintoma observável:** Patrícia (cliente farma) liga "estamos aí amanhã pra auditoria de fornecedor"; Sandra (RT) entra em pânico, vira a noite separando PDFs, planilhas, certificados-pai; OU cliente registra reclamação no e-mail, e-mail vai pro spam, lab passa do prazo regulatório de resposta, cliente vai pra ANPD/INMETRO
- **Personas mais afetadas:** Sandra (RT — sobrevivência regulatória), Marcos (apresenta), Roldão (cliente em risco — receita), Patrícia (representa o cliente farma)
- **Dimensões:**
  - **Agudez 5/5** — perder cliente farma é R$ 30-150k/ano por contrato
  - **Frequência 1-4/mês** (=2) — 1-3 auditorias/ano por cliente farma + reclamações esporádicas
  - **DAP 300/mês inferido** (auto-reportado-estimado R$ 600 → deflacionado R$ 300) — alto quando ativa
  - **Solvability 3/5** — "modo auditoria" (JTBD-058 — 1 clique exibe certificados + cadeia + NC + signatários autorizados) + workflow de reclamação 7.9 (JTBD-093) — moderado
  - **Reach 40%** — só atinge labs que atendem cliente farma/automotivo/aeroespacial; mas é decisivo pra eles
  - **Evitabilidade não (=1)** — workaround atual ("virar a noite") destrói Sandra
- **Score:** (5 × 2 × 0,40 × 300) ÷ (3 × 1) = **400**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §11 #11/#12/#14 + Persona Patrícia §"Como ela aceita evidência do software" + JTBD-058 (modo auditoria 1 clique) + JTBD-031 (provar validação) + JTBD-093 (workflow reclamação 7.9) + D-012 + D-013 + R-024
- **Implicação pra MVP:** ENTRA parcial (modo auditoria simples MVP-1 com filtros básicos; workflow de reclamação 7.9 estruturado pode ficar MVP-2)
- **Módulo provável:** Qualidade
- **Vínculo com JTBD:** JTBD-058, JTBD-031, JTBD-093, BIG-02

---

### Dor #14: Cliente farma exige certificado em 3 dias úteis + cronograma anual sem lembrete
- **Origem (jornada):** Ciclo Comercial §4.11 + §11 #11 — "Cliente farma exige cronograma fixo, mas planilha não emite lembrete automático → lab esquece visita programada → cliente farma sai com cara de raiva" + "Cliente farma exige certificado em 3 dias úteis — lab descobre que prazo apertado quebra fluxo manual; signatário gargalo materializa"
- **Sintoma observável:** Patrícia liga "preciso do certificado X até 3ª feira pra aprovar o lote"; lab vê na sexta; Marcos está com pilha de 20; entrega na 4ª; cliente farma multa contratual + pondera trocar de fornecedor
- **Personas mais afetadas:** Marcos (signatário sobrecarregado), Sandra (RT testemunha), Roldão (cliente em risco), Patrícia (representa exigência)
- **Dimensões:**
  - **Agudez 4/5** — alta; multa contratual + risco de perder cliente
  - **Frequência 5-20/mês** (=10) — depende da concentração de cliente farma; alta quando ativa
  - **DAP 200/mês inferido** (auto-reportado-estimado R$ 400 → deflacionado R$ 200)
  - **Solvability 3/5** — cronograma anual com lembrete + SLA por cliente + fila priorizada do signatário — moderado
  - **Reach 35%** — só atinge labs com cliente farma/automotivo; mas decisivo
  - **Evitabilidade não (=1)** — workaround atual (planilha + memória do Marcos) é o que falha
- **Score:** (4 × 10 × 0,35 × 200) ÷ (3 × 1) = **933**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §4.11 + §11 #11 + Persona Patrícia §"O que ela rejeita (e bloqueia compra)" + JTBD-044 (contratos recorrentes — alerta 60-90d) + D-014
- **Implicação pra MVP:** ENTRA (cronograma anual + lembrete — boa parte é Dor #02 com perfil farma; SLA do signatário pode ficar MVP-2)
- **Módulo provável:** CRM (contratos anuais) + Operação (priorização)
- **Vínculo com JTBD:** JTBD-044, JTBD-092 (proposta renovação automática), BIG-10

---

### Dor #15: Comissões calculadas em planilha frágil — 3-5 dias do mês + brigas mensais
- **Origem (jornada):** decisão fundadora Roldão 17/05/2026 (`dominio-de-negocio.md` §"Módulo de Comissões Configuráveis") — não está explícita na Jornada §1-12 porque a Jornada foca em fluxo cliente, mas é decisão fundadora canônica
- **Sintoma observável:** Cláudia (financeiro) passa 3-5 dias do mês mexendo em planilha mestre com fórmulas frágeis; cada colaborador questiona o número ("eu fiz X OS, não fui pago direito"); Roldão paga comissão R$ 500 sobre OS que deu R$ 1.200 de prejuízo invisível (descobre só no DRE do trimestre); regra mudou em maio mas planilha de junho usa regra antiga
- **Personas mais afetadas:** Cláudia (esgotamento mensal), Roldão (paga comissão errada), Rogério (briga por número), Bruno (não confia no holerite), Carlos (motorista UMC mais ainda sem visibilidade)
- **Dimensões:**
  - **Agudez 4/5** — alta — drenante + financeiro + risco trabalhista (R-055 score 12)
  - **Frequência 5-20/mês** (=10) — fechamento mensal + brigas semanais
  - **DAP 350/mês inferido** (auto-reportado-estimado R$ 700 → deflacionado R$ 350) — alto entre empresas com 5+ colaboradores comissionados
  - **Solvability 4/5** — DSL de regra configurável + 8 formas de cálculo (bruto, líquido, valor fixo, etc.) + gatilho por recebimento + simulador "se rodasse hoje" + auditoria de ajuste é trabalho substancial
  - **Reach 75%** — universal entre PME 5-10 pessoas com técnicos/vendedores comissionados
  - **Evitabilidade sim (=2)** — workaround atual (planilha) "funciona" com dor
- **Score:** (4 × 10 × 0,75 × 350) ÷ (4 × 2) = **1.312**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Módulo de Comissões Configuráveis" + JTBD-071 a JTBD-082 (12 jobs) + BIG-09 + R-055/R-056/R-057
- **Implicação pra MVP:** ENTRA (7º gap defensável; configuração + fechamento mensal + auditoria MVP-1; previsões em pipeline MVP-2)
- **Módulo provável:** Comissões (BIG-09)
- **Vínculo com JTBD:** JTBD-071 a JTBD-082, BIG-09

---

### Dor #16: Caixa do técnico + frota descontrolados (adiantamento por WhatsApp; combustível dobrado; multa esquecida vira protesto)
- **Origem (jornada):** decisão fundadora Roldão 17/05/2026 (`dominio-de-negocio.md` §"Controle de Técnico em Campo, Despesas, Frota e UMC") + Ciclo Operacional §5.4-5.5
- **Sintoma observável:** Bruno (técnico) sai pra viagem de 3 dias, pede R$ 500 de adiantamento no WhatsApp da Cláudia; volta com bolso cheio de papel amassado; 30% dos comprovantes somem; planilha do RH não bate; carro X com manutenção atrasada quebra na BR; multa chega 2 meses depois, vira protesto + CNH suspensa de Bruno; UMC com pesos-padrão de R$ 100-300k roda sem rastreamento
- **Personas mais afetadas:** Bruno (não-mendigar, não-ser-acusado), Cláudia (planilha lateral interminável), Carlos (motorista UMC com baixo letramento digital), Roldão (custo invisível + risco patrimonial)
- **Dimensões:**
  - **Agudez 4/5** — alta — operacional + financeira + patrimonial (UMC) + jurídica (multa não paga vira protesto, CNH suspensa)
  - **Frequência >20/mês** (=30) — diário/semanal contínuo
  - **DAP 300/mês inferido** (auto-reportado-estimado R$ 600 → deflacionado R$ 300) — alto entre operações com 2+ técnicos de campo
  - **Solvability 4/5** — app mobile + foto + categorização + workflow de aprovação + integração frota (KM, manutenção, multa) é trabalho substancial; integração SENATRAN incerta
  - **Reach 70%** — universal em quem opera campo (perfil A/B/C/D que faz campo); irrelevante em lab puro de bancada
  - **Evitabilidade não (=1)** — workaround atual é precisamente o que produz R-043 + R-044 + R-045 + R-046 + R-047
- **Score:** (4 × 30 × 0,70 × 300) ÷ (4 × 1) = **6.300**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Controle de Técnico em Campo" + Jornada §5.4-5.5 + JTBD-060 a JTBD-070 (11 jobs) + BIG-08 + R-043 a R-047 (5 riscos novos da decisão)
- **Implicação pra MVP:** ENTRA (6º gap defensável; adiantamento + prestação + KM + manutenção alerta MVP-1; TCO consolidado MVP-2)
- **Módulo provável:** Frota+UMC+Caixa do Técnico (BIG-08)
- **Vínculo com JTBD:** JTBD-060 a JTBD-070, BIG-08

---

### Dor #17: Cliente não-acreditado confunde "selo INMETRO" com "certificado de calibração" (multa IPEM + lab acusado)
- **Origem (riscos):** R-040 score 12 — "Cliente final do tenant esquece de fazer verificação periódica INMETRO obrigatória (balança comercial — anual via IPEM). Cliente leva multa do IPEM e culpa o software" + Jornada §10.1 "Confusão cliente final entre 'selo INMETRO' e 'certificado de calibração'"
- **Sintoma observável:** João-Sênior (dono de açougue) acha que "calibrou a balança" = está em dia com IPEM; verifica certificado de calibração na parede; 6 meses depois o IPEM aparece, multa o açougue porque verificação periódica anual estava vencida; João liga revoltado pro Roldão "eu paguei vocês!"; lab fica acusado injustamente; cliente vai pra concorrente
- **Personas mais afetadas:** João-Sênior (cliente final low-tech multado), Roldão (acusado), Sandra (gerente que cobra renovação), Letícia (atende reclamação)
- **Dimensões:**
  - **Agudez 4/5** — perda de cliente + Reclame Aqui + dano reputacional
  - **Frequência 1-4/mês** (=2) — 1-3 casos/mês na empresa-modelo que atende balança comercial
  - **DAP 100/mês inferido** (auto-reportado-estimado R$ 200 → deflacionado R$ 100) — baixo-moderado porque o dono geralmente NÃO percebe que isso é dor evitável
  - **Solvability 1/5** — calendário de verificação periódica IPEM separado de calibração + nota no certificado "esta calibração NÃO substitui a verificação INMETRO obrigatória" + alerta 90/60/30 dias é trivial
  - **Reach 60%** — só atinge labs que atendem balança comercial (varejo); mas é fração grande do mercado BR
  - **Evitabilidade sim (=2)** — workaround atual ("ninguém faz") tolera a dor
- **Score:** (4 × 2 × 0,60 × 100) ÷ (1 × 2) = **240**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` R-040 score 12 + Jornada §10.1 + Persona João-Sênior §"Frase-chave" (a confirmar) + JTBD-012 (saber a hora de cobrar verificação IPEM) + BIG-06 (Metrologia Legal + Voluntária no mesmo pacote) + D-019
- **Implicação pra MVP:** ENTRA (BIG-06 é decisão fundadora MVP-1; aviso no certificado é POC de 1 dia)
- **Módulo provável:** Metrologia + CRM (calendário de verificação)
- **Vínculo com JTBD:** JTBD-012, BIG-06

---

### Dor #18: Selo INMETRO/lacre sem rastreabilidade individual (multa IPEM + risco fraude metrológica)
- **Origem (decisão fundadora):** Roldão 17/05/2026 (`dominio-de-negocio.md` §"Módulo de Estoque Completo para Assistência Técnica") + R-051 + R-052
- **Sintoma observável:** Bruno aplica lacre na balança do cliente após reparo; anota número em papel; foto fica solta no WhatsApp; controle de estoque de lacre só na cabeça do técnico; IPEM aparece "cadê o selo 12345 que vocês aplicaram em maio?"; Sandra vasculha 30 minutos sob pressão de fiscal na sala; risco real de multa + responsabilidade legal (selo aplicado em equipamento errado = fraude metrológica — R-052)
- **Personas mais afetadas:** Bruno (técnico aplicador), Sandra (RT responde fiscal), Roldão (responsabilidade), Auditor IPEM (fiscaliza)
- **Dimensões:**
  - **Agudez 5/5** — multa IPEM + risco jurídico (fraude metrológica é crime)
  - **Frequência 1-4/mês** (=2) — fiscalização IPEM esporádica mas alta-consequência
  - **DAP 150/mês inferido** (auto-reportado-estimado R$ 300 → deflacionado R$ 150) — moderado entre quem aplica selo INMETRO (subset do ICP)
  - **Solvability 2/5** — controle individual por número de série + foto obrigatória + workflow de perda + busca por número é POC moderado
  - **Reach 50%** — só atinge labs que aplicam lacre/selo INMETRO (assistência técnica de balança comercial); fora do escopo de lab puro de bancada
  - **Evitabilidade não (=1)** — workaround atual (planilha lateral) não resiste a fiscalização
- **Score:** (5 × 2 × 0,50 × 150) ÷ (2 × 1) = **375**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Módulo de Estoque…" + JTBD-101 a JTBD-103 + JTBD-108 (responder fiscal em 30s) + BIG-12 + R-051/R-052
- **Implicação pra MVP:** ENTRA (9º gap defensável; rastreabilidade individual + foto obrigatória + busca por número MVP-1)
- **Módulo provável:** Estoque com lacre/selo (BIG-12)
- **Vínculo com JTBD:** JTBD-101, JTBD-103, JTBD-108, BIG-12

---

### Dor #19: Registro técnico em WhatsApp/caderno viola cláusula 7.5.1 (NC permanente silenciosa)
- **Origem (jornada):** §6.bis (Violações regulatórias silenciosas) — "Registro em WhatsApp NÃO cumpre cláusula 7.5.1 — mensagem pode ser apagada, conta encerrada, conversa exportada com perda. Caderno físico também viola (não tem timestamp confiável nem assinatura inequívoca). Violação silenciosa permanente"
- **Sintoma observável:** Bruno em campo manda foto + áudio "achei isso, posso seguir?" pro Marcos no WhatsApp; Marcos responde "sim"; 6 meses depois cliente reclama, foto sumiu do WhatsApp (conta encerrada / exportação perde metadado); auditor Cgcre pede evidência → não tem; OU caderno de campo do Bruno tem anotação a lápis ilegível
- **Personas mais afetadas:** Bruno (executor), Marcos (signatário aprova), Sandra (RT testemunha NC), Roldão (responsabilidade), Auditor Cgcre
- **Dimensões:**
  - **Agudez 4/5** — NC ativa permanente como Dor #04, mas em fluxo de campo (não cálculo)
  - **Frequência >20/mês** (=30) — todo dia de campo gera registro em WhatsApp/caderno
  - **DAP 150/mês inferido** (auto-reportado-estimado R$ 300 → deflacionado R$ 150) — moderado; muitos donos não percebem o risco até auditoria
  - **Solvability 2/5** — app mobile com timestamp confiável + foto com metadado + assinatura técnica é viável; offline-first robusto é mais complexo (MVP-2)
  - **Reach 70%** — universal em quem opera campo (perfil A/B/C); irrelevante em D puro
  - **Evitabilidade não (=1)** — workaround atual é a violação
- **Score:** (4 × 30 × 0,70 × 150) ÷ (2 × 1) = **6.300**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §5.5 + §6.bis (cláusula 7.5.1) + JTBD-022 (offline) + JTBD-024 (assinatura no celular) + JTBD-109 (registro offline com sincronização) + BIG-05
- **Implicação pra MVP:** ENTRA (app web responsivo + foto com metadado + assinatura touch MVP-1; offline-first robusto MVP-2)
- **Módulo provável:** Operação (mobile/campo) + Metrologia (registros)
- **Vínculo com JTBD:** JTBD-022, JTBD-024, JTBD-109, BIG-05

---

### Dor #20: Cliente "morre" no CRM após calibração (sem CRM contínuo) — descoberta tardia da migração pra concorrente
- **Origem (decisão fundadora):** Roldão 17/05/2026 (`dominio-de-negocio.md` §"Cliente 360°, CRM Contínuo e Automações") + Jornada §1 "1 a 3 clientes finais perdidos por trimestre"
- **Sintoma observável:** João (cliente final) calibra em janeiro; recebe certificado; lab "esquece" dele; em janeiro do ano seguinte João renova com concorrente que mandou WhatsApp; Roldão descobre 1 ano depois quando puxa lista do ano "ué, cadê esse?"; sem alerta de cliente inativo >180d; sem oportunidade automática de "equipamento sem manutenção >12 meses"
- **Personas mais afetadas:** Roldão (perda silenciosa de receita), Rogério (vendedor não recebe alerta), Sandra (não monitora ciclo cliente), todas as personas internas
- **Dimensões:**
  - **Agudez 4/5** — alta; 1-3 clientes/trimestre × LTV médio = R$ 30-90k/ano em receita perdida silenciosamente
  - **Frequência 5-20/mês** (=10) — clientes inativando-se continuamente
  - **DAP 300/mês inferido** (auto-reportado-estimado R$ 600 → deflacionado R$ 300) — alto entre quem PERCEBE; dono geralmente subestima
  - **Solvability 3/5** — Cliente 360° em 1 tela + alerta de inativo >180d + oportunidade automática "equipamento sem manutenção" é trabalho moderado; depende de BIG-10 + BIG-11
  - **Reach 90%** — universal em PME
  - **Evitabilidade sim (=2)** — workaround atual (cabeça do dono + planilha) tolera
- **Score:** (4 × 10 × 0,90 × 300) ÷ (3 × 2) = **1.800**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Cliente 360°…" + Jornada §1 "1 a 3 clientes finais perdidos por trimestre" + JTBD-083 (lista priorizada) + JTBD-090 (alerta cliente inativo) + JTBD-096 (oportunidade auto pós-12m) + JTBD-091 (Cliente 360° em 1 tela) + BIG-10
- **Implicação pra MVP:** ENTRA (8º gap defensável; Cliente 360° em 1 tela + alerta inativo MVP-1; campanha de reativação MVP-2)
- **Módulo provável:** CRM (BIG-10)
- **Vínculo com JTBD:** JTBD-083, JTBD-090, JTBD-091, JTBD-096, BIG-10

---

## Por persona — top 3 dores e score médio

> Score médio calculado sobre as dores que afetam diretamente a persona (não inclui dores onde a persona aparece como afetada secundária).

| Persona | Top 3 dores (por ID) | Score médio das top 3 |
|---|---|---|
| **Roldão (dono)** | #02 (28.500), #10 (8.750), #04 (8.250) | **15.166** |
| **Sandra (RT/gerente)** | #07 (3.000), #13 (400), #03 (2.400) | **1.933** |
| **Letícia (atendente)** | #01 (8.100), #05 (2.869), #20 (1.800) | **4.256** |
| **Bruno (técnico campo)** | #16 (6.300), #19 (6.300), #08 (1.000) | **4.533** |
| **Marcos (metrologista/signatário)** | #04 (8.250), #07 (3.000), #03 (2.400) | **4.550** |
| **Cláudia (financeiro)** | #09 (3.187), #11 (2.000), #15 (1.312) | **2.166** |
| **Rogério (vendedor)** | #02 (28.500), #20 (1.800), #15 (1.312) | **10.537** |
| **Carlos (motorista UMC)** | #16 (6.300), #15 (1.312), #08 (1.000) | **2.870** |
| **João (cliente final eng.)** | #05 (2.869), #02 (28.500), #20 (1.800) | **11.056** |
| **Auditor Cgcre/IPEM** | #03 (2.400), #06 (3.000), #18 (375) | **1.925** |
| **Patrícia (farma)** | #13 (400), #14 (933), #03 (2.400) | **1.244** |
| **João-Sênior (low-tech açougue)** | #17 (240), #02 (28.500), #05 (2.869) | **10.536** |
| **Bruna (técnica)** | #19 (6.300), #16 (6.300), #08 (1.000) | **4.533** |
| **Roldão Sênior 65+ (PME veterano)** | #12 (4.500), #02 (28.500), #09 (3.187) | **12.062** |

**Leitura:**
- **Persona com maior dor agregada:** Roldão (15.166) — confirma "founder is customer" e Painel do Dono como diferencial estratégico.
- **Personas com dor agregada >10k:** Roldão Sênior 65+ (12.062), João eng (11.056), Rogério (10.537), João-Sênior (10.536) — quatro perfis cuja dor é resolvida primariamente pela Dor #02 (recalibração esquecida). Confirma que CRM contínuo + automação é o eixo de venda transversal.
- **Persona com dor agregada mais baixa:** Patrícia (1.244) — não porque ela "dói pouco", mas porque atinge subset minoritário (40% Reach); quando atinge, é decisivo (cliente farma).
- **Carlos (motorista UMC)** entrou no mapa em 17/05/2026 e ainda é sub-representado em JTBDs — risco de cobertura na onda 1 de entrevistas.

---

## Por módulo provável — dores relacionadas e score acumulado

| Módulo | Dores relacionadas (ID) | Score acumulado |
|---|---|---|
| **CRM / Cliente 360° (BIG-10)** | #02 (28.500), #05 (2.869), #14 (933), #20 (1.800), #11 (parcial 1.000) | **35.102** |
| **Cadastros base / Cliente** | #01 (8.100) | **8.100** |
| **Fiscal / NFS-e (BIG-04)** | #10 (8.750), #09 (parcial 1.593) | **10.343** |
| **Metrologia (cálculo + emissão + padrões + assinatura)** | #03 (2.400), #04 (8.250), #06 (3.000), #07 (3.000) | **16.650** |
| **Frota + UMC + Caixa do técnico (BIG-08)** | #16 (6.300), #08 (parcial 500) | **6.800** |
| **Comissões (BIG-09)** | #15 (1.312) | **1.312** |
| **Estoque com lacre/selo (BIG-12)** | #18 (375) | **375** |
| **Operação (OS + agenda + mobile)** | #05 (parcial 1.434), #08 (parcial 500), #19 (6.300) | **8.234** |
| **Financeiro (conciliação + cobrança)** | #09 (1.593), #11 (1.000) | **2.593** |
| **Qualidade (NC, auditoria, reclamação 7.9, competência)** | #13 (400), #07 (parcial 1.500) | **1.900** |
| **Painel do Dono (transversal)** | #12 (4.500) | **4.500** |
| **Automações (BIG-11)** | #02 (parcial 14.250), #11 (parcial 1.000), #20 (parcial 900) | **16.150** |
| **Metrologia Legal (BIG-06)** | #17 (240) | **240** |

**Leitura:**
- **Módulo com maior score acumulado:** CRM/Cliente 360° (35.102) + Automações (16.150) — somam 51.252; coração da venda. **Decisão fundadora confirmada.**
- **Metrologia (16.650)** vem em 3º — pilar técnico defensável (BIG-02).
- **Fiscal/NFS-e (10.343)** com cutover 01/09/2026 — escassez de oferta no mercado (gap confirmado em Concorrentes §3-4).
- **Cadastros base (8.100)** — foundation que destrava CRM + Fiscal + Operação.
- Módulos baixos (Estoque 375, Metrologia Legal 240) NÃO indicam pouca importância — indicam Reach menor (subset do TAM) com Agudez alta quando ativa.

---

## Top 5 dores prioritárias com recomendação MVP

| # | Dor | Score | Recomendação MVP | Justificativa |
|---|---|---|---|---|
| 1 | **#02 — Esquecimento de recalibração (30-50% receita perdida)** | **28.500** | **ENTRA MVP-1 (eixo primário de venda)** | Receita perdida direta R$ 8-12k/mês (Jornada §8). Universal (95% Reach). Solvability baixa (calendário + WhatsApp template). É uma das duas vendas-engatilho (junto com NFS-e). Resolve drama emocional do Roldão #49. Casa com BIG-10 + BIG-11. |
| 2 | **#10 — NFS-e municipal cutover 01/09/2026** | **8.750** | **ENTRA MVP-1 (deadline duro)** | Cutover obrigatório R-016. Gap absoluto BR confirmado (Concorrentes §4 — só FP2 cobre, regional). 100% Reach. Tese central do produto. BaaS fiscal (Focus/PlugNotas) reduz Solvability pra 3. Sem isso, lab perde capacidade fiscal em 01/09/2026. |
| 3 | **#04 — Word/Excel/macros = NC permanente cláusula 7.11** | **8.250** | **ENTRA MVP-1 (pitch real do produto)** | Jornada §6.5 define explicitamente como "o pitch real do Aferê — tirar o lab da NC, não 'facilitar o cálculo'". Atinge 55% Reach (planilha + Cali sem dossiê). Frequência altíssima (todo certificado emitido). Sem isso, o produto não tem narrativa metrológica defensável. |
| 4 | **#01 — Cadastro digitado 4-6 vezes** | **8.100** | **ENTRA MVP-1 (foundation)** | Foundation. Sem cliente único, CRM (#02 e #20), NFS-e (#10) e Cobrança (#11) não funcionam. Solvability baixa (2/5). 90% Reach. Promovido a BIG-07. Resolver isso destrava 5 outras dores. |
| 5 | **#19 — Registro técnico em WhatsApp = NC 7.5.1 silenciosa** | **6.300** | **ENTRA MVP-1 parcial (web responsivo + foto com metadado; offline robusto = MVP-2)** | Universal em quem opera campo (70% Reach). Frequência altíssima (todo dia de campo). Violação ativa permanente como #04 — narrativa de NC silenciosa vende. Cobertura mínima MVP-1 (app web + foto + assinatura touch) é o que faz BIG-05; offline-first verdadeiro fica MVP-2 conforme `jobs-to-be-done.md` §BIG-05. |

---

## Dores que NÃO entram no MVP (non-goals)

> Pelo menos 5 dores reais que ficam fora do MVP-1. Alinha com Anti-jobs ANTI-01 a ANTI-11 (`jobs-to-be-done.md` §5).

| Dor (descrição curta) | Origem | Por que NÃO entra no MVP-1 | Tratamento futuro |
|---|---|---|---|
| **Folha de pagamento + ponto + holerite + férias da equipe** | Jornada §2.2 (acúmulo de papel + RH) + Persona Cláudia menciona "RH é problema" | **ANTI-01**: domínio RH completo é mercado próprio (Senior, ADP, Sankhya RH); ROI baixo pro ICP; complexidade trabalhista alta | Integração externa com Pontomais/Sankhya RH (MVP-3+). Comissões (#15) NÃO entra aqui — é módulo próprio BIG-09. |
| **Pagamento online com cartão direto (gateway próprio)** | Jornada §7.2 + R-025 (PCI-DSS 4.0.1) | **ANTI-02**: vira PCI-DSS escopo full; custo de auditoria anual desproporcional ao ticket; risco regulatório alto | Usar PSP terceiro (Asaas, Pagar.me, Stripe) — escopo SAQ A; integração leve no MVP-2 |
| **BI sofisticado / dashboards customizáveis / query SQL pelo usuário** | Persona Roldão pediria em algum momento "quero ver gráfico de X por Y" | **ANTI-05 + ANTI-09**: gigantes resolvem melhor (Metabase, PowerBI, Looker); custo de UX alto; vira plataforma e não produto opinativo | Dashboards fixos por papel no MVP-1 (JTBD-013, JTBD-097); export CSV/Parquet pra BI externo via API no MVP-2 |
| **Mensageria interna entre técnicos / chat / Slack-mini** | Jornada §5 grupo WhatsApp interno + Persona Bruna menciona "comunicação difícil" | **ANTI-08**: mercado saturado (WhatsApp já usado); custo de UX alto; baixo valor diferencial | Equipes continuam usando WhatsApp pessoal/grupo; produto só notifica eventos relevantes |
| **Calendário/agenda como produto (não só integração)** | Jornada §5.3 Google Calendar individual + JTBD-009 | **ANTI-10**: Google Calendar e Outlook resolvem; reinventar não agrega; UX é caro | Integração bidirecional Google Calendar (técnico vê agenda da OS no calendário pessoal) — MVP-2 |
| **Customização individual por tenant ("o cliente X precisa de uma tela diferente")** | Risco R-001 + Persona Roldão tendência natural | **ANTI-11 CRÍTICO**: customização individual mata produto opinativo + dispara dívida técnica exponencial + materializa R-001 (founder is customer virando "cada cliente é customer") | Única forma: **configuração estruturada** (switches, perfis, checklists). Cliente que quer mais paga **setup** que vira config **nativa pra todos** — não código exclusivo. |
| **Treinamento de técnico júnior / trilha de procedimento embutida** | JTBD-033 + JTBD-050 + JTBD-055 | Solvability 5/5 (exige curadoria técnica especializada de centenas de procedimentos por grandeza/faixa); ROI MVP-1 baixo | MVP-3 — biblioteca de procedimentos PT-BR é diferencial estratégico de longo prazo |
| **Pesquisa NPS estruturada + relatórios de satisfação** | Jornada §5.10 (pós-venda inexistente) + JTBD-085 (parcial — só disparo de retenção) | Solvability moderada (3/5) mas Reach baixo no MVP-1 (donos PME geralmente NÃO sabem operar NPS); risco de feature "ninguém usa" | MVP-2 — disparo de tarefa de retenção em NPS negativo entra com BIG-11, mas formulário NPS estruturado fica MVP-2 |
| **Hardware proprietário (calibrador, sensor, dispositivo de coleta)** | JTBD-023 (OCR/conexão direta) + Concorrentes Beamex/Fluke | **ANTI-06**: não somos fabricante; Beamex/Fluke/Presys já fazem | Integrar via Bluetooth/USB com hardware existente — MVP-2/3 |
| **Gestão clínica/análises clínicas humanas (LIS)** | Patrícia (farma) pode pedir; cliente hospital pode pedir | **ANTI-03**: domínio próprio (CFM 1821/2007, SBIS-CFM); ABNT NBR ISO 15189 ≠ 17025 | Fora de escopo permanente; se cliente farma exigir, integração leitura-only |

---

## Saída esperada

- **Top 5 dores prioritárias com score:** ver tabela acima — #02 (28.500), #10 (8.750), #04 (8.250), #01 (8.100), #19 (6.300).
- **Recomendação de MVP-1 baseada em score:** 5 dores acima ENTRAM. 7 dores adicionais (#02 já listada; #06, #07, #12, #15, #16, #18, #20) ENTRAM total OU parcial conforme tabela ranqueada. **13 dores no MVP-1; 7 no MVP-2/3.**
- **Lista de dores fora de escopo:** ver §"Dores que NÃO entram no MVP" acima — 10 categorias alinhadas a ANTI-01 a ANTI-11.

---

## Próximos passos (re-rankear pós-Onda 1)

1. **Validar números na Onda 1 de entrevistas** (3-5 empresas). Cada dor acima precisa de pelo menos:
   - 1 citação literal substituindo `[INFERÊNCIA — validar em onda 1]`.
   - Frequência real auto-reportada.
   - DAP real auto-reportada (deflacionar 50% como regra Auditor 6).
   - Reach corrigido após mapear o ICP real.
2. **Re-rankear top 5.** Score atual é palpite ponderado por evidência interna; pós-entrevistas pode mudar ordem (especialmente Dor #02 vs #10 — qual é o gatilho de compra real?).
3. **Detectar dores omitidas.** As 20 acima cobrem 4 ciclos + 4 decisões fundadoras + 14 personas; entrevista pode revelar uma 21ª (provável áreas: contrato anual farma, licitação pública §4.10, atestado de capacidade técnica §4.12).
4. **Alimentar `sintese-final.md`** com top 5 + recomendação MVP-1.
5. **Alimentar `validacao-ativa.md`** com perguntas-chave por dor (já tem rascunho em Jornada §15).
