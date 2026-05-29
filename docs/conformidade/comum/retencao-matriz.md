---
owner: roldao
revisado_em: 2026-05-28
proximo_review: 2026-08-23
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

> **Nota terminológica (FA-A1 R3 — parecer advogado 2026-05-18):** onde a matriz diz "anonimização (CPF → hash)", trata-se tecnicamente de **pseudonimização com chave de servidor** (HMAC-SHA256 é irreversível, mas CPF tem espaço enumerável — quem tiver a chave de hash + lista de CPFs confirma presença por força bruta). Só vira **anonimização efetiva** quando combinada com (a) crypto-shredding da chave KMS do tenant (dado cru ilegível) **e** (b) indisponibilidade da chave de hash de PII para aquele dado. A redação "anonimização por hash" nas linhas da §2/§3 deve ser lida sob essa ressalva — não qualificar como anonimização pura perante a ANPD.

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
| **Chave de hash de PII aposentada (`PII_HASH_KEYS_RETIRED` — FA-A1)** | ≥ maior prazo de qualquer audit trail que a usou | 10 anos (alinhado a "audit trail paths sensíveis") | Prestação de contas LGPD art. 37 + art. 18/19 (titular saber acessos) | Cofre de segredo do app (env/secret manager — NÃO no banco do tenant) | **Eliminação só após crypto-shredding de 100% dos hashes gerados sob ela.** Descartar antes torna a trilha permanentemente INCONCLUSIVA (perda irreversível de prova exigível) |
| **Comunicação com ANPD / órgão regulador** | 5 anos | 10 anos | Obrigação regulatória | B2 WORM | Manter (referência futura) |
| **Contrato assinado entre Aferê e tenant (DPA, ToS, addendum)** | 5 anos após término + 5 anos | 10 anos | Direito civil + boas práticas | B2 WORM | Manter |
| **ASO (Atestado de Saúde Ocupacional)** | **20 anos pós-vínculo** | 20 anos | **NR-7 item 7.4.5.1 (vence LGPD direito esquecimento)** + CLT art. 168 | PG (vínculo ativo) → B2 WORM cifrado por chave KMS do tenant | Anonimização (CPF → hash; nome → "Colaborador anonimizado #N") preservando aptidão+validade+médico para auditoria MTE histórica |
| **Foto com GPS/EXIF do App Técnico** | 5 anos | 5 anos | Execução contrato + ISO 17025 7.7 (rastreabilidade) + audit | PG (90 dias quente) → B2 cifrado | Anonimização: face borrada + EXIF removido; foto-anônima preservada 25 anos se compõe evidência ISO 17025 |
| **Assinatura touch de aceite + CPF (App Técnico)** | 5 anos | 5 anos | Execução contrato (prova de aceite) | B2 WORM | Anonimização CPF (hash) + traçado preservado por 25 anos se compõe evidência ISO 17025 |
| **Trilha GPS contínua do técnico (deslocamento + jornada)** | 5 anos | 5 anos | Legítimo interesse (RAT-13) + obrigação trabalhista (jornada) | PG (90 dias) → B2 frio | Crypto-shredding |
| **Cobrança recorrente Billing SaaS (token gateway, bandeira, últimos 4)** | Vigência + 30 dias | 5 anos para fatura | Execução contrato + obrigação fiscal | PG (token) + B2 (fatura) | Token: revogado no gateway + descartado; fatura: anonimização + crypto-shredding |
| **Histórico de consentimento Comunicação Omnichannel (opt-in/opt-out)** | Opt-out + 6 meses (prova) | 5 anos | Cumprimento LGPD art. 8º (prova de consentimento) | B2 WORM | Anonimização (telefone/e-mail → hash) preservando registro de revogação |
| **Sessão de Suporte SaaS (acesso remoto)** | 5 anos | 10 anos | Audit reforçado (INV-001) + defesa em incidente | B2 WORM (chave KMS separada — atendente Aferê não tem chave) | Manter (audit forense) |
| **Cadastro de equipamento do cliente final (ativo)** | Vigência cliente + 5 anos | 25 anos se tem cert emitido (INV-025/ISO 17025 cl. 8.4) | LGPD art. 7º V + ISO 17025 cl. 8.4 quando há cert | PG (vigência) → B2 (resto) | Anonimização do vínculo `cliente_atual_id` (NULL) se cliente shredded; `cliente_id_original_hash` preservado |
| **`bus_outbox` (fila intermediária de eventos de domínio — T-CLI-107)** | `processado_em` + 0 dias | `processado_em` + 7 dias | LGPD art. 6º III (minimização) — NÃO é evidência regulatória; cadeia hash F-A é a fonte da verdade imutável | PG (RLS FORCE) | DELETE físico via cleanup job (Wave A) — cascata via `tenant_id` em offboarding tenant. Pedido de eliminação de titular individual (cenário B) NÃO toca outbox: minimização cumprida pelo cleanup natural de 7 dias |
| **Equipamento sucateado/extraviado** | 5 anos pós-sucateamento | 25 anos se tem cert emitido | ISO 17025 cl. 8.4 + audit fiscal | B2 WORM | Anonimização vínculos PII; hash + dados técnicos preservados |
| **EquipamentoEvento / audit_trail.eventos do equipamento** | 5 anos | 25 anos | ISO 17025 cl. 8.4 + INV-001 (hash chain) | B2 WORM | Payload já sanitizado (hashes); manter |
| **QR Code (token + hash + emissão + revogação)** | Enquanto equipamento ativo + 5 anos | 25 anos se referenciado por cert | Execução contrato + ISO 17025 cl. 8.4 | PG (ativo) → B2 (revogado) | Revogação automática 90 dias após re-emissão; hash mantido em audit |
| **Foto do equipamento (RAT-EQP-FOTO)** | Vigência equipamento + 5 anos pós-sucateamento | 25 anos se compõe evidência ISO 17025 | LGPD art. 7º V (técnica) ou art. 11 § 4º (sensível se rosto) + ISO 17025 cl. 7.4.4 (condição chegada) | PG (90 dias quente) → B2 cifrado | EXIF removido no upload; se rosto identificável → blur ou eliminação; se compõe evidência ISO → preservar 25 anos |
| **`TransferenciaEquipamentoAceite` + termo v1.x (US-EQP-004)** | 5 anos (Receita — defesa em contestação fiscal) | **25 anos** (cadeia metrológica intocada) | **ISO 17025 cl. 8.4 + LGPD art. 16 I (preservação por obrigação legal) + RBC NIT-DICLA-021 cl. 4.2** | B2 WORM | Payload já tem `cedente_id_hash`/`cessionario_id_hash` (HMAC tenant) — sem PII em claro. Texto do termo versionado preservado integralmente (CC art. 462). |
| **`ConsentimentoHistoricoEquipamento` (T-EQP-039 / P-EQP-R6)** | Vigência consentimento + 5 anos | **25 anos** (defesa probatória em incidente cessão) | **ISO 17025 cl. 8.4 + LGPD art. 16 I + RBC NIT-DICLA-021 cl. 4.2 + LGPD art. 8 §5 (revogabilidade auditável)** | B2 WORM | Justificativa de revogação gravada como hash HMAC (texto cru NUNCA persistido). Manter granularidade (nada/resumo/completo) por 25 anos pra reconstruir fluxo de visibilidade. |
| **`EquipamentoDevolucaoFoto` (US-EQP-006-4 / cl. 7.4.5)** | Vigência equipamento + 5 anos pós-devolução | **25 anos** (encerramento do depósito CC art. 624 + cadeia ISO) | **ISO 17025 cl. 8.4 + LGPD art. 16 I + RBC NIT-DICLA-021 cl. 4.2 + LGPD art. 7º V (defesa)** | PG (90 dias) → B2 WORM cifrado | EXIF strip + SHA-256 imutável pós-INSERT. Termo de devolução com `termo_aceite_hash` (HMAC) anexado. |
| **`RecebimentoProvisorio` + foto (Caminho A Roldão)** | TTL D+7 (descartado) ou vigência Equipamento promovido + 5 anos | **25 anos** quando promovido a Equipamento canônico | **ISO 17025 cl. 8.4 + LGPD art. 16 I + RBC NIT-DICLA-021 cl. 4.2** | B2 WORM (promovido); B2 frio (descartado) | INV-EQP-PROV-001: provisório descartado MANTÉM registro 25a (forense) — só `status` muda para `expirado_descartado`. Promovido vincula UUID equipamento_promovido_id. |
| **`EquipamentoVersao` (US-EQP-002 / cl. 8.4)** | 5 anos (Receita) | **25 anos** (cada mudança controlada vincula a cert metrológico vigente) | **ISO 17025 cl. 8.4 (registros técnicos imutáveis) + LGPD art. 16 I + RBC NIT-DICLA-021 cl. 4.2** | B2 WORM | Payload sanitizado (whitelist 14 campos / blacklist 7 — INV-EQP-VERSAO-002). `valor_anterior_hash`/`valor_novo_hash` HMAC tenant; texto cru NUNCA persistido. Tabela INSERT-only (T-EQP-012). |
| **OS — atividade `calibracao` (ADR-0023)** | 5 anos (Receita se faturada) | **25 anos** (vincula a certificado emitido) | ISO 17025 cl. 8.4 + LGPD art. 16 I + RBC NIT-DICLA-021 cl. 4.2 | B2 WORM | Anonimização vínculo `cliente_id` (NULL); registro técnico preservado (cadeia metrológica intocada) |
| **OS — atividade `manutencao_corretiva` (ADR-0023)** | 5 anos (Receita se faturada) | 5 anos | LGPD art. 7º V (execução contrato) + CTN art. 173 | PG (90 dias quente) → B2 frio | Anonimização vínculo `cliente_id` (NULL) ao fim de 5a; sem cadeia ISO obrigatória |
| **OS — atividade `manutencao_preventiva` (ADR-0023)** | 5 anos (Receita se faturada) | **25 anos quando faz parte de contrato preventivo de equipamento calibrado** | LGPD art. 7º V + ISO 17025 cl. 8.4 (quando vinculada a equipamento calibrado) | B2 WORM se vinculada a equipamento com cert; B2 frio caso contrário | Anonimização parcial; manter registro técnico se vinculado a cert |
| **OS — atividade `instalacao` (ADR-0023)** | 5 anos (Receita + garantia legal CDC art. 26) | **25 anos quando precede calibração inicial registrada** | LGPD art. 7º V + CDC art. 26 + ISO 17025 cl. 8.4 (se calibração inicial) | B2 WORM se precede cert; B2 frio caso contrário | Anonimização parcial; manter registro técnico se vinculado a cert |
| **OS — atividade `verificacao_inmetro` (ADR-0023)** | 5 anos | **20 anos** (laudo INMETRO tem efeito regulatório) | INMETRO Portaria 590 + LGPD art. 7º II (obrigação legal) | B2 WORM | Manter laudo + assinatura RT (anonimização CPF preservando nome+CREA) |
| **OS — atividade `vistoria` (ADR-0023)** | 5 anos (CC art. 205 prescrição civil ordinária) | 10 anos | LGPD art. 7º V + CC art. 205 (prazo prescricional ordinário) | B2 WORM | Manter laudo de vistoria assinado por RT (passivo civil em compra de equipamento usado — GAP-SEG-02 corretora) |
| **OS sem atividade `calibracao`/`verificacao_inmetro` (cancelada/só-manutenção)** | 5 anos (Receita) | 5 anos | LGPD art. 7º V + CTN art. 173 | PG → B2 | Anonimização + crypto-shredding (sem obrigação ISO/INMETRO) |
| **`AceiteAtividade` (TEMA-D.3 — Lei 14.063/2020)** | retenção da atividade pai + 1 ano | igual atividade pai | Lei 14.063 art. 4º (prova de manifestação) + LGPD art. 7º V | mesma da atividade | Versão termo + hash texto + `ip_hash` + timestamp preservados; assinatura touch original anonimizada após 5a se atividade não-calibração; certificate A1/A3 issuer hash preservado |
| **`EventoDeOS` + `EventoDeCalibracao` (audit imutável WORM — RAT-08)** | 5 anos | **25 anos quando vinculado a atividade calibração ou certificado** | ISO 17025 cl. 8.4 + Marco Civil art. 15 + INV-OS-AUD-001/INV-CAL-AUD-001 | B2 WORM | Payload já sanitizado (hash HMAC tenant); manter integralmente |
| **`PadraoMetrologico` — cadastro-mestre do padrão (M5 — ADR-0040)** | 5 anos pós-baixa/sucateamento | **25 anos** (cadeia de rastreabilidade ao SI — cl. 6.5) | **ISO 17025 cl. 6.4/6.5/8.4 + LGPD art. 16 I + RBC NIT-DICLA-021** | PG (estado ≠ terminal) → B2 WORM | Soft-delete B (sem DELETE físico — INV-SOFT-002); não contém PII direta (`localizacao_lab` anti-PII). Manter registro técnico |
| **`RecalExternoPadrao` / `VerificacaoIntermediaria` / `IntercomparacaoPT` (M5 — cl. 6.4.10/6.6)** | 5 anos | **25 anos** (histórico de calibração/VI/PT do padrão sustenta a validade dos certificados emitidos com ele) | **ISO 17025 cl. 6.4/6.6/8.4 + LGPD art. 16 I + RBC NIT-DICLA-021** | B2 WORM (append-only / imutável pós-retorno) | Cert externo PDF é `storage_key` opaca de binário cifrado por chave KMS do tenant (C-14 — pode conter PII de terceiro); método VI / ação corretiva canonicalizados + hash (ADR-0029). Manter |
| **`AnaliseCartaControle` (M5 — carta Shewhart probatória, ADR-0070)** | 5 anos | **25 anos** (registro probatório congelado da decisão metrológica — cl. 8.4) | **ISO 17025 cl. 7.11/8.4 + LGPD art. 16 I + INV-PAD-010** | B2 WORM (append-only) | Justificativa do RT canonicalizada + hash (ADR-0029); limites/σ/versão-motor preservados pra replay CGCRE. Manter |
| **`*_id_hash` de funcionário em evento de padrão (responsável recal / executor VI / RT que aprova — M5)** | igual ao registro-pai (até 25 anos) | **25 anos** | **Prestação de contas LGPD art. 37 + ISO 17025 cl. 8.4** — pseudônimo (HMAC-tenant ADR-0064) permanece dado pessoal (LGPD art. 12: reversível por quem detém a chave) | B2 WORM (junto do registro-pai) | NUNCA PII em claro (só `HashVersionado`). Eliminação só via crypto-shredding da chave HMAC do tenant (alinhado à linha "Chave de hash de PII aposentada") — descartar antes torna a trilha metrológica inconclusiva |
| **Nome desnormalizado do executor/responsável na evidência técnica de evento de padrão (recal / VI / PT — M5, C-13)** | 5 anos (cadastro operacional quente) | **~25 anos** (nome compõe a evidência técnica de VI/PT/recal — cl. 8.4) | **ISO 17025 cl. 8.4 + LGPD art. 7º II/V + art. 16 I (preservação por obrigação legal)** | PG (operacional quente 5a) → B2 WORM (evidência 25a) | Replica **Cenário A**: após 5a o vínculo operacional segue a retenção do cadastro; o nome desnormalizado que compõe a evidência herda 25 anos com **CPF anonimizado (hash) e nome preservado**. Direito do titular art. 18 = recusa parcial fundamentada (art. 16 I). Distinto da linha acima (que é o `*_id_hash` no evento WORM) |
| **PDF de certificado externo de recalibração do padrão (`cert_externo_storage_key` — M5, C-13/C-14)** | Vigência do padrão + 5 anos | **~25 anos** (sustenta a validade dos certificados emitidos com o padrão — cl. 6.4/8.4) | **ISO 17025 cl. 6.4/6.6/8.4 + LGPD art. 7º II + art. 16 I** | B2 WORM — **binário cifrado pela chave KMS do tenant** (envelope encryption); evento guarda só hash | **PODE conter PII de TERCEIRO** (assinatura/nome/CPF do signatário do lab acreditado externo). Documento probatório cifrado — **NÃO anonimizar o binário**. Fim de prazo = **crypto-shredding** da chave KMS do tenant (offboarding). Redação DPA sobre PII de terceiro embarcada → lote revisão OAB pré-produção |

