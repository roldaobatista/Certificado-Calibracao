---
owner: <SecurityOwner>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 240
proposito: política de ciclo de vida de chaves criptográficas — geração, armazenamento, rotação, revogação, destruição, separação de funções e auditoria
---

<!--
template: key-management-policy.template.md
destino: docs/seguranca/key-management-policy.md
uso: política única do projeto sobre chaves. Complementa a política de criptografia (que define o algoritmo). Esta define o ciclo de vida (quem gera, onde guarda, quando troca, quem audita).
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6
revisão obrigatória: 12 meses ou após troca de KMS/HSM ou após incidente envolvendo chave.
-->

# Política de Gestão de Chaves — Aferê Prumo

> **Chave criptográfica** = a "senha que destranca o cofre" da cifra. O algoritmo (AES, RSA) é público; a segurança depende **inteiramente** de a chave ser secreta, gerada de forma aleatória, guardada em lugar seguro e trocada periodicamente. Esta política descreve o **ciclo de vida** de toda chave do projeto: nasce, vive, é rotacionada, é revogada quando necessário, e é destruída ao fim da vida útil.

## 1. Princípios não-negociáveis

- **Nunca em código.** Toda chave vive em cofre dedicado (KMS, HSM, Vault). Código pega a chave em runtime via identidade de carga.
- **Separação de funções.** Quem gera a chave NÃO é quem audita o uso dela. Quem opera o cofre NÃO é o único com acesso ao log.
- **Rotação programada.** Toda chave tem prazo de expiração. Sem prazo = vulnerabilidade.
- **Princípio do menor privilégio.** Cada serviço acessa só as chaves que precisa, só pelas operações que precisa (cifrar vs decifrar vs assinar).
- **Auditoria ativa.** Toda operação de uso de chave fica registrada (quem, quando, qual chave, qual operação). Log imutável.

## 2. Tipos de chave usados no projeto

| Tipo de chave | Para que serve | Algoritmo | Tamanho | Onde vive |
|---|---|---|---|---|
| **DEK** (Data Encryption Key) | cifrar dado em repouso (coluna, arquivo, backup) | AES-256-GCM | 256 bits | gerada no momento, cifrada pela KEK, guardada junto com o dado (envelope encryption) |
| **KEK** (Key Encryption Key) | cifrar DEKs | AES-256 | 256 bits | KMS/HSM — **nunca** sai do cofre |
| **Master Key** | derivar KEKs | gerenciada pelo provedor de KMS | conforme provedor | HSM do provedor |
| **TLS server key** | autenticar servidor em TLS | ECDSA-P256 ou RSA-2048+ | 256 / 2048+ bits | cofre + servidor (carregada em memória no boot) |
| **mTLS client key** | autenticar serviço cliente | ECDSA-P256 | 256 bits | cofre, montada via CSI/secrets driver |
| **JWT signing key** | assinar token de autenticação | Ed25519 ou RS256 | 256 / 2048+ bits | cofre — kid rotativo |
| **Release signing key** | assinar artefato publicado | Ed25519 ou GPG RSA-4096 | 256 / 4096 bits | hardware token (YubiKey) ou HSM offline |
| **Database master password** | abrir conexão admin no SGBD | senha forte (≥32 chars) | n/a | cofre |
| **Backup encryption key** | cifrar backup antes de subir pro cold storage | AES-256-GCM | 256 bits | cofre **diferente** do banco — se invadem produção, não invadem backup |

## 3. Geração

| Requisito | Política |
|---|---|
| Fonte de entropia | CSPRNG do SO (`/dev/urandom`, `BCryptGenRandom` no Windows) ou HSM certificado FIPS 140-2 Nível 3+ |
| Bibliotecas aceitas | OpenSSL ≥3.0, libsodium, BoringSSL, biblioteca nativa do KMS do provedor. Proibido: `Math.random`, `rand()` de C, `random.random()` do Python. |
| Ambiente | chave de produção é gerada **dentro** do cofre/HSM, nunca em laptop de dev nem em CI compartilhado |
| Comprovação | log do cofre registra geração com timestamp, identidade que solicitou, tipo e tamanho |

