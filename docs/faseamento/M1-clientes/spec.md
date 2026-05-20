---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
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
  PG; hash chain é gate Wave A se 1 de 4 gatilhos disparar (ANPD em
  incidente, CGCRE supervisão TOP-50, tenant farma RDC 658/2022, ou
  auditor cyber marcar gap material — RBC §D do P2).
- **NG-CLI-11**: tratamento de dados pessoais sensíveis (LGPD art. 11)
  — Aferê **NÃO** recebe em MVP-1. Campo "observação" do cadastro
  bloqueia entrada de regex de dado sensível (saúde, biometria, dados
  genéticos, opinião política, religião) com fail-loud no POST.
- **NG-CLI-12**: dados pessoais de criança e adolescente (LGPD art. 14)
  — Aferê **NÃO** trata em MVP-1. Validador de cliente PF rejeita
  cadastro com data de nascimento que aponte para idade < 18 anos.

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
  comportamento já em `csv_safety.py` após SANEA-03),
- `INV-013-A` (âncora de contagem diária imutável de
  `AcessoDadosCliente` por tenant — detecção barata de supressão de
  log; corretora-seguros-saas §A P-CLI-S1).

Todos exigem cobertura `tests/regressao/inv_cli_*.py` happy + unhappy
ANTES do fechamento — pré-condição de segurabilidade (ADR-0019 +
AUDIT-07 R-CLI-01).

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
- **AC-CLI-001-4** (advogado-saas-regulado §A P-CLI-A1 + §D): aceite
  LGPD é OBRIGATÓRIO no POST direto. Sem campos abaixo o POST retorna
  400 e a mensagem cita o campo faltante. Imutáveis após criar
  (LGPD art. 8 §6 — prova).
  - `aceite_lgpd_em` (timestamp UTC)
  - `aceite_lgpd_base_legal` (enum — 5 valores):
    `CONSENTIMENTO` (LGPD art. 7º I),
    `EXECUCAO_CONTRATO` (art. 7º V),
    `OBRIG_LEGAL` (art. 7º II),
    `LEGITIMO_INTERESSE` (art. 7º IX — exige `lia_id` apontando teste
    de balanceamento vigente do tenant),
    `PROTECAO_CREDITO` (art. 7º X — restrito a operações de
    bloqueio/cobrança).
  - `aceite_lgpd_declaracao_id` (FK `DeclaracaoLGPD` vigente do
    controlador correspondente ao `tipo_titular`: tenant publica
    declaração para `CLIENTE_FINAL_DO_TENANT`; Aferê publica
    declaração para `USUARIO_OPERADOR`).
  - `aceite_lgpd_origem` (enum: `CADASTRO_DIRETO` |
    `IMPORTACAO_LEGADA` | `MIGRACAO_SISTEMA_ANTERIOR`).
    `IMPORTACAO_LEGADA` só aceita base `EXECUCAO_CONTRATO` ou
    `OBRIG_LEGAL` (nunca `CONSENTIMENTO`).
- **AC-CLI-001-7** (consultor-rbc-iso17025 §B item 1): alteração de
  `nome` (PF) ou `razao_social`/`nome_fantasia` (PJ) em cliente ativo
  grava `ClienteIdentidadeHistorico(cliente_id, campo, valor_anterior,
  valor_novo, data_efetivacao, evidencia_documental_id, criado_por)` —
  trilha de rastreabilidade ISO/IEC 17025 §7.8.2.1 (b) + §8.4
  preservada por 25 anos. Campo `evidencia_documental_id` opcional
  para alteração simples; obrigatório se alteração coincide com `M&A`
  (ver AC-CLI-005-3).
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
  resolução segue até o vencedor vivo (US-CLI-005). Materialização
  preguiçosa: se hops > 1, a leitura grava
  `cliente_resolvido_id` na própria transação via UPDATE (tech-lead
  §A P-CLI-T1) — próxima leitura é O(1).