---

## 3. Como resolver conflito Receita × ISO × LGPD

### Cenário A: Certificado de calibração com PII do signatário humano
- Receita: 5 anos (se há fatura ligada)
- ISO 17025: ~25 anos
- LGPD direito ao esquecimento: titular pode pedir

**Resolução (regra explícita para módulo Calibração):**
- **Manter certificado** (cumprimento de obrigação regulatória — base legal LGPD art. 7º II)
- **PII do signatário anonimizada após 5 anos**, dados técnicos preservados por ~25 anos:
  - CPF do signatário → hash irreversível
  - Nome do signatário → preservado (competência técnica é parte do certificado)
  - Cargo/competência → preservado
  - PII do cliente/signatário do tomador → substituir CPF por hash + manter razão social/nome para rastreabilidade ISO
  - **Dados técnicos da calibração (medições, incertezas, padrões usados, datas, condições ambientais)** → preservados 25 anos sem anonimização
- Documentar a substituição em audit trail WORM (`INV-001`) com hash do estado anterior + hash do estado anonimizado
- **Drill DRILL-RET-07** (a adicionar): em 2031, certificado de 2026 deve ter PII anonimizada + dados técnicos lidos sem perda

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

### Cenário D: Colaborador demitido pede exclusão do ASO (NR-7 × LGPD direito esquecimento)
- LGPD art. 18 VI: titular pode pedir exclusão.
- NR-7 item 7.4.5.1: empregador deve guardar **20 anos pós-vínculo**.
- Conflito: norma trabalhista vence LGPD (base art. 11 II "a" obrigação legal).

