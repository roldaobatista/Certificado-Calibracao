---
owner: roldao
revisado-em: 2026-06-12
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/PUBLICAÇÃO"
---

# Política de Privacidade — Plataforma Aferê (PoP v1.0)

> ❄️ **CONGELADO (decisão Roldão 2026-06-12, auditoria de cerimônia R19):** emendas de cláusulas por módulo estão suspensas até o gate GATE-LGPD-POP-1. O subagente `advogado-saas-regulado` atua no P2 SOMENTE para risco de DESIGN (estrutura de dado, texto de tela visível ao titular) — não para polir prosa desta minuta que será reescrita por OAB humana pré-publicação.

> Minuta preparada por subagente IA (`advogado-saas-regulado`) conforme LGPD (Lei 13.709/2018), Marco Civil da Internet e Resoluções CD/ANPD 2/2022, 15/2024, 18/2024 e 19/2024. **Não substitui validação por advogado(a) com OAB ativa.**

---

## 1. Identificação da Controladora

**Razão social:** [a definir — entidade legal Aferê]
**CNPJ:** [a definir]
**Endereço:** [a definir]
**Encarregado de Dados (DPO):** [a designar formalmente — durante dogfooding contato roldao.tecnico@gmail.com]
**Canal LGPD:** dpo@[dominio-a-definir]

---

## 2. Definições

**Plataforma:** Aferê — SaaS multi-tenant para gestão de assistência técnica + laboratórios de calibração.
**Tenant:** pessoa jurídica que contrata a Plataforma e atua como Controladora de dados de seus Clientes Finais (LGPD art. 5º VI).
**Cliente Final:** pessoa física ou jurídica atendida pelo Tenant; titular de dados pessoais tratados pelo Tenant via Plataforma.
**Aferê:** Controladora de dados de cadastro do Tenant; Operadora de dados de Clientes Finais (art. 5º VII).

---

## 3. Dados Coletados

### 3.1. Como Controladora (dados do Tenant)
- Razão social, CNPJ, endereço, telefone, e-mail corporativo
- Dados do administrador inicial: nome, CPF, e-mail, telefone, foto perfil
- Dados de pagamento do plano (gateway PSP separado — Aferê não armazena PAN PCI-DSS)
- Logs de acesso administrativo do Tenant (IP hash HMAC, user-agent, timestamp)

### 3.2. Como Operadora (dados de Clientes Finais)
- Cadastro: razão social/nome, CPF/CNPJ, endereço, contatos
- Equipamentos: marca, modelo, NS, fotos, localização física (sem PII)
- OS: descrição problema/serviço, geolocalização (opt-in), assinatura touch (biometria — INV-OS-ACEITE-BIO-001)
- Calibração/Certificados: dados técnicos vinculados ao equipamento e ao Cliente Final
- Comunicação: e-mail, telefone, WhatsApp (quando opt-in)

### 3.3. Dados de pessoal técnico do Tenant
- Responsável Técnico (RT): nome, CPF, registro conselho de classe, vigência, grandezas autorizadas
- Signatário A3 ICP-Brasil: nome, CPF, dados do certificado (sem chave privada — A3 é client-side)
- Técnico de campo: nome, CPF, função, geolocalização durante atividade (opt-in)

### 3.4. Dados sensíveis (art. 11 LGPD)
- **Biometria touch (assinatura de aceite — RAT-07, RAT-08, INV-OS-ACEITE-BIO-001):** dado sensível tratado sob art. 11 II "g" (cumprimento de obrigação legal — Lei 14.063/2020) + art. 11 II "a" (consentimento específico no momento da coleta). Cifrada com chave KMS dedicada `BIOMETRIA_KEY_<tenant>`.

---

## 4. Bases Legais (LGPD art. 7º e 11)

| Categoria | Base legal | Justificativa |
|---|---|---|
| Cadastro do Tenant | art. 7º V | Execução de contrato SaaS |
| Pagamento do plano | art. 7º V + IX | Execução + legítimo interesse comercial |
| Dados de Clientes Finais (operação) | art. 7º II + V (operador, via Tenant) | Obrigação legal/contratual entre Tenant↔Cliente Final |
| RT, signatário A3 | art. 7º II + 11 II "a" | Obrigação regulatória NIT-DICLA-021 + ICP-Brasil |
| Biometria touch | art. 11 II "g" + "a" | Lei 14.063/2020 + consentimento específico |
| Geolocalização técnico | art. 7º I + IX | Consentimento opt-in + legítimo interesse (auditoria operacional) |
| Logs de acesso (IP hash, audit) | art. 7º II + IX | Marco Civil art. 15 + segurança/defesa |
| Comunicação transacional | art. 7º V | Execução de contrato |

---

## 5. Finalidades

Lista completa em `docs/conformidade/comum/finalidades-lgpd.md`. Resumo:
- prestação dos serviços contratados;
- cumprimento de obrigação regulatória (Receita, ISO 17025, NIT-DICLA, INMETRO);
- segurança da informação e prevenção a fraude;
- defesa em juízo e cumprimento de ordem judicial;
- comunicação transacional com titular do serviço;
- auditoria pela CGCRE/RBC quando aplicável.

---

## 6. Compartilhamento e Sub-operadores

Lista pública em `docs/conformidade/comum/subprocessadores.md`. Sub-operadores nomeados (Wave A):

