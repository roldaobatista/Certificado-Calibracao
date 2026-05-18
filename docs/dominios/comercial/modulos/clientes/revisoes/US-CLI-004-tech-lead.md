---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-004
plano_revisado: docs/dominios/comercial/modulos/clientes/planos/US-CLI-004.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-CLI-004 (Bloqueio cliente — manual + automatico)

## Resumo executivo

Plano captou bem o escopo realista de Marco 1: implementar 100% do lado manual + cravar contratos (utilitaria, evento, audit, job stub) para os ACs automaticos que dependem de modulos inexistentes (`financeiro/contas-receber`, `comunicacao-omnichannel`, `agenda`). Direcao correta. Mas o plano tem **7 ressalvas** que precisam ser endereçadas antes de `/implement` — 3 sao bloqueantes (modelagem flat vs historica, integracao errada com `AuthorizationProvider`, idempotencia indefinida) e 4 sao patterns que custam zero agora e doem em Wave A (job stub via management command vs Procrastinate ja instalado, payload do evento, semantica do `causation_id`, defesa em profundidade no `cliente_bloqueado_para_acao`).

## Veredito

**APROVADO COM RESSALVAS** (7 ressalvas — bloqueiam `/implement` ate endereçadas no plano; nenhuma exige reabertura da Story).

---

## Ressalvas (ordem por gravidade)

### 1. CRITICA — Modelagem: flat no Cliente perde historico de bloqueios; tabela `cliente_bloqueios` 1:N e o pattern correto

**Problema:** `T-CLI-019` propoe campos flat no proprio Cliente (`bloqueado`, `bloqueio_motivo`, `bloqueio_justificativa`, `bloqueio_em`, `bloqueio_por_usuario_id`). Releitura do AC-CLI-004-6 (reativacao) + AC-CLI-004-3 (re-bloqueio quando outra fatura vence) revela que **um cliente pode passar por N ciclos bloqueio→desbloqueio→bloqueio** ao longo da vida. Modelagem flat **sobrescreve** o estado anterior — historico evapora. Isso quebra 3 cenarios reais:

1. **Auditoria CGCRE / LGPD art. 9** — "porque esse cliente foi bloqueado e desbloqueado 4 vezes em 2026?" Sem historico, resposta vira "consultar audit_trail" (custoso, fora do dominio).
2. **Disputa juridica** — cliente alega "fui bloqueado injustamente em janeiro, perdi negocio". Se em marco ele foi desbloqueado e re-bloqueado em julho, o estado atual nao serve de prova de janeiro.
3. **Metricas de produto** (BI / ADR-0011) — "% clientes recidivos em inadimplencia" exige ler historico, nao o estado.

`audit_trail` resolve forense, **nao resolve consulta de negocio** — dimensao `dim_cliente_bloqueio` no warehouse precisa de fonte estruturada.

**Correcao exigida:**
1. Tabela nova `cliente_bloqueios` (1:N com Cliente):
   ```
   id (UUID PK)
   cliente_id (FK Cliente)
   tenant_id (UUID, REPLICA pra RLS — INV-TENANT-001)
   motivo (enum: manual, inadimplencia_90d) NOT NULL
   justificativa (text, >= 30 chars quando motivo=manual)
   iniciado_em (datetime) NOT NULL
   iniciado_por_usuario_id (UUID, NULL quando motivo=inadimplencia_90d — job system)
   encerrado_em (datetime, NULL = bloqueio ativo)
   encerrado_por_usuario_id (UUID, NULL quando reativacao automatica)
   encerrado_motivo (enum: desbloqueio_manual, quitou_inadimplencia, NULL quando ativo)
   causation_id (UUID, NULL quando manual)
   criado_em / atualizado_em
   ```
2. **UNIQUE INDEX parcial** garantindo no maximo 1 ativo por cliente:
   ```sql
   CREATE UNIQUE INDEX uq_cliente_bloqueio_ativo
     ON cliente_bloqueios (tenant_id, cliente_id)
     WHERE encerrado_em IS NULL;
   ```
   Isso e o equivalente do `uq_cliente_doc_ativo` aplicado em US-CLI-005 — pattern consistente.
3. Cliente NAO ganha `bloqueado: bool` denormalizado — a utilitaria (ver ressalva 4) consulta `cliente_bloqueios` direto. Tentar manter flag denormalizada gera o N+1 problem da ADR-0015 "Alternativa 3 — REJEITADA" e exige trigger pra sincronizar (debito que nao queremos).
4. RLS policy para `cliente_bloqueios` na mesma migration (hook `migration-rls-check` bloqueia senao) — happy path: `tenant_id` igual ao contexto; unhappy path: cross-tenant retorna 0 linhas.

