---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-EQP-004
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-004.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-EQP-004 (Transferir equipamento intra-tenant com aceite duplo)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. O termo `v1.0-2026-05-18` definido em `texto_versao_transferencia.py` PRECISA passar por advogado humano com OAB antes do go-live público envolvendo cliente final não-dogfooding, porque é instrumento juridicamente vinculante (Lei 14.063/2020 art. 4º I) entre o tenant e dois clientes finais (cedente + cessionário) — e qualquer ambiguidade vira disputa contratual + reclamação ANPD.

---

## Veredito

**APROVADO COM RESSALVAS (R1–R6).** O plano está sólido na arquitetura: INV-050 protege cross-tenant, aceite duplo está endereçado, payload sanitizado (hashes), `motivo_categoria` enum, segregação ISO 17025 cl. 4.2 mapeada, idempotency 24h pra mutação destrutiva. As ressalvas são ajustes finos pra (i) garantir o texto D2 do PRD-advogado seja replicado **literalmente** em `texto_versao_transferencia.py`, (ii) fechar o vetor de fraude do aceite "presencial" Marco 2 sem portal-cliente, (iii) sanitização robusta no `motivo_detalhe`, (iv) versionamento do texto espelhando US-CLI-001 R2 (snapshot legal), (v) payload do evento `equipamento.transferido` sem regressão.

---

### R1 — Texto do termo em `texto_versao_transferencia.py` precisa replicar D2 do PRD-advogado, com 3 ajustes (BLOQUEANTE)

O T-EQP-039 cita "texto do termo (advogado D2)" mas não exibe o texto final. Ao implementar a constante `TEXTOS_HISTORICOS["v1.0-2026-05-18"]`, **o texto deve ser exatamente o D2 do PRD-advogado §D2** com 3 ajustes pra fechar lacunas detectadas nesta revisão:

**Gaps identificados no D2 original:**
1. Falta menção explícita ao **canal de direitos LGPD** do tenant (espelho INV-006 / R4 US-CLI-001). Cessionário PF tem que enxergar como exercer art. 18.
2. Falta menção a **Lei 14.063/2020 art. 4º I** (assinatura eletrônica simples) no corpo do termo — o D2 cita no rodapé do E4, mas o termo em si tem que registrar.
3. Falta declaração de **não-cessão** explícita de NF-e, certificados anteriores e responsabilidades fiscais/trabalhistas (D2 tem isso, mas precisa estar no texto da constante, não só no E4).

**Texto sugerido pra `TEXTOS_HISTORICOS["v1.0-2026-05-18"]` (replicação fiel D2 + 3 ajustes):**

```
TERMO DE TRANSFERÊNCIA DE EQUIPAMENTO

O CLIENTE CEDENTE, identificado pela referência interna [HASH_CEDENTE],
autoriza a transferência da titularidade operacional do equipamento
identificado pela TAG [TAG] e número de série [NS] ao CLIENTE
CESSIONÁRIO, identificado pela referência interna [HASH_CESSIONARIO],
para fins de [MOTIVO_CATEGORIA_LEGIVEL].

O CESSIONÁRIO declara aceitar a titularidade, assumindo as obrigações
de guarda, manutenção e calibração futuras, bem como o histórico
técnico anterior do equipamento, na forma da NBR ISO/IEC 17025.

Esta transferência NÃO transfere: (i) documentos fiscais (NF-e)
emitidos pelo cedente; (ii) certificados de calibração anteriores
à transferência (que permanecem confidenciais ao cedente, salvo
consentimento expresso registrado neste ato); (iii) responsabilidades
trabalhistas ou tributárias do cedente; (iv) eventuais penalidades
contratuais já constituídas entre o cedente e o laboratório
[Razão Social do Tenant].

CEDENTE e CESSIONÁRIO podem exercer seus direitos de titular de
dados pessoais (art. 18 da Lei 13.709/2018 — LGPD) pelo canal
indicado em [link: /{tenant_slug}/lgpd].

Aceitação digital registrada com data, hora e identificador de
dispositivo, na forma da Lei 14.063/2020 art. 4º, inciso I
(assinatura eletrônica simples). Configuração de assinatura
avançada/qualificada (art. 4º II/III) disponível por contratação
específica em V2.
```

