---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-EQP-002
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-002.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-EQP-002 (LGPD + Assinatura Eletrônica + Auditoria Regulatória)

> **Aviso legal obrigatório:** subagente IA, sem OAB ativa, texto consultivo. As mensagens PT de rejeição (§3), o texto do parecer técnico assinado pelo RT (§4) e o registro de aprovação do gestor da qualidade (§5) precisam revisão de advogado humano OAB ativa **antes do go-live público** (não bloqueia MVP-1 dogfooding). Quando a integração real Lacuna Web PKI substituir o `MockAssinaturaA3Service`, repete-se a revisão.

---

## Veredito

**APROVADO COM RESSALVAS.** O plano US-EQP-002 está sólido na arquitetura: INV-025 + versionamento imutável + enum `motivo_mudanca` + workflow `gestor_qualidade` + A3 em perfil A para classe/faixa atendem ISO/IEC 17025 cl. 7.8 + 8.4 e Lei 14.063/2020. Mas seis pontos exigem ajuste antes de promover a `stable` — todos focados nas novidades desta US (mensagens de rejeição, parecer assinado, aprovação do gestor, anti-PII no texto livre, sanitização dos eventos).

A base legal mestre para a imutabilidade pós-cert (INV-025) é **art. 7º II + art. 16 I da LGPD** — a obrigação regulatória (ISO/IEC 17025 cl. 7.8 “Garantia da validade dos resultados” + cl. 8.4 “Controle de registros”) prevalece sobre direito ao esquecimento (art. 18 VI) enquanto durar o ciclo de retenção do certificado emitido.

### Ressalvas (R1–R6)

