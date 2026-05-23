---
owner: Roldão
revisado-em: 2026-05-23
status: stable
modulo: fiscal
dominio: financeiro
---

# PRD — Fiscal (NFS-e + NFe)

## 1. O que é

Emissão, cancelamento, correção e contingência de documentos fiscais (NFS-e municipal + NFe estadual quando aplicável). Integração via BaaS (PlugNotas/Focus) pra abstrair heterogeneidade de 5500+ municípios.

## 2. Por que existe

Dor #10 (NFS-e multi-município) — Big Job 04 (BIG-04). **Deadline regulatório 01/09/2026** (Porto Alegre 01/07/2026): municípios saem do padrão local pro CONFAZ 95/22 nacional. Sem isso, Aferê = receita zero (tenant não consegue faturar serviço).

Wave A #1 absoluto. Top 3 lock obrigatório.

## 3. Personas

P-FIN-01 (emite NFS-e), P-FIN-02 (dono — vê emissões/cancelamentos), P-FIN-05 (contador externo — V2 SPED), P-FIN-06 (auditor fiscal — V2 acesso indireto).

## 4. Escopo MVP-1 (Wave A)

- Emitir NFS-e em ≥ 70% dos municípios via BaaS (cobertura ABRASF + grandes capitais)
- Cancelar NFS-e (< 24h)
- Emitir CC-e (correção)
- Contingência automática via BaaS (SVC-AN/SVC-RS pra NFe; mecanismos do município pra NFS-e)
- Inutilização de numeração
- Configuração tenant: regime fiscal + alíquotas + código LC 116 (tenant configura com contador)
- WORM 5 anos do XML
- UI estado "operando em contingência"
- Audit completo de cada emissão/cancelamento
- Plug & play do certificado digital (A1; A3 conforme ADR-0009)

## 5. Escopo cutover 01/09/2026

- Smoke test sandbox 30 dias antes
- Comunicado aos tenants 15 dias antes
- Modo "rascunho postergado" durante semana de cutover
- Suporte estendido
- Postmortem

## 6. Non-goals MVP-1 (explícitos)

- **Aferê NÃO calcula imposto** — só exibe campos pra preenchimento orientado pelo contador.
- Cálculo de ISS/ICMS automático.
- Apuração mensal contábil (responsabilidade contador externo).
- SPED Fiscal export — V2.
- NFe completa (V2 — calibração emite NFS-e majoritariamente; NFe entra quando tenant vende peça).
- DDA (Débito Direto Autorizado).
- Cobertura de FP2 exclusivos (Vitória) — verificar BaaS antes de aceitar tenant da região (`fiscal.md`).
- Integração com sistema contábil externo (Domínio/Alterdata) — V2.
- Lucro Real complexo / ZFM SUFRAMA particular (anti-persona).
- **CT-e (Conhecimento de Transporte) — Wave B sob demanda** (ADR-0049). Recoleta de instrumento dispensa via NFS-e/NFA-e (regulamento UF).
- **NFC-e (NF Consumidor — varejo) — Wave B sob demanda** (ADR-0049). Calibração não vende em varejo.
- **Inutilização de NFS-e municipal — Wave B sob demanda** (cada município mecanismo próprio; modelo 55 coberto em US-FIS-005).
- **DCTF-Web / EFD-Reinf — V2** (responsabilidade contador externo no MVP-1).

## 7. User Stories + AC binários (BDD GIVEN-WHEN-THEN — Onda 5 saneamento 2026-05-23)

### US-FIS-001 — Emitir NFS-e a partir de Cert/OS concluída (fluxo correto Onda 8)

**Persona:** P-FIN-01 (operador financeiro do tenant)
**Gatilho correto (Onda 8 — auditor regulatório 7 corrigiu inversão):** **Certificado calibração emitido OU OS concluída → emite NFS-e → cria ContasReceber.TituloEmitido**. ContasReceber.Pago é evento POSTERIOR (pagamento da fatura emitida), NÃO gatilho de emissão.