> **Exemplo preenchido:**
> Toda DEK de coluna nasce via `aws kms generate-data-key --key-id alias/<projeto>-kek-prod --key-spec AES_256`. A AWS retorna a DEK em claro (usada uma vez, descartada da memória) + a DEK cifrada (gravada junto com o dado). A KEK nunca sai do KMS.

## 4. Armazenamento

### 4.1 Onde pode

| Local | Tipo de chave aceito | Observação |
|---|---|---|
| HSM dedicado (CloudHSM, Thales, YubiHSM) | Master Key, KEK crítica, Release signing key | Nível mais alto. Obrigatório para PCI-DSS, eIDAS qualificado. |
| KMS gerenciado (AWS KMS, GCP KMS, Azure Key Vault) | KEK, JWT signing, TLS server | Bom padrão para SaaS regulado. |
| Vault (HashiCorp / OpenBao) | TLS server, DB password, qualquer segredo de aplicação | Self-hosted ou gerenciado. |
| Secrets Manager do provedor (AWS Secrets Manager, GCP Secret Manager) | DB password, API key de terceiro | Bom para projetos cloud-native. |
| Hardware token (YubiKey) | Release signing offline, SSH | Para chaves usadas raramente, alta criticidade. |

### 4.2 Onde NÃO pode (jamais)

- Repositório Git (público OU privado) — gitleaks bloqueia.
- Arquivo `.env` commitado.
- Variável de ambiente em pipeline cujo log é visível para devs.
- Anexo de e-mail / Slack / WhatsApp.
- Anotação em wiki / Notion / Confluence sem cifragem.
- Disco local de laptop sem cifragem (FileVault / BitLocker / LUKS obrigatórios).
- Print/screenshot — mesmo apagado depois, fica em backup do SO.

## 5. Rotação programada

| Tipo de chave | Frequência mínima | Gatilho de rotação extra |
|---|---|---|
| DEK (envelope) | a cada uso (efêmera) | n/a — gerada por mensagem/registro |
| KEK | **anual** | suspeita de comprometimento; saída de pessoa com acesso |
| Master Key | **a cada 2 anos** | igual à KEK |
| TLS server cert | **90 dias** (automático via cert-manager / certbot) | revogação da CA; comprometimento |
| mTLS client cert | **90 dias** | igual ao TLS server |
| JWT signing key | **a cada 90 dias** (kid rotativo, suporte a 2 chaves ativas durante transição) | comprometimento; mudança de algoritmo |
| Release signing key | **anual** | comprometimento; saída do mantenedor principal |
| Database password (admin) | **180 dias** | saída de DBA; suspeita |
| API key de terceiro (Stripe, SendGrid, etc.) | **90 dias** | log incomum no provedor; vazamento detectado |
| SSH key pessoal de mantenedor | **anual** | troca de máquina; suspeita |
| Backup encryption key | **anual** | igual à KEK |

**Processo padrão de rotação:**

1. Gerar nova chave (no cofre).
2. Cadastrar nova como "ativa para escrever".
3. Manter antiga como "ativa para ler" durante janela de coexistência (mínimo 24h, ou até último dado cifrado pela antiga ser re-cifrado).
4. Re-cifrar dados que precisam migrar (em background).
5. Marcar antiga como "revogada" — não pode mais decifrar nem assinar.
6. Após período de retenção legal (ver §7), destruir.
7. Registrar no log de auditoria.

## 6. Revogação (gatilhos)

Revogar **imediatamente** ao identificar:

- Vazamento confirmado ou suspeito (`git push` de segredo, log público, dump).
- Comprometimento do dispositivo onde a chave era usada (laptop roubado, servidor invadido).
- Saída de pessoa com acesso administrativo ao cofre.
- Fim do contrato com fornecedor que tinha acesso (operador, suboperador).
- Detecção de uso anômalo no log do cofre (geografia, horário, volume incomum).
- Algoritmo da chave classificado como obsoleto pela NIST/OWASP/ANPD.

