---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente + corretora SUSEP humana
marco: Wave A Marco 3 — operacao/os
tipo: review-p2-corretora
spec-revisada: docs/faseamento/M3-os/spec.md
relacionados:
  - docs/adr/0019-rc-codigo-ia.md
  - docs/adr/0028-mapa-coberturas-wave-a.md
  - docs/conformidade/comum/seguros/gates-seg.md
  - docs/conformidade/comum/seguros/briefing-corretora-susep.md
selo: "PRÉ-COTAÇÃO — NÃO EMITE APÓLICE. REQUER CORRETORA SUSEP CREDENCIADA (Lei 4.594/64 + Res. CNSP)"
---

# Parecer — Corretora Seguros (P2 ritual Spec Kit, Marco 3 `operacao/os`)

## Sumário executivo

- **Decisão geral:** **BLOQUEANTE** — Marco 3 não pode entrar em **dogfooding produtivo Balanças Solution** com instrumentos físicos sem GATE-SEG-BPT-1 emitido. Spec.md está tecnicamente sólida sob lente de risco segurável, mas omite 3 ganchos contratuais/probatórios que afetam diretamente a segurabilidade da operação.
- **6 achados reais** abaixo (P-OS-S1..S6). 1 BLOQUEANTE, 3 ALTO (AJUSTADO), 2 MÉDIO (ACEITE com gate rastreado).
- **Aviso legal obrigatório:** este parecer é consultivo. **Nenhuma das coberturas, capitais, franquias ou cláusulas aqui citadas constitui contrato de seguro.** Lei 4.594/64 + Resoluções CNSP exigem **corretora SUSEP credenciada humana** pra cotar, intermediar e emitir apólice. Toda recomendação concreta abaixo carrega o flag **[REQUER CORRETORA SUSEP HUMANA]**.

---

## Achados

### P-OS-S1 — GATE-SEG-BPT-1 não está cravado como bloqueio de Definition of Done do M3 [BLOQUEANTE]

**Severidade:** CRÍTICO.
**Lente:** R-OS-1, R-OS-6 e contexto operacional Balanças Solution dogfooding.

**Análise.** Spec §14 (Definition of Done) lista 11 critérios técnicos pra fechar M3, mas **nenhum vincula entrada em produção dogfooding ao GATE-SEG-BPT-1**. ADR-0028 marca BPT como EMERGENCIAL — Balanças Solution já recebe instrumentos físicos hoje (CC art. 627 configura depositário). No momento que M3 entra em produção dogfooding, **a Aferê passa a registrar formalmente custódia BPT em banco de produção sem apólice** — isto agrava o risco vs. a operação papel/planilha atual, porque:

1. Audit trail digital comprova custódia formal (prova contra o segurado em caso de sinistro).
2. Foto + geo + biometria do AceiteAtividade tornam o sinistro **mais provável de ser pago se houver apólice, mas também mais provável de ser apontado como negligência se não houver**.
3. Cobertura retroativa BPT é negociável, mas seguradora pode recusar emissão se descobrir custódia ativa não declarada.

Spec §9 cita GATE-SEG-BPT-1 mas como "rastreado, não bloqueia fechamento do M3". **Discordo:** fechamento técnico do M3 é ok sem BPT; **entrada em dogfooding produtivo NÃO é**.

**Decisão recomendada (AJUSTAR spec).**

- Adicionar na §14 DoD um item **separado e nomeado**:
  - `[ ] GATE-SEG-BPT-1 emitido (apólice BPT real ≥ R$ 500k/sinistro, franquia fixa R$ 10-15k) ANTES de a 1ª OS produtiva criar AtividadeDaOS de tipo manutencao_*/calibracao/instalacao em Balanças Solution.`
- Adicionar no plan.md (P2) um item "**fase 0 pré-dogfooding**" que inclui:
  - feature flag `OS_PRODUTIVO_DOGFOODING_BS=false` por default;
  - flag só liga após corretora SUSEP confirmar emissão e apólice arquivada em `docs/conformidade/comum/seguros/apolices/` (estrutura a criar);
  - hook ou predicate authz `pode_criar_os_produtiva_balancas` checa a flag.
- Marcar no §12 mapa de riscos um R-OS-11 novo: **"Marco 3 entra em dogfooding sem apólice BPT emitida → exposição depositário CC art. 627 sem cobertura"** — probabilidade alta (default sem gate), impacto crítico.

