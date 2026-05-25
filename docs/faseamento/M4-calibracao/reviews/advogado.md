---
owner: advogado-saas-regulado
revisado_em: 2026-05-25
status: stable
tipo: review-p2-advogado
marco: Wave A Marco 4 — metrologia/calibracao
fase-ritual: P2
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/adr/0021-anonimizacao-vs-retencao-regulatoria.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0029-canonicalizacao-texto-probatorio.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
  - docs/conformidade/comum/dpia/dpia-calibracao.md
  - REGRAS-INEGOCIAVEIS.md
  - docs/faseamento/M3-os/reviews/advogado.md
---

# Parecer Jurídico Consultivo — Review P2 Advogado / Marco 4 (metrologia/calibracao)

> **SELO:** PARECER CONSULTIVO IA — NÃO SUBSTITUI VALIDAÇÃO OAB HUMANA.
> Este documento é parecer de subagente IA sem inscrição OAB. Onde marcado `🔴 REQUER OAB`, advogado humano licenciado deve revalidar **antes do 1º tenant externo pago**. Para dogfooding (Balanças Solution) o parecer destrava P3 sob INV-RITUAL-001, mas as flags 🔴 ficam rastreadas como GATEs Wave A.

## Resumo executivo

A spec do Marco 4 é, sob lente jurídica, **mais densa e arriscada que a do Marco 3 OS** — concentra três vetores sensíveis: (i) subcontratação cl. 6.6 (US-CAL-017 — relação triangular tenant↔cliente↔subcontratado com DPA cl. 4.7); (ii) **decisão técnica vinculante com override do cliente** (ADR-0024 — quem assume risco quando regra escolhida pelo cliente falha?); (iii) **retenção 25a metrológica vs LGPD art. 18** (ADR-0021 Zona B preserva `cliente_referencia_hash` por 25 anos, hash de CPF/contato técnico inclusive). Os INVs `INV-CAL-TXT-001`, `INV-CAL-SUBC-001..004`, `INV-CAL-FRAUDE-*` e `INV-HMAC-001..005` cobrem a estrutura técnica; a **camada contratual/probatória ainda tem 8 lacunas materiais** que precisam virar T-CAL ou GATEs antes do `/implement` Fase 5+ e antes de tenant externo pago.

**Veredito por severidade (INV-RITUAL-001 — MÉDIO+ bloqueia fechamento de fase):**
- **BLOQUEANTE (0):** nenhum achado bloqueia P2.
- **MÉDIO ajustado (6):** P-CAL-A1, P-CAL-A2, P-CAL-A3, P-CAL-A4, P-CAL-A5, P-CAL-A6 — exigem retrofit em spec/plan/tasks ou criação de GATE Wave A com data-limite (MÉDIO trata como bloqueante de fechamento de fase).
- **ACEITE com GATE Wave A (2):** P-CAL-A7, P-CAL-A8 — risco residual mitigável, ficam rastreados.

**Flag transversal — 🔴 REQUER OAB HUMANA:**
- Texto canônico `aceite-subcontratacao-v1.0.md` (US-CAL-017).
- Modelo de DPA cl. 4.7 com `LaboratorioSubcontratado` (CNPJ + acreditação + sub-subcontratação proibida).
- DPIA-calibracao (atualmente em minuta — `aguarda-revisao-oab: true`).
- Texto canônico de `OverrideRegraDecisaoCliente` (ADR-0024 — distribuição de risco contratual).
- Texto canônico de `ConsentimentoFotoEvidenciaRecepcao` (cl. 7.4 — base legal explícita ao cliente).
- Lista palavra-chave saúde estendida `INV-CAL-TXT-001` (paciente, leito, prontuário, gestante, pediatra — art. 11 LGPD).
- Política de contestação de decisão pós-emissão (CDC art. 26 + 30 dias).

---

## Análise por área

### LGPD / Privacidade

