---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# DPIA / RIPD — Módulos novos sensíveis

> **Pra quê:** Resolução ANPD 15/2024 + LGPD art. 38 exigem Relatório de Impacto à Proteção de Dados (RIPD/DPIA) **antes** do release de tratamento de alto risco. Este documento consolida os 5 RIPDs obrigatórios dos módulos novos do mapeamento (Famílias 6-7 em diante), evitando 5 arquivos separados em estado embrionário.
>
> **Base normativa:** Lei 13.709/2018 (LGPD) art. 5º X, 6º, 7º, 11, 38, 50; Resolução ANPD 2/2022 (orientações RIPD); Resolução ANPD 15/2024 (incidentes).
>
> **Quando promover:** quando cada módulo entrar em Foundation/Wave de desenvolvimento, copiar o respectivo bloco para `docs/conformidade/comum/ripd/RIPD-NN-<modulo>.md` em arquivo próprio e marcar como aprovado pelo DPO designado (V2). Hoje (pré-código), DPIA-XX preenchido pelo subagente `advogado-saas-regulado` + revisado pelo Roldão.
>
> **Template:** `docs/conformidade/comum/ripd-modelo.md`.

---

## Índice

| ID | Módulo | RAT | Status | Risco residual |
|----|--------|-----|--------|----------------|
| DPIA-01 | `suporte-plataforma/suporte-saas` (acesso remoto) | RAT-15 | draft | Médio — controles compensatórios robustos |
| DPIA-02 | `operacao/app-tecnico` (GPS contínuo + foto/biometria implícita) | RAT-13 (complementa RAT-07) | draft | Médio-alto — RIPD bloqueante antes do release mobile |
| DPIA-03 | `rh-frota-qualidade/seguranca-trabalho` + `treinamentos` (ASO) | RAT-14 | draft | Médio — dado sensível mas base obrigação legal blindada |
| DPIA-04 | `comercial/comunicacao-omnichannel` (consentimento marketing) | RAT-12 | draft | Médio — opt-out duro mitiga a maior parte |
| DPIA-05 | `financeiro/billing-saas` (cobrança recorrente + PCI) | RAT-16 | draft | Baixo — escopo PCI delegado a gateway certificado (SAQ-A) |

---

## DPIA-01 — Suporte SaaS: acesso remoto a dados regulados do tenant

### 1. Operação avaliada
- **Operação:** RAT-15 — equipe de Suporte SaaS abre sessão temporária dentro do tenant do cliente (acesso "break-glass" supervisionado) para diagnosticar ticket.
- **Módulo:** `docs/dominios/suporte-plataforma/modulos/suporte-saas/` (US-SUP-007 Acesso remoto registrado).
- **Categoria de dado:** todo dado do tenant que estiver disponível na tela acessada — pode incluir **regulado** (PII de clientes finais, certificados de calibração, dados fiscais).
- **Titulares afetados:** indireto — clientes finais e colaboradores do tenant cujos dados aparecem na tela acessada.
- **Frequência:** recorrente sob demanda (cada ticket que exija acesso).

### 2. Necessidade e proporcionalidade
- **Por que coletar/acessar:** diagnosticar bug que não se reproduz em ambiente isolado; sem acesso real, suporte vira "tente reiniciar" e SLA falha.
- **Alternativas consideradas:** (a) shadow tenant sintético — não reproduz volume/borda real; (b) screen sharing com o usuário — cliente raramente disponível em tempo real; (c) anonimização on-the-fly — quebra reprodução do bug.
- **Minimização:** sessão com TTL 2h (default), revogável pelo admin tenant a qualquer momento, banner visível durante toda a sessão, escopo de leitura por padrão (escrita exige aprovação extra do admin tenant).

### 3. Base legal (LGPD)
- **Aferê ↔ tenant:** Execução de contrato (art. 7º V) — DPA prevê suporte técnico.
- **Aferê ↔ titulares dos dados do tenant:** Aferê é operador; controlador (tenant) autoriza via DPA + consentimento explícito do admin do tenant em cada sessão.

