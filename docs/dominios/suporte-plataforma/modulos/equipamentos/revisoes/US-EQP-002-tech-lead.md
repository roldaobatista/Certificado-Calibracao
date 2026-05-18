---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-002
plano_revisado: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-002.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-EQP-002

## Resumo executivo

Plano bem estruturado, faz o trabalho duro de articular versionamento, A3 condicional por perfil e workflow `gestor_qualidade` em uma só US com 26 tasks. Decisões C2 (incluir `cliente_atual_id_no_momento` no snapshot) e adapter `MockAssinaturaA3Service` corretas. Há, porém, **6 ressalvas** — uma crítica (função SQL stub mascarada da governança de portas), duas altas (mock A3 mascarando bugs + SLA D+7 fora de Marco 2) e três médias. Nenhuma reabre Story; todas endereçáveis dentro do próprio plano.

## Veredito

**APROVADO COM RESSALVAS** (6 ressalvas — bloqueiam `/implement` até endereçadas; ressalvas 5 e 6 podem ser mitigadas com nota explícita no plano sem mudar tasks).

---

## Ressalvas (ordem por gravidade)

### TL1. CRÍTICA — Função SQL stub `equipamento_tem_certificado_emitido()` escapa do `port-binding-validator`

**Problema:** o plano (T-EQP-019) cria uma função SQL no banco (`equipamento_tem_certificado_emitido(equipamento_id, tenant_id) RETURNS BOOLEAN`) que sempre retorna `false` enquanto módulo certificados não existe. Quando o módulo nascer, ela vira VIEW/função real consultando `certificados`. **Mas:**

1. O hook `port-binding-validator` (a criar em US-EQP-003 por T-EQP-016 do US-EQP-001) é desenhado para validar `settings.PORT_BINDINGS` em código Python (`EmptyCertificadoQueryService` vs adapter real). **Função SQL não passa por esse caminho.** Logo, se alguém promover `settings.production` apontando `CertificadoQueryService` para o adapter real, a função SQL pode continuar retornando `false` indefinidamente — e o trigger PG nunca dispara em prod. Isso é uma **bomba-relógio regulatória**: certificados emitidos sendo editados em campos imutáveis sem que ninguém perceba até auditoria CGCRE.

2. O trigger é a **única** defesa de banco contra INV-025 (a camada `application` confia no retorno do trigger). Se a função SQL ficar dessincronizada do adapter Python, a defesa em profundidade morre.

**Correção exigida (não-negociável):**
1. Renomear a função SQL stub para `equipamento_tem_certificado_emitido_v0_stub()` (sufixo `_v0_stub` explícito) — quando o módulo certificados nascer, **OBRIGA** criar `_v1` apontando para a tabela real + DROP da `_v0_stub` na mesma migration. Sem isso, alguém que abrir `\df+` no psql não percebe que está em estado degradado.
2. Estender o hook `port-binding-validator` (T-EQP-016 US-EQP-001) para ler também `pg_proc` via query e bloquear release prod se houver função com sufixo `_stub` em schema `public`/`equipamentos`. Adicionar 1 caso ao `_test-runner.sh`.
3. Adicionar comentário PG na função: `COMMENT ON FUNCTION equipamento_tem_certificado_emitido_v0_stub IS 'STUB: sempre retorna false. Substituir por v1 quando módulo certificados nascer. Bloqueia release prod via port-binding-validator.';`
4. Teste explícito que falha em CI quando settings.production é simulado + função `_v0_stub` ainda existe: `test_funcao_stub_certificado_bloqueia_settings_production`.

Sem isso, a "defesa em profundidade" do trigger é teatro.

### TL2. ALTA — `MockAssinaturaA3Service` sempre-ok abre janela para regressão silenciosa