- **Foto de instrumento (cl. 7.4 + RecepcaoItemCalibracao §3.2):** a spec declara `foto_evidencia_id UUID NULL FK` e "cliente pode recusar foto", mas **não declara a base legal** sob a qual a foto é coletada quando o cliente NÃO recusa. Sem isso, em fiscalização ANPD, a foto entra como tratamento sem hipótese legal — vetor de auto-de-infração ANPD art. 7º. Ver P-CAL-A5.
- **Cliente PJ → contato PF (RAT-09):** PRD §311 menciona `LaboratorioSubcontratado.contato_comercial_hash` + `contato_tecnico_hash` mas a spec **não tem RAT-09 reciprocamente** para o **contato PF do cliente do tenant** (quem recebe o cert, quem assina aceite, quem aprova subcontratação). A base legal pra processar esse PF deveria estar declarada explicitamente — execução de contrato (art. 7º V) cobre o contato contratual, mas **não cobre o RT do cliente** que assina aceite biométrico (art. 11 II — dado sensível biométrico exige base própria). Ver P-CAL-A6.
- **Subcontratação cl. 6.6 + LGPD art. 11 + cl. 4.7 ISO:** a spec exige `dpa_versao` em `LaboratorioSubcontratado` mas **não declara onde está o modelo** do DPA, nem se o DPA proíbe sub-subcontratação (NG-CAL-13 declara non-goal técnico, mas DPA contratual precisa fechar isso expressamente). Sem DPA assinado o subcontratado vira **operador de fato sem contrato escrito** — LGPD art. 39 §1º veda. Ver P-CAL-A1.
- **AceiteSubcontratacao biometria touch:** `assinatura_payload_encrypted` herda INV-OS-ACEITE-BIO-001 (KMS dedicada). Boa estrutura técnica. **Gap:** texto canônico v1.0 não existe ainda; tela de captura do consentimento art. 11 II "a" (paralelo a P-OS-A1 do M3) não está descrita como AC binário em US-CAL-017. Ver P-CAL-A1.
- **Anti-PII INV-CAL-TXT-001 — 10 campos:** lista é boa (`razao_correcao`, `motivo_cancelamento`, `descricao_nc`, `causa_raiz`, `acao_corretiva`, `motivo_subcontratacao`, `justificativa_excecao_2a_conf`, `observacoes_gerais`, `decisao_manual_se_zona`, `motivo_inaptidao`). Aplica regex herdada de INV-OS-TXT-001 (CPF/CNPJ/email/tel/nomes). **Gap:** mesmo problema de falso-negativo do M3 (P-OS-A3) — calibração de instrumento médico em hospital vai trazer "balança pediátrica", "berço aquecido neonatal", "infusora paciente leito 305". Sem extensão de regex + lista palavra-chave saúde, art. 11 LGPD vaza em audit WORM 25a. Ver P-CAL-A2.
- **EXIF strip em INV-CAL-FOTO-001:** spec referencia o INV (linha 158 REGRAS) mas **não declara teste/hook** que valide strip antes do upload. Sem hook, primeira foto vaza GPS do laboratório (sigilo industrial LPI art. 195) + endereço do cliente. Ver P-CAL-A7.

### Contratual

- **Override de regra de decisão pelo cliente (ADR-0024 + US-CAL-002):** este é o achado **mais sensível juridicamente**. A spec permite que o cliente requisite `regra_decisao_override_cliente = true` com assinatura ADR-0029. **O ADR-0024 declara que "override exige cláusula contratual ativa do tenant↔cliente" (INV-CAL-DEC-002) mas não existe modelo de cláusula nem mecanismo de verificação** dessa cláusula no fluxo. Risco material: cliente farma escolhe Aceitação Simples (em vez de Banda de Guarda 30%), instrumento aprova marginalmente, paciente é dosado errado, ação indenizatória cai sobre o tenant — porque sem contrato escrito que distribua o risco, **o Código Civil art. 927 §único atribui responsabilidade ao prestador do serviço técnico** (atividade de risco). Ver P-CAL-A3.
- **Lock pós-emissão (ADR-0024 INV-CAL-DEC-003):** lock impede fraude técnica, mas **não impede contestação do cliente sob CDC art. 26** (30 dias para reclamação de serviço aparente; 90 dias para vício oculto). A spec não declara fluxo de contestação pré-recall (recall fica em Marco 5/ADR-0045). Ver P-CAL-A4.
- **AceiteSubcontratacao com assinatura touch (US-CAL-017 AC-CAL-017-3):** a Lei 14.063/2020 art. 4º dá validade jurídica à assinatura eletrônica simples APENAS para atos de baixo a médio risco — **subcontratação de serviço metrológico ICP-Brasil-rastreável é alto risco probatório**. Touch pode ser questionado em juízo cível; A3 deveria ser o default (touch como fallback documentado). Ver P-CAL-A1.
- **Texto certificado declara subcontratação (AC-CAL-017-4):** texto está correto mas a spec **não menciona se o cliente final pode recusar receber cert subcontratado** (CDC art. 6º III — direito à informação prévia). Se cliente consentiu subcontratação MAS depois recebe cert e reclama, é "vício de informação" CDC art. 30. Texto canônico do aceite deve declarar **expressamente** que o cert virá com subcontratação declarada. Ver P-CAL-A1.

### Regulatório

