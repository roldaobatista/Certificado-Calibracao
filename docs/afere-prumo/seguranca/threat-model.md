---
owner: <SecurityOwner>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 250
proposito: modelagem de ameaças (STRIDE) do projeto — componentes, atacantes, ameaças, mitigações, risco residual e dono de aceitação
---

<!--
template: threat-model.template.md
uso: copiar para docs/segurança/threat-model.md.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6
revisão obrigatória: 12 meses ou ao mudar trust boundary / adicionar componente novo / após incidente.
-->

# Threat Model — Aferê Prumo

> **Documento CONDICIONAL.** Aplica-se a projeto regulado, que trate dado pessoal ou que tenha superficie exposta relevante. Se o produto e uma ferramenta local sem dado de terceiros e sem exposicao de rede, **nao preencha** — registre o motivo em `docs/nao-aplica.md`.

> **Modelo de ameacas** = mapa do que pode dar errado de proposito. Identificamos componentes, atacantes, ameacas e as defesas contra elas. **TTL de revisao: 12 meses** (ou ao adicionar componente novo, mudar trust boundary, ou apos incidente).

## 1. Escopo

Componentes incluidos nesta versao do modelo:

| Componente | Tipo | Trust zone |
|---|---|---|
| <api-publica> | servico HTTP exposto na Internet | externa |
| <api-interna> | servico HTTP so acessivel via rede privada | interna |
| <banco-de-dados> | armazenamento persistente | privada |
| <cofre-de-segredos> | gestao de credenciais | privada-restrita |
| <fila-de-eventos> | mensageria assincrona | interna |
| <cliente-web/mobile> | aplicacao do usuario final | nao-confiavel |

Fora do escopo: <listar — ex: dependencias de terceiros sob SLA proprio, infra do provedor cloud abaixo da camada IaaS>.

## 2. Data flow diagram (DFD textual)

```
[Cliente]
   |  (1) HTTPS + JWT
   v
[API publica] ----(2) SQL + TLS----> [Banco]
   |  (3) gRPC interno + mTLS
   v
[API interna] ----(4) AMQP TLS----> [Fila] --(5) consumer mTLS--> [Worker]
   |
   v
[Cofre] (acesso somente via IAM short-lived token)
```

Numeracao dos fluxos vira referencia das ameacas na secao 5.

## 3. Assets criticos

| Asset | Tipo | Criticidade | Onde vive |
|---|---|---|---|
| <dados-pessoais-clientes> | dado | alta (LGPD Art. 5) | banco principal + backups |
| <credenciais-de-servico> | segredo | critica | cofre |
| <chave-de-assinatura-release> | segredo | critica | hardware token |
| <logs-de-auditoria> | dado | alta (integridade) | bucket append-only |
| <infra-de-build-e-deploy> | infra | alta | <provedor-ci> |
| <codigo-fonte> | propriedade intelectual | media-alta | repositorio + mirror |

## 4. Perfis de atacante

| Perfil | Capacidade | Motivacao | Vetor tipico |
|---|---|---|---|
| **Externo casual** | scripts publicos, scanners | curiosidade, defacement | endpoints expostos, credenciais default |
| **Externo direcionado** | tempo, recursos, exploits 0-day | financeira, espionagem, sabotagem | spear phishing, exploracao de cadeia de dependencias |
| **Insider acidental** | acesso legitimo | erro humano | comando errado, vazamento de log, commit de segredo |
| **Insider malicioso** | acesso legitimo + conhecimento interno | retaliacao, financeira | exfiltracao via canal legitimo, sabotagem |
| **Supply chain** | controle de dependencia upstream | financeira, posicionamento | pacote comprometido, typosquatting, build server invadido |

## 5. STRIDE por componente

> **STRIDE** = Spoofing (forjar identidade), Tampering (adulterar dado), Repudiation (negar acao realizada), Information disclosure (vazar dado), Denial of Service (derrubar), Elevation of privilege (ganhar acesso alem do permitido).

### 5.1 API publica

