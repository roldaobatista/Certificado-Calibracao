---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: draft
diataxis: reference
audiencia: agente
marco: Wave A Marco 1 — clientes
tipo: especificacao-forward
substitui:
  - docs/dominios/comercial/modulos/clientes/auditorias/CONSOLIDADO.md (retroativo)
relacionados:
  - .specify/memory/constitution.md
  - docs/dominios/comercial/modulos/clientes/prd.md
  - docs/dominios/comercial/modulos/clientes/modelo-de-dominio.md
  - docs/faseamento/F-A/spec.md
  - docs/faseamento/F-B/spec.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0015-lifecycle-tenant.md
  - docs/adr/0017-cnpj-alfanumerico.md
  - REGRAS-INEGOCIAVEIS.md
---

# Wave A — Marco 1 (clientes) — Especificação (forward, autoritativa)

> **O que este documento é (Constituição §1, §2):** a fonte da verdade
> do que o Marco 1 `clientes` **deve fazer**. Spec-as-source: o código é
> derivado/validado contra esta spec — não o contrário. Onde código
> divergir desta spec (após revisão dos 4 subagentes), **o código é
> corrigido**, não a spec.
>
> **Por que existe (decisão Roldão 2026-05-18→2026-05-19):** Marco 1
> foi construído US a US sem spec-mãe; a auditoria 10 lentes
> (`docs/dominios/comercial/modulos/clientes/auditorias/CONSOLIDADO.md`)
> identificou 3 vereditos negativos e 10 SANEA bloqueantes. Saneamento
> US a US convergiu parcialmente — SANEA-04, 05, 07, 08, 09 e Onda 2
> ainda têm gaps. Esta spec recria o passo 1 (governa o código),
> reconciliação acontece em P3/P4.
>
> **Pra Roldão (uma frase):** este é o "contrato" do módulo que cadastra
> os clientes do tenant, com a regra exata de cada tela e do que NÃO
> entra aqui.

---

## 1. Escopo

Cadastro PF/PJ multi-tenant + Visão 360° auditada + Importação CSV/XLSX
+ Bloqueio comercial (manual + automático por inadimplência) + Dedup
manual e automático. Construído sobre F-A (multi-tenant + RLS + audit +
PII HMAC) e F-B (auth + authz unificada + MFA real), seguindo
nomenclatura PT e ADR-0007 (domínio + spec→código).

### Non-goals explícitos (Constituição §5 — proibição positiva)

Marco 1 `clientes` **NÃO** entrega, e nenhum agente deve inferir que
entrega:

- **NG-CLI-1**: cadastro do **equipamento** do cliente — Marco 2
  (`suporte-plataforma/equipamentos`).
- **NG-CLI-2**: histórico técnico de calibração — `operacao/certificados`.
- **NG-CLI-3**: lead não-convertido — `crm/leads`; lead vira cliente só
  ao converter.
- **NG-CLI-4**: cobrança ativa/boleto/régua — `financeiro/contas-receber`.
  Aqui só **consume** evento de inadimplência.
- **NG-CLI-5**: rating externo (Serasa/SPC) — V2.
- **NG-CLI-6**: portal self-service do cliente final — V2.
- **NG-CLI-7**: CRM custom fields com lógica condicional — Wave B.
- **NG-CLI-8**: mailing/campanha — fora do produto.
- **NG-CLI-9**: integração ReceitaWS/CNPJ realtime — V2 (validação
  algorítmica obrigatória aqui; consulta externa não).
- **NG-CLI-10**: hash chain dedicada de `acessos_dados_cliente` — F-A
  AC-FA-005-7 deixa explícita a decisão: imutabilidade vem do trigger
  PG; hash chain é gate Wave A se ANPD/CGCRE exigir.

### Invariantes governados (Constituição Regra mestre 2 — citar IDs)

Texto canônico em `REGRAS-INEGOCIAVEIS.md`. Marco 1 `clientes` materializa:
`INV-024` (dedup unique por tenant+tipo_pessoa+documento), `INV-013`
(log de visualização de PII), `INV-INT-010` (cliente bloqueado bloqueia
operação), `INV-001` (auditoria imutável — via F-A), `INV-TENANT-001..004`
(multi-tenant — via F-A), `INV-AUTHZ-001..003` (autorização — via F-B),
`SEC-CSV-001` (anti-injection em export — abaixo, novo ID).

Marco 1 **introduz** os IDs novos:
- `INV-CLI-001` (âncora de identidade canônica — SANEA-05),
- `INV-CLI-002` (política LGPD única — SANEA-07),
- `SEC-CSV-001` (anti-injection em geração de CSV — formalização do
  comportamento já em `csv_safety.py` após SANEA-03).