**Procedimento de revogação:** segue o runbook `docs/operacao/runbooks/incidente-seguranca.md`. Após revogação, abrir post-mortem se houve comprometimento real.

## 7. Destruição segura (fim de vida)

Quando a chave é destruída:

- KMS gerenciado: usar API de scheduled deletion (AWS: 7-30 dias de pending; GCP: 24h-30 dias). Esse delay é proteção contra erro humano.
- HSM físico: zeroização via comando do HSM. Log do HSM registra evento.
- Hardware token: destruição física (corte do chip) quando descartado.
- Retenção legal mínima: ver legislação aplicável (LGPD não exige reter chave após eliminação do dado; algumas normas setoriais sim — ver `mercado-regulatorio.md`).
- Registro: log imutável (WORM) com timestamp, quem solicitou, motivo, confirmação.

## 8. Papéis e responsabilidades (separação de funções)

| Papel | Pode | Não pode |
|---|---|---|
| **Key Custodian** (custodiante) | gerar, rotacionar, revogar chaves no cofre | acessar dado cifrado pelas chaves; usar chave em aplicação |
| **Operador de aplicação** | usar chave via API do cofre (cifrar/decifrar para a aplicação) | exportar chave em claro; gerar nova chave em produção |
| **Auditor** | ler log do cofre; verificar conformidade da política | gerar, usar ou revogar chave |
| **DPO** | aprovar exceções; revisar política | operar tecnicamente o cofre |
| **DevOps / SRE** | configurar cofre, IAM, política de acesso | acessar conteúdo cifrado |

> **Separação mínima:** ninguém acumula `Key Custodian` + `Auditor` no mesmo papel. Se a equipe é pequena (≤2 pessoas), aceitar exceção via ADR com mitigação compensatória (ex: log encaminhado para auditor externo).

## 9. Auditoria

| Item auditado | Frequência | Responsável | Como |
|---|---|---|---|
| Log de acesso ao cofre (quem, quando, qual chave, qual operação) | revisão mensal | Auditor | dashboard + alerta para padrões anômalos |
| Inventário de chaves ativas vs documentadas aqui | trimestral | Security Owner | script que lista chaves do cofre e confere contra esta política |
| Rotações em dia (nenhuma chave expirada-mas-ativa) | mensal automático | pipeline CI | falha se chave passou do prazo |
| Conformidade com política | anual | Auditor externo (quando aplicável) | revisão documental + amostra de operações |
| Teste de incidente de chave (key compromise drill) | anual | Security Owner | simular revogação + medir RTO |

## 10. Exceções

Toda exceção a esta política exige:

1. ADR (`docs/adr/ADR-NNNN-excecao-kms-<motivo>.md`).
2. Aprovação do Security Owner + DPO.
3. Prazo máximo de 6 meses.
4. Mitigação compensatória.
5. Linha em `docs/seguranca/excecoes-kms.md`.

## 11. Vinculação

- `criptografia-policy.md` — algoritmos que estas chaves usam.
- `threat-model.md` — ameaças mitigadas (Spoofing, Information Disclosure, Elevation).
- `SECURITY.md` — política externa de rotação publicada.
- `INV-SEC-KMS-*` — invariantes que validam (ex: nenhuma chave hardcoded; rotação dentro do prazo).
- Runbooks: `incidente-seguranca.md`, `rotacao-emergencial-de-chave.md`.

## 12. Checklist de promoção draft → stable

- [ ] Inventário §2 reflete chaves reais em uso (validado por script automatizado).
- [ ] Toda chave de §2 tem dono, prazo de rotação, local de armazenamento documentado.
- [ ] Separação de funções §8 implementada na IAM do cofre.
- [ ] Auditoria §9 com primeiro ciclo concluído (log do mês corrente revisado).
- [ ] Runbook de revogação testado em drill.
- [ ] Exceções (se houver) com ADR aprovado.
- [ ] `revisado-em` atualizado; `status: stable`.
