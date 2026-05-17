# REGRAS-INEGOCIÁVEIS.md

> **Fonte única de regras críticas do projeto.** Funde INVARIANTES de negócio + regras de TESTES + regras de SEGURANÇA com IDs estáveis. Outros docs **citam IDs** (`INV-007`, `SEC-003`), **não duplicam texto**.
>
> Toda regra crítica aqui tem (ou terá) um **hook** que valida — regra sem hook é decorativa.

---

## Como citar
- Em código (comentário): `// INV-007: certificado emitido é imutável`
- Em commit: `fix(INV-TENANT-001): adiciona tenant_id no WHERE da query X`
- Em teste: `test_inv_007_certificado_emitido_nao_pode_ser_editado`
- Em PR description: "Mudança afeta INV-003 — auditor revisou"

## Como adicionar regra nova
1. Cria entrada nesta tabela com próximo ID livre (`INV-NNN`, `INV-TENANT-NNN`, `TST-NNN`, `SEC-NNN`).
2. Cria hook que valida a regra (ou justifica por que NÃO dá pra automatizar).
3. Cria ≥1 teste que prova a regra (nome do teste cita o ID).
4. Documenta consequência de violar.

---

## INV-* — Invariantes de negócio

> **Migrado em 17/05/2026 (3ª auditoria de 10 agentes — Auditor 6 compliance):** INV-001..020 estavam só em `docs/discovery/normas-e-regulacao.md` (capítulo discovery, fora do arquivo canônico). Sem migração, hooks de validação não disparavam porque o catálogo canônico estava vazio. Migração completa pra cá; hooks correspondentes a criar progressivamente.

