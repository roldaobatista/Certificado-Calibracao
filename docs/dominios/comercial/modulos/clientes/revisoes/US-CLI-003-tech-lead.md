---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-003
autor: tech-lead-saas-regulado
plano_revisado: docs/dominios/comercial/modulos/clientes/planos/US-CLI-003.md
veredito: REPROVADO
---

# Tech Lead Review — Plano US-CLI-003 (Importacao 1-clique CSV)

## 1. Veredito

**REPROVADO.** O plano tem direcao certa em escopo (CSV-only, sincrono, lote 1000, dedup via UNIQUE INDEX parcial existente, use case puro), mas esta arquiteturalmente **incompleto demais** pra abrir `/tasks`. Faltam decisoes basicas (encoding, delimitador, mapeamento, transacao, idempotencia, formato do erro, contrato do upload) e tem **2 falhas criticas de seguranca** (DoS por tamanho de arquivo e CSV injection / formula injection nao endereçadas) — ambas com superficie de ataque imediata em qualquer tenant pago. O numero de ressalvas (12, sendo 4 criticas) excede o que a regra do projeto considera "ressalvas" — o plano precisa ser **reescrito**, nao apenas corrigido item a item. Apos reescrita, re-submeter pra parecer.

## 2. Resumo executivo

Plano de 59 linhas pra uma Story que mexe em **upload de arquivo de usuario** + **insert em lote** + **dedup transacional** + **audit em batch** — 4 superficies sensiveis. A densidade tecnica esta abaixo do necessario:
- `T-CLI-043` carrega comentario contraditorio ("recebendo Repository + InadimplenciaSource — nao, so Repository") que revela indecisao.
- `T-CLI-044` propoe `bulk_create_or_update` sem mencionar deadlock, isolation level, ou `select_for_update`.
- Nao ha tarefa pra sanitizar conteudo (CSV injection), validar Content-Type, limitar tamanho em bytes, nem decidir encoding/delimitador.
- Mapeamento sugerido (AC-1) nao tem formato definido — risco de cada agente inventar JSON diferente.
- Nao ha tarefa pra integrar com `AuthorizationProvider` checando se o **tenant** esta suspenso (ADR-0015 fluxo 3 — `modo: bloqueado_total` deve negar importar) — so checa perfil do usuario.

## 3. Ressalvas numeradas

### R1. CRITICA — Tamanho de upload nao tem limite em bytes (DoS imediato)

- **Problema:** `T-CLI-045` fala "limite 1000 linhas + validacao tamanho upload no settings" — mas nao define **qual limite em bytes**, **quem aplica** (Django `DATA_UPLOAD_MAX_MEMORY_SIZE`? nginx upstream? DRF parser?), nem **o que devolve**. Hoje Django default e 2.5MB (`DATA_UPLOAD_MAX_MEMORY_SIZE`). Um atacante envia arquivo de 500MB de UTF-8 com BOM esquisito; o parser drena memoria/disco antes de checar "1000 linhas".
- **Causa:** ordem invertida — o plano valida linhas **depois** de carregar; precisa validar **antes** (em bytes, no parser/middleware).
- **Correcao exigida:**
  1. Cravar limite **em bytes** explicito no plano: **2 MiB** (suficiente pra ~10000 linhas CSV razoaveis; 1000 linhas reais cabem em ~150 KiB).
  2. Configurar `DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024` em `config/settings/base.py` — declarar no plano qual setting + valor.
  3. Validar `Content-Length` no parser DRF antes de ler o body (`FileUploadParser` ou custom). Excedeu → **413 Payload Too Large** estruturada (`{"detail": "arquivo_excede_limite", "limite_bytes": 2097152}`).
  4. Validar `Content-Type` whitelist: `text/csv`, `application/csv`, `application/vnd.ms-excel`, `text/plain`. Qualquer outro → 415.
  5. Teste novo: `test_upload_excede_2mib_retorna_413` + `test_upload_content_type_invalido_retorna_415`.
- **Severidade:** CRITICA — DoS trivial. Sem isso, qualquer tenant pago pode derrubar o app.

### R2. CRITICA — CSV injection / formula injection nao endereçada (Excel quebra na maquina do operador)