- **Retenção 25a × LGPD art. 18 (Zona B ADR-0021):** ADR aceita preserva CNPJ + razão social + endereço fiscal 25 anos por obrigação legal CTN art. 173 + ISO 17025 §8.4. **Defesa jurídica é sólida** para cliente PJ. **Mas** o `cliente_referencia_hash` em `Calibracao` é hash do CPF do cliente PF (quando aplicável) ou CNPJ. Para cliente PF que invoque eliminação dura e não tenha NF nem cert emitido **na época do pedido** mas **passou a ter depois** (calibração concluída pós-pedido), há janela onde Zona A se aplica mas dado vira Zona B retroativamente — sem trigger explícito que **bloqueie nova calibração para cliente em processo de eliminação ativa**. Ver P-CAL-A8.
- **DPIA-calibracao status `minuta`:** Spec §2.4 declara que DPIA é minuta e aguarda OAB. Mesma estrutura do M3 (P-OS-A6). Linguagem está coerente. **Não há drift no M4 nesta dimensão** — bom.
- **CAPA cl. 7.10/8.7 `NaoConformidade.descricao` + `causa_raiz`:** spec aplica INV-CAL-TXT-001 + canonicalização INV-DOC-CANON-001 + hash. Estrutura sólida. **Gap:** `responsavel_acao_user_id` UUID cru em `NaoConformidade` (linha 338 — não declarado como hash). Esse UUID é PII (identifica colaborador). Audit WORM 25a guarda UUID cru = vetor de stalking trabalhista. Ver P-CAL-A2.
- **Subcontratação + transferência internacional:** spec não exclui `LaboratorioSubcontratado` no exterior. Se subcontratado está fora do Brasil, LGPD art. 33 exige base legal específica (decisão de adequação ANPD ou cláusulas-padrão). Hoje não há país com decisão de adequação ANPD vigente. Ver P-CAL-A1.

---

## Achados

### P-CAL-A1 — Subcontratação (US-CAL-017): 4 lacunas contratuais cumulativas

**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001) — bloqueante de fase

**Evidência:** Spec §3.2 `LaboratorioSubcontratado.dpa_versao VARCHAR(20)`; AceiteSubcontratacao `texto_canonico_id UUID NOT NULL FK → docs/conformidade/comum/termos/aceite-subcontratacao-v1.0.md` (declarado como REQUER OAB); `assinatura_payload_encrypted BYTEA NULL (touch ou A3)`; NG-CAL-13 declara sub-subcontratação non-goal técnico mas DPA contratual não fecha.

**Base legal:** LGPD art. 11 II "a" + art. 39 §1º (operador exige contrato escrito) + art. 33 (transferência internacional) + Lei 14.063/2020 art. 4º (assinatura eletrônica simples — alto risco) + CDC art. 6º III + cl. 4.7 ISO/IEC 17025 + ILAC G18.

**Análise:** quatro gaps cumulativos no mesmo fluxo:
1. **Modelo DPA cl. 4.7 inexistente** — `dpa_versao` referencia versão de um documento que ainda não foi escrito. Sem DPA assinado, subcontratado opera sem contrato de operador LGPD = art. 39 §1º violado.
2. **Sub-subcontratação só está proibida tecnicamente (NG-CAL-13)** — contratualmente o subcontratado pode terceirizar para um 3º lab sem o tenant principal saber. DPA deve trazer cláusula expressa.
3. **Touch como assinatura válida em alto risco** — Lei 14.063 art. 4º exige avançada/qualificada para alto risco probatório. A3 deve ser default; touch só com declaração de aceite consciente.
4. **Transferência internacional sem cláusula** — `LaboratorioSubcontratado` pode estar no exterior; LGPD art. 33 exige base. Spec não bloqueia.

**Decisão recomendada:**
1. **Criar `docs/conformidade/comum/minutas/dpa-laboratorio-subcontratado-v1.0.md`** (status `minuta — aguarda-revisao-oab: true`) com cláusulas mínimas: (a) papel operador LGPD; (b) finalidade restrita à calibração contratada; (c) proibição expressa de sub-subcontratação; (d) DPO do subcontratado; (e) prazo de retenção alinhado a ISO 17025 §8.4; (f) plano de incidente Res. ANPD 15/2024 cascateado; (g) cláusula de transferência internacional só com decisão de adequação ANPD vigente ou cláusulas-padrão aprovadas; (h) auditoria anual do tenant principal sobre o subcontratado.
2. **Criar `docs/conformidade/comum/termos/aceite-subcontratacao-v1.0.md`** (canonicalização INV-DOC-CANON-001) declarando ao cliente: (a) que serviço será realizado em outro laboratório acreditado X com credenciamento Y; (b) que dado do instrumento e do cliente serão transferidos para o subcontratado; (c) que cert final declarará a subcontratação; (d) que tenant principal mantém responsabilidade técnica total perante cliente (cl. 6.6 ISO + art. 14 CDC — solidariedade do fornecedor); (e) opção real de recusa (que abre fluxo alternativo: tenant indica outro lab, cliente busca outro lab, ou cliente desiste).
3. **Adicionar AC-CAL-017-7:** `GIVEN subcontratação iniciada, WHEN assinatura touch usada em vez de A3, THEN sistema marca alerta P3 + grava no audit indicação "touch-em-alto-risco" + exige declaração canonicalizada do cliente "li e aceito assinar por touch" (texto canônico extra).` Default A3.
4. **Adicionar AC-CAL-017-8:** `GIVEN LaboratorioSubcontratado.pais != BR, WHEN configurar subcontratação, THEN sistema bloqueia 412 SubcontratadoForaBR_TransferenciaInternacionalSemBase — destrava só com cláusulas-padrão ANPD aprovadas (campo dpa_clausulas_internacionais_id NOT NULL).`
5. **Criar INV-CAL-SUBC-005:** `LaboratorioSubcontratado.dpa_versao deve resolver para arquivo existente em docs/conformidade/comum/minutas/ com status != minuta na data da configuração; subcontratado sem DPA aceito = 412 DPAFaltante.`
6. **🔴 REQUER OAB:** DPA + texto aceite v1.0 + texto "touch-em-alto-risco" — todos os 3 documentos precisam revisão OAB antes do 1º tenant externo pago. GATE-CAL-SUBC-OAB criado.

