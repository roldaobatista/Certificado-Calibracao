---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Matriz de retenção de dados

> **Pra quê:** reconciliar prazos de retenção que conflitam — Receita Federal (5 anos), ISO 17025 cláusula 8.4 (~25 anos), LGPD direito ao esquecimento (sob demanda). Sem matriz explícita, time engenharia escolhe sob pressão e cria risco regulatório.
>
> **Origem:** Auditor 1+4+5 da 2ª auditoria de 10 agentes (16/05/2026).

---

## 1. Princípio

Cada categoria de dado tem:
1. **Prazo mínimo** definido por norma (Receita, ISO, ANVISA, ANATEL, BACEN)
2. **Prazo máximo razoável** definido por boas práticas + LGPD
3. **Base legal** que justifica a retenção
4. **Ação ao fim do prazo** (eliminação total, anonimização ou crypto-shredding)
5. **Local de armazenamento** (banco quente, B2 frio, WORM)

---

## 2. Matriz completa

| Categoria de dado | Prazo mín | Prazo máx | Base legal | Local | Ação fim de prazo |
|-------------------|-----------|-----------|------------|-------|---------------------|
| **NF-e / NFS-e emitida** | 5 anos | 5 anos + 90 dias | Receita Federal art. 173 CTN | PG (1 ano quente) → B2 WORM (4 anos) | Anonimização + crypto-shredding |
| **Lote fiscal (XML completo)** | 5 anos | 5 anos | Receita Federal | B2 WORM | Crypto-shredding |
| **Certificado de calibração emitido** | ~25 anos | Permanente | ISO 17025 cláusula 8.4 + boas práticas RBC | B2 WORM | Manter (NÃO eliminar — necessário pra rastreabilidade metrológica histórica) |
| **Dados de medição associados ao certificado** | ~25 anos | Permanente | ISO 17025 8.4 | B2 WORM | Manter |
| **Audit trail (toda ação de usuário)** | 2 anos | 5 anos | Boas práticas LGPD + governança | PG (90 dias) → B2 frio (resto) | Crypto-shredding |
| **Audit trail (ações em paths sensíveis: financeiro/auth/kms/migrations)** | 5 anos | 10 anos | Boas práticas + ISO 27001 (futuro) | B2 WORM | Crypto-shredding |
| **Cadastro de cliente (tenant)** | Vigência contrato + 5 anos | + 5 anos | LGPD art. 7º V (execução contrato) + Receita | PG (vigência) → B2 (5 anos) | Crypto-shredding |
| **Cadastro de pessoa física (usuário operacional do tenant)** | Vigência + 5 anos | + 5 anos | LGPD art. 7º V + execução contrato | PG → B2 | Crypto-shredding |
| **Cadastro de cliente final do tenant** | Definido pelo controlador (tenant) | 5 anos default | LGPD — controlador define | PG → B2 | Crypto-shredding (tenant decide) |
| **PII em mensagem WhatsApp / e-mail** | 1 ano | 2 anos | Legítimo interesse + opt-in | PG (90 dias) → B2 (resto) | Anonimização |
| **Telemetria + analytics** | 13 meses | 13 meses | Legítimo interesse art. 7º IX | Grafana Cloud + Axiom | Anonimização automática |
| **Logs de aplicação** | 30 dias quente + 1 ano frio | 1 ano | Boas práticas | Axiom (30d) → B2 (resto) | Eliminação |
| **GPS / localização técnico de campo** | 5 anos | 5 anos | RAT-07 + ISO 17025 (rastreabilidade ação) | PG → B2 | Crypto-shredding |
| **Foto/anexo de OS** | 5 anos | 5 anos | Execução contrato + audit | B2 | Crypto-shredding |
| **Backup completo (todos dados)** | 30 dias rotativo | 1 ano | Continuidade | B2 (chave KMS por tenant) | Crypto-shredding (chave destruída → backup ilegível) |
| **Sessão de usuário (login token)** | 24h-30 dias | 30 dias | Execução + segurança | Redis | Eliminação automática (TTL) |
| **Senha de usuário (hash)** | Vigência conta | Vigência | Execução | PG | Eliminação imediata na exclusão da conta |
| **Comunicação com ANPD / órgão regulador** | 5 anos | 10 anos | Obrigação regulatória | B2 WORM | Manter (referência futura) |
| **Contrato assinado entre Aferê e tenant (DPA, ToS, addendum)** | 5 anos após término | 10 anos | Direito civil + boas práticas | B2 WORM | Manter |

---

## 3. Como resolver conflito Receita × ISO × LGPD