- **Problema:** plano nao menciona sanitizacao de celulas que comecam com `=`, `+`, `-`, `@`, `\t`, `\r`. Um atacante importa CSV com nome = `=cmd|'/c calc'!A1` ou `@SUM(1+1)*cmd|'/c notepad'!A1`. Quando o operador (dono Roldao migrando do Bling) **exporta a lista de clientes pra Excel** depois, a celula vira formula executavel — RCE no Excel da maquina dele. Vetor classico (OWASP "Formula Injection"; CVE-2014-3524 et al.).
- **Causa:** importacao confia em texto livre vindo do CSV.
- **Correcao exigida:**
  1. Sanitizacao **na escrita** (no `bulk_create_or_update`): qualquer string que comece com `=`, `+`, `-`, `@`, `\t`, `\r` recebe prefixo `'` (apostrofo) — neutraliza formula sem destruir o dado.
  2. Funcao utilitaria `sanitizar_celula_csv(v: str) -> str` em `src/infrastructure/clientes/csv_safety.py`, reutilizada por exportacao futura.
  3. Teste: `test_importar_neutraliza_formula_em_nome_e_email` (entrada `=cmd|...` → grava `'=cmd|...` no banco; round-trip pra export devolve string literal, nao formula).
  4. Documentar no plano que **export** futuro (Wave A) tambem aplica a mesma funcao no boundary de saida (defesa em profundidade).
- **Severidade:** CRITICA — superficie de RCE indireto. Bonus: protege tambem o Auditor LGPD/CGCRE que abrir CSV exportado pro Excel.

### R3. CRITICA — Dedup em lote sem decisao sobre isolation level + lock

- **Problema:** `T-CLI-044` propoe `bulk_create_or_update` mas nao detalha:
  - Como evitar **deadlock** quando importacao A (linhas 1-1000) e importacao B (linhas 500-1500) tocam o mesmo CPF? Ordem de aquisicao de locks importa — sem ordenacao deterministica, dois ciclos pegam locks invertidos → deadlock detector PG aborta uma.
  - `select_for_update()` por linha (skip_locked? no_wait?) ou advisory lock por (tenant_id, documento)?
  - Isolation level: `READ COMMITTED` (default Django) sofre lost-update no UPDATE de duplicata se duas linhas no mesmo arquivo tem CPF=X (uma sobrescreve a outra silenciosamente). `REPEATABLE READ` ou `SERIALIZABLE` resolve, mas custa retry.
- **Causa:** plano usou frase generica "transaction.atomic + cursor + serializacao" sem expandir.
- **Correcao exigida:**
  1. Decidir e cravar no plano: **`SERIALIZABLE` por importacao** (transaction `set isolation level serializable` no inicio do use case). Custo aceitavel pra 1000 linhas; protege lost-update.
  2. **Advisory lock por tenant**: `pg_advisory_xact_lock(hashtext('importacao_clientes:' || tenant_id::text))` no inicio do use case — serializa duas importacoes simultaneas do **mesmo tenant**. Tenants diferentes nao competem (lock e tenant-scoped). Padroniza com hash chain do audit (`audit/services.py:48`).
  3. Dedup intra-arquivo (duas linhas com mesmo CPF no mesmo CSV): pre-processar o arquivo em memoria, agrupar por documento, ultima linha vence + relatorio explicita `linhas_colapsadas_intra_arquivo: N`. Documentar no plano explicitamente — caso contrario o operador vai dizer "importei 1000 linhas, criou 998" e ninguem entende.
  4. Adicionar 2 testes: `test_2_importacoes_simultaneas_mesmo_tenant_serializam_sem_deadlock` + `test_csv_com_documento_duplicado_intra_arquivo_colapsa_e_relata`.
- **Severidade:** CRITICA — deadlock em prod = falha silenciosa do worker, cliente reclama "minha importacao sumiu".

### R4. CRITICA — Tenant suspenso (ADR-0015 fluxo 3) deve negar importar; predicado ABAC faltando