- **AC-CLI-002-6** (tech-lead §B item 2 + corretora §B item 1):
  circuit breaker observado para gravação em `AcessoDadosCliente`.
  Falha de gravação ≥ 0.1% das tentativas em janela de 5min dispara
  alerta P1 + métrica `acessos_dados_cliente.gravacao_falhada_total{
  tenant_id}` em sink imutável. Endpoint NÃO degrada para "permitir
  sem registro" — fail-loud preservado (LGPD art. 37); o alerta serve
  pra time operacional intervir antes que a indisponibilidade
  prolongada vire risco de continuidade.
- **AC-CLI-002-7** (`INV-013-A`, corretora §A P-CLI-S1): job daily
  conta `AcessoDadosCliente` por tenant e publica em métrica
  imutável (WORM B2 quando GATE-1 ativo; até lá, evento na cadeia
  sistema). Gap na sequência diária (dia X+1 < X) dispara alerta P1
  — supressão de log de acesso a PII detectável sem hash chain
  dedicada.

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
- **AC-CLI-003-7** (advogado §D + tech-lead §C item 3): linha CSV sem
  `aceite_lgpd_em` explícito é processada APENAS se
  `aceite_lgpd_origem=IMPORTACAO_LEGADA` e
  `aceite_lgpd_base_legal ∈ {EXECUCAO_CONTRATO, OBRIG_LEGAL}` foram
  passados no payload de execução (defaults do tenant na chamada do
  importador). Cadastro entra em estado **restrito**
  (`pii_regularizacao_em IS NULL` flag = pending): sem campanhas,
  sem compartilhamento com terceiros até regularização. Dashboard
  agrega esses cadastros para o tenant regularizar.

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
  publicação ATÔMICA com gravação do `ClienteBloqueio` — **outbox
  transacional** (tech-lead §A P-CLI-T2 DECIDIDO): tabela `bus_outbox`
  local ao schema tenant, INSERT no mesmo `transaction.atomic` que a
  gravação do bloqueio + `registrar_em_cadeia`; worker dedicado faz
  publish + delete. Sem caminho secundário "commit-na-cadeia".
- **AC-CLI-004-8** (consultor-rbc §A P-CLI-R2 + §E): bloqueio
  comercial **NÃO afeta** validade técnica de certificado já emitido.
  Recall de certificado segue exclusivamente fluxo NIT-DICLA-030 §5.7
  + ISO/IEC 17025 §7.10 (trabalho não conforme), governado pelo módulo
  `operacao/certificados` (Marco futuro) — proibido derivar do estado
  `bloqueado` em qualquer consumer.
- **AC-CLI-004-9** (consultor-rbc §E item 1): bloqueio dispara
  cancelamento automático de **agendamentos futuros não-iniciados** do
  cliente; consumer `operacao/agenda` recebe `Cliente.Bloqueado` e
  publica `Agenda.CancelamentoAutomatico(motivo="bloqueio",
  agenda_id)`. Reagendamento para "quando regularizar" responsabilidade
  do módulo `operacao/agenda`.
- **AC-CLI-004-10** (consultor-rbc §E item 2): calibração **em
  execução** (item já recebido no laboratório) é **concluída** mesmo
  com cliente bloqueado — ISO/IEC 17025 §7.1.1 + §7.8.1 (dever
  técnico de finalizar e emitir relatório). Consumer
  `operacao/certificados` consulta predicate
  `cliente.bloqueado_para_entrega` e roteia para fluxo de
  **retenção física** (CC art. 644) sem afetar validade técnica.