1. **R1 — Texto PT da rejeição 422 ao tentar editar imutável pós-cert:** padronizar mensagem com (a) campo bloqueado, (b) motivo em linguagem do operador, (c) base regulatória citada explicitamente, (d) caminho alternativo (criar versão / dar baixa por sucateamento). Sem isso, o atendente fica perdido e abre chamado de “sistema travado” quando, na verdade, há motivo regulatório. Texto pronto em §3.
2. **R2 — Audit do parecer do gestor de qualidade na aprovação `motivo=outros` precisa ser tão imutável quanto o do RT.** Plano (T-EQP-024) coloca a aprovação em tabela `AprovacaoPendenteEquipamentoVersao`, mas não declara: (i) que a decisão (`aprovado`/`rejeitado`) é **imutável após gravada** (trigger PG anti-UPDATE/DELETE), (ii) que o registro vincula `gestor_user_id`, `gestor_user_id_hash` (sobrevive ao crypto-shredding do gestor que saiu da empresa), `decisao_em` (UTC), `ip_hash`, `ua_hash`, `parecer_texto` (texto livre — exige regex anti-PII espelho INV-EQP-LOC-001), `decisao_assinatura_hash` (HMAC tenant-salt do payload {gestor_id, equipamento_id, versao_n, decisao, parecer, timestamp}). Sem isso, a aprovação vira “quem aprovou o quê quando” sem prova auditável — ISO 17025 cl. 8.4 quebra. Detalhe em §5.
3. **R3 — Texto do parecer técnico que o RT assina via A3 precisa ser versionado e congelado no snapshot da versão.** Plano cita campo `assinatura_a3_hash` em `EquipamentoVersao` (T-EQP-020), mas falta `assinatura_a3_versao_texto_id` (FK pro catálogo de textos versionados do parecer). Sem isso, em 5 anos o RT pode alegar “não foi isso que assinei — o sistema mudou o texto depois”. Espelho exato da R2 do US-CLI-001 (versionamento de aceite LGPD). Texto sugerido em §4 + adicionar campo na T-EQP-020.
4. **R4 — `motivo_detalhe` (texto livre ≥100 chars quando `motivo=outros`) é vetor de PII indireto.** Operador apressado escreve “troquei porque o Sr. Carlos da Silva, CPF 123.456.789-00, do cliente Padaria do Zé, reclamou que a balança…”. Plano não aplica nenhuma validação. Aplicar **mesma regex anti-PII** de `localizacao_fisica` (INV-EQP-LOC-001) ao campo `motivo_detalhe` — espelho exato. Promover a **INV-EQP-VERSAO-001** nova: `motivo_detalhe` E `parecer_gestor_texto` rejeitam CPF / CNPJ / e-mail / telefone / nomes capitalizados ≥2 palavras consecutivas com 400 + mensagem PT clara (§3). Acrescentar teste `test_motivo_detalhe_com_pii_rejeita` à lista T-EQP-026.
5. **R5 — Sanitização do payload de eventos `equipamento.editado` e `equipamento.versao_criada`.** Plano T-EQP-025 cita payload `{equipamento_id, versao_n, campos_alterados[], motivo_mudanca, assinou_a3}` — está adequado para `versao_criada`. Falta declarar explicitamente que (a) `campos_alterados[]` carrega apenas **nome do campo**, nunca o valor antigo/novo (valores ficam no snapshot do `EquipamentoVersao`, sob RLS), (b) `motivo_detalhe` E `parecer_gestor_texto` NUNCA entram no envelope do bus (são consultáveis via API autorizada — bus replica para Wave B BI e perderia RLS), (c) eventos carregam `cliente_atual_id_no_momento_hash` (não UUID — espelho B1 do PRD-advogado), (d) `assinatura_a3_hash` no envelope é apenas hash truncado de 16 bytes (prova de existência, não conteúdo). Detalhe em §6.
6. **R6 — SLA do workflow `gestor_qualidade` precisa de política de escalonamento e fallback de gestor único.** Plano §Riscos C3 cita “job D+7 escala alerta P2” — ok, mas falta: (a) o que acontece se o tenant tem **apenas 1 gestor de qualidade** e ele está afastado/desligado? Precisa fallback `admin_tenant` pode auto-promover outro usuário a `gestor_qualidade` interino (auditado), (b) política de **conflito de interesses**: o próprio gestor que aprova NÃO pode ter sido o autor da edição que solicitou aprovação (ISO 17025 cl. 6.2 segregação de funções) — bloqueio backend no use case; (c) prazo legal: D+7 é razoável para metrologia, mas reduzir para D+3 quando a edição afeta `classe_exatidao`/`faixa_medicao` (atributos que entram no escopo de acreditação CGCRE). Detalhe em §5.

### Não-ressalvas (validadas como corretas)

- ✅ **Base legal mestre INV-025:** art. 7º II (obrigação legal/regulatória) + art. 16 I (retenção para cumprir obrigação). ISO/IEC 17025 cl. 7.8.6 (“Garantia da validade dos resultados anteriores”) + cl. 8.4.2 (“os registros devem ser mantidos por período definido… legíveis, prontamente identificáveis e recuperáveis”) sustentam a imutabilidade pós-cert. **Não é exigência LGPD pura — é o art. 7º II habilitando o cumprimento da norma técnica.**
- ✅ **Assinatura A3 do RT em perfil A para classe/faixa:** correto. Lei 14.063/2020 art. 4º III (qualificada, ICP-Brasil) + MP 2.200-2/2001 art. 10 §1º — assinatura digital com certificado emitido por AC credenciada na ICP-Brasil tem **presunção de veracidade** entre as partes e perante terceiros. Para perfil A (acreditação CGCRE), essa presunção é o que sustenta o certificado de calibração emitido pelo laboratório acreditado em juízo (NIT-DICLA-030 + ABNT NBR ISO/IEC 17025 cl. 7.5).
- ✅ **Perfil B não exige A3:** correto. Fora do escopo de acreditação CGCRE, a parametrização é decisão técnica interna do laboratório — assinatura simples (Lei 14.063/2020 art. 4º I, login + timestamp + IP hash) basta. Não confundir com perfil A.
- ✅ **Enum fechado `motivo_mudanca` (6 valores RBC B7):** correto. ISO 17025 cl. 8.4.3 exige registros “rastreáveis e identificáveis” — enum fechado dá taxonomia auditável; “outros” + justificativa ≥100 chars + workflow gestor é a válvula de escape adequada (não cria categoria infinita; força revisão humana).
- ✅ **Snapshot incluir `cliente_atual_id_no_momento`:** correto e já refletido na decisão tech-lead C2. Snapshot guarda valor no momento da mudança de versionável — alinha com B1 do PRD-advogado (hash referência sobrevive ao crypto-shredding).
- ✅ **Trigger PG `bloquear_update_imutaveis_pos_cert` consultando porta `CertificadoQueryService` via função SQL stub:** correto. Stub retorna `false` enquanto módulo certificados não existe (US-EQP-002 não pode esperar Wave B). Hook `port-binding-validator` (T-EQP-003) bloqueia release prod com stub — esse é o gate regulatório.
- ✅ **`MockAssinaturaA3Service` sempre retorna ok:** aceitável para Wave A Marco 2 dogfooding, **desde que** o adapter real (`LacunaWebPkiAssinaturaA3Service`) seja substituído antes do go-live público com qualquer perfil A. Hook `port-binding-validator` cobre.