| Categoria | Ameaca | Mitigacao | Controle (auditor/hook/INV) | Teste automatico que prova mitigacao | Risco residual | Owner aceitacao | Revisao |
|---|---|---|---|---|---|---|---|
| Spoofing | atacante forja token JWT | assinatura assimetrica (RS256), kid rotativo, validacao de iss/aud | INV-SEC-AUTH-01 | `tests/security/auth_invalid_jwt.*` | baixo | <security-owner> | anual |
| Tampering | replay de request autenticado | nonce + janela curta (5min) + idempotency-key | INV-SEC-AUTH-02 | `tests/security/replay_protection.*` | baixo | <security-owner> | anual |
| Repudiation | usuario nega acao destrutiva | audit log append-only com hash encadeado | INV-AGENT-AUDIT-01 | `tests/security/audit_log_append_only.*` | baixo | <dpo> | anual |
| Info disclosure | mensagem de erro vaza stack/SQL | error handler que sanitiza em prod | INV-SEC-ERR-01 | `tests/security/error_sanitization.*` | baixo | <security-owner> | anual |
| DoS | flood de requests | rate-limit por IP + por token + circuit breaker | INV-SEC-RL-01 | `tests/security/rate_limit.*` | medio | <ops-owner> | semestral |
| Elevation | bypass de autorizacao em rota privada | guard centralizado + teste por rota | INV-SEC-AUTHZ-01 | `tests/security/authz_matrix.*` | baixo | <security-owner> | anual |

### 5.2 Banco de dados

| Categoria | Ameaca | Mitigacao | Controle | Teste automatico que prova mitigacao | Risco residual | Owner | Revisao |
|---|---|---|---|---|---|---|---|
| Tampering | escrita direta fora da aplicacao | acesso somente via role da app + audit no SGBD | INV-SEC-DB-01 | `tests/security/db_role_permissions.*` | baixo | <dba> | anual |
| Info disclosure | dump do banco roubado | criptografia em repouso + acesso a backup com MFA | INV-SEC-DB-02 | `tests/security/backup_encryption_policy.*` | baixo | <dba> | anual |
| DoS | query custosa derruba banco | timeout + statement_timeout + pool limit | INV-SEC-DB-03 | `tests/performance/query_timeout.*` | medio | <dba> | semestral |

> **Protecao do dado em repouso e em transito.** As mitigacoes de "Info disclosure" acima (criptografia em repouso, em transito, acesso a backup) seguem os algoritmos e parametros definidos em `docs/seguranca/criptografia-policy.md`. As chaves usadas nessa criptografia (geracao, guarda, rotacao e revogacao) seguem `docs/seguranca/key-management-policy.md` — uma chave mal gerida derruba toda a protecao mesmo com algoritmo forte.

### 5.3 Cofre de segredos

| Categoria | Ameaca | Mitigacao | Controle | Teste automatico que prova mitigacao | Risco residual | Owner | Revisao |
|---|---|---|---|---|---|---|---|
| Spoofing | servico forja identidade pra puxar segredo | IAM com identidade de carga + token short-lived | INV-SEC-VAULT-01 | `tests/security/vault_identity.*` | baixo | <security-owner> | anual |
| Info disclosure | log do cofre vaza segredo | mascaramento obrigatorio no log + alerta | INV-SEC-VAULT-02 | `tests/security/secret_log_redaction.*` | baixo | <security-owner> | anual |

### 5.4 Cliente

| Categoria | Ameaca | Mitigacao | Controle | Teste automatico que prova mitigacao | Risco residual | Owner | Revisao |
|---|---|---|---|---|---|---|---|
| Tampering | cliente modificado falsifica dado | servidor nunca confia no cliente, valida tudo | INV-SEC-CLIENT-01 | `tests/security/server_side_validation.*` | baixo | <security-owner> | anual |
| Info disclosure | XSS exfiltra token | CSP estrita + httpOnly cookie + SameSite=Lax | INV-SEC-CLIENT-02 | `tests/security/csp_cookie_flags.*` | baixo | <security-owner> | anual |

## 6. Trust boundaries