- **AC-CLI-004-11** (tech-lead §B item 3): worker que processa
  `bus_outbox` opera em contexto multi-tenant via helper único
  `processar_outbox_em_contexto_tenant(linha)` morando na **F-A**
  (não em `clientes/`) — assegura `INV-TENANT-001..004` no caminho do
  worker; consumer nunca recebe mensagem de tenant diferente do
  contexto ativo.

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
- **AC-CLI-005-3** (`INV-CLI-001`, consultor-rbc §A P-CLI-R1 + §C):
  identidade canônica. `Cliente.cliente_canonico_id` (UUIDField,
  default=self na criação, **imutável runtime via trigger PG** — ver
  AC-CLI-005-7) aponta para o cliente vencedor da cadeia. Após mesclar:
  - perdedor.soft_deleted_at = now()
  - perdedor.cliente_canonico_id = vencedor.id (única transição
    válida — trigger valida)
  - histórico (OS, certificados, faturas, contatos, NPS) **não migra
    FKs** — segue apontando para `perdedor.id`; a resolução acontece na
    leitura via `resolver_cliente_canonico(id)` (segue cadeia com cap
    10 hops; fail-loud + alerta P1 + métrica `dedup.profundidade` se
    ≥ 7 — corretora §A P-CLI-S2).
  - certificados emitidos **antes** da mesclagem mantêm o snapshot
    de identidade {`cliente_id`, `nome`, `documento`,
    `endereco_completo`, `razao_social_se_PJ`} congelado no momento
    da emissão (no schema do módulo `operacao/certificados`, Marco
    futuro — aqui só a INTERFACE de leitura `cliente_snapshot_jsonb`
    fica acordada).
  - `Cliente.Dedup.Mesclado` no evento carrega payload `{vencedor_id,
    perdedor_id, documentos_hash_ambos, justificativa, autorizador_id,
    evidencia_documental_id_opcional, tipo_mesclagem}` —
    rastreabilidade ISO/IEC 17025 §7.8.2.1 (b) + §8.4.
- **AC-CLI-005-3b** (consultor-rbc §C): campo
  `tipo_mesclagem ∈ {DUPLICATA_OPERACIONAL, M&A_SOCIETARIO}` no POST
  `/clientes/dedup/executar/`. Se `M&A_SOCIETARIO`,
  `evidencia_documental_id` (FK pra anexo: contrato social
  consolidado, ata JC, procuração) é **obrigatório** — 400 sem anexo.
  Defesa cível (CC art. 1.116) + supervisão CGCRE robusta.
- **AC-CLI-005-4**: publica `Cliente.Dedup.Mesclado(vencedor_id,
  perdedor_id, causation_id)`. Payload **sem PII além do necessário**
  — nome/documento entram só como hash (`SANEA Onda 2` — formalizado).
- **AC-CLI-005-5**: re-dedup do perdedor (já mesclado) é rejeitado com
  400 — não há "cadeia de mesclagens manuais" a partir do nó morto.
- **AC-CLI-005-6** (advogado §A P-CLI-A2): evento
  `Cliente.Dedup.Mesclado` tem retenção 25 anos com classificação
  WORM — fundamentação composta (a) ISO/IEC 17025:2017 cl. 8.4.2 +
  NIT-DICLA-026 (registros técnicos), (b) LGPD art. 16 III
  (conservação por obrigação legal/regulatória), (c) LGPD art. 16 II
  (exercício regular de direitos em processo). Payload sanitizado:
  só UUIDs + hashes HMAC; nome/documento crus **proibidos** no
  evento.
- **AC-CLI-005-7** (tech-lead §B item 1, `INV-CLI-001`):
  imutabilidade runtime de `cliente_canonico_id` via **trigger PG
  BEFORE UPDATE** em `cliente`. Trigger valida:
  - valor anterior era `id` próprio (criação default) OR já apontava
    para outro cliente vivo (re-mesclagem proibida — AC-CLI-005-5);
  - novo valor referencia cliente vivo do **mesmo tenant**
    (`soft_deleted_at IS NULL` AND `tenant_id` igual);
  - allow só via `# canonico-imutavel: skip -- <razão ≥10 chars>` em
    migration de manutenção declarada.
  Hook `cliente-canonico-imutavel.sh` cobre tempo de migration;
  trigger cobre tempo de runtime — defesa em profundidade.

## US-CLI-006 — Direitos do titular, revogação e incidentes (LGPD)