### 2. CRITICA — Utilitaria `cliente_bloqueado_para_acao` repete logica do `AuthorizationProvider`; certo e extender o Provider

**Problema:** `T-CLI-022` propoe uma funcao stand-alone `cliente_bloqueado_para_acao(cliente_id, action) -> Decisao` que OS/orcamentos/agenda chamariam diretamente. Isso fragmenta o ponto de decisao de autorizacao em **dois caminhos paralelos**:
- Caminho 1: `AuthorizationProvider.can("os.criar", user_id=X)` — checa matriz `authz_perfil_acao`.
- Caminho 2: `cliente_bloqueado_para_acao(cliente_id, "os.criar")` — checa `cliente_bloqueados`.

Cada modulo consumidor (OS, orcamentos, agenda) tem que se lembrar de chamar OS DOIS. Esquecimento = bug de seguranca (`INV-INT-010` quebrada). Hook `authz-check` so pega o primeiro caminho — o segundo passa silencioso.

**ADR-0012** (Autorizacao unificada) cravou que `AuthorizationProvider.can()` e o **unico ponto** de decisao. ADR-0015 fluxo 4 (linha 250 do ADR) tambem explicita: `AuthorizationProvider.can("os.criar", {"cliente_id": X})` — predicado ABAC adicionado AO PROVIDER, nao funcao paralela.

**Correcao exigida:**
1. `cliente_bloqueado_para_acao` **morre como API publica**. Vira detalhe interno de implementacao.
2. `AuthorizationProvider.can()` ganha parametro `resource: dict | None = None` (se ja nao tem; conferir no `django_provider.py:74`). Quando `resource={"cliente_id": X}` chega, Provider consulta um registry de predicados ABAC e nega se algum predicado retorna `denied`.
3. Predicado `cliente_nao_bloqueado` registrado em `src/infrastructure/authz/predicates.py` (criar arquivo agora — estabelece pattern). Predicado consulta `cliente_bloqueios` (WHERE encerrado_em IS NULL) e retorna `Decisao(allowed=False, reason="cliente_bloqueado_inadimplencia"|"cliente_bloqueado_manual")` conforme `motivo` do bloqueio ativo.
4. Predicado e auto-aplicado para actions com prefixo configuravel (lista cravada agora: `os.criar`, `orcamento.criar`, `agenda.alocar`). Wave A adiciona mais via migration que **estende a lista**, nao re-inventa o predicado.
5. Hook `authz-check` ja sera o unico guardiao — fragmentacao evitada.

Sem isso, em Wave A teremos 3 modulos consumidores chamando 2 funcoes diferentes para "posso fazer X com cliente Y?" — anti-pattern de manutencao.

### 3. CRITICA — Idempotencia indefinida: bloquear cliente ja bloqueado tem 3 semanticas possiveis; o plano nao escolhe

**Problema:** `T-CLI-025` lista `test_bloqueio_eh_idempotente` mas o plano nao especifica QUAL idempotencia:

| Opcao | Comportamento | Risco |
|---|---|---|
| A: No-op | Bloqueio ja existente persiste; novo POST retorna 200 com bloqueio atual | Operador pensa que "atualizou" justificativa e nao atualizou |
| B: Sobrescreve | Justificativa antiga apagada; nova grava | Perde rastreabilidade — quem bloqueou em janeiro? por que? |
| C: 409 Conflict | Erro explicito | Operador precisa desbloquear+bloquear pra trocar motivo (2 cliques) |

Soma com a ressalva 1: se modelagem virar 1:N, idempotencia ganha 4a opcao — **bloqueio ativo permanece, justificativa NAO muda, retorna 200 com `bloqueio_id` do ativo** (idempotencia transparente, sem sobrescrever historia).

**Correcao exigida:**
1. Decidir formalmente: **Opcao D** (com modelagem 1:N).
   - POST `/clientes/{id}/bloquear/` quando ja existe bloqueio ativo → 200 OK + payload com `bloqueio_id` do ativo + flag `ja_estava_bloqueado: true` + audit `cliente.bloqueio_tentativa_noop` (action separada — discrimina tentativa real de duplicar).
   - Justificativa nova NAO sobrescreve a antiga (ressalva 1.3).
   - Para trocar motivo: desbloquear + bloquear de novo (2 linhas em `cliente_bloqueios` — historico preservado).
