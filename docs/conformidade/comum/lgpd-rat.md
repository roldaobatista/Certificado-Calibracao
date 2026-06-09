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
| RAT-11 | Cadastro de cliente final no Portal do Cliente + área cliente Marketplace | Nome, e-mail, telefone, CPF/CNPJ, endereço, IP de aprovação, geolocalização aproximada (IP) | Identificação + contato + comportamento | Aferê age como **operador** — base do controlador (tenant); para a área de autoatendimento: Execução de contrato (art. 7º V) + consentimento explícito do titular (art. 7º I) na primeira entrada | Permitir autoatendimento, aprovação eletrônica de orçamentos com prova de IP/timestamp, 2ª via fatura, consulta de OS/certificados | Vigência da conta + 5 anos (fiscal); aprovação/rejeição de orçamento em WORM (5 anos) |
| RAT-12 | Captação de leads no Marketplace público + opt-in marketing Comunicação Omnichannel | Nome, e-mail, telefone, CPF/CNPJ opcional, UTM, IP, evento de visualização | Identificação + comportamento | **Consentimento explícito (art. 7º I)** para marketing/comercial; Legítimo interesse (art. 7º IX) para o registro de visita não-identificada (sem PII direta) | Qualificar lead, criar oportunidade no CRM, comunicação comercial multi-canal com controle de opt-in/opt-out | Lead com opt-in: até opt-out + 6 meses pós-revogação; visita anônima: 13 meses (analytics) |
| RAT-13 | Geolocalização contínua + biometria implícita em fotos (App Técnico) | GPS contínuo (lat/long/timestamp), trilha de deslocamento, fotos com EXIF (GPS + timestamp + dispositivo), face do cliente em foto opcional, assinatura touch + CPF de aceite | Identificação + comportamento + **biometria implícita** (face em foto, traçado de assinatura) | Execução de contrato (art. 7º V) + Legítimo interesse (art. 7º IX) **com RIPD obrigatório** (DPIA-02). Art. 11 (sensível) NÃO se aplica a biometria implícita capturada apenas para evidência de aceite — sem extração/matching biométrico. | Comprovação de presença, audit de OS, rastreabilidade ISO 17025, prova de aceite contratual | GPS/trilha: 5 anos; foto com EXIF: 5 anos; assinatura de aceite: 5 anos. Após prazo: anonimização (face desfocada / EXIF removido) + crypto-shredding do bruto |
| RAT-14 | Dados de saúde — ASO (Segurança do Trabalho + Treinamentos) | CPF colaborador, resultado ASO (apto/inapto/apto com restrições), tipo exame (admissional/periódico/retorno/mudança função/demissional), médico examinador (CRM), data, validade, PDF do laudo | **Sensível — saúde (art. 11 LGPD)** | **Obrigação legal/regulatória (art. 11 II "a")** — NR-7 (PCMSO) + CLT art. 168 + NR-35 (saúde ocupacional altura). Sem consentimento (não é base aplicável para vínculo trabalhista) | Cumprir obrigação MTE/eSocial, bloquear alocação de técnico em campo sem ASO válido | Vigência vínculo + 20 anos (NR-7 item 7.4.5.1) — campeão sobre LGPD direito esquecimento (base "obrigação legal" vence) |
| RAT-15 | Acesso remoto de equipe de Suporte SaaS ao tenant | Sessão de suporte (TTL 2h), user ID atendente, IP atendente, ações executadas no tenant (diff), consentimento do admin tenant (timestamp + IP), motivo do acesso | Identificação + comportamento + acesso a "regulado" do tenant | Execução de contrato Aferê↔tenant (art. 7º V) + consentimento explícito do admin do tenant (art. 7º I) registrado a cada sessão | Atender ticket de suporte, diagnosticar bug com dados reais do tenant, atender SLA | Log de sessão: 5 anos (audit reforçado — INV-001); revogação encerra acesso imediato; sem dado do tenant copiado para fora |
| RAT-16 | Cobrança recorrente Billing SaaS — dados de pagamento via gateway PCI-DSS | Apenas: nome/CPF/CNPJ do contratante, token opaco do gateway (Stripe/PagSeguro), bandeira do cartão, últimos 4 dígitos, status fatura. **NUNCA**: PAN completo, CVV, dados de track | Identificação + financeiro | Execução de contrato (art. 7º V) + obrigação fiscal (art. 7º II) | Cobrar mensalidade/anualidade do SaaS, controlar inadimplência, gerar fatura | 5 anos (fiscal); token do gateway até cancelamento + 30 dias; nenhum PAN/CVV armazenado (escopo PCI-DSS SAQ-A por delegação ao gateway certificado) |
| RAT-17 | Importação em massa de cadastro de cliente final do tenant (US-CLI-003) | Nome, CPF/CNPJ, e-mail, telefone, endereço — chegam via CSV exportado de sistema anterior (Cali/Bling/etc) | Identificação + contato | Aferê age como **operador** — base do controlador (tenant), declarada na importação: Execução de contrato (art. 7º V) **ou** Consentimento (art. 7º I) com prova externa. Categoria de risco **elevada** (volume + velocidade) | Migração de cadastro do sistema anterior do tenant para o Aferê | Cliente importado: vigência do contrato tenant + 5 anos. **Arquivo CSV bruto: transitório (deletado pós-execução).** Declaração de procedência: 5 anos. Audit `cliente.importacao_executada`: 25 anos. DPIA-06 obrigatória antes do go-live público (diferida pra Wave A — Marco 1 dogfooding-only) |
| RAT-EQP-FOTO | Foto do equipamento (cadastro, recebimento no lab, devolução) — módulo `equipamentos` US-EQP-001/006 | Imagem do equipamento físico (TAG, plaqueta, lacre, dano). **Captura incidental possível:** rosto de funcionário/cliente, crachá, documento ao fundo, monitor de computador. EXIF (GPS, modelo do device, timestamp) é **removido no upload**. | Identificação + potencialmente **sensível (biometria facial — art. 11)** se rosto identificável capturado por acidente | **Execução de contrato (art. 7º V)** para foto técnica sem pessoa identificável + **ISO 17025 cl. 7.4.4** (registrar condição de chegada) + **art. 11 § 4º** se rosto identificável (consentimento OU anonimização via blur — tenant é controlador desse tratamento incidental). | Identificação visual do ativo; evidência de estado físico (lacre, dano, contaminação); rastreabilidade ISO 17025 | Vigência do equipamento + 5 anos pós-sucateamento; **25 anos** se compõe evidência ISO 17025 cl. 7.4.4. Foto com rosto: blur automático sugerido (V2 quando ML pronto) OU exclusão sob notificação do titular em 15 dias úteis. EXIF removido sempre no upload. |
| RAT-CFG-EMPRESA | Cadastro tributário da empresa/filiais do tenant (`configuracoes-sistema` US-CFG-001) — P2/ADV-06 | Razão social, CNPJ, IE/IM, endereço, telefone/e-mail de contato, logo. **PII de PF embutida:** MEI = CPF dentro do CNPJ; IE/IM de empresário individual; telefone/e-mail/endereço quando de pessoa física (dono/responsável) | Identificação + contato + fiscal | **Obrigação fiscal (art. 7º II)** + **Execução de contrato (art. 7º V)**. Minimização (art. 6º III): `im`/`logo_url`/`site`/`telefone` são **opcionais** | Alimentar documentos fiscais e operacionais do tenant com dados cadastrais corretos | Vigência do tenant + 5 anos (fiscal — `retencao-matriz.md`); PII de MEI/contato anonimizada no fim de prazo; razão social/CNPJ preservados enquanto houver documento fiscal no prazo. *Conjunto final de regimes/figuras fiscais = revisão contador/OAB pré-produção (ADV-01/02)* |