- **Problema:** `T-CLI-047` seed `clientes.importar` so pra `admin_tenant` esta correto, **mas insuficiente**. ADR-0015 fluxo 3 cravou que tenant em `modo: bloqueado_total` (D+15 inadimplencia) so deve acessar "area de regularizacao". Importar 1000 clientes nao e regularizacao — e a operacao **mais cara** que existe no modulo. Plano nao tem predicado ABAC `tenant_ativo` no `AuthorizationProvider`.
- **Causa:** authz so checa perfil; estado do tenant nao entra na decisao.
- **Correcao exigida:**
  1. Registrar predicado ABAC `tenant_nao_suspenso` em `src/infrastructure/authz/predicates.py` (mesma localizacao do `cliente_nao_bloqueado` da R2 do parecer US-CLI-004) — consulta `tenant.modo_suspensao` (a criar quando ADR-0015 entrar; **deixar stub agora**: predicado retorna sempre `allowed=True` + TODO marcando dependencia).
  2. Configurar `clientes.importar` na lista de actions auto-aplicadas do predicado.
  3. Teste: `test_importar_com_tenant_stub_nao_suspenso_passa` + skip marker pra `test_importar_com_tenant_suspenso_nega_403` (skip ate ADR-0015 entrar — registra o contrato).
  4. Documentar no plano que esse predicado e o canal **unico** pra ADR-0015 fluxo 3 interceptar importacao — caso contrario, em Wave A alguem vai criar checagem paralela e a fragmentacao do parecer US-CLI-004 R2 se repete.
- **Severidade:** CRITICA — INV-INT-009 (suspensao desliga features) so e exigivel via predicado. Sem stub agora, contrato perde.

### R5. ALTA — Encoding + delimitador + BOM nao decididos; AC-1 fica ambiguo

- **Problema:** Brasil exporta CSV com **3 variacoes legitimas**: (a) UTF-8 sem BOM virgula (Bling moderno), (b) UTF-8 com BOM ponto-e-virgula (Excel BR), (c) Latin-1 (ISO-8859-1) ponto-e-virgula (Cali legado, Excel 2010-). Plano nao decide qual aceita, qual rejeita, ou como detecta.
- **Causa:** AC-1 "preview com 10 primeiras linhas" depende de saber decodificar 10 primeiras linhas; sem decisao, cada agente vai usar `open(arq, "r")` cego (UTF-8 estrito = falha em Latin-1).
- **Correcao exigida:**
  1. Decidir e cravar: **aceitar (a) e (b)**. Latin-1 (c) **rejeita com 400** + mensagem "salve como UTF-8 (Excel: Salvar Como > CSV UTF-8)". Razao: detectar encoding com `charset-normalizer` introduz heuristica que falha em 10% dos casos e gera bug nojento; cravar UTF-8 desde o dia 1.
  2. Aceitar **delimitador `,` e `;`** com **deteccao automatica** via `csv.Sniffer().sniff(amostra)` na primeira leitura — devolver no preview o delimitador detectado, operador confirma na execucao.
  3. Aceitar **BOM UTF-8** (strip transparente no parser).
  4. Tarefa nova `T-CLI-04X`: utilitaria `ler_csv_normalizado(arq) -> tuple[delimitador, dialeto, linhas]` em `src/infrastructure/clientes/csv_io.py`.
  5. Testes: `test_csv_utf8_bom_com_ponto_virgula_brasileiro_detecta_e_le`, `test_csv_latin1_rejeita_com_400_e_dica`, `test_csv_delimitador_misto_detecta_pelo_maior_consenso`.
- **Severidade:** ALTA — sem isso, 30% dos uploads quebram silenciosamente ou geram lixo no banco.

### R6. ALTA — Formato do "mapeamento sugerido" nao definido (AC-1 fica nao-implementavel)