2. Renomear o teste para `test_bloqueio_idempotente_retorna_noop_sem_sobrescrever_motivo`.
3. Adicionar teste explicito: `test_bloqueio_de_cliente_ja_bloqueado_nao_dispara_evento_duplicado` (evento `Cliente.Bloqueado` so publica na transicao **sem ativo → com ativo**; replay nao re-publica — economiza ruido pro bus).

### 4. ALTA — `causation_id` semantica: nullable UUID com convencao de "aponta pra que" precisa ser cravada agora

**Problema:** plano (T-CLI-024) menciona "causation_id (UUID opcional ligando ao titulo vencido)". Quando ContasReceber existir, `causation_id` aponta pra `TituloVencido.id`. Mas o plano nao formaliza:
1. **Que outras causations** sao validas hoje (manual = NULL; importacao em batch futuro = `ImportacaoBatch.id`; politica nova = `PoliticaInadimplencia.id`). Sem enum/conveccao, em Wave A cada agente vai inventar.
2. **FK ou apenas UUID solto?** FK exige tabela existente (impossivel agora pra TituloVencido). UUID solto exige documentar contrato de "qual resource e".

**Correcao exigida:**
1. Acrescentar 2 campos em `cliente_bloqueios` (e nao 1):
   - `causation_id: UUID NULL` (so o UUID; nao FK ate tabela existir; Wave A pode adicionar FK via migration sem dor)
   - `causation_type: VARCHAR(40) NULL` (enum cravado agora: `titulo_vencido`, `importacao_batch`, `politica_inadimplencia`. NULL quando motivo=manual.)
2. Documentar regra no plano: "`causation_id IS NULL` se e so se `motivo='manual'` (CHECK CONSTRAINT). `motivo='inadimplencia_90d'` exige `causation_type='titulo_vencido'` + `causation_id NOT NULL` — Wave A garante quando job real publicar."
3. Mesmo padrao replica em `auditoria.payload` — esse e o **mesmo `causation_id`** propagado, nao um campo novo:
   ```json
   {"causation": {"type": "titulo_vencido", "id": "<uuid>"}}
   ```
4. Teste no Marco 1 (job stub): `test_job_stub_publica_audit_com_causation_titulo_vencido_uuid_simulado` (stub gera UUID fake — quando Wave A trocar pelo real, o teste valida que o contrato esta preservado).

### 5. ALTA — Job stub via `management command` vs Procrastinate ja instalado: usar Procrastinate desde ja, nao adiar

**Problema:** plano (`Non-goals` linha 50) afirma: "Job Celery real (depende de ContasReceber). Implementar como management command stub." 2 problemas:

1. **Celery NAO esta no projeto** (`pyproject.toml` linha 16): `procrastinate = "^2.9.0"` esta. AGENTS.md §2 e claro: "procrastinate (NAO pg-boss — esse e Node). Celery secundario se necessario." Plano repetiu o ADR-0015 que ainda fala em Celery (linha 212 do ADR — `@celery.task`) porque ADR foi escrito antes da decisao stack. AGENTS.md vence o ADR-0015 nesse ponto.
2. **Procrastinate ja vem instalado** mas nao configurado em `config/`. Se o job stub for management command, em Wave A vamos ter dois ciclos de retrabalho: (a) criar management command, (b) descartar pra Procrastinate, (c) configurar Procrastinate beat. Memoria `nao-construir-codigo-descartavel` veta isso.

**Correcao exigida:**
1. Configurar Procrastinate como parte deste plano (Marco 1 do US-CLI-004):
   - `config/procrastinate.py` (app + Django connector + retry policy)
   - Migration Procrastinate aplicada (`procrastinate.contrib.django` ja gera)
   - Worker no `docker-compose.yml` (service `procrastinate-worker`)
2. Definir job `job_inadimplencia_alertas` como `@procrastinate.app.task(queue="cobranca", periodic="0 2 * * *")` **ja na forma final**.
3. No Marco 1, o job consulta um `InadimplenciaSource` (Protocol em `src/domain/comercial/clientes/inadimplencia.py`) — implementacao concreta retorna lista vazia (sem TituloVencido). Wave A cria o adapter real em `src/infrastructure/financeiro/contas_receber/inadimplencia_source.py`. Pattern Protocol+adapter (ADR-0007 §2) — mesmo padrao do `ClienteRepository` em US-CLI-005.
4. Teste no Marco 1: `test_job_inadimplencia_com_source_vazio_nao_bloqueia_ninguem` + `test_job_inadimplencia_com_source_fake_bloqueia_corretamente` (source fake retorna 1 cliente com 95d → assert que `cliente_bloqueios` ganha 1 linha + audit grava + nao re-bloqueia em re-execucao por idempotencia ressalva 3).