---

## §3 — Textos PT prontos para colar (mensagens de rejeição 422 / 400)

### 3.1 — Rejeição ao editar **TAG** pós-cert

> **Não é possível alterar a TAG deste equipamento.**
>
> Já existe certificado de calibração emitido para esta TAG. A norma **ABNT NBR ISO/IEC 17025 cláusula 8.4** exige que o identificador de campo permaneça inalterado durante todo o ciclo de retenção do certificado, para garantir rastreabilidade entre o certificado emitido e o equipamento físico.
>
> **O que fazer:**
> - Se a etiqueta física foi perdida ou danificada, imprima a mesma TAG novamente (a TAG é um identificador lógico, não a etiqueta).
> - Se o equipamento foi substituído por outro, cadastre o novo como equipamento separado e dê baixa neste (status “sucatear”).

### 3.2 — Rejeição ao editar **número de série**

> **Não é possível alterar o número de série deste equipamento.**
>
> Já existe certificado de calibração emitido. O número de série é o vínculo legal entre o certificado e o equipamento físico do fabricante — alterá-lo invalidaria o histórico de calibrações perante auditoria CGCRE (NIT-DICLA-030) e ANVISA/INMETRO.
>
> **Base regulatória:** ABNT NBR ISO/IEC 17025 cl. 7.8.2 (conteúdo do certificado) + cl. 8.4 (controle de registros).
>
> **Se o número está errado no cadastro:** corrija via fluxo “correção de erro material” (motivo `correcao_cadastro_inicial`) — exige aprovação do gestor da qualidade e justificativa documentada.

### 3.3 — Rejeição ao editar **fabricante**

> **Não é possível alterar o fabricante deste equipamento.**
>
> Já existe certificado de calibração emitido. O fabricante consta no certificado emitido ao cliente — alterá-lo violaria a integridade do registro técnico exigida pela **norma ABNT NBR ISO/IEC 17025 cláusula 8.4**.
>
> **Se houve erro de cadastro:** abra solicitação de correção (motivo `correcao_cadastro_inicial`) com justificativa e aguarde aprovação do gestor da qualidade.

### 3.4 — Rejeição ao editar **perfil_tenant_no_momento_cadastro**

> **Não é possível alterar o perfil do laboratório associado a este equipamento.**
>
> Já existe certificado de calibração emitido. O perfil (A — acreditado CGCRE / B — não acreditado) consta no certificado emitido e determina o escopo regulatório aplicado (RBC B4). Alterá-lo retroativamente colocaria o laboratório em descumprimento do **regulamento RBC NIT-DICLA-005** e da **ABNT NBR ISO/IEC 17025 cl. 5.5**.
>
> Esse campo é um instantâneo regulatório do momento do cadastro e permanece fixo.

