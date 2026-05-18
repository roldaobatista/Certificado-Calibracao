---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-EQP-001
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-001.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-EQP-001 (LGPD + contratos)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Antes do go-live público envolvendo QR Code físico aberto e fotos de equipamento (US-EQP-001 + irmãs), advogado humano OAB ativa precisa revisar (i) as mensagens UX PT-BR que vão a milhares de titulares e (ii) o DPA tenant↔Aferê. Para este parecer, o foco está em **garantir que o cadastro inicial e o evento de audit não contaminem nem vazem PII**.

---

## Sumário (≤150 palavras)

**APROVADO COM RESSALVAS (R1–R5).** US-EQP-001 está juridicamente sólida na arquitetura (INV-EQP-LOC-001, RAT-EQP-FOTO, qr-publico-allowlist e B1/B5 do parecer do PRD já cravados). Cinco ajustes finos antes do code-complete: (R1) **texto exato PT-BR** da rejeição anti-PII de `localizacao_fisica` (faltava na US — só havia placeholder); (R2) **sanitização do payload** `equipamento.cadastrado` — declarar campo-a-campo o que entra em claro vs hash salgado, evitando regredir o que clientes Marco 1 já decidiu; (R3) **base legal explícita** para `cliente_id_original_hash` (operador agindo sob instrução documentada do controlador — art. 7º V c/c art. 39 LGPD); (R4) **NÃO há aceite LGPD no cadastro de equipamento** — equipamento é bem móvel, não titular; aceite já foi colhido em US-CLI-001 do cliente vinculado, com texto justificativo pronto pra colar; (R5) **mensagem 409 TAG duplicada** não pode vazar dado de outro equipamento (oracle).

---

## Veredito

**APROVADO COM RESSALVAS.** O plano US-EQP-001 herda corretamente os bloqueadores do parecer de PRD (B1–B5) e os transforma em tasks (T-EQP-006 PII guard, T-EQP-007 HMAC, T-EQP-011 audit sanitizado). As ressalvas abaixo são preenchimento de texto e declaração explícita de base legal — não há furo arquitetural.

### Ressalvas (R1–R5)

#### R1 — Texto PT-BR da rejeição anti-PII em `localizacao_fisica` (CONCERN)

**Estado atual:** AC-EQP-001-4 diz "retorna 400 (INV-EQP-LOC-001) com texto orientando a remover", mas não fixa o texto. T-EQP-006 cita reuso de `pii_guard` do US-CLI-004 sem cravar o copy. Sem texto, cada implementador vai inventar — risco de mensagem que **vaza qual dado foi detectado** (ex.: "encontrei o CPF 123.456.789-00 no campo") ou que **culpa o atendente** ("você não pode escrever isso aqui").

**Por que jurídico se importa:** mensagem de erro é interface com titular indireto (o atendente do tenant). Mensagem clara reduz workaround do atendente (cadastrar PII em outro campo livre — risco LGPD art. 6º V qualidade). Mensagem que ecoa o input pode ela mesma virar log com PII (se o atendente colar a tela no chat de suporte).

**Texto sugerido — pronto pra colar (mensagem do response 400, idêntica à do US-CLI-004 R2 para consistência):**

```json
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "code": "localizacao_fisica_pii_detectada",
  "campo": "localizacao_fisica",
  "mensagem": "Identifiquei dados pessoais no texto da localização (CPF, CNPJ, e-mail, telefone ou nome de pessoa). Reescreva descrevendo apenas o local físico do equipamento — por exemplo: \"Almoxarifado A — prateleira 3\" ou \"Laboratório de qualidade — bancada 2\". Os dados do cliente já estão no cadastro dele e aparecem automaticamente na ficha do equipamento.",
  "exemplos_validos": [
    "Almoxarifado A — prateleira 3",
    "Laboratório de qualidade — bancada 2",
    "Setor de envase — linha 4"
  ]
}
```