**Flag.** [REQUER CORRETORA SUSEP HUMANA] — emissão da apólice BPT depende exclusivamente de corretora SUSEP. Sem ela, GATE não fecha e dogfooding fica bloqueado por contrato com Aferê (não só por boas práticas).

---

### P-OS-S2 — R-OS-3 biometria cross-tenant: spec não amarra cláusula nomeada art. 11 LGPD na cobertura Cyber [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** R-OS-3 (biometria coletada em key_id errada — cross-tenant).

**Análise.** Spec trata o risco tecnicamente bem (INV-OS-ACEITE-BIO-001 + hook `biometria-key-validator` + RLS no AceiteAtividade). Mas se o incidente acontecer mesmo com controles (ex: bug no provisionamento KMS), o evento é **vazamento de dado biométrico = categoria especial LGPD art. 11**. A ANPD trata isso como **circunstância agravante** na dosimetria (até 2% do faturamento, teto R$ 50M, mais sanções não-pecuniárias).

ADR-0028 Modalidade 2 (Cyber R$ 5M) cobre LGPD genérica via `consequential regulatory damages` nomeando ANPD (GATE-SEG-META-1). Mas **não há cláusula nomeada cobrindo dado sensível art. 11** especificamente. Algumas seguradoras excluem ou sublimitam categorias especiais (biométrico, saúde, racial, etc.) — precisa cláusula afirmativa.

A spec.md §12 R-OS-3 cita só mitigação técnica, sem amarrar à cobertura segurável.

**Decisão recomendada (AJUSTAR briefing corretora + ADR-0028 + spec).**

- Adicionar à Modalidade 2 (Cyber) do ADR-0028, cláusula obrigatória nova:
  - `Sensitive personal data — LGPD art. 11 (biometric, racial, health, religion) — affirmative coverage, no sub-aggregate restriction`.
- Adicionar no briefing-corretora §5 (riscos enumerados) um item explícito: "biometria touch (templates derivados) coletada em campo, criptografada com KMS key dedicada por tenant — vazamento cross-tenant é evento de categoria especial".
- Adicionar nas perguntas obrigatórias à corretora SUSEP: "a apólice cobre vazamento de dado sensível art. 11 LGPD sem sublimite separado?"
- Spec.md §12 R-OS-3: estender mitigação com `+ cobertura Cyber Modalidade 2 cláusula sensitive personal data (GATE-SEG-CYBER-1 + cláusula nova)`.

**Flag.** [REQUER CORRETORA SUSEP HUMANA] — só corretora pode confirmar quais seguradoras aceitam essa cláusula afirmativa sem sublimite separado.

---

### P-OS-S3 — R-OS-5 cancelamento parcial pós-fatura + R-OS-9 valor_total race: cobertura `wrongful billing` está sublimitada e R-OS-5 não está coberto [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** R-OS-5 (faturamento incorreto após cancelamento parcial pós-fatura) + R-OS-9 (cancelamento múltiplo concorrente).

**Análise.** Spec §12 R-OS-5 diz "NG-OS-4 + gate `GATE-FIN-CR-AJUSTE-POS-FATURA` Wave B + INV-OS-FAT-001". Tecnicamente é NG (não está no escopo). Mas no plano segurável existem 2 ângulos não cobertos:

1. **Erro fiscal residual com Receita Federal/SEFAZ.** Se o cancelamento parcial gerar NF complementar/cancelamento de NF emitida fora de prazo, multa Receita Federal pode cair. ADR-0028 Modalidade 1 E&O lista `consequential regulatory damages` nomeando SEFAZ + Receita Federal — OK, isso cobre. Mas spec não amarra.
2. **Wrongful billing capped em R$ 50k.** ADR-0028 Modalidade 1 cita `Wrongful billing (cobrança indevida billing-saas > R$ 50k)`. Lendo literal, **o que está coberto é o que excede R$ 50k**, mas a faixa típica de erro num cancelamento parcial num tenant PME é R$ 5k-30k — **fica EXATAMENTE na faixa abaixo do gatilho de cobertura**. Isso é uma exclusão por sublimite invertido (cobre só sinistros grandes; pequenos correm por conta da Aferê).
3. **R-OS-9 race condition em valor_total** — mitigado por `SELECT FOR UPDATE`. Mas se vazar (ex: deadlock retry mal feito) e gerar billing duplicado entre tenants, **risco vicarious tenant**: tenant é cobrado errado → tenant cobra cliente final errado → cliente final processa tenant → tenant subroga contra Aferê. Vicarious liability tenant on-site não cobre cobrança incorreta entre tenant↔cliente-final.