### 3.5 — Rejeição 400 ao detectar PII em `motivo_detalhe` (R4)

> **Identifiquei dados pessoais no texto da justificativa.**
>
> A justificativa de alteração ficará registrada em trilha de auditoria de longo prazo (até 25 anos conforme ISO/IEC 17025 cl. 8.4) e em eventos do sistema. Para proteger os dados pessoais dos seus clientes e funcionários (Lei 13.709/2018 art. 6º incisos III e V — princípios da necessidade e qualidade), **não inclua aqui:**
> - CPF, CNPJ, RG ou outros documentos;
> - nomes próprios de pessoas (use cargo: “o atendente”, “o cliente”, “o técnico”);
> - e-mail ou telefone;
> - endereço residencial.
>
> Descreva apenas **o fato técnico** que motivou a alteração. Os dados do cliente já estão no cadastro dele e ficam vinculados pelo identificador.

### 3.6 — Rejeição 422 ao tentar editar `classe_exatidao` ou `faixa_medicao` em perfil A sem A3

> **Esta alteração exige assinatura digital do Responsável Técnico.**
>
> Este laboratório opera em **perfil A (acreditado CGCRE)** para este equipamento. Alterações em **classe de exatidão** ou **faixa de medição** afetam o escopo de acreditação publicado e, pela **ABNT NBR ISO/IEC 17025 cláusula 7.5** combinada com a **Lei 14.063/2020 artigo 4º inciso III** e a **MP 2.200-2/2001**, exigem assinatura digital qualificada (certificado A3 ICP-Brasil) do Responsável Técnico.
>
> **Como prosseguir:** conecte o token A3 do RT no computador, autorize a assinatura quando o sistema pedir, e a alteração será registrada com o parecer técnico assinado.

---

## §4 — Texto do parecer técnico que o RT assina via A3 (PT-BR, versionado)

Texto candidato versão **1.0** — armazenar em `EquipamentoVersaoParecerTextoCatalogo` (tabela nova, igual ao catálogo de finalidades LGPD do US-CLI-001) e referenciar via `assinatura_a3_versao_texto_id` no `EquipamentoVersao` (T-EQP-020 adendo R3).

> **Parecer técnico do Responsável Técnico — Alteração de atributo regulado de equipamento (perfil A)**
>
> Eu, na qualidade de **Responsável Técnico** do laboratório **[Razão Social do Tenant]** (CNPJ {HASH_TENANT}), declaro que:
>
> 1. Avaliei tecnicamente a alteração proposta no equipamento de **TAG {TAG}** / número de série **{NS}**, fabricante **{FABRICANTE}** modelo **{MODELO}**, versão **v{N}**;
> 2. A alteração refere-se a **{CAMPO_ALTERADO}** — de **{VALOR_ANTERIOR}** para **{VALOR_NOVO}**;
> 3. O motivo da alteração é **{MOTIVO_CATEGORIA_LEGIVEL}** (categoria fechada conforme ABNT NBR ISO/IEC 17025 cl. 8.4);
> 4. A alteração está em conformidade com o escopo de acreditação CGCRE deste laboratório e com a **NIT-DICLA-030** vigente, **OU** justifica-se por correção de erro material previamente identificado;
> 5. Os certificados anteriores deste equipamento (versões 1..{N-1}) permanecem válidos para o período em que foram emitidos, conforme cl. 7.8.6, e estão preservados como registro imutável;
> 6. Assumo a responsabilidade técnica por esta alteração para todos os efeitos da **Lei nº 9.933/1999**, do **Decreto nº 6.275/2007** e do regulamento **RBC** vigente.
>
> Esta declaração é assinada digitalmente com certificado A3 ICP-Brasil em conformidade com a **Lei nº 14.063/2020 art. 4º III** e a **MP 2.200-2/2001**, gerando presunção de autoria e integridade do documento.

