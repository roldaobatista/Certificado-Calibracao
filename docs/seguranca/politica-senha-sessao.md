---
documento: política canônica de senha + sessão + allowlist anti-PII em authz
status: draft
owner: tech-lead-saas-regulado
revisado-em: 2026-05-23
revisado-por: auditor-seguranca + auditor-conformidade-lgpd (Onda 3 saneamento F-B)
relacionado:
  - docs/adr/0038-familia-inv-auth.md (INV-AUTH-001..005)
  - docs/adr/0012-autorizacao-unificada.md (INV-AUTHZ-001..004)
  - REGRAS-INEGOCIAVEIS.md
---

# Política de senha + sessão + allowlist anti-PII

> **Fonte única dos parâmetros canônicos** das invariantes INV-AUTH-001..005 + esclarecimento textual de INV-AUTHZ-002 sobre PII em `resource`/`escopo_avaliado`. Toda implementação Wave A consome este doc — não duplica valores em settings.py / código de domínio sem citar §.

---

## §1 — Política de senha (INV-AUTH-002)

| Parâmetro | Valor | Base |
|---|---|---|
| Comprimento mínimo | 12 caracteres | NIST SP 800-63B rev.4 §5.1.1.2 (memorized secrets) |
| Categorias exigidas | 3 das 4 (maiúscula, minúscula, dígito, símbolo) | OWASP ASVS L2 V2.1 |
| Histórico (anti-reuso) | últimas **5 senhas** | NIST SP 800-63B + ABNT NBR ISO/IEC 27002 |
| Expiração (perfis sensíveis) | **180 dias** | Política interna — NIST não exige expiração genérica, exige só pra "memorized secret comprometida" |
| Expiração (perfis não-sensíveis) | sem expiração compulsória | NIST SP 800-63B (expiração compulsória sem motivo prejudica segurança) |
| Termos vetados (case-insensitive, sem acentos) | `email`, `nome`, `cpf`, `cnpj_tenant` | OWASP |
| Algoritmo hash | bcrypt cost 12 (Django default 4.x) | OWASP ASVS L2 V2.4.4 |

**Lista canônica de perfis sensíveis** (consome esta lista quem precisa: INV-AUTH-002 expiração, INV-AUTH-003 sessão reduzida, INV-AUTH-004 troca 90d):

- `admin_tenant`
- `financeiro`
- `signatario`
- `metrologista_bancada`
- `gerente_operacional`

Novo perfil sensível: adicionar **aqui** + na seed `0007_seed_perfis_marco_3_4.py` se for global, ou em migration própria se tenant-specific (INV-AUTHZ-004).

## §2 — Sessão (INV-AUTH-003)

| Parâmetro | Perfil padrão | Perfil sensível |
|---|---|---|
| Idle timeout | 30 min | 15 min |
| Máximo absoluto | 8 h | 4 h |
| Cookie `SameSite` | `Lax` | `Strict` |
| Cookie `Secure` | obrigatório (produção) | obrigatório (produção) |
| Cookie `HttpOnly` | obrigatório | obrigatório |
| Refresh token Flutter (Wave A) | rotação por uso, janela 7d | rotação por uso, janela 24h |

Idle measurement: último request autenticado (qualquer endpoint não-`OPTIONS`). `Last-Activity-At` em sessão Redis.

## §3 — Lockout (INV-AUTH-001)

| Parâmetro | Valor |
|---|---|
| Tentativas falhadas pra bloquear | 5 |
| Janela de contagem | 15 min |
| Duração do bloqueio | 30 min |
| Chave de contagem | `email` **OU** `ip_hash` (qualquer dos dois bate o limite) |
| Mensagem de erro ao usuário | "credenciais inválidas ou conta indisponível" (sempre igual, defesa contra enumeração) |
| Desbloqueio manual | apenas `admin_tenant` (registra `RegistroAlterado`) |

## §4 — Troca forçada (INV-AUTH-004)

- Perfis sensíveis: cada 90 dias.
- D-7: banner em todas as telas + e-mail.
- D-3: e-mail diário.
- D-0: bloqueio operacional (`auth_must_change_password`) — única ação permitida é trocar senha.
- Pós-troca: histórico §1 impede reuso das últimas 5.

## §5 — Retenção tentativas-login (INV-AUTH-005)

| Tabela | Retenção | Pós-prazo |
|---|---|---|
| `auth_login_tentativa` | 365 dias | DELETE; agregar antes em `auth_login_tentativa_agregado` |
| `auth_login_tentativa_agregado` | indefinido | só conta + dia + tenant + motivo (sem PII) |
| Evento `AcessoSeguranca.LoginFalha` no WORM B2 | 5 anos (INV-AUTHZ-002) | descarte do bucket WORM por política de bucket |

Worker `expurga_login_tentativa.py` (Wave A): roda diário 03:00 UTC, agrega + apaga.

## §6 — Allowlist anti-PII em `resource` / `escopo_avaliado` (INV-AUTHZ-002)