### P-CAL-A2 — INV-CAL-TXT-001 anti-PII: falsos negativos médicos + UUID cru em NaoConformidade

**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Evidência:** REGRAS linha 157 — INV-CAL-TXT-001 lista 10 campos com regex herdada de INV-OS-TXT-001 (P-OS-A3 já estendeu pra saúde no M3). Spec §3.2 `NaoConformidade.responsavel_acao_user_id UUID NOT NULL` cru (não hash).

**Base legal:** LGPD art. 5º I + art. 11 (dado sensível saúde) + Res. CD/ANPD 2/2022 art. 2º III (singling out) + art. 37 (registro do operador).

**Análise:** dois gaps:
1. **Regex de calibração herda M3 mas calibração roda em ambiente médico/farma** — campos como `RecepcaoItemCalibracao.motivo_inaptidao` em hospital trarão "infusora UTI neonatal", "balança pediátrica leito 12", "pHmetro lab gestantes". O M3 já endereçou no P-OS-A3 (regex saúde extendida + lista palavra-chave + quarentena). **A spec do M4 não confirma que herda essa extensão** — apenas referencia "INV-EQP-LOC-001 estendida". Precisa cravar.
2. **`responsavel_acao_user_id` UUID cru em NaoConformidade (linha 338)** — INV-CAL-AUD-001 (linha 159 REGRAS) proíbe UUID cru de operador em EventoDeCalibracao, mas NaoConformidade não está coberta. Audit WORM 25a guarda UUID cru = stalking trabalhista (igual P-OS-A2).

**Decisão recomendada:**
1. Atualizar INV-CAL-TXT-001 referenciando expressamente extensão saúde do INV-OS-TXT-001 (P-OS-A3): regex endereço + sequência numérica ≥7 dígitos + lista palavra-chave saúde (`paciente|leito|prontuário|menor|criança|gestante|HIV|positivo|pediátrica|neonatal|UTI|infusora`) + normalização NFC + lowercase. Quarentena 24h gerente.
2. Adicionar `responsavel_acao_user_id_hash CHAR(80) NOT NULL` em `NaoConformidade` (paralelo a `corretor_id_hash` em LeituraCorrecao). UUID cru fica em campo auxiliar `responsavel_acao_user_id UUID NULL` SOMENTE em zona quente (≤90d); após esse prazo, job procrastinate `nc-responsavel-pseudonimizacao` zera UUID cru e fica só o hash. INV-CAL-NC-002 NOVA.
3. **🔴 REQUER OAB:** lista palavra-chave saúde estendida pra ambiente farma/medical — definição operacional art. 11 LGPD. GATE-CAL-PII-SAUDE-OAB.

### P-CAL-A3 — Override regra de decisão pelo cliente (US-CAL-002 + ADR-0024): cláusula contratual exigida mas não verificada

**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Evidência:** Spec §3.2 `regra_decisao_override_cliente BOOLEAN DEFAULT false (true se cliente requisitou override em US-CAL-002 com assinatura ADR-0029)`. ADR-0024 INV-CAL-DEC-002: "override de cliente exige cláusula contratual ativa do tenant↔cliente". **Spec não tem AC binário que VERIFIQUE a cláusula** antes de aceitar o override. R-M4-04 lista o risco mas mitigação atual é só "snapshot + lock" — não distribuição de responsabilidade.

**Base legal:** Código Civil art. 927 §único (atividade de risco — responsabilidade objetiva); CDC art. 14 (solidariedade do fornecedor); CDC art. 25 (vedação de cláusula que exonere); LGPD art. 7º V; ISO 17025 cl. 7.8.6.

**Análise:** sem cláusula contratual válida do cliente assumindo o risco da regra escolhida, o art. 927 §único do CC aplica — atividade metrológica com instrumento médico é de risco; responsabilidade objetiva do prestador. Cliente farma escolheu Aceitação Simples (em vez de Banda de Guarda 30%), instrumento aprovou marginalmente, paciente dosado errado — tenant é réu solidário (CDC art. 14) e arca com indenização **mesmo tendo o `regra_decisao_override_cliente=true` no snapshot**, porque cláusulas que exoneram fornecedor de responsabilidade por defeito de serviço são nulas (CDC art. 25).

A defesa só funciona se: (a) houver contrato escrito entre tenant↔cliente que distribua risco técnico explicitamente, com assinatura ICP-Brasil; (b) cláusula passar no controle judicial CDC art. 51 (cláusula abusiva); (c) decisão técnica de fato refletir escolha consciente e informada do cliente (laudo + memorial de cálculo).