- **Problema:** AC-1 fala "mapeamento sugerido" mas plano nao define schema. Em qual formato? Que campos do Cliente sao alvos? Quais heuristicas? Sem isso, T-CLI-041 e adivinhacao.
- **Causa:** plano pulou design da resposta de preview.
- **Correcao exigida:**
  1. Schema da resposta `POST /importar-preview/`:
     ```json
     {
       "delimitador_detectado": ";",
       "encoding_detectado": "utf-8",
       "linhas_amostra": [["coluna1", "coluna2", ...], ...],  // 10 linhas brutas
       "headers_arquivo": ["CPF/CNPJ", "Razao Social", "E-mail", "Telefone", ...],
       "mapeamento_sugerido": {
         "documento": {"coluna": "CPF/CNPJ", "confianca": "alta"},
         "nome": {"coluna": "Razao Social", "confianca": "alta"},
         "email": {"coluna": "E-mail", "confianca": "alta"},
         "telefone": {"coluna": "Telefone", "confianca": "media"},
         "tipo_pessoa": {"coluna": null, "confianca": "inferida_por_documento"}
       },
       "campos_destino_disponiveis": ["documento", "nome", "nome_fantasia", "email", "telefone", "tipo_pessoa"]
     }
     ```
  2. Heuristica de matching: tabela `HEADER_HEURISTICAS` em `csv_io.py`:
     - `documento` <- header em `{"CPF", "CNPJ", "CPF/CNPJ", "Documento", "DOC"}` (case-insensitive)
     - `nome` <- `{"Nome", "Razao Social", "Cliente", "Nome Completo"}`
     - `email` <- `{"E-mail", "Email", "Correio Eletronico"}`
     - `telefone` <- `{"Telefone", "Fone", "Celular", "WhatsApp"}`
  3. `tipo_pessoa` inferido por len(documento normalizado) — 11=PF, 14=PJ.
  4. Teste: `test_preview_mapeia_header_cpf_cnpj_pra_documento` + `test_preview_devolve_confianca_baixa_quando_header_desconhecido`.
- **Severidade:** ALTA — sem schema, AC-1 vira contrato ambiguo entre agentes futuros.

### R7. ALTA — Idempotencia de re-upload nao definida; rerun com mesmo arquivo deve ser previsivel

- **Problema:** `T-CLI-042` aceita `update_existing` mas nao define o que acontece em rerun com **mesmo arquivo**:
  - `update_existing=true`: idempotente (mesmos dados, sem efeito alem do audit de "executou de novo")? Ou re-conta como "atualizado N"?
  - `update_existing=false`: cada linha bate no UNIQUE e vai pra "rejeitados" como `ja_existe`? Ou pula silenciosamente?
- **Causa:** comportamento nao especificado.
- **Correcao exigida:**
  1. **`update_existing=true`**: idempotente — re-aplica SET; se valores iguais, `UPDATE` no PG marca a linha mas nao muda nada (custo barato). Relatorio reporta `atualizados=0, criados=0, sem_mudanca=N` (3a categoria nova).
  2. **`update_existing=false`**: cada duplicata vai pra `rejeitados` com motivo `ja_existe_no_tenant`. **Nao** silencioso.
  3. **Hash do arquivo importado**: calcular `sha256(arquivo_bytes)` + gravar no audit `cliente.importacao_executada` em `payload.arquivo_hash`. Rerun com mesmo hash **alerta** no relatorio (`reimportacao_detectada: true, ultima_importacao_em: <ts>`) — operador decide se quer continuar.
  4. Teste: `test_rerun_mesmo_arquivo_update_existing_true_e_idempotente` + `test_rerun_mesmo_arquivo_emite_alerta_reimportacao`.
- **Severidade:** ALTA — sem isso, "importei de novo por engano" vira incidente de suporte.

### R8. ALTA — Use case puro com comentario contraditorio; Repository protocol precisa ser extendido

- **Problema:** `T-CLI-043` diz `importar_clientes.py — use case puro recebendo Repository + InadimplenciaSource (nao, so Repository)`. Comentario parentetico admite indecisao no proprio plano — agente que ler isso vai inventar.
- **Causa:** plano nao decidiu.
- **Correcao exigida:**
  1. **So `ClienteRepository`** — `InadimplenciaSource` nao tem relevancia em importar.
  2. Extender `ClienteRepository` (Protocol em `src/domain/comercial/clientes/repository.py`) com:
     ```python
     def bulk_upsert(
         self,
         *,
         tenant_id: UUID,
         linhas: list[ClienteImportacaoInput],
         update_existing: bool,
         agora: datetime,
     ) -> ResultadoImportacao: ...
     ```
     Onde `ClienteImportacaoInput` e DTO frozen + `ResultadoImportacao` tem `(criados, atualizados, sem_mudanca, rejeitados: list[LinhaRejeitada])`.
  3. Adapter `DjangoClienteRepository.bulk_upsert` usa `bulk_create(update_conflicts=True, update_fields=[...], unique_fields=["tenant_id","tipo_pessoa","documento"])` do Django 5.0 — nativo, ja considera o UNIQUE INDEX parcial.
  4. Use case **nunca** importa `django.*`. Use case importa o Protocol + DTOs do domain. Padrao identico ao `mesclar_clientes.py` (ja aceito em US-CLI-005).
  5. Remover comentario contraditorio do `T-CLI-043` no plano.