**Problema:** T-EQP-022 cria adapter que **sempre retorna OK** + log warning. Os 2 testes propostos no plano (`perfil_A_sem_a3` e `perfil_A_com_a3`) garantem que o **fluxo de exigência** funciona — mas **não** garantem que, quando o adapter real (`LacunaWebPkiAssinaturaA3Service`) entrar, ele seja efetivamente chamado nos casos certos. Risco concreto: alguém esquece de mudar `settings.PORT_BINDINGS` ao mudar para prod, mock continua ativo, todas as assinaturas passam silenciosamente — e auditor descobre 3 meses depois que **nenhum** versionamento perfil A foi efetivamente assinado.

**Correção exigida:**
1. `MockAssinaturaA3Service.validar()` deve gravar **registro em `auditoria`** com `action="assinatura_a3.mock_usado"` + payload `{equipamento_id, versao_n, ambiente: settings.ENVIRONMENT}`. Esse registro vira **canário de regressão**: query `SELECT COUNT(*) FROM auditoria WHERE action='assinatura_a3.mock_usado' AND created_at > '<deploy_prod>'` em runbook pós-deploy precisa retornar 0. Hook `mock-in-production.sh` já existente cobre o caminho do código, mas **só código** — registros mock em audit complementam.
2. Adicionar teste anti-regressão: `test_mock_assinatura_grava_audit_canario_em_dev` + nota no plano (riscos §1) explicando o mecanismo.
3. Hash retornado pelo mock deve ser **diferente** de qualquer hash plausível de A3 real — formato `MOCK-A3-{uuid4}` + comprimento ≥36 chars, base64url puro **proibido**. Assim, busca regex em prod por hashes A3 que começam com `MOCK-A3-` revela mock vazado.
4. `LacunaWebPkiAssinaturaA3Service` stub deve **levantar `NotImplementedError`** (não retornar OK), garantindo que se settings.production apontar pra ele antes de Lacuna integrar, sistema falha alto e cedo. ADR-0009 pendente justifica.

### TL3. ALTA — Workflow `gestor_qualidade` + tabela `AprovacaoPendenteEquipamentoVersao` + Django admin + SLA D+7 é trabalho demais para Marco 2

**Problema:** T-EQP-024 + T-EQP-021 (caminho `motivo=outros`) entregam tabela nova, Django admin com botões aprovar/rejeitar, gravação de justificativa, **e** o plano (riscos §3) menciona "job de SLA D+7 que escala alerta P2". **Isso é uma feature completa** dentro de uma US que já tem trigger PG, A3 condicional, versionamento, snapshot JSONB, 15 testes.

Risco operacional: Marco 2 estoura prazo, ou pior — entrega tudo mas mal testado. O auditor de Qualidade vai cobrar cobertura ≥85% inclusive do workflow async, que precisa testar SLA D+7 (sem Procrastinate ativo, isso é management command + cron — débito que ninguém vai pagar).

**Correção exigida:**
1. **Fatiar:** mover `AprovacaoPendenteEquipamentoVersao` + Django admin + SLA D+7 para **US-EQP-002b** (sub-US, mesmo Marco 2, executada APÓS US-EQP-002 entregar). Plano US-EQP-002 termina em "retorna 202 com `aprovacao_pendente_id` + grava linha em `auditoria` com `action="equipamento.versionamento_aguardando_aprovacao"`".
2. Alternativa (se Roldão preferir uma US só): explicitar que SLA D+7 **não é entregue** em Marco 2 — apenas tabela + Django admin operacionalmente usáveis. Job de SLA fica para Wave B late (depende de Procrastinate). Documentar em non-goals.
3. Minha recomendação: **fatiar em US-EQP-002 + US-EQP-002b**. Mantém commits atômicos (princípio §7 AGENTS.md), reduz risco de Marco 2 escorregar, e permite que `advogado-saas-regulado` revise separadamente o texto PT da fila de aprovação (que é interface usuário-final).

### TL4. MÉDIA — Snapshot JSONB com Pydantic + GIN parcial: medir antes de criar índice