**Decisão recomendada:**
1. **Criar entidade `OverrideRegraDecisaoCliente`** (Padrão B imutável): `id, tenant_id, cliente_id, calibracao_id, regra_escolhida, regra_default_tenant, justificativa_canonicalizada (≥100 chars anti-PII), contrato_clausula_referencia_id UUID NOT NULL FK, assinatura_a3_cliente_payload_encrypted BYTEA NOT NULL, validade_inicio TIMESTAMPTZ NOT NULL, validade_fim TIMESTAMPTZ NULL, audit_evento_id UUID NOT NULL`.
2. **Adicionar AC-CAL-002-3:** `GIVEN cliente requisita override de regra de decisão, WHEN tenant tenta aceitar, THEN sistema exige (a) cláusula contratual ativa vigente (predicate clausula_override_vigente(cliente_id, em_data)) + (b) assinatura A3 do cliente (NÃO touch) + (c) justificativa canonicalizada ≥100 chars anti-PII; ausente → 412 OverrideSemContratoOuA3.`
3. **Criar INV-CAL-DEC-002 (já existe mas precisa hook):** hook `override-regra-decisao-contrato-check.sh` valida no commit que use case `configurar_calibracao` invoca predicate `clausula_override_vigente` quando `regra_decisao_override_cliente=true`.
4. **Criar `docs/conformidade/comum/minutas/clausula-override-regra-decisao-v1.0.md`** com texto canônico que: (a) reconheça que regra padrão do tenant é X; (b) cliente assume responsabilidade técnica pela escolha alternativa Y; (c) tenant cumpre dever de informação sobre consequência técnica; (d) **NÃO declare exoneração total** (não passa CDC art. 25) — declare que cliente é coobrigado solidário no risco do método.
5. **🔴 REQUER OAB:** o texto da cláusula é o ponto crítico — passa pelo controle CDC art. 51 (cláusula abusiva). OAB humana deve redigir. GATE-CAL-OVERRIDE-OAB.

### P-CAL-A4 — Lock pós-emissão (ADR-0024) sem fluxo de contestação CDC art. 26

**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Evidência:** ADR-0024 §"Lock pós-emissão" — `Calibracao.status = APROVADA + cert EMITIDO → regra_decisao imutável`. INV-CAL-DEC-003. Spec §4 declara "Estado `aprovada` é IMUTÁVEL — reprocessar exige nova calibração com `causation_id` apontando à anterior." **Não há fluxo de contestação pré-recall** (recall é Marco 5/ADR-0045).

**Base legal:** CDC art. 26 (30 dias reclamação serviço aparente; 90 dias vício oculto) + CDC art. 50 (garantia contratual sem prejuízo da legal) + ISO 17025 cl. 7.9 (reclamações).

**Análise:** cliente que recebe cert e suspeita de erro técnico (ex: medição contradiz histórico do instrumento) tem 30/90 dias por lei pra reclamar. Hoje a spec faz `aprovada → imutável → nova calibração com causation_id`. Isso é **operacionalmente correto** mas **juridicamente não basta**: o cliente precisa ter um canal formal de **reclamação registrada com prazo de resposta**, não só "abra outra calibração". cl. 7.9 ISO 17025 EXIGE procedimento documentado de reclamações.

**Decisão recomendada:**
1. **Criar entidade `ReclamacaoCalibracao`** (Padrão B imutável + estado-máquina): `id, tenant_id, calibracao_id, certificado_id NULL, reclamante_referencia_hash, descricao_canonicalizada (≥30 chars anti-PII INV-CAL-TXT-001), recebida_em, prazo_resposta_dia_util, respondida_em NULL, decisao VARCHAR(30) (PROCEDENTE_RECALL | PROCEDENTE_ERRATA | IMPROCEDENTE_FUNDAMENTADA), resposta_canonicalizada NULL, correlation_id`.
2. **Adicionar US-CAL-018:** "Reclamação do cliente sobre calibração emitida (cl. 7.9 + CDC art. 26)" — 4 AC: (a) abrir reclamação dentro de 90 dias da emissão (CDC); (b) atribuir RT independente (preferencialmente não o conferente da calibração original); (c) resposta fundamentada em ≤15 dias úteis; (d) decisão dispara Marco 5 saga apropriada (RECALL/ERRATA/manter).
3. **Adicionar nota no §15 Sumário pra Roldão:** "o que o cliente vê de novo (10): canal de reclamação técnica da calibração emitida — registro, RT independente, resposta em 15 dias úteis".
4. **GATE-CAL-RECLAMACAO-FLUXO** Wave A (não bloqueia M4 dogfooding; bloqueia 1º tenant externo).

### P-CAL-A5 — Foto evidência em RecepcaoItemCalibracao sem base legal declarada + EXIF strip não-testado