**Regras invioláveis do texto:**
1. **NÃO ecoar o input recebido.** Não dizer "o texto 'João Silva 123.456.789-00' contém CPF" — apenas a **categoria detectada**.
2. **NÃO listar quais categorias foram detectadas individualmente** (ex.: "detectei CPF E telefone"). Risco: vira oracle de validador externo pra confirmar formato. Listar **a união** ("CPF, CNPJ, e-mail, telefone ou nome de pessoa") sem dizer qual disparou.
3. **NÃO culpar o atendente** ("você não pode escrever isso") — usar primeira pessoa ("identifiquei") + ofereçer alternativa válida.
4. **Exemplos PT-BR neutros** — sem CPF, sem nomes próprios, sem endereços reais nos exemplos retornados pela API (já estão no copy E2 do PRD-advogado §E2).

**Task:** complementar T-EQP-006 com fixture `tests/equipamentos/fixtures/pii_guard_messages.py` cravando o texto acima como constante — qualquer mudança do copy passa por revisão de advogado. Hook `anti-mascaramento` já existe pra evitar skip do teste.

#### R2 — Sanitização do payload `equipamento.cadastrado` (BLOQUEADOR)

**Estado atual:** T-EQP-011 diz "gravar audit `equipamento.cadastrado` com payload `{equipamento_id, tag, cliente_id_original_hash, perfil_tenant_no_momento_cadastro}`". Está **quase certo, mas incompleto** — não declara o que NÃO entra, nem trata 4 campos que o atendente preenche e que tendem a vazar pra audit se não houver gate explícito.

**Catálogo definitivo do payload `equipamento.cadastrado` (assinatura final, sob INV-013 + INV-AUDIT-PII):**

| Campo | Entra em claro? | Hash salgado por tenant? | Justificativa |
|---|---|---|---|
| `tipo_evento` = "equipamento.cadastrado" | ✅ claro | n/a | metadado obrigatório |
| `event_id` (UUIDv7) | ✅ claro | n/a | metadado obrigatório |
| `tenant_id` (UUID) | ✅ claro | n/a | INV-013, opaco |
| `usuario_id` (UUID) | ✅ claro | n/a | INV-013, opaco |
| `equipamento_id` (UUID) | ✅ claro | n/a | opaco, sem PII |
| `tag` | ⚠️ ver decisão | sim, `tag_hash` | **decisão: hash salgado.** TAG é definido pelo tenant; pode conter padrão revelador ("BLS-CLIENTE-EUROFARMA-001"). Em scan público a TAG não aparece (INV-051 allowlist B3). Em audit, fica como `tag_hash = sha256(tag + salt_tenant)`. Reconstrução só com banco operacional + salt — controlador (tenant) consegue, admin Aferê não |
| `cliente_id_original` (UUID) | ❌ **NÃO** | n/a | mantém-se no banco operacional, audit recebe só o hash. FK morre quando cliente é crypto-shredded |
| `cliente_id_original_hash` (bytes 32) | ✅ claro (já é hash) | já é hash salgado | mesmo salt do hash de PII do cliente (modelo-dominio §28); sobrevive ao crypto-shredding LGPD art. 18 VI; rastreabilidade ISO 17025 cl. 8.4 |
| `numero_serie` | ❌ **NÃO** | sim, `numero_serie_hash` | NS pode revelar lote/data de fabricação; em scan público nunca aparece; em audit fica hashado |
| `fabricante` | ✅ claro | n/a | dado público de catálogo (Mettler, Toledo, Mitutoyo); não PII |
| `modelo` | ✅ claro | n/a | dado público de catálogo |
| `localizacao_fisica` | ❌ **NUNCA** | sim, `localizacao_fisica_hash` | mesmo após passar pelo PII guard (INV-EQP-LOC-001), pode vazar `"galpão da Eurofarma SP"` que isolado parece neutro mas combinado com `tenant_id` vira reidentificável. Hash salgado preserva auditabilidade ("mudou de local entre evento X e Y") sem expor conteúdo |
| `perfil_tenant_no_momento_cadastro` | ✅ claro | n/a | enum {A,B,C,D}, não PII (RBC B4) |
| `qrcode_hash` (HMAC) | ✅ claro | n/a | é hash por design (INV-051) |
| `causation_id` | ✅ claro | n/a | UUID, sem PII |
| `correlation_id` | ✅ claro | n/a | UUID, sem PII |
| `ip_hash` (do request HTTP) | ✅ claro (já é hash) | sim, `sha256(ip + salt_tenant)` | espelho US-CLI-001 |
| `user_agent_hash` | ✅ claro (já é hash) | sim | espelho US-CLI-001 |
| `created_at` | ✅ claro | n/a | timestamp UTC |