### 4. Riscos identificados
| ID | Risco | Prob. (1-5) | Imp. (1-5) | Score |
|----|-------|-------------|------------|-------|
| R1 | Atendente Aferê copia dados do tenant para fora (export indevido) | 2 | 5 | 10 |
| R2 | Sessão fica aberta após o necessário (TTL excedido por bug) | 3 | 3 | 9 |
| R3 | Admin do tenant aprova sem entender o impacto (consentimento "às cegas") | 4 | 3 | 12 |
| R4 | Atendente acessa tenant errado (cross-tenant) | 1 | 5 | 5 |
| R5 | Log de sessão é editado/apagado | 1 | 5 | 5 |
| R6 | Atendente compromentido (insider) usa acesso para fraude | 1 | 5 | 5 |

### 5. Medidas de mitigação
| Risco | Medida | Resíduo |
|-------|--------|---------|
| R1 | DLP básico — bloquear copy/paste em massa; export gera evento crítico; cláusula contratual + treinamento; rotação de senha do atendente trimestral | Aceitável |
| R2 | TTL hard 2h enforced em JWT + watchdog que mata sessão fora do prazo; alerta após 90 min | Aceitável |
| R3 | UI de aprovação mostra: dados que serão expostos, atendente identificado, motivo do ticket, opção de cancelar a qualquer momento; obrigatório re-confirmar 2x | Aceitável |
| R4 | RLS PostgreSQL `NOBYPASSRLS` + smoke test CI cross-tenant + role específica `support_user` que só lê tenant alvo da sessão | Aceitável |
| R5 | Log WORM em B2 com chave KMS separada (atendente Aferê NÃO tem chave) — `INV-001` | Aceitável |
| R6 | MFA obrigatório no atendente Aferê + auditoria mensal de sessões pelo Auditor de Segurança + revogação imediata em desligamento | Aceitável |

### 6. Balanceamento de legítimo interesse
Não aplicável — base é execução de contrato + consentimento explícito a cada sessão.

### 7. Direitos do titular
Titular (cliente final do tenant) exerce direitos via tenant controlador. Aferê notifica em 24h se o titular pedir relatório de quem acessou seus dados — log de sessão é fonte de verdade.

### 8. Transferência internacional
Não — atendente Aferê opera de São Paulo (mesma jurisdição do tenant brasileiro). Sessão não exporta dados.

### 9. Decisão
- ✅ Aprovado para implementar **com** as 6 mitigações acima como bloqueantes do release.

### 10. Revisão
- Anual ou em mudança de fluxo de acesso remoto. Gatilho antecipado: 1º incidente ou alteração ANPD.

---

## DPIA-02 — App Técnico: geolocalização contínua + biometria implícita em fotos/assinaturas

### 1. Operação avaliada
- **Operação:** RAT-13 (complementa RAT-07 já existente) — App mobile Flutter coleta GPS contínuo durante deslocamento + execução, fotos com EXIF (GPS + dispositivo + timestamp), assinatura touch do cliente + CPF de aceite.
- **Módulo:** `docs/dominios/operacao/modulos/app-tecnico/` (US-APP-003 check-in GPS, US-APP-006 fotos, US-APP-007 assinatura aceite).
- **Categoria de dado:** identificação + comportamento + biometria implícita (face capturada em foto + dinâmica de assinatura — sem extração biométrica).
- **Titulares afetados:** técnicos de campo (colaboradores do tenant) + clientes finais (quem assina + quem aparece em foto).
- **Frequência:** contínua durante jornada de trabalho do técnico.

### 2. Necessidade e proporcionalidade
- **Por que:** ISO 17025 cláusula 7.7 + rastreabilidade ISO 9001 + audit ISO/IEC 17020; comprovação trabalhista de jornada; defesa em ação judicial de "técnico não compareceu"; substituir papel/WhatsApp pessoal (zero compliance LGPD).
- **Alternativas:** (a) GPS só em check-in/check-out — perde trilha de deslocamento e prova de tempo em obra; (b) sem foto — perde evidência técnica e de aceite; (c) só assinatura em papel — perde rastreabilidade digital e abre fraude.
- **Minimização:** GPS desligado quando app fechado; foto categorizada (antes/durante/depois/avaria) — sem captura "selfie" sistemática; assinatura coletada apenas no aceite final; EXIF removido em foto exposta ao cliente final via Portal.

