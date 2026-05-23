---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 3 — operacao/os
tipo: review-p2-advogado
fase-ritual: P2 (revisão dos 4 subagentes em paralelo)
autor: subagente advogado-saas-regulado (IA — sem OAB)
selo: "PARECER CONSULTIVO IA — NÃO SUBSTITUI VALIDAÇÃO OAB HUMANA"
relacionados:
  - docs/faseamento/M3-os/spec.md
  - docs/conformidade/comum/dpia/dpia-os.md
  - docs/conformidade/comum/minutas/dpa-modelo-cap-responsabilidade.md
  - docs/conformidade/comum/minutas/politica-de-privacidade-afere-v1.0.md
  - REGRAS-INEGOCIAVEIS.md
  - docs/adr/0021-anonimizacao-vs-retencao.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0029-canonicalizacao-texto-probatorio.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
---

# Parecer Jurídico Consultivo — Review P2 Advogado / Marco 3 (operacao/os)

## Resumo executivo

A spec do Marco 3 está **estruturalmente sólida** sob a ótica LGPD/contratual. Os 17 INV-OS-* + RAT-07/08 endereçam todos os pontos sensíveis cravados nas auditorias 10 lentes (Onda 6 + Onda 7) e a DPIA-OS já cobre biometria touch, geolocalização e foto de campo. Há, contudo, **7 lacunas materiais** que precisam virar T-OS-NNN ou GATEs explícitos antes de `/implement`.

**Veredito por severidade (INV-RITUAL-001):**
- **BLOQUEANTE (zero):** nenhum achado bloqueia P2.
- **AJUSTADO MÉDIO (5):** P-OS-A1, P-OS-A2, P-OS-A3, P-OS-A4, P-OS-A6 — exigem retrofit em spec/plan/tasks ou criação de gate Wave A com data-limite (INV-RITUAL-001 trata MÉDIO como bloqueante de fechamento de fase).
- **ACEITE com gate (2):** P-OS-A5, P-OS-A7 — risco residual baixo, mas ficam rastreados como GATE Wave A.

**Flag transversal — REQUER VALIDAÇÃO OAB HUMANA:**
- DPIA-OS (atualmente `minuta — aguarda-revisao-oab: true`). Spec §2.4 referencia DPIA "aprovada" — terminologia precisa ser ajustada (ver P-OS-A6).
- Cláusula de aceite eletrônico (texto-canon) — força probatória Lei 14.063/2020 art. 4º depende de instrumento contratual entre Tenant e Cliente Final que o subagente IA não pode chancelar.
- Cláusula de dispensa de aceite (US-OS-013) — o termo PDF anexado é instrumento jurídico, REQUER MODELO REVISTO POR OAB.
- DPA cap responsabilidade — `dpa-modelo-cap-responsabilidade.md` (status `minuta`, `aguarda-revisao-oab: true`) — cobertura Marco 3 OK em termos estruturais, mas assinatura com Tenant pago exige OAB.

---

## Análise por área

### LGPD / Privacidade
- **Biometria touch (art. 11):** dupla base legal declarada (art. 11 II "g" Lei 14.063/2020 + art. 11 II "a" consentimento específico) é juridicamente robusta. INV-OS-ACEITE-BIO-001 está completo (chave KMS dedicada por tenant, watermark contextual, validação anti-rabisco, audit obrigatório). **Gap:** o fluxo de captura **do consentimento art. 11** no momento (tela do app exibida ao Cliente Final antes do touch) não está descrito como AC binário em US-OS-004 nem em US-OS-013 — ver P-OS-A1.
- **Geolocalização (RAT-07):** INV-OS-GEO-001 limita precisão em payload de evento (município/bairro) e em audit WORM, mas a coordenada exata persistida no `os_evento` interno (item d do INV) **não tem retenção numérica declarada nem TTL automático** — ver P-OS-A2.
- **Anti-PII texto livre (INV-OS-TXT-001):** regex CPF/CNPJ/email/telefone/nomes capitalizados é boa primeira camada, mas insuficiente contra: (i) endereço completo, (ii) número de pedido/contrato/protocolo que indireta o titular, (iii) descrição clínica/saúde (art. 11) em razão_cancelamento de instalação em hospital, (iv) PII por transliteração (ñ→n, espaços extras, dígitos por extenso). Ver P-OS-A3.
- **Foto no-show (US-OS-014):** terceiros capturados acidentalmente não estão tratados — ver P-OS-A5.

