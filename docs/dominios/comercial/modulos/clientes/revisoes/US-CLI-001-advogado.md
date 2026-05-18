---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-CLI-001
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-001.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-CLI-001 (LGPD)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Quando o módulo "portal-cliente" / DPO formal for implementado, o texto do aceite e a política de privacidade devem passar por advogado humano licenciado antes do go-live público.

---

## Veredito

**APROVADO COM RESSALVAS.** O plano US-CLI-001 está juridicamente sólido na arquitetura (RAT-03 já catalogado em `lgpd-rat.md`, INV-024 dedup, INV-013 audit, INV-TENANT-001/002 isolamento). As ressalvas abaixo são ajustes finos pra refletir corretamente o papel de **operador** do Aferê (controlador é o tenant) e proteger contra reabertura regulatória.

### Ressalvas (R1–R6)

1. **R1 — Texto do aceite precisa refletir que o tenant é o controlador.** O aceite que o cliente final do tenant dá no formulário NÃO é "concordo que Aferê trate meus dados" — é "concordo que [Razão Social do Tenant] trate meus dados, usando Aferê como operador". Plano não tem essa nuance no AC-2; ver texto sugerido §3.
2. **R2 — `aceite_lgpd_em` (datetime) é insuficiente.** Snapshot legal exige também: `aceite_lgpd_versao_texto` (FK pro texto vigente no momento — versionamento imutável) + `aceite_lgpd_ip_hash` (prova de origem, INV-013) + `aceite_lgpd_finalidade_id` (FK pro catálogo de finalidades, T-CLI-002). Sem esses 3 campos, em 2 anos não dá pra provar a ANPD "qual texto o titular aceitou em [data]". Tornar nullable só `ip_hash` (cadastro feito pelo atendente no balcão não tem IP do titular — registrar então `aceite_origem: balcao|portal|importacao`).
3. **R3 — PJ não exige aceite LGPD da PJ em si**, mas **EXIGE** quando o cadastro coleta dado de pessoa física associada (sócio, representante legal, contato responsável). Plano e PRD não distinguem. Recomendação: tornar `aceite_lgpd_em` **obrigatório para PF** e **obrigatório para PJ apenas quando `contatos[].cpf IS NOT NULL OR socios[].cpf IS NOT NULL`**. Em PJ "limpa" (sem PF associada), aceite é dispensável — registrar `aceite_lgpd_em = NULL, aceite_lgpd_dispensa_motivo = "pj_sem_pf_associada"`.
4. **R4 — Direitos do titular (art. 18) NÃO precisam ser implementados neste plano**, mas a UI de cadastro **PRECISA** exibir link "Como exercer seus direitos LGPD" apontando pra página pública do tenant com DPO+canal (INV-006). Plano não menciona. Recomendação: AC novo `AC-CLI-001-3 — UI mostra link "direitos LGPD" abaixo do checkbox do aceite, apontando pra rota `/{tenant_slug}/lgpd` (página pode ser placeholder até módulo `lgpd-portal` da Wave B existir)`. Sem isso, INV-006 fica decorativa no cadastro.
5. **R5 — Retenção: ok diferir crypto-shredding pra Wave B**, mas registrar em comentário no modelo `Cliente` que `aceite_lgpd_em` E `aceite_lgpd_ip_hash` são **dados acessórios à execução do contrato** (LGPD art. 16 II) e seguem a mesma matriz de retenção do cliente principal (`docs/conformidade/comum/retencao-matriz.md` — 5 anos fiscal default + ciclo ISO 17025 quando houver certificado emitido). Não esquecer no crypto-shredding da Wave B.
6. **R6 — Cliente estrangeiro (passaporte/RNE) OK ficar out-of-scope MVP-1**, mas validar que o VO `CPF` (e o `CNPJ` da ADR-0017) **rejeitam** entrada que não seja CPF/CNPJ brasileiro válido com mensagem clara ("cadastro de estrangeiro será suportado em V2"), evitando que atendente force CPF inválido ou use CPF de outra pessoa. Sem essa rejeição explícita, atendente vai inventar workaround — risco LGPD (uso indevido de CPF de terceiro).

### Não-ressalvas (validadas como corretas)

