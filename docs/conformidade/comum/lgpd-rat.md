---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# LGPD — Registro de Atividades de Tratamento (RAT)

> **Pra quê:** atender LGPD art. 37 (controlador e operador devem manter registro das operações de tratamento). Fonte primária do RAT do Aferê. Atualizar a cada operação nova ou base legal alterada.
>
> **Base normativa:** Lei 13.709/2018 (LGPD), Resolução ANPD 15/2024 (incidentes), Enunciado CD/ANPD 4 (DPO obrigatório em larga escala).

---

## 1. Papéis (LGPD)

| Papel | Quem |
|-------|------|
| **Controlador** | O cliente (tenant) é controlador dos dados das pessoas físicas que ele cadastra (clientes finais, técnicos, etc.) |
| **Operador** | Aferê (a empresa que opera o software) é operador — trata dados em nome do controlador |
| **Encarregado (DPO)** | A definir. Subagente `advogado-saas-regulado` prepara minutas; designação formal de DPO humano dispara em V2 ou no 1º incidente real (ver `discovery/sintese-final.md` seção 7) |

**Implicação operacional:** Aferê presta serviço; controlador (tenant) é quem responde primariamente perante o titular. DPA (Data Processing Agreement) entre Aferê e tenant define limites — modelo em `docs/conformidade/comum/dpa-modelo.md` (a criar).

---

## 2. Registro de Atividades de Tratamento (RAT)

Lista de operações de tratamento de dados pessoais que o Aferê realiza, com base legal correspondente.

| # | Operação | Dados pessoais tratados | Categoria | Base legal | Finalidade | Retenção |
|---|----------|------------------------|-----------|------------|------------|----------|
| RAT-01 | Cadastro de tenant (assinatura do contrato) | Nome, e-mail, CPF/CNPJ do contratante | Identificação | Execução de contrato (art. 7º V) | Identificar pagador e responsável legal | Vigência do contrato + 5 anos (fiscal) |
| RAT-02 | Cadastro de usuário operacional (técnico, atendente, financeiro) | Nome, e-mail, telefone, CPF | Identificação | Execução de contrato (art. 7º V) + Legítimo interesse (art. 7º IX) | Login, atribuição de papel, audit trail | Vigência do contrato + 5 anos |
| RAT-03 | Cadastro de cliente final do tenant (BIG-07) | Nome, e-mail, telefone, CPF/CNPJ, endereço | Identificação + contato | Aferê age como **operador** — base legal é do controlador (o tenant) | Atender obrigações comerciais do tenant | Definida pelo tenant; 5 anos default fiscal |
| RAT-04 | Emissão de certificado de calibração (BIG-02) | Nome do signatário técnico + cliente final | Identificação | Obrigação regulatória (art. 7º II + ISO 17025 cláusula 7.8) | Emitir documento exigido por norma | **~25 anos** (ISO 17025 8.4) |
| RAT-05 | Emissão de NFS-e (BIG-04) | Dados do contribuinte e do tomador | Identificação + fiscal | Obrigação fiscal (art. 7º II) | Cumprir obrigação tributária | 5 anos (Receita Federal) |
| RAT-06 | Lembrete de recalibração via WhatsApp (BIG-10/11) | Telefone + identificação do equipamento | Identificação + contato | Execução de contrato (art. 7º V) + opt-in registrado | Lembrar próxima calibração | Até opt-out do titular |
| RAT-07 | Coleta de localização (mobile técnico de campo) | GPS, timestamp, foto | Identificação + comportamento | Legítimo interesse (art. 7º IX) + opt-in técnico | Comprovar atendimento + audit OS | 5 anos |
| RAT-08 | Log de auditoria do sistema | User ID + ação + timestamp + IP | Identificação + comportamento | Obrigação regulatória + Legítimo interesse (segurança) | Audit trail LGPD/ISO 17025/RBC | 2 anos (governança) a 25 anos (calibração) |
| RAT-09 | Cookies + telemetria | ID anônimo + comportamento | Comportamento | Legítimo interesse (art. 7º IX) + consentimento se sensível | Observabilidade + product analytics | 13 meses |
| RAT-10 | Backup + storage WORM | Cópia das operações acima | — | Mesma da operação original | Continuidade do serviço + DR | Conforme `retencao-matriz.md` |

Matriz consolidada de retenção em `docs/conformidade/comum/retencao-matriz.md` (a criar).

---

## 3. Bases legais — quando usar qual