**Decisão recomendada (AJUSTAR ADR-0028 + briefing).**

- Renegociar Modalidade 1 cláusula `Wrongful billing`: **remover gatilho R$ 50k e usar franquia fixa R$ 5k por evento**, cobrindo do R$ 5k até sublimite por evento (R$ 3M). Esta é prática de mercado pra E&O tech.
- Adicionar cláusula nomeada **`Tax penalty exposure — incorrect cancellation / late tax document`** dentro do `consequential regulatory damages`, nomeando Receita Federal + SEFAZ específicos.
- Spec.md §12 R-OS-5: estender com `+ cobertura E&O Modalidade 1 cláusula wrongful billing (franquia R$ 5k) + tax penalty exposure (GATE-SEG-EO-1 + cláusulas novas)`.
- Spec.md §12 R-OS-9: estender mitigação para `+ saga compensação cross-módulo ADR-0034 + monitoramento divergência valor_total NN p99/24h`.

**Flag.** [REQUER CORRETORA SUSEP HUMANA] — corretora precisa negociar a franquia fixa baixa (R$ 5k) vs. preço; algumas seguradoras só aceitam franquia % capital.

---

### P-OS-S4 — R-OS-6 vício metrológico cascateia em Accreditation Loss + recall farma — falta cláusula que liga atividade=calibracao a Modalidade 7 [ALTO]

**Severidade:** ALTO (AJUSTADO).
**Lente:** R-OS-6 (concorrência 2 atividades simultâneas mesmo equipamento corrompe medição) + interface com Marco 4.

**Análise.** R-OS-6 é o risco mais perigoso operacionalmente, porque a falha é **silenciosa**: medição contaminada vira certificado emitido, certificado vira evidência regulatória do cliente final, dano emerge meses depois (auditoria CGCRE, recall farma, inspeção ANVISA). O caminho de subrogação é:

1. Cliente do tenant usa instrumento calibrado errado → fabrica lote farma fora de spec → ANVISA recall.
2. Cliente do tenant processa o tenant (laboratório) → tenant subroga contra Aferê alegando defeito de software (vício no controle de concorrência ADR-0041).
3. Apólice acionada: **E&O ampliado Modalidade 1** (`software validation defect causing accreditation suspension` — ADR-0025 cl. 7.11) + **Accreditation Loss Extension Modalidade 7** + **`pharmaceutical/food recall extension` R$ 3M sublimite**.

**O problema:** spec §12 R-OS-6 cita apenas mitigação técnica (`INV-OS-CONC-001 + matriz ADR-0041 + lock por equipamento_id`). Não amarra à cascata segurável. E **a cláusula `software validation defect`** é exatamente o gatilho contratual que conecta R-OS-6 a Modalidade 1 ampliado — sem ela, seguradora pode argumentar "defeito de produto, não E&O".

Além disso, **R-OS-6 toca a fronteira M3↔M4**: o vício acontece em M3 (concorrência), mas o dano materializa em M4 (medição/certificado). Se a apólice for cotada antes de M4 ficar estável, há risco de a cláusula ser fechada sem cobrir explicitamente o vetor M3.

**Decisão recomendada (AJUSTAR briefing + spec).**

- No briefing-corretora §5, adicionar caso de uso narrativo curto: "**vetor de dano R-OS-6**: bug de concorrência em OS multi-atividade contamina medição → cliente final farma → recall ANVISA". Pedir à corretora que a cláusula `software validation defect` da Modalidade 1 **cubra explicitamente vetores anteriores ao módulo Calibração** (não só erro no cálculo de incerteza, também erro no controle de OS que precede a medição).
- Spec.md §12 R-OS-6: estender com `+ cobertura E&O Modalidade 1 cláusula software validation defect (cobre vetor M3) + Accreditation Loss Modalidade 7 + sublimite recall farma R$ 3M (GATE-SEG-EO-1 + GATE-SEG-ACR-1)`.
- Adicionar AC novo ou test de saga obrigatório (sugerir em P4 tasks): `tests/sagas/test_saga_vicio_concorrencia_cascateia_cert.py` — simula 2 atividades concorrentes em mesmo equipamento, verifica que matriz bloqueia. **Esse teste é evidência probatória obrigatória pra defesa em sinistro futuro** — comprova due diligence da Aferê.

