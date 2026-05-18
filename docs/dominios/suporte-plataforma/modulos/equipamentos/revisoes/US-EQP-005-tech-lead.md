---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-005
plano_revisado: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-005.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-EQP-005

## Resumo executivo

Plano cobre bem a superfície sensível do sucatamento (estado terminal, idempotência, confirmação dupla, audit segregado para cert vigente, foto opcional com EXIF strip, rate limit e Idempotency-Key destrutivo). Reaproveita o padrão `EmptyService` já aprovado em US-EQP-004 / US-CLI-001 (log-as-bus interim em `auditoria` WORM com hash chain) e respeita os subagentes upstream (advogado R1–R6, RBC C5/B5). Há, contudo, **6 ressalvas** que precisam ser endereçadas antes de `/tasks`: duas **CRÍTICAS** (sintaxe do trigger PG `bloquear_saida_de_sucata` + ambiguidade de porta `OS` vs `Certificado`), uma **ALTA** (idempotência sob concorrência: precisa `select_for_update` + Idempotency-Key em camadas distintas), uma **ALTA** (defesa em profundidade ausente para garantir cumprimento de contrato quando `Empty*Service` está plugado em prod) e duas **MÉDIAS** (escopo da foto + design da confirmação dupla).

## Veredito

**APROVADO COM RESSALVAS** (6 ressalvas — bloqueiam `/tasks` até endereçadas no plano; nenhuma exige reabertura da Story ou da PRD).

---

## Ressalvas (ordem por gravidade)

### 1. CRÍTICA — Sintaxe segura do trigger `bloquear_saida_de_sucata` + brecha do `current_user`

**Problema:** o plano (T-EQP-052, migration 0016) declara "trigger PG impede UPDATE para outros status exceto `extraviado` (admin via Django admin)" mas não especifica COMO o trigger distingue "admin Django" do resto. As 3 abordagens possíveis têm falhas conhecidas:

1. **`session_user` / `current_user`** — fura. Toda a aplicação usa o mesmo role PG (`afere_app`); ORM, admin e endpoint REST chegam no banco com o MESMO usuário. O trigger não consegue distinguir.
2. **`SET LOCAL afere.allow_sucata_exit = true`** antes do UPDATE — funciona mas precisa de wrapper Django que QUALQUER caminho admin chame; é facilmente burlado por um `Equipamento.objects.filter(pk=x).update(status='ativo')` em shell.
3. **Bloquear TUDO em PG + permitir transição apenas via função `SECURITY DEFINER` `marcar_extraviado_de_sucata(equipamento_id, justificativa)`** chamada explicitamente pelo admin Django — esta é a abordagem segura (espelha o padrão `auditoria_bloqueia_mutation` em `src/infrastructure/audit/migrations/`).

**Correção exigida (não-negociável):**

1. Trigger PG `bloquear_saida_de_sucata` em `BEFORE UPDATE ON equipamento` que rejeita **qualquer** transição saindo de `sucata`, sem exceção, com `RAISE EXCEPTION 'INV-EQP-XXX: sucata é estado terminal — use marcar_extraviado_de_sucata()'`.
2. Função PG `marcar_extraviado_de_sucata(equipamento_uuid UUID, justificativa TEXT, usuario_id UUID)` `SECURITY DEFINER` que: valida `current_setting('app.tenant_id', true) IS NOT NULL` (RLS context); faz o UPDATE para `extraviado` desabilitando o trigger via flag de sessão **interna à função** (`PERFORM set_config('afere.bypass_sucata_trigger', 'on', true)`); grava `auditoria` com `action='equipamento.extraviado_pos_sucata'` + `justificativa` no payload; reabilita o trigger. Apenas a função tem permissão de setar a flag — o `equipamento` views layer não.
3. Trigger checa `current_setting('afere.bypass_sucata_trigger', true) = 'on'` ANTES de bloquear. Como esse setting só é setado dentro da função `SECURITY DEFINER`, ninguém consegue burlar via shell/ORM/Django admin direto.
4. Comentário `# tests-coverage: <teste_happy>, <teste_unhappy>` na migration apontando teste happy (admin → extraviado via função) + unhappy (UPDATE direto via ORM → IntegrityError + audit não-gravado).
5. Sintaxe deve evitar `pg_authid`/`pg_roles` (frágeis); apoiar-se em `set_config('afere.*', ..., true)` (sempre `true` = local à transação, evita vazamento entre sessões).