- **Severidade:** ALTA — indecisao no plano vira divergencia em codigo.

### R9. ALTA — Atomicidade insuficiente: parcial-commit vs all-or-nothing nao decidido

- **Problema:** plano nao decide: se linha 500 falha por CNPJ invalido, **as 499 anteriores ja foram inseridas** (parcial-commit) ou **rolam back tudo** (all-or-nothing)?
  - Parcial-commit + `skip_invalid=true`: operador ve relatorio "criados=499, rejeitados=1, restantes=500 nao processados". Confuso.
  - All-or-nothing + `skip_invalid=false`: linha 500 invalida aborta tudo; operador conserta CSV e re-tenta.
  - `skip_invalid=true` deve ser **dentro da mesma transacao** (separar linhas validas das invalidas em pre-processamento; ai sim transacao unica processa so as validas).
- **Causa:** plano nao formaliza.
- **Correcao exigida:**
  1. Cravar: **pre-processamento separa validas/invalidas; transacao unica processa so validas; relatorio devolve invalidas com motivo**.
  2. `skip_invalid=false` (default): se houver QUALQUER linha invalida no pre-processamento, **400 estruturada** + lista de erros + nenhuma linha persistida.
  3. `skip_invalid=true`: invalidas viram `rejeitados[]` no relatorio; validas inseridas em transacao unica.
  4. Teste: `test_executar_skip_invalid_false_com_1_linha_invalida_nao_persiste_nada` + `test_executar_skip_invalid_true_com_1_linha_invalida_persiste_999_e_relata_1`.
- **Severidade:** ALTA — diferença operacional enorme entre os 2 modos.

### R10. MEDIA — Audit `cliente.importacao_executada` precisa de schema cravado + sem PII

- **Problema:** `T-CLI-046` diz "audit com totais + nenhuma PII" — direcao certa, mas sem schema cravado vira invencao. Padrao das US anteriores: `event_id`, `tenant_id`, hashes pra referencia PII.
- **Causa:** plano nao definiu schema.
- **Correcao exigida:**
  1. Action lowercase: `cliente.importacao_executada` (consistente com `cliente.criado`, `cliente.mesclado`, `cliente.bloqueado` ja aceitos).
  2. Schema do `payload_jsonb`:
     ```json
     {
       "event_id": "<uuid v4>",
       "tenant_id": "<uuid>",
       "importacao_id": "<uuid>",  // id sintetico desta operacao, util pra relatorio
       "arquivo_hash": "<sha256 do arquivo bytes>",
       "arquivo_nome_hash": "<sha256 do filename — sem PII>",
       "totais": {
         "linhas_lidas": 1000,
         "linhas_colapsadas_intra_arquivo": 3,
         "criados": 850,
         "atualizados": 100,
         "sem_mudanca": 40,
         "rejeitados": 7
       },
       "rejeitados_motivos_agregados": {"cnpj_invalido": 4, "ja_existe_no_tenant": 3},
       "rejeitados_linhas_hashes": ["<sha256(linha_1_bytes)>", ...],  // referencia sem PII
       "update_existing": true,
       "delimitador": ";",
       "encoding": "utf-8",
       "usuario_id": "<uuid>",
       "executado_em": "<ISO8601>"
     }
     ```
  3. **PII proibida no audit**: documento, nome, email, telefone — nada vai pra `payload_jsonb`. Referencia a linha rejeitada via `sha256(bytes_linha_original)`. Operador que precisa investigar consulta o arquivo original (que NAO e armazenado pelo sistema — ver R12).
  4. Teste: `test_audit_importacao_nao_contem_cpf_cnpj_nome_email_telefone` (regex/scan do payload).