### Contratual
- **Dispensa de aceite (US-OS-013):** termo PDF anexado falta requisitos formais (Cláusula 39 CDC — prática abusiva quando dispensa sem justa causa; assinatura interna do gerente como única chancela é frágil em juízo). Ver P-OS-A4.
- **Sucessão societária (INV-OS-SUC-001):** transferência de dado pessoal cliente A→B em fusão é juridicamente admissível pelo art. 7º V (execução de contrato sucedido) + Código Civil art. 1.116, mas requer **documento M&A externo verificável** referenciado em `sucessao_societaria_id`. Spec não exige hash/CNPJ/protocolo dessa cessão — ver P-OS-A7.

### Regulatório
- **Retenção dupla 5a/25a:** DPIA §6 trata coerentemente Receita (5a) × ISO 17025 cl. 8.4 (~25a). Spec §3.1 não dispara o filtro retroativo de retenção (não há campo `retencao_categoria` ou trigger de migração) — ver P-OS-A6.
- **GATE-OS-DPIA-OAB:** spec §9 lista corretamente como pré-requisito do 1º tenant externo pago. Confirmado.
- **GATE-OS-BIOMETRIA-KMS:** confirmado pré-coleta.

---

## Achados

### P-OS-A1 — Captura formal do consentimento art. 11 LGPD para biometria touch ausente como AC binário
**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Análise:** A DPIA-OS §5 e a Política de Privacidade §3.4 declaram que a biometria touch usa "dupla âncora": art. 11 II "g" (Lei 14.063/2020) + art. 11 II "a" (consentimento específico no momento). Esta segunda âncora exige **comprovação técnica do consentimento livre, informado, específico e destacado** (Res. CD/ANPD 2/2022 + Guia ANPD Consentimento 2022). Hoje em US-OS-004 (concluirAtividade) não há AC que descreva: (i) tela exibida ao Cliente Final antes do touch com texto canônico de consentimento; (ii) gravação do `consentimento_id` (UUID + hash do texto exibido + versão da política + timestamp) **vinculado ao `AceiteAtividade`**; (iii) opção real de recusa (que abre o caminho US-OS-013 dispensa). Sem isso, em fiscalização ANPD, "consentimento art. 11 II a" cai e sobra só "g" — que vincula só onde Lei 14.063 obriga.

**Decisão recomendada:**
1. Criar nova entidade `ConsentimentoBiometriaTouch` (Padrão B imutável) com `id`, `tenant_id`, `atividade_id`, `cliente_referencia_hash`, `texto_canonico_id`, `texto_hash`, `versao_politica`, `concedido_em`, `tela_renderizada_evidencia` (screenshot opcional).
2. Adicionar AC-OS-004-7: `GIVEN tela de aceite renderizada com texto canônico de consentimento art. 11 + botão "concordo e assino" SEPARADO de "concluir", WHEN cliente toca em concordar, THEN cria ConsentimentoBiometriaTouch ANTES de AceiteAtividade (foreign key 1:1).`
3. Adicionar INV-OS-CONSBIO-001 em REGRAS-INEGOCIAVEIS.md: "AceiteAtividade.consentimento_id NOT NULL quando captura biometria touch; sem consentimento → 412 ConsentimentoBiometriaAusente."
4. Texto canônico do consentimento entra na pasta `docs/conformidade/comum/termos/` (canonicalização INV-DOC-CANON-001 aplica) — REQUER VALIDAÇÃO OAB humana antes do 1º tenant externo.

### P-OS-A2 — Retenção numérica da coordenada exata (geo opt-in) não tem TTL automático
**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Análise:** INV-OS-GEO-001 item (d) diz "coordenada exata persistida só em `os_evento` interno com retenção limitada" — mas não declara em quanto tempo a coordenada decimal é truncada para município. DPIA-OS §6.4 fala "5 anos com truncamento para município após o prazo", porém spec §3.1 não tem trigger / job que execute esse truncamento. Risco: tenant litiga em ação trabalhista contra técnico e a coordenada decimal vira prova de stalking (RAT-07 prevê retenção 5a alinhada à OS). Sem job operacional, a coordenada exata fica até a anonimização total, contradizendo proporcionalidade declarada na DPIA.

