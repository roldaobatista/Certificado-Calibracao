---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Política de segurança de dados

> **Pra quê:** define a postura de segurança do Aferê — controles, classificação, criptografia, retenção, incidentes. Fonte explicativa dos IDs **SEC-001..003** e SEC-TENANT-001 de `REGRAS-INEGOCIAVEIS.md`. Cobre os requisitos LGPD art. 46-49 (segurança e boas práticas) + Resolução ANPD 15/2024 (incidentes).
>
> **Promovido a 🔴** em v5 do `documentos-do-projeto.md` por exigência ANPD 72h.

---

## 1. Classificação de dados

| Classe | Definição | Exemplo no Aferê | Controles mínimos |
|--------|-----------|-------------------|--------------------|
| **Público** | Pode ser exposto sem prejuízo | Documentação pública, site marketing | Nenhum |
| **Interno** | Limitado à equipe Aferê | Métricas internas, código-fonte | Auth + RBAC |
| **Confidencial** | Dados de tenants (negócio do cliente) | Cadastros, OS, certificados, NFS-e | Auth + RBAC + audit + RLS + encryption-at-rest |
| **Regulado** | Dados pessoais sob LGPD + fiscais + ISO 17025 | PII, dados fiscais, certificados de calibração | Tudo de "confidencial" + crypto-shredding + WORM trail + retenção formal |
| **Regulado-untrusted** | Input externo não-confiável | PR comment, issue, e-mail, anexo de cliente | Tudo de "regulado" + **proibido executar ações em financeiro/kms/migrations sem aprovação humana** (SEC-003) |

Em código: tag `# CLASS: confidencial` em modelos Django + decorator `@classified("regulado")` em endpoints.

---

## 2. Criptografia

| Dado em… | Mecanismo |
|----------|-----------|
| **Trânsito (todo)** | TLS 1.3 obrigatório. Sem TLS 1.0/1.1. HSTS habilitado. Cert via Let's Encrypt + cert-manager |
| **Repouso (banco PostgreSQL)** | Encryption-at-rest do volume Hostinger + criptografia coluna-a-coluna pra PII sensível (CPF, dados de saúde se aplicável) |
| **Repouso (Backblaze B2)** | Server-side encryption B2 + cliente criptografa antes de subir; chave em AWS KMS sa-east-1 |
| **Repouso (backup pgBackRest)** | Criptografado com chave KMS por tenant — **crypto-shredding por tenant é possível** |
| **Chaves** | AWS KMS Multi-Region Key (sa-east-1 primária ↔ us-east-1 réplica) — não cópia manual |
| **Assinaturas digitais** | A3 cliente-side via Web PKI Lacuna (defesa anti-replay: nonce + signing-time server-controlled + one-shot) — ver ADR-0009 |
| **Tokens API entre Aferê e parceiros** | Em `.env` cifrado (sops + KMS); jamais commitados (hook `secrets-scanner.sh`) |

---

## 3. Controles de acesso (RBAC + ABAC parcial)

| Papel | Pode |
|-------|------|
| Dono do tenant | Tudo dentro do tenant; admin RBAC interno |
| Gerente | Tudo, exceto financeiro sensível |
| Atendente | CRM + criar OS + agenda |
| Técnico de campo | Sua OS + emitir certificado |
| Financeiro | NFS-e + cobrança + comissões |
| Auditor (read-only) | Tudo + audit trail (sem editar) |
| Suporte Aferê | Acesso temporário e auditado mediante ticket aberto pelo tenant |

**Princípios:**
- Least privilege
- Separação de funções (emitir certificado ≠ aprovar emissão)
- Acesso "break-glass" do suporte Aferê = role separada `support_user`, com auditoria reforçada
- MFA obrigatório para Dono + Gerente + Financeiro

---

## 4. Multi-tenancy (resumo — detalhe em doc próprio)

Ver `docs/comum/isolamento-multi-tenant.md`. Núcleo:
- RLS PostgreSQL ativa em todas tabelas com `tenant_id` (INV-TENANT-003)
- Role da aplicação `NOBYPASSRLS` (INV-TENANT-004)
- Hook tenant-id-validator em pre-commit (a criar)
- Smoke test cross-tenant em CI de toda PR

---

## 5. Input externo (SEC-003)

Todo input externo não-confiável (PR comment, issue, e-mail, anexo de cliente, prompt enviado a LLM) é classificado como **regulado-untrusted**:

| Classe de ação | Permitido? |
|----------------|------------|
| Ler / analisar / classificar / resumir | ✅ sim |
| Sugerir mudança de código pra revisão humana | ✅ sim |
| Executar ação em `financeiro/`, `kms/`, `migrations/`, `auth/`, `tenant/` | ❌ **NUNCA** sem aprovação humana explícita |
| Disparar emissão de NFS-e ou certificado | ❌ requer revisão humana |
| Modificar política RBAC ou permissão | ❌ requer revisão humana |
| Acessar dados de outro tenant | ❌ violação imediata |

