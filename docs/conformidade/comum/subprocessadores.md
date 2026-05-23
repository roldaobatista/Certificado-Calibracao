---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/PUBLICAÇÃO"
finalidade: lista pública versionada de sub-operadores da Plataforma Aferê (LGPD art. 39 §4º + DPA cl. 7)
---

# Lista de Sub-operadores — Plataforma Aferê

> Documento público versionado. Atualização exige aviso prévio de 30 dias aos Tenants e direito de objeção fundamentada.

---

## Versão

**v1.0 — 2026-05-23** (minuta inicial — aguarda validação OAB + assinatura DPAs)

---

## 1. Sub-operadores ativos / planejados (Wave A)

| # | Nome | Finalidade | Dado tratado | País sede | Certificações | Base transferência (se exterior) | DPA assinado? | Versão DPA |
|---|---|---|---|---|---|---|---|---|
| 1 | **AWS** (Amazon Web Services) | Gestão de chaves criptográficas — KMS Multi-Region Key | Material criptográfico, chaves de cifragem por tenant | EUA (sa-east-1 primária + us-east-1 réplica) | ISO 27001, SOC 2 Type II, PCI-DSS L1, HIPAA | Cláusulas-padrão contratuais + criptografia em trânsito/repouso | **Pendente** — em negociação | — |
| 2 | **Backblaze B2** | Storage WORM long-tail (certificados, NFS-e, audit) | Documentos cifrados client-side; trilha de eventos | EUA (datacenters multi-região) | ISO 27001, SOC 2 Type II | Cláusulas-padrão + criptografia client-side antes de upload | **Pendente** | — |
| 3 | **PlugNotas** | Emissão de NFS-e (provider) | CNPJ tomador/prestador, dados fiscais, valores | Brasil | LGPD compliance declarada; ISO em validação | N/A (BR-BR) | **Pendente** | — |
| 4 | **Lacuna Software** (Web PKI) | Assinatura A3 ICP-Brasil client-side (NUNCA recebe chave privada) | Hash do documento, signing-time, nonce (sem dados pessoais do signatário no servidor Aferê) | Brasil | Lacuna Web PKI homologada Lacuna; ICP-Brasil compatível | N/A (BR-BR) | **Pendente** | — |
| 5 | **Anthropic** (Claude API) | Geração de código por agentes IA + operação de subagentes | Trechos de spec, código, contexto técnico (sem PII de Clientes Finais) | EUA | SOC 2 Type II | Cláusulas-padrão + Trust Policy Anthropic + Data Retention 0 dias (não treina com inputs) | **Pendente** — verificar Trust Policy | — |
| 6 | **Grafana Cloud** | Observabilidade (métricas, dashboards) | Telemetria operacional (sem PII bruta — IP hash HMAC) | EUA | ISO 27001, SOC 2 Type II | Cláusulas-padrão | **Pendente** | — |
| 7 | **Axiom** | Logs estruturados | Logs de aplicação (sanitizados — sem PII direta) | EUA | SOC 2 Type II | Cláusulas-padrão | **Pendente** | — |
| 8 | **Hostinger** | VPS KVM hospedagem (São Paulo/BR) | Volume de servidor (PostgreSQL + aplicação) | Brasil (datacenter SP) | Verificar certificações específicas | N/A (BR-BR) | **Pendente — verificar contrato vigente** | — |

---

## 2. Sub-operadores potenciais (futuros, V2+)

| # | Nome | Finalidade | Gatilho de contratação |
|---|---|---|---|
| 9 | Gateway de pagamento (Asaas / Iugu / Gerencianet / Stripe) | Cobrança recorrente billing-saas | Bloqueador antes do 1º tenant externo pago |
| 10 | Provedor WhatsApp Business API (Z-API / Twilio / Meta direta) | Comunicação omnichannel | Wave B (`comunicacao-omnichannel`) |
| 11 | Provedor e-mail transacional (SendGrid / Postmark / Amazon SES) | Comunicação titular + alertas | Wave A (mínimo SES embutido AWS) |
| 12 | Provedor SMS transacional | MFA + comunicação | Wave A (avaliar custo×benefício SMS vs autenticador) |
| 13 | Provedor B alternativo (Magalu Cloud / Oracle / AWS sa-east) | Disaster Recovery | Wave A (avaliar — `dr-plan.md` cenário c) |

---

## 3. Política de mudança de sub-operador

3.1. **Inclusão de novo sub-operador:** aviso prévio de **30 dias** aos Tenants via e-mail e publicação atualizada deste documento.

3.2. **Direito de objeção do Tenant:** fundamentação técnica/jurídica em até 30 dias; Aferê reavaliará a inclusão ou ofertará migração de cenário ao Tenant impactado.

3.3. **Substituição de sub-operador:** mesmo prazo + relatório de equivalência de garantias.

3.4. **Remoção de sub-operador:** notificação imediata + plano de migração de dados/funcionalidade.

---

## 4. Auditoria

4.1. Aferê pode auditar sub-operadores em até 1 vez por ano ou sempre que houver incidente confirmado.

4.2. Tenant pode solicitar relatório resumido de auditoria mediante NDA (resultado consolidado, sem dados sensíveis dos demais Tenants).

4.3. ANPD pode auditar a cadeia operacional via Aferê na qualidade de Operador.

---

## 5. Pendências bloqueantes pré-1º tenant externo pago

- [ ] DPA assinado com AWS
- [ ] DPA assinado com Backblaze B2
- [ ] DPA assinado com PlugNotas
- [ ] DPA assinado com Lacuna
- [ ] DPA + Trust Policy validados com Anthropic (verificar opt-out de treinamento)
- [ ] DPA assinado com Grafana Cloud
- [ ] DPA assinado com Axiom
- [ ] Contrato Hostinger revisado quanto à LGPD
- [ ] Modelo ANPD de cláusulas-padrão (Res. 19/2024) adotado quando publicado oficialmente
- [ ] Designação formal de DPO
- [ ] Validação OAB desta lista

---

**FIM Subprocessadores v1.0 — MINUTA — REQUER VALIDAÇÃO OAB**