**Decisão recomendada:**
1. Adicionar tarefa T-OS-NNN: "job procrastinate periódico `os-geo-truncamento` que após 5 anos da `AtividadeDaOS.concluida_em` faz UPDATE `os_evento` SET `geo_municipio_hash` = ..., `geo_lat` = NULL, `geo_long` = NULL, audit-trail Evento `GeoTruncadoLGPD`".
2. Criar AC-OS-NN binário no drill `validar_m3_os` (item 21): job agendado + teste de regressão simula passagem de tempo (`freezegun`) e valida truncamento.
3. Atualizar INV-OS-GEO-001 (REGRAS-INEGOCIAVEIS.md linha 133) item (d): "retenção máxima 5 anos da conclusão da atividade, após o que `geo_lat/long` viram NULL e fica só `geo_municipio_hash`; trigger `os_geo_truncamento_trg` agendado por `procrastinate_periodic`".

### P-OS-A3 — Anti-PII em texto livre tem 4 falsos negativos previsíveis
**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Análise:** INV-OS-TXT-001 lista regex "CPF, CNPJ, e-mail, telefone, ≥2 nomes capitalizados consecutivos". Em produção real de texto de campo (motivo cancelamento OS de manutenção em hospital), saem regularmente: (i) "paciente leito 305", "menor de idade na recepção" → dados de saúde art. 11; (ii) endereço completo "Rua X 123 ap 401"; (iii) números de protocolo/pedido/CRM que isolados parecem inocentes mas indireta o titular (singling out — Res. CD/ANPD 2/2022 art. 2º III); (iv) ofuscação trivial ("c.p.f. 123" / "telefone do João é zero um um..." por extenso). A regex atual passa em todos os quatro.

**Decisão recomendada:**
1. Estender INV-OS-TXT-001 com: (a) regex endereço (`\d+\s*(ap|apto|apt|bloco|sala|conjunto|cj)\.?\s*\d+`); (b) regex sequência numérica ≥7 dígitos não-CNPJ/CPF (protocolo/CRM); (c) lista palavra-chave saúde mínima (`paciente|leito|prontuário|menor|criança|gestante|HIV|positivo`) que dispara revisão de gerente em vez de bloqueio; (d) normalização Unicode NFC + lowercase antes da regex (canonicaliza ofuscação trivial).
2. Adicionar campo `motivo_texto_revisao_gerente_pendente BOOLEAN` em entidades com texto livre — se a lista saúde gatilho dispara, o texto fica em quarentena 24h até gerente revisar.
3. Documentar em DPIA-OS §10 que "regex anti-PII é defesa em profundidade, não infalível; treinamento do técnico + revisão de gerente em campos suspeitos cobrem o residual".
4. **OAB FLAG:** lista de palavras-chave saúde precisa de validação jurídica (art. 11 LGPD definição operacional).

### P-OS-A4 — Dispensa de aceite (US-OS-013) frágil contra alegação CDC art. 39
**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Análise:** US-OS-013 hoje gera "marca 'aceite dispensado por gerência' no certificado/fatura" baseada apenas em assinatura interna do gerente. O CDC art. 39 V coíbe "exigir do consumidor vantagem manifestamente excessiva", e a jurisprudência STJ trata dispensa unilateral de aceite como **inversão indevida do ônus probatório**. Em juízo de pequenas causas, o cliente alega "não autorizei, não recebi, não vi serviço" e o termo PDF interno não vence — porque foi gerado sem participação do cliente. AC-OS-013-1 exige "termo PDF anexado" mas não diz **quem produz, com qual conteúdo mínimo, com qual cadeia probatória**.

**Decisão recomendada:**
1. Adicionar AC-OS-013-5: `GIVEN dispensa solicitada, WHEN gerente confirma, THEN servidor gera TermoDispensaAceite a partir de template canonicalizado (INV-DOC-CANON-001) contendo OBRIGATORIAMENTE: (a) descrição objetiva da circunstância (3 cenários: recusa formal / ausência após no-show registrado / impossibilidade técnica de captura); (b) referência ao no-show vinculado quando aplicável; (c) hash da foto de evidência (no-show ou recusa); (d) declaração de boa-fé do gerente; (e) assinatura A3 do gerente (não só sessão autenticada).`
2. Restringir base de uso: dispensa **só** após no-show prévio registrado (US-OS-014) OU recusa explícita gravada (foto/áudio do cliente recusando — opt-in). Sem precedente → 412 `DispensaSemPrecedente`.
3. Atualizar lista certificados/faturas: marca "aceite dispensado" no rodapé deve incluir link público (QR) para o cliente consultar o termo PDF — **direito à informação CDC art. 6º III**.
4. **OAB FLAG:** modelo do TermoDispensaAceite REQUER OAB. Subagente IA não chancela.

