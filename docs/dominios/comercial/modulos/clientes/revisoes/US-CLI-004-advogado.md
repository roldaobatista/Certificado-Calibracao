---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-CLI-004
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-004.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-CLI-004 (LGPD + CDC + Superendividamento)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Antes do go-live público envolvendo bloqueio comercial de consumidores PF, advogado humano licenciado precisa revisar (em especial: enum de motivos visível ao cliente final, textos de comunicação prévia D+30/60/89, e a tese de que bloqueio comercial intra-tenant não equivale a negativação cadastral).

---

## Sumário (≤150 palavras)

**APROVADO COM RESSALVAS BLOQUEANTES (R1–R6).** O plano US-CLI-004 acerta no fundamento — bloqueio comercial intra-tenant **não é** protesto (Lei 9.492/97) nem negativação cadastral (SPC/Serasa), é exercício de exceção do contrato não cumprido (CC art. 476) e gestão de risco de crédito do tenant; LGPD/CDC permitem. **Mas 6 buracos precisam ser tampados antes do code-complete:** (R1) `bloqueio_justificativa` em texto livre vaza PII no audit WORM — exigir enum + regex anti-PII (espelho R2 do US-CLI-005); (R2) bloqueio silencioso fere CDC art. 6º III/IV — tenant **deve** comunicar D+30/60/89 antes do bloqueio D+90 e a régua AC-5 é a notificação prévia obrigatória, não opcional; (R3) reativação ≤5min vira SLA contratual no DPA tenant↔Aferê; (R4) `inadimplencia_90d` no model não é dado sensível (art. 5º II), mas exige confidencialidade reforçada — admin Aferê não pode ler; (R5) Lei 14.181/2021 + LBI exigem fluxo manual de revisão antes do bloqueio automático D+90; (R6) audit do bloqueio em outro tenant é confidencial — admin Aferê suporte forense vê hash, não conteúdo.

---

## Veredito

**APROVADO COM RESSALVAS BLOQUEANTES.** Fundamento jurídico do bloqueio está correto e é distinto de protesto/negativação. Justificativa e motivo precisam saneamento de PII (espelho do US-CLI-005). Régua AC-5 é obrigatória, não opcional, e precisa ser implementada como **gate** do AC-3 (bloqueio só dispara se as 3 notificações prévias foram comprovadamente enviadas — vira invariante).

### Ressalvas (R1–R6)

#### R1 — `bloqueio_justificativa` em texto livre é vetor de vazamento (BLOQUEANTE)

T-CLI-019 define `bloqueio_justificativa: text` exigindo ≥30 chars (AC-1). Texto livre do funcionário do tenant vai gerar isto:

> "Sr. Silva CPF 123.456.789-00 atrasou 2 boletos do orçamento OR-2026-0145 (R$ 4.320), telefone (11) 99876-5432 não atende, e-mail joaosilva@gmail.com bounced — bloqueando preventivo."

Essa justificativa viaja pro **audit `cliente.bloqueado`** (B2 WORM, 5–10 anos retenção — `retencao-matriz.md` §2) e fica visível a admin Aferê em suporte forense. Mesmo veto do US-CLI-001 (auditoria com PII cru) e US-CLI-005 R1/R2 — **três problemas concretos:**

1. **Crypto-shredding fica impossível** — quando titular exercer art. 18 VI em 2031, o audit WORM ainda terá CPF/nome/email/telefone em texto e WORM não permite UPDATE/DELETE.
2. **Cross-tenant blast radius** — admin Aferê lê PII do tenant via audit; fura expectativa do tenant-controlador (INV-013).
3. **NC LGPD art. 6º III (necessidade)** — audit precisa provar **que** houve bloqueio e **por qual categoria de motivo**, não **descrever** o titular ou os títulos vencidos (esses ficam em ContasReceber, com retenção própria gerida pelo tenant).

**Solução obrigatória — payload sanitizado (espelho US-CLI-005 R1):**