- **Severidade:** MEDIA — desvio do padrao das 4 US anteriores ja aceitas; corrigir aqui evita drift.

### R11. MEDIA — Sincrono no Marco 1 precisa caber em timeout; medir + documentar

- **Problema:** plano declara sincrono mas nao mediu/declarou timeout. Gunicorn default e 30s. 1000 linhas em PG via `bulk_create` com `update_conflicts` em transacao SERIALIZABLE — ordem de grandeza 1-5s em maquina dev, mas pode estourar em prod com IO alto.
- **Causa:** plano nao mediu.
- **Correcao exigida:**
  1. Drill: rodar `test_bulk_upsert_1000_linhas_p95_abaixo_de_10s` em CI (pytest marker `slow`). Se falhar consistentemente, sinaliza necessidade de quebrar em chunks.
  2. Documentar no plano (riscos): "Sincrono valido enquanto p95 < 10s na suite de drill. Acima disso, **forcar Procrastinate** mesmo no Marco 1 (memoria `nao-construir-codigo-descartavel` — vide US-CLI-004 R5)".
  3. Resposta HTTP: timeout 30s no nivel Gunicorn (`--timeout 30` em `prod.py`); cliente recebe 504 se passar.
- **Severidade:** MEDIA — risco de descobrir tarde demais. Drill resolve.

### R12. MEDIA — Retencao do arquivo importado nao decidida (territorio do advogado)

- **Problema:** plano nao diz se o **arquivo CSV bruto** e armazenado em algum lugar (Backblaze B2 WORM? somente em memoria? descartado depois do processamento?). LGPD + ISO 17025 8.4 + Receita 5 anos tem regras diferentes sobre isso.
- **Causa:** decisao regulatoria/LGPD — escalar advogado.
- **Correcao exigida (parcial, tecnica):**
  1. **Padrao default proposto**: arquivo **descartado** apos processamento. So `arquivo_hash` (sha256) e `arquivo_nome_hash` ficam em audit. Operador que precisa re-importar carrega de novo.
  2. **Justificativa tecnica**: armazenar CSV bruto cria deposito permanente de PII (CPFs/CNPJs/nomes/emails) em Backblaze — superficie LGPD ampla. Hash + audit dao rastreabilidade sem armazenamento.
  3. **Escalar ao advogado**: confirmar se LGPD/ISO 17025 obriga reter o arquivo original (ex: "comprovacao de origem do dado") ou se hash + audit basta. Plano deve listar isso explicitamente em "Subagentes a consultar".
- **Severidade:** MEDIA — decisao 100% regulatoria; nao bloqueia codigo mas precisa ficar visivel.

## 4. Riscos arquiteturais (nao bloqueantes, dignos de nota)

- **A. Aceite LGPD em lote pra PF**: plano (linha 26) diz "PF em lote rejeita ou exige flag de aceite presencial". Esse e territorio do advogado — minha leitura tecnica e que **rejeitar** e seguro; **flag de aceite presencial** abre brecha pra abuso (operador marca tudo sem aceite real). Tecnicamente, ambas sao implementaveis; recomendo aguardar parecer do advogado antes de codificar a opcao final.
- **B. Procrastinate nao habilitado neste plano**: US-CLI-004 R5 do parecer anterior exigiu Procrastinate. Importacao 1000 linhas sincrona valida (R11), mas Cali/Bling parsers (Wave A) vao processar 10000+ linhas — vao depender de Procrastinate. Se US-CLI-004 nao habilitar Procrastinate, Wave A vai re-abrir essa briga. Recomendo: importacao sincrona em Marco 1, **enfileiravel** em Wave A (mesmo use case, decorator `@procrastinate.task`).
- **C. Pre-processamento em memoria de 1000 linhas**: ~2 MiB de body + estruturas Python intermedias chegam facil a 50-100 MiB de RSS por request. Gunicorn 2 workers no plano F-A — DoS de 4 requests paralelos cabe na RAM da VPS (3 GiB livres). Nao bloqueante, mas dimensionar em alerta Grafana quando Wave A entrar.
- **D. Hash chain do audit em batch**: `registrar_auditoria` usa `pg_advisory_xact_lock` (parecer US-CLI-005 ressalva 6.3). 1 importacao = 1 linha de audit (agregada). Tudo ok. Se algum agente futuro decidir gravar 1 audit por linha importada, contention vira problema. Cravar no plano (riscos): **1 importacao = 1 linha audit `cliente.importacao_executada`. NUNCA 1 audit por linha.** Detalhe das linhas vai em `payload.totais` + hashes.
- **E. Idempotencia entre import + merge**: se cliente A foi mesclado em B (US-CLI-005) e operador re-importa CSV antigo que tem CPF de A, o que acontece? Sem flag de "merged_into", o documento de A esta soft-deleted (manager default nao ve), cria novo cliente C com mesmo CPF — historico fragmenta. Solucao: dedup tambem consulta `Cliente.all_objects` (parecer US-CLI-005 ressalva 3) — se documento existe em soft-deleted, **rejeita com motivo `documento_pertence_a_cliente_mesclado`** + sugere consultar `vencedor_id` via audit `cliente.mesclado`. Adicionar teste `test_importar_documento_de_cliente_mesclado_rejeita_com_link_vencedor`.