### P-OS-A5 — Foto de no-show (US-OS-014) pode capturar terceiros sem aviso
**Severidade:** ACEITE com GATE

**Análise:** US-OS-014 prevê "foto evidencia" no marcarNoShow. A foto de fachada/recepção/sala de espera pode capturar vizinho, transeunte, paciente, recepcionista que não é o titular contratual. Embora seja ônus mínimo (art. 7º IX legítimo interesse — defesa em cobrança de deslocamento), e a foto vá pra audit imutável, há expectativa de privacidade razoável de quem não é parte do contrato. DPIA-OS R6 trata foto incidental em conclusão mas não em no-show.

**Decisão recomendada:**
1. Criar **GATE-OS-FOTO-NOSHOW-BLUR**: roadmap Wave A2 — blur automático de rostos antes do upload (modelo on-device); até lá, AC-OS-014 inclui aviso ao técnico "evite enquadrar pessoas; capture apenas a fachada e o número do imóvel".
2. Adicionar campo `foto_no_show_avisos_terceiros_acknowledged BOOLEAN` que o técnico marca antes de capturar (audit do consentimento do operador com a regra).
3. Atualizar Política de Privacidade §3.4 e DPIA-OS R6 cobrindo no-show explicitamente (atualmente cobre só aceite).
4. Risco residual baixo (foto restrita a fachada + sem PII em audit publicado — INV-OS-AUD-001 hash) — não bloqueia P2, mas fica rastreado.

### P-OS-A6 — Spec §2.4 declara DPIA "aprovada" mas DPIA-OS está em `status: minuta — aguarda-revisao-oab: true`
**Severidade:** MÉDIO (AJUSTADO INV-RITUAL-001)

**Análise:** Spec.md §2.4 (linhas 140-144): "DPIA aprovada (minuta OAB pendente)". O frontmatter do DPIA-OS é `status: minuta` + `aguarda-revisao-oab: true`. O termo "aprovada" sugere ao agente de codificação (P3/P4) que pode prosseguir sem ressalva — mas a DPIA é vinculante só após OAB. Há **drift terminológico** entre spec e DPIA. Acrescente: GATE-OS-DPIA-OAB (§9 spec) marca a OAB como pré-requisito do 1º tenant externo, **não do fechamento do Marco 3**, o que é coerente com dogfooding-only, mas precisa ficar explícito.

**Decisão recomendada:**
1. Reescrever spec.md §2.4 título: "DPIA em minuta (aprovação OAB pendente — GATE-OS-DPIA-OAB pré-tenant externo pago)".
2. Adicionar nota no §15 (Não-bloqueio): "Marco 3 dogfooding-only (Balanças Solution) não exige DPIA OAB-aprovada; 1º tenant externo pago bloqueia em GATE-OS-DPIA-OAB."
3. Atualizar nota similar em §16 (Próximo passo) para o subagente advogado em P2: "o subagente IA emite parecer consultivo; OAB humana revalida antes de produção externa".
4. Criar campo `Cliente.permite_persistencia_25a` (consent regulatório explícito) que **dispara** retenção 25a; sem ele, OS sem certificado fica em 5a (Receita). Hoje o filtro é implícito (presença de Calibracao link).

### P-OS-A7 — Sucessão societária M&A (INV-OS-SUC-001) sem requisito de evidência documental externa
**Severidade:** ACEITE com GATE

**Análise:** INV-OS-SUC-001 permite reabertura cross-cliente preservando audit + `sucessao_societaria_id` (FK). Spec.md §3.1 declara o campo mas **não define a entidade `SucessaoSocietaria`**, seus requisitos mínimos (CNPJ sucessor + sucedido + protocolo Junta Comercial + data do ato + hash do PDF do contrato de M&A) nem a validação. O ato societário **é** justa causa legal (Código Civil art. 1.116 + LGPD art. 7º V), mas sem evidência documental verificável, qualquer agente do tenant poderia inventar um "sucessao_societaria_id" e burlar a INV-OS-ANON-001 (bypass de anonimização via M&A fake).