**Problema:** T-EQP-017 propõe Pydantic schema + UNIQUE `(equipamento_id, versao_n)`. PRD review C3 menciona GIN index. O plano **não** menciona GIN — está correto **se** o uso for "ler versão N do equipamento X" (B-tree composto resolve). Mas se Wave A virar a query "buscar todos equipamentos cujo snapshot teve `classe_exatidao='Classe I'` no passado", GIN seria necessário.

**Correção exigida:**
1. Adicionar nota explícita no plano: "GIN index em `snapshot_atributos_versionaveis` **NÃO** criado em Marco 2 — medir uso real primeiro. Adicionar via migration posterior apenas se query JSONB virar hot path em log de slow queries (>50 req/s no histórico).". Citar memória `feedback_nao_construir_codigo_descartavel`: índice criado prematuramente vira débito (recriação em tabela grande é custosa).
2. Pydantic schema deve validar **antes** do `to_dict()` que persiste no JSONB — não confiar em PG `jsonb` para schema. Validação acontece no use case (`application/`), não no model (camada `infrastructure/`).
3. Adicionar teste: `test_snapshot_pydantic_rejeita_campo_extra_estrito` (Pydantic v2 `model_config = ConfigDict(extra="forbid")`). Sem isso, agente futuro adiciona campo "ad-hoc" no snapshot e quebra leitura retroativa.

### TL5. MÉDIA — Enum `motivo_mudanca` fechado: política de evolução ausente

**Problema:** T-EQP-018 crava 6 valores enum (`correcao_cadastro_inicial`, `reparo_reclassificou`, `recalibracao_revelou_drift_permanente`, `troca_componente_principal`, `reidentificacao_fabricante`, `outros`). Bom porque limita superfície, **mas** o plano não responde: como adicionar um 7º valor no futuro? Duas escolhas com trade-offs muito diferentes:

- **(a) Migration nova com `ALTER TYPE ... ADD VALUE`** — global, todos tenants enxergam. Bom para regulação federal que muda lei.
- **(b) Tabela de catálogo `motivo_mudanca_catalogo` por tenant** — flexível, mas perde a garantia de "RBC B7 só aceita estes 6".

**Correção exigida:**
1. Decisão explícita no plano (riscos §5 novo): **opção (a)** — `ALTER TYPE` via migration revisada pelo subagente `consultor-rbc-iso17025`. Justificativa: RBC B7 é norma federal CGCRE; tenant não decide o que conta como "motivo válido de versionamento" em sistema regulado ISO 17025.
2. Documentar processo: "Para adicionar valor novo ao enum `motivo_mudanca`, abrir mini-ADR + revisão `consultor-rbc-iso17025` + migration `ALTER TYPE motivo_mudanca ADD VALUE '<novo>';`. Mudança aplica a todos tenants. Valor `outros` continua sendo escape válido até decisão regulatória."
3. Teste: `test_enum_motivo_mudanca_tem_exatamente_6_valores` (anti-regressão — se alguém adicionar sem ADR, teste quebra e força conversa).

### TL6. MÉDIA — Trigger PG `bloquear_update_imutaveis_pos_cert` + transação: ordem de avaliação

**Problema:** T-EQP-019 cria trigger BEFORE UPDATE em `equipamento`. Use case (T-EQP-021) faz lookup em Python via porta `CertificadoQueryService.equipamento_tem_certificado_emitido()` antes de decidir UPDATE direto vs versionamento. Existem **dois caminhos** que consultam o mesmo fato: aplicação (Python via porta) + banco (trigger via função SQL). Risco: race condition entre os dois — aplicação lê "não tem cert" → decide UPDATE direto → entre essa leitura e o UPDATE, certificado é emitido → trigger bloqueia o UPDATE.