**Justificativa da escolha 3:** padrão `SECURITY DEFINER` + flag de transação é o mesmo aprovado em `auditoria_bloqueia_mutation` (Marco 4 F-A). Não inventa pattern novo. Hook `audit-immutability-check` já entende esse pattern e não bloqueia legitimamente.

### 2. CRÍTICA — `OSQueryService` ≠ `CertificadoQueryService` — plano e api.md misturam

**Problema:** o plano §T-EQP-053 chama corretamente `CertificadoQueryService.equipamento_tem_certificado_vigente()`. Mas `api.md:143` (que o próprio plano cita como contrato) diz: *"Cert vigente (`OSQueryService.equipamento_tem_certificado_vigente()`) + ..."* — usando `OSQueryService` para uma checagem que é de **certificado**. Inconsistência entre dois documentos canônicos.

Isso vai virar bug em `/implement`: o agente vai (a) implementar dois métodos com mesmo nome em portas diferentes, (b) chamar a porta errada, (c) ou criar uma única porta polifuncional violando segregação ISP.

**Correção exigida:**

1. `OSQueryService.equipamento_tem_os_aberta() -> bool` — só checa OS aberta.
2. `CertificadoQueryService.equipamento_tem_certificado_vigente() -> CertificadoSummary | None` — só checa cert vigente (já existe no modelo-de-dominio v2 segundo o plano).
3. Corrigir `contratos/api.md:143` para `CertificadoQueryService.equipamento_tem_certificado_vigente()` em PR atômico ANTES de abrir `/tasks` desta US.
4. Bindings em settings (sandbox): `EmptyOSQueryService` (retorna `False`) + `EmptyCertificadoQueryService` (retorna `None`). Hook `port-binding-validator.sh` (já existente — D5 da review PRD) bloqueia release prod se settings.production apontar para qualquer `Empty*`.

### 3. ALTA — Idempotência: 2 calls simultâneas precisam de `select_for_update` + Idempotency-Key NÃO substituem um ao outro

**Problema:** T-EQP-053 diz "Validar status atual != `sucata` (idempotência: se já sucata → 200 com mesma resposta)" + T-EQP-056 testa `test_idempotency_key_24h_recusa_reuso_destrutivo`. Mas há **três cenários distintos** que o plano trata como um só:

1. **Mesmo cliente reenvia mesma requisição com mesma `Idempotency-Key`** (típico double-submit de UI / retry de rede) — resposta deve ser 200 com mesmo body que a primeira chamada bem-sucedida, sem gravar segundo audit. Resolve com tabela `idempotency_keys` (tenant + key + response_hash + ttl 24h).
2. **Mesmo cliente reenvia com `Idempotency-Key` diferente, mas equipamento já é `sucata`** — resposta 200 idempotente "já está sucata", **sem** gravar segundo audit (estado já consistente). Resolve com `if status == 'sucata': return 200_sem_audit`.
3. **DUAS requisições concorrentes do mesmo equipamento** chegando ao banco quase simultaneamente (atendente clicou 2x rapidamente, OU dois operadores diferentes no mesmo equipamento) — sem proteção, ambas leem status=ativo, ambas tentam UPDATE, ambas tentam gravar audit. Resolve com `Equipamento.objects.select_for_update().get(pk=id)` **dentro** de `transaction.atomic()`. Sem isso, mesmo idempotency-key não protege (porque keys são diferentes).