**Task obrigatória:** T-EQP-011 deve receber sub-task `T-EQP-011a — teste de regressão anti-vazamento do payload audit`:

```python
# tests/equipamentos/test_audit_payload_sanitizado.py
def test_evento_equipamento_cadastrado_nao_contem_pii_cru():
    # cadastra equipamento com TAG = "BLS-CLIENTE-EUROFARMA-001",
    # NS = "MT-2024-789456", localizacao = "Lab Q — bancada 2"
    payload_serializado = json.dumps(evento.payload, ensure_ascii=False)
    # nenhum campo bruto deve aparecer
    assert "EUROFARMA" not in payload_serializado
    assert "MT-2024-789456" not in payload_serializado
    assert "bancada" not in payload_serializado
    # hashes devem aparecer e ter shape correto
    assert evento.payload["tag_hash"].startswith("sha256:")
    assert evento.payload["numero_serie_hash"].startswith("sha256:")
    assert evento.payload["localizacao_fisica_hash"].startswith("sha256:")
    # ip e ua já hashados
    assert evento.payload["ip_hash"].startswith("sha256:")
    # campos opacos por design entram em claro
    assert UUID(evento.payload["equipamento_id"])
    assert evento.payload["perfil_tenant_no_momento_cadastro"] in {"A","B","C","D"}
```

Hook `audit-pii-salt-check` já listado em T-EQP-015 cobre o cenário do `cliente_id_original_hash`. Estender o hook (ou o `INV-checker`) pra também olhar `tag_hash`, `numero_serie_hash`, `localizacao_fisica_hash`.

#### R3 — Base legal de `cliente_id_original_hash` precisa ser declarada explicitamente (CONCERN)

**Estado atual:** modelo-de-dominio §22 cita o campo, US descreve uso, mas não há um único parágrafo na US-EQP-001 dizendo **sob qual artigo da LGPD esse hash existe**. Em auditoria ANPD, "por que vocês mantêm referência cifrada do cliente após ele exercer art. 18 VI?" exige resposta documentada.

**Texto pronto pra colar — seção nova "Base legal" do US-EQP-001 (após "Resumo", antes de "Sequência de tasks"):**

> **Base legal LGPD (art. 7º + art. 11 + art. 16):**
>
> O cadastro de equipamento e o evento de audit `equipamento.cadastrado` são realizados pela CONTRATADA (Aferê) na qualidade de **operadora** (LGPD art. 5º VII), sob **instrução documentada** (art. 39) do CONTRATANTE (tenant), que é o **controlador** (art. 5º VI). As bases legais aplicáveis a cada finalidade são:
>
> 1. **Cadastro do equipamento e vínculo ao cliente final** — art. 7º V (execução de contrato comercial tenant↔cliente final, no qual o equipamento é objeto da prestação).
> 2. **Geração de QR Code e impressão de etiqueta** — art. 7º V (identificação operacional do ativo); art. 7º III só se aplica ao endpoint público anônimo `/v1/qr/{hash}` (interesse legítimo restrito a mensagem genérica, sem PII — INV-EQP-QR-001).
> 3. **Snapshot `perfil_tenant_no_momento_cadastro`** — art. 7º II (obrigação regulatória RBC/NIT-DICLA-005) cumulada com art. 16 I (retenção pra cumprir obrigação legal).
> 4. **`cliente_id_original_hash` (rastreabilidade pós-crypto-shredding)** — art. 7º II c/c art. 16 I: ISO/IEC 17025 cl. 8.4 (registros técnicos imutáveis ~25 anos) é obrigação regulatória que **prevalece** sobre direito ao esquecimento (art. 18 VI), nos termos do art. 16 I. O hash salgado por tenant **não é PII reidentificável fora do banco do controlador** — admin Aferê não tem o salt; após crypto-shredding do cliente original, o hash perdeu o referente. Conformidade simultânea com cl. 8.4 e art. 18 VI sem manter PII bruta.
> 5. **Foto do equipamento (se anexada nesta US ou em US irmã)** — art. 7º V para registro técnico do ativo; se capturar pessoa identificável, vira art. 11 § 4º (dado sensível) e exige consentimento OU anonimização pelo tenant-controlador (RAT-EQP-FOTO).
>
> A CONTRATADA **não escolhe** a base legal — apenas executa a configuração documentada pelo CONTRATANTE no DPA e no fluxo do produto. Eventual auditoria ANPD deve ser endereçada ao tenant-controlador; a CONTRATADA fornece audit trail e ferramentas (INV-013, art. 37 LGPD).