```python
{
    "cliente_id": "<uuid>",
    "tenant_id": "<uuid>",
    "acao": "bloqueado",
    "motivo_categoria": "manual_inadimplencia" | "manual_quebra_confianca" | "manual_solicitacao_juridico" | "manual_outro" | "automatico_inadimplencia_90d",
    "justificativa_hash": "<sha256(texto)>",
    "justificativa_len": 142,
    "usuario_id": "<uuid ou 'system'>",
    "timestamp": "...",
    "causation_id": "<uuid do título vencido — se automático>",
    "ip_hash": "<sha256(ip + salt_tenant)>"
}
```

**O texto bruto da justificativa NÃO entra no audit.** Fica em `Cliente.bloqueio_justificativa` no banco operacional (mutável, com filtro RLS por tenant, com retenção controlada pelo tenant via crypto-shredding na Wave B). Quem quer reconstruir "o que o atendente escreveu" lê o `Cliente.bloqueio_justificativa` atual; se o cliente foi desbloqueado e re-bloqueado, mantém histórico via tabela `cliente_bloqueio_historico` separada (também sob RLS + retenção fiscal/contratual do tenant).

**Task nova:** **T-CLI-024b** — sanitizar payload de audit + teste de regressão `test_bloqueio_audit_sem_pii_cru` rodando regex de CPF/email/telefone no payload serializado.

#### R2 — Motivo deve ser enum + sanitizador regex anti-PII no campo livre (BLOQUEANTE)

T-CLI-019 cria `bloqueio_motivo: str(40)` + enums `MOTIVO_BLOQUEIO_MANUAL` e `MOTIVO_BLOQUEIO_INADIMPLENCIA_90D`, mas só dois valores. Insuficiente. Espelho do R2 do US-CLI-005.

**Enum completo proposto:**

| `bloqueio_motivo` (enum) | Quando usar | Origem |
|---|---|---|
| `manual_inadimplencia` | Atendente decide bloquear por atraso visível antes de D+90 | Funcionário tenant |
| `manual_quebra_confianca` | Cheque devolvido, fraude suspeita, comportamento abusivo | Funcionário tenant |
| `manual_solicitacao_juridico` | Cliente em processo judicial com o tenant | Funcionário tenant |
| `manual_outro` | Exige `bloqueio_justificativa` ≥30 chars com regex anti-PII | Funcionário tenant |
| `automatico_inadimplencia_90d` | Job D+90 disparou após régua AC-5 cumprida | Sistema |

Para `bloqueio_justificativa` (sempre obrigatória ≥30 chars per AC-1, mas com restrição extra em `manual_outro`):

- Limite 500 chars (não 30 mínimo apenas — também ter teto).
- Validação backend: regex bloqueia CPF (`\d{3}\.?\d{3}\.?\d{3}-?\d{2}`), CNPJ (`\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}`), e-mail (`\S+@\S+\.\S+`), telefone (≥10 dígitos seguidos). Se detectar → rejeita 400: "Não inclua dados pessoais do cliente na justificativa. Descreva o motivo sem CPF, e-mail ou telefone — esses dados já estão no cadastro."
- Template safe sugerido (UI futura): *"Cliente apresenta atraso reiterado em pagamentos com tentativas de contato esgotadas; bloqueio preventivo até regularização."*

**Task nova:** **T-CLI-019b** — expandir enum para 5 valores + sanitizador regex anti-PII no `bloqueio_justificativa`.

#### R3 — Bloqueio silencioso fere CDC art. 6º III/IV — régua AC-5 é GATE obrigatório, não opcional (BLOQUEANTE)

O plano coloca AC-CLI-004-5 (régua D+30/60/89) como "não implementável sem comunicacao-omnichannel — só documentação do contrato + 3 eventos esquematizados". **Isso fura a base jurídica do AC-3.**

Por quê:

- **CDC art. 6º III/IV** (informação adequada e clara + proteção contra práticas abusivas) exige que o consumidor seja informado de cobrança em curso e da consequência (bloqueio comercial). Bloqueio surpresa em D+90 sem notificação prévia documentada é prática abusiva.
- **Lei 14.181/2021 (superendividamento)** + **Lei 13.146/2015 (LBI)** reforçam dever do credor de comunicação prévia, em linguagem compreensível, com prazo para regularização. A régua D+30/60/89 é exatamente isso.
- **Lei 9.492/1997 (protesto)** NÃO se aplica (bloqueio comercial ≠ protesto cartorial), mas a doutrina pacífica é que **qualquer restrição comercial unilateral exige aviso prévio razoável**.