**Resolução:**
1. Comunicar ao titular o prazo legal (20 anos) e a recusa fundamentada na NR-7 (transparência LGPD art. 9º).
2. Restringir acesso ao ASO: somente perfis "RH" + "gerente SST" + "auditor read-only" + médico do trabalho continuam vendo; demais perfis perdem acesso imediato.
3. Após o prazo NR-7 (20 anos pós-vínculo): anonimização (CPF → hash, nome → "Colaborador anonimizado #N") preservando: aptidão (apto/inapto/restrição), validade, médico examinador (CRM), data — necessários para auditoria MTE histórica.
4. Registrar pedido + resposta + prazo em audit WORM.

### Cenário E: Cliente final do tenant pede exclusão de foto com sua face (App Técnico)
- Foto capturada com EXIF + GPS durante OS no estabelecimento dele.
- ISO 17025 cláusula 7.7 pode exigir foto como evidência.

**Resolução:**
1. Avaliar se a foto compõe evidência ISO 17025/9001 da OS específica.
2. **Se compõe evidência:** anonimizar in-place — face borrada + EXIF removido + assinatura preservada como evidência; manter por 25 anos.
3. **Se NÃO compõe evidência (foto opcional/avaria/lembrete):** eliminação total imediata.
4. Comunicar ao titular a decisão + base legal.
5. Registrar em audit WORM.

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
| DRILL-RET-07 | Certificado calibração 2026 lido em 2031 com PII signatário anonimizada | CPF signatário = hash; nome preservado; dados técnicos completos |
| DRILL-RET-08 | Colaborador demitido em 2026 pede exclusão ASO em 2027 | Recusa fundamentada NR-7 + acesso restrito imediato + anonimização agendada para 2046 |
| DRILL-RET-09 | ASO de 2026 em 2046 (20 anos pós-vínculo) | CPF anonimizado, validade+aptidão preservados, médico CRM legível |
| DRILL-RET-10 | Cliente pede exclusão foto facial 2026 que compõe evidência ISO 17025 | Face borrada + EXIF removido in-place, audit registra ✓ |
| DRILL-RET-11 | `bus_outbox` retenção 7 dias pós-processado (T-CLI-107) | `SELECT COUNT(*) FROM bus_outbox WHERE processado_em < now() - interval '7 days'` retorna 0. **Mensal** (BLOQ-A2 advogado) |
| DRILL-RET-PAD-01 | Recalibração externa de padrão registrada em 2026 (com nome do executor/responsável + PDF cert externo cifrado) lida em 2031 (M5 — análogo DRILL-RET-07) | CPF executor = hash; nome do responsável preservado na evidência técnica; PDF cert externo legível via descriptografia da chave KMS do tenant; dados técnicos do recal completos |

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
