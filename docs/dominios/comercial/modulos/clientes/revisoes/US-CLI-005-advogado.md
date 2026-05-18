---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-CLI-005
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-005.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-CLI-005 (LGPD)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Antes de qualquer go-live público envolvendo mesclagem de cadastros de titulares finais, advogado humano licenciado deve revisar (especialmente o template do campo `motivo`, que pode virar vetor de vazamento de PII em logs).

---

## Sumário (≤150 palavras)

**APROVADO COM RESSALVAS BLOQUEANTES (R1–R5).** O plano US-CLI-005 acerta no fundamento: soft-delete em vez de hard-delete está alinhado com LGPD art. 16 II (retenção de dados acessórios à execução do contrato) e ISO 17025 cl. 8.4 (~25 anos quando há certificado emitido). **Porém, 5 buracos LGPD precisam ser tampados antes do code-complete:** (R1) `campos_sobrescritos` no audit grava PII cru — proíbe, igual veto US-CLI-001; (R2) campo `motivo` em texto livre vaza PII se atendente descrever titular — exigir enum + comentário sanitizado; (R3) soft-delete não é resposta ao art. 18 VI, esquecimento exige crypto-shredding (Wave B) com reconciliação Receita/ISO; (R4) dedup INV-024 PRECISA olhar `deletado_em IS NOT NULL` (senão reativação por novo cadastro com mesmo CPF cria duplicata); (R5) titular do registro perdedor NÃO precisa ser notificado (art. 9º não se aplica — não é nova finalidade, é correção de qualidade art. 6º V).

---

## Veredito

**APROVADO COM RESSALVAS BLOQUEANTES.** Soft-delete vs hard-delete está juridicamente correto. Audit + motivo precisam saneamento de PII antes do code-complete. Reativação por dedup precisa contemplar perdedor soft-deleted.

### Ressalvas (R1–R5)

#### R1 — Audit `cliente.mesclado` NÃO PODE conter PII cru (BLOQUEANTE)

O T-CLI-013 propõe payload `{vencedor_id, perdedor_id, campos_sobrescritos, motivo, usuario_id}` onde `campos_sobrescritos = {"nome": "valor_a_manter", "email": "...", "telefone": "..."}`. **Isso é PII cru no audit trail.**

- **Veto idêntico ao US-CLI-001:** Auditor de Segurança barrou audit com PII na 2ª auditoria (commit 238fa45 área). INV-001 + INV-013 + INV-AUTHZ-002 exigem audit imutável **com** retenção longa (audit trail em B2 WORM = 5–10 anos, ver `retencao-matriz.md` §2). PII cru no audit cria 3 problemas:
  1. **Crypto-shredding fica impossível** — quando titular exercer art. 18 VI em 2031, o audit ainda terá CPF/nome/email em texto, e WORM não permite UPDATE/DELETE.
  2. **Cross-tenant blast radius** — admin Aferê (suporte forense) consegue ler dados do tenant via audit, fura a expectativa do tenant-controlador.
  3. **NC LGPD art. 6º III** (necessidade) — o audit precisa provar **que** houve mesclagem, não **quais valores** foram trocados (esses ficam no estado pós-merge da própria linha de Cliente, que é o "depois" do INV-001).

- **Solução obrigatória — payload sanitizado:**

  ```python
  {
      "vencedor_id": "<uuid>",
      "perdedor_id": "<uuid>",
      "campos_sobrescritos_keys": ["nome", "email", "telefone"],   # apenas nomes dos campos
      "motivo_categoria": "duplicata_confirmada",                  # enum (ver R2)
      "motivo_observacao_hash": "<sha256 do texto livre, se houver>",
      "usuario_id": "<uuid>",
      "tenant_id": "<uuid>",
      "timestamp": "...",
      "ip_hash": "<sha256(ip + salt_tenant)>"
  }
  ```

  Os **valores** sobrescritos não vão pro audit — quem quiser reconstruir "o que mudou" usa o snapshot `antes/depois` do INV-001 sobre a linha `Cliente` (que tem retenção por crypto-shredding controlada pelo tenant). O audit `cliente.mesclado` é metadado de operação, não cópia de dado.