### 3. Base legal
- **GPS técnico:** Execução de contrato trabalhista (art. 7º V) + Legítimo interesse (art. 7º IX) com **opt-in** documentado em política aceita na admissão; técnico vê seu próprio histórico (`logins-recentes` equivalente).
- **Foto do cliente final:** Execução de contrato OS (art. 7º V) + consentimento implícito no momento da execução (banner físico/digital antes da foto).
- **Assinatura touch + CPF:** Execução de contrato (art. 7º V) — prova de aceite contratual.
- **Biometria implícita NÃO ativada:** não há extração/matching/template biométrico — só evidência fotográfica. Se evoluir para reconhecimento facial em algum recurso, **exige novo RIPD + base art. 11 própria**.

### 4. Riscos identificados
| ID | Risco | Prob. | Imp. | Score |
|----|-------|-------|------|-------|
| R1 | GPS vira "rastreamento abusivo" do técnico fora de horário (sindical, ANPD) | 4 | 4 | 16 |
| R2 | Foto captura terceiro não-consentido (família do cliente, transeunte) | 3 | 3 | 9 |
| R3 | EXIF da foto vaza endereço residencial do cliente | 3 | 4 | 12 |
| R4 | Assinatura touch capturada sob coação (cliente assina sem entender) | 2 | 4 | 8 |
| R5 | Cache offline com PII fica em celular roubado | 3 | 4 | 12 |
| R6 | Evolução silenciosa para reconhecimento facial sem novo RIPD | 2 | 5 | 10 |

### 5. Medidas de mitigação
| Risco | Medida | Resíduo |
|-------|--------|---------|
| R1 | GPS só durante "OS em execução" + horário de trabalho; técnico vê próprio histórico; política de admissão explícita; sem dashboard "onde está cada técnico em tempo real" para gestores fora de regra de operação | Aceitável |
| R2 | UI obriga categorização da foto + texto "não fotografe terceiros sem autorização"; treinamento operacional | Aceitável |
| R3 | EXIF removido antes de exposição via Portal do Cliente / e-mail / WhatsApp; original com EXIF só dentro do tenant (audit) | Aceitável |
| R4 | Tela de aceite mostra resumo do serviço + valor + termos em fonte legível; checkbox "li e concordo" antes do touch; cliente recebe cópia PDF | Aceitável |
| R5 | PIN/biometria do dispositivo obrigatória no app; wipe remoto em furto reportado; cache local cifrado; sessão expira após X dias offline | Aceitável |
| R6 | INV nova: "introdução de matching biométrico exige novo RIPD aprovado + ADR"; hook `block-biometric-feature.sh` (a criar) bloqueia merge sem evidência | Aceitável |

### 6. Balanceamento de legítimo interesse (GPS técnico)
- **Finalidade legítima:** prova de execução, segurança do trabalho (saber onde está o técnico em emergência), cumprimento ISO 17025/9001.
- **Necessidade:** sem GPS contínuo, perde-se prova de tempo em obra (impacto fiscal/trabalhista) e rastreabilidade técnica.
- **Equilíbrio:** técnico recebe ganho (sem WhatsApp pessoal, segurança em emergência) + opt-in explícito + visibilidade do próprio dado + escopo limitado ao horário de OS — interesse legítimo prevalece.

### 7. Direitos do titular
Técnico exporta próprio histórico GPS via tela "Meus dados (LGPD)" (US-ACS-012). Cliente final pede exclusão de foto via canal Portal do Cliente — anonimização (face borrada) mantida a foto se ela compõe evidência ISO 17025.