**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Evidência:** Spec §3.2 `RecepcaoItemCalibracao.foto_evidencia_id UUID NULL FK ("EvidenciaFotoAtividade" — opcional; cliente pode recusar foto)`. REGRAS linha 158 INV-CAL-FOTO-001 declara EXIF strip + blur + watermark mas spec não declara teste/hook que valide.

**Base legal:** LGPD art. 7º (bases legais) + art. 11 (sensível) + LPI art. 195 (sigilo industrial) + cl. 7.4 ISO 17025 (registro de itens).

**Análise:** "cliente pode recusar foto" é ótimo do ponto de vista de proporcionalidade, mas **quando ele NÃO recusa, sob qual base legal a foto entra?** Opções:
- art. 7º V (execução de contrato): sustentável se contrato de calibração menciona evidência fotográfica;
- art. 7º IX (legítimo interesse): exige teste de balanceamento documentado (RIPD);
- art. 7º I (consentimento): aceita mas frágil (consentimento pode ser revogado).

Sem **declaração explícita da base legal no momento da coleta** (tela do operador mostra ao cliente "esta foto será usada para X com base legal Y"), em fiscalização ANPD a foto é tratamento sem base.

**Decisão recomendada:**
1. **Criar `docs/conformidade/comum/termos/aviso-foto-recepcao-v1.0.md`** (canonicalização INV-DOC-CANON-001) declarando ao cliente: (a) finalidade (registro técnico cl. 7.4 ISO 17025 — identificação do item, estado de recebimento, evidência de eventuais danos); (b) base legal preferencial: **legítimo interesse** (art. 7º IX) com teste de balanceamento documentado em RIPD-Calibracao + fallback consentimento; (c) prazo de retenção (alinhado à calibração — Zona B se cert emitido); (d) direito de recusa sem prejuízo do serviço.
2. **Adicionar AC-CAL-001-3:** `GIVEN cliente apresenta instrumento na recepção, WHEN operador for capturar foto evidência, THEN sistema exibe texto canônico aviso-foto-recepcao + botão "concordo" (entra em RecepcaoItemCalibracao.foto_evidencia_id) ou "recuso" (entra em RecepcaoItemCalibracao.foto_evidencia_recusa_id apontando para entidade ConsentimentoFotoRecusado).`
3. **Criar hook `foto-exif-strip-check.sh`** (Fase 9 M4) — valida no upload que metadados EXIF foram strippados; teste de regressão `test_inv_cal_foto_001_exif_strip.py` com foto contendo GPS antes/depois.
4. **🔴 REQUER OAB:** texto canônico aviso-foto-recepcao + teste de balanceamento legítimo interesse RIPD-Calibracao. GATE-CAL-FOTO-OAB.

### P-CAL-A6 — Contato técnico do cliente (RAT-09) sem base legal explícita para biometria/A3

**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Evidência:** Spec §3.2 — `Calibracao.cliente_referencia_hash` (do cliente PJ); `AceiteSubcontratacao.cliente_referencia_hash` (idem). PRD §316 referencia "contato técnico" do cliente como assinante. Spec não declara entidade `ContatoTecnicoClienteAssinante` nem base legal para processar biometria/A3 dessa pessoa física.

**Base legal:** LGPD art. 7º V (execução de contrato — cobre contato contratual administrativo) + art. 11 II "g" (Lei 14.063) + art. 11 II "a" (consentimento específico) — para biometria/dado sensível, art. 7º V NÃO basta.

**Análise:** quando cliente PJ designa um contato técnico que assina aceite biométrico (touch) ou A3 (e-CPF), processar dado biométrico/A3 desse PF exige base do art. 11 (sensível) ou art. 7º (não sensível mas requer base explícita para A3). O PRD trata o contato como dado do cliente PJ — incorreto: a pessoa física é titular próprio.

**Decisão recomendada:**
1. **Adicionar RAT-CAL-01** (renumerar RAT-09): "Processamento de dado pessoal de contato técnico de cliente PJ que assina aceites em calibração — base legal: art. 11 II "g" (Lei 14.063 obriga registro) + art. 11 II "a" (consentimento específico no momento da assinatura); finalidade restrita à evidência probatória ISO 17025 + ICP-Brasil; retenção alinhada Zona B 25a se cert emitido."
2. **Criar entidade `ConsentimentoContatoTecnicoCliente`** (paralelo a `ConsentimentoBiometriaTouch` do M3 INV-OS-CONSBIO-001) com `id, tenant_id, cliente_id, contato_pf_referencia_hash, texto_canonico_id, texto_hash, versao_politica, concedido_em, evidencia_renderizacao_id`.
3. **Adicionar INV-CAL-CONT-001:** `AceiteSubcontratacao.consentimento_contato_id NOT NULL quando contato técnico PF assina; sem consentimento → 412 ConsentimentoContatoAusente.`
4. **🔴 REQUER OAB:** texto canônico do consentimento + revisão se "consentimento específico" no contexto B2B é livre (relação assimétrica empregador-empregado pode invalidar). GATE-CAL-CONT-OAB.

### P-CAL-A7 — INV-CAL-FOTO-001 EXIF strip declarado mas sem hook + sigilo industrial LPI art. 195