**Correção exigida:**
1. Use case deve rodar dentro de `SELECT ... FOR UPDATE` na linha `equipamento` + ler `CertificadoQueryService` dentro da mesma transação. Trigger BEFORE UPDATE é defesa em profundidade — se disparar, retornar 409 "estado mudou durante operação, refaça".
2. Adicionar teste `test_race_condition_cert_emitido_durante_edit_retorna_409`: usar `transaction.atomic()` aninhada + savepoint para simular cert emitido entre leitura e UPDATE. Garantia: nunca corromper estado.
3. Documentar no plano (riscos novo §6): "Trigger PG é defesa em profundidade contra race; aplicação deve usar `FOR UPDATE`. Em condição de corrida, 409 é resposta esperada, não bug."

---

## Pontos fortes do plano

- Decisão C2 (incluir `cliente_atual_id_no_momento` no snapshot) bem fundamentada — separa "operacional" (transferência) de "versionável" (atributo técnico). Linha clara.
- Reusa hook `policy-test-coverage` para trigger PG (T-EQP-019) — exige happy+unhappy. Padrão consistente com F-A.
- Texto PT da resposta 422 imutável + 202 aguardando aprovação corretamente delegado ao `advogado-saas-regulado`.
- Non-goals explícitos (Lacuna real, UI HTMX gestor, VIEW real) — não tenta morder mais do que mastiga.
- Enum `motivo_mudanca` mapeia 1:1 para cláusulas RBC B7 (entrada `consultor-rbc-iso17025`).

---

## Hook `port-binding-validator` — cobertura de função SQL

Ressalva TL1 já cobre. Resumo da extensão necessária no hook (criação em US-EQP-001 T-EQP-016):

```bash
# Trecho conceitual — port-binding-validator.sh estendido
# Quando rodar com flag ENVIRONMENT=production:
psql -At -c "SELECT proname FROM pg_proc WHERE proname LIKE '%\_v0\_stub' OR proname LIKE '%\_stub';"
# Se retornar linhas → exit 1 (bloqueia release prod)
# Allow via: `# port-stub-allow: <funcao> -- <razão ≥30 chars>` em arquivo migration
```

Adicionar 2 casos ao `_test-runner.sh`: (1) stub presente + ENVIRONMENT=production → bloqueia; (2) stub presente + ENVIRONMENT=dev → passa.

---

## Recomendação operacional

1. Aplicar TL1, TL2, TL3 literalmente — bloqueiam `/tasks`.
2. TL4, TL5, TL6: adicionar notas explícitas nos riscos do plano + 3 testes citados. Não exigem reabertura de Story.
3. **Recomendação final do tech-lead: fatiar US-EQP-002 em duas (TL3) — entrega base + aprovação separadamente.** Reduz risco de Marco 2 estourar, mantém commits atômicos, permite revisão paralela.
4. Após `/implement`, rodar:
   - `auditor-seguranca`: foco em race condition trigger vs aplicação (TL6) + canário mock A3 (TL2).
   - `auditor-qualidade`: cobertura ≥85% inclusive ramos enum `motivo_mudanca` (TL5).
   - `auditor-produto`: validação texto PT do 202 "aguardando aprovação" (alinhado com advogado).

---

## Limites de honestidade

- **Confiante:** TL1, TL2, TL3, TL5 (estado real do projeto + hooks atuais + padrão F-A clientes já confirmado).
- **Suspeita não-provada:** TL6 — race condition trigger vs aplicação é teórica; em produção real com 50 clientes concorrentes pode escapar mesmo com `FOR UPDATE` se o adapter `CertificadoQueryService` real não estiver atomicamente coerente. Quando módulo certificados nascer, **re-revisar este ponto** com cicatriz de prod. Não substitui pentest externo.
- **Fora do meu alcance:** validação se enum `motivo_mudanca` cobre **todos** cenários CGCRE — escalar `consultor-rbc-iso17025` (já listado nos subagentes a consultar pelo plano). Texto PT da fila de aprovação gestor — escalar `advogado-saas-regulado`.
- **Sutileza de runtime:** `MockAssinaturaA3Service` em prod por engano (TL2) é cenário que IA-review **não pega sozinho**. Canário em audit + hook `mock-in-production` cobrem 80%; os outros 20% só drill cronometrado de deploy resolve.