Custo agora: 1 dia adicional. Custo se adiar: 3 dias em Wave A + risco de descobrir incompatibilidade Procrastinate↔Django 5 tarde demais.

### 6. MEDIA — Contrato de evento `Cliente.Bloqueado` / `Cliente.Desbloqueado`: payload sem PII + nomes lowercase + idempotencia bus

**Problema:** plano cita `Cliente.Bloqueado(motivo="manual", justificativa=...)` mas:
1. **`justificativa` pode conter PII** (operador escreve "cliente Joao Silva CPF 123 deve R$ 5k") — o mesmo problema endereçado em US-CLI-005 ressalva R2 (advogado). Plano nao filtra.
2. **`Cliente.Bloqueado` em PascalCase** — repete o erro endereçado em US-CLI-001/005 (convencao do projeto: `cliente.bloqueado` lowercase + dot.notation).
3. **Sem `event_id`** — quando Wave A trocar audit-trail-as-bus por bus real, idempotencia exige `event_id` UNIQUE. Sem definir agora, consumers vao reprocessar duplicados.

**Correcao exigida:**
1. Action lowercase: `cliente.bloqueado` e `cliente.desbloqueado` (alinha com `cliente.criado`, `cliente.mesclado`).
2. Payload final do evento (audit `payload_jsonb`):
   ```json
   {
     "event_id": "<uuid v7 — ordenacao temporal>",
     "tenant_id": "<uuid>",
     "cliente_id": "<uuid>",
     "bloqueio_id": "<uuid — ressalva 1 1:N>",
     "motivo": "manual" | "inadimplencia_90d",
     "justificativa_hash": "<sha256 quando manual>",
     "causation": {"type": "titulo_vencido", "id": "<uuid>"} | null,
     "iniciado_em": "<ISO8601>",
     "iniciado_por_usuario_id": "<uuid> | null (job system)"
   }
   ```
3. `justificativa` original NAO vai pro audit. Vai pra `cliente_bloqueios.justificativa` (banco do tenant — coberto por RLS + crypto-shredding Wave B). Audit grava so o hash. Mesma logica que US-CLI-005 R1 advogado.
4. `Cliente.Desbloqueado` mesmo padrao + `encerrado_motivo` + `encerrado_em` + (opcional) `bloqueio_duracao_dias`.

### 7. MEDIA — Authz: `clientes.bloquear` em admin_tenant esta certo, mas perfil `financeiro` (Wave A) precisa entrar no roadmap aqui

**Problema:** `T-CLI-023` propoe seed `clientes.bloquear` e `clientes.desbloquear` para `admin_tenant`. Story original (PRD §6 US-CLI-004) diz "financeiro/dono". Atualmente perfil `financeiro` NAO existe (`authz/0003_seed_perfis.py:25-47` so seed admin_tenant, tecnico, rt_signatario, cliente_externo_leitura — mesma situacao endereçada em US-CLI-005 ressalva 1).

**Correcao exigida:**
1. Marco 1: seed APENAS para `admin_tenant` (alinhado com US-CLI-005). OK como esta.
2. Documentar no plano (riscos): "Quando Wave A introduzir perfil `gerente_financeiro` (modulo financeiro/contas-receber), adicionar `clientes.bloquear` + `clientes.desbloquear` ao seed dele via migration nova. NAO antecipar agora."
3. Garantir que o predicado `cliente_nao_bloqueado` (ressalva 2) tambem checa que o **usuario que esta bloqueando** nao e o cliente bloqueado por si mesmo (caso bizarro mas defesa em profundidade) — actions `clientes.bloquear`/`desbloquear` NAO entram na lista de actions auto-aplicadas do predicado (sem essa cautela, admin bloqueia → admin nao consegue desbloquear porque o predicado nega).

---

## Pontos fortes do plano