**Flag.** [REQUER CORRETORA SUSEP HUMANA] — exatamente esse tipo de cláusula (`software validation defect cobrindo vetores upstream`) é onde corretoras especializadas em tech E&O ganham/perdem o caso. Marsh/AON Tech/Howden têm precedente nisso; corretora generalista provavelmente não.

---

### P-OS-S5 — US-OS-013 dispensa de aceite + US-OS-014 no-show com foto: lacuna vicarious + foto terceiros [MÉDIO]

**Severidade:** MÉDIO (AJUSTADO).
**Lente:** US-OS-013 dispensa + US-OS-014 no-show.

**Análise.** Dois cenários distintos, ambos abrem ângulo de RC contra Aferê pela via vicarious:

1. **US-OS-013 dispensa de aceite.** Gerente do tenant dispensa aceite do cliente final. Cliente final depois nega que o serviço foi prestado / contesta resultado. Cliente final processa o tenant. Tenant alega "a plataforma permitiu a dispensa, eu confiei no fluxo" → subroga contra Aferê. **Vetor segurável:** ADR-0028 Modalidade 1 cláusula `Vicarious liability — tenant operative on-site` cobre? **Lendo literal: não.** A cláusula nomeia "tenant operative on-site" (técnico do tenant em campo). Gerente do tenant dispensando aceite remotamente é outra coisa — é **decisão administrativa do tenant via plataforma**. Lacuna.

2. **US-OS-014 no-show com foto.** Spec menciona "foto evidencia" mas não delimita quem aparece. Se a foto pega passantes, vizinhos, funcionários do cliente que não eram alvo da OS — todos têm direitos LGPD (imagem é dado pessoal). Cliente do cliente pode reclamar. Risco direto:
   - LGPD multa ANPD (coberto Cyber se cláusula nomeada).
   - RC imagem (direito personalíssimo CC art. 20).
   - **Cyber pode excluir RC imagem** se não nomeada — geralmente Cyber cobre "data privacy", não "image rights".

**Decisão recomendada (AJUSTAR ADR-0028 + spec).**

- ADR-0028 Modalidade 1, expandir cláusula `Vicarious liability` para `Vicarious liability — tenant operative on-site OR tenant administrative decision via platform` (cobre US-OS-013 dispensa remota).
- ADR-0028 Modalidade 2 (Cyber), adicionar cláusula nomeada `Image rights — incidental third-party capture in field service photo`.
- Spec.md §12 adicionar R-OS-11 novo: "no-show com foto captura terceiros → risco LGPD + RC imagem CC art. 20". Probabilidade média, impacto médio. Mitigação: AC obrigatório em US-OS-014 "foto deve ser enquadrada no instrumento/local; aviso UX 'evite enquadrar terceiros'; opt-out manual'".
- Spec.md §12 adicionar R-OS-12 novo: "dispensa de aceite pelo gerente do tenant gera vicarious contra Aferê — cliente final contesta serviço". Mitigação: termo de dispensa (PDF gerado, hash, evento `DispensaAceiteEmitida`) precisa **citar explicitamente que a decisão é do tenant**, não da Aferê.

**Flag.** [REQUER CORRETORA SUSEP HUMANA] — cláusula `image rights` é incomum em Cyber; corretora precisa confirmar viabilidade.

---

### P-OS-S6 — R-OS-7 hash quebrado 25 anos + R-OS-10 OS combinada NC trava cal indefinidamente — cobertura long-tail + prazo regulatório [MÉDIO]

**Severidade:** MÉDIO (ACEITE com gate rastreado).
**Lente:** R-OS-7 + R-OS-10.

**Análise.**

- **R-OS-7 (texto não canonicalizado quebra hash 25a depois).** Spec mitiga com INV-DOC-CANON-001 + teste regressão. Bom. Cobertura segurável: **ADR-0028 Modalidade 1 cláusula `Long-tail data custody — 25 years`** já cobre. Mas o ponto delicado é: **retroatividade ilimitada nas renovações anuais**. Apólices E&O brasileiras default são claims-made — se Aferê deixar renovação cair em ano X, sinistro reportado em ano X+1 referente a fato do ano X-5 fica descoberto. Spec não traz esse risco operacional.
- **R-OS-10 (OS combinada NC trava cal indefinidamente).** Cliente final do tenant perde prazo regulatório (ex: verificação INMETRO obrigatória em balança de feira). Cliente final autuado por INMETRO. Subroga contra tenant → subroga contra Aferê. **Cobertura:** Accreditation Loss Modalidade 7 cobre perda de acreditação CGCRE, mas **não cobre prazo INMETRO de equipamento de cliente final do tenant** (INMETRO ≠ CGCRE; gatilho da Modalidade 7 é "tenant perde escopo CGCRE/RBC"). Lacuna sutil.