---

## 3. Bases legais — quando usar qual

| Base legal | Quando | Exemplo no Aferê |
|------------|--------|-------------------|
| **Execução de contrato (V)** | Tratamento necessário pra cumprir contrato com o titular | RAT-01, RAT-02, RAT-06 |
| **Obrigação legal/regulatória (II)** | Lei ou norma exige | RAT-04 (ISO 17025), RAT-05 (Receita), RAT-08 (audit trail) |
| **Legítimo interesse (IX)** | Necessário pra interesse legítimo do controlador, sem prejuízo do titular | RAT-07, RAT-09 — sempre com RIPD/DPIA documentada |
| **Consentimento (I)** | Quando nenhuma das anteriores cabe | RAT-09 cookies não-essenciais |
| **Dados sensíveis (saúde, biométricos)** | Art. 11 — bases mais restritas | RAT-14 (ASO — base art. 11 II "a" obrigação legal NR-7 + CLT 168); biometria implícita em foto/assinatura de aceite (RAT-13) NÃO é tratamento de dado sensível enquanto não há extração/matching biométrico — se evoluir para reconhecimento facial, exige RIPD novo e base própria |

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

## 5. Incidentes de segurança — playbook ANPD 3 dias úteis (Resolução CD/ANPD 15/2024)

Em caso de incidente envolvendo dados pessoais:

| T | Ação |
|---|------|
| **T+0** | Detecção (alerta Grafana / report manual / auditor de segurança bloqueio em série) |
| **T+15min** | Acionamento do RACI (`docs/governanca/RACI-incidente-ai.md`) — Roldão notificado |
| **T+1h** | Contenção inicial (suspender tenant afetado, rotacionar credencial, etc.) |
| **T+24h** | Avaliação do impacto — comunicar tenant(s) afetado(s) se confirmado |
| **T+3 dias úteis** | Comunicação ANPD via formulário oficial (Res. CD/ANPD 15/2024 art. 6º — 3 dias úteis, não 72h corridas) |
| **T+30d** | Postmortem público (`docs/operacao/incidente-postmortem.md` — template a criar) |

Template de notificação ANPD em `docs/conformidade/comum/incidente-anpd-modelo.md` (a criar).

---

## 6. RIPD / DPIA (Relatório de Impacto à Proteção de Dados)

Obrigatório quando o tratamento envolver alto risco. No Aferê:

- ✅ RIPD obrigatório pra RAT-07 (geolocalização técnico de campo) — antes do release do mobile
- ✅ RIPD obrigatório pra RAT-09 (telemetria) — antes de ligar product analytics
- ⏳ RIPD condicional pra LLM (RAT futuro — chatbot CS) — antes do release
- ✅ **5 RIPDs/DPIA dos módulos novos sensíveis** consolidados em `docs/conformidade/comum/dpia-modulos-novos.md`:
  - DPIA-01 — Suporte SaaS / acesso remoto a dados regulados (RAT-15)
  - DPIA-02 — App Técnico / geolocalização contínua + biometria implícita (RAT-13, complementa RAT-07)
  - DPIA-03 — Segurança do Trabalho / ASO (dado sensível saúde — art. 11) (RAT-14)
  - DPIA-04 — Comunicação Omnichannel / consentimento marketing multi-canal (RAT-12)
  - DPIA-05 — Billing SaaS / cobrança recorrente + PCI por delegação (RAT-16)

Template em `docs/conformidade/comum/ripd-modelo.md`.

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