**O que precisa mudar no plano:**

1. AC-CLI-004-3 (job D+90) **só pode bloquear** se houver registro de que os 3 alertas D+30/60/89 foram enviados ao cliente final. Vira **invariante** novo:
   - **INV-CLI-BLOQ-001**: bloqueio automático por inadimplência exige `regua_cobranca_d30_enviado_em IS NOT NULL AND regua_cobranca_d60_enviado_em IS NOT NULL AND regua_cobranca_d89_enviado_em IS NOT NULL` no título vencido. Se qualquer um for NULL, job pula este título e gera alerta `regua_cobranca_incompleta` pro gerente operacional do tenant.
2. Como `comunicacao-omnichannel` é Wave A (não existe no Marco 1), o **fallback obrigatório** é: tenant recebe alerta no admin Django dizendo "Cliente X cumpriria D+90 hoje mas régua de notificação não foi disparada; envie comunicação manual e marque caixa OU desabilite bloqueio automático para este cliente". **Bloqueio automático fica desligado por default no Marco 1** — só liga quando comunicacao-omnichannel existir. Documentar como flag de feature em `Tenant.bloqueio_automatico_inadimplencia_habilitado=False` (default).
3. Bloqueio **manual** (AC-1) **também** exige que o atendente confirme um checkbox "Confirmo que comuniquei previamente o cliente sobre o débito e a possibilidade de bloqueio." O backend grava `bloqueio_comunicacao_previa_confirmada: bool` (NOT NULL pra bloqueios manuais por motivo `manual_inadimplencia`). Sem confirmação, API rejeita 400.

**Tasks novas:**
- **T-CLI-019c** — campo `bloqueio_comunicacao_previa_confirmada: bool` no model + validação no endpoint.
- **T-CLI-021b** — flag `bloqueio_automatico_inadimplencia_habilitado` em Tenant, default `False`; job verifica antes de executar.
- **T-CLI-023b** — INV-CLI-BLOQ-001 documentada em `REGRAS-INEGOCIAVEIS.md`.

#### R4 — `motivo=inadimplencia_90d` NÃO é dado pessoal sensível, mas exige confidencialidade reforçada (recomendação)

Pergunta do briefing: "inadimplencia_90d é dado pessoal sensível? Vincula reputação financeira."

**Resposta jurídica:**

- **NÃO é "dado sensível" no sentido técnico da LGPD art. 5º II** (que lista origem racial, convicção religiosa, opinião política, saúde, dado genético/biométrico, vida sexual). Inadimplência é dado pessoal **comum** (art. 5º I).
- **MAS é dado de alta sensibilidade comercial** (reputação financeira) e o tratamento equivocado o transforma em quase-negativação. **Diferença crítica:**
  - **Sistema interno do tenant** (uso operacional, base art. 7º V execução de contrato) → **permitido** sem consentimento. Esse é o caso do US-CLI-004.
  - **Exportar pra SPC/Serasa/SCR Bacen** (terceiros) → **outra finalidade**, **outra base legal** (art. 7º VI exercício regular de direitos ou art. 7º IX legítimo interesse com LIA), **outro produto** (não esta US). Vira `negativacao` module na Wave B+ com fluxo próprio (LIA documentada, opt-out, art. 9º notificação).
- **Confidencialidade reforçada exigida:**
  - INV-013 (confidencialidade — log de visualização) deve cobrir leitura do `Cliente.bloqueio_motivo` e `Cliente.bloqueio_justificativa`. Quando admin do tenant visualiza, gera audit `cliente.bloqueio_visualizado`.
  - **Admin Aferê (suporte forense) NÃO lê** `bloqueio_justificativa` — só vê o hash + categoria do enum. RLS já cobre (Aferê não tem JWT de tenant), mas defensivo: filtrar coluna em qualquer endpoint de superadmin/suporte.

**Task nova:** **T-CLI-024c** — INV-013 estende a logar visualização de `bloqueio_motivo`/`bloqueio_justificativa`.