**Decisão recomendada (ACEITE rastreado).**

- **R-OS-7:** adicionar ao briefing-corretora pergunta obrigatória: "qual é o prazo retroativo máximo aceitável? Buscar retroatividade ilimitada com ato de cobertura contínuo via renovação anual sem gap (`continuity of coverage clause`)". Spec aceite — risco residual aceitável se a corretora confirmar continuity of coverage.
- **R-OS-10:** spec aceite — mitigação técnica (resolução NC clara + cancelamento manutenção libera calibração) é suficiente pra MVP. Gate rastreado: **GATE-SEG-INMETRO-PRAZO-1** novo (a registrar em `gates-seg.md`) — avaliar pré-1º tenant com equipamento INMETRO obrigatório se cláusula `consequential regulatory damages` Modalidade 1 cobre prazo INMETRO de cliente final do tenant. **Não bloqueia M3.**

**Flag.** [REQUER CORRETORA SUSEP HUMANA] — continuity of coverage é cláusula complexa, depende do mercado segurador no momento da cotação.

---

## Resumo decisão (tabela)

| ID | Severidade | Decisão | Ação P3 (plan.md) |
|---|---|---|---|
| P-OS-S1 | BLOQUEANTE | AJUSTAR | DoD inclui GATE-SEG-BPT-1 + feature flag dogfooding + R-OS-11 novo |
| P-OS-S2 | ALTO | AJUSTADO | Cláusula sensitive data art. 11 em Modalidade 2 + R-OS-3 estende mitigação |
| P-OS-S3 | ALTO | AJUSTADO | Franquia R$ 5k wrongful billing + tax penalty exposure + R-OS-5/9 estende |
| P-OS-S4 | ALTO | AJUSTADO | software validation defect cobre vetor M3 + teste saga vicio_concorrencia + R-OS-6 estende |
| P-OS-S5 | MÉDIO | AJUSTADO | Vicarious tenant administrative decision + image rights + R-OS-11/12 novos |
| P-OS-S6 | MÉDIO | ACEITE | Continuity of coverage no briefing + GATE-SEG-INMETRO-PRAZO-1 novo |

**Modalidades de seguro afetadas:** 1 (E&O), 2 (Cyber), 4 (BPT), 7 (Accreditation Loss).

---

## O que NÃO está coberto neste parecer (limites do consultor IA)

- Não emiti opinião sobre prêmio anual real — só corretora SUSEP cota com proposta firme.
- Não opinei sobre escolha entre Marsh/AON/Howden — depende de relacionamento comercial atual e disponibilidade de cláusulas técnicas tech E&O no mercado brasileiro hoje.
- Não validei se a apólice atual da Balanças Solution (se existir) já tem alguma cobertura BPT genérica — **Roldão precisa pedir cópia da apólice corporativa atual à seguradora da Balanças Solution e enviar à corretora SUSEP** pra evitar dupla contratação.
- Não opinei sobre sinistro real — não há sinistro aberto.

---

## Próximos passos (P3 — matriz reconciliação)

1. **Roldão:** contratar corretora SUSEP (Marsh / AON Tech / Howden) — flag bloqueante #1 do projeto.
2. **Agente:** integrar P-OS-S1..S6 na matriz reconciliação (P3 ritual) cruzando com pareceres tech-lead/advogado/RBC.
3. **Agente:** atualizar `docs/conformidade/comum/seguros/briefing-corretora-susep.md` com as novas cláusulas e perguntas obrigatórias listadas em S2/S3/S4/S5/S6.
4. **Agente:** propor atualização ADR-0028 (rev 2) com cláusulas adicionais (sensitive data, wrongful billing franquia R$ 5k, tax penalty, software validation defect upstream M3, vicarious administrative decision, image rights, continuity of coverage).
5. **Agente:** propor R-OS-11 + R-OS-12 na spec.md §12.
6. **Agente:** registrar GATE-SEG-INMETRO-PRAZO-1 em `docs/conformidade/comum/seguros/gates-seg.md`.

---

**[REQUER CORRETORA SUSEP HUMANA]** — todo capital, franquia, cláusula e modalidade citados aqui são pré-cotação. Apólice válida só com corretora SUSEP credenciada (Lei 4.594/64 + Res. CNSP). Este parecer **não substitui** corretora humana.