- ✅ **Base legal RAT-03 — operador (controlador é o tenant)**: correto. Aferê não escolhe a base, o tenant escolhe. Base efetiva mais comum no Aferê: art. 7º V (execução de contrato comercial tenant↔cliente final). Quando há obrigação fiscal (NF-e, certificado), reforça com art. 7º II.
- ✅ **Nome + CPF é PII (art. 5º I LGPD), NÃO sensível (art. 5º II)**: correto. Não precisa consentimento separado. "Execução de contrato" basta. Sensível seria saúde/biometria/origem racial — RAT-13 e RAT-14 cobrem essas.
- ✅ **Catálogo de finalidades curto (4 entradas iniciais)**: razoável. As 4 bases do art. 7º que cabem em B2B: `execucao_contrato (V)`, `obrigacao_legal (II)`, `interesse_legitimo (IX)`, `consentimento (I)`. Adicionar `dados_sensiveis (art. 11)` quando módulos de saúde/biometria entrarem.
- ✅ **Soft-delete + retenção 5 anos (US-CLI-005 AC-2)**: correto. LGPD art. 16 I (retenção pra cumprir obrigação legal/regulatória) prevalece sobre direito ao esquecimento quando há OS/certificado emitido pro cliente — ISO 17025 cl. 8.4 (~25 anos) campeão.
- ✅ **Dedup INV-024**: correto. LGPD art. 6º V (qualidade) exige que dado seja exato e atualizado — duplicata viola isso.

---

## Texto sugerido do aceite LGPD (PT-BR, ≤ 2 frases)

> **Para PF (ou PJ com PF associada):**
>
> "Declaro estar ciente de que **[Razão Social do Tenant]** tratará meus dados pessoais (nome, CPF, contato e endereço) para a **execução dos serviços contratados** e para o cumprimento de **obrigações legais e regulatórias** aplicáveis (fiscais, metrológicas e contratuais), conforme art. 7º, incisos II e V, da Lei 13.709/2018 (LGPD). Posso exercer meus direitos de titular (art. 18) pelo canal indicado em **[link: /{tenant_slug}/lgpd]**."

**Justificativa do texto:**
- Cita expressamente o **tenant** como controlador (não o Aferê) — refletindo papel RAT-03.
- Cita **dois incisos** do art. 7º (II + V) porque o cadastro alimenta tanto execução de contrato quanto NF-e/certificado (obrigação legal) — abrange ambas as bases sem precisar refazer aceite quando emite NF-e/certificado.
- Lista **categorias de dado** (nome, CPF, contato, endereço) — atende princípio da transparência (art. 6º VI) e necessidade (art. 6º III); evita "carta branca" genérica.
- Link pra exercer direitos (art. 18) cumpre INV-006 sem exigir DPO formal já implementado.
- **NÃO inclui marketing/lembretes** — esses exigem aceite separado (RAT-06 opt-in WhatsApp), nunca empacotar com aceite de cadastro (vedação de bundle de consentimento, art. 8º §4º).

**Variante para PJ pura (sem PF associada — recomendação R3):**

> "O cadastro desta pessoa jurídica não trata dados pessoais de pessoa física e, portanto, está fora do âmbito da LGPD (Lei 13.709/2018 art. 1º). Caso sejam adicionados sócios, representantes ou contatos pessoa física, o aceite LGPD será solicitado naquele momento."

---

## Análise por área

### LGPD / Privacidade

- **Papel correto:** Aferê = operador (LGPD art. 5º VII); tenant = controlador (art. 5º VI). RAT-03 já formaliza isso. Toda comunicação de aceite, política de privacidade e exercício de direito é do **tenant**, não do Aferê.
- **Base legal default:** art. 7º V (execução de contrato comercial tenant↔cliente final) + art. 7º II (quando emite NF-e/certificado, obrigação fiscal/regulatória). Não é "obrigação legal vs execução de contrato" — é **as duas**, sequencialmente: cadastra pra contratar; ao emitir NF-e/cert, ativa obrigação legal.
- **Não é dado sensível:** art. 11 não se aplica a nome/CPF/contato. Aplica quando ASO/saúde/biometria entram (RAT-13/14 — fora do US-CLI-001).
- **PJ vs PF:** LGPD art. 1º cobre apenas PF. Cadastro de PJ "limpa" (CNPJ + razão + endereço corporativo) está fora da LGPD. Quando há sócio/contato PF (`socios[].cpf` ou `contatos[].cpf` preenchido), a PJ se torna controladora dos dados dessa PF e o aceite passa a ser exigido (recomendação R3).
- **Direitos do titular (art. 18):** Aferê encaminha pro tenant em ≤24h (já em `lgpd-rat.md` §4). UI do US-CLI-001 só precisa expor o **link** pro canal do tenant (ressalva R4).
- **Retenção:** art. 16 II (acessórios à execução do contrato) — alinhado com retenção matriz.

### Contratual