## 5. Pontos fortes do plano

- **Escopo enxuto correto**: CSV-only, sincrono, lote 1000, Cali/Bling parsers diferidos pra Wave A — direcao certa pra Marco 1 sem gold-plate.
- **Reuso do UNIQUE INDEX parcial de US-CLI-005**: dedup automatico via constraint existente em vez de inventar logica nova; aproveita codigo ja aceito.
- **Non-goals explicitos**: 5 itens claros (Cali/Bling, XLSX, async, PF com aceite individual, conflito manual) — evita drift de escopo.
- **Audit em batch correto**: `cliente.importacao_executada` como evento unico (nao 1 por linha) — alinha com pattern de `cliente.criado`/`cliente.mesclado`/`cliente.bloqueado` e protege hash chain do audit.
- **Subagentes a consultar listados**: tech-lead (este) + advogado — reconhece os 2 vetores (tecnico + regulatorio) corretamente.
- **Realismo sobre Marco 1**: plano nao tenta antecipar Procrastinate worker nem UI rica — escopo apropriado pra entregar.

## 6. Recomendacao operacional

1. **Reescrever o plano** endereçando R1-R12. Estrutura sugerida pra revisao: cravar **R1, R2, R3, R4** primeiro (criticas); R5-R9 sao decisoes basicas de design; R10-R12 sao polimento.
2. Consultar `advogado-saas-regulado` em paralelo — aceite LGPD em lote (R12 + Risco A) + retencao do arquivo + RAT da importacao sao territorio dele.
3. Re-submeter pra parecer tech-lead **apos reescrita** (nao item-a-item — o plano atual e enxuto demais pra absorver 12 ressalvas via patch).
4. Apos `/implement`, rodar 3 auditores Familia 5: **Seguranca** (foco em R1 + R2 + R4 — DoS, formula injection, predicado tenant), **Qualidade** (cobertura dos 20+ testes propostos + drill de p95), **Produto** (mensagens de erro pro operador Roldao — "salve como UTF-8" deve ser amigavel).

## 7. Limites de honestidade

- **Confiante**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10 — estado real confirmado lendo `config/settings/base.py` (sem limite de upload), `repositories.py` (Repository nao tem `bulk_upsert`), `views.py` (sem predicado tenant), `models.py` (UNIQUE INDEX parcial existe), ADR-0015 fluxo 3, parecer US-CLI-004 R5 (Procrastinate).
- **Suspeita nao-provada**: R11 (p95 < 10s em 1000 linhas) — nao medi em hardware real. Drill resolve em CI.
- **Fora do meu alcance**:
  - Aceite LGPD em lote pra PF (rejeitar vs flag) — escalar advogado.
  - Retencao do arquivo bruto importado (LGPD vs Receita vs ISO 17025) — escalar advogado.
  - Texto do erro pro operador (R5 "salve como UTF-8") — escalar Produto/UX.
  - Pentest da superficie de upload (formula injection + DoS combinados) — recomendar pentest externo antes do 1o tenant pago, conforme limite ja citado em revisoes anteriores.