**Severidade:** ACEITE com GATE Wave A

**Evidência:** REGRAS linha 158 INV-CAL-FOTO-001 — EXIF strip + blur + watermark. Spec §2.3 lista 4 hooks novos M4 P9 mas `foto-exif-strip-check` NÃO ESTÁ na lista; está coberto P-CAL-A5 acima.

**Base legal:** LGPD art. 5º I + LPI art. 195 (sigilo industrial) + ISO 17025 cl. 7.4.

**Análise:** sem hook, primeira foto do laboratório vaza GPS do tenant (endereço da bancada de calibração) — concorrente faz engenharia reversa do escopo CMC observando fotos. Vetor de espionagem industrial.

**Decisão recomendada:**
1. Adicionar `foto-exif-strip-check.sh` à lista §2.3 M4 P9 (5º hook, não 4).
2. Criar GATE-CAL-FOTO-EXIF-HOOK (Wave A) com teste de regressão antes do 1º tenant externo.
3. Risco residual baixo se P-CAL-A5 for endereçado em paralelo (mesma frente de trabalho).

### P-CAL-A8 — Janela retroativa de Zona A → Zona B (cliente PF anonimizado durante calibração em curso)

**Severidade:** ACEITE com GATE Wave A

**Evidência:** Spec §6.2 consumer `Cliente.Anonimizado` — "Propaga `cliente_id=null` + preserva `cliente_referencia_hash` em Calibracao + AceiteSubcontratacao + RecepcaoItemCalibracao". ADR-0021 § "Cliente PF sem vínculo regulatório" prevê DELETE efetivo enquanto não há cert/NF emitido.

**Base legal:** LGPD art. 16 + ADR-0021.

**Análise:** janela temporal: cliente PF abre OS (sem cert ainda — Zona A elegível para DELETE). Calibração roda. Cliente pede eliminação dura no meio. **Hoje o consumer `Cliente.Anonimizado` simplesmente propaga e perde `cliente_id`** — mas calibração ainda não emitiu cert, ainda estaria em Zona A. Se cert é emitido depois, hash sobrevive mas é hash "vazio". Pior: cliente que pediu eliminação acreditando ter direito ao DELETE (Zona A) descobre que cert foi emitido pós-pedido e dado dele virou Zona B 25a.

INV-OS-ANON-001 (REGRAS linha 141) bloqueia anonimização quando OS está aberta. M4 herda? **A spec não declara explicitamente** que calibração em andamento bloqueia anonimização cliente (paralela a INV-OS-ANON-001).

**Decisão recomendada:**
1. **Criar INV-CAL-ANON-001:** `Cliente com Calibracao em status NOT IN ('aprovada','rejeitada','cancelada') bloqueia anonimização Zona A/B (paralelo INV-OS-ANON-001). Módulo Clientes consulta calibrações abertas → 409 AnonimizacaoBloqueadaPorCalibracaoAberta + publica AnonimizacaoBloqueada com calibracao_ids_bloqueantes. Quando calibração atinge estado terminal, watchdog dispara nova tentativa.`
2. **Adicionar consumer M1/M4 cross-check** em `Cliente.AnonimizacaoSolicitada` antes de propagar como `Cliente.Anonimizado`.
3. GATE-CAL-ANON-CONCORRENCIA Wave A (não bloqueia M4 dogfooding — Balanças Solution é PJ; bloqueia 1º tenant externo PF).

---

## Riscos identificados (consolidado)

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| ANPD aplica multa por subcontratação sem DPA cl. 4.7 (art. 39 §1º — até 2% faturamento) | ALTA | ALTO | P-CAL-A1: modelo DPA + INV-CAL-SUBC-005 + GATE-CAL-SUBC-OAB |
| Sub-subcontratação fora de controle do tenant | MÉDIA | ALTO | P-CAL-A1: cláusula expressa no DPA proibindo |
| Transferência internacional sem base ANPD (lab subcontratado fora BR) | BAIXA | CRÍTICO | P-CAL-A1: AC-CAL-017-8 bloqueia + cláusulas-padrão |
| Indenização objetiva (CC art. 927 §único) por override de regra sem cláusula contratual válida | MÉDIA | CRÍTICO | P-CAL-A3: OverrideRegraDecisaoCliente entidade + INV-CAL-DEC-002 hook + cláusula OAB |
| Vazamento art. 11 LGPD em texto livre clínico (paciente/leito/gestante) em audit WORM 25a | ALTA | CRÍTICO | P-CAL-A2: regex saúde estendida + quarentena + lista palavra-chave OAB |
| Stalking trabalhista via UUID cru `responsavel_acao_user_id` em NaoConformidade WORM | MÉDIA | ALTO | P-CAL-A2: hash + pseudonimização pós-90d |
| Reclamação CDC art. 26 sem canal formal = NC cl. 7.9 ISO 17025 | MÉDIA | MÉDIO | P-CAL-A4: ReclamacaoCalibracao + US-CAL-018 |
| Foto recepção sem base legal declarada = tratamento sem hipótese (art. 7º LGPD) | ALTA | MÉDIO | P-CAL-A5: aviso v1.0 + RIPD-Calibracao + hook EXIF |
| Biometria contato técnico cliente PJ sem consentimento art. 11 = nulidade probatória | MÉDIA | ALTO | P-CAL-A6: ConsentimentoContatoTecnicoCliente + INV-CAL-CONT-001 |
| Sigilo industrial laboratório vazado via foto com GPS (LPI art. 195) | MÉDIA | MÉDIO | P-CAL-A7: hook foto-exif-strip-check |
| Cliente PF anonimização durante calibração aberta gera estado inconsistente | BAIXA | MÉDIO | P-CAL-A8: INV-CAL-ANON-001 paralelo INV-OS-ANON-001 |