### Cenário A: Certificado de calibração com PII do signatário humano
- Receita: 5 anos (se há fatura ligada)
- ISO 17025: ~25 anos
- LGPD direito ao esquecimento: titular pode pedir

**Resolução:**
- **Manter certificado** (cumprimento de obrigação regulatória — base legal LGPD art. 7º II)
- **Anonimizar PII do signatário** após 5 anos: substituir CPF por hash + manter nome + competência técnica
- Documentar a substituição em audit trail

### Cenário B: Cliente final do tenant pede exclusão (LGPD art. 18)
- Tenant é controlador; Aferê é operador
- Aferê notifica tenant em 24h; tenant decide em 15 dias úteis

**Resolução:**
1. **Exclusão lógica imediata** (flag `deleted_at`) — 15 dias de carência
2. **Após carência:** crypto-shredding (chave KMS por tenant **NÃO** é por cliente final — chave é por tenant; logo a "exclusão" é via apagamento PII + flag)
3. **Anonimização campo a campo:** nome → "Cliente anonimizado #N", e-mail → null, CPF → hash, etc.
4. **Manter referências fiscais** (NF-e emitida em nome dele permanece — base legal "obrigação fiscal")
5. **Manter certificados de calibração** em nome dele (base legal ISO 17025)
6. **Log da exclusão** em WORM: hash do request + timestamp + tenant que aprovou

### Cenário C: Tenant cancela contrato com Aferê
1. **30 dias de retenção quente** pra reativação (suspensão, não exclusão)
2. **Export completo dos dados** entregue ao tenant (portabilidade)
3. **15 dias adicionais** após confirmação de recebimento
4. **Crypto-shredding** da chave KMS do tenant — todos os backups encriptados com aquela chave ficam ilegíveis
5. **Anonimização** dos dados quentes restantes que ainda referenciam o tenant em audit log compartilhado
6. **WORM permanece** (registros fiscais e certificados ISO 17025 continuam acessíveis pra recuperação compulsória se exigido por norma)

---

## 4. Crypto-shredding — mecanismo

- Cada tenant tem **1 chave KMS própria** em AWS KMS sa-east-1 (replicada em us-east-1 via Multi-Region Key)
- Todo dado em repouso é criptografado com essa chave (envelope encryption)
- Backup pgBackRest também usa essa chave
- Storage B2 também usa essa chave (server-side + client-side)
- **Crypto-shredding = destruir a chave** → dado encriptado fica inutilizável, sem precisar tocar em mídia (Backblaze, fitas de backup, snapshots)
- Operação registrada em audit WORM compartilhado (não no audit do tenant — que já foi destruído)
- Tempo de execução: instantâneo (operação AWS KMS) + propagação eventual em caches

**O que crypto-shredding NÃO resolve:**
- Dados em cache LLM externo (OpenAI/Anthropic) — separado, não passa pela chave KMS
- Dados em logs Grafana/Axiom — esses já são anonimizados antes
- Dados em e-mails enviados (cliente final, ANPD) — não voltam

---

## 5. Drill trimestral

| ID | Cenário | Esperado |
|----|---------|----------|
| DRILL-RET-01 | NF-e emitida em 2021 deve estar acessível em 2026 | Ler de B2 WORM em < 30s |
| DRILL-RET-02 | Certificado emitido em 2020 deve estar acessível em 2046 | Documento + chain de calibração ok |
| DRILL-RET-03 | Pedido de LGPD art. 18: titular pede exclusão | Anonimização em 15 dias úteis; certificados ISO mantidos |
| DRILL-RET-04 | Tenant cancela em janeiro; em fevereiro tenta restaurar | Restore total ok |
| DRILL-RET-05 | Tenant cancelou 6 meses atrás; ANPD pede dado fiscal | NF-e acessível; PII anonimizada |
| DRILL-RET-06 | Crypto-shredding executado; pasta de backup ainda visível | Conteúdo criptografado ilegível ✓ |

---

## 6. Auditoria

- **Mensal:** Auditor de Segurança roda script de scan que lista dados além do prazo máximo
- **Trimestral:** drill conforme tabela
- **Anual:** revisão da matriz por DPO (humano contratado) — quando V2 ativar

---

## 7. Referências

- `docs/conformidade/comum/lgpd-rat.md` — RAT detalhado
- `docs/conformidade/comum/seguranca-dados.md` — política geral
- `docs/comum/isolamento-multi-tenant.md` — chave KMS por tenant
- `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md` (a criar) — cláusula 8.4 (retenção 25 anos)
- LGPD: lei 13.709/2018
- ISO 17025:2017
- Receita Federal: art. 173 CTN (5 anos)
- ANPD Resolução 15/2024 (incidentes)