**Como** titular dos dados (cliente final do tenant), **quero** rotas
estáveis para exercer os direitos garantidos por LGPD art. 18 + revogar
consentimento (art. 8º §5º), e **quero** que incidentes sejam
comunicados, **para** que dogfooding e o 1º tenant externo não violem
obrigações imediatas a partir do primeiro cadastro real.

> Justificativa (advogado §B): sem essas rotas, dogfooding com PII real
> de cliente final já configura violação de art. 18. Não é Marco 2 —
> é pré-condição mínima de processar PII real.

- **AC-CLI-006-1** (LGPD art. 18 — direitos do titular): endpoints
  estáveis `POST /clientes/{id}/direitos-titular/{tipo}/` com `tipo` ∈
  {`confirmacao`, `acesso`, `correcao`, `anonimizacao`, `portabilidade`,
  `eliminacao`, `informacao_compartilhamento`, `revogacao_consentimento`}.
  SLA 15 dias úteis (Res. CD/ANPD nº 2/2022 art. 11), prorrogável por
  + 15 dias mediante justificativa publicada ao titular.
- **AC-CLI-006-2** (revogação — LGPD art. 8º §5º): endpoint
  `revogacao_consentimento` é **gratuito e imediato** —
  efeito ≤ 1 min; cliente migra para estado `consentimento_revogado_em`,
  bases CONSENTIMENTO viram inaplicáveis; tratamentos subsequentes só se
  outra base legal aplicar (e o tenant precisa registrar a mudança).
- **AC-CLI-006-3** (advogado §E, matriz eliminação vs anonimização):
  `tipo=eliminacao` aplica matriz declarada:
  | Categoria | Conflito de prazo | Ação |
  |-----------|-------------------|------|
  | Cadastro sem NF/cert atrelado | nenhum | **Eliminação efetiva** (DELETE + cascade preservando audit chain) |
  | Cadastro com NF emitida | Receita 5a (CTN 173) | **Anonimização em lugar** (nome="Cliente anonimizado #N", documento=hash HMAC, e-mail/telefone NULL); NF em B2 WORM preservada por 5a com `cliente_id_hash` |
  | Cadastro com certificado ISO | ISO §8.4 ~25a | **Anonimização parcial diferida** — signatário humano preservado (ISO cl. 6.2); CPF/CNPJ vira hash; razão social mantida (rastreabilidade) |
  | Aceite LGPD + audit chain | Audit ~10a | **Anonimização do conteúdo PII no payload** preservando estrutura (timestamps, ações, IDs opacos); cadeia íntegra (trigger F-A intacto) |
  Resposta sempre `200` com `acao_aplicada ∈ {ELIMINACAO, ANONIMIZACAO}`
  e base legal citada (LGPD art. 16 I/II/III aplicável).
- **AC-CLI-006-4** (LGPD art. 11 + NG-CLI-11): rota de cadastro/edição
  aplica regex anti-PII-sensível em campos livres (`observacao`,
  `descricao_adicional`); match → 400 com mensagem "dado sensível não
  é tratado no Aferê MVP-1".
- **AC-CLI-006-5** (LGPD art. 14 + NG-CLI-12): cadastro PF com
  `data_nascimento` apontando para < 18 anos → 400 com mensagem
  "dados de criança/adolescente não são tratados no Aferê MVP-1".
- **AC-CLI-006-6** (Res. ANPD 15/2024 — incidente): evento
  `Cliente.PII.IncidenteDetectado(tenant_id, descricao_curta,
  categoria_pii_afetada, qt_titulares_estimada, causation_id)` no bus
  alimenta módulo de governança. SLA comunicação ANPD 3 dias úteis
  (módulo de governança opera o canal externo — aqui só o evento).