| Sub-operador | Finalidade | Sede | DPA |
|---|---|---|---|
| AWS (KMS Multi-Region) | Gestão de chaves criptográficas | EUA (us-east-1 réplica) | Pendente assinatura |
| Backblaze B2 | Storage WORM long-tail | EUA | Pendente |
| PlugNotas | Emissão NFS-e (provider) | Brasil | Pendente |
| Lacuna Web PKI | Assinatura A3 client-side | Brasil | Pendente |
| Anthropic | Geração de código por agentes IA | EUA | Pendente |
| Grafana Cloud | Observabilidade | EUA | Pendente |
| Axiom | Logs | EUA | Pendente |
| Hostinger | VPS hospedagem (BR/SP) | Brasil | Verificar |

**Compromisso:** todos os sub-operadores serão formalizados com DPA antes do 1º tenant externo pago.

---

## 7. Transferência Internacional

7.1. Aferê transfere dados para EUA via AWS KMS (chave réplica us-east-1), Backblaze B2, Anthropic API, Grafana Cloud, Axiom.

7.2. **Base legal da transferência (LGPD art. 33):**
- ausência de decisão de adequação ANPD para os EUA até a data desta minuta;
- adoção de **cláusulas-padrão contratuais** específicas com cada sub-operador (estado de construção operacional — ver §6);
- **garantias específicas:** criptografia em trânsito TLS 1.3, em repouso AES-256, KMS gerenciado, monitoramento de acesso, contratos com cláusulas de confidencialidade e auditabilidade.

7.3. **Monitoramento regulatório:** Aferê acompanha publicação oficial de modelo ANPD de cláusulas-padrão (Res. CD/ANPD 19/2024 — operacionalização em construção) e migrará contratos quando texto oficial for emitido.

---

## 8. Retenção

8.1. Matriz consolidada em `docs/conformidade/comum/retencao-matriz.md`. Princípios gerais:

| Categoria | Prazo mínimo | Base |
|---|---|---|
| Documento fiscal (NFS-e) | 5 anos | Receita Federal |
| Certificado de calibração | ~25 anos | ISO 17025 cl. 8.4 |
| Cadastro de Cliente Final (durante contrato) | Vigência + 5 anos | Execução de contrato + defesa |
| Audit log de acesso (IP hash, ações) | 2 anos | Marco Civil + boas práticas |
| Biometria touch | 5 anos quando não vinculada a calibração; 25 anos quando vinculada | Cumprimento legal + ISO 17025 |
| Telemetria | 13 meses | Legítimo interesse — anonimização após |

8.2. **Pedido de eliminação:** segue ADR-0021 (Zona A — eliminação efetiva / Zona B — anonimização in-place / Zona C — anonimização campo-a-campo) conforme base legal autônoma incidente.

---

## 9. Direitos do Titular (LGPD art. 18)

9.1. O titular pode exercer, mediante requisição formal ao DPO ou via canal `dpo@[dominio]`:
- **Acesso** aos dados tratados
- **Correção** de dados incompletos, inexatos ou desatualizados
- **Portabilidade** em formato estruturado
- **Eliminação** de dados tratados com base em consentimento
- **Anonimização**, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade
- **Informação** sobre compartilhamento e sub-operadores
- **Revogação de consentimento** quando aplicável

9.2. **Prazo de resposta:** 15 dias corridos (Res. CD/ANPD 2/2022 e 15/2024).

9.3. **Fluxo operacional:** ver `docs/conformidade/comum/runbook-dpo-encarregado.md`.

9.4. **Negativa fundamentada:** quando base legal autônoma (Receita, ISO 17025, defesa em juízo) impedir o atendimento, a Aferê responderá com fundamentação técnica e orientará sobre recurso à ANPD.

---

## 10. Encarregado de Dados (DPO)

**Nome:** [a designar formalmente]
**Contato:** dpo@[dominio]
**Durante dogfooding (Balanças Solution + Aferê pré-1º tenant externo pago):** Roldão Batista — roldao.tecnico@gmail.com — função acumulada informalmente com apoio do subagente `advogado-saas-regulado`.

---

## 11. Incidentes de Segurança

11.1. Em caso de incidente que possa acarretar risco ou dano relevante aos titulares, a Aferê:
- comunicará ao Tenant afetado em até 24h da confirmação (DPA cl. 10.1);
- comunicará à ANPD em até **3 dias úteis** (Res. CD/ANPD 15/2024);
- comunicará aos titulares quando exigido pela ANPD ou quando o impacto direto justificar;
- conduzirá postmortem completo em até 30 dias.

11.2. Modelo de comunicação: `docs/conformidade/comum/incidente-anpd-modelo.md`.

---

## 12. Cookies e Tecnologias Similares

12.1. A Plataforma utiliza cookies estritamente necessários (sessão, autenticação, MFA, CSRF) e cookies analíticos opt-in (caso utilizados — anonimizados).

12.2. Gestão de cookies disponível na interface da Plataforma.

---

## 13. Atualizações desta Política

13.1. Esta Política pode ser atualizada mediante aviso prévio de 30 dias por e-mail ao administrador do Tenant.

13.2. Versões históricas preservadas em repositório auditável.

13.3. **Versão atual:** v1.0 — 2026-05-23 (minuta).

---

## 14. Pendências bloqueantes pré-publicação

- [ ] Razão social Aferê definida + CNPJ ativo
- [ ] Endereço da Controladora
- [ ] DPO formalmente designado
- [ ] DPAs com 7 sub-operadores assinados
- [ ] Modelo ANPD de cláusulas-padrão (Res. 19/2024) publicado e adotado
- [ ] Validação OAB desta Política
- [ ] Política publicada em site público com link permanente

---

**FIM Política de Privacidade v1.0 — MINUTA — REQUER VALIDAÇÃO OAB**