- Reconhecimento explicito do limite (AC-3..7 dependem de modulos inexistentes — contrato + stub + audit prontos) e honesto.
- Separacao clara entre manual (100% Marco 1) e automatico (contrato + job stub) e a abordagem certa pra evitar especular schema externo.
- `T-CLI-022` (utilitaria) tem a intencao correta — so precisa virar predicado dentro do Provider (ressalva 2).
- T-CLI-024 (causation_id no audit) ja antecipou o sinal critico — so precisa formalizar enum (ressalva 4).
- Hooks ja sao aproveitados (`authz-check`, `audit-immutability-check`, `tenant-id-validator`).
- Lista de 9 testes inclui boa parte dos cenarios — falta complementar com os 5 das ressalvas (cross-tenant predicado, idempotencia sem evento duplicado, job source vazio, job source fake, causation enum).

## Testes finais sugeridos (14 = 9 propostos + 5 das ressalvas)

Originais (9): mantidos.

Acrescentar:
- `test_bloqueio_idempotente_retorna_noop_sem_sobrescrever_motivo` (renomeia o 9o)
- `test_bloqueio_de_cliente_ja_bloqueado_nao_dispara_evento_duplicado` (ressalva 3)
- `test_predicado_cliente_nao_bloqueado_nega_os_criar_cross_tenant_seguro` (ressalva 2)
- `test_job_inadimplencia_com_source_vazio_nao_bloqueia_ninguem` (ressalva 5)
- `test_job_inadimplencia_com_source_fake_bloqueia_e_publica_causation` (ressalva 5)
- `test_historico_n_bloqueios_preservado_apos_2_ciclos_block_unblock_block` (ressalva 1)

---

## ADR-0011 (BI espelho) — impacto

Tabela 1:N `cliente_bloqueios` (ressalva 1) e exatamente o que o CDC/ETL Wave B vai consumir pra dimensao `fact_cliente_bloqueio` (analise de recidiva, MTBF inadimplencia, eficacia da regua D+30/60/89). Modelagem flat impediria isso.

## ADR-0014/0015 — impacto

`INV-INT-010` (cliente bloqueado bloqueia operacao) so e exigivel atraves do `AuthorizationProvider` unificado (ressalva 2). Hook `authz-check` ja existe; predicado ABAC e o conector. Sem isso, INV-INT-010 vira "documento" sem guardiao real.

---

## Recomendacao operacional

1. Aplicar as 7 ressalvas no plano (`docs/dominios/comercial/modulos/clientes/planos/US-CLI-004.md`) — bloqueante pra abrir `/tasks`.
2. Consultar `advogado-saas-regulado` em paralelo — justificativa de bloqueio + direito do titular saber motivo + retencao do historico de bloqueios (LGPD art. 9 transparencia + art. 16 retencao) sao territorio dele. Plano ja lista isso em "Subagentes a consultar".
3. Re-revisar (este parecer) **NAO** e necessario se as 7 forem aplicadas literalmente. Se divergencia, re-invocar.
4. Apos `/implement`, rodar 3 auditores Familia 5: Seguranca (foco no predicado ABAC + ausencia de fragmentacao authz), Qualidade (cobertura dos 14 testes + nome citando INV-INT-010), Produto (mensagem 200 noop e clara pro operador? mensagem `denied` em "os.criar" sugere "quitar debito"?).

---

## Limites de honestidade

- **Confiante:** ressalvas 1, 2, 3, 4, 5, 6, 7 — estado real confirmado lendo `clientes/models.py`, `authz/django_provider.py:66-244`, `authz/0003_seed_perfis.py`, `pyproject.toml:16`, `audit/services.py:25-62`, ADR-0007, ADR-0012, ADR-0015 linhas 201-260.
- **Suspeita nao-provada:** ressalva 5 — Procrastinate v2.9.0 com Django 5 e PG 16 deve rodar limpo, mas nao medi `procrastinate healthchecks` em ambiente real. Recomendo cron drill cronometrado no Marco 1 (mesma cadencia do drill F-A) antes de habilitar o job em prod-like.
- **Fora do meu alcance:**
  - Justificativa armazenada e PII tratada? Direito do titular saber motivo do bloqueio? — escalar `advogado-saas-regulado` (ja listado no plano).
  - Texto da `justificativa` minimo (30 chars suficiente? 50?) e enum `motivo` final — escalar UX/Produto.
  - Race condition entre job_inadimplencia (02:00 BRT) e operador desbloqueando manualmente as 02:00:05 — recomendo pentest externo (R$ 25-50k) antes do 1o tenant pago, conforme limite ja citado em revisoes anteriores. Mitigacao parcial: advisory lock + UNIQUE INDEX parcial cobrem 80% do caso.