**Decisão recomendada:**
1. Criar GATE-OS-SUCESSAO-EVIDENCIA: entidade `SucessaoSocietaria(id, tenant_id, sucedido_cnpj_hash, sucessor_cnpj_hash, protocolo_junta_comercial, data_ato, contrato_pdf_hash, contrato_pdf_b2_uri, registrado_por_admin_tenant_id, A3_admin_assinatura)` — admin do tenant precisa anexar PDF do ato societário com assinatura A3 antes de a FK ser usável.
2. Adicionar AC-OS-006-8 (reabrirOS): `GIVEN tentativa de reabertura cross-cliente, WHEN sucessao_societaria_id não tem A3 do admin OU contrato_pdf_hash inválido, THEN 412 SucessaoSemEvidencia.`
3. INV-OS-SUC-001 hoje está absolutamente correto enquanto regra; o gap é só evidência. Pode entrar em Wave A após Marco 3 fechar (não bloqueia M3 dogfooding — Balanças Solution não terá M&A).
4. **OAB FLAG:** lista de protocolos aceitos da Junta Comercial precisa parecer jurídico para validar se basta o NIRE / CNPJ alterado / cisão parcial.

---

## Riscos identificados (consolidado)

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Multa ANPD por consentimento biométrico genérico/implícito (art. 52 II — até 2% faturamento) | Média | Alto | P-OS-A1: entidade `ConsentimentoBiometriaTouch` + AC binário |
| Stalking trabalhista via coordenada decimal 5a persistida sem TTL | Baixa | Alto | P-OS-A2: job `os-geo-truncamento` + INV revisado |
| Vazamento de saúde art. 11 em razão_cancelamento (hospital) | Média | Crítico | P-OS-A3: regex estendida + quarentena + treinamento |
| Cobrança contestada (CDC art. 39) por aceite dispensado unilateralmente | Média | Médio | P-OS-A4: TermoDispensaAceite formal + precondição no-show/recusa + A3 gerente |
| Captura incidental de terceiros em foto de no-show | Média | Médio | P-OS-A5: blur roadmap + aviso ao técnico + DPIA atualizada |
| Bypass de anonimização via M&A fake | Baixa | Alto | P-OS-A7: evidência documental + A3 admin |
| Drift entre spec ("DPIA aprovada") e DPIA (minuta) confunde agentes de implementação | Alta | Médio | P-OS-A6: ajuste terminológico em spec.md §2.4 |

---

## Próximos passos

- ⚠️ **Esta minuta é parecer consultivo de subagente IA — sem OAB.** Os achados P-OS-A1 (texto canônico consentimento art. 11), P-OS-A3 (lista palavra-chave saúde art. 11), P-OS-A4 (TermoDispensaAceite + CDC art. 39) e P-OS-A7 (lista de protocolos Junta Comercial aceitos como evidência M&A) **REQUEREM VALIDAÇÃO OAB HUMANA** antes do 1º tenant externo pago.
- Aplicar os 7 achados em **P3 (matriz reconciliação)** + **P4 (tasks.md)** como T-OS-NNN dedicados (sugestão: T-OS-CONSBIO-01, T-OS-GEO-TRUNC-02, T-OS-TXT-EXT-03, T-OS-DISP-FORM-04, T-OS-FOTO-AVISO-05, T-OS-SPEC-AJUSTE-06, T-OS-SUC-EVID-07).
- Gates Wave A novos rastreados (não bloqueiam fechamento M3 dogfooding): **GATE-OS-FOTO-NOSHOW-BLUR**, **GATE-OS-SUCESSAO-EVIDENCIA**, **GATE-OS-CONSBIO-TEXTO-OAB**.
- **Sugiro contratar consulta OAB pontual focada (4-6h)** antes do 1º tenant externo para validar em bloco: DPIA-OS, texto canônico de consentimento biométrico, TermoDispensaAceite, lista de palavras-chave de saúde (anti-PII), lista de protocolos Junta Comercial. Preparei este parecer + DPIA-OS + minutas para otimizar o tempo do(a) advogado(a).
- **Ritual:** com estes 5 MÉDIOs ajustados em P3/P4, o subagente advogado emite **ACEITE** condicionado para destravar implementação dogfooding. Auditor 10 Família 5 (`auditor-conformidade-lgpd`) vai re-rodar em P5 com gate INV-RITUAL-001 (ZERO MÉDIO).