**Justificativa do texto (jurídica):**
- Cita expressamente as duas leis-base (14.063/2020 art. 4º III + MP 2.200-2/2001) — sustenta presunção de autoria.
- Cita ISO/IEC 17025 cl. 7.8.6 + 8.4 — alinha com obrigação regulatória (LGPD art. 7º II).
- Identifica RT por **vínculo de função** (não por nome) — o hash do user_id é o que vai pro audit; o nome aparece apenas no PDF impresso do parecer, gerado server-side com dados do diretório do tenant.
- Lista o campo + valores anterior/novo no **texto exibido**, mas o **hash assinado** carrega esses valores hasheados (não em claro) — evita que valor em claro vaze via inspeção de transação A3.
- O `assinatura_a3_versao_texto_id` aponta para este texto exato; mudança no texto cria versão 1.1 (novos pareceres usam 1.1, históricos preservam vínculo com 1.0).

---

## §5 — Audit do parecer do gestor de qualidade (R2 + R6)

### 5.1 — Modelo `AprovacaoPendenteEquipamentoVersao` — campos obrigatórios

Plano T-EQP-024 cita a tabela mas não define campos. Especificação jurídica mínima (espelho do que ISO 17025 cl. 8.4 + LGPD art. 37 exigem como registro auditável):

```
aprovacao_pendente_equipamento_versao
├── id (UUID)
├── tenant_id (UUID, RLS)
├── equipamento_id (UUID)
├── versao_n_proposta (int)
├── snapshot_proposto (JSONB — payload completo)  ← imutável
├── motivo_mudanca (enum, sempre 'outros' nesta tabela)
├── motivo_detalhe (text, ≥100 chars, regex anti-PII INV-EQP-VERSAO-001)
├── solicitante_user_id (UUID)
├── solicitante_user_id_hash (bytes 32, salt tenant)  ← sobrevive crypto-shredding
├── solicitada_em (timestamptz, UTC)
├── solicitante_ip_hash (bytes 32)
├── status (enum: 'pendente'|'aprovada'|'rejeitada'|'cancelada')
├── gestor_user_id (UUID, NULL até decisão)
├── gestor_user_id_hash (bytes 32, NULL até decisão)  ← R2
├── decisao_em (timestamptz UTC, NULL até decisão)
├── decisao_ip_hash (bytes 32, NULL)
├── decisao_ua_hash (bytes 32, NULL)
├── parecer_gestor_texto (text, regex anti-PII, ≥50 chars quando rejeita ou aprova com ressalva)
├── decisao_assinatura_hash (bytes 32 — HMAC-SHA256(tenant_salt, payload))  ← R2 prova de integridade
├── sla_prazo_em (timestamptz — D+3 se afeta classe/faixa; D+7 caso contrário)  ← R6
├── escalado_em (timestamptz, NULL — preenchido quando job de SLA dispara alerta)
└── (sem updated_at; registro é imutável após decisão — trigger anti-UPDATE)
```

### 5.2 — Imutabilidade da decisão (R2)

Trigger PG nova `bloquear_update_decisao_aprovacao`:
- Quando `status` transiciona de `pendente` para `aprovada`/`rejeitada` → permite UPDATE (única transição válida).
- Quando `status` já é `aprovada`/`rejeitada` → bloqueia qualquer UPDATE com erro: `"aprovação já decidida; alterações exigem nova solicitação de versão"`.
- Bloqueia DELETE em qualquer status diferente de `cancelada` (cancelamento só por solicitante antes da decisão).

Hook `audit-immutability-check` (já existe) deve ser ESTENDIDO para também bloquear `DROP TRIGGER bloquear_update_decisao_aprovacao`. Adicionar entrada ao hook em US-EQP-002 (não criar hook novo).

### 5.3 — Segregação de funções (R6 item b)

