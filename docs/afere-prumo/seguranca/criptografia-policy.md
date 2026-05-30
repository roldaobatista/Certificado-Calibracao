---
owner: <SecurityOwner>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 220
proposito: política de criptografia — cifras obrigatórias em repouso e em trânsito, hash de senhas, cifras proibidas, gestão de certificados e exceções
---

<!--
template: criptografia-policy.template.md
destino: docs/seguranca/criptografia-policy.md
uso: política única do projeto sobre cifragem. Vinculada a INV-SEC-CRYPTO-* e ao threat-model.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6
revisão obrigatória: 12 meses, ou ao surgir vulnerabilidade pública na cifra usada, ou ao mudar provedor de KMS/HSM.
-->

# Política de Criptografia — Aferê Prumo

> **Criptografia** = embaralhar dado com uma chave de modo que só quem tem a chave consegue ler. Esta política define **quais algoritmos podemos usar e quais estão proibidos**. Cifra fraca expõe dado mesmo quando o atacante não invade nada — basta ler do disco ou da rede.

## 1. Princípios não-negociáveis

- **Padrão é cifrar.** Dado pessoal, segredo, credencial — sempre cifrado em repouso E em trânsito. "Não cifrar" exige ADR + assinatura do DPO.
- **Algoritmo público, chave secreta.** Nunca confiar em "algoritmo secreto" — princípio de Kerckhoffs.
- **Default seguro.** Configuração padrão da biblioteca usa cifra forte. Não permitir downgrade silencioso (ex: cliente velho aceitar TLS 1.0).
- **Atualizar quando quebra.** Se NIST/OWASP/CWE classifica algoritmo como obsoleto, migrar dentro de 90 dias.

## 2. Cifras obrigatórias

### 2.1 Em repouso (disco, banco, backup)

| Uso | Algoritmo obrigatório | Modo | Tamanho mínimo da chave | Observação |
|---|---|---|---|---|
| Banco de dados (cifra a nível de disco) | **AES-256** | **GCM** | 256 bits | TDE do SGBD OU LUKS / dm-crypt no SO. Chave no KMS. |
| Coluna sensível (PII, dado bancário) | **AES-256** | **GCM** ou **GCM-SIV** | 256 bits | Cifra a nível de aplicação ANTES de gravar. |
| Backup | **AES-256** | **GCM** | 256 bits | Chave **diferente** da chave do banco em produção. |
| Arquivo em bucket (S3 / GCS / Azure Blob) | **AES-256** (SSE-KMS) | GCM ou CBC do provedor | 256 bits | Preferir CMK gerenciada (chave nossa, não do provedor). |
| Segredo no cofre | **AES-256** | conforme cofre (Vault, KMS) | 256 bits | Acesso só por identidade de carga + audit log. |

### 2.2 Em trânsito (rede)

| Uso | Protocolo mínimo | Cifras aceitas | Observação |
|---|---|---|---|
| HTTP público (Internet) | **TLS 1.3** (mínimo TLS 1.2) | suites AEAD: `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`, `TLS_AES_128_GCM_SHA256` | Desabilitar TLS 1.0 / 1.1 / SSLv3. |
| Rede interna (serviço↔serviço) | **mTLS 1.3** | mesmas suites do público | Cliente e servidor se autenticam — ambos provam identidade. |
| Banco de dados | **TLS 1.2+** | suite AEAD | Forçar `sslmode=verify-full` (Postgres) ou equivalente. |
| Fila / mensageria | **TLS 1.2+** | suite AEAD | Cliente valida cert do broker. |
| SSH | **SSHv2** com curvas modernas (Ed25519) | ChaCha20-Poly1305 ou AES-256-GCM | Desabilitar protocolo 1 e cifras CBC fracas. |

### 2.3 Hash de senha

Senha **nunca** é guardada em texto, **nunca** é cifrada (cifrada é reversível — senha não pode ser reversível). É **hasheada** com função lenta e com sal.

| Algoritmo | Parâmetros mínimos | Quando usar |
|---|---|---|
| **Argon2id** (preferido) | `memory=64MiB, iterations=3, parallelism=4` | Aplicação nova. Recomendado pela OWASP 2023+. |
| **bcrypt** | `cost ≥ 12` | Aplicação existente que não pode migrar imediatamente. Migrar para Argon2id no próximo grande release. |
| **scrypt** | `N=2^17, r=8, p=1` | Aceito quando o ecossistema só oferece scrypt. |
| **PBKDF2-HMAC-SHA256** | `iterations ≥ 600.000` | Último recurso (FIPS/compliance que exige). |

**Sal obrigatório:** ≥16 bytes aleatórios, único por senha, armazenado junto.

### 2.4 Hash de integridade (não-senha)

| Uso | Algoritmo | Observação |
|---|---|---|
| Integridade de arquivo / log encadeado | **SHA-256** ou **SHA-512** ou **BLAKE3** | Para conferir que não foi alterado. |
| HMAC (assinar mensagem com chave) | **HMAC-SHA-256** ou **HMAC-SHA-512** | Sempre que precisar provar autoria de payload. |
| Assinatura digital | **Ed25519** (preferido) ou **ECDSA-P256** ou **RSA-PSS-2048+** | Release, JWT, certificado. |

