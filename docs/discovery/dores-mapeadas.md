# Discovery — Dores mapeadas

> **Artefato Rodada 0** (agente sintetiza, a partir das entrevistas). Dores ranqueadas por **6 dimensões** (Auditor 6 v2):
>
> **Versão pré-entrevistas, baseada em síntese.** Esta primeira passagem cruza `jornada-atual-sem-produto.md` (4 ciclos + 14 dores D-NNN + custo R$ 35-50k/mês), `jobs-to-be-done.md` (~109 JTBDs + 12 Big Jobs), `personas-detalhadas.md` (14 personas) e `riscos.md` (57 riscos R-NNN). **Nenhuma entrevista real ainda foi feita.** Tudo abaixo é inferência rastreada a evidência interna (ciclo/passo da jornada + JTBD + risco). **Top dores serão re-rankeadas após Onda 1 com citações literais.**
>
> **⚠️ Versão pós-auditoria 12 agentes (17/05/2026 noite).** Top 5 re-rankeado: removido halo founder-customer (Aud-13 + Aud-19). Reach deflacionado 20% onde Reach ≥ 0,80 sem citação literal. Segunda deflação DAP 30% em dores vinculadas a decisões fundadoras (DF-1 Frota+UMC+Caixa, DF-2 Comissões, DF-3 Cliente 360°, DF-4 Estoque com lacre/selo). Top 5 antes: 4 das 5 eram dores vinculadas a DF (improbabilidade estatística < 5%). Top 5 corrigido: apenas 1 dor-DF permanece (#02, e ainda assim com Reach deflacionado).

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
> - **Segunda deflação DAP 30% adicional** aplicada em dores vinculadas a decisões fundadoras (Aud-13 + Aud-19, 17/05/2026): vínculo com DF pode ter inflado o palpite original.
> - Evitabilidade "sim" = 2 (workaround existe), "não" = 1 (não existe ou viola norma).
> - Score: (A × F × R × DAP) ÷ (S × E) — divisão usa Solvability como custo de implementação e Evitabilidade como urgência inversa.
> - **Marcação `[INFERÊNCIA — validar em onda 1]`:** dor cuja existência é razoavelmente garantida pela jornada, mas cujos números (frequência, DAP, reach) são palpite. **Toda dor abaixo está marcada porque não temos entrevista real ainda** — a marcação distingue "inferência forte com 3+ fontes internas" de "inferência fraca com 1 fonte".

Ranking não é cego ao score — sempre justificar com citação literal da entrevista (a vir).

---

## Dores ranqueadas (20 dores — pré-entrevistas, pós-auditoria 17/05/2026)

> **Cobertura por ciclo:** 4 dores no Ciclo Comercial · 5 dores no Ciclo Operacional · 5 dores no Ciclo Metrológico · 3 dores no Ciclo Financeiro · 3 dores transversais.
> **Cobertura por decisão fundadora:** Frota+UMC+Caixa do Técnico (Dor #08, #16) · Comissões Configuráveis (Dor #15) · Cliente 360°+Automações (Dor #02, #05, #20) · Estoque com lacre/selo INMETRO (Dor #18).

---

### Dor #01: Cadastro de cliente digitado 4 a 6 vezes em sistemas que não conversam
- **Origem (jornada):** Ciclo Comercial §4.8 — "MESMO DADO digitado de 4 a 6 vezes... pior ponto de duplicação da jornada" + violação silenciosa de §6.bis (LGPD art. 33 — sem DPA entre Bling/Cali/Drive)
- **Sintoma observável:** atendente Letícia leva 20 a 45 minutos por cliente novo, criando o mesmo CNPJ em planilha "Clientes.xlsx" + Bling + Cali/Metroex + planilha de OS + grupo WhatsApp; erro de digitação trava NFS-e dias depois, endereço diferente entre sistemas manda técnico pro lugar errado
- **Personas mais afetadas:** Letícia (atendente, sente todos os dias), Cláudia (financeiro, herda o erro fiscal), Roldão (dono, paga horas perdidas), Sandra (RT, perde rastreabilidade), Bruno (técnico, vai pra endereço errado)
- **Dimensões (pós-auditoria):**
  - **Agudez 3/5** — não paralisa empresa mas drena 1-3h por cadastro novo + erros caros depois
  - **Frequência >20/mês** — 5 a 15 clientes novos/mês × 4-6 sistemas; atualizações de dado existente diárias
  - **DAP 150/mês inferido** (auto-reportado-estimado R$ 400 → deflacionado R$ 200 → revisado pra R$ 150 pós-auditoria) — dor universal mas mal-quantificada pelo dono ("é assim mesmo")
  - **Solvability 2/5** — modelo de dados com cliente como entidade única + integração com NFS-e (BaaS Focus/PlugNotas) é viável em poucos sprints
  - **Reach 80%** (era 90% — deflação 20% Aud-13 por ausência de citação literal) — observado em jornada §2.2 como característica de "100% das empresas BR" do ICP, mas alvo de viés do dono que enxerga ICP estreito
  - **Evitabilidade não (=1)** — workaround é o problema; planilha não substitui integração
- **Score:** (3 × 30 × 0,80 × 150) ÷ (2 × 1) = **5.400** (era 8.100 — recalibrado)
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §4.8 "MESMO DADO digitado de 4 a 6 vezes — pior ponto de duplicação da jornada" + Persona Letícia §"O que a deixa louca": "Cliente é cadastrado 4 vezes — em 4 telas diferentes — e ainda assim quando vou achar, sumiu" + JTBD-054 + D-001 + BIG-07 (promovido a Big Job)
- **Implicação pra MVP:** ENTRA (foundation — Cliente 360° começa aqui)
- **Módulo provável:** Cliente / Cadastros base
- **Vínculo com JTBD:** JTBD-054, BIG-07, BIG-10 (Cliente 360°)

---

### Dor #02: Esquecimento de lembrar cliente da próxima calibração (recalibração perdida 30-50%)
- **Origem (jornada):** Ciclo Metrológico §6.12 — "NÃO é sistemático. Empresa-modelo perde 30-50% das recalibrações por esquecimento" + Ciclo Comercial §4.11 (contrato anual farma sem lembrete automático)
- **Sintoma observável:** planilha "Validades.xlsx" + Google Calendar; Rogério (vendedor) e Letícia (atendente) "quando lembram" mandam mensagem manual; cliente final recebe lembrete do concorrente antes; empresa perde 30-50% das recalibrações que tinha direito a renovar
- **Personas mais afetadas:** Roldão (perde receita recorrente), Rogério (perde comissão de renovação), Sandra (não fecha ciclo de qualidade), João (cliente final fica sem certificado válido)
- **Dimensões (pós-auditoria):**
  - **Agudez 5/5** — receita perdida direta; dor canônica do setor de calibração
  - **Frequência 10-30/mês** — 60-180 certificados/mês × 30-50% esquecimento → ~30 oportunidades perdidas/mês na empresa-modelo
  - **DAP 250/mês inferido** (auto-reportado-estimado R$ 800 → deflacionado R$ 400 → segunda deflação 30% pra R$ 250) — ⚠️ **Segunda deflação aplicada (auditoria 17/05/2026 — Aud-13): vínculo com DF-3 (Cliente 360°+Automações) pode ter inflado DAP no primeiro palpite.**
  - **Solvability 2/5** — calendário de recalibração + WhatsApp template aprovado + automação simples
  - **Reach 75%** (era 95% — deflação 20% Aud-13 por Reach inflacionado sem citação literal) — universal em calibração; observado em Jornada §1 e §8 como R$ 8-12k/mês de receita perdida
  - **Evitabilidade não (=1)** — workaround atual (planilha) é exatamente o que falha
- **Score:** (5 × 30 × 0,75 × 250) ÷ (2 × 1) = **14.062** (era 28.500 — recalibrado; aproximadamente 15.000)
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
  - **Reach 85%** — universal em PME 5-10 pessoas; pode cair em perfil D pequeno. **Reach NÃO deflacionado: Letícia é persona presente em qualquer empresa do ICP — dor visível em entrevista direta com atendente.**
  - **Evitabilidade sim (=2)** — workaround atual (responder manualmente) é cansativo mas funciona
- **Score:** (3 × 30 × 0,85 × 150) ÷ (2 × 2) = **2.869**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §5.8 explicitamente "10-30 perguntas/dia" + Persona Letícia §"O que a deixa louca": "10 vezes por dia: 'cadê o orçamento que mandei segunda?'. Eu não sei. Procuro no e-mail, na pasta, no WhatsApp do Roldão" + JTBD-017 (responder cadê certificado sem levantar) + JTBD-091 (Cliente 360° em 1 tela) + D-005
- **Implicação pra MVP:** ENTRA (portal cliente lite + automação de notificação de mudança de status — quick win). **Promovida ao top 5 pós-auditoria (não-DF, persona universal, viés founder-customer baixo).**
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
  - **DAP 350/mês inferido** (auto-reportado-estimado R$ 700 → deflacionado R$ 350) — alto; já pagam Bling/Omie/Conta Azul justamente pra isso. **NÃO recebe segunda deflação: não é DF, é fato regulatório com data fixa.**
  - **Solvability 3/5** — BaaS fiscal (Focus, PlugNotas, TecnoSpeed) resolve a parte BR; integração com OS é nossa
  - **Reach 100%** — universal: toda empresa do ICP emite NFS-e. **Reach NÃO deflacionado: cutover atinge todos.**
  - **Evitabilidade sim (=2)** — Bling/Omie já fazem; gap é integrar com OS de calibração
- **Score:** (5 × 30 × 1,00 × 350) ÷ (3 × 2) = **8.750**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §7.1 (R-016) + Concorrentes §3-4 "GAP CONFIRMADO" — nenhum dos 14 concorrentes nacionais (Cali, Metroex, Calibre, Q-MAN, ConfLab, etc.) tem NFS-e nativa; FP2 cobre só Santa Maria/RS + JTBD-034 + BIG-04 + D-021 + R-016 score 20
- **Implicação pra MVP:** ENTRA (uma das duas vendas-engatilho — junto com Dor #02; tese central do produto per Concorrentes §6). **Top 1 pós-auditoria: fato regulatório com data (01/09/2026) imune a viés founder-customer.**
- **Módulo provável:** Fiscal/NFS-e (BIG-04)
- **Vínculo com JTBD:** JTBD-034, BIG-04

---

### Dor #11: Inadimplência tratada pessoalmente pelo dono (cobrança constrangedora)
- **Origem (jornada):** Ciclo Financeiro §7.5 + §7.6 — "Cobrança vira problema pessoal do dono. Cliente inadimplente é também cliente operacional ativo → conflito interno: cobrar e perder cliente OU atender e nunca receber"
- **Sintoma observável:** Cláudia identifica boleto vencido na planilha "Inadimplentes.xlsx"; manda WhatsApp constrangedor pro cliente; cliente nega ("já paguei!"); escala pro Roldão que liga pessoalmente; Letícia abre nova OS pra cliente bloqueado porque ninguém avisou; receita continua sendo entregue sem entrar
- **Personas mais afetadas:** Roldão (peso emocional), Cláudia (drenagem + sentir-se "chata"), Letícia (erro por desinformação), Rogério (vendedor descobre tarde)
- **⭐ Dor universal NÃO-FUNDADORA — virou Opportunity própria (OP11 Cobrança) no OST pós-auditoria 17/05/2026**
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
- **⭐ Dor universal NÃO-FUNDADORA — virou Opportunity própria (OP12 Painel do Dono) no OST pós-auditoria 17/05/2026**
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
- **Dimensões (pós-auditoria):**
  - **Agudez 4/5** — alta — drenante + financeiro + risco trabalhista (R-055 score 12)
  - **Frequência 5-20/mês** (=10) — fechamento mensal + brigas semanais
  - **DAP 245/mês inferido** (auto-reportado-estimado R$ 700 → deflacionado R$ 350 → segunda deflação 30% pra R$ 245) — ⚠️ **Segunda deflação aplicada (auditoria 17/05/2026 — Aud-13): vínculo com DF-2 (Comissões Configuráveis) pode ter inflado DAP no primeiro palpite.**
  - **Solvability 4/5** — DSL de regra configurável + 8 formas de cálculo + simulador é trabalho substancial
  - **Reach 55%** (era 75% — deflação 20% Aud-13) — só labs que comissionam tecnicamente — [INFERÊNCIA — só labs que comissionam tecnicamente]
  - **Evitabilidade sim (=2)** — workaround atual (planilha) "funciona" com dor
- **Score:** (4 × 10 × 0,55 × 245) ÷ (4 × 2) = **674** (era 1.312 — recalibrado)
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Módulo de Comissões Configuráveis" + JTBD-071 a JTBD-082 (12 jobs) + BIG-09 + R-055/R-056/R-057
- **Implicação pra MVP:** ENTRA (7º gap defensável; configuração + fechamento mensal + auditoria MVP-1; previsões em pipeline MVP-2)
- **Módulo provável:** Comissões (BIG-09)
- **Vínculo com JTBD:** JTBD-071 a JTBD-082, BIG-09

---

### Dor #16: Caixa do técnico + frota descontrolados (adiantamento por WhatsApp; combustível dobrado; multa esquecida vira protesto)
- **Origem (jornada):** decisão fundadora Roldão 17/05/2026 (`dominio-de-negocio.md` §"Controle de Técnico em Campo, Despesas, Frota e UMC") + Ciclo Operacional §5.4-5.5
- **Sintoma observável:** Bruno (técnico) sai pra viagem de 3 dias, pede R$ 500 de adiantamento no WhatsApp da Cláudia; volta com bolso cheio de papel amassado; 30% dos comprovantes somem; planilha do RH não bate; carro X com manutenção atrasada quebra na BR; multa chega 2 meses depois, vira protesto + CNH suspensa de Bruno; UMC com pesos-padrão de R$ 100-300k roda sem rastreamento
- **Personas mais afetadas:** Bruno (não-mendigar, não-ser-acusado), Cláudia (planilha lateral interminável), Carlos (motorista UMC com baixo letramento digital), Roldão (custo invisível + risco patrimonial)
- **Dimensões (pós-auditoria):**
  - **Agudez 4/5** — alta — operacional + financeira + patrimonial (UMC) + jurídica
  - **Frequência >20/mês** (=30) — diário/semanal contínuo
  - **DAP 210/mês inferido** (auto-reportado-estimado R$ 600 → deflacionado R$ 300 → segunda deflação 30% pra R$ 210) — ⚠️ **Segunda deflação aplicada (auditoria 17/05/2026 — Aud-13): vínculo com DF-1 (Frota+UMC+Caixa) pode ter inflado DAP no primeiro palpite.**
  - **Solvability 4/5** — app mobile + foto + categorização + workflow + integração frota é trabalho substancial
  - **Reach 55%** (era 70% — deflação 20% Aud-13) — só labs com 3+ técnicos de campo + frota própria + UMC — [INFERÊNCIA — só labs com 3+ técnicos de campo + frota própria + UMC]
  - **Evitabilidade não (=1)** — workaround atual é precisamente o que produz R-043 + R-044 + R-045 + R-046 + R-047
- **Score:** (4 × 30 × 0,55 × 210) ÷ (4 × 1) = **3.465** (era 6.300 — recalibrado)
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Controle de Técnico em Campo" + Jornada §5.4-5.5 + JTBD-060 a JTBD-070 (11 jobs) + BIG-08 + R-043 a R-047
- **Implicação pra MVP:** ENTRA parcial pós-auditoria (adiantamento + prestação + KM MVP-1; **TCO consolidado e frota completa movem pra MVP-2**)
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
  - **Solvability 1/5** — calendário de verificação periódica IPEM separado de calibração + nota no certificado + alerta 90/60/30 dias é trivial
  - **Reach 60%** — só atinge labs que atendem balança comercial (varejo); mas é fração grande do mercado BR
  - **Evitabilidade sim (=2)** — workaround atual ("ninguém faz") tolera a dor
- **Score:** (4 × 2 × 0,60 × 100) ÷ (1 × 2) = **240**
- **Citações:** `[INFERÊNCIA — validar em onda 1]` R-040 score 12 + Jornada §10.1 + Persona João-Sênior §"Frase-chave" (a confirmar) + JTBD-012 (saber a hora de cobrar verificação IPEM) + BIG-06 + D-019
- **Implicação pra MVP:** ENTRA (BIG-06 é decisão fundadora MVP-1; aviso no certificado é POC de 1 dia)
- **Módulo provável:** Metrologia + CRM (calendário de verificação)
- **Vínculo com JTBD:** JTBD-012, BIG-06

---

### Dor #18: Selo INMETRO/lacre sem rastreabilidade individual (multa IPEM + risco fraude metrológica)
- **Origem (decisão fundadora):** Roldão 17/05/2026 (`dominio-de-negocio.md` §"Módulo de Estoque Completo para Assistência Técnica") + R-051 + R-052
- **Sintoma observável:** Bruno aplica lacre na balança do cliente após reparo; anota número em papel; foto fica solta no WhatsApp; controle de estoque de lacre só na cabeça do técnico; IPEM aparece "cadê o selo 12345 que vocês aplicaram em maio?"; Sandra vasculha 30 minutos sob pressão de fiscal na sala; risco real de multa + responsabilidade legal (selo aplicado em equipamento errado = fraude metrológica — R-052)
- **Personas mais afetadas:** Bruno (técnico aplicador), Sandra (RT responde fiscal), Roldão (responsabilidade), Auditor IPEM (fiscaliza)
- **Dimensões (pós-auditoria):**
  - **Agudez 5/5** — multa IPEM + risco jurídico (fraude metrológica é crime)
  - **Frequência 1-4/mês** (=2) — fiscalização IPEM esporádica mas alta-consequência
  - **DAP 105/mês inferido** (auto-reportado-estimado R$ 300 → deflacionado R$ 150 → segunda deflação 30% pra R$ 105) — ⚠️ **Segunda deflação aplicada (auditoria 17/05/2026 — Aud-13): vínculo com DF-4 (Estoque com lacre/selo) pode ter inflado DAP no primeiro palpite.**
  - **Solvability 2/5** — controle individual por número de série + foto obrigatória + workflow de perda + busca por número é POC moderado
  - **Reach 50%** (mantido — Aud-13 considerou reconhecido como subset realista) — só atinge labs que aplicam lacre/selo INMETRO
  - **Evitabilidade não (=1)** — workaround atual (planilha lateral) não resiste a fiscalização
- **Score:** (5 × 2 × 0,50 × 105) ÷ (2 × 1) = **262** (era 375 — recalibrado)
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Módulo de Estoque…" + JTBD-101 a JTBD-103 + JTBD-108 + BIG-12 + R-051/R-052
- **Implicação pra MVP:** ENTRA (9º gap defensável; rastreabilidade individual + foto obrigatória + busca por número MVP-1)
- **Módulo provável:** Estoque com lacre/selo (BIG-12)
- **Vínculo com JTBD:** JTBD-101, JTBD-103, JTBD-108, BIG-12

---

### Dor #19: Registro técnico em WhatsApp/caderno viola cláusula 7.5.1 (NC permanente silenciosa) + frota sem TCO
- **Origem (jornada):** §6.bis (Violações regulatórias silenciosas) — "Registro em WhatsApp NÃO cumpre cláusula 7.5.1 — mensagem pode ser apagada, conta encerrada, conversa exportada com perda. Caderno físico também viola"
- **Sintoma observável:** Bruno em campo manda foto + áudio "achei isso, posso seguir?" pro Marcos no WhatsApp; Marcos responde "sim"; 6 meses depois cliente reclama, foto sumiu do WhatsApp; auditor Cgcre pede evidência → não tem; OU caderno de campo do Bruno tem anotação a lápis ilegível. **Aspecto frota TCO (custo total de operação por veículo) também herda halo founder-customer.**
- **Personas mais afetadas:** Bruno (executor), Marcos (signatário aprova), Sandra (RT testemunha NC), Roldão (responsabilidade), Auditor Cgcre
- **Dimensões (pós-auditoria):**
  - **Agudez 4/5** — NC ativa permanente como Dor #04, mas em fluxo de campo (não cálculo)
  - **Frequência >20/mês** (=30) — todo dia de campo gera registro em WhatsApp/caderno
  - **DAP 105/mês inferido** (auto-reportado-estimado R$ 300 → deflacionado R$ 150 → segunda deflação 30% pra R$ 105) — ⚠️ **Segunda deflação aplicada (auditoria 17/05/2026 — Aud-13): vínculo com DF-1 (Frota TCO) pode ter inflado DAP no primeiro palpite.**
  - **Solvability 2/5** — app mobile com timestamp confiável + foto com metadado é viável; offline-first robusto é MVP-2
  - **Reach 55%** (era 70% — deflação 20% Aud-13) — só labs com frota — [INFERÊNCIA — só labs com frota própria + técnicos campo]
  - **Evitabilidade não (=1)** — workaround atual é a violação
- **Score:** (4 × 30 × 0,55 × 105) ÷ (2 × 1) = **3.465** (era 6.300 — recalibrado)
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Jornada §5.5 + §6.bis (cláusula 7.5.1) + JTBD-022 (offline) + JTBD-024 (assinatura no celular) + JTBD-109 + BIG-05
- **Implicação pra MVP:** ENTRA (app web responsivo + foto com metadado + assinatura touch MVP-1; offline-first robusto MVP-2). **Pós-auditoria: desceu do top 5 (era #5) pra top 8 — removido halo founder-customer.**
- **Módulo provável:** Operação (mobile/campo) + Metrologia (registros)
- **Vínculo com JTBD:** JTBD-022, JTBD-024, JTBD-109, BIG-05

---

### Dor #20: Cliente "morre" no CRM após calibração (sem CRM contínuo) — descoberta tardia da migração pra concorrente
- **Origem (decisão fundadora):** Roldão 17/05/2026 (`dominio-de-negocio.md` §"Cliente 360°, CRM Contínuo e Automações") + Jornada §1 "1 a 3 clientes finais perdidos por trimestre"
- **Sintoma observável:** João (cliente final) calibra em janeiro; recebe certificado; lab "esquece" dele; em janeiro do ano seguinte João renova com concorrente que mandou WhatsApp; Roldão descobre 1 ano depois quando puxa lista do ano "ué, cadê esse?"; sem alerta de cliente inativo >180d; sem oportunidade automática de "equipamento sem manutenção >12 meses"
- **Personas mais afetadas:** Roldão (perda silenciosa de receita), Rogério (vendedor não recebe alerta), Sandra (não monitora ciclo cliente), todas as personas internas
- **Dimensões (pós-auditoria):**
  - **Agudez 4/5** — alta; 1-3 clientes/trimestre × LTV médio = R$ 30-90k/ano em receita perdida silenciosamente
  - **Frequência 5-20/mês** (=10) — clientes inativando-se continuamente
  - **DAP 210/mês inferido** (auto-reportado-estimado R$ 600 → deflacionado R$ 300 → segunda deflação 30% pra R$ 210) — ⚠️ **Segunda deflação aplicada (auditoria 17/05/2026 — Aud-13): vínculo com DF-4/DF-3 (Estoque + Cliente 360°) pode ter inflado DAP no primeiro palpite.**
  - **Solvability 3/5** — Cliente 360° em 1 tela + alerta de inativo >180d + oportunidade automática é trabalho moderado
  - **Reach 90%** — universal em PME (Reach mantido — dor não exige perfil específico, atinge qualquer PME)
  - **Evitabilidade sim (=2)** — workaround atual (cabeça do dono + planilha) tolera
- **Score:** (4 × 10 × 0,90 × 210) ÷ (3 × 2) = **1.260** (era 1.800 — recalibrado)
- **Citações:** `[INFERÊNCIA — validar em onda 1]` Decisão fundadora Roldão 17/05/2026 + `dominio-de-negocio.md` §"Cliente 360°…" + Jornada §1 "1 a 3 clientes finais perdidos por trimestre" + JTBD-083 + JTBD-090 + JTBD-096 + JTBD-091 + BIG-10
- **Implicação pra MVP:** ENTRA (8º gap defensável; Cliente 360° em 1 tela + alerta inativo MVP-1; campanha de reativação MVP-2)
- **Módulo provável:** CRM (BIG-10)
- **Vínculo com JTBD:** JTBD-083, JTBD-090, JTBD-091, JTBD-096, BIG-10

---

## Por persona — top 3 dores e score médio (pós-auditoria)

> Score médio calculado sobre as dores que afetam diretamente a persona (não inclui dores onde a persona aparece como afetada secundária). **Tabela atualizada com scores pós-auditoria 17/05/2026.**

| Persona | Top 3 dores (por ID) | Score médio das top 3 |
|---|---|---|
| **Roldão (dono)** | #02 (14.062), #10 (8.750), #04 (8.250) | **10.354** |
| **Sandra (RT/gerente)** | #07 (3.000), #03 (2.400), #13 (400) | **1.933** |
| **Letícia (atendente)** | #01 (5.400), #05 (2.869), #20 (1.260) | **3.176** |
| **Bruno (técnico campo)** | #16 (3.465), #19 (3.465), #08 (1.000) | **2.643** |
| **Marcos (metrologista/signatário)** | #04 (8.250), #07 (3.000), #03 (2.400) | **4.550** |
| **Cláudia (financeiro)** | #09 (3.187), #11 (2.000), #15 (674) | **1.953** |
| **Rogério (vendedor)** | #02 (14.062), #20 (1.260), #15 (674) | **5.332** |
| **Carlos (motorista UMC)** | #16 (3.465), #15 (674), #08 (1.000) | **1.713** |
| **João (cliente final eng.)** | #02 (14.062), #05 (2.869), #20 (1.260) | **6.063** |
| **Auditor Cgcre/IPEM** | #06 (3.000), #03 (2.400), #18 (262) | **1.887** |
| **Patrícia (farma)** | #14 (933), #13 (400), #03 (2.400) | **1.244** |
| **João-Sênior (low-tech açougue)** | #02 (14.062), #05 (2.869), #17 (240) | **5.723** |
| **Bruna (técnica)** | #16 (3.465), #19 (3.465), #05 (2.869) | **3.266** |
| **Roldão Sênior 65+ (PME veterano)** | #02 (14.062), #12 (4.500), #09 (3.187) | **7.249** |

**Leitura pós-auditoria:**
- **Roldão (10.354) continua maior dor agregada** — mas a diferença pra outras personas caiu significativamente após remoção do halo founder-customer. Saudável.
- **Personas com dor agregada >5k:** Roldão (10.354), Roldão Sênior (7.249), João eng (6.063), João-Sênior (5.723), Rogério (5.332). **Antes da auditoria, eram 4 personas >10k; agora só 1 — o achatamento confirma que o viés founder-customer estava inflando scores.**
- **Patrícia (1.244) mantém perfil de "dor decisiva quando atinge"** — Reach baixo (35-40%) mas alto valor por cliente farma.
- **Bruna e Roldão Sênior 65+:** ambas eram sub-cobertas no doc original; tabela atualizada inclui-as com clareza.

---

## Por módulo provável — dores relacionadas e score acumulado (pós-auditoria)

| Módulo | Dores relacionadas (ID) | Score acumulado |
|---|---|---|
| **CRM / Cliente 360° (BIG-10)** | #02 (14.062), #05 (2.869), #14 (933), #20 (1.260), #11 (parcial 1.000) | **20.124** |
| **Cadastros base / Cliente** | #01 (5.400) | **5.400** |
| **Fiscal / NFS-e (BIG-04)** | #10 (8.750), #09 (parcial 1.593) | **10.343** |
| **Metrologia (cálculo + emissão + padrões + assinatura)** | #03 (2.400), #04 (8.250), #06 (3.000), #07 (3.000) | **16.650** |
| **Frota + UMC + Caixa do técnico (BIG-08)** | #16 (3.465), #08 (parcial 500) | **3.965** |
| **Comissões (BIG-09)** | #15 (674) | **674** |
| **Estoque com lacre/selo (BIG-12)** | #18 (262) | **262** |
| **Operação (OS + agenda + mobile)** | #05 (parcial 1.434), #08 (parcial 500), #19 (3.465) | **5.399** |
| **Financeiro (conciliação + cobrança)** | #09 (1.593), #11 (1.000) | **2.593** |
| **Qualidade (NC, auditoria, reclamação 7.9, competência)** | #13 (400), #07 (parcial 1.500) | **1.900** |
| **Painel do Dono (transversal)** | #12 (4.500) | **4.500** |
| **Automações (BIG-11)** | #02 (parcial 7.031), #11 (parcial 1.000), #20 (parcial 630) | **8.661** |
| **Metrologia Legal (BIG-06)** | #17 (240) | **240** |

**Leitura pós-auditoria:**
- **Módulo com maior score acumulado:** CRM/Cliente 360° (20.124) + Automações (8.661) — somam 28.785 (era 51.252). **Confirmação enfraquecida da DF-3, mas ainda topo do ranking.**
- **Metrologia (16.650)** vem em 2º — pilar técnico defensável (BIG-02) **agora compete de igual pra igual com CRM**, contraponto saudável.
- **Fiscal/NFS-e (10.343)** com cutover 01/09/2026 — escassez de oferta no mercado (gap confirmado).
- **Frota+UMC (3.965) e Comissões (674)** caíram pesado — sinal de que precisam de validação forte na Onda 1 antes de ocupar tanto espaço no MVP-1.

---

## Top 5 dores prioritárias com recomendação MVP (pós-auditoria 17/05/2026)

> **⚠️ Top 5 RECALIBRADO removendo halo founder-customer.** Top 5 original tinha 4 das 5 dores vinculadas a decisões fundadoras (improbabilidade estatística <5%). Top 5 corrigido:

| # | Dor | Score | Recomendação MVP | Justificativa |
|---|---|---|---|---|
| 1 | **#10 — NFS-e municipal cutover 01/09/2026** | **8.750** | **ENTRA MVP-1 (deadline duro)** | **Fato regulatório com data fixa — imune a viés founder-customer.** Cutover obrigatório R-016. Gap absoluto BR confirmado (Concorrentes §4). 100% Reach. Tese central do produto. |
| 2 | **#02 — Esquecimento de recalibração (30-50% receita perdida)** | **~14.062** | **ENTRA MVP-1 (eixo primário de venda)** | Receita perdida direta R$ 8-12k/mês. Universal (75% Reach pós-deflação). Mantém Top 1-2 mesmo após dupla deflação — sinal forte. Resolve drama emocional do Roldão. Única dor-DF no top 5. |
| 3 | **#04 — Word/Excel/macros = NC permanente cláusula 7.11** | **8.250** | **ENTRA MVP-1 (pitch real do produto)** | **Não-DF, validável por auditor metrológico independente.** Jornada §6.5 define como "o pitch real do Aferê". Atinge 55% Reach. Frequência altíssima. Sem isso, o produto não tem narrativa metrológica defensável. |
| 4 | **#01 — Cadastro digitado 4-6 vezes** | **~5.400** | **ENTRA MVP-1 (foundation)** | Foundation. Sem cliente único, CRM (#02 e #20), NFS-e (#10) e Cobrança (#11) não funcionam. Solvability baixa (2/5). 80% Reach pós-deflação. Promovido a BIG-07. |
| 5 | **#05 — Status de OS perguntado 10-30x/dia** | **2.869** | **ENTRA MVP-1 (quick win, não-DF)** | **Promovido ao top 5 pós-auditoria.** Persona Letícia universal em qualquer empresa do ICP — viés founder-customer mínimo. Dor visível em entrevista direta com atendente. Quick win com portal cliente lite + automação WhatsApp. |

> **Mudança chave:** Dor #19 (Registro WhatsApp + Frota TCO) **desceu do top 5 (#5) pra top 8** porque carrega halo founder-customer (DF-1 Frota TCO). O score original (6.300) inflava por Reach 0,70 sem citação literal e DAP sem deflação DF.

---

## Top 6-8 (referência para MVP-1 parcial)

| # | Dor | Score | Notas |
|---|---|---|---|
| 6 | **#12 — Dono apaga incêndio (Painel do Dono)** | 4.500 | ⭐ **Não-DF, virou OP12 Painel do Dono no OST pós-auditoria** |
| 7 | **#16 — Caixa do técnico + frota** | 3.465 | DF-1 com dupla deflação aplicada |
| 8 | **#19 — Registro WhatsApp + frota TCO** | 3.465 | DF-1 com dupla deflação; desceu do top 5 |

---

## Dores que NÃO entram no MVP (non-goals)

> Pelo menos 5 dores reais que ficam fora do MVP-1. Alinha com Anti-jobs ANTI-01 a ANTI-11 (`jobs-to-be-done.md` §5).
>
> **⚠️ Nota Aud-20:** ANTI-11 (customização individual por tenant) **é mantido como real** neste doc — sincronizar com `jobs-to-be-done.md` §5 que atualmente lista só ANTI-01..ANTI-10. **Pendência atribuída ao subagente D na divisão de trabalho pós-auditoria 17/05/2026.**

| Dor (descrição curta) | Origem | Por que NÃO entra no MVP-1 | Tratamento futuro |
|---|---|---|---|
| **Folha de pagamento + ponto + holerite + férias da equipe** | Jornada §2.2 + Persona Cláudia | **ANTI-01**: domínio RH completo é mercado próprio | Integração externa com Pontomais/Sankhya RH (MVP-3+). |
| **Pagamento online com cartão direto (gateway próprio)** | Jornada §7.2 + R-025 (PCI-DSS 4.0.1) | **ANTI-02**: vira PCI-DSS escopo full | Usar PSP terceiro (Asaas, Pagar.me, Stripe) — MVP-2 |
| **BI sofisticado / dashboards customizáveis / query SQL** | Persona Roldão pediria em algum momento | **ANTI-05 + ANTI-09**: gigantes resolvem melhor | Dashboards fixos por papel no MVP-1; export CSV/Parquet via API no MVP-2 |
| **Mensageria interna entre técnicos / chat** | Jornada §5 + Persona Bruna | **ANTI-08**: mercado saturado (WhatsApp já usado) | Equipes continuam usando WhatsApp pessoal; produto só notifica eventos |
| **Calendário/agenda como produto (não só integração)** | Jornada §5.3 Google Calendar individual | **ANTI-10**: Google Calendar e Outlook resolvem | Integração bidirecional Google Calendar — MVP-2 |
| **Customização individual por tenant** | Risco R-001 + Persona Roldão tendência natural | **ANTI-11 CRÍTICO**: customização individual mata produto opinativo + dispara dívida técnica exponencial. *(Nota Aud-20: a ser sincronizado com `jobs-to-be-done.md` §5 pelo subagente D)* | Única forma: **configuração estruturada** (switches, perfis, checklists). Cliente que quer mais paga **setup** que vira config **nativa pra todos**. |
| **Treinamento de técnico júnior / trilha de procedimento embutida** | JTBD-033 + JTBD-050 + JTBD-055 | Solvability 5/5 + ROI MVP-1 baixo | MVP-3 — biblioteca de procedimentos PT-BR é diferencial de longo prazo |
| **Pesquisa NPS estruturada + relatórios de satisfação** | Jornada §5.10 + JTBD-085 (parcial) | Solvability moderada mas Reach baixo no MVP-1 | MVP-2 — disparo de tarefa de retenção em NPS negativo entra com BIG-11 |
| **Hardware proprietário (calibrador, sensor, dispositivo)** | JTBD-023 + Concorrentes Beamex/Fluke | **ANTI-06**: não somos fabricante | Integrar via Bluetooth/USB com hardware existente — MVP-2/3 |
| **Gestão clínica/análises clínicas humanas (LIS)** | Patrícia (farma) pode pedir | **ANTI-03**: domínio próprio (CFM 1821/2007, SBIS-CFM) | Fora de escopo permanente; integração leitura-only se exigido |

---

## Imunização contra founder bias

> **Seção nova pós-auditoria 17/05/2026.** Cinco entrevistas-tipo que MAIS expõem viés founder-customer e que devem ser priorizadas na Onda 1 para evitar que o produto se torne "customização disfarçada" do laboratório do Roldão.

| Entrevista-tipo | Por que expõe viés | O que testar |
|---|---|---|
| **Lab de bancada-only para indústria farma** (sem campo, sem UMC) | Anti-perfil de Roldão (que tem campo + UMC). Se essa empresa pagar pelo produto, BIG-08 (Frota) é mesmo opcional. | DAP por Dor #04 e #03 isoladas; Reach real de Dor #16/#19 (deve cair pra <40%) |
| **Perfil C acreditando-se agora** (em processo de Cgcre) | Anti-perfil de Roldão (já acreditado). Foco em pré-acreditação muda o pitch. | Quanto pagaria por matriz competência (#07) e dossiê validação (#04) vs portal cliente (#05) |
| **Operação 2-3 técnicos PJ** (sem CLT) | Anti-perfil de Roldão (CLT + comissão). PJ não tem comissão, não tem férias gargalo. | Reach real de Dor #15 (Comissões) — deve cair pra <30% |
| **Lab que atende açougueiro/varejo low-tech puro** (sem farma, sem indústria) | Anti-perfil de Roldão (cliente farma é forte). Confirma se BIG-06 (Metrologia Legal) é vendável sozinho. | DAP por Dor #17 isolada; rejeição de Dor #13 (modo auditoria farma) |
| **Lab CLT puro sem comissão técnica** (técnico recebe salário fixo) | Anti-perfil direto da DF-2 (Comissões). | Reach real de Dor #15 — provavelmente 0 — confirma que DF-2 é opcional, não core |

**Regra de gatilho:** se 3 das 5 entrevistas-tipo confirmarem que uma DF é "opcional, não core", a DF é **rebaixada de obrigatória pra módulo opcional MVP-2** sem perda de produto.

---

## Saída esperada

- **Top 5 dores prioritárias com score (pós-auditoria):**
  - #10 NFS-e (8.750)
  - #02 Recalibração (~14.062 / 15.000)
  - #04 Word/Excel NC 7.11 (8.250)
  - #01 Cadastro 4-6x (~5.400 / 5.500)
  - #05 Status OS 10-30x/dia (2.869)
- **Recomendação de MVP-1 baseada em score:** **12 dores entram** (era 13). **Dor #19 (frota TCO + WhatsApp) move pra MVP-2** mantendo OP3 só com app + caixa no MVP-1; aspecto cláusula 7.5.1 (registro técnico com foto+timestamp) fica MVP-1 como POC mínimo.
- **Total de dores no documento:** 20.
- **Lista de dores fora de escopo:** ver §"Dores que NÃO entram no MVP" — 10 categorias alinhadas a ANTI-01 a ANTI-11.

---

## Dores externamente validadas — descobertas na pesquisa documental (17/05/2026 noite)

> **Origem:** 4 buckets de pesquisa documental independente rodados em paralelo (validação externa do Portão 1 da ADR-0001 candidata). Roldão optou por NÃO fazer Onda 1 declarada agora (proteção competitiva), então essas dores vieram de fontes públicas: reviews/Reclame Aqui, grupos sociais/YouTube/fóruns técnicos, marketing dos concorrentes, regulatório/acadêmico. Doc consolidado em `validacao-externa-documental.md`.
>
> **Status:** dores 21-32 ainda **não têm score completo** (sem entrevista, faltam DAP/Frequência reais). Confirmadas como **dores externamente observadas** com evidência citada — entram como hipóteses fortes pro MVP-1 ou backlog.

### Categoria A — Funcionalidade técnica

#### Dor #21: Update do sistema quebra customização (vendor lock-in pós-personalização)
- **Origem documental:** Bucket B (Capterra IndySoft jan/2025 — Jared: *"Toda atualização quebra ou reduz a eficiência da customização"*; padrão também em GAGEtrak; provável também em Cali sem evidência pública)
- **Sintoma observável:** cliente personaliza templates de certificado, fórmulas de incerteza, layouts; próxima atualização do fornecedor quebra tudo; workaround é "manter estrutura fixa" (= não atualizar)
- **Personas mais afetadas:** Marcos (signatário — templates customizados), Sandra (RT — formulários do SGQ), Roldão (dono — perdeu horas customizando)
- **Implicação pra MVP:** ENTRA como princípio arquitetural (não como feature) — customização declarativa + versionada em git (YAML/JSON), nunca código injetado. Vira ADR técnica futura.
- **Módulo provável:** transversal — afeta Metrologia, Cadastros, CRM
- **Vínculo com riscos:** novo risco a criar (R-066 candidato) — "update do fornecedor quebra customização do cliente"

#### Dor #23: Vazamento de dados de cliente por planilha compartilhada (cláusula 4.2)
- **Origem documental:** Bucket B (Blog da Metrologia caso real — *"laboratório decide usar planilhas Excel pras calibrações e dá acesso a todos os colaboradores. Alguém de outro setor, leigo, compartilha planilha com dados de clientes à mostra. Quebra cláusula 4.2 sem perceber"*)
- **Sintoma observável:** colaborador leigo encaminha planilha por e-mail/WhatsApp com dados de cliente A pra colaborador que atende cliente B (concorrente do A); viola ISO 17025 4.2 (confidencialidade); pode virar processo civil/regulatório
- **Personas mais afetadas:** Sandra (RT — responsável pelo SGQ), Roldão (dono — risco regulatório), cliente final
- **Diferença em relação à Dor #04:** #04 era sobre CÁLCULO em planilha (NC permanente 7.11). #23 é sobre CONFIDENCIALIDADE (4.2) — separados.
- **Implicação pra MVP:** ENTRA — RNF de segurança (controle de acesso por cliente + log de quem viu o quê + isolamento multi-tenant rigoroso)
- **Módulo provável:** Plataforma (RBAC + Audit Trail)
- **Vínculo com riscos:** reforça R-003 (vazamento entre tenants) e R-014 (LGPD multa ANPD)

#### Dor #31: Manutenção preditiva por uso/desgaste do instrumento (refinamento da #02)
- **Origem documental:** Bucket C (TOTVS + Metroex + Portal ISO vendem como diferencial — "frequência baseada em uso, não em prazo fixo")
- **Sintoma observável:** instrumento usado intensamente em 6 meses degrada mais que um pouco usado em 12 meses; alerta por prazo fixo desperdiça calibração desnecessária OU subestima drift; cliente farma pede análise estatística de drift
- **Personas mais afetadas:** Sandra (RT — quer otimizar agenda de calibração), Patrícia (cliente farma — exige análise de tendência), Marcos (signatário — decide se aprova com base em drift)
- **Implicação pra MVP:** MVP-2 ou enterprise. Refinamento da Dor #02, não dor independente.
- **Módulo provável:** Metrologia (cálculo + tendência) + CRM (alerta inteligente)

#### Dor #32: Análise estatística MSA/SPC para cliente industrial (Gage R&R, IATF 16949)
- **Origem documental:** Bucket C (Metroex + Qualiex + TOTVS vendem MSA/Gage R&R)
- **Sintoma observável:** cliente industrial (automotivo IATF 16949 ou eletro-eletrônico AIAG) pede estudo de MSA/Gage R&R do instrumento; lab calibrador não tem ferramenta integrada e faz manualmente em Excel ou recusa o serviço
- **Personas mais afetadas:** Sandra (RT — perde negócio sem essa capacidade), Marcos (signatário — calcula manualmente), cliente industrial
- **Implicação pra MVP:** Condicional ao ICP. Se MVP-1 inclui labs servindo automotivo IATF, é dor real. Se ICP for só PME comercial, MVP-2.
- **Módulo provável:** Metrologia (módulo MSA opcional)

### Categoria B — Modelo comercial do produto

#### Dor #25: Cláusula de fidelidade 12 meses + reajuste anual abusivo
- **Origem documental:** Bucket A (4 concorrentes com queixa pública — Conta Azul: *"aumento abusivo todos os anos"*; Field Control: *"cláusulas contratuais que obrigam pagamento do valor total até o final do contrato de um ano, mesmo sem utilizar"*; Bling, Tiny: idem)
- **Sintoma observável:** cliente tenta cancelar SaaS pra trocar de fornecedor mas é preso por cláusula de 12 meses; cliente renova e descobre reajuste 3x acima de IPCA; vira reclamação Reclame Aqui
- **Implicação pro modelo comercial do Aferê:** decisão prévia obrigatória — pricing transparente (sem fidelidade abusiva, reajuste pré-anunciado, pricing por uso real) seria diferenciador. Se Aferê copiar padrão SaaS BR, herda essa dor.
- **Módulo provável:** Plataforma (Faturamento/Contratos)
- **Vínculo com riscos:** novo risco a criar — "modelo comercial padrão do mercado pode replicar dor do mercado"

#### Dor #26: Suporte cordial mas inefetivo / chat abandonado
- **Origem documental:** Bucket A (Auvo: *"Os atendentes são ótimos! Sempre bastante educados, mas não conseguem evoluir com a solução"*; Tiny: *"o atendente percebe que não consegue sanar a questão, simplesmente abandona a conversa"*)
- **Sintoma observável:** atendente é educado, abre ticket, escala pra "time técnico" e nunca volta; cliente tenta 3x, desiste, churna em 60 dias
- **Implicação pro Aferê:** decisão de modelo de suporte — SLA explícito como diferencial (custo alto, escala difícil) OU produto auto-explicativo o suficiente pra suporte ser raro (melhor pra MEI). Conecta com LEAP F-18 (CS L1 cabe em modelo 100% agentes — bot + Roldão fallback).
- **Módulo provável:** Plataforma (Suporte/CS)
- **Vínculo com riscos:** R-062 (CS L1 inexistente = churn 90 dias > 40%) já cobre

#### Dor #27: Integração prometida na venda que não funciona depois
- **Origem documental:** Bucket A (Auvo + OMIE: *"a plataforma prometeu integração com o OMIE — um dos principais motivos do fechamento do negócio — mas a integração não funciona"*; Tiny + ML Full + TikTok Shop; Bling + WooCommerce/Mercado Livre)
- **Sintoma observável:** vendedor mostra "integra com X" no funil; cliente assina; ao tentar usar, descobre que integração está "em desenvolvimento" ou tem limitações graves; vira queixa Reclame Aqui
- **Implicação pro Aferê:** princípio de transparência radical — distinguir publicamente "integração pronta" vs "roadmap" vs "via Zapier/webhook custom". Cada integração quebrada = reclamação pública + churn.
- **Módulo provável:** Plataforma (Integrações + Marketing)
- **Vínculo com riscos:** reforça Dor #01 (cadastro 4-6x) mas com ângulo "comercial enganoso"

#### Dor #28: Instabilidade em horário fiscal crítico paralisa cliente
- **Origem documental:** Bucket A (Bling jan/2025: 2 incidentes paralisantes — *"fiquei duas semanas com sistema inoperante"*; Field Control 33 dias dezembro 2024 — *"sistema ficou fora do ar durante todo o mês"*)
- **Sintoma observável:** sistema cai no dia 30 (fechamento de mês fiscal) ou no início do mês (emissão de NFS-e); cliente não consegue faturar; perde dinheiro; vira queixa pública agressiva
- **Implicação pra MVP:** SLA público + status page + drill de DR mensal cronometrado desde dia 1. **Já refletido no Portão 3 da ADR-0001** (4 drills cronometrados antes do 1º tenant pago).
- **Módulo provável:** Plataforma (Observabilidade + DR)
- **Vínculo com riscos:** confirma R-009 (Hostinger SPOF) e Parecer 8 (incidente em produção)

### Categoria C — Estrutura de mercado

#### Dor #24: Mercado BR fechado, sem comunidade pública (oportunidade estrutural)
- **Origem documental:** Bucket B (Cali, FP2, Aferitec — zero presença em Reddit, Facebook público, LinkedIn grupos abertos; único espaço público ativo é Blog da Metrologia, neutro/não-vendedor)
- **Sintoma observável:** cliente Cali insatisfeito não tem onde reclamar publicamente — vira ticket 1:1 com suporte; mercado opera fechado; novos entrantes não sabem o que cliente real sente
- **Implicação pro Aferê:** **OPORTUNIDADE** estrutural — construir comunidade pública cedo (Discord/grupo Telegram/fórum aberto) é diferencial em mercado fechado. Também é **RISCO** — pode indicar base instalada muito pequena (Cali tem ~5 funcionários, Metroex cita "80 clientes").
- **Módulo provável:** Marketing/Comunidade (não-feature do produto)
- **Vínculo com riscos:** R-001 (founder is customer) — se mercado é tão pequeno, TAM real pode estar inflado

#### Dor #29: Janela ENIQ 2025-2026 — pressão regulatória simultânea (12-18 meses)
- **Origem documental:** Bucket D (NIT-DICLA-030 rev. 15 dez/2024 + NFS-e Padrão Nacional CGSN 189/2026 + RDC ANVISA 658/2022 e 972/2025 + ENIQ Resolução CONMETRO 2/2025 + Operação Tô de Olho INMETRO+ANP fev/2026: 362 irregularidades em 2 dias)
- **Sintoma observável:** lab que estava operando confortavelmente em planilha começa a perder cliente farma por falta de SGQ digital; perde direito de emitir NFS-e a partir de 01/09/2026; recebe NC em auditoria CGCRE; é autuado pelo IPEM
- **Implicação pra MVP:** **CRÍTICA — orienta priorização do MVP-1.** Player que entregar emissor NFS-e + cálculo de incerteza conforme NIT-DICLA-030 rev. 15 + trilha auditoria 17025 em ≤ 12 meses **captura mercado em onda regulatória forçada**. Janela expira em 12-18 meses.
- **Módulo provável:** Marketing (positioning) + Fiscal + Metrologia + Plataforma (Audit Trail)
- **Vínculo com riscos:** R-016 (cutover NFS-e 01/09/2026) já cobre; janela completa reforça urgência

#### Dor #30: Disputa de jurisdição IPEM × cliente final
- **Origem documental:** Bucket D (IPEM-RJ e IPEM-SP têm página dedicada a FAQ jurídico + recurso de auto de infração — sinal de litígio recorrente)
- **Sintoma observável:** IPEM autua o cliente final (posto de gasolina, comerciante de feira); cliente recorre ao laboratório de calibração pra "comprovar que estava certo"; lab é envolvido em processo administrativo/judicial sem ter sido parte original
- **Implicação pra MVP:** pode virar **tipo de serviço diferenciado** ("OS de defesa de auto de infração IPEM" = preço maior, processo padronizado, trilha auditável reforçada).
- **Módulo provável:** Operação (tipo especial de OS)
- **Vínculo com riscos:** novo risco potencial — "lab responsabilizado em processo IPEM que não originou"

### Categoria D — Marketing e diferencial

#### Dor #22: Calibração rápida demais é red flag de fraude (sinal de mercado sobre confiança)
- **Origem documental:** Bucket B (KN Waagen — alerta público: *"Sempre desconfie de calibração RBC de balança executada em menos de 5 minutos"*)
- **Sintoma observável:** lab competidor faz calibração "expressa" (5-10 min), emite certificado, cobra metade do preço; cliente final desconfia mas não tem como provar; quem faz certo (60-90 min reais) parece "lento e caro"
- **Implicação pra Aferê:** **diferencial de marketing real** — trilha auditável publicável (timestamp início/fim de cada etapa, fotos das condições ambientais, registro de medições intermediárias) como **prova de qualidade**, não só compliance. "Veja: nossas calibrações duraram em média X minutos, com Y medições. Concorrente faz em 5 minutos — pergunte como" é argumento defensável.
- **Módulo provável:** Metrologia (Audit Trail Publicável) + Marketing (positioning)
- **Vínculo:** transforma INV-001 (audit trail imutável) de "obrigação regulatória" em "arma de marketing"

---

## Resumo das 12 dores novas

| # | Dor | Categoria | Status MVP-1 |
|---|---|---|---|
| 21 | Update quebra customização | Técnica | Princípio arquitetural (ADR técnica) |
| 22 | Calibração rápida = red flag fraude | Marketing/Diferencial | Marketing (trilha publicável) |
| 23 | Vazamento dados por planilha compartilhada (4.2) | Técnica | RNF segurança obrigatório |
| 24 | Mercado fechado sem comunidade pública | Estrutural | Estratégia (criar comunidade cedo) |
| 25 | Fidelidade 12 meses + reajuste abusivo | Comercial | Decisão de modelo comercial pré-MVP |
| 26 | Suporte cordial mas inefetivo | Comercial | Já coberto por F-18 + R-062 |
| 27 | Integração prometida que não funciona | Comercial | Princípio: transparência radical de roadmap |
| 28 | Instabilidade em horário fiscal | Operacional | Já coberto pelo Portão 3 da ADR-0001 |
| 29 | Janela ENIQ 2025-2026 | Estrutural | **Orienta priorização MVP-1 — janela 12-18 meses** |
| 30 | Disputa IPEM × cliente final | Operacional | Tipo de serviço diferenciado (MVP-2?) |
| 31 | Manutenção preditiva por uso/desgaste | Técnica | MVP-2 ou enterprise |
| 32 | Análise estatística MSA/SPC | Técnica | Condicional ao ICP |

---

## Próximos passos (re-rankear pós-Onda 1)

1. **Validar números na Onda 1 de entrevistas** (3-5 empresas). Priorizar as **5 entrevistas-tipo anti-Roldão** da seção "Imunização contra founder bias". Cada dor acima precisa de pelo menos:
   - 1 citação literal substituindo `[INFERÊNCIA — validar em onda 1]`.
   - Frequência real auto-reportada.
   - DAP real auto-reportada (deflacionar 50% como regra Auditor 6, com possível segunda deflação 30% se dor vinculada a DF).
   - Reach corrigido após mapear o ICP real.
2. **Re-rankear top 5.** Score atual é palpite ponderado por evidência interna pós-auditoria; pós-entrevistas pode mudar ordem.
3. **Detectar dores omitidas.** As 20 acima cobrem 4 ciclos + 4 decisões fundadoras + 14 personas; entrevista pode revelar uma 21ª.
4. **Alimentar `sintese-final.md`** com top 5 + recomendação MVP-1.
5. **Alimentar `validacao-ativa.md`** com perguntas-chave por dor (já tem rascunho em Jornada §15).
6. **Sincronizar ANTI-11 com `jobs-to-be-done.md` §5** (pendência Aud-20 — subagente D).