- **Task nova:** **T-CLI-013b** — sanitizar payload (testes garantem que `campos_sobrescritos_keys` não contém valores, só nomes; teste de regressão `test_mesclar_audit_sem_pii_cru` rodando regex de CPF/email no payload serializado).

#### R2 — Campo `motivo` em texto livre é vetor de vazamento (BLOQUEANTE)

O plano exige `motivo` (T-CLI-015 `test_mesclar_motivo_obrigatorio`) sem restringir conteúdo. Texto livre do atendente vai virar isto:

> "Cliente Sr. Silva 12345678900 tem 2 cadastros, mesclei pq mudou e-mail de jsilva@gmail pra joaosilva@hotmail"

Esse motivo viaja pro audit (B2 WORM, 5–10 anos) **e** pra trilha visível a admin Aferê em suporte forense. Vazamento garantido por descuido do atendente. Mesma família do "bundle de consentimento" — não confiar em disciplina de texto livre.

- **Solução obrigatória — enum + observação sanitizada:**

  | `motivo_categoria` (enum) | Quando usar |
  |---|---|
  | `duplicata_confirmada` | Mesmo CPF/CNPJ comprovado |
  | `mesma_pessoa_documentos_diferentes` | CPF antigo + CPF novo do mesmo titular (raro) |
  | `unificacao_pos_fusao_empresarial` | PJ — fusão/aquisição (CNPJ A virou CNPJ B) |
  | `correcao_erro_digitacao_anterior` | Cadastro errado virou novo cadastro correto |
  | `outro` | Exige `observacao` (texto livre limitado a 200 chars com regex anti-PII — ver abaixo) |

  O campo livre `observacao` (opcional, só obrigatório se `motivo_categoria=outro`):
  - Limite 200 chars.
  - Validação no backend: regex bloqueia entrada que contenha CPF (`\d{3}\.?\d{3}\.?\d{3}-?\d{2}`), CNPJ (formato), e-mail (`\S+@\S+`), telefone (≥10 dígitos seguidos). Se detectar, rejeita com 400: "Não inclua dados pessoais do titular no motivo — use a categoria 'duplicata_confirmada' ou descreva sem PII."
  - Template safe sugerido (mostrar como placeholder na UI quando V2 trouxer wizard): **"Dois cadastros do mesmo titular criados em datas diferentes; mantido o mais recente por estar atualizado."**

- **Task nova:** **T-CLI-013c** — implementar enum + sanitizador regex anti-PII no `observacao`.

#### R3 — Soft-delete NÃO é resposta ao art. 18 VI (esquecimento) — clarificar no plano

O plano diz "perdedor vira soft-delete auditável" e cita "LGPD" em AC-2. **Soft-delete não cumpre direito ao esquecimento** — só posterga decisão. Dois cenários distintos:

1. **Mesclagem (US-CLI-005):** perdedor vira soft-deleted = correto. Não é exercício de direito do titular, é correção de qualidade (art. 6º V). Soft-delete preserva audit (art. 37) + atende retenção fiscal Receita 5 anos + ISO 17025 25 anos se há cert. **Esse é o caso US-CLI-005.**

2. **Exercício art. 18 VI pelo titular (Wave B, módulo `lgpd-portal`):** titular pede eliminação. Resposta correta é **crypto-shredding por tenant** com reconciliação:
   - Se há NF-e/cert emitido → reter dado anonimizado (Receita 5 anos / ISO 25 anos) com base art. 16 II.
   - Se NÃO há registro de retenção legal → eliminar PII (CPF, nome, contato, endereço) preservando apenas chave técnica `cliente_id` + flag `esquecido_em` no audit.
   - Crypto-shredding: chave KMS por tenant → destruir chave em B2 WORM torna conteúdo ilegível sem violar imutabilidade do WORM (essa é a técnica que reconcilia art. 16 + art. 18).