---

## Limite legítimo — NÃO substitui OAB humana

Os achados abaixo **REQUEREM revisão por advogado humano com OAB ativa antes do 1º tenant externo pago**. Subagente IA não chancela:

1. **🔴 P-CAL-A1** — DPA `LaboratorioSubcontratado` + texto canônico `aceite-subcontratacao-v1.0.md` + texto "touch-em-alto-risco" + cláusulas-padrão transferência internacional. GATE-CAL-SUBC-OAB.
2. **🔴 P-CAL-A2** — lista palavra-chave saúde estendida art. 11 LGPD (definição operacional). GATE-CAL-PII-SAUDE-OAB.
3. **🔴 P-CAL-A3** — texto da cláusula contratual `clausula-override-regra-decisao-v1.0.md` (controle CDC art. 25 + 51). GATE-CAL-OVERRIDE-OAB.
4. **🔴 P-CAL-A5** — aviso foto recepção `aviso-foto-recepcao-v1.0.md` + RIPD-Calibracao teste balanceamento legítimo interesse. GATE-CAL-FOTO-OAB.
5. **🔴 P-CAL-A6** — texto consentimento contato técnico PF + análise se consentimento B2B é livre (relação assimétrica). GATE-CAL-CONT-OAB.
6. **🔴 DPIA-calibracao** — minuta P2 (este parecer + tech-lead + corretora + RBC alimentam); OAB humana revalida e assina antes de tenant externo. GATE-CAL-DPIA-OAB (já listado §9.1 spec).

**Sugiro contratar consulta OAB pontual focada (6-8h)** antes do 1º tenant externo para validar em bloco os 6 documentos canônicos + DPIA-calibracao. Preparei este parecer + spec + ADRs 0021/0024/0026/0029/0064 para otimizar o tempo do(a) advogado(a).

---

## Veredicto

**AJUSTAR.** Spec do M4 calibracao está **estruturalmente sólida sob lente jurídica** (INVs anti-fraude robustos, retenção 25a defensável via ADR-0021, canonicalização texto probatório aplicada, biometria com KMS dedicada herdada do M3). Não há bloqueante crítico. Mas os **6 MÉDIOs (P-CAL-A1..A6)** precisam virar T-CAL-NNN em P3/P4 antes de `/implement` Fase 5+ avançar — INV-RITUAL-001 trata MÉDIO como bloqueante de fechamento de fase. Os 2 ACEITE-com-GATE (P-CAL-A7, P-CAL-A8) ficam rastreados como Wave A.

**Próximos passos:**
- Aplicar 6 achados MÉDIOs em P3 (matriz reconciliação) + P4 (tasks.md) como T-CAL dedicados: `T-CAL-SUBC-DPA-01`, `T-CAL-TXT-SAUDE-02`, `T-CAL-OVERRIDE-CLAUSULA-03`, `T-CAL-RECLAMACAO-CDC-04`, `T-CAL-FOTO-BASE-LEGAL-05`, `T-CAL-CONSENT-CONTATO-06`.
- GATEs Wave A novos rastreados: `GATE-CAL-SUBC-OAB`, `GATE-CAL-PII-SAUDE-OAB`, `GATE-CAL-OVERRIDE-OAB`, `GATE-CAL-RECLAMACAO-FLUXO`, `GATE-CAL-FOTO-OAB`, `GATE-CAL-CONT-OAB`, `GATE-CAL-FOTO-EXIF-HOOK`, `GATE-CAL-ANON-CONCORRENCIA`. Todos bloqueiam 1º tenant externo pago, nenhum bloqueia M4 dogfooding Balanças Solution.
- Auditor-conformidade-lgpd (Família 5) re-roda em P5 com gate INV-RITUAL-001 (ZERO MÉDIO).

> **Reiteração final do selo:** este parecer é consultivo de subagente IA sem OAB. As 6 flags 🔴 REQUER OAB são **inegociáveis** antes do 1º tenant externo pago — não há substituição automatizada para validação OAB humana em textos canônicos contratuais, cláusulas que tocam CDC art. 25/51, e DPIA formalmente aprovado. Para dogfooding Balanças Solution o parecer é suficiente para destravar P3.