---

## 2. Como ler as User Stories

`US-CLI-NNN` → `AC-CLI-NNN-N` (aceite **binário**: passou / não passou).
Cada AC ganha em P3 (`tasks.md`) coluna **Estado**: `OK` (código satisfaz,
validado), `GAP` (diverge — vira `T-CLI-NNN`), `TRACK` (gate Wave A
rastreado — não bloqueia fechamento do marco). Esta spec define o alvo;
P3 mede.

Severidade no fechamento: `INV-RITUAL-001` — MÉDIO bloqueia igual a
CRÍTICO/ALTO; só BAIXO é rastreável.

---

## US-CLI-001 — Cadastro PF/PJ < 1 min com dedup e aceite LGPD

**Como** atendente, **quero** abrir formulário curto e cadastrar PF
(CPF) ou PJ (CNPJ) com validação algorítmica imediata e aceite LGPD
obrigatório, **para** começar atendimento sem perder o cliente na linha.

- **AC-CLI-001-1**: POST `/clientes/` com CPF/CNPJ válido pelo algoritmo
  oficial (Mod-11 para CPF; ADR-0017 CNPJ alfanumérico tratado
  uniformemente — letras + dígitos `[A-Z0-9]{14}` válido até dígito
  verificador) cria `Cliente`(id UUID, tenant_id, tipo_pessoa,
  documento, nome, e-mail, telefone, endereço, segmento) com
  `tenant_id` injetado do middleware (nunca do cliente).
- **AC-CLI-001-2**: documento inválido pelo algoritmo retorna 400 com
  mensagem clara — sem fallback de validação fraca.
- **AC-CLI-001-3**: documento **já existente ativo** no mesmo tenant
  retorna 409 com link pro cliente existente (`INV-024` — UNIQUE
  parcial `(tenant_id, tipo_pessoa, documento) WHERE soft_deleted_at IS
  NULL`). Cliente soft-deletado com mesmo documento NÃO bloqueia
  recadastro.
- **AC-CLI-001-4**: aceite LGPD é OBRIGATÓRIO — sem `aceite_lgpd_em` o
  POST retorna 400. `aceite_lgpd_em`, `aceite_lgpd_base_legal` (enum:
  `CONSENTIMENTO`, `EXECUCAO_CONTRATO`, `OBRIG_LEGAL`),
  `aceite_lgpd_declaracao_id` (FK pra declaração ativa do tenant)
  gravados imutáveis (LGPD art. 8 §6 — prova do consentimento).
- **AC-CLI-001-5**: criar publica `Cliente.Criado` no bus com `tenant_id`,
  `cliente_id`, `documento_hash` (HMAC F-A — nunca documento cru),
  `aceite_lgpd_base_legal`, `causation_id` da request.
- **AC-CLI-001-6**: criar registra elo na cadeia de auditoria do tenant
  (F-A `registrar_auditoria` cadeia tenant), com `action="cliente.criado"`
  e payload canonicalizado sanitizado (`sanitizar_payload_audit` aplicado
  em ESCRITA, não só leitura — `SEC-SANITIZE-001`).

## US-CLI-002 — Visão 360° auditada (timeline + abas)

**Como** atendente/vendedor, **quero** abrir `/clientes/{id}` e ver
tudo do cliente em uma tela (timeline + abas: OS, certificados,
financeiro, contatos, NPS, anexos), **para** atender sem trocar de aba.

- **AC-CLI-002-1**: GET `/clientes/{id}/visao360/` retorna timeline
  cronológica reversa com eventos consolidados dos módulos vizinhos
  via projeção de eventos do bus (`EventoTimeline` materialização local
  no schema tenant — fonte única, atualizada por consumers).
- **AC-CLI-002-2**: p95 < 1.5s para cliente com até 500 eventos no
  período de 12 meses. Paginação obrigatória (cursor por timestamp)
  acima de 100 eventos por janela.
- **AC-CLI-002-3** (`INV-013`): cada GET grava ANTES de renderizar uma
  linha em `AcessoDadosCliente` com `{usuario_id, tenant_id, cliente_id,
  finalidade=VISAO_360, timestamp, ip_hash (HMAC server-side), recurso
  JSONB (sem PII cru — só identificadores opacos)}`. Trigger PG
  anti-mutation aplica (F-A AC-FA-005-7). Resposta da view **bloqueia**
  se a gravação falhar (não há "sucesso silencioso").