- **AC-FIS-001-1 (happy):** GIVEN Certificado#C emitido (`Certificados.CertificadoEmitido`) OR OS#X concluída sem cert (manutenção) AND tenant tem cert A1/A3 vigente AND BaaS PlugNotas respondendo AND verificação OCSP do A3 retornou `good` (ADR-0046), WHEN consumer `Fiscal.gerar_nfse_de_servico_concluido(origem_id, tipo_servico)` é invocado, THEN endpoint POST `/api/v1/fiscal/nfse` retorna 201 com payload `{nfse_id, numero, chave_acesso_44, xml_url, pdf_url, status: "emitida"}` em p95 ≤ 5s AND evento `Fiscal.NFSeEmitida{nfse_id, cliente_referencia_hash, certificado_id, tipo_servico, valor_centavos}` publicado AND INV-INT-001 satisfeito (`tipo_servico=calibracao` → `certificado_id OR declaracao_id` NOT NULL — DeclaracaoCalibracaoBasica do `calibracao/prd.md` Onda 7) AND **INV-FIS-CR-001 satisfeito** (US-FIS-007 cria ContasReceber.TituloEmitido em ≤ 5s do `Fiscal.NFSeEmitida`).
- **AC-FIS-001-2 (cert vencido):** GIVEN cert digital tenant `vigencia_fim < now()`, WHEN POST `/api/v1/fiscal/nfse`, THEN retorna 422 com `{erro: "CERT_VENCIDO", detalhe, link_renovacao}` AND NENHUMA emissão.
- **AC-FIS-001-3 (BaaS down):** GIVEN PlugNotas timeout > 10s, WHEN POST `/api/v1/fiscal/nfse`, THEN sistema dispara contingência (AC-FIS-002) automaticamente em < 60s.
- **AC-FIS-001-4 (cross-tenant):** GIVEN consumer recebe evento `Certificados.CertificadoEmitido` de tenant A, WHEN tenta emitir NFS-e referenciando cliente de tenant B, THEN bloqueia hard com 422 anti-oracle (INV-TENANT-001).
- **AC-FIS-001-5 (idempotência):** WHEN POST com mesmo `Idempotency-Key: {causation_id}` 2 vezes em 24h, THEN retorna mesmo `nfse_id` ambas as vezes (IDEMP-001).
- **AC-FIS-001-6 (OCSP revoked — ADR-0046):** GIVEN A3 do tenant revogado pela AC (OCSP `revoked`), WHEN POST, THEN retorna 409 `{erro: "CERT_REVOGADO"}` + publica `A3.RevogacaoDetectada` + escalação P1.
- **AC-FIS-001-7 (município sem cobertura BaaS):** GIVEN onboarding de tenant em município sem cobertura BaaS declarada em `fiscal-contingencia.md`, WHEN tenant tenta ativar fiscal, THEN bloqueia ativação com 422 + mensagem clara + opção "cadastrar mecanismo manual" (V2).
- **Teste:** `tests/test_fiscal_us_001*.py`

### US-FIS-002 — Contingência automática SEFAZ/município fora

- **AC-FIS-002-1 (entrada):** GIVEN BaaS NF-e indisponível > 60s, WHEN próximo POST `/api/v1/fiscal/nfse`, THEN sistema entra em modo `contingencia=true`, UI mostra banner "Operando em contingência (SVC-AN)", evento `Fiscal.ContingenciaAtivada{provider, modo}` publicado.
- **AC-FIS-002-2 (saída):** GIVEN BaaS volta a responder (3 health checks ok consecutivos), WHEN próxima emissão, THEN sai de contingência, evento `Fiscal.ContingenciaDesativada` publicado, lote em contingência é reprocessado em background.
- **AC-FIS-002-3 (município sem SVC + rascunho postergado vence):** GIVEN município X não tem mecanismo de contingência declarado em `fiscal-contingencia.md`, WHEN BaaS cai, THEN sistema bloqueia emissão com 503 + mensagem clara + opção "rascunho postergado" salvando localmente. Rascunho postergado **vence em 48h**; após isso, sistema alerta dono Aferê + bloqueia fechamento de OS dependente até a NF ser emitida ou descartada formalmente.
- **Teste:** `tests/test_fiscal_us_002*.py` (mock chaos engineering BaaS)

### US-FIS-003 — Cancelar NFS-e em < 24h

- **AC-FIS-003-1 (happy):** GIVEN NF-e#N emitida há < 24h, WHEN DELETE `/api/v1/fiscal/nfse/{N}` com motivo ≥30 chars, THEN cancela na SEFAZ + persiste `cancelado_em` + `motivo_cancelamento` + retorna 200 com novo XML cancelamento, em p95 ≤ 5s.
- **AC-FIS-003-2 (prazo expirado):** GIVEN NF-e#N emitida há > 24h, WHEN DELETE, THEN retorna 422 com `{erro: "PRAZO_EXPIRADO", detalhe: "Use CC-e ou nota de ajuste"}`.
- **AC-FIS-003-3 (cross-tenant):** tentar cancelar NF-e de outro tenant → 404 anti-oracle.
- **Teste:** `tests/test_fiscal_us_003*.py`

### US-FIS-004 — CC-e (Carta de Correção)