- **Solução obrigatória — adendo no plano US-CLI-005, seção "Limites desta fase":**

  > "Soft-delete do cadastro perdedor **NÃO** é resposta ao direito ao esquecimento (LGPD art. 18 VI). É **correção de qualidade** (art. 6º V) + **retenção contratual/regulatória** (art. 16 II + ISO 17025 cl. 8.4). Exercício de esquecimento pelo titular é tratado em módulo separado (`lgpd-portal` da Wave B) via crypto-shredding por tenant com reconciliação à matriz de retenção."

- **Task nova:** **T-CLI-013d** — adicionar nota explicativa no AC-2 + comentário no model `Cliente.deletado_em`.

#### R4 — Dedup INV-024 PRECISA ignorar `deletado_em IS NOT NULL` corretamente — BLOQUEANTE

Cenário real: cliente A é mesclado em B; A fica soft-deleted (`deletado_em != NULL`). Meses depois, atendente cadastra novo cliente com **mesmo CPF de A**. O que acontece?

- **Comportamento errado 1:** queryset default filtra `deletado_em IS NULL` (T-CLI-010), então dedup INV-024 **não vê** o A soft-deleted, deixa criar duplicata → existe agora um cliente novo com CPF X **e** A soft-deleted com CPF X. INV-024 violada silenciosamente.
- **Comportamento errado 2:** constraint `UNIQUE (tenant_id, cpf_ou_cnpj)` no banco rejeita o INSERT mesmo com A soft-deleted (porque constraint não respeita o filtro Python) → atendente vê erro "CPF já existe" e o cliente A está invisível (filtro default), atendente pensa que sistema está bugado → workaround manual.

- **Solução obrigatória — duas camadas:**

  1. **Constraint condicional:** índice único parcial **`UNIQUE (tenant_id, cpf_ou_cnpj) WHERE deletado_em IS NULL`** (PostgreSQL suporta nativamente em `CREATE UNIQUE INDEX ... WHERE ...`). Isso permite reativação por novo cadastro **e** preserva A soft-deleted no histórico.
  2. **UX no dedup:** quando atendente digita CPF que existe **só** em registro soft-deleted, sistema mostra: "Existe cadastro arquivado com este CPF (mesclado em [data] para [vencedor_id]). [Reabrir cadastro original] [Criar cadastro novo]." Em vez de bloquear cego, dá saída — "reabrir" desfaz o soft-delete em V2 (rollback, hoje out-of-scope no non-goal); "criar novo" funciona porque o índice é parcial.

- **Task nova:** **T-CLI-009b** — alterar T-CLI-009 pra usar `UNIQUE INDEX ... WHERE deletado_em IS NULL` em vez de `UNIQUE (tenant_id, cpf_ou_cnpj)` simples. **T-CLI-015b** — adicionar teste `test_dedup_inv024_ignora_perdedor_soft_deleted_no_constraint`.

#### R5 — Titular do registro perdedor NÃO precisa ser notificado (LGPD art. 9º não se aplica)

Pergunta do briefing: "precisa notificar titular (art. 9º)?" — **Não.**

- LGPD art. 9º exige informação clara sobre **finalidade, forma, duração do tratamento** etc. **no momento da coleta** (ou na mudança substancial de finalidade). Mesclagem de cadastro duplicado **não é** mudança de finalidade — é correção de qualidade do mesmo dado pra mesma finalidade (execução de contrato art. 7º V).
- Notificar titular de cada mesclagem geraria ruído sem ganho legal e poderia até parecer falha operacional do tenant.
- **Quando seria obrigatório notificar:** se a mesclagem **modificar a finalidade** ou **transferir o dado a terceiro** — não é o caso aqui (intra-tenant, mesmo controlador, mesma finalidade).
- **O que SIM é exigido:** registrar a mesclagem no audit (já no plano) **e** disponibilizar o histórico ao titular se ele exercer art. 18 II (direito de acesso) — isso vem do `lgpd-portal` Wave B, não do US-CLI-005.