> **Contexto F-B-M2 / F-B-M3 (Onda 3):** auditor 2 detectou que o texto atual de INV-AUTHZ-002 lista campos da `audit_trail.authz_decisions` mas **não veda explicitamente PII por valor**. Implementador Wave A pode achar que gravar `resource_summary = "CPF 123.456.789-09"` está OK — não está.

### Regra textual canônica

> **PII por referência, nunca por valor.** Os campos `resource_summary` e `escopo_avaliado` da tabela `audit_trail.authz_decisions` aceitam **somente identificadores opacos** (`uuid`, `slug`) e **classificadores** (tipo de entidade, ação). É **vetado** persistir nome próprio, CPF, CNPJ por extenso, e-mail, telefone, endereço, CEP, RG, biometria, dado de saúde, dado financeiro detalhado (saldo, número de conta) ou qualquer combinação que permita identificar pessoa natural sem cruzamento adicional.

### Allowlist canônica de slugs/chaves permitidos em `escopo_avaliado` JSON

Slugs cujos VALORES são uuid ou enum opaco — seguros pra Marco 3 (OS) e Marco 4 (Calibração):

- `tenant_id`
- `usuario_id`
- `perfil_id` / `perfis_id`
- `recurso_kind` / `resource_kind` (enum: `OS`, `AtividadeDaOS`, `Certificado`, `Equipamento`, `Cliente`, `Fatura` …)
- `recurso_id` / `resource_id`
- `os_id`
- `atividade_id`
- `tecnico_executor_id`
- `equipamento_id`
- `certificado_id`
- `cliente_id` (uuid, **não** nome)
- `fatura_id`
- `contas_receber_id`
- `signatario_id`
- `metodo` (enum: `senha`, `sso_oidc`, `passkey_webauthn` …)
- `motivo` (enum controlado: `perfil_sem_acao`, `tenant_diferente`, `escopo_recurso`, `vigencia_expirada`)
- `vigencia_em` (timestamp ISO)
- `correlation_id` (uuid)

### Denylist (proibido — hook `pii-em-authz-decisions-check.sh` Wave A bloqueia)

- `nome`, `nome_completo`, `razao_social`, `nome_fantasia` (em texto literal)
- `cpf`, `cnpj` (em texto literal — uuid de cliente OK)
- `email` (em texto literal — `email_hash` OK)
- `telefone`, `celular`
- `endereco`, `cep`, `logradouro`, `bairro`, `cidade` (combinação geo identifica)
- `rg`, `passaporte`, `cnh`
- `saldo`, `valor_fatura`, `valor_pago` (em valor monetário literal — uuid da fatura OK)
- `data_nascimento`
- `biometria_*` (qualquer campo de biometria)
- `cid`, `prontuario`, `medicamento` (dados de saúde)

### Verificação automatizada

Hook `pii-em-authz-decisions-check.sh` (a criar em Wave A) faz:
1. Lê arquivos `**/authz/*.py` + `**/policies/*.py`.
2. Detecta `audit_decision.resource_summary = ...` ou `decision.escopo_avaliado = {...}`.
3. Se valor literal contém regex CPF/CNPJ/e-mail/telefone-BR → bloqueia commit.
4. Override: `# pii-em-authz: skip -- <razão ≥10 chars + commit do tech-lead>` na linha.

## §7 — Mapeamento operacional

| Item | Local de implementação Wave A |
|---|---|
| Lib de lockout | django-axes 7.x (decisão pendente revisão tech-lead) |
| Hash histórico senha | `auth_senha_historico` tabela própria, FK `usuario_id`, índice `(usuario_id, criada_em DESC)` |
| Tabela de tentativas | `auth_login_tentativa` (eventos detalhados) + `auth_login_tentativa_agregado` (pós-365d) |
| Worker de expurgo | `src/jobs/expurga_login_tentativa.py` (procrastinate task diária) |
| Banner D-7..D-0 troca | middleware `forcar_troca_senha.py` — checa flag `auth_must_change_password` antes de roteamento |
| Validador senha | `src/security/password_policy.py` — chamado em `LoginView.post_password_change` + `PasswordChangeView` |

## §8 — Itens a fazer (Wave A)

- [ ] Aceitar ADR-0038.
- [ ] Adicionar INV-AUTH-001..005 em REGRAS-INEGOCIAVEIS.md (esta Onda já cobre).
- [ ] Migration `0008_auth_login_tentativa.py` (tabela detalhada + agregado).
- [ ] Migration `0009_auth_senha_historico.py` (histórico 5 senhas).
- [ ] Hook `auth-policy-check.sh` (valida LoginView/PasswordChangeView).
- [ ] Hook `pii-em-authz-decisions-check.sh` (denylist §6).
- [ ] Testes E2E: 3 (`test_inv_auth_001_lockout`, `test_inv_auth_002_politica_senha`, `test_inv_auth_003_sessao_idle`).