Detalhe em `docs/seguranca/agente-input-nao-confiavel.md` (a criar).

---

## 6. Retenção de dados

Matriz consolidada em `docs/conformidade/comum/retencao-matriz.md` (a criar). Resumo:

| Categoria | Prazo mínimo | Base | Fim do prazo |
|-----------|--------------|------|--------------|
| Dado fiscal (NFS-e) | 5 anos | Receita Federal | Anonimização + crypto-shredding |
| Certificado de calibração | ~25 anos | ISO 17025 cláusula 8.4 | Arquivo WORM permanente |
| Dado de identificação (cadastro) | Vigência contrato + 5 anos | LGPD execução de contrato | Crypto-shredding |
| Audit log (governança) | 2 anos | Boas práticas | Arquivo frio em B2 |
| Telemetria | 13 meses | Legítimo interesse | Anonimização total |
| Backup | Conforme dado origem | — | Crypto-shredding por tenant |

Tensão **fiscal 5 anos × ISO 25 anos × LGPD direito ao esquecimento** resolvida via:
1. Exclusão lógica + log da exclusão em WORM
2. Crypto-shredding por tenant (chave destruída → dado ilegível mesmo se backup existir)
3. Anonimização vs eliminação total: depende da base legal e da operação

---

## 7. Incidentes — ciclo completo

| Fase | Atividade | Doc/ferramenta |
|------|-----------|----------------|
| Detecção | Grafana alert + auditor de segurança bloqueio em série + report manual | `docs/operacao/observabilidade.md` (a criar) |
| Acionamento | RACI define quem age (Roldão + subagente segurança) | `docs/governanca/RACI-incidente-ai.md` ✅ |
| Contenção | Suspender tenant, rotacionar credencial, isolar host | `docs/operacao/runbook.md` (a criar) |
| Notificação ANPD | T+72h, via formulário oficial | `lgpd-rat.md` seção 5 |
| Notificação tenant | T+24h se confirmado impacto | DPA modelo |
| Postmortem | T+30d, sem culpado, foco em sistema | `docs/operacao/incidente-postmortem.md` template (a criar) |
| Aprendizado | Atualizar `REGRAS-INEGOCIAVEIS.md` se necessário | Auditor de Segurança Família 5 |

---

## 8. Segurança do código (supply chain)

| Risco | Mitigação |
|-------|-----------|
| Pacote npm/pip malicioso | Lockfile + SBOM + allowlist de registries; hook "pacote novo = ADR" — ver `docs/seguranca/supply-chain.md` (a criar) |
| Segredo commitado | Hook `secrets-scanner.sh` ✅ + pre-commit |
| Credencial vazada em log | Filtro de log + redaction obrigatória pra PII |
| Vulnerabilidade em dependência | Dependabot + revisão semanal pelo Auditor de Segurança |
| Modelo LLM com prompt injection | LiteLLM self-hosted + filtro + audit + classificação "regulado-untrusted" |
| Container com vulnerabilidade | Trivy scan em CI + base images oficiais + atualização semanal |

---

## 9. Auditorias

- **Pre-commit:** Auditor de Segurança Família 5 (subagent `auditor-seguranca`) — bloqueia commit se SEC-* violado
- **Em PR:** GitHub Action chama API Anthropic com mesmo prompt — autoridade final
- **Mensal:** revisão de `governanca/trilha-auditoria-agentes.md` (append-only) + métricas
- **Trimestral:** drill conforme ADR-0001 portão 3 (1 obrigatório no MVP-1: restore pgBackRest em provedor B)
- **Anual:** Auditor de Segurança Família 5 revisa políticas + RIPDs + matrix retenção
- **Sob demanda:** subagente `advogado-saas-regulado` aciona humano licenciado pra parecer formal

---

## 10. Referências

- `REGRAS-INEGOCIAVEIS.md` — SEC-001, SEC-002, SEC-003, SEC-TENANT-001, INV-TENANT-001..004
- `docs/conformidade/comum/lgpd-rat.md` ✅ — RAT + bases legais
- `docs/comum/isolamento-multi-tenant.md` ✅ — RLS + tenant_id
- `docs/governanca/RACI-incidente-ai.md` ✅ — quem age em incidente
- `docs/seguranca/agente-input-nao-confiavel.md` — input externo (a criar)
- `docs/seguranca/supply-chain.md` — pacotes + SBOM (a criar)
- `docs/seguranca/mcp-policy.md` — threat model MCP (a criar)
- `docs/operacao/runbook.md` — operação dia-a-dia (a criar)