| ID | Regra | Base normativa | Hook que valida | Escopo por perfil | Consequência de violar |
|---|---|---|---|---|---|
| INV-001 | Trilha de auditoria imutável (`quem, quando, antes, depois`) com hash encadeado, em toda operação que toca certificado de calibração ou documento fiscal | 17025 cl. 7.11 + 8.4 + Marco Civil art. 15 + LGPD art. 37 | Banco com WORM + hash em append-only | Absoluta (todos perfis) | Falha de auditoria CGCRE + processo LGPD ANPD |
| INV-002 | Toda emissão de certificado grava cadeia de rastreabilidade completa (instrumento → padrão → certificado do padrão → incerteza). Sem cadeia, emissão bloqueia | NIT-DICLA-030 rev. 15 item 8.2.6 + 17025 cl. 6.5 | Pre-commit hook na emissão | Absoluta em A; configurável em B/C/D | Rejeição em supervisão Cgcre (R-018 score 25) |
| INV-003 | Signatário só assina dentro do **escopo de autorização vigente na data da assinatura** | 17025 cl. 6.2 + NIT-DICLA-021 | Validação no momento de assinar; congelar autorização vigente | Absoluta em A; configurável em B/C/D | Certificado nulo retroativo (R-060) |
| INV-004a | Nenhum deploy em produção sem aprovação documentada do responsável técnico do laboratório | 17025 cl. 7.11 | CI bloqueia merge/deploy sem registro | Absoluta em A; configurável em B/C/D | NC em auditoria |
| INV-004b | Toda alteração em rotina de cálculo de incerteza requer revalidação registrada | 17025 cl. 7.11 + EA-4/02 | Hook detecta mudança em arquivos da rotina; bloqueia merge | Absoluta em A; configurável em B/C/D | Incerteza não-rastreável |
| INV-004c | A versão do software fica gravada em cada certificado emitido | 17025 cl. 7.11 + boa prática (recall) | Campo obrigatório no template do certificado | Absoluta (todos perfis) | Recall impossível |
| INV-005 | Comunicação de incidente LGPD em ≤3 dias úteis (ANPD + titular) + registro de TODOS incidentes por ≥5 anos. ATPP tem prazo dobrado | Res. CD/ANPD 15/2024 art. 6º, 9º, 10 | Workflow obrigatório no painel de incidente | Absoluta (todos perfis) | Multa ANPD (R-014) |
| INV-006 | DPO publicado no site (identidade + contato em local de destaque) + canal de titular funcional. ATPP dispensado de DPO mas mantém canal | Res. CD/ANPD 18/2024 | Validação no setup do tenant | Absoluta (todos perfis) | Não-conformidade LGPD |
| INV-007 | NF-e: arquitetura preparada pra SVC-AN/SVC-RS desde dia 0 (não como contingência tardia) | NT 2013/007 + boa prática | Cliente sem SVC configurado: deploy de NF-e bloqueado | Absoluta (todos perfis) | Sistema fiscal indisponível em contingência |
| INV-008 | Logs de acesso à aplicação retidos por ≥6 meses (recomendado 12 meses) com sigilo | Marco Civil art. 15 | Política de retenção no banco de logs | Absoluta (todos perfis) | Impossibilidade de investigar incidente |
| INV-009 | MFA pra usuários com acesso ao CDE (Cardholder Data Environment) — não só admins | PCI 4.0.1 (expansão) | Validação no login | Absoluta quando PCI aplica | Não-conformidade PCI |
| INV-010 | Registros 17025 com retenção ≥ ciclo de calibração do cliente + 1 ciclo (tipicamente 5–25 anos) | 17025 cl. 8.4 | Política de retenção por tipo de registro; LGPD base "obrigação legal" | Absoluta em A; configurável em B/C/D | Perda de rastreabilidade histórica |
| INV-011 | Emissão de certificado bloqueia se padrão usado tem calibração vencida | 17025 cl. 6.5 + 7.2 | Pre-commit hook na emissão | Absoluta em A; configurável em B/C/D | Certificado nulo (Dor #06) |
| INV-012 | Workflow de Não Conformidade (cl. 7.10 + 8.7) com bloqueio de emissão até resolução documentada | 17025 cl. 7.10 + 8.7 | NC aberta no instrumento → bloqueio na emissão | Absoluta em A; configurável em B/C/D | NC reincidente em supervisão |
| INV-013 | Confidencialidade cl. 4.2: acesso a dados de cliente do laboratório só com permissão explícita + log de toda visualização (incluindo admins) | 17025 cl. 4.2 | RBAC + audit trail visualização | Absoluta (todos perfis) | Vazamento intra-tenant (Dor #23 nova) |
| INV-014 | Aceitação de certificado de calibração de padrão externo bloqueada se omitir resultado de medição + incerteza | NIT-DICLA-030 rev. 15 item 8.2.6 | Validação no cadastro de padrão | Absoluta em A; configurável em B/C/D | Cadeia de rastreabilidade quebrada |
| INV-015 | **Tenant não pode emitir certificado de tipo superior ao perfil declarado.** Perfil B/C/D não pode emitir com selo RBC; perfil D não pode emitir declarando "rastreável ao RBC" se não tem padrão RBC. Upgrade de perfil exige prova documental | INMETRO + LGPD + CDC | Validação no momento de gerar PDF do certificado + no upgrade de perfil | Absoluta (todos perfis) — invariante que SEPARA os perfis | Fraude regulatória + Roldão responde solidariamente (R-039) |
| INV-016 | **Conformidade WCAG 2.1 AA + PDF/UA em toda interface visível pra usuário.** Portal cliente, app mobile, certificado PDF, telas de cadastro | Lei 13.146/2015 (LBI) art. 63 + e-MAG + WCAG 2.1 AA + Lei 14.133/2021 | axe-core ou Lighthouse no CI; PDF/UA conformance no gerador; revisão manual a cada release | Absoluta (todos perfis) | Multa MP + reprovação em licitação (R-048) |
| INV-017 | **Assinatura digital ICP-Brasil A3/A1 + carimbo do tempo ITI em toda emissão de certificado de calibração.** Sem assinatura + carimbo válidos, emissão bloqueia | MP 2.200-2/2001 art. 10 + Lei 14.063/2020 | Hook bloqueia emissão sem A3 em A; mínimo A1 em B; carimbo ITI absoluto | A: A3 obrigatório. B: A1 mínimo. C/D: A1 ou ITI isolado | Certificado sem valor legal |
| INV-018 | **Vendor (Aferê) mantém RT técnico publicado no site** (engenheiro CREA com competência metrológica). Substituição em até 60 dias máximo. RT assina dossiê de validação por release. **DECISÃO 17/05/2026 (Roldão):** Aferê opera SEM RT no MVP-1, com R-065 score 20 aceito conscientemente; RT entra em V2-V3 quando produto estiver pronto. Não atender cliente farma TOP no MVP-1. | ISO 17025 cl. 7.11 + boa prática auditoria | Página pública mostra RT vigente; dashboard interno mostra status | Absoluta a partir de V2-V3 (decisão dependente) | Cliente farma TOP recusa fornecedor sem RT (R-065 score 20 — aceito) |
| INV-019 | **Dossiê de validação por release pública.** Toda release gera URS + casos de teste + change log + assinatura digital do RT-vendor + carimbo ITI. Disponibilizado pra tenant em até 48h | ISO/IEC 17025 cl. 7.11.2 + NIT-DICLA-016 item 5.8 | CI bloqueia deploy de release pública sem dossiê assinado anexado; portal do tenant disponibiliza | Absoluta a partir de V2-V3 (depende de INV-018) | Tenant não consegue submeter o software em auditoria do próprio tenant |
| INV-020 | **Jornada de motorista UMC conforme Lei 13.103/2015 + CLT 235-C.** 30 min descanso a cada 5h30 de direção; 11h ininterruptas entre jornadas; tempo-espera = sobreaviso 1/3 | Lei 13.103/2015 + CLT art. 235-C §9 | Hook valida agenda da UMC; bloqueia agendamento que infringe | Aplicável a tenants que operam UMC (todos perfis quando operam UMC) | Passivo trabalhista no tenant + Roldão arrolado solidariamente (R-058) |

**Notas operacionais:**
- INV-001..017, 019, 020: hooks a criar progressivamente conforme módulo correspondente entra no MVP-1
- INV-018: PENDENTE — aceita conscientemente, dispara em V2-V3
- TST-004 valida automaticamente: todo INV-NNN crítico deve ter ≥1 teste cujo nome cita o ID

---

## INV-TENANT-* — Invariantes de multi-tenancy

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-TENANT-001 | Toda query SQL/ORM contém `tenant_id` no WHERE | Linter de query + teste de fuzzing | Vazamento cross-tenant — incidente #1 ANPD + perda de cliente |
| INV-TENANT-002 | Toda tabela com dados de cliente tem coluna `tenant_id` NOT NULL | Migration linter | Mesmo |
| INV-TENANT-003 | RLS (Row-Level Security) ativa em todas tabelas com `tenant_id` (se stack escolhida = PostgreSQL) | Migration check + teste | Mesmo |
| INV-TENANT-004 | Role da aplicação Django criada com `NOBYPASSRLS` + `NOSUPERUSER`. Migrations rodam com role separada `app_migrator` (também NOBYPASSRLS). Hook de migration valida `current_setting('is_superuser') = off` e testa que policy RLS não pode ser ignorada. | Migration check + teste de bypass | Docker Compose mal configurado rodando como `postgres` superuser anula RLS inteira — vazamento determinístico em qualquer query. Auditor 2 da 1ª auditoria de 10 agentes (17/05/2026). |

Reforçados pelo ADR-0002 (multi-tenancy) — rascunho em `docs/adr/0002-multi-tenancy.md`.

---

## TST-* — Regras de teste

| ID | Regra | Hook | Consequência de violar |
|---|---|---|---|
| TST-001 | Proibido `skip()` / `xit()` / `@Disabled` sem justificativa em comentário com data e dono | Linter | Teste falso-verde mascara bug |
| TST-002 | Proibido `assertTrue(true)`, `assert 1 == 1` e outras assertions vazias | Linter AST | Mesmo |
| TST-003 | Proibido `@ts-ignore`, `eslint-disable`, `# type: ignore` sem comentário com justificativa | Linter | Bypass silencioso |
| TST-004 | Toda INV-NNN crítica tem ≥1 teste cujo nome cita o ID | CI grep | Invariante decorativa |

---

## INV-AGENT-* — Invariantes de operação por agente IA

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-AGENT-001 | Todo input externo não-confiável (campo preenchido por cliente final, e-mail/anexo de fornecedor, PR comment, issue de cliente) entra em código tipado como `UntrustedInput[T]` (brand type Pydantic). Funções que consomem `UntrustedInput` NÃO podem chamar diretamente: API de LLM (LiteLLM), `subprocess`, ORM com query dinâmica, `eval`/`exec`, gravação direta em tabela de domínio crítico (financeiro, fiscal, KMS, migrations). Pra esses casos, exige passagem por sanitizer + log explícito + revisão humana se score de risco > 0,5. | Lint AST custom (`semgrep` rule) bloqueia `LLMGateway.chat(...)` com input não-marcado; teste de fuzzing prova injection bloqueada | Prompt injection via input de cliente final move agente a executar ação cross-tenant (R-027 score 25). ADR-0000 regra #5. |

---

## SEC-* — Regras de segurança

| ID | Regra | Hook | Consequência de violar |
|---|---|---|---|
| SEC-001 | Proibido commitar segredo (chave, token, senha) — formato detectado por scanner | Hook `.claude/hooks/secrets-scanner.sh` ✅ | Vazamento de credencial |
| SEC-002 | Proibido `rm -rf`, `git reset --hard` sem aprovação humana explícita | Hook `.claude/hooks/block-destructive.sh` ✅ | Perda de trabalho |
| SEC-TENANT-001 | RLS ativa em todas tabelas com dados de cliente — ver INV-TENANT-003 | Migration check | Vazamento cross-tenant |
| SEC-003 | Input externo não-confiável (PR comment, issue, e-mail, anexo de cliente) NUNCA pode executar ação em `financeiro/`, `kms/`, `migrations/` sem aprovação humana | `seguranca/agente-input-nao-confiavel.md` define mecanismo | Prompt injection causa vazamento financeiro |

---

## Manutenção

- Toda mudança nesta lista exige aprovação humana via CODEOWNERS (este arquivo está em `REGRAS-INEGOCIAVEIS.md`, listado em `.github/CODEOWNERS`).
- IDs **nunca são reciclados** — regra descontinuada vira `INV-007 (DESCONTINUADA em 2027-XX-YY: motivo)`.
- Auditor de qualidade (Família 5) revisa este arquivo a cada release.