- **AC-FIS-004-1 (happy):** GIVEN NF-e#N emitida com descrição errada (campo corrigível por CC-e — não muda valor/CNPJ/data), WHEN POST `/api/v1/fiscal/nfse/{N}/cce` com `texto_correcao` (15-1000 chars), THEN gera CC-e na SEFAZ, retorna 201 com `{cce_id, sequencial, xml_url}`, máximo 20 CC-e por NF-e (limite SEFAZ).
- **AC-FIS-004-2 (campo não-corrigível):** GIVEN tentativa de CC-e em valor/CNPJ/data, WHEN POST, THEN 422 com lista de campos corrigíveis.
- **Teste:** `tests/test_fiscal_us_004*.py`

### US-FIS-005 — Inutilização de numeração

- **AC-FIS-005-1 (alerta):** GIVEN sistema detecta gap entre números emitidos (NF #100 emitida, #101..#105 puladas, #106 nova emissão), WHEN job diário roda, THEN notifica admin tenant + UI mostra "Inutilize #101 a #105 até DD/MM" (prazo SEFAZ — 30 dias).
- **AC-FIS-005-2 (inutilização):** GIVEN admin tenant clica "Inutilizar #101 a #105" + justificativa ≥30 chars, WHEN POST `/api/v1/fiscal/inutilizacao` com `{numero_inicio, numero_fim, justificativa}`, THEN gera evento INUT na SEFAZ, retorna 201, persiste em WORM.
- **AC-FIS-005-3 (prazo perdido):** GIVEN > 30 dias sem inutilizar, WHEN job roda, THEN escalation alerta P1 + dashboard inadequação fiscal.
- **Teste:** `tests/test_fiscal_us_005*.py`

### US-FIS-006 (V2) — Export contador externo

- **AC-FIS-006-1 (V2):** GIVEN papel `contador_externo` (V2), WHEN GET `/api/v1/fiscal/export?periodo=YYYY-MM&formato=sped|csv`, THEN retorna export read-only com audit reforçado (registra em `AcessoDadosCliente`).

### US-FIS-007 — `Fiscal.NFSeEmitida` cria ContasReceber.TituloEmitido (INV-FIS-CR-001 — Onda 8)

**Persona:** sistema (consumer financeiro)
**Gatilho:** evento `Fiscal.NFSeEmitida`

- **AC-FIS-007-1 (happy):** GIVEN `Fiscal.NFSeEmitida` consumido pelo módulo `financeiro/contas-receber`, WHEN handler executa, THEN cria `ContasReceber` com `{titulo_id, valor, vencimento, status: TituloEmitido, nfse_id_origem, cliente_id}` em ≤ 5s do evento AND publica `ContasReceber.TituloEmitido` AND **INV-FIS-CR-001 satisfeito**.
- **AC-FIS-007-2 (idempotência):** WHEN mesmo `nfse_id` chega 2x (replay), THEN cria 1 único título (IDEMP-001).
- **AC-FIS-007-3 (consumer cross-tenant):** isolation INV-TENANT-001 preservado.

### US-FIS-008 — Job anual atualizar_tabelas_fiscais (CFOP/CST/CSOSN/NCM/LC116 — Onda 8 A-REG-01)

**Persona:** sistema (job Celery anual + override manual admin)

- **AC-FIS-008-1:** GIVEN tabelas de referência fiscais (CFOP, CST, CSOSN, NCM, LC116) com versionamento, WHEN job `atualizar_tabelas_fiscais` roda anualmente em janeiro 02:00 BRT, THEN baixa fontes oficiais (Receita Federal + IBGE), valida hash de integridade, persiste em tabelas `referencia_fiscal_<tipo>` com `vigente_de/vigente_ate`, publica `Fiscal.TabelasReferenciaAtualizadas{versao, fonte}`.
- **AC-FIS-008-2 (override tenant):** GIVEN tenant em UF/município com regra exceção, WHEN admin tenant carrega override CSV, THEN sistema valida formato + persiste como overlay (não substitui global).
- **AC-FIS-008-3 (rollback):** GIVEN nova tabela quebra emissão de tenants, WHEN admin Aferê reverte versão, THEN job restaura versão anterior + notifica P1.

### US-FIS-009 — Devolução / estorno NF emitida (ADR-0049 — Onda 8)

- **AC-FIS-009-1 (devolução de mercadoria):** GIVEN cliente devolve peça/instrumento referente a NF emitida, WHEN POST `/api/v1/fiscal/devolucao` com `{nfe_origem_id, motivo, itens_devolvidos}`, THEN emite NF de ajuste com CFOP de retorno (5202/6202/etc conforme UF) OR registra NF de devolução do destinatário (entrada), persiste vínculo `nfe_origem_id`, retorna 201.
- **AC-FIS-009-2 (validação prazo):** GIVEN devolução fora de prazo regulamentar UF, WHEN POST, THEN avisa "exige NF complementar/ajuste extemporâneo (US-FIS-010)".

### US-FIS-010 — Nota de ajuste extemporânea (cancelamento > 24h)

- **AC-FIS-010-1:** GIVEN NF emitida há > 24h precisa ser ajustada (cancelamento extemporâneo SEFAZ aceita até 30 dias com NC mediante NF-e de ajuste), WHEN POST `/api/v1/fiscal/ajuste-extemporaneo` com motivo ≥50 chars + autorização admin, THEN emite NF de ajuste vinculada à NF original, persiste em WORM, audit `Fiscal.AjusteExtemporaneoEmitido`.
- **AC-FIS-010-2:** GIVEN tentativa fora de prazo de 30 dias, THEN 422 "fora de prazo SEFAZ — orientar contador externo".

### US-FIS-CUT-001 — Cutover CONFAZ 95/22 (deadline 01/09/2026)

- **AC-FIS-CUT-001-1:** GIVEN tenant em município que migra para CONFAZ 95/22 nacional em data X, WHEN data ≥ X-30, THEN UI mostra banner "Cutover em DD/MM — modo sandbox disponível", e-mail enviado ao admin tenant.
- **AC-FIS-CUT-001-2:** GIVEN durante semana do cutover, WHEN tenant emite NF-e, THEN sistema oferece modo "rascunho postergado" (salva local, emite quando estabilizar) sem perder receita.
- **AC-FIS-CUT-001-3:** GIVEN cutover concluído, WHEN postmortem gerado, THEN registra métricas (% emissões sucesso, tempo médio recuperação, tenants impactados).
- **Teste:** drill manual antes de 01/09/2026.

## 7.1 Dados de referência fiscais (Onda 8 A-REG-01)

Tabelas atualizadas anualmente via job `atualizar_tabelas_fiscais` (US-FIS-008). Fonte: Receita Federal (CFOP/CST/CSOSN/NCM) + IBGE/LC 116 (códigos de serviço). Override por tenant (overlay).

- `referencia_cfop` — Código Fiscal de Operações e Prestações
- `referencia_cst` — Código de Situação Tributária (ICMS/IPI/PIS/COFINS)
- `referencia_csosn` — Código de Situação Operacional do Simples Nacional
- `referencia_ncm` — Nomenclatura Comum do Mercosul
- `referencia_lc116` — Códigos de serviço LC 116/2003 + 175/2020

Enum `regime_tributario`: `NORMAL`, `SIMPLES_NACIONAL`, `MEI`, `ST_INDICADOR` (indicador substituição tributária — informativo), `LUCRO_REAL`, `LUCRO_PRESUMIDO`.

## 8. NFR

- Emissão p95 < 5s (depende de SEFAZ/município)
- Disponibilidade: 99,5% emissão (BaaS define SLA upstream)
- Contingência automática: detecção < 60s, troca de modo sem intervenção
- WORM: imutabilidade verificável por hash

## 9. Invariantes

- **INV-007 — NF-e contingência desde dia 0** (inegociável; sem contingência = não vai pra produção)
- INV-008 — audit log obrigatório de cada emissão/cancelamento/correção
- XML original preservado em WORM 5 anos
- **INV-INT-001 (corrigida Onda 8)** — NFS-e `tipo_servico=calibracao` exige `certificado_id OR declaracao_id NOT NULL` (DeclaracaoCalibracaoBasica não-RBC do `calibracao/prd.md` Onda 7)
- **INV-FIS-CR-001** (nova Onda 8) — `Fiscal.NFSeEmitida` cria `ContasReceber.TituloEmitido` em ≤ 5s (US-FIS-007). Fluxo correto: Cert/OS → NF → CR. `ContasReceber.Pago` é evento posterior do pagamento.
- **INV-A3-OCSP-001** (ADR-0046) — emissão NF bloqueia se A3 do tenant revogado (verificação OCSP/CRL online)

## 10. Dependências

- **Cert/OS concluído (Onda 8 fluxo corrigido)** — gatilho de emissão. Consome `Certificados.CertificadoEmitido` e `OperacaoOS.OSConcluida`.
- Contas a Receber (consumer downstream de `Fiscal.NFSeEmitida` — US-FIS-007 cria título)
- OP-FIN (módulo financeiro mínimo)
- `certificados-digitais` (Onda 8 — porta `verificar_status` OCSP/CRL — ADR-0046)
- ADR-0008 (FiscalProvider — fiscal pluggable; extende pra CT-e/NFC-e Wave B per ADR-0049)
- ADR-0009 (onde A3 assina)
- ADR-0046 (OCSP/CRL revogação online)
- ADR-0047 (LTV em cert calibração; NF não exige)
- ADR-0048 (cadastro segregado A3 — uso de e-CNPJ p/ NF, não e-CPF)
- ADR-0049 (CT-e/NFC-e/devolução)
- BaaS escolhido (PlugNotas ou Focus — abstraído)
