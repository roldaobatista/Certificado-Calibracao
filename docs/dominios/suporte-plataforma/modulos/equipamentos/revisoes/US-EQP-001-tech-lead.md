---
owner: tech-lead-saas-regulado (subagente)
revisado-em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-001
plano_revisado: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-001.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-EQP-001

## Resumo executivo

Plano sólido no fatiamento (T-EQP-001..015 estão bem desenhadas e quase todas ≤1 commit). A maioria do que importava arquiteturalmente já foi capturada no review de PRD anterior (INV-049/050/051, ports `Empty*`, snapshot RBC B4, allowlist QR). Aqui o parecer foca **só** no que o plano introduz de novo ou deixa ambíguo: escolha de PDF generator, localização do `KMS_qr_secret` em dev, naming/binding das portas stub, sintaxe da trigger PG anti-mutation, cadastro provisório e dois riscos cross-tenant não óbvios. **6 ressalvas** — duas BLOQUEADOR antes de `/tasks`, três CONCERN, uma NIT.

## Veredito

**APROVADO COM RESSALVAS** (2 BLOQUEADOR + 3 CONCERN + 1 NIT). Nenhuma exige reabrir a US.

---

## Ressalvas (ordem por gravidade)

### TL1. BLOQUEADOR — `KMS_qr_secret` em dev: localização errada no plano + falta hook anti-vazamento (INV-051)

**Problema:** o plano (T-EQP-007 + risco §1) propõe `settings.KMS_QR_SECRET = "dev-only-not-secret-rotate-in-prod"` lido de env var. Três problemas:

1. **Mora no lugar errado.** O segredo HMAC nunca pode ser uma constante de `settings/base.py` ou `settings/dev.py` — qualquer dev que abre `git log` ou rode `manage.py diffsettings` lê o valor. Padrão correto: `os.environ["KMS_QR_SECRET"]` lido em `src/infrastructure/equipamentos/qr_token.py` (lazy), com **fallback explícito apenas em DEBUG=True**, e `prod.py` exigindo `env("KMS_QR_SECRET")` sem default — exatamente o mesmo padrão de `DJANGO_SECRET_KEY` em `config/settings/base.py:29`.

2. **Falta entrada no `.env.example`** com comentário explicando rotação anual + obrigatoriedade de mover para AWS KMS MRK em prod. Sem isso, primeira pessoa que tentar `docker compose up` em dev nova quebra silenciosamente (HMAC com bytes vazios → tokens previsíveis).

3. **Hook `qr-hmac-check.sh` não existe e o plano remete vagamente.** O nome já está reservado no `REGRAS-INEGOCIAVEIS.md:91`, mas a especificação precisa estar no plano agora pra alguém implementar (e pra Auditor de Segurança bater contra).

**Correção exigida:**

- T-EQP-007 lê via `from django.conf import settings; settings.KMS_QR_SECRET` que vem de `env("KMS_QR_SECRET", default="DEV-ONLY-NOT-SECRET-USE-AWS-KMS-IN-PROD")` em `base.py`, e `prod.py` re-declara sem default. Warning estruturado no log toda vez que o módulo carrega com o valor default (uma vez por boot, não por request).
- Adicionar T-EQP-007b: criar `.claude/hooks/qr-hmac-check.sh` com 4 regras (bloqueia exit 2):
  - Bloqueia commit em `**/qr_token.py` se HMAC for chamado com argumento literal (`hmac.new(b"...")`) — força ler de settings.
  - Bloqueia commit em `config/settings/prod.py` se a string `DEV-ONLY-NOT-SECRET` aparecer.
  - Bloqueia commit em `qr_token.py` se função usa `hashlib.sha256` puro (sem HMAC) — algoritmo errado por descuido.
  - Bloqueia commit em `qr_token.py` se a string concatenada no HMAC não conter `tenant_id` (anti-regressão INV-051).
- Adicionar caso ao `_test-runner.sh` (passa de 103 → 107 testes de hook).
- Documentar no plano que rotação anual NÃO recomputa hashes existentes: validação consulta tabela `qrcode.hash` por igualdade (não rerun HMAC). Esse ponto já está em `qr-publico-allowlist.md §3` mas precisa aparecer no plano pra implementador não inverter.

### TL2. BLOQUEADOR — Cadastro provisório (cliente_id nullable) é gap conhecido — CORTAR de US-EQP-001 e cravar non-goal explícito

**Problema:** plano §riscos 5 diz "Decisão deferida". Isso vai virar feature creep. Hoje a story PRD não pede cadastro provisório; ela pede CRUD com `cliente_id` obrigatório. Deferir agora significa:

- Modelo nasce com `cliente_atual_id = ForeignKey(Cliente, null=True)` "preventivamente" — e nunca mais sai. Acabamos com banco produção tendo equipamento sem dono, INV-050 enfraquecida.
- OU modelo nasce NOT NULL e quando US-EQP-006 chegar (Wave A late) a migration vai precisar relaxar — e migration que vai de NOT NULL para nullable em tabela populada é cara em PG (rewrite ou online-schema-change).

**Recomendação técnica:** US-EQP-001 entrega `cliente_atual_id` **NOT NULL**. Cadastro provisório é variação que US-EQP-006 entrega via tabela separada `EquipamentoRecebimento` (estado pré-cadastro) que, ao virar `Equipamento`, exige `cliente_atual_id` resolvido. Estado intermediário NÃO vai para `equipamento` direto. Padrão análogo ao usado em fiscal NFS-e (rascunho vive em outra tabela).

**Correção exigida:**

- Adicionar non-goal explícito: "NÃO suportar `cliente_atual_id = NULL`. Cadastro provisório é US-EQP-006, em tabela separada."
- Modelo nasce com `cliente_atual_id = ForeignKey(Cliente, on_delete=PROTECT, null=False)`.
- Remover ambiguidade do risco §5.

### TL3. CONCERN ALTA — Estrutura `Empty*` adapter + binding: especificar naming + onde registra

**Problema:** plano (T-EQP-009/010) propõe `EmptyCertificadoQueryService` em `src/infrastructure/equipamentos/adapters/` e diz "registro em `settings.PORT_BINDINGS`". Hoje `PORT_BINDINGS` **não existe** em nenhum settings (grep confirmou: aparece só em docs). Sem decisão concreta agora, dois agentes diferentes vão inventar dois padrões diferentes — esse erro já aconteceu com o `ClienteRepository` (que acabou sem registro central; cada use case importa direto o adapter Django).

**Recomendação técnica:**

- **Naming:** `Empty<NomePort>Adapter` (não `Empty<NomePort>Service` — o `Service` já está no nome da porta). Ex: `EmptyCertificadoQueryAdapter`. Consistente com naming `*Adapter` que o ADR-0007 já usa.
- **Localização:** `src/infrastructure/equipamentos/adapters/empty_certificado_query.py` — singular, `_adapter` é redundante no nome do arquivo já dentro de `adapters/`.
- **Registro:** criar em `config/settings/base.py` um dict `PORT_BINDINGS` com formato:
  ```python
  PORT_BINDINGS = {
      "CertificadoQueryService": "src.infrastructure.equipamentos.adapters.empty_certificado_query.EmptyCertificadoQueryAdapter",
      "OSQueryService": "src.infrastructure.equipamentos.adapters.empty_os_query.EmptyOSQueryAdapter",
  }
  ```
- **Resolver:** uma função `resolve_port(name: str)` em `src/infrastructure/shared/port_registry.py` usando `django.utils.module_loading.import_string`. Use cases pedem `resolve_port("CertificadoQueryService")` — nunca importam adapter direto.
- **Hook `port-binding-validator.sh`** (já no §91 do REGRAS-INEGOCIAVEIS): bloqueia `prod.py` se algum binding apontar para classe `Empty*`. Hook fica para Wave A Marco 2; já registra no plano.

**Correção exigida:** atualizar T-EQP-009/010 com naming concreto + adicionar T-EQP-009b "criar `port_registry.py` + entrada em `PORT_BINDINGS` em `base.py`". Sem isso, o binding fica como instrução vaga.

### TL4. CONCERN ALTA — Trigger PG `bloquear_update_perfil_tenant_snapshot`: sintaxe + tests-coverage no commit

**Problema:** plano (T-EQP-004) cita trigger mas não dá sintaxe. Hook `policy-test-coverage.sh` exige `# tests-coverage:` em migrations que criam policy RLS — mas o hook **não exige** isso para triggers de imutabilidade. Resultado: migration sobe com trigger que ninguém testa, e o `audit-immutability-check.sh` só pega `auditoria_anti_*` — não pega triggers de equipamento.

**Sintaxe recomendada para T-EQP-004:**

```sql
CREATE OR REPLACE FUNCTION equipamento_bloquear_update_perfil_snapshot()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.perfil_tenant_no_momento_cadastro IS DISTINCT FROM OLD.perfil_tenant_no_momento_cadastro THEN
        RAISE EXCEPTION 'INV-049/RBC-B4: perfil_tenant_no_momento_cadastro é imutável após criação (equipamento_id=%)', OLD.id
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER equipamento_anti_update_perfil_snapshot
    BEFORE UPDATE ON equipamento
    FOR EACH ROW
    EXECUTE FUNCTION equipamento_bloquear_update_perfil_snapshot();
```

**Pontos sensíveis:**