No use case `DecidirAprovacaoVersao`:
```
if aprovacao.solicitante_user_id == request.user.id:
    raise PermissionDenied(
        "Conflito de interesses: o solicitante da alteração não pode aprovar a própria solicitação. "
        "ABNT NBR ISO/IEC 17025 cláusula 6.2 (segregação de funções)."
    )
```
Teste novo: `test_solicitante_nao_pode_aprovar_propria_versao`.

### 5.4 — SLA diferenciado (R6 item c)

Job D+3 quando `snapshot_proposto.campos_alterados` contém `classe_exatidao` ou `faixa_medicao` (alto impacto regulatório CGCRE); D+7 nos demais casos. Após o prazo, dispara alerta P2 ao `admin_tenant` (e-mail + notificação in-app).

### 5.5 — Fallback gestor único (R6 item a)

Política operacional (não invariante de código): se tenant tem 0 ou 1 usuário com role `gestor_qualidade` ativo, o `admin_tenant` pode atribuir interinamente outro usuário ao papel via fluxo já existente do `authz` (registrado como evento `usuario.papel_atribuido_interinamente`, audit obrigatório).

---

## §6 — Sanitização dos eventos `equipamento.editado` e `equipamento.versao_criada` (R5)

Especificação do envelope do bus — declarar explicitamente em `docs/comum/catalogo-eventos.md` (atualizar quando US-EQP-002 entrar em implementação):

### `equipamento.editado` (UPDATE direto pré-cert)
```json
{
  "evento_id": "uuid",
  "tenant_id": "uuid",
  "ts": "ISO-8601 UTC",
  "ator_user_id_hash": "bytes32 base64",
  "equipamento_id": "uuid",
  "campos_alterados": ["modelo", "localizacao_fisica"],    // ← nomes, nunca valores
  "motivo_mudanca": "correcao_cadastro_inicial",            // ← enum, valor controlado
  "perfil_tenant_no_momento": "A|B"
}
```

### `equipamento.versao_criada` (pós-cert)
```json
{
  "evento_id": "uuid",
  "tenant_id": "uuid",
  "ts": "ISO-8601 UTC",
  "ator_user_id_hash": "bytes32 base64",
  "equipamento_id": "uuid",
  "versao_n": 3,
  "versao_anterior_n": 2,
  "campos_alterados": ["classe_exatidao", "faixa_medicao"],
  "motivo_mudanca": "outros",
  "exigiu_a3_rt": true,
  "assinatura_a3_hash_truncado": "bytes16 base64",          // ← prova de existência
  "assinatura_a3_versao_texto_id": "uuid",
  "aprovacao_pendente_id": "uuid",                          // ← referência
  "cliente_atual_id_no_momento_hash": "bytes32 base64",     // ← B1 PRD; nunca UUID
  "perfil_tenant_no_momento": "A|B"
}
```

### Proibições explícitas no envelope (cravar em invariante `INV-EQP-VERSAO-002`)
- ❌ **Nunca** carregar `motivo_detalhe` (texto livre) no bus — replicação Wave B BI perderia RLS e pode conter PII residual mesmo com regex.
- ❌ **Nunca** carregar `parecer_gestor_texto` no bus — mesma razão.
- ❌ **Nunca** carregar valor antigo/novo de campos versionados — esses ficam apenas no `EquipamentoVersao` (sob RLS).
- ❌ **Nunca** carregar UUID cru de `cliente_atual_id_no_momento` — apenas hash salgado por tenant.
- ❌ **Nunca** carregar a assinatura A3 completa — apenas hash truncado de 16 bytes (prova de existência, não conteúdo).

Adicionar teste `test_evento_versao_criada_nao_vaza_motivo_detalhe` à T-EQP-026.

---

## Análise por área

### LGPD / Privacidade