| Fronteira | De → Para | Controles na travessia |
|---|---|---|
| Internet → API publica | nao-confiavel → externa | TLS, WAF, rate-limit, autenticacao |
| API publica → API interna | externa → interna | mTLS, allowlist de IP, autorizacao |
| API interna → cofre | interna → privada-restrita | IAM + token de curta duracao + audit |
| Worker → fila | interna → interna | mTLS + ACL por topico |
| Build → registry | CI → privada-restrita | OIDC federado, sem chave longa-duracao |

## 7. Attack surface

Listar todos os pontos de entrada que recebem input externo:

- Endpoints HTTP publicos: <quantos>, listados em `docs/api/openapi.yaml`.
- Webhooks recebidos de terceiros: <listar provedores>.
- Filas que consomem mensagem externa: <listar>.
- Upload de arquivo: <sim/nao, limites>.
- Formularios autenticados: <quantos>.
- Endpoints administrativos: <restritos a — IP/VPN/MFA?>.

Redução de superficie: o que nao precisa estar exposto NAO esta.

## 8. Anti-padroes a evitar

- **Timing attacks**: comparacao de hash/token com `==` curto-circuito. Usar comparacao tempo-constante.
- **Error info leakage**: stack trace em resposta de producao. Usar codigo opaco + correlacao via log.
- **API enumeration**: respostas diferentes para "usuario nao existe" vs "senha errada". Padronizar resposta.
- **Verbose headers**: `Server: nginx/1.21.x`, `X-Powered-By`. Remover ou genericar.
- **Inseguro por default**: feature flag de seguranca que vem desligada. Default deve ser seguro.
- **Confianca em IP**: allowlist sem segundo fator. IP nao e identidade.
- **Segredo em URL/query string**: vai parar em log do proxy. Usar header `Authorization`.
- **Hash de senha rapido**: MD5/SHA1/SHA256 puros. Usar Argon2id ou bcrypt com custo apropriado.

## 9. Manutencao deste modelo

- Revisao agendada **anual** (data em `revisado-em`).
- Revisao **adicional obrigatoria** ao: incluir componente novo, mudar trust boundary, alterar perfil de atacante relevante, apos incidente classificado MEDIO+.
- Cada ameaca tem **owner de aceitacao** que assina o risco residual. Sem owner = ameaca nao aceita = correcao obrigatoria.
- Cada ameaca precisa apontar para pelo menos um teste automatico, auditor ou hook verificavel. Sem prova automatica, marque `teste pendente: T-SEC-NNN` e nao feche PASS ZERO.

## 10. Vinculacao com

- `SECURITY.md` (politica geral, canal de divulgacao, SLA).
- `dependency-policy.md` (vetor supply chain).
- `criptografia-policy.md` (algoritmos e parametros das mitigacoes de protecao de dado).
- `key-management-policy.md` (ciclo de vida das chaves dessas mitigacoes).
- `INV-AGENT-AUDIT-*` (invariantes de auditoria que comprovam controles).
- `INV-SEC-*` (invariantes de seguranca testadas).
- ADRs que justificam escolha de mitigacao especifica (ex: ADR-00X — escolha de JWT vs sessao server-side).
- Auditor `auditor-seguranca` (subagente que valida controles).
- `docs/operacao/runbooks/incidente-seguranca.md` (resposta quando mitigacao falha).

## 11. Checklist de promocao draft -> stable

- [ ] Confirmado que o projeto se enquadra (regulado / trata dado pessoal / tem superficie exposta); senao, registrar em `docs/nao-aplica.md`.
- [ ] **Todo componente em producao** consta no escopo (secao 1) e no data flow (secao 2).
- [ ] STRIDE (secao 5) preenchido para cada componente, sem placeholder `<...>`.
- [ ] Mitigacoes de protecao de dado apontam para `criptografia-policy.md` e `key-management-policy.md`.
- [ ] **Toda ameaca** tem owner de aceitacao e ao menos um teste/auditor/hook que prova a mitigacao.
- [ ] Risco residual de cada ameaca esta aceito (sem owner = correcao obrigatoria).
- [ ] Trust boundaries (secao 6) e attack surface (secao 7) refletem a arquitetura atual.
- [ ] Frontmatter `revisado-em` atualizado; `status: stable`; proxima revisao agendada (max 12 meses).