#### R4 — NÃO há aceite LGPD no cadastro de equipamento — declarar e justificar (NIT)

**Pergunta da spec:** "Aceite LGPD necessário no cadastro de equipamento? (Espelho US-CLI-001 R1/R3)".

**Resposta jurídica curta:** **NÃO.** Equipamento é **bem móvel** (CC art. 82), não pessoa. LGPD art. 1º cobre exclusivamente "tratamento de dados pessoais", entendidos como "informação relacionada a pessoa natural identificada ou identificável" (art. 5º I). Uma balança/paquímetro/termômetro não é titular de direitos.

**Por que mesmo assim a pergunta merece resposta na US (e não só no parecer):**

O cadastro do equipamento **carrega referência** a um cliente (PF ou PJ com PF associada) **já cadastrado** em US-CLI-001 — e foi **naquele** cadastro que o aceite LGPD do titular foi colhido (ou dispensado, no caso de PJ pura, conforme US-CLI-001 R3). O vínculo `equipamento.cliente_atual_id` **não cria** novo tratamento de PII além do que o aceite original já cobre (finalidade "execução de contrato comercial tenant↔cliente final" — art. 7º V).

**Sub-casos a tratar explicitamente:**

- ✅ Cliente PF com aceite colhido em US-CLI-001 — vínculo equipamento não exige novo aceite.
- ✅ Cliente PJ com PF associada (sócio/contato) com aceite colhido em US-CLI-001 — vínculo equipamento não exige novo aceite.
- ✅ Cliente PJ pura (sem PF associada, `aceite_lgpd_dispensa_motivo = "pj_sem_pf_associada"`) — vínculo equipamento confirma a dispensa; segue art. 1º LGPD (fora do âmbito).
- ⚠️ **Foto do equipamento que capturar rosto** — aí sim vira art. 11 § 4º (sensível); aceite/anonimização é responsabilidade do **tenant** (controlador do tratamento incidental), conforme RAT-EQP-FOTO já cravado no parecer do PRD §B4. Esta US não entra no fluxo de foto.
- ⚠️ Cadastro provisório com `cliente_id IS NULL` (US-EQP-006, fora do escopo) — não há referência a PII, dispensa LGPD; quando o cliente for posteriormente vinculado, o aceite preexistente em US-CLI-001 cobre.

**Texto pronto pra colar — adicionar como "Non-goal jurídico" no plano:**

> **Aceite LGPD no cadastro de equipamento (não aplicável):** equipamento é bem móvel (CC art. 82) e está fora do âmbito da LGPD (art. 1º). O aceite do titular (cliente PF ou PF associada a PJ) foi colhido em US-CLI-001 e cobre todas as finalidades de operação derivadas do contrato comercial — cadastro de equipamento, emissão de OS, certificado, NF-e. Caso a US futura US-EQP-001-foto introduza captura fotográfica, RAT-EQP-FOTO disciplina o tratamento incidental de imagem (art. 11 § 4º), com o tenant como controlador desse tratamento.

#### R5 — Mensagem 409 TAG duplicada não pode vazar info de outro equipamento (CONCERN)