- **AC-CLI-006-7** (registro operações — LGPD art. 37): além de
  `AcessoDadosCliente` (leitura, AC-CLI-002-3), grava
  `OperacaoTratamentoCliente(tenant_id, cliente_id, finalidade ∈ {
  CADASTRO, EDICAO, EXPORT, COMPARTILHAMENTO_INTERMODULAR},
  usuario_id, timestamp)` — fonte para `art. 37` quando ANPD pedir
  inventário de tratamentos.

---

## 3. Critérios de fechamento do Marco 1

Marco 1 `clientes` FECHADO via ritual quando **todos** abaixo verdes,
e o **loop dos 10 auditores Família 5 = zero CRÍTICO/ALTO/MÉDIO** nas
10 lentes:

1. Todos os AC-CLI-NNN-N acima OK ou rebaixados para TRACK com gate.
2. Suite verde no fluxo padrão (`pytest -p no:randomly`), cobertura ≥
   80% global e ≥ 90% nos arquivos `clientes/` (path crítico).
3. `_test-runner.sh` 130+ casos (sem reabrir hooks).
4. `makemigrations --check` limpo; `migrate --database=migrator`
   from-scratch verde.
5. Drill `validar_f_a` 5/5 verde (não regredir F-A) +
   `validar_m1_clientes` (a criar em P4) com cenário concorrente
   de cadastro/importação/dedup multi-tenant.
6. `INV-CLI-001`, `INV-CLI-002`, `SEC-CSV-001` e `INV-013-A`
   registrados em `REGRAS-INEGOCIAVEIS.md` com hooks correspondentes
   (lista em §"Hooks novos / atualizações" do `plan.md`).
7. SANEA-04 (confirmado FECHADO via F-A FA-C1), SANEA-05 (resolvido
   em US-CLI-005), SANEA-07 (resolvido em §"Decisão arquitetural"
   do plan), SANEA-08 (resolvido via `audit/event_helpers.py`),
   SANEA-09 (resolvido via §9 + suite anti-regressão).
8. Onda 2 — médios resolvidos: PII em payload de mesclagem
   (sanitizado em AC-CLI-005-3 — só UUIDs/hashes); retenção 25a
   (AC-CLI-005-6 + GATE-CLI-1 documento `retencao-matriz.md`
   promovido a stable); performance timeline (AC-CLI-002-2 SLA +
   materialização preguiçosa); refactor god-class views.py
   (decidido P-CLI-T3 — parte do Marco).
9. **Suite anti-regressão** `tests/regressao/inv_cli_*.py` cobre cada
   um dos 4 INVs novos com **happy + unhappy** (corretora §D + ADR-0019
   Pilar 2). Sem isso, AUDIT-07 R-CLI-01 propaga.
10. Property-based test de `resolver_cliente_canonico` com ≥ 1000
    cadeias geradas validando idempotência + ausência de ciclo +
    cap 10 (corretora §D).
11. Hooks novos cravados e em `_test-runner.sh`:
    `lgpd-policy-unica.sh`, `cliente-canonico-imutavel.sh`,
    `csv-safety-import.sh`, `event-helper-unico.sh`.

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

## 6. Decisões dos 4 revisores (P2 concluído 2026-05-19)

> Cada P-CLI-XN abaixo recebeu parecer dos 4 subagentes humano-substitutos.
> Os ajustes deles foram absorvidos nas seções US-CLI-001..006 e nos
> critérios §3 acima. Esta seção é o registro auditável das decisões.

### `tech-lead-saas-regulado` — AJUSTADOS / aceitos

- **P-CLI-T1 AJUSTADO** → resolução encadeada com cap=10 +
  **materialização preguiçosa** (UPDATE em leitura se hops > 1).
  Cravado em AC-CLI-002-5. Job batch só se V2 mostrar p99 > 200ms.
- **P-CLI-T2 AJUSTADO** → **outbox transacional como padrão único
  Wave A**; sem caminho "commit-na-cadeia" secundário (cinto-e-
  suspensório vira ambiguidade). Cravado em AC-CLI-004-7.
- **P-CLI-T3 ACEITE** → refactor views.py em 5 arquivos por US é
  parte do Marco 1, não Onda 2. Cravado em §3 item 8.