| Base legal | Quando | Exemplo no Aferê |
|------------|--------|-------------------|
| **Execução de contrato (V)** | Tratamento necessário pra cumprir contrato com o titular | RAT-01, RAT-02, RAT-06 |
| **Obrigação legal/regulatória (II)** | Lei ou norma exige | RAT-04 (ISO 17025), RAT-05 (Receita), RAT-08 (audit trail) |
| **Legítimo interesse (IX)** | Necessário pra interesse legítimo do controlador, sem prejuízo do titular | RAT-07, RAT-09 — sempre com RIPD/DPIA documentada |
| **Consentimento (I)** | Quando nenhuma das anteriores cabe | RAT-09 cookies não-essenciais |
| **Dados sensíveis (saúde, biométricos)** | Art. 11 — bases mais restritas | Não aplicável no MVP-1 (escopo Aferê não trata dados sensíveis); reavaliar se entrar segmento médico |

---

## 4. Direitos do titular (art. 18)

Aferê (operador) **encaminha solicitação ao controlador (tenant)** em até 24h. Tenant responde ao titular em 15 dias úteis.

| Direito | Como atender |
|---------|--------------|
| Confirmação + acesso | Tenant exporta dados do titular via UI Aferê → entrega ao titular |
| Correção | Tenant edita no Aferê → propagação em tempo real |
| Anonimização / bloqueio / eliminação | Função "anonimizar titular" no painel admin — substitui PII por hash + crypto-shredding |
| Portabilidade | Export JSON estruturado padronizado |
| Revogação de consentimento | Função "opt-out" — registra em audit + para tratamento dependente |
| Revisão de decisão automatizada | LLM gateway (LiteLLM) registra prompt+output em audit; revisão humana sob pedido |

---

## 5. Incidentes de segurança — playbook ANPD 72h (Resolução 15/2024)

Em caso de incidente envolvendo dados pessoais:

| T | Ação |
|---|------|
| **T+0** | Detecção (alerta Grafana / report manual / auditor de segurança bloqueio em série) |
| **T+15min** | Acionamento do RACI (`docs/governanca/RACI-incidente-ai.md`) — Roldão notificado |
| **T+1h** | Contenção inicial (suspender tenant afetado, rotacionar credencial, etc.) |
| **T+24h** | Avaliação do impacto — comunicar tenant(s) afetado(s) se confirmado |
| **T+72h** | Comunicação ANPD via formulário oficial (resolução exige até 3 dias úteis) |
| **T+30d** | Postmortem público (`docs/operacao/incidente-postmortem.md` — template a criar) |

Template de notificação ANPD em `docs/conformidade/comum/incidente-anpd-modelo.md` (a criar).

---

## 6. RIPD / DPIA (Relatório de Impacto à Proteção de Dados)

Obrigatório quando o tratamento envolver alto risco. No Aferê:

- ✅ RIPD obrigatório pra RAT-07 (geolocalização técnico de campo) — antes do release do mobile
- ✅ RIPD obrigatório pra RAT-09 (telemetria) — antes de ligar product analytics
- ⏳ RIPD condicional pra LLM (RAT futuro — chatbot CS) — antes do release

Template em `docs/conformidade/comum/ripd-modelo.md` (a criar).

---

## 7. Transferência internacional

- **AWS KMS sa-east-1 ↔ us-east-1 (Multi-Region Key):** **chaves**, não dados — atende decisão CD/ANPD sobre tratamento de chaves criptográficas em jurisdição protegida
- **Backblaze B2 EU Central:** dados criptografados (chave fica em AWS KMS sa-east-1) — UE tem decisão de adequação ANPD (sim, em vigor)
- **Grafana Cloud / Axiom (US):** logs **anonimizados** + telemetria — sem PII direta

Detalhar em `docs/conformidade/comum/transferencia-internacional.md` (a criar quando o 1º tenant farma TOP aparecer).

---

## 8. Governança LGPD

- **Versão deste RAT:** revisar trimestralmente; cada operação nova de tratamento = nova linha aqui antes do código merge
- **Auditor de Segurança Família 5** valida em pre-commit: PR que adiciona campo PII sem entrada em RAT → veto
- **DPO designado** (a definir — V2): revisa anualmente + responde solicitações do titular
- **Treinamento da equipe** — Roldão obrigatório; humanos sob demanda quando contratados

---

## 9. Referências cruzadas

- `REGRAS-INEGOCIAVEIS.md` — IDs SEC-*, INV-TENANT-*
- `docs/comum/isolamento-multi-tenant.md` — RLS + tenant_id (defesa contra vazamento cross-tenant)
- `docs/conformidade/comum/seguranca-dados.md` — política de segurança + RIPD/DPIA
- `docs/governanca/RACI-incidente-ai.md` — quem responde em incidente
- `docs/operacao/incidente-postmortem.md` — template (a criar)