- `IS DISTINCT FROM` (não `<>`) — `<>` com NULL retorna NULL e silenciosamente passa. Aqui o campo é NOT NULL pela INV-049, mas defesa em profundidade.
- `ERRCODE = 'check_violation'` (SQLSTATE 23514) — permite que o adapter Django identifique a violação especificamente (`psycopg.errors.CheckViolation`) e converta para 422 com mensagem PT-BR clara. Sem ERRCODE, vira `IntegrityError` genérico.
- Naming `equipamento_anti_update_*` (lowercase + `anti_*` prefix) — coerente com a convenção que o `audit-immutability-check.sh` já protege para `auditoria_anti_*`. Permite estender o hook para barrar `DROP TRIGGER equipamento_anti_*` no mesmo padrão.

**Correção exigida:**

1. Plano cita sintaxe completa em T-EQP-004 (inclusive ERRCODE).
2. Migration tem comentário `# trigger-coverage: tests/equipamentos/test_perfil_snapshot_imutavel.py::test_update_perfil_rejeita_check_violation` apontando teste happy+unhappy.
3. Estender `audit-immutability-check.sh` (T-EQP-016 — já planejado) para barrar `DROP TRIGGER equipamento_anti_*` E `ALTER TABLE equipamento DISABLE TRIGGER ALL`.
4. Teste deve verificar `psycopg.errors.CheckViolation` (não `IntegrityError` genérico) — senão se alguém trocar para ERRCODE diferente o teste continua passando errado.

### TL5. CONCERN MÉDIA — PDF generator: recomendação WeasyPrint, com 2 condições

**Decisão técnica solicitada.** Comparativo pragmático para a etiqueta US-EQP-001 (T-EQP-014) **e** o certificado ISO 17025 que vai chegar em outro módulo:

| Critério | ReportLab | WeasyPrint |
|---|---|---|
| Etiqueta simples (QR + 3 campos) | ✅ direto | ✅ HTML+CSS |
| Certificado complexo (tabela calibração) | 🔴 código procedural | ✅ Django template reuso |
| Dev experience pra agente IA | ⚠️ API procedural extensa | ✅ HTML que ele já sabe |
| Deps no container | leve | gtk/pango (~80MB) |
| Determinismo byte-a-byte (LTV/audit) | ✅ | ⚠️ depende da versão do pango |
| Velocidade (etiqueta única) | 50ms | 300ms |
| Velocidade (lote 100 etiquetas) | 5s | 30s |

**Minha recomendação: WeasyPrint** para etiqueta **e** certificado, por 2 motivos:

1. **Reaproveitamento na Wave A:** o certificado de calibração (módulo `certificados`, Wave A late) é o documento crítico do produto, terá tabelas + variáveis + branding por tenant. Em ReportLab cada um é ~500 linhas de Python procedural; em WeasyPrint é template HTML que o agente IA gera bem. Investir em ReportLab agora só para a etiqueta paga em deuda quando o certificado chegar.

2. **A3 assina PDF, não gera PDF.** Determinismo byte-a-byte é exigência da assinatura PAdES-LTV, mas isso é resolvido fixando versões (`weasyprint==62.x`, `pango==1.54.x`) no `pyproject.toml` + testes de regressão por hash. Não é razão para escolher ReportLab.

**Condições não-negociáveis para WeasyPrint:**

- (a) `Dockerfile` já instala `libpango-1.0-0 libpangoft2-1.0-0` (validar antes de cravar — risco de imagem 80MB maior).
- (b) Teste de regressão por hash SHA-256 do PDF gerado com fixture controlada (`tests/equipamentos/test_pdf_etiqueta.py::test_hash_estavel_versao_weasyprint`). Se uma atualização do WeasyPrint mudar 1 byte, teste falha → ponto de revisão consciente (não silêncio).

**Correção exigida:** T-EQP-014 declara WeasyPrint + as 2 condições; testes incluem o de hash estável.

### TL6. NIT — Action `equipamento.imprimir_etiqueta` proposta em T-EQP-013 mas não aparece em endpoint

**Problema mínimo:** o seed de actions inclui `equipamento.imprimir_etiqueta`, mas o único endpoint que gera PDF é `GET /v1/equipamentos/{id}/qr` (T-EQP-014), que provavelmente vai casar com `equipamento.ler`. Action órfã agora vira papel sem uso e auditor pergunta "para que serve?".

**Correção:** ou (a) o endpoint `GET /qr` verifica `equipamento.imprimir_etiqueta` (não `.ler`) — mais correto, porque imprimir etiqueta é ação distinta de visualizar (operacionalmente, almoxarife pode ter ler mas não imprimir), OU (b) remove a action do seed e adiciona quando US-EQP-002 trouxer impressão em lote. Recomendo (a) — mantém o seed minimalista e usa action já criada.