- **AC-CLI-002-4**: filtro por tipo de evento (OS, Certificado, Fatura,
  NPS, Anexo) sob mesmo SLA; cada filtro registra acesso separadamente
  apenas se houver mudança de finalidade declarada.
- **AC-CLI-002-5**: `cliente_id` referenciado em qualquer endpoint que
  exiba dados do cliente **deve resolver via `INV-CLI-001` âncora de
  identidade canônica** — se o cliente referenciado foi mesclado, a
  resolução segue até o vencedor vivo (US-CLI-005).

## US-CLI-003 — Importação 1-clique (CSV/XLSX)

**Como** dono migrando de Cali/Bling, **quero** subir CSV/XLSX e ver
mapeamento automático, **para** não digitar 800 cadastros.

- **AC-CLI-003-1**: POST `/clientes/importar/preview/` aceita CSV/XLSX
  ≤ 10MB, retorna 10 primeiras linhas + mapeamento sugerido coluna→campo
  + warnings (documento inválido, e-mail malformado).
- **AC-CLI-003-2**: POST `/clientes/importar/executar/` roda em job
  Celery com `Idempotency-Key` obrigatório no header (`IDEMP-001`);
  retorna `import_id`; status via GET `/clientes/importar/{import_id}/`
  com {criados, atualizados, rejeitados, [linhas_erro]}.
- **AC-CLI-003-3**: bulk upsert acontece **dentro do `transaction.atomic`
  que adquire o `pg_advisory_xact_lock` por-tenant** (FECHADO
  SANEA-01) — duas importações concorrentes do mesmo tenant são
  serializadas; concorrentes de tenants distintos rodam em paralelo.
- **AC-CLI-003-4**: dedup em lote por `(tenant_id, tipo_pessoa,
  documento)` (`INV-024`); linha com documento inválido pelo algoritmo
  vai para rejeitados com motivo. Idempotência da retry: re-executar
  com mesma `Idempotency-Key` retorna o mesmo `import_id` sem reaplicar.
- **AC-CLI-003-5** (`SEC-CSV-001`): export de relatório de importação
  e qualquer export futuro de cliente passa por `sanitizar_celula_csv`
  — célula iniciando com `=`, `+`, `-`, `@`, `\t`, `\r` (ou com espaços
  antes desses) recebe apóstrofo prefixo. Teste cobre célula com
  espaços iniciais explicitamente.
- **AC-CLI-003-6**: salt usado em qualquer hash de PII durante a
  importação é HMAC com `PII_HASH_KEY` (F-A) — não derivável de
  `tenant_id` (FECHADO SANEA-02).

## US-CLI-004 — Bloqueio comercial (manual + automático)

**Como** financeiro/dono, **quero** marcar cliente como bloqueado
(manual) OU que sistema marque automaticamente após inadimplência > 90
dias, **para** impedir nova OS/orçamento/agenda sem quitar débito.

- **AC-CLI-004-1** (manual): POST `/clientes/{id}/bloquear/` exige
  papel `financeiro` ou `dono` (via `AuthorizationProvider.can` F-B),
  justificativa ≥ 30 chars. Cria `ClienteBloqueio`(cliente_id, motivo=
  `MANUAL`, justificativa, criado_por, criado_em). Publica
  `Cliente.Bloqueado`. Auditoria gravada.
- **AC-CLI-004-2**: GIVEN cliente bloqueado, WHEN
  `AuthorizationProvider.can("os.criar", {cliente_id})` ou similar para
  orçamento/agenda THEN retorna `denied` com `reason` ∈ {
  `cliente_bloqueado_manual`, `cliente_bloqueado_inadimplencia`}. F-B
  cobre o caminho; aqui só o predicate.
- **AC-CLI-004-3** (automático, ADR-0015 fluxo 4): job
  `job_inadimplencia_alertas` (Celery diário 02:00 BRT, com
  `Idempotency-Key`= `<data>-<tenant_id>`) consome
  `ContasReceber.TituloVencido` com `dias_vencido >= 90`. Cria
  `ClienteBloqueio` com `motivo=INADIMPLENCIA_90D`. Publica
  `Cliente.Bloqueado` + `ContasReceber.ClienteInadimplenteAlertaP1`.
- **AC-CLI-004-4**: régua progressiva D+30, D+60, D+89 dispara
  `ContasReceber.ReguaCobrancaDispachada` (escalada
  WhatsApp→email→ligação). Bloqueio só em D+90.
- **AC-CLI-004-5** (reativação): WHEN `ContasReceber.Pago` chega e
  cliente já não tem outros títulos com `dias_vencido >= 90`, THEN
  publica `Cliente.Desbloqueado(motivo="quitou_inadimplencia")` em ≤
  5min. Reativação manual exige mesma autoridade que o bloqueio manual.