### 8. Transferência internacional
Não — dados ficam em Hostinger SP/BR + B2 EU Central (com decisão adequação ANPD).

### 9. Decisão
- ✅ Aprovado para implementar **com**:
  - INV nova "biometria-matching exige novo RIPD + ADR"
  - Política de admissão atualizada com opt-in GPS antes do 1º técnico usando o app
  - DPIA-02 revisado se app evoluir para versão com selfie/face match

### 10. Revisão
- A cada release maior do App Técnico ou trimestral, o que vier primeiro.

---

## DPIA-03 — Segurança do Trabalho: ASO (dado sensível de saúde)

### 1. Operação avaliada
- **Operação:** RAT-14 — armazenamento e processamento de ASO (Atestado de Saúde Ocupacional) de colaboradores do tenant: tipo (admissional/periódico/retorno/mudança/demissional), resultado (apto/inapto/apto-com-restrição), médico examinador, validade, PDF do laudo.
- **Módulos:** `docs/dominios/rh-frota-qualidade/modulos/seguranca-trabalho/` (US-SST-003 alerta ASO vencido, US-SST-004 bloqueio sem ASO) + `docs/dominios/rh-frota-qualidade/modulos/treinamentos/` (vinculação ASO ↔ habilitação).
- **Categoria de dado:** **sensível (saúde — art. 11 LGPD)**.
- **Titulares afetados:** colaboradores do tenant.
- **Frequência:** periódica (admissional + anual mínimo NR-7).

### 2. Necessidade e proporcionalidade
- **Por que:** NR-7 (PCMSO) + CLT art. 168 + NR-35 (saúde para altura) obrigam o empregador a ter ASO válido para cada colaborador exposto a risco. Sem armazenar, empregador não cumpre obrigação legal e Aferê vira "papel-passado".
- **Alternativas:** (a) armazenar só hash + flag apto/inapto — não atende auditoria MTE que exige laudo; (b) terceirizar para SaaS de medicina ocupacional — possível V2; MVP é módulo nativo.
- **Minimização:** Aferê armazena **resultado** (apto/inapto/restrição), **validade** e **PDF do laudo**. Não armazena diagnóstico específico, CID-10, exames complementares — esses ficam com o médico examinador / clínica.

### 3. Base legal
- **Art. 11 II "a" — cumprimento de obrigação legal/regulatória** do empregador (NR-7, CLT 168, NR-35, ANVISA/MTE). Sem consentimento (não é base aplicável a vínculo trabalhista para dado de saúde ocupacional — Enunciado CD/ANPD).
- **Não há base art. 11 I (consentimento)** — colaborador NÃO pode "recusar" ASO mantendo vínculo de trabalho em função de risco; consentimento seria viciado.

### 4. Riscos identificados
| ID | Risco | Prob. | Imp. | Score |
|----|-------|-------|------|-------|
| R1 | Acesso ao laudo por perfil sem necessidade (atendente vê ASO) | 3 | 5 | 15 |
| R2 | Diagnóstico detalhado vaza no PDF (médico colocou CID-10) | 3 | 5 | 15 |
| R3 | ASO vaza para gestor comercial e influencia decisão de promoção (discriminação) | 2 | 5 | 10 |
| R4 | Colaborador demitido pede exclusão do ASO (LGPD direito esquecimento) | 4 | 3 | 12 |
| R5 | Backup com ASO em jurisdição inadequada | 2 | 5 | 10 |
| R6 | ASO carregado por terceiro mal-intencionado para fraude | 1 | 4 | 4 |