#### R5 — Lei 14.181/2021 (superendividamento) + LBI exigem rota manual de revisão antes do bloqueio automático (BLOQUEANTE-SOFT)

Cenário real: cliente PF idoso, vulnerável ou em superendividamento atinge D+90 e é bloqueado automaticamente; perde acesso a serviço de calibração de balança que sustenta seu comércio.

- **Lei 14.181/2021 art. 54-A** introduz dever de **revisão e renegociação** quando consumidor manifesta dificuldade. O credor não pode simplesmente cortar — deve oferecer plano.
- **LBI (Lei 13.146/2015)** exige razoabilidade adicional pra PCD.
- O job D+90 automático **não pode bypassar** isso.

**Solução obrigatória:**

1. Job D+90, **antes de bloquear**, dispara **`Cliente.PreBloqueioAlerta`** → gerente do tenant tem **janela de 24h** pra revisar manualmente (renegociar, parcelar, manter ativo).
2. Se gerente não age em 24h, bloqueio efetiva-se com `motivo_categoria="automatico_inadimplencia_90d_sem_revisao_manual"`.
3. Se gerente age (cria plano de renegociação no `financeiro/contas-receber` — Wave A), bloqueio é cancelado e nova régua começa.
4. Audit registra: pre-alerta enviado, gerente agiu (sim/não), decisão final.

**No Marco 1 (sem ContasReceber):** job stub respeita o intervalo 24h e o evento `Cliente.PreBloqueioAlerta` é publicado pro futuro consumo do `comunicacao-omnichannel` e `financeiro`.

**Task nova:** **T-CLI-021c** — pré-alerta 24h + estado intermediário `Cliente.bloqueio_pendente_revisao` no model.

#### R6 — Audit do bloqueio em outro tenant é confidencial — admin Aferê suporte forense vê hash, não conteúdo (BLOQUEANTE)

Pergunta do briefing: "audit do bloqueio com causation_id ligando ao título vencido — em outro tenant a auditoria deve ser confidencial?"

**Resposta:** sim. Mesmo princípio do US-CLI-005 R1 e do INV-013.

- **Tenant é controlador** do dado de inadimplência do cliente final. Aferê é **operador** (DPA tenant↔Aferê).
- Admin Aferê (suporte forense, debugger, dev em prod) **não pode ler** `bloqueio_justificativa` ou `causation_id` resolvido para o título específico, **mesmo em suporte de incidente**.
- Em incidente forense: admin Aferê vê audit com `cliente_id_hash`, `motivo_categoria`, `causation_id_hash`, `timestamp` — suficiente pra investigar comportamento do sistema, insuficiente pra identificar titular ou valor do débito. Se forense exige acesso a PII, escala pro tenant-controlador autorizar caso a caso (procedimento documentado em `docs/operacao/runbooks/suporte-forense-com-pii.md` — pendente Wave A).

**Solução:**
- Tabela `audit_trail.authz_decisions` (já planejada) tem coluna `tenant_id` com RLS forçada (NOBYPASSRLS). Consultas de admin Aferê passam por view `audit_trail.authz_decisions_sanitized` que hashea PII e remove `causation_id` cru.
- INV-AUDIT-PII-001 (a criar): "consulta cross-tenant ao audit por admin Aferê passa por view sanitizada; consulta direta à tabela exige role `tenant_admin` com `tenant_id` no contexto."

**Task nova:** **T-CLI-024d** — view sanitizada `audit_trail.authz_decisions_sanitized` + INV-AUDIT-PII-001 em `REGRAS-INEGOCIAVEIS.md`. (Pode escorregar para Wave A se travar Marco 1 — neste caso, restringir acesso humano direto ao schema `audit_trail` para 1 conta forense com 2FA, documentar mitigação compensatória.)

### Não-ressalvas (validadas como corretas)