- **AC-CLI-004-6**: cada transição grava em F-B `authz_decisions` com
  `causation_id` do título vencido (rastreabilidade).
- **AC-CLI-004-7** (`INV-INT-010`): emissor (job/endpoint) garante
  publicação ATÔMICA com gravação do `ClienteBloqueio` — outbox/
  transactional event ou commit-na-cadeia (F-A). Consumer fora desse
  contrato é falha.

## US-CLI-005 — Dedup manual (wizard lado a lado)

**Como** atendente, **quero** wizard que mostre 2 cadastros lado a
lado e me deixe escolher campo a campo qual valor manter, **para**
consolidar sem perder histórico.

- **AC-CLI-005-1**: GET `/clientes/{vencedor_id}/dedup/{perdedor_id}/`
  retorna comparação campo a campo de PF/PJ + contagem de OS,
  certificados, faturas, contatos atrelados a cada lado.
- **AC-CLI-005-2**: POST `/clientes/dedup/executar/` exige papel
  `atendente_senior` ou `dono`, payload `{vencedor_id, perdedor_id,
  campos_escolhidos: {campo: "vencedor"|"perdedor"}}`. Mesclar é
  ATÔMICO: dentro de `transaction.atomic` + advisory lock por tenant.
- **AC-CLI-005-3** (`INV-CLI-001`): identidade canônica.
  `Cliente.cliente_canonico_id` (UUIDField, default=self na criação,
  imutável após criar) aponta para o cliente vencedor da cadeia. Após
  mesclar:
  - perdedor.soft_deleted_at = now()
  - perdedor.cliente_canonico_id = vencedor.id
  - histórico (OS, certificados, faturas, contatos, NPS) **não migra
    FKs** — segue apontando para `perdedor.id`; a resolução acontece na
    leitura via `resolver_cliente_canonico(id)` (segue cadeia até
    encontrar vivo; cap 10 hops com fail-loud se circular).
  - certificados emitidos **antes** da mesclagem continuam citando
    o `cliente_id` original (auditoria de tradução pra CGCRE — `D-01`).
- **AC-CLI-005-4**: publica `Cliente.Dedup.Mesclado(vencedor_id,
  perdedor_id, causation_id)`. Payload **sem PII além do necessário**
  — nome/documento entram só como hash (`SANEA Onda 2` — formalizado).
- **AC-CLI-005-5**: re-dedup do perdedor (já mesclado) é rejeitado com
  400 — não há "cadeia de mesclagens manuais" a partir do nó morto.
- **AC-CLI-005-6**: evento `Cliente.Dedup.Mesclado` tem retenção 25
  anos (ISO 17025 §8.4) com classificação WORM — formalizado em
  retenção-matriz (GATE Onda 2).

---

## 3. Critérios de fechamento do Marco 1

Marco 1 `clientes` FECHADO via ritual quando **todos** abaixo verdes,
e o **loop dos 10 auditores Família 5 = zero CRÍTICO/ALTO/MÉDIO** nas
10 lentes:

1. Todos os AC-CLI-NNN-N acima OK ou rebaixados para TRACK com gate.
2. Suite verde no fluxo padrão (`pytest -p no:randomly`), cobertura ≥
   80% global e ≥ 90% nos arquivos `clientes/` (path crítico).
3. `_test-runner.sh` 130/130 (sem reabrir hooks).
4. `makemigrations --check` limpo; `migrate --database=migrator`
   from-scratch verde.
5. Drill `validar_f_a` 5/5 verde (não regredir F-A).
6. `INV-CLI-001` e `INV-CLI-002` registrados em `REGRAS-INEGOCIAVEIS.md`
   com hooks correspondentes (ou justificativa explícita pra ausência).
7. SANEA-04, 05, 07, 08, 09 — fechados na causa-raiz ou rebaixados
   com gate rastreado (não silenciado).
8. Onda 2 — médios resolvidos (PII em payload de mesclagem, retenção
   25a, performance timeline, refactor god-class).

---

## 4. Eventos do bus (publicados pelo módulo)

| Evento | Quando | Consumers | Retenção |
|--------|--------|-----------|----------|
| `Cliente.Criado` | POST `/clientes/` | crm, operação, financeiro | 5 anos (Receita) |
| `Cliente.Atualizado` | PATCH `/clientes/{id}/` | crm (re-segmentação) | 5 anos |
| `Cliente.Bloqueado` | bloqueio manual ou D+90 | operação, comercial, omnichannel | 5 anos |
| `Cliente.Desbloqueado` | desbloqueio manual ou `ContasReceber.Pago` | operação, comercial | 5 anos |
| `Cliente.Dedup.Mesclado` | POST `/clientes/dedup/executar/` | todos (re-resolução canônica) | **25 anos / WORM** (ISO 17025) |