### 5. Medidas de mitigação
| Risco | Medida | Resíduo |
|-------|--------|---------|
| R1 | RBAC: somente "gerente SST" + "RH" + "médico do trabalho" + auditor (read-only) veem laudo; demais veem só "apto/inapto/validade" | Aceitável |
| R2 | UI no upload alerta: "se o laudo contém diagnóstico/CID-10, peça versão sem diagnóstico ao médico — Aferê armazena apenas aptidão"; campo opcional "redigir CID antes de subir" | Aceitável residual — depende do médico cooperar |
| R3 | Auditoria mensal de quem acessa ASO; alerta automático se gestor comercial acessou ASO de subordinado | Aceitável |
| R4 | NR-7 item 7.4.5.1 exige guarda **20 anos pós-vínculo**; obrigação legal vence direito de esquecimento; titular informado do prazo no momento do pedido | Conforme — não-mitigável (lei vence LGPD) |
| R5 | Encryption-at-rest com chave KMS por tenant + B2 com B2-EU + crypto-shredding na rescisão tenant respeitando prazo NR-7 | Aceitável |
| R6 | Upload exige perfil "gerente SST" + 2FA + log WORM do upload | Aceitável |

### 6. Balanceamento de legítimo interesse
Não aplicável — base é obrigação legal art. 11 II "a".

### 7. Direitos do titular
- Acesso: colaborador exporta próprio histórico ASO via "Meus dados (LGPD)".
- Correção: solicitação ao gerente SST + médico examinador.
- Exclusão: bloqueada por 20 anos pós-vínculo (NR-7) — após esse prazo, anonimização (CPF → hash, nome → "Colaborador anonimizado").

### 8. Transferência internacional
Backup em B2 EU Central — UE tem decisão de adequação ANPD. Sem outra transferência.

### 9. Decisão
- ✅ Aprovado para implementar **com**:
  - RBAC estrito (R1 mitigado em código)
  - UI de upload com aviso de redação CID-10 (R2)
  - Alerta auditoria de acesso anômalo (R3)
  - Comunicação ao colaborador sobre prazo NR-7 antes de armazenar (transparência LGPD art. 9º)

### 10. Revisão
- Anual + a cada mudança da NR-7 ou novo Enunciado CD/ANPD.

---

## DPIA-04 — Comunicação Omnichannel: consentimento marketing + rastreio multi-canal

### 1. Operação avaliada
- **Operação:** RAT-12 — rastreio de consentimento (opt-in/opt-out) por canal (WhatsApp + e-mail + SMS + chat portal) por finalidade (transacional vs marketing/comercial) + bloqueio de envio quando opt-out.
- **Módulo:** `docs/dominios/comercial/modulos/comunicacao-omnichannel/` (US-COM-002, US-COM-003).
- **Categoria de dado:** identificação + comportamento (canal, frequência, opt-in/out histórico).
- **Titulares:** clientes finais do tenant que receberam comunicação ou interagiram.
- **Frequência:** contínua.

### 2. Necessidade e proporcionalidade
- **Por que:** LGPD art. 8º § 5º exige consentimento livre, informado, inequívoco; CDC art. 6º proíbe spam/cobrança vexatória; Meta (WhatsApp Business) exige opt-in registrado por canal externo; sem rastro digital, tenant vira inadimplente regulatório.
- **Alternativas:** (a) deixar tenant configurar opt-in em planilha externa — perde sincronismo + risco vazamento; (b) usar opt-in implícito ("já é cliente") — viola LGPD para marketing.
- **Minimização:** registra texto exato do termo + canal + timestamp + IP; sem captura de comportamento navegacional fora da própria comunicação.

### 3. Base legal
- **Consentimento explícito (art. 7º I)** para comunicação de marketing/comercial.
- **Execução de contrato (art. 7º V)** para comunicação transacional essencial (OS encerrada, fatura vencida, certificado pronto) — não exige consentimento adicional mas exige opt-out funcional.

### 4. Riscos identificados
| ID | Risco | Prob. | Imp. | Score |
|----|-------|-------|------|-------|
| R1 | Envio para cliente em opt-out (falha de bloqueio) | 3 | 5 | 15 |
| R2 | Opt-in coletado sem clareza da finalidade ("aceito termos genéricos") | 4 | 3 | 12 |
| R3 | Cliente reclama na ANPD por receber WhatsApp sem opt-in (Aferê é solidário com tenant) | 3 | 4 | 12 |
| R4 | Atendente envia mensagem fora do template aprovado por Meta | 4 | 3 | 12 |
| R5 | Histórico de opt-in editado ("alguém ajeitou") | 1 | 5 | 5 |
| R6 | Lista de clientes em opt-out vaza (assédio competitivo) | 2 | 4 | 8 |