Conclusão R5: **manter plano como está nesse aspecto** — sem notificação automática ao titular. Documentar o porquê no AC-2 ou comentário no use case `mesclar_clientes.py`.

### Não-ressalvas (validadas como corretas)

- ✅ **Soft-delete em vez de hard-delete:** correto. LGPD art. 16 II + ISO 17025 cl. 8.4 + Receita 5 anos suportam retenção. Hard-delete só via crypto-shredding controlado pelo tenant (Wave B).
- ✅ **`deletado_em` + `deletado_por_usuario_id` + `deletado_motivo` no model:** correto pro requisito audit (INV-001).
- ✅ **`Cliente.all_objects` separado:** correto. Garante isolamento entre operação corrente (filtro padrão) e auditoria forense (manager all).
- ✅ **Cross-tenant bloqueado (T-CLI-012):** correto. RLS já cobre; defensivo bom.
- ✅ **Authz `clientes.mesclar` exigindo `admin_tenant`:** correto. Ação destrutiva merece perfil restrito; alinhado a INV-AUTHZ-001 + SEC-LEAST-PRIV-001.
- ✅ **Evento `Cliente.Mesclado` publicado pra futuro consumo:** correto. Preserva contrato pra Wave A (OS/cert/financeiro) sem implementar consumers que não existem.

---

## Texto sugerido — template safe pro motivo (UI futura wizard V2)

Em vez de campo livre, UI deve ser **`select` com 5 opções** (enum R2). Quando `outro` é selecionado, abrir textarea com:

- **Placeholder:** *"Descreva o motivo da mesclagem **sem incluir** nome, CPF, telefone ou e-mail do titular. Exemplo: 'Dois cadastros do mesmo titular criados em datas diferentes; mantido o mais recente por estar atualizado.'"*
- **Contador visual:** 0/200.
- **Validação client-side:** highlight vermelho se regex anti-PII detecta CPF/CNPJ/email/telefone, com tooltip "Use a categoria padrão ou descreva sem dados pessoais."
- **Validação server-side:** rejeita 400 com mesma mensagem (cinto + suspensório porque atendente pode desabilitar JS).

**Para o MVP-1 (sem UI, só API):** o backend já valida enum + regex; documentação da rota em `docs/dominios/comercial/modulos/clientes/contratos/api.md` (T-CLI-011) descreve os 5 valores aceitos e o regex aplicado a `observacao`.

---

## Análise por área

### LGPD / Privacidade

- **Base legal da mesclagem:** art. 6º V (qualidade) — princípio que **exige** dado exato e atualizado. Mesclar duplicatas **cumpre** LGPD, não viola. Não há nova base legal a declarar.
- **Papel do Aferê na mesclagem:** **operador** (igual US-CLI-001). Tenant é controlador da decisão de mesclar; Aferê só executa instrução documentada (a chamada à API). DPA tenant↔Aferê cobre.
- **Retenção pós-mesclagem:** registro perdedor soft-deleted segue **mesma matriz** do cliente principal (`retencao-matriz.md` §2 — "Cadastro de cliente final do tenant: 5 anos default fiscal"). Quando há OS/cert emitido referenciando o `perdedor_id` (futuro Wave A), retenção sobe pra ~25 anos ISO 17025.
- **Direitos do titular (art. 18):** mesclagem não dispara nenhum direito automaticamente. Se titular exercer art. 18 II (acesso), `lgpd-portal` Wave B retornará histórico **consolidado** — incluindo nota "este cadastro foi mesclado em [data] a partir de cadastro arquivado".

### Contratual

- DPA tenant↔Aferê já cobre operações de qualidade de dado (limpeza, dedup, mesclagem) como parte da instrução documentada do tenant — não precisa addendum.
- Quando atendente do tenant aperta "Mesclar" no balcão, a instrução é o **fluxo do produto**.