- Bloqueantes adicionais absorvidos: AC-CLI-005-7 (trigger PG runtime
  + hook), AC-CLI-002-6 (circuit breaker), AC-CLI-004-11 (helper
  outbox em contexto na F-A), e §3 item 5 (drill multi-tenant).
- Helper único `audit/event_helpers.py` cravado no `plan.md` §"Decisão
  arquitetural geral" + hook `event-helper-unico.sh` no §3 item 11.

### `advogado-saas-regulado` — AJUSTADOS / aceitos

- **P-CLI-A1 AJUSTADO** → enum sobe para 5 bases legais
  (`CONSENTIMENTO`, `EXECUCAO_CONTRATO`, `OBRIG_LEGAL`,
  `LEGITIMO_INTERESSE` com `lia_id`, `PROTECAO_CREDITO`).
  Cravado em AC-CLI-001-4 + AC-CLI-003-7.
- **P-CLI-A2 ACEITE com fundamentação reforçada** → ISO §8.4.2 +
  NIT-DICLA-026 + LGPD art. 16 II/III. Cravado em AC-CLI-005-6.
- **P-CLI-A3 ACEITE** → fail-loud em `AcessoDadosCliente`,
  fundamentado em LGPD art. 37 + art. 6º X + Res. CD/ANPD nº 2/2022.
- Lacunas absorvidas (US-CLI-006 nova): direitos do titular (AC-006-1),
  revogação (AC-006-2), eliminação vs anonimização (AC-006-3),
  dados sensíveis (AC-006-4 + NG-CLI-11), criança/adolescente
  (AC-006-5 + NG-CLI-12), incidente ANPD (AC-006-6), registro de
  operações (AC-006-7).
- Recomendação operacional: contrato com advogado humano licenciado
  ANTES do 1º tenant externo pago — não bloqueia Marco 1 técnico.

### `consultor-rbc-iso17025` — AJUSTADOS / aceitos

- **P-CLI-R1 AJUSTADO** → snapshot de identidade no certificado
  emitido + `cliente_canonico_id` resolvido na leitura + payload
  rastreável em `Cliente.Dedup.Mesclado`. Cravado em AC-CLI-005-3 +
  AC-CLI-005-3b (`tipo_mesclagem`).
- **P-CLI-R2 ACEITE com ressalva** → bloqueio comercial ≠ recall
  técnico. Cravado em AC-CLI-004-8.
- Bloqueantes absorvidos: AC-CLI-001-7 (`ClienteIdentidadeHistorico`
  em alteração de razão social), AC-CLI-004-9 (cancelar agenda),
  AC-CLI-004-10 (calibração em execução conclui).
- Hash chain dedicada de `AcessoDadosCliente` = gate Wave A se 1 de 4
  gatilhos disparar (NG-CLI-10 detalha).
- Recomendação: contratar consultor RBC humano credenciado antes da
  1ª supervisão CGCRE formal — este parecer cobre ~80% do dossiê.

### `corretora-seguros-saas` — AJUSTADOS / aceitos

- **P-CLI-S1 AJUSTADO** → adicionar `INV-013-A` (contagem diária
  imutável de `AcessoDadosCliente`) como âncora barata de detecção
  de supressão. Cravado em AC-CLI-002-7.
- **P-CLI-S2 ACEITE com 2 ajustes** → alerta P1 em ciclo +
  métrica `dedup.profundidade` (alerta se ≥ 7). Cravado em
  AC-CLI-005-3 bullet 3.
- ADR-0019 cláusula segurabilidade absorvida: §3 item 9 exige suite
  anti-regressão dos 4 INVs novos + §3 item 10 property-based test do
  resolver canônico.
- Checklist 14 itens pré-1º tenant externo (BIA, DPA, retenção,
  incident response, controles compensatórios) é gate operacional
  rastreado fora do Marco 1 técnico — anotado em retenção-matriz.

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