### 5. Medidas de mitigação
| Risco | Medida | Resíduo |
|-------|--------|---------|
| R1 | Bloqueio em camada de envio (não no UI) — qualquer chamada `enviar(cliente, canal, finalidade)` consulta tabela de consentimento; falha = exceção bloqueante + alerta crítico; teste automático mensal | Aceitável |
| R2 | UI de opt-in mostra cada finalidade separada (toggle por finalidade) + texto plain-language (não jurídico); versão do termo registrada | Aceitável |
| R3 | DPA Aferê↔tenant deixa claro: tenant é controlador; Aferê só executa o que tenant configurou; Aferê é operador (responsabilidade solidária mitigada por DPA) | Aceitável |
| R4 | Sistema só envia template aprovado pelo canal externo; texto livre só em janela 24h pós-mensagem do cliente; auditoria | Aceitável |
| R5 | WORM em B2 com chave KMS separada; admin do tenant não pode editar (`INV-001`) | Aceitável |
| R6 | RBAC: export de lista exige perfil "gerente comercial" + log + 2FA + watermark do tenant no export | Aceitável |

### 6. Balanceamento legítimo interesse
Não aplicável — consentimento explícito é base para marketing.

### 7. Direitos do titular
- Opt-out a qualquer momento e canal (US-COM-003).
- Acesso ao histórico de comunicação direcionada via Portal do Cliente.
- Exclusão: opt-out + 6 meses retenção pós-revogação (prova LGPD de cumprimento) + anonimização.

### 8. Transferência internacional
Provedores: WhatsApp (Meta — EUA), SendGrid/Mailgun (EUA), Twilio (EUA). Todos com Cláusulas-Padrão Contratuais; PII minimizada no payload (sem CPF; nome + telefone + texto).

### 9. Decisão
- ✅ Aprovado para implementar **com**:
  - Bloqueio em camada de envio (R1) — invariante de código + teste
  - UI de opt-in por finalidade (R2)
  - DPA atualizado antes do release (R3)
  - Auditoria mensal de envio fora-de-template (R4)

### 10. Revisão
- Trimestral nos 12 primeiros meses + anual depois.

---

## DPIA-05 — Billing SaaS: cobrança recorrente + PCI por delegação

### 1. Operação avaliada
- **Operação:** RAT-16 — cobrança mensal/anual do tenant cliente do Aferê via gateway de pagamento (Stripe/PagSeguro), com tokenização do cartão pelo gateway e armazenamento mínimo no Aferê (token opaco + bandeira + últimos 4).
- **Módulo:** `docs/dominios/financeiro/modulos/billing-saas/` (US-BIL-002 cobrança recorrente).
- **Categoria de dado:** identificação + financeiro (subset).
- **Titulares:** representante legal do tenant cliente (PJ que contrata o Aferê).
- **Frequência:** mensal/anual recorrente.

### 2. Necessidade e proporcionalidade
- **Por que:** sem cobrança automática, SaaS não escala; sem dado mínimo (token + bandeira + últimos 4), tenant não vê extrato/troca cartão.
- **Alternativas:** (a) boleto/Pix apenas — exclui mercado de cartão recorrente; (b) cobrança manual via planilha — não escala.
- **Minimização:** PAN completo + CVV + track **nunca** entram no Aferê; somente token opaco do gateway. Escopo PCI-DSS reduzido a **SAQ-A** (delegação total ao gateway certificado).

### 3. Base legal
- Execução de contrato (art. 7º V) + obrigação fiscal (art. 7º II) para NFS-e do SaaS.