**Correção exigida:**

1. Use case envolve TUDO em `with transaction.atomic():` (mesma exigência da revisão US-EQP-004 §1 — use case não pode depender de `ATOMIC_REQUESTS`).
2. `equipamento = Equipamento.objects.select_for_update().get(pk=id, tenant=active_tenant)` antes de ler status atual.
3. Após `select_for_update`, recheckar status: se já `sucata`, retornar 200 com payload da última audit `equipamento.sucateado*` referente ao equipamento (consulta `auditoria` por `resource_summary` ou `payload.equipamento_id`).
4. `Idempotency-Key` (T-EQP-056) é camada ADICIONAL: tabela `idempotency_keys(tenant_id, idempotency_key, request_hash, response_body, response_status, expires_at)` com `UNIQUE(tenant_id, idempotency_key)`. Hit → retorna response_body sem reprocessar. Miss → processa + grava key + response. TTL 24h (alinhado advogado R5 destrutivo).
5. Teste novo: `test_sucatar_concorrente_dois_workers_so_um_grava_audit` (simular com `threading` + 2 transações, ou via fixture `@pytest.mark.django_db(transaction=True)` + 2 sessões).

### 4. ALTA — `EmptyNotificacaoClienteService` em prod: contrato mínimo cumprido pelo evento de audit, mas defesa em profundidade está incompleta

**Problema:** o plano §Riscos #1 documenta corretamente que cliente final NÃO recebe e-mail até `comunicacao-omnichannel` nascer (Wave B+). A mitigação proposta — *"documentar em CURRENT.md + plano Wave B mostra que consumer real fica nessa porta"* — depende de **memória organizacional** (alguém lembrar de plugar o consumer real antes do go-live público). Histórico recente mostra que esse mecanismo falha (drift de docs corrigido várias vezes em maio/2026).

A advogada R5 reforça: o tenant **pode** ler do audit e notificar manualmente nesse intervalo, mas só pode se SOUBER que precisa fazer isso. Hoje não há sinal pra ninguém.

**Correção exigida:**

1. Gravar evento `equipamento.sucateado_com_certificado_vigente` em `auditoria` **com `notificacao_status="pendente_consumer"`** no payload — sinal explícito de que a notificação está em fila aguardando consumer real. Quando o consumer Wave B+ plugar, ele atualiza para `notificacao_status="enviada"` em LINHA NOVA do audit (`equipamento.notificacao_sucatamento_enviada`), nunca mutando a anterior (INV-001).
2. Documentar em `docs/conformidade/comum/controles-compensatorios-codigo-ia.md` (criar ou estender) uma seção "Notificações operacionais com consumer pendente" listando: (a) quais eventos hoje gravam `notificacao_status=pendente_consumer`; (b) responsabilidade do tenant de monitorar manualmente até Wave B; (c) data prevista de Wave B; (d) hook `port-binding-validator` que bloqueia release prod com binding `Empty*` em settings.production.
3. Hook `port-binding-validator.sh` (já criado em D5 da PRD review) precisa de teste explícito que falhe se `settings.production.PORT_BINDINGS.NotificacaoClienteService == 'EmptyNotificacaoClienteService'`. Não confiar em vigilância humana.
4. **NÃO trocar** o stub atual por implementação real nesta US — Wave A Marco 2 fica como está. A correção é tornar visível o débito por design (audit + doc + hook), não fingir que está resolvido.
5. Acrescentar ressalva R2 do advogado (já feita): `notificacao_template_versao` e `notificacao_canal` no payload do audit desde JÁ — consumer real Wave B só lê dali, não precisa reconstruir.

### 5. MÉDIA — Confirmação dupla `confirmacao_dupla=true`: design de UI/UX prematuro, mas o **contrato semântico** precisa cravar agora