Helper único de gravação `audit/event_helpers.py` (`SANEA-08`) — não
copiar o envelope 6×.

---

## 5. Premissas e dependências

- **F-A FECHADA via ritual** (multi-tenant + RLS fail-loud +
  audit-imutavel + PII HMAC versionado + hooks 130/130). `clientes`
  herda integralmente, não duplica.
- **F-B FECHADA via ritual** (auth + authz unificada + MFA real). US-CLI-002
  Visão 360° depende de `INV-013` registrar acesso ANTES de renderizar;
  US-CLI-004 depende de `AuthorizationProvider.can`.
- **ADR-0017 CNPJ alfanumérico**: VO `CNPJ` aceita `[A-Z0-9]{14}` com
  dígito verificador (vigência IN RFB 2.229/2024 — jul/2026).
- **ADR-0015 fluxo 4**: lifecycle de bloqueio por inadimplência depende
  de eventos do `financeiro/contas-receber` (módulo futuro). Marco 1
  estabelece o predicate + handler; emissor real vem depois.
- **ADR-0007**: agregado de domínio `Cliente` com `assert_invariant`
  (SANEA-07) — política LGPD num **único lar** chamada pelos boundaries.

---

## 6. Pontos para os 4 revisores (P2 — bloqueante até resposta)

### Para `tech-lead-saas-regulado`

- **P-CLI-T1**: identidade canônica via `cliente_canonico_id` com
  resolução encadeada na leitura (cap 10 hops) é aceitável, ou requer
  materialização (campo `cliente_resolvido_id` updated por job)?
  Custo/correção do trade-off.
- **P-CLI-T2**: outbox transacional para eventos do bus vs commit-na-
  cadeia F-A — ambos atendem `INV-INT-010`; qual é o caminho do Marco 1
  (formalizar pra Wave A inteira)?
- **P-CLI-T3**: god-class views.py (988 linhas hoje) — refactor por US
  é parte do fechamento do marco ou Onda 2 (não bloqueia)?

### Para `advogado-saas-regulado`

- **P-CLI-A1**: aceite LGPD com 3 bases legais (CONSENTIMENTO,
  EXECUCAO_CONTRATO, OBRIG_LEGAL) cobre todos os casos de cadastro de
  cliente PF/PJ? Falta algum (interesse legítimo, proteção do crédito)?
- **P-CLI-A2**: retenção do `Cliente.Dedup.Mesclado` em 25 anos /
  WORM — fundamentação ISO 17025 §8.4 + ANPD obrigam? Documento
  jurídico exato.
- **P-CLI-A3**: registro de `AcessoDadosCliente` **antes** de
  renderizar — falha de gravação deve bloquear a resposta da view (sem
  "sucesso silencioso"). Confirma o veredito legal.

### Para `consultor-rbc-iso17025`

- **P-CLI-R1**: certificados emitidos **antes** da mesclagem continuarem
  citando o `cliente_id` original (com resolução canônica na leitura) é
  conforme NIT-DICLA-005 / 8.4? Há requisito CGCRE que exija reemissão
  ou ata de mesclagem assinada?
- **P-CLI-R2**: cliente bloqueado por inadimplência continuar com
  certificados válidos (não há revogação automática) — aceitável?

### Para `corretora-seguros-saas`

- **P-CLI-S1**: ausência de hash chain dedicada em `AcessoDadosCliente`
  (só trigger anti-mutation) afeta segurabilidade RC profissional? F-A
  AC-FA-005-7 aceita; corretora confirma.
- **P-CLI-S2**: dedup com resolução encadeada (perdedor não é
  hard-deleted, FK histórica preserva ID original) é segurável em
  contrato — risco de processo "vocês perderam meu cadastro"?

---

## 7. O que NÃO redefiniu (herdado, não duplicar)

- Toda multi-tenant infra (middleware, RLS templates, contexts) é F-A.
- Todo authz/MFA/sessão é F-B.
- PII HMAC + sanitização + cadeia de auditoria + trigger anti-mutation
  são F-A.
- Hooks já cobrem `INV-TENANT-001..004`, `audit-immutability`,
  `migration-rls-check`, `tenant-id-validator` — não recriar.

Onde Marco 1 ADICIONA invariante novo (`INV-CLI-001`, `INV-CLI-002`,
`SEC-CSV-001`), P2 decide o hook correspondente; P4 implementa.