**Estado atual:** AC-EQP-001-3 diz "retorna 409 com mensagem 'TAG já existe — escolha outra'". Texto curto **está correto na intenção** mas precisa ser cravado e testado para não regredir.

**Riscos de vazamento se mensagem for "ajudada" por implementador bem-intencionado:**

1. **"TAG já existe no equipamento BLS-2026-000123"** — vaza outra TAG (e indiretamente revela o histórico de numeração do tenant).
2. **"TAG já existe — pertence ao cliente Eurofarma SP"** — vaza vínculo cliente-equipamento (PII por associação).
3. **"TAG já existe (criada em 2024-03-15)"** — vaza timeline do tenant.
4. **Cross-tenant:** retornar 409 quando a TAG existe **em outro tenant** = oracle de enumeração. Mesmo princípio do US-CLI-001 (CPF/CNPJ não-duplicado cross-tenant) e do AC-EQP-003-4 (QR revogado indistinguível de hash de outro tenant).

**Regras invioláveis da resposta 409:**

```json
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "code": "tag_ja_em_uso",
  "campo": "tag",
  "mensagem": "Esta TAG já está em uso por outro equipamento da sua empresa. Escolha uma identificação diferente.",
  "sugestao": null
}
```

**Sub-regras:**

1. **Apenas dentro do mesmo tenant** o 409 é retornado (INV-049 é por tenant). TAG duplicada cross-tenant retorna **201 Created** normalmente — não revela existência em outro tenant.
2. **NÃO ecoar a TAG submetida** no corpo da resposta. Se o atendente submeteu "BLS-2026-000123", a resposta NÃO repete a string — só identifica o campo (`"campo": "tag"`). Razão: log de erro do navegador pode ser compartilhado em suporte; ecoar input vira PII se a TAG codificar nome de cliente.
3. **NÃO sugerir próxima TAG livre.** Sugestão automática (`"sugestao": "BLS-2026-000124"`) revela sequência de numeração do tenant a quem submeteu TAG aleatória — vetor de enumeração.
4. **Audit do 409:** registrar `equipamento.cadastro_recusado` com `motivo_categoria = "tag_duplicada"`, **sem** a string da TAG submetida; só `tag_hash`.

**Task obrigatória:** complementar T-EQP-015 com `test_409_tag_duplicada_nao_ecoa_tag_submetida` + `test_tag_duplicada_cross_tenant_nao_retorna_409` (este último já listado, mas reforçar que retorno é 201, não 422/404).

---

## Não-ressalvas (validadas como corretas)

- ✅ **`cliente_id_original_hash` salgado por tenant** — design correto, base legal explicitada em R3, sobrevive a crypto-shredding sem violar art. 18 VI nem cl. 8.4.
- ✅ **PII guard reutilizado de `pii_guard.py`** — espelho US-CLI-004/005 R2; mesmo regex, mesma fixture de exemplos válidos.
- ✅ **`perfil_tenant_no_momento_cadastro` imutável via trigger PG** — enum {A,B,C,D}, não PII; RBC B4 cumprido.
- ✅ **QR Code com HMAC + KMS_qr_secret + endpoint público com allowlist** — RAT-EQP-QR-001 já cravada via parecer PRD §B3; US-EQP-003 trata o endpoint público em detalhe (este parecer não duplica).
- ✅ **`localizacao_fisica` ≤200 chars com PII guard** — INV-EQP-LOC-001 cravada.
- ✅ **Audit `equipamento.cadastrado` em `auditoria.eventos`** — INV-013 + WORM B2 herdados da F-A. Sanitização detalhada em R2.

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Implementador "ajuda" usuário ecoando TAG submetida no 409 — vira oracle | Alta sem R5 | NC LGPD (PII por associação) + enumeração | R5 — texto cravado em fixture + 2 testes obrigatórios |
| Audit `equipamento.cadastrado` grava TAG/NS/localização em claro — bloqueia crypto-shredding em 2031 | Alta sem R2 | NC LGPD art. 18 VI + retenção residual ilegal | R2 — payload sanitizado + hash salgado + teste regressão + hook estendido |
| Mensagem PT-BR da rejeição PII ecoa input recebido | Média sem R1 | Log com PII + atendente cola tela em suporte | R1 — texto cravado em fixture; teste verifica que resposta não contém substring do input |
| Atendente força workaround colocando PII em `descricao` ou outro campo livre | Média | NC LGPD art. 6º V (qualidade) | Reuso do `pii_guard` em todos os campos livres (já em T-EQP-006); copy E2 do PRD-advogado orientando |
| ANPD pergunta base legal do hash pós-shredding e não há resposta documentada | Baixa | Multa potencial + atraso em resposta ANPD | R3 — seção "Base legal" cravada no plano com 5 itens |
| Implementador entende que precisa de "aceite LGPD do equipamento" e bloqueia fluxo desnecessariamente | Média | Atrito UX + atraso no Marco 2 | R4 — Non-goal jurídico explícito; equipamento é bem móvel |