### 4. Riscos identificados
| ID | Risco | Prob. | Imp. | Score |
|----|-------|-------|------|-------|
| R1 | Webhook do gateway falsificado (atacante simula pagamento) | 3 | 5 | 15 |
| R2 | Aferê acidentalmente loga PAN/CVV (linha de log de debug) | 2 | 5 | 10 |
| R3 | Token do gateway vaza (atacante usa pra clonar cobranças no gateway) | 2 | 4 | 8 |
| R4 | Cobrança duplicada por job não-idempotente | 3 | 3 | 9 |
| R5 | Tenant cancela cartão e Aferê continua tentando (CDC art. 39) | 3 | 3 | 9 |
| R6 | Mudança de gateway expõe tokens não-portáveis | 2 | 3 | 6 |

### 5. Medidas de mitigação
| Risco | Medida | Resíduo |
|-------|--------|---------|
| R1 | Webhook valida assinatura HMAC + IP allowlist do gateway + idempotência por `event_id` | Aceitável |
| R2 | Filtro de log com regex PAN/CVV (PCI-DSS req 3.3); rejeição em CI; revisão trimestral de logs | Aceitável |
| R3 | Token escopado por tenant + rotação trimestral; gateway tem 2FA na conta admin Aferê | Aceitável |
| R4 | Job idempotente por `(tenant_id, periodo)`; tentativa duplicada retorna mesma fatura existente | Aceitável |
| R5 | Após 3 falhas consecutivas, sistema bloqueia novas tentativas e abre ticket para tenant regularizar; comunicação clara ao tenant | Aceitável |
| R6 | Cláusula contratual: gateway exporta tokens em formato padrão Stripe/Adyen na rescisão; ADR específica antes de troca | Aceitável |

### 6. Balanceamento legítimo interesse
Não aplicável — base é contrato + obrigação fiscal.

### 7. Direitos do titular
- Acesso: extrato de cobranças em painel do tenant.
- Correção: trocar cartão a qualquer momento.
- Exclusão: cancelamento do contrato + crypto-shredding após prazo fiscal (5 anos); token revogado no gateway + 30 dias.

### 8. Transferência internacional
Stripe (EUA) ou PagSeguro (BR). Stripe via Cláusulas-Padrão. Aferê comunica ao tenant qual gateway está em uso.

### 9. Decisão
- ✅ Aprovado para implementar **com**:
  - PCI-DSS SAQ-A assinado antes do release (gateway certificado)
  - HMAC + IP allowlist (R1) — não-negociável
  - Filtro log PAN/CVV (R2) — hook em CI
  - Documentar contratualmente conduta de cancelamento (R5)

### 10. Revisão
- Anual + a cada troca de gateway + a cada mudança no PCI-DSS.

---

## Próximos passos

1. **DPO formal designado** (V2): aprovar formalmente DPIA-01..05 antes do release de cada módulo.
2. **Hooks de invariante** (a criar):
   - `block-biometric-feature.sh` — bloqueia merge que adiciona matching biométrico sem novo RIPD aprovado.
   - `log-pci-scanner.sh` — bloqueia commit com log que pode vazar PAN/CVV (regex).
3. **Auditoria trimestral** Família 5 — Auditor de Segurança valida que mitigações listadas estão em código + teste.
4. **Atualização dos PRDs** correspondentes — referência cruzada `dpia-modulos-novos.md#DPIA-NN` em cada PRD impactado.

---

## Referências

- `docs/conformidade/comum/lgpd-rat.md` — RAT-11 a RAT-16 (novas entradas)
- `docs/conformidade/comum/ripd-modelo.md` — template formal
- `docs/conformidade/comum/seguranca-dados.md` — política de segurança
- `docs/conformidade/comum/retencao-matriz.md` — prazos consolidados
- LGPD: Lei 13.709/2018 art. 5º, 6º, 7º, 11, 38, 50
- ANPD Resolução 2/2022 (RIPD) + 15/2024 (incidentes)
- Enunciado CD/ANPD 4 (DPO em larga escala)
- NR-7 (PCMSO) item 7.4.5.1 (guarda 20 anos)
- PCI-DSS v4.0 SAQ-A (escopo delegado)