**Problema:** o plano §T-EQP-053 trata `confirmacao_dupla` como boolean no body do POST. Isso é suficiente para o backend Marco 2, mas joga toda a responsabilidade pro frontend (HTMX) garantir que `confirmacao_dupla=true` só é enviado APÓS confirmação humana real. Há 3 níveis possíveis, com custo crescente:

| Nível | Mecanismo | Resistência a replay/automação |
|---|---|---|
| 1 | Checkbox UI + 2º clique no mesmo modal | Zero — agente IA / curl direto manda `true` sem confirmar |
| 2 | 2 requests separados: `POST /sucatear/preview` retorna `challenge_token` + `POST /sucatear?challenge=...` consome | Média — protege contra acidente de UI, não contra cliente malicioso |
| 3 | Assinatura A3 do operador no challenge_token (PAdES detached) | Alta — exige certificado digital ICP-Brasil |

Wave A Marco 2 não tem A3 ativo (ADR-0009 ainda proposta). Mas **decidir agora** o nível 1 sem cravar o contrato semântico significa que migrar pra nível 2/3 na Wave B vira breaking change na API.

**Correção exigida:**

1. Marco 2 entrega **nível 1** (checkbox + 2º clique no modal HTMX), suficiente para fechar US-EQP-005.
2. Contrato da API hoje: `confirmacao_dupla: { tipo: "checkbox_modal", ts_marcacao: <iso8601>, ts_confirmacao: <iso8601>, intervalo_min_ms: 1500 }` — **objeto**, não boolean. Backend valida: `ts_confirmacao - ts_marcacao >= 1500ms` (anti-double-click acidental). Em audit grava o objeto completo.
3. Em V2 / Wave B, adicionar `tipo: "a3_signature"` com payload assinado — mesmo endpoint, sem breaking change. Documentar em api.md §126 ("Sobre o campo `confirmacao_dupla`: extensível por discriminator `tipo`. Hoje só `checkbox_modal` é aceito; `a3_signature` em V2.").
4. Teste novo: `test_sucatar_intervalo_confirmacao_menor_que_1500ms_retorna_412` (anti-clique acidental).
5. Texto exato do modal HTMX **NÃO** é responsabilidade desta US — é US futura de UI; cravar como non-goal explícito no plano.

### 6. MÉDIA — Foto evidência: cabe NESTA US ou esperar US-EQP-006?

**Problema:** o plano §T-EQP-051 + §T-EQP-053 implementa upload de foto evidência + EXIF strip + URL no `Equipamento`. Mas US-EQP-006 (recebimento no lab) cria a porta `FotoStorageService` formal + `LocalFotoStorageService` (dev) + `B2FotoStorageService` (stub) + adapter EXIF. Há 3 caminhos:

1. **Implementar foto agora em US-EQP-005, sem a porta** — atalho server-side que lê multipart e grava em path local com EXIF strip inline. Vira código duplicado quando US-EQP-006 chegar.
2. **Implementar a porta `FotoStorageService` AGORA em US-EQP-005** — antecipa US-EQP-006, mas a US-EQP-006 só nasce depois (`Pré-requisitos: US-EQP-005`). Inversão de dependência.
3. **Adiar foto pra US-EQP-006 e fechar US-EQP-005 sem foto** — corretora C1 chama foto de "recomendado", não obrigatório no sucatamento (perfis B/C/D não exigem; em perfil A o cliente normalmente já está no fluxo de recebimento que sucateou).

**Correção exigida:**