**Apontamentos pro implementador (T-EQP-039):**
- Placeholders `[HASH_CEDENTE]`, `[HASH_CESSIONARIO]`, `[TAG]`, `[NS]`, `[MOTIVO_CATEGORIA_LEGIVEL]`, `[Razão Social do Tenant]`, `[link: /{tenant_slug}/lgpd]` são injetados em runtime pela UI HTMX (Tela E4 do cessionário) e pelo serializer do PDF impresso. **Nunca substituir os placeholders dentro da constante** — armazenar o texto-modelo é o que garante o snapshot legal versionado.
- Mostrar **texto integral** ao cedente (na tela de aceite do cedente, equivalente ao E4 mas com perspectiva inversa) e ao cessionário (E4). Cedente vê o termo antes de marcar checkbox; cessionário também.
- Hash do texto: gravar `hashlib.sha256(texto_renderizado_utf8).hexdigest()` em `TransferenciaEquipamentoAceite.texto_renderizado_hash` (campo novo a acrescentar — ver R5).

---

### R2 — Aceite "presencial" é vetor de fraude do atendente; mitigação obrigatória em 3 camadas (BLOQUEANTE)

O plano (riscos #3) reconhece que Marco 2 não tem portal-cliente; aceite presencial é capturado via UI HTMX onde o atendente preenche "cliente assinou no balcão". **Isso abre vetor para o atendente forjar aceite** (marcar ambos os checkboxes sem o cliente estar presente), o que em disputa real:
- Quebra a presunção de validade da Lei 14.063/2020 art. 4º I (que exige "ato inequívoco do signatário").
- Cessionário pode alegar "nunca aceitei" e o tenant fica sem prova robusta.
- Em PF (cessionário pessoa física), tratamento sem base legal válida = NC LGPD art. 7º.

**Mitigação mínima Marco 2 (3 camadas):**

1. **Camada técnica — campos auditáveis no `TransferenciaEquipamentoAceite`:**
   - `aceite_origem_via: enum { portal, presencial, email_confirmado, importacao_legado }` — já previsto.
   - `aceite_origem_atendente_user_id: FK` (NULL quando `via=portal`) — **acrescentar**: quem do tenant capturou o aceite presencial. Permite rastrear atendente em disputa.
   - `aceite_origem_evidencia_url: URL NULL` — **acrescentar**: link opcional pra foto do termo impresso assinado físico pelo cedente (Backblaze B2 WORM). Atendente é instruído (E4 + treinamento) a anexar foto sempre que via=presencial. Não obrigatório no schema (atrito UX), mas auditável.
   - Idem para `aceite_destino_*`.

2. **Camada UI — texto de responsabilização do atendente (acrescentar à Tela E4 / fluxo presencial):**

   > **Aviso ao atendente registrando aceite presencial:**
   > Você está confirmando que o **cliente [Razão Cedente]** leu e aceitou o termo de transferência acima, presencialmente, na unidade do laboratório. Esta ação fica registrada com seu usuário, data e hora. Recomendamos anexar foto do termo impresso assinado pelo cliente em [campo opcional]. Aceites forjados podem gerar reclamação ANPD, responsabilização pessoal e demissão por justa causa (CLT art. 482 alínea "a").
   > [ Confirmar aceite presencial ] [ Cancelar ]

3. **Camada audit — campo `via` no payload do evento `equipamento.transferido`:**
   Acrescentar `aceite_origem_via` e `aceite_destino_via` ao payload (sem PII — são enums). Isso permite ao tenant + Aferê detectar padrão suspeito (atendente X faz 50 transferências/mês todas com via=presencial sem foto) via alerta operacional (Wave B+ analytics).

**Não é mitigação completa** (a única seria portal-cliente real com OTP/A3), mas eleva o custo da fraude e cria rastro auditável. **V2 (Wave B+) obrigatoriamente** migra pra portal-cliente com OTP SMS/e-mail ao titular antes do aceite contar como válido. Documentar isso como **dívida regulatória explícita** em `docs/conformidade/equipamentos/transferencia-aceite-presencial-marco2.md` (criar).

---

### R3 — Sanitização do `motivo_detalhe` — regex reusada de US-EQP-001 cobre, mas 500 chars é demais; mensagem de rejeição precisa estar pronta

O plano (T-EQP-041) diz "validação anti-PII em `motivo_detalhe` (mesma regex `localizacao_fisica`)". A regex de `localizacao_fisica` (INV-EQP-LOC-001) detecta CPF, CNPJ, e-mail, telefone, ≥2 nomes capitalizados consecutivos. **Validação está correta**, mas dois pontos:

**R3.1 — Limite 500 chars é generoso demais pra um campo de motivo livre.**
Em `localizacao_fisica` o limite é 200 chars. `motivo_detalhe` de transferência tende a ser ainda mais curto ("equipamento vendido conforme NF 12345"). **Reduzir para 300 chars** — economiza armazenamento, reduz superfície de PII leak por erro, força atendente a ser objetivo. Quanto maior o campo livre, maior o risco do atendente narrar contexto pessoal ("dono X faleceu, herdeiro Y vai usar"). 300 cabe motivo objetivo.

**R3.2 — Texto pronto de rejeição PT-BR (acrescentar à T-EQP-041, espelho E2 US-CLI-004):**

> *"Identifiquei dados pessoais no campo motivo (CPF, CNPJ, e-mail, telefone ou nome). Descreva apenas o motivo objetivo da transferência (ex: 'venda conforme NF 12345', 'comodato encerrado', 'correção de cadastro duplicado'). Dados das pessoas envolvidas já estão registrados nos cadastros dos clientes."*

E acrescentar ao E4 (antes do campo) o aviso preventivo:

> **Motivo da transferência (até 300 caracteres)**
> Exemplo: *"venda registrada na NF 12345"*, *"comodato encerrado em [data]"*, *"correção de cadastro — equipamento vinculado ao cliente errado na importação inicial"*.
> Não inclua nomes, CPF, e-mail ou telefone — esses dados já estão no cadastro do cliente.

---

### R4 — Payload do evento `equipamento.transferido` — confirmar com 2 acréscimos contra regressão

O `modelo-de-dominio.md` §"Eventos publicados" define o payload atual:

```
{ equipamento_id, cliente_anterior_id_hash, cliente_novo_id_hash,
  motivo_categoria, motivo_texto_hash, aceite_origem_ts, aceite_destino_ts }
```

**Validação jurídica do payload:**
- ✅ Hashes (não UUIDs nem nomes) — bom; alinhado B1 PRD-advogado + LGPD art. 6º III/V.
- ✅ `motivo_categoria` enum — bom; permite analytics sem revelar PII.
- ✅ `motivo_texto_hash` — bom; comprova que houve motivo registrado sem expor o texto.
- ✅ Timestamps de aceite — bom; prova temporal Lei 14.063/2020.

**Faltam pra fechar fraude/rastreabilidade (acrescentar — espelha R2):**

1. `aceite_origem_via` e `aceite_destino_via` (enums) — sem isso, em disputa "nunca aceitei", não dá pra reconstruir se foi portal ou balcão. Enum não é PII.
2. `texto_versao_id` (string ou FK) — registra qual versão do termo foi aceita (v1.0-2026-05-18 etc.). Sem isso, em 2 anos, se ANPD/tenant perguntar "qual texto o titular aceitou", a resposta vira "olhar tabela `transferencia_equipamento_aceite`" — quebra a invariante de WORM auto-suficiente.

**Payload completo recomendado:**

```json
{
  "equipamento_id": "<uuid>",
  "cliente_anterior_id_hash": "<sha256>",
  "cliente_novo_id_hash": "<sha256>",
  "motivo_categoria": "venda|comodato|doacao|correcao_cadastral|outro",
  "motivo_detalhe_hash": "<sha256>",
  "aceite_origem_ts": "<iso8601>",
  "aceite_origem_via": "portal|presencial|email_confirmado|importacao_legado",
  "aceite_destino_ts": "<iso8601>",
  "aceite_destino_via": "portal|presencial|email_confirmado|importacao_legado",
  "texto_versao_id": "v1.0-2026-05-18",
  "consentimento_compartilhamento_historico_em_transferencia": false
}
```

**Renomear pra consistência com plano:** o `modelo-de-dominio.md` está com `motivo_texto_hash`; o plano US-EQP-004 e o PRD-advogado D2 falam de `motivo_detalhe_hash`. **Padronizar para `motivo_detalhe_hash`** (atualizar `modelo-de-dominio.md` no mesmo PR). Espelha campo do model `TransferenciaEquipamentoAceite.motivo_detalhe_hash`.

**NUNCA logar no payload (reforçar como teste de regressão):**
- Razão social/nome do cedente/cessionário em claro.
- CPF/CNPJ em claro.
- Texto livre do `motivo_detalhe` (só hash).
- IP em claro (só hash, e mesmo o hash fica no model `TransferenciaEquipamentoAceite.aceite_*_ip_hash`, não no payload do evento).

T-EQP-048 já tem `test_evento_transferido_payload_so_hashes_e_categorias` — **expandir asserts** pra cobrir os 2 acréscimos (`texto_versao_id` presente + `via` presente).

---

### R5 — Versionamento do `texto_versao_id`: espelhar exatamente US-CLI-001 R2 (snapshot legal imutável)

O plano (riscos #4) diz "Texto do termo legalmente vinculante: versionado em constants. Mudança = nova versão. Aceites antigos preservam versão dada (advogado R2 US-CLI-001)." **Conceito correto, faltam 3 garantias estruturais:**

**R5.1 — Estrutura espelha `lgpd.py` (US-CLI-001):**

```python
# src/infrastructure/equipamentos/texto_versao_transferencia.py

VERSAO_VIGENTE = "v1.0-2026-05-18"

TEXTOS_HISTORICOS: dict[str, str] = {
    "v1.0-2026-05-18": "<texto integral conforme R1>",
    # Versões antigas NUNCA são removidas. Sempre acrescentar nova entrada.
}

VIAS_VALIDAS = ("portal", "presencial", "email_confirmado", "importacao_legado")
```

**R5.2 — Imutabilidade reforçada por trigger PG:**

O plano já prevê trigger `bloquear_update_aceite_apos_concretizado` em T-EQP-038. **Reforçar escopo:** o trigger BEFORE UPDATE em `transferencia_equipamento_aceite` deve bloquear mudança em **qualquer campo** após `aceite_origem_em IS NOT NULL AND aceite_destino_em IS NOT NULL`, incluindo:
- `texto_renderizado_hash` (campo novo R1) — garante que o que o titular viu não muda.
- `aceite_origem_versao_texto_id`, `aceite_destino_versao_texto_id` — versão que vigia no momento do aceite, congelada.
- `motivo_detalhe_hash`, `motivo_categoria` — não-reescrevíveis.

Allow via comment `# audit-immutability: skip -- <razão ≥10 chars>` (espelho `audit-immutability-check.sh`) só pra migração de schema legada, nunca em runtime.

**R5.3 — Teste obrigatório:**
T-EQP-048 já tem `test_aceite_versao_texto_id_referencia_constante_vigente`. **Acrescentar dois testes:**
- `test_mudar_texto_vigente_nao_afeta_aceites_antigos` — simular mudança de `VERSAO_VIGENTE` para `v1.1-2027-01-01`; aceite gravado em `v1.0-2026-05-18` continua referenciando v1.0 e renderiza o texto antigo via `TEXTOS_HISTORICOS["v1.0-2026-05-18"]`.
- `test_versao_inexistente_em_texto_versao_id_rejeita_400` — segurança contra cliente API enviando `texto_versao_id` arbitrário.

---

### R6 — Idempotency-Key 24h é correto pra mutação destrutiva, mas mensagem de erro deve mencionar transferência específica

T-EQP-048 inclui `test_idempotency_key_24h_recusa_reuso_destrutivo`. Bom (C4 do PRD-advogado). **Acrescentar:** mensagem PT-BR da rejeição 409 deve ser inequívoca pra evitar atendente reusar key acreditando que é "falha de rede":

> *"Esta transferência já foi processada nas últimas 24 horas com a mesma chave de idempotência. Se a transferência anterior está concluída, abra a ficha do equipamento [TAG] pra confirmar. Se algo deu errado, abra um chamado pra equipe de suporte do laboratório — não reenvie."*

---

## Bases legais (LGPD art. 7º) confirmadas

| Finalidade | Base legal | Justificativa |
|---|---|---|
| Transferir vínculo equipamento↔cliente final | art. 7º V + art. 7º VI | Aferê = operador (RAT-03); tenant = controlador; aceite duplo cumpre CC art. 421/422 (boa-fé + função social do contrato) |
| Registrar `motivo_detalhe` (sanitizado) | art. 7º V + art. 7º VI | Necessidade operacional + rastreabilidade audit |
| Audit `equipamento.transferido` com hashes | art. 7º II + art. 16 I | Imutabilidade exigida ISO 17025 cl. 8.4 + Marco Civil art. 15; hash satisfaz rastreabilidade sem perpetuar PII |
| Segregação histórico de certs anteriores (RBC B6) | art. 6º III (necessidade) + ISO 17025 cl. 4.2 (confidencialidade) | Cessionário não tem direito a histórico do cedente sem consentimento expresso |
| Texto versionado do termo (snapshot legal) | art. 6º VI (transparência) + LGPD art. 9º | Titular vê EXATAMENTE o que aceitou; reconstituível 5+ anos depois |

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Atendente forja aceite presencial sem cliente | Alta (Marco 2 sem portal) | Disputa contratual + NC LGPD art. 7º + reclamação ANPD/Procon | R2 — 3 camadas: rastreio atendente + evidência opcional + aviso UX de responsabilização |
| Texto do termo divergir do D2 do PRD-advogado | Média se implementador improvisa | Termo juridicamente frágil; ambiguidade vira disputa | R1 — texto pronto pra colar em `texto_versao_transferencia.py` |
| `motivo_detalhe` vaza PII de terceiro ("herdeiro Maria Silva CPF 123") | Média sem regex; Baixa com R3 | NC LGPD art. 7º + uso indevido de PII de não-titular | R3.1 (limite 300 chars) + R3.2 (regex anti-PII reusada US-EQP-001) |
| Payload `equipamento.transferido` regride e loga PII em claro | Baixa com teste; Alta sem | NC LGPD + INV-013 violada | R4 — payload com hashes + 2 acréscimos + teste de regressão expandido |
| Versão antiga do termo é "reescrita" e quebra snapshot legal | Baixa com trigger; Alta sem | ANPD pergunta "qual texto foi aceito" e resposta diverge | R5.2 — trigger BEFORE UPDATE em todos campos pós-concretização |
| Idempotency-Key reusada porque atendente pensa "deu erro de rede" | Média | Possível duplicação de evento OU usuário acha que falhou e tenta caminho alternativo | R6 — mensagem PT-BR inequívoca |

---

## Próximos passos

- ✅ Aplicar R1 — texto pronto colar em `texto_versao_transferencia.py` (T-EQP-039) **idêntico** ao bloco em R1.
- ✅ Aplicar R2 — acrescentar `aceite_origem_atendente_user_id` + `aceite_origem_evidencia_url` (idem destino) ao schema da migration 0013 (T-EQP-038); criar `docs/conformidade/equipamentos/transferencia-aceite-presencial-marco2.md` (dívida regulatória explícita).
- ✅ Aplicar R3 — reduzir limite pra 300 chars (T-EQP-041); usar texto de rejeição PT-BR exato §R3.2.
- ✅ Aplicar R4 — acrescentar `texto_versao_id`, `via` (origem + destino) ao payload `equipamento.transferido` em `modelo-de-dominio.md` §Eventos; padronizar nome pra `motivo_detalhe_hash`; expandir asserts de `test_evento_transferido_payload_so_hashes_e_categorias`.
- ✅ Aplicar R5 — estrutura espelho `lgpd.py` em `texto_versao_transferencia.py`; estender trigger `bloquear_update_aceite_apos_concretizado` pra cobrir `texto_renderizado_hash`; acrescentar 2 testes (mudança não-retroativa + versão inexistente 400).
- ✅ Aplicar R6 — mensagem PT-BR §R6 na rejeição 409 do idempotency 24h.
- ⚠️ **Antes do go-live público** (não dogfooding): termo `v1.0-2026-05-18` precisa revisão por advogado humano com OAB ativa especialista LGPD + direito digital (perfil: 5+ anos, experiência SaaS B2B operador, conhecimento Lei 14.063/2020 + ISO 17025 cl. 4.2 + 8.4). Esta minuta + RAT + payload de evento otimizam tempo dele/dela (estimado 2-3h).
- ⏳ Diferido Wave B+ obrigatoriamente: portal-cliente real com OTP SMS/e-mail antes do aceite válido — fecha vetor R2 de forma definitiva.
- ⏳ Diferido V2 configurável: A3 ICP-Brasil opcional por tenant na transferência (D2 §rodapé já contempla — Lei 14.063/2020 art. 4º II/III).

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 5º VI/VII, 6º III/V/VI, 7º II/V/VI, 9º, 16 I/II, 18, 37
- Lei 14.063/2020 — art. 4º I/II/III (assinatura eletrônica)
- MP 2.200-2/2001 — ICP-Brasil
- Código Civil — art. 421 (função social do contrato), 422 (boa-fé objetiva)
- CLT art. 482 alínea "a" (justa causa por ato de improbidade — fraude do atendente)
- Marco Civil da Internet (Lei 12.965/2014) — art. 15 (retenção de logs)
- ISO/IEC 17025 cl. 4.2 (confidencialidade) + 8.4 (controle de registros)
- INV-050, INV-025, INV-013, INV-TENANT-001, INV-EQP-LOC-001 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03 (`docs/conformidade/comum/lgpd-rat.md`)
- US-CLI-001-advogado §R2 (precedente snapshot legal versionado)
- PRD-advogado equipamentos §B2 + §D2 + §E4 (origem do termo)