### Regulatório (ANPD)

- **Mesclagem NÃO é incidente.** Não dispara Res. CD/ANPD 15/2024.
- **Mesclagem errada (vencedor e perdedor são titulares diferentes — atendente confundiu)** vira **incidente de qualidade** (art. 6º V) → tenant decide se reverter ou notificar titular afetado. Rollback de soft-delete é V2 (non-goal atual) — então plano deve documentar que erro de mesclagem hoje é **irreversível na prática** sem suporte Aferê via SQL forense. Isso é risco operacional aceito; documentar.

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Audit `cliente.mesclado` com `campos_sobrescritos` cru → PII no WORM 5–10 anos → impossível esquecer | Alta sem R1 | Multa ANPD + NC LGPD art. 16 | **R1** — payload sanitizado (só keys, não values) |
| Atendente escreve PII do titular em `motivo` texto livre → vaza no audit | Alta sem R2 | NC LGPD + risco reputacional | **R2** — enum + regex anti-PII no `observacao` |
| Reativação por novo cadastro com mesmo CPF do soft-deleted → INV-024 violada silenciosamente OU bloqueio confuso pro atendente | Alta sem R4 | UX ruim + qualidade de dado (art. 6º V) | **R4** — `UNIQUE INDEX ... WHERE deletado_em IS NULL` parcial + UX "reabrir/criar novo" |
| Confusão entre soft-delete (US-CLI-005) e direito ao esquecimento (Wave B) → time implementa esquecimento como soft-delete pensando estar OK | Média sem R3 | NC LGPD art. 18 VI quando titular pedir esquecimento | **R3** — adendo explicativo no plano + comentário no model |
| Mesclagem errada por atendente (titulares diferentes) sem rollback no MVP-1 | Média | Incidente qualidade + retrabalho | Documentar que rollback é V2; suporte Aferê via SQL forense por enquanto |
| Notificação automática ao titular implementada por excesso de zelo → ruído + dúvida do titular | Baixa | UX ruim + custo de suporte | **R5** — documentar que não é exigida; manter plano sem notificação |

---

## Próximos passos

- ✅ Aplicar R1–R4 no plano `US-CLI-005.md` (autoria: agente que implementar — tech-lead ou implementador). R5 é apenas documentação esclarecedora.
- ✅ Tasks novas: **T-CLI-009b** (índice único parcial), **T-CLI-013b** (audit sanitizado), **T-CLI-013c** (enum + regex anti-PII), **T-CLI-013d** (nota explicativa AC-2), **T-CLI-015b** (teste reativação por CPF de soft-deleted).
- ⚠️ **Antes do go-live público (não MVP-1 dogfooding):** template do enum + observação precisa revisão de advogado humano com OAB ativa — palavras em campo legalmente visível ao tenant (ex.: catálogo de motivos) deve ser revisado.
- ⏳ Diferido pra Wave B (`lgpd-portal`): exercício art. 18 (acesso, esquecimento, portabilidade); crypto-shredding por tenant; reconciliação Receita 5 anos × ISO 25 anos.
- ⏳ Diferido pra V2: rollback de mesclagem (desfazer soft-delete); UI wizard com placeholders template safe; mesclagem em batch.

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 5º VI/VII, 6º III/V/VI, 7º II/V, 8º §4º, 9º, 16 II, 18 II/VI, 37, 46
- Res. CD/ANPD 15/2024 — incidentes (não aplicável a mesclagem)
- ISO/IEC 17025 cl. 8.4 — retenção de registros
- INV-001, INV-013, INV-024, INV-AUTHZ-001/002, INV-TENANT-001/002, SEC-LEAST-PRIV-001 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03 (`docs/conformidade/comum/lgpd-rat.md`)
- `docs/conformidade/comum/retencao-matriz.md` §2
- US-CLI-001 revisão `US-CLI-001-advogado.md` (veto anterior PII em audit)