- DPA tenant↔Aferê deve ter cláusula expressa: "tenant é controlador, define base legal e finalidade; Aferê executa instruções documentadas do tenant" (modelo em `docs/conformidade/comum/dpa-modelo.md`, draft).
- Quando atendente do tenant cadastra cliente no balcão, a "instrução documentada" é o **fluxo do produto** — não precisa contrato separado por cliente final.

### Regulatório (ANPD)

- **Res. CD/ANPD 15/2024 (incidente):** se vazar cadastro de cliente final, o **tenant** comunica ANPD em ≤3 dias úteis. Aferê **comunica o tenant em ≤24h** após detecção (cláusula DPA). INV-005 cobre.
- **Res. CD/ANPD 18/2024 (DPO):** o tenant deve ter DPO publicado (INV-006). Aferê (operador) **não é obrigado** a ter DPO próprio pela Res. 18 — mas Roldão decidiu publicar voluntariamente em V2 (`lgpd-rat.md` §1). Pra MVP-1 dogfooding, link "/lgpd" pode apontar pra página estática com e-mail do Roldão como contato.
- **Diferencial Aferê (vs Calibre.Software):** mystery shopping documental mostrou Calibre com base legal "consentimento" pra cadastro de cliente final (errado — leva a problema quando cliente revoga e a OS continua aberta) e sem versionamento de texto de aceite. Texto sugerido §3 + ressalva R2 (versionamento) constroem esse diferencial.

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Aceite sem versionamento — ANPD pergunta "qual texto foi aceito em [data]" e não há resposta | Média | Multa ANPD (2% faturamento, limitado a R$ 50M) | R2 — adicionar `aceite_lgpd_versao_texto` + `aceite_lgpd_ip_hash` + `aceite_lgpd_finalidade_id` |
| UI sem link pra direitos do titular — INV-006 decorativa | Alta sem R4; Baixa com R4 | NC LGPD + reclamação titular | R4 — AC-CLI-001-3 com link "/lgpd" placeholder |
| PJ sem PF associada exigindo aceite desnecessariamente — atrito UX | Alta sem R3 | UX ruim + risco de admin marcar checkbox por padrão (vicia consentimento) | R3 — `aceite_lgpd_em` obrigatório só se PF ou PJ com PF associada |
| Bundle de consentimento (cadastro + marketing no mesmo aceite) — art. 8º §4º vedação | Média se UI for descuidada | NC LGPD + ressentimento do titular | Texto sugerido NÃO inclui marketing; RAT-06 (lembrete WhatsApp) tem opt-in separado |
| Workaround do atendente pra cadastrar estrangeiro com CPF inválido | Alta | Uso indevido de CPF de terceiro + falha de qualidade (art. 6º V) | R6 — VO `CPF`/`CNPJ` rejeita com mensagem clara "estrangeiro V2" |
| Crypto-shredding na Wave B esquece `aceite_lgpd_ip_hash` | Média | Resíduo de PII após exclusão = NC | R5 — comentário no modelo + checklist Wave B |

---

## Próximos passos

- ✅ Aplicar R1–R6 no plano `US-CLI-001.md` (autoria: agente que implementar — tech-lead ou implementador).
- ✅ Criar `docs/conformidade/comum/finalidades-lgpd.md` (T-CLI-002) com as 4 finalidades iniciais e referência cruzada pra `lgpd-rat.md` §3.
- ⚠️ **Antes do go-live público do Aferê** (não MVP-1 dogfooding): texto do aceite §3 PRECISA revisão de advogado humano com OAB ativa porque será exibido a milhares de titulares e qualquer ambiguidade vira reclamação ANPD. Recomendo contratar consulta pontual com advogado especialista em LGPD (perfil: 5+ anos LGPD, experiência com SaaS B2B operador); preparei este parecer + RAT completo pra otimizar o tempo dele/dela (estimado 2-3h de revisão).
- ⏳ Diferido pra Wave B: implementação da página `/{tenant_slug}/lgpd` (módulo `lgpd-portal`) — placeholder estática serve no MVP-1.
- ⏳ Diferido pra módulo separado: portabilidade (export JSON art. 18 V), revogação programática, anonimização (crypto-shredding).

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 1º, 5º I/II/VI/VII, 6º III/V/VI, 7º I/II/V/IX, 8º §4º, 11, 16 I/II, 18, 37
- Res. CD/ANPD 15/2024 — incidentes
- Res. CD/ANPD 18/2024 — DPO
- ISO/IEC 17025 cl. 8.4 — retenção de registros
- INV-005, INV-006, INV-010, INV-013, INV-024, INV-TENANT-001/002 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03, RAT-04, RAT-05 (`docs/conformidade/comum/lgpd-rat.md`)
- ADR-0017 (CNPJ alfanumérico — IN RFB 2.229/2024)