---

## Próximos passos

- ✅ Aplicar R1–R5 no plano `US-EQP-001.md` (autoria: implementador) **antes** de promover a `stable`.
- ✅ Criar fixture `tests/equipamentos/fixtures/pii_guard_messages.py` com texto do response 400 (R1).
- ✅ Adicionar sub-task `T-EQP-011a` (teste de regressão anti-vazamento do payload audit) na sequência (R2).
- ✅ Adicionar seção "Base legal" no plano (R3) — texto pronto pra colar acima.
- ✅ Adicionar Non-goal jurídico "Aceite LGPD no cadastro de equipamento" (R4).
- ✅ Cravar fixture do response 409 + 2 testes adicionais (R5).
- ⚠️ **Antes do go-live público do Aferê** (não MVP-1 dogfooding): texto do response 400 (R1), 409 (R5), e a seção "Base legal" (R3) PRECISAM revisão de advogado humano com OAB ativa porque serão exibidos a milhares de titulares indiretos e fundamentam resposta a ANPD. Recomendo contratar consulta pontual com advogado especialista em LGPD + ICP-Brasil (perfil: 5+ anos LGPD operador-controlador, familiar com ISO 17025/CGCRE); preparei este parecer + parecer-PRD-equipamentos + RAT-EQP-FOTO + qr-publico-allowlist pra otimizar o tempo dele/dela (estimado 1.5–2h de revisão).
- ⏳ Diferido pra US-EQP-002+: imutabilidade de TAG/NS/fabricante pós-cert (INV-025 — fora do escopo desta US).
- ⏳ Diferido pra US-EQP-003: comportamento do endpoint público `/v1/qr/{hash}` (já tratado em parecer PRD §B3 e em `qr-publico-allowlist.md`).
- ⏳ Diferido pra Wave B: crypto-shredding programático que valide que hashes salgados (`tag_hash`, `numero_serie_hash`, `localizacao_fisica_hash`, `cliente_id_original_hash`) **sobrevivem** ao shredding do cliente original; teste de integração Wave B.

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 1º, 5º I/II/VI/VII, 6º III/V, 7º II/III/V, 11 § 4º, 16 I/VI, 18 VI, 37, 39
- Código Civil (Lei 10.406/2002) — art. 82 (bens móveis), art. 421/422 (contratos)
- ISO/IEC 17025:2017 — cl. 7.4 (manuseio do item), cl. 7.8 (identificação), cl. 8.4 (registros)
- Res. CD/ANPD 15/2024 — incidentes (caso payload vaze PII bruta)
- INV-049, INV-051, INV-EQP-LOC-001, INV-EQP-QR-001, INV-013, INV-TENANT-001 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03, RAT-EQP-FOTO (`docs/conformidade/comum/lgpd-rat.md`)
- `docs/conformidade/equipamentos/qr-publico-allowlist.md`
- Parecer PRD-advogado deste módulo (B1–B5) — base já cravada
- Pareceres irmãos: US-CLI-001-advogado (R1–R6), US-CLI-004-advogado (R1–R2), US-CLI-005-advogado (R1–R2)