- **Base legal da imutabilidade pós-cert (INV-025):** art. 7º II (obrigação legal/regulatória — ISO 17025 + RBC + portarias INMETRO) + art. 16 I (retenção para cumprir obrigação). Prevalece sobre direito ao esquecimento (art. 18 VI) durante ciclo de retenção do certificado. **Não há conflito** — é o art. 16 I funcionando como projetado.
- **Texto livre (`motivo_detalhe`, `parecer_gestor_texto`):** vetor clássico de PII indireto. Regex anti-PII espelho do `localizacao_fisica` (US-CLI-004 R2 / INV-EQP-LOC-001) — promovido a invariante novo **INV-EQP-VERSAO-001**.
- **Hash do gestor (`gestor_user_id_hash`):** sobrevive ao crypto-shredding do gestor que sai da empresa (mesma lógica B1 do PRD para cliente). LGPD art. 18 VI atendido (UUID some) sem perder rastreabilidade ISO 17025 (hash permanece).
- **Audit do parecer técnico assinado por A3:** preserva conteúdo do parecer (texto + hash da assinatura). Isso é dado pessoal? **Não diretamente** — o parecer fala de equipamento. O nome do RT aparece no PDF gerado server-side mas no banco fica `user_id_hash`. LGPD art. 7º II habilita a retenção.

### Contratual

- **Lei 14.063/2020 art. 4º:**
  - inc. I — assinatura simples (login + IP + timestamp): usada em perfil B + edição pré-cert + aceite simples.
  - inc. II — assinatura avançada (mecanismos forte de autenticação, não-ICP): não usada nesta US.
  - inc. III — assinatura qualificada (ICP-Brasil A1/A3): **obrigatória** em perfil A para classe/faixa.
- **MP 2.200-2/2001 art. 10 §1º:** documento assinado com cert ICP-Brasil tem presunção de veracidade entre signatários e perante terceiros. É o que sustenta o certificado de calibração em juízo.
- **Defesa anti-replay (recomendada — não bloqueia esta US, mas é cabeça pro adapter real):** nonce server-side + signing-time server-controlled + one-shot (já em ADR-0009).

### Regulatório

- **ABNT NBR ISO/IEC 17025:**
  - cl. 6.2 — segregação de funções (R6 item b — solicitante não aprova).
  - cl. 7.5 — controle de dados e gestão da informação.
  - cl. 7.8.2 — conteúdo do certificado (identificação inequívoca do item).
  - cl. 7.8.6 — garantia da validade dos resultados (versões anteriores válidas no período em que vigeram).
  - cl. 8.4.2/8.4.3 — controle de registros (legíveis, identificáveis, recuperáveis, sem alteração não-autorizada).
- **NIT-DICLA-005 + NIT-DICLA-030:** escopo de acreditação CGCRE — alteração em `classe_exatidao`/`faixa_medicao` em perfil A pode afetar escopo publicado; **fora do escopo** o laboratório perde o direito de emitir certificado RBC para aquele atributo (decisão técnica do RT, suportada por A3).
- **Lei 9.933/1999 + Decreto 6.275/2007 (Conmetro):** responsabilidade do RT por declaração técnica — texto §4 carrega menção expressa para sustentar imputação em caso de auditoria/fiscalização.

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Mensagem 422 genérica ao bloquear edição → atendente abre chamado de “sistema travado” | Alta sem R1 | Suporte sobrecarregado + atendente força workaround | R1 — textos §3 com base regulatória citada |
| `motivo_detalhe` ou `parecer_gestor_texto` virar reservatório de PII de clientes | Alta sem R4 | NC LGPD art. 6º III/V + risco vazamento | R4 — INV-EQP-VERSAO-001 (regex anti-PII espelho) |
| Aprovação do gestor sem audit imutável → ISO 17025 cl. 8.4 quebra | Média sem R2 | Perda de acreditação CGCRE | R2 — trigger PG anti-UPDATE + decisao_assinatura_hash |
| Texto do parecer do RT mudar depois sem versionamento → RT contesta autoria | Média sem R3 | Perda de presunção de veracidade do A3 + responsabilidade técnica diluída | R3 — `assinatura_a3_versao_texto_id` + catálogo versionado |
| Evento `versao_criada` vazar PII para BI/replicas perdendo RLS | Média sem R5 | Vazamento sistêmico cross-tenant na Wave B | R5 — INV-EQP-VERSAO-002 (proibições explícitas no envelope) |
| Solicitante aprova a própria solicitação → segregação de funções (cl. 6.2) violada | Alta se UI não bloqueia | NC CGCRE + risco de fraude operacional | R6.b — bloqueio backend `solicitante != aprovador` |
| Tenant com 1 só gestor de qualidade afastado → workflow paralisa | Baixa, mas crítica quando ocorre | Operação bloqueada por dias/semanas | R6.a — admin_tenant atribui interino auditado |
| `MockAssinaturaA3Service` chega em produção sem substituição | Baixa (hook port-binding cobre) | Falso atestado A3 → invalida certificados | Hook `port-binding-validator` bloqueia release prod |