- ✅ **Bloqueio comercial ≠ protesto (Lei 9.492/97):** correto. Bloqueio comercial intra-tenant é exceção do contrato não cumprido (CC art. 476) + gestão de risco. Protesto é ato cartorial unilateral irreversível, fora de escopo.
- ✅ **Bloqueio comercial ≠ negativação SPC/Serasa:** correto. Negativação é compartilhar com bureau de crédito (terceiro), outra base legal, outro produto. US-CLI-004 fica intra-tenant.
- ✅ **`causation_id` ligando ao título vencido:** correto pro rastreio causa-efeito (INV-001). Risco de PII via causation está em R6, não no campo em si.
- ✅ **Authz `clientes.bloquear`/`clientes.desbloquear` exigindo `admin_tenant`:** correto. Ação restritiva merece perfil restrito (SEC-LEAST-PRIV-001).
- ✅ **Bloqueio idempotente (`test_bloqueio_eh_idempotente`):** correto. Defensivo bom.
- ✅ **Endpoint POST `/clientes/{id}/desbloquear/` manual:** correto. Tenant precisa rota de desbloqueio manual independente do automático (pra casos negociados fora do sistema).

---

## Texto sugerido — enum + comunicação obrigatória

### Enum `bloqueio_motivo` (5 valores)

```python
class BloqueioMotivo(models.TextChoices):
    MANUAL_INADIMPLENCIA = "manual_inadimplencia", "Inadimplência (manual)"
    MANUAL_QUEBRA_CONFIANCA = "manual_quebra_confianca", "Quebra de confiança (manual)"
    MANUAL_SOLICITACAO_JURIDICO = "manual_solicitacao_juridico", "Solicitação do jurídico (manual)"
    MANUAL_OUTRO = "manual_outro", "Outro motivo (manual — exige justificativa detalhada)"
    AUTOMATICO_INADIMPLENCIA_90D = "automatico_inadimplencia_90d", "Inadimplência > 90 dias (automático)"
```

### Templates de comunicação obrigatória (régua D+30/60/89)

Para o módulo `comunicacao-omnichannel` da Wave A consumir. **Não confundir com texto interno ao tenant** — esses são textos enviados ao cliente final:

- **D+30 (WhatsApp/SMS):** "Olá [nome curto]. Identificamos pendência financeira em aberto de [valor formatado] referente ao serviço [tipo]. Acesse [link curto] para regularizar ou fale conosco no [canal]. Em caso de dificuldade, podemos negociar."
- **D+60 (e-mail):** assunto "Pendência financeira com [tenant.nome_fantasia] — opções de regularização" / corpo com valor, vencimento original, link de boleto 2ª via, opção de parcelamento, prazo até bloqueio (30 dias).
- **D+89 (ligação registrada OU mensagem formal):** "Última comunicação antes do bloqueio comercial automático. Em 24h o sistema impedirá novas ordens de serviço, orçamentos e agendamentos. Fale com [contato] para regularizar ou negociar."

Todos os 3 contêm:
- Identificação clara do credor.
- Valor + vencimento original.
- Opção de negociação (Lei 14.181/2021).
- Canal humano de contato (LBI).
- Aviso da consequência (bloqueio em [data]).

**Validação jurídica humana (OAB) obrigatória antes do go-live público** — esses textos visíveis ao consumidor final são interface legalmente sensível.

---

## Análise por área

### LGPD / Privacidade

- **Base legal do bloqueio comercial:** art. 7º V (execução de contrato/medidas preliminares) — o cliente assinou contrato/aceite implícito quando contratou; bloqueio por inadimplência é gestão da relação contratual. Sem necessidade de consentimento.
- **Papel do Aferê:** **operador** (igual US-CLI-001, US-CLI-005). Tenant é controlador; Aferê executa instrução documentada.
- **Direitos do titular:** titular pode exercer art. 18 II (acesso — saber por que está bloqueado, com que motivo) e art. 18 III (correção — se motivo está errado). Atendimento desses direitos é do **tenant** (controlador). Aferê fornece ferramenta (futuro `lgpd-portal` Wave B).
- **Retenção:** `Cliente.bloqueio_*` no banco operacional segue mesma matriz do cliente (5 anos default + ISO 17025 se OS/cert emitido) — `retencao-matriz.md` §2. `cliente_bloqueio_historico` (se criado por R1) idem.
- **Transparência:** AC-2 já prevê que `AuthorizationProvider.can()` retorna `reason="cliente_bloqueado_manual"` + sugestão de regularização. **Bom.** Esse é o "saber por que" para o atendente do tenant. Para o **cliente final**, transparência vem via régua AC-5 (R3) + atendimento humano.