1. **Caminho 3.** Remover T-EQP-051 (campo `foto_evidencia_sucatamento_url`) + remover ramo "Foto evidência: se enviada, EXIF removido..." de T-EQP-053. Remover testes `test_foto_evidencia_exif_removido`.
2. US-EQP-006 cria a porta `FotoStorageService` + AlterField em `Equipamento` para adicionar `foto_evidencia_sucatamento_url` + AlterField + endpoint `PATCH /v1/equipamentos/{id}/foto-evidencia-sucatamento` (action separada). Bonus: separa autz (sucatear vs anexar foto pós-fato).
3. Riscos do plano §3 (advogado RAT-EQP-FOTO + aviso prévio R4) migram pro US-EQP-006 — já estão no plano de lá.
4. Justificativa: foto-evidência-sucatamento sem porta `FotoStorageService` formal vira código órfão; com porta antes de US-EQP-006 inverte ordem de dependência declarada; remover foto agora não compromete a US (sucatar com cert vigente + notificação + audit cumpre RBC B5 + advogado R1–R6). US fica menor, entrega mais rápida.

---

## Pontos fortes do plano

- Audit segregado `equipamento.sucateado` vs `equipamento.sucateado_com_certificado_vigente` — reflete ISO 17025 cl. 7.10 (auditor RBC valida).
- Idempotency-Key TTL 24h para mutação destrutiva — alinhado padrão US-CLI-005 + advogado R5.
- Rate limit 10 req/min/usuário — razoável para destrutivo.
- Estado terminal cravado em trigger PG (defesa em banco) + check em código — defesa em profundidade real.
- Reaproveita corretamente `EmptyNotificacaoClienteService` + `EmptyCertificadoQueryService` + binding em settings (padrão consolidado em US-CLI-001, US-EQP-001, US-EQP-004).
- Non-goals explícitos (consumer real, blur facial, reativação, geolocalização) — não deixa débito implícito.

---

## Recomendação operacional

1. Aplicar as 6 ressalvas no plano (`docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-005.md`) — bloqueante pra abrir `/tasks`.
2. **Atômico antes de tudo:** corrigir inconsistência `OSQueryService` → `CertificadoQueryService` em `contratos/api.md:143` em PR separado (ressalva 2).
3. Criar (ou estender) `docs/conformidade/comum/controles-compensatorios-codigo-ia.md` cobrindo "Notificações operacionais com consumer pendente" (ressalva 4) — pode ser PR atômico junto.
4. Após `/implement`, rodar:
   - Auditor de Qualidade — cobertura dos testes (incluir os novos: concorrência §3, intervalo confirmação §5, port-binding §4).
   - Auditor de Segurança — foco no trigger `bloquear_saida_de_sucata` (tentar burlar via ORM, shell, raw SQL, admin Django) + não-vazamento cross-tenant em `Idempotency-Key`.
   - Auditor de Produto — confirmar que o nível 1 de confirmação dupla atende RBC B5 hoje E que o contrato extensível §5 não complica UX desnecessariamente.

---

## Limites de honestidade

- **Confiante:** ressalvas 1, 2, 3, 5 — padrões já aplicados em F-A e Marco 1 clientes; código real lido (`audit/models.py`, `audit/migrations/`, `equipamentos/contratos/api.md`).
- **Suspeita não-provada:** ressalva 4 — não verifiquei se `port-binding-validator.sh` já está ativo em `.claude/settings.json` (D5 da PRD review listou como "criar"; status pode ter avançado). Se ainda não está, criar é pré-requisito antes do go-live público — não bloqueia esta US.
- **Fora do meu alcance:** ergonomia do modal HTMX de confirmação dupla (ressalva 5) — escalar `consultor-rbc-iso17025` se a leitura jurídica do botão "Confirmo que entendo que cert vigente continua emitido" precisar de wording específico ISO 17025. Adv R4 (aviso foto) já está coberto na ressalva 6 (foto migra pra US-EQP-006).
- **Fora do meu alcance — escala de produção:** trigger `bloquear_saida_de_sucata` + `SECURITY DEFINER` precisa de drill cronometrado em ambiente com >1k equipamentos para confirmar custo da função em lote (se admin Django marca 50 equipamentos extraviados de uma vez). Recomendo registrar como teste de carga Wave B antes de 1º tenant pago — não bloqueia Marco 2.