---

## Próximos passos

- ✅ Aplicar R1–R6 no plano `US-EQP-002.md` (autoria: agente que implementar).
- ✅ Promover **INV-EQP-VERSAO-001** (regex anti-PII em `motivo_detalhe` e `parecer_gestor_texto`) e **INV-EQP-VERSAO-002** (proibições no envelope de eventos) em `REGRAS-INEGOCIAVEIS.md`.
- ✅ Estender hook `audit-immutability-check.sh` para cobrir `bloquear_update_decisao_aprovacao` (não criar hook novo; adicionar à allowlist negativa).
- ✅ Adicionar 4 testes novos à T-EQP-026: `test_motivo_detalhe_com_pii_rejeita`, `test_parecer_gestor_com_pii_rejeita`, `test_solicitante_nao_pode_aprovar_propria_versao`, `test_evento_versao_criada_nao_vaza_motivo_detalhe`.
- ✅ Criar `docs/conformidade/equipamentos/parecer-rt-texto-v1.md` com o texto §4 versionado (catálogo).
- ⚠️ **Antes do go-live público com qualquer perfil A:** advogado humano OAB ativa revisa: (a) texto §4 do parecer assinado (responsabilidade técnica do RT em juízo), (b) integração real Lacuna Web PKI substituindo `MockAssinaturaA3Service` (cláusula DPA Aferê↔Lacuna), (c) mensagens §3 (linguagem regulatória sustentada). Recomendo consulta pontual com advogado especializado em (i) direito digital + assinatura ICP-Brasil, (ii) regulação metrológica/INMETRO/CGCRE. Estimo 3-4h de revisão com este parecer + PRD-advogado + ADR-0009 pré-lidos.
- ⏳ Diferido: integração real Lacuna Web PKI (depende ADR-0009 fechar); endpoint próprio + UI HTMX do gestor (Marco 2 deixa via Django admin).

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 5º VI/VII, 6º III/V, 7º II/V, 11 (não aplicável aqui), 16 I/II, 18 VI, 37
- Lei 14.063/2020 — art. 4º I/II/III (assinatura eletrônica simples/avançada/qualificada)
- MP 2.200-2/2001 — art. 10 §1º (presunção de veracidade ICP-Brasil)
- Lei 9.933/1999 + Decreto 6.275/2007 — Conmetro / responsabilidade técnica
- ABNT NBR ISO/IEC 17025 — cl. 6.2, 7.5, 7.8.2, 7.8.6, 8.4.2, 8.4.3
- NIT-DICLA-005 (acreditação) + NIT-DICLA-030 (rastreabilidade) — CGCRE
- ADR-0009 (onde A3 assina — cliente-side via Lacuna)
- ADR-0017 (CNPJ alfanumérico — IN RFB 2.229/2024) — para hashes de tenant
- INV-025, INV-049..051, INV-EQP-LOC-001 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-EQP-FOTO (a criar — B4 do PRD-advogado)
- US-CLI-001-advogado.md R2 + US-CLI-004 R2 (espelho regex anti-PII + versionamento de texto assinado)