### Contratual

- DPA tenant↔Aferê cobre operações de gestão de inadimplência como instrução documentada. Não precisa addendum.
- **Novo:** `reativação_em ≤5min` do AC-6 deve virar **SLA contratual** em DPA tenant↔Aferê (ou no contrato comercial Aferê-tenant). Caso de prazo prometido tecnicamente que vira obrigação contratual. Sugestão: "tempo máximo entre `ContasReceber.Pago` e `Cliente.Desbloqueado` ≤5min em 95% dos casos, ≤15min em 99%, sem garantia para falhas de infraestrutura declaradas em status page."
- Contrato Aferê-tenant deve incluir cláusula: "tenant é responsável pela legalidade da decisão de bloqueio e pelo cumprimento de CDC/LGPD/Lei 14.181/2021 em relação a seus clientes finais; Aferê fornece ferramenta operacional sem juízo de mérito sobre a inadimplência."

### CDC

- **CDC art. 6º III (informação adequada):** régua AC-5 (R3) cumpre quando implementada.
- **CDC art. 6º IV (proteção contra práticas abusivas):** bloqueio sem notificação prévia é prática abusiva — R3 resolve.
- **CDC art. 39 V (exigir vantagem manifestamente excessiva):** se atendente bloqueia cliente por valor pequeno sem proporcionalidade, pode virar prática abusiva. Mitigação: documentar que decisão de bloqueio é do tenant; produto não recomenda valor mínimo.
- **CDC art. 42 (cobrança vexatória):** Aferê não cobra (tenant cobra). Textos da régua R3 devem evitar tom vexatório — revisão OAB humana obrigatória pré-go-live.

### Lei 14.181/2021 (superendividamento) + LBI

- R5 cobre o essencial — pré-bloqueio com janela de 24h pra revisão manual.
- Tenant pode (não obrigado a) configurar "lista de clientes com tratamento diferenciado" (PCD, idoso, em superendividamento declarado) que **nunca** sofrem bloqueio automático, só manual. Sugestão V2 (não bloqueia Marco 1): flag `Cliente.tratamento_diferenciado: bool` + audit ao alterar.

### Regulatório (ANPD)

- **Bloqueio comercial NÃO é incidente LGPD.** Não dispara Res. CD/ANPD 15/2024.
- **Bloqueio errado** (atendente bloqueia cliente errado) é incidente de qualidade (art. 6º V), não de segurança. Tenant decide se notifica titular.
- **Exportar dado de inadimplência pra terceiros (Wave B `negativacao`)** dispararia múltiplas obrigações — fora deste escopo.

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| `bloqueio_justificativa` com PII cru no audit WORM 5–10 anos | Alta sem R1 | NC LGPD art. 16 + impossível crypto-shredding | **R1** — payload sanitizado + texto bruto fora do audit |
| Funcionário escreve PII na justificativa | Alta sem R2 | Vazamento + NC LGPD | **R2** — enum + regex anti-PII (espelho US-CLI-005) |
| Bloqueio D+90 sem comunicação prévia (CDC art. 6º + Lei 14.181) | Alta sem R3 | Ação consumerista + multa Procon + dano reputacional | **R3** — régua AC-5 vira gate obrigatório; bloqueio auto default OFF até comunicacao-omnichannel existir |
| Cliente PF vulnerável (idoso, PCD, superendividado) bloqueado sem revisão | Média sem R5 | Ação consumerista + LBI + Lei 14.181 | **R5** — pré-alerta 24h + revisão manual |
| Admin Aferê lê PII em suporte forense via audit | Alta sem R6 | NC LGPD art. 6º (necessidade) + quebra INV-013 | **R6** — view sanitizada `audit_trail.authz_decisions_sanitized` |
| Confusão entre bloqueio comercial e negativação SPC/Serasa | Média | Tenant entende errado e exporta sem base legal | Documentar que negativação é módulo separado Wave B+ |
| SLA reativação ≤5min não cumprido em prod (filas atrasadas) | Média | Quebra de SLA contratual + cliente final sem acesso após pagar | DPA tenant↔Aferê redige SLA como "≤5min em 95% dos casos, ≤15min em 99%" |
| Mesclagem de cadastros (US-CLI-005) preserva bloqueio do perdedor → vencedor herda bloqueio inesperado | Média | Cliente correto fica bloqueado por engano | Documentar em US-CLI-005 que mesclagem **não** propaga bloqueio; vencedor mantém seu estado |