## 3. Cifras e práticas PROIBIDAS

> Bloquear no CI (lint de segurança — gitleaks, semgrep, eslint-plugin-security) qualquer ocorrência destas.

| Item | Por que proibido |
|---|---|
| **MD5** | Colisões trivialmente exploráveis desde 2004. Não usar nem para hash não-criptográfico (risco de regressão). |
| **SHA-1** | Colisões exploradas em produção (SHAttered, 2017). Proibido inclusive em assinatura. |
| **DES, 3DES** | Bloco de 64 bits — vulnerável a SWEET32. |
| **RC4** | Quebrado em TLS desde 2013 (RFC 7465 proíbe). |
| **AES-ECB** | Modo ECB vaza padrões — nunca usar para mais de 1 bloco. |
| **AES-CBC sem MAC** | Vulnerável a padding oracle. Se CBC, exigir HMAC (encrypt-then-MAC). |
| **Senha em texto plano** | Inclusive em log, exceção, mensagem de erro, e-mail de recuperação. |
| **Senha hasheada com MD5/SHA-1/SHA-256 puros** | Hash rápido = ataque de dicionário trivial. Usar Argon2id/bcrypt. |
| **TLS 1.0 / TLS 1.1 / SSLv2 / SSLv3** | Vulnerabilidades exploráveis (POODLE, BEAST). |
| **Self-signed cert em produção** | Aceita apenas em ambiente de teste isolado. |
| **Chave hardcoded no código** | Sempre cofre. INV-SEC-KMS-01. |
| **IV/nonce reutilizado em GCM** | Quebra catastroficamente a confidencialidade E a integridade. Sempre gerar aleatório por mensagem. |
| **Random fraco (`Math.random`, `rand()` de C)** | Usar CSPRNG do SO (`/dev/urandom`, `crypto.randomBytes`, `secrets` no Python). |

## 4. Gestão de certificados

| Item | Política |
|---|---|
| Emissor para produção externa | CA pública confiável (Let's Encrypt, DigiCert, etc.). |
| Emissor para mTLS interno | CA privada gerenciada (ex: HashiCorp Vault PKI, AWS Private CA, step-ca). |
| Validade máxima | 90 dias (recomendação CA/Browser Forum). Renovação automatizada (cert-manager, certbot). |
| Tamanho da chave | RSA-2048+ ou ECDSA-P256+. Preferir ECDSA por desempenho. |
| Cipher suites permitidas | Definidas na seção 2.2. |
| Monitoramento de expiração | Alerta com ≥14 dias de antecedência. Métrica de SLO. |
| HSTS (HTTP Strict Transport Security) | Obrigatório em produção. `max-age` ≥ 1 ano, `includeSubDomains`, `preload` quando aplicável. |
| Revogação | OCSP stapling habilitado. Lista de cert revogado verificada. |

## 5. Geração e armazenamento de material criptográfico

- **Geração**: sempre via CSPRNG do SO ou de biblioteca auditada (`crypto.randomBytes`, `secrets.token_bytes`, `os/rand` em Go, `rand` em Rust).
- **Armazenamento**: cofre dedicado (KMS, HSM, Vault, AWS Secrets Manager). **Nunca** em `.env` commitado, **nunca** em variável de ambiente exportada em script versionado.
- **Ciclo de vida das chaves**: ver `key-management-policy.md` (documento separado).

## 6. Exceções

Toda exceção a esta política exige:

1. **ADR explícito** (`docs/adr/ADR-NNNN-excecao-cripto-<motivo>.md`) descrevendo o porquê.
2. **Aprovação** do Security Owner E do DPO (se envolver dado pessoal).
3. **Prazo** de remoção da exceção (máximo 12 meses; renovável com nova aprovação).
4. **Mitigação compensatória** documentada (ex: rotação mais frequente, audit log adicional).
5. **Linha em** `docs/seguranca/excecoes-cripto.md` listando exceção, motivo, prazo, owner.

> **Exemplo preenchido (aceitável):**
> ADR-0042 — uso temporário de PBKDF2-HMAC-SHA256 600k iterações no módulo `legacy-import` por compatibilidade com cofre Corporativo CA-XYZ que ainda não suporta Argon2id. Mitigação: rotação de senha forçada a cada 90 dias; migração para Argon2id agendada até 2026-12-31. Owner: <nome>.

## 7. Vinculação

- `threat-model.md` — ameaças mitigadas por esta política.
- `key-management-policy.md` — ciclo de vida das chaves usadas aqui.
- `SECURITY.md` — política externa (canal de divulgação).
- `INV-SEC-CRYPTO-*` — invariantes testadas em CI que comprovam aderência.
- ADRs sobre escolha de algoritmo / biblioteca de cripto.

## 8. Checklist de promoção draft → stable

- [ ] Todas as cifras listadas em §2 estão implementadas e testadas (INV-SEC-CRYPTO-*).
- [ ] CI bloqueia cifras proibidas (§3) via lint de segurança.
- [ ] Pipeline de TLS testado com `testssl.sh` ou `sslyze` (sem nota abaixo de A).
- [ ] Gestão de certificados (renovação, alerta, monitor) está ativa.
- [ ] Exceções (se houver) têm ADR aprovado e prazo registrado.
- [ ] `revisado-em` atualizado; `status: stable`.