---

## Riscos cross-tenant não óbvios (defesa em profundidade)

### R-DEF-1. T-EQP-007 `gerar_hash_qr` recebe `tenant_id` como argumento

Olhei a assinatura proposta: `gerar_hash_qr(equipamento_id, tenant_id, emitido_em)`. Risco: caller passa errado o `tenant_id` (ex: usa `equipamento.cliente_atual.tenant_id` em vez de `equipamento.tenant_id`). Defesa: a função deve **buscar internamente** o `tenant_id` a partir do `equipamento_id` (consulta Django ORM com `active_tenant_context`), nunca confiar em argumento externo. Custo: 1 query a mais. Ganho: impossível chamar errado.

Padrão análogo ao que `clientes/views.py:_hashear_pii` faz — recebe `tenant_id`, mas o call site é sempre `_active_tenant_obrigatorio()`. Em `gerar_hash_qr` o ideal é nem aceitar `tenant_id` como argumento — derivar internamente.

### R-DEF-2. Teste `test_tag_duplicada_cross_tenant_nao_vaza` (T-EQP-015)

O plano lista o teste mas não diz a forma. Inspirado na ressalva 1 do review US-CLI-001: garantir que o teste cria tenant A com TAG=X (commit), depois tenant B tenta criar TAG=X — **esperado 201 (não 409)**, porque a unicidade é `(tenant_id, tag)`. Se algum agente futuro trocar UNIQUE composto por `unique=True` em `tag`, esse teste explode. Especificar isso no plano evita teste cosmético "201 OR 409, qualquer dos dois".

### R-DEF-3. `_hashear_pii` em `cliente_id_original_hash` do audit precisa de sal por tenant

Plano T-EQP-011 grava `equipamento.cadastrado` com `cliente_id_original_hash`. Hoje, `cliente_id` é UUID (já não é PII direta), mas o hook `audit-pii-salt-check.sh` é conservador e pode bloquear se o agente escrever `hashlib.sha256(cliente_id.bytes).hexdigest()`. Solução correta: usar o helper `hashear_pii_com_salt_tenant` que já existe em `audit/services.py`. Plano deve referenciar esse helper explicitamente em T-EQP-011 para o agente implementador não inventar wrapper local.

---

## Pontos fortes do plano

- Fatiamento T-EQP-001..015 está em granularidade de commit — bom.
- Reconhecimento explícito de portas stub (T-EQP-009/010) ao invés de hard-deps a módulos inexistentes — correto.
- Aproveitamento dos hooks ativos (`tenant-id-validator`, `authz-check`, `migration-rls-check`, `audit-pii-salt-check`) confirmado caso a caso.
- Lista de 12 testes T-EQP-015 já cobre happy + unhappy + cross-tenant — ponto alto vs plano US-CLI-001 que precisou ser corrigido para incluir cross-tenant.
- INV-EQP-LOC-001 (anti-PII em `localizacao_fisica`) tratada com regex reutilizado de US-CLI-004 — boa hygiene de código.

---

## Recomendação operacional

1. Aplicar as 6 ressalvas no plano (sobretudo TL1 e TL2 — bloqueantes para `/tasks`).
2. **Não re-revisar** se as 6 forem aplicadas literalmente.
3. Após `/implement`:
   - Auditor de Segurança: foco em INV-051 + KMS_qr_secret + rate-limit por IP + audit sem PII em claro.
   - Auditor de Qualidade: cobertura ≥85% no módulo equipamentos + teste do hash WeasyPrint determinístico.
   - Auditor de Produto: validar que cadastro provisório fica fora dessa US (não criar débito implícito).

---

## Limites de honestidade

- **Confiante:** TL1 (KMS_qr_secret), TL2 (cadastro provisório), TL3 (PORT_BINDINGS), TL4 (sintaxe trigger), TL6 (action órfã) — verifiquei os arquivos reais (`settings/base.py`, `REGRAS-INEGOCIAVEIS.md`, hooks).
- **Recomendação técnica forte mas com condição:** TL5 (WeasyPrint) — recomendação depende do `Dockerfile` aceitar gtk/pango sem brigar. Pedir ao implementador validar `docker compose build` antes de cravar.
- **Fora do meu alcance:**
  - Performance real do WeasyPrint em lote de 1000 etiquetas (sem cicatriz de produção; vale medir antes de cravar) — recomendo benchmark explícito antes de Wave A late.
  - Se o agente de implementação vai conseguir produzir HTML+CSS para o certificado ISO 17025 sem oscilar — risco de IA gerar CSS quebrado em edge cases (margens em página > 1, page-break dentro de tabela). Eu suspeito que vai precisar de 2-3 iterações com auditor de Qualidade; não é bloqueador agora.