---

## Próximos passos

- ✅ Aplicar R1–R6 no plano `US-CLI-004.md` (autoria: agente implementador).
- ✅ Tasks novas (resumo):
  - **T-CLI-019b** — enum 5 valores + sanitizador regex anti-PII em `bloqueio_justificativa`.
  - **T-CLI-019c** — campo `bloqueio_comunicacao_previa_confirmada: bool`.
  - **T-CLI-021b** — flag `Tenant.bloqueio_automatico_inadimplencia_habilitado` (default `False`).
  - **T-CLI-021c** — pré-alerta 24h + estado `bloqueio_pendente_revisao`.
  - **T-CLI-023b** — INV-CLI-BLOQ-001 em `REGRAS-INEGOCIAVEIS.md` (régua AC-5 como gate).
  - **T-CLI-024b** — audit sanitizado + teste `test_bloqueio_audit_sem_pii_cru`.
  - **T-CLI-024c** — INV-013 estendida a `bloqueio_motivo`/`bloqueio_justificativa`.
  - **T-CLI-024d** — view sanitizada `audit_trail.authz_decisions_sanitized` + INV-AUDIT-PII-001 (pode escorregar a Wave A com mitigação compensatória documentada).
- ⚠️ **Antes do go-live público:** advogado humano OAB ativa revisa: (a) textos da régua D+30/60/89, (b) cláusula contratual SLA reativação ≤5min, (c) cláusula DPA sobre responsabilidade do tenant pela legalidade do bloqueio, (d) catálogo de motivos do enum visível ao tenant.
- ⏳ Diferido pra Wave A: implementação real da régua via `comunicacao-omnichannel`; ContasReceber real substitui mock; consumers OS/orçamento/agenda implementam predicado `cliente_bloqueado_para_acao`.
- ⏳ Diferido pra Wave B: módulo `negativacao` (SPC/Serasa/SCR Bacen) com LIA própria; `lgpd-portal` para titular exercer art. 18; flag `Cliente.tratamento_diferenciado` (PCD/idoso/superendividamento).
- ⏳ Diferido pra V2: rollback de bloqueio com restauração de estado anterior; bloqueio parcial (só novas OS, mantém agenda existente).

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 5º I/II, 6º III/V/VI, 7º V/VI/IX, 9º, 16 II, 18 II/III/VI, 37, 46
- Lei 8.078/1990 (CDC) — art. 6º III/IV, 39 V, 42, 51
- Lei 14.181/2021 (superendividamento) — art. 54-A
- Lei 13.146/2015 (LBI) — razoabilidade em relações de consumo
- Lei 9.492/1997 (protesto) — **não aplicável** (declarado como tese)
- CC/2002 — art. 476 (exceção do contrato não cumprido)
- Marco Civil Internet (Lei 12.965/2014) — art. 15 (logs de acesso 6 meses)
- Res. CD/ANPD 15/2024 — incidentes (não aplicável a bloqueio comercial)
- INV-001, INV-005, INV-013, INV-AUTHZ-001, INV-AUTHZ-002, INV-INT-010, INV-TENANT-001/002, SEC-LEAST-PRIV-001 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03 (`docs/conformidade/comum/lgpd-rat.md`)
- `docs/conformidade/comum/retencao-matriz.md` §2
- ADR-0015 fluxo 4 (lifecycle tenant — inadimplência)
- US-CLI-001 revisão `US-CLI-001-advogado.md` (veto PII em audit — precedente)
- US-CLI-005 revisão `US-CLI-005-advogado.md` (R1/R2 — enum + sanitizador, precedente espelhado)
