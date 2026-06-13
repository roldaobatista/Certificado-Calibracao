---
owner: roldao
revisado-em: 2026-06-12
status: stable
diataxis: reference
audiencia: agente+roldao
relacionados:
  - REGRAS-INEGOCIAVEIS.md
  - docs/faseamento-modulos.md
---

# Invariantes de Módulos Futuros

> **Origem:** movidas do mestre `REGRAS-INEGOCIAVEIS.md` em 2026-06-12 pela
> auditoria de cerimônia R14 (aprovação Roldão). IDs, texto e base normativa
> estão **integralmente preservados** — só mudaram de endereço.
>
> **Ciclo de vida:** quando um módulo entrar em construção (fase P1 spec), a
> família correspondente volta ao mestre OU é fragmentada na fatia do módulo.
> Decisões continuam válidas — só o endereço mudou.
>
> **Critério de retorno:** grep de qualquer ID desta família em `src/`, `tests/`
> ou `.claude/hooks/` retorna ocorrência → família volta ao mestre antes do P2
> plan daquele módulo.

---

## INV-ORC-* — Invariantes de Orçamentos (Wave A `orcamentos`)

> Criadas em 2026-05-23 (Onda 9 — auditoria Wave A operacional). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-ORC-EXP-001 | **Job de expiração de orçamento é idempotente por `orcamento_id` e respeita timezone do tenant.** Re-execução do job na mesma data não duplica evento `Orcamento.Expirado` nem altera estado se já expirado. Timezone do tenant (configurável; default `America/Sao_Paulo`) define corte D+1 da `validade_ate`. | Auditor `auditor-idempotencia` detecta job `expirar_orcamentos` sem `SELECT ... FOR UPDATE` em `orcamento_id` ou sem comparação contra timezone tenant. | Cliente vê orçamento "expirado" em data errada (timezone server vs tenant); evento duplicado fura régua de cobrança. |

---

## INV-CHM-* — Invariantes de Chamados (Wave A/B `chamados`)

> Criadas em 2026-05-23 (Onda 9). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-CHM-RAST-001 | **Conversão chamado→orçamento→OS preserva rastreabilidade tripla.** Quando chamado vira orçamento (Wave B), `Orcamento.chamado_origem_id` é NOT NULL. Quando orçamento aprovado gera OS, `OS.orcamento_origem_id` é NOT NULL. Se chamado virou OS direta (sem orçamento), `OS.chamado_origem_id` é NOT NULL e `OS.orcamento_origem_id IS NULL`. Audit registra cada salto. | Migration linter exige as 3 FKs nos modelos. Teste E2E reproduz os 2 caminhos (chamado→orç→OS e chamado→OS) e valida campos. | Cliente reclama de cobrança duplicada e não conseguimos rastrear "qual chamado virou qual OS" → falha de atendimento + dúvida de cobrança. |

---

## INV-AG-* — Invariantes de Agenda (Wave A `agenda`)

> Criadas em 2026-05-23 (Onda 9). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-AG-ADR0023-001 | **`EventoAgenda` com `tipo=os` exige `atividade_id NOT NULL` (FK para `AtividadeDaOS`).** Campo `os_id` é derivado (`= atividade.os_id`). Migration garante. Detecção de conflito (overlap por técnico) continua valendo. | Migration linter verifica que `evento_agenda.atividade_id` é NOT NULL quando `tipo=os` (CHECK constraint). Teste E2E cria 2 atividades da mesma OS em técnicos diferentes em janelas diferentes → sucesso. | Caso combinado (calibração em lab + manutenção em campo, mesma OS) impossível de agendar; ADR-0023 quebrada. |

---

## INV-APP-* — Invariantes do App Técnico de Campo (Wave A `app-tecnico`)

> Criadas em 2026-05-23 (Onda 9). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-APP-ADR0023-001 | **`ServicoExecutado`, `ConsumoPeca`, `Foto`, `Checklist`, `AssinaturaAceite` exigem `atividade_id NOT NULL`** (FK para `AtividadeDaOS`). NÃO podem ser filhos diretos de `OS`. Checklist é por atividade — tipo distinto = checklist distinto. | Migration linter rejeita FK direta `os_id` nessas 5 entidades sem `atividade_id` paralelo. Teste E2E reproduz: tentar criar `ServicoExecutado` com `os_id` mas sem `atividade_id` → rejeitado. | App técnico mostra OS como bloco único; manutenção e calibração compartilham checklist errado; ADR-0023 quebrada na execução de campo. |
| INV-APP-CANON-001 | **`AssinaturaAceite.corpo_canonico_hash` é calculado via `canonicalizar_texto_termo` (ADR-0029).** Função SHA-256 sobre bytes UTF-8 sem BOM + LF + NFC + sem trailing whitespace + marcadores `<<<CORPO INICIO/FIM>>>`. Imutável após `INSERT`. | Hook `aceite-canonico-check.sh` valida que código de coleta de aceite chama `canonicalizar_texto_termo` antes de SHA-256. Teste E2E reproduz aceite em Linux e Windows → mesmo hash. | Tribunal invalida aceite eletrônico por hash divergente (TJSP série 1037xxx-xx); prova Lei 14.063/2020 art. 4º cai. |
| INV-APP-SESS-001 | **Sessão offline do app expira 7 dias sem sync; biometria é default; PIN é fallback; wipe remoto via comando push.** Login no app exige biometria (face/digital) com PIN de 6 dígitos como fallback. Após 7 dias sem sincronização com servidor, sessão local é forçada a re-autenticação. Comando `RemoteWipe` enviado via push limpa dados locais. | Auditor `auditor-seguranca` detecta no app config de sessão sem expiração ≤7d ou sem handler `RemoteWipe`. Teste E2E reproduz expiração + wipe. | Técnico furtado mantém acesso aos dados de clientes por semanas → vazamento LGPD; falta de biometria padrão = senha vazada = acesso pleno. |
| INV-APP-SYNC-001 | **Sync parcial: técnico baixa apenas OS atribuídas + últimos 6 meses de histórico do cliente alvo. Quota local 2GB; LRU eviction.** Servidor não envia base completa do tenant. Quando armazenamento local passa de 2GB, dados mais antigos não-pendentes são removidos via LRU. Operações pendentes nunca são removidas. | Auditor `auditor-seguranca` detecta endpoint de sync que aceita request sem filtro `tecnico_id` + `janela_meses`. Teste E2E reproduz quota cheia → LRU dispara → pendente preservado. | App baixa 50GB de dados de outros técnicos do tenant → LGPD minimização violada + bateria/storage do dispositivo estourado. |

---

## INV-FIN-* — Invariantes de Financeiro operacional (Wave A `contas-receber` / `gateway`)

> Criadas em 2026-05-23 (Onda 9). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-FIN-REATIV-001 | **`ContasReceber.Pago` da última fatura vencida do cliente bloqueado por inadimplência publica `Cliente.Desbloqueado(motivo=pagamento_quitou)` em ≤5min.** Consumer em `clientes/` reativa cliente, libera novo orçamento + OS. Caso parcial: bloqueio mantém até último título vencido ser quitado. | Auditor `auditor-observabilidade` valida que consumer de `ContasReceber.Pago` existe e publica `Cliente.Desbloqueado` quando última fatura vencida fecha. Teste E2E reproduz GATE-CLI-6. | Cliente paga e continua bloqueado; vendedor não consegue abrir orçamento; churn por falha operacional. Reabre GATE-CLI-6. |
| INV-FIN-INAD-001 | **Inadimplência do CLIENTE do tenant ≠ inadimplência do TENANT.** Bloqueio de cliente do tenant por atraso (default 90d, configurável por tenant) usa `Cliente.bloqueado=true` (INV-INT-010). Bloqueio do tenant no SaaS Aferê (`billing-saas` ADR-0015) usa `BillingSaas.TenantSuspenso` (INV-INT-009). **Nenhuma policy/code cruza os dois**: cliente bloqueado não afeta plano do tenant; tenant suspenso não bloqueia clientes do tenant. | Hook `policy-tenant-vs-cliente.sh` (a criar) verifica que `Cliente.bloqueado=true` só é setado por job `job_inadimplencia_alertas` (INV-INT-010) e que `TenantSuspenso` só é setado por `billing-saas`. Auditor `auditor-conformidade-lgpd` revisa cross-referências. | Cliente do tenant paga em dia mas é bloqueado porque o tenant está em atraso no SaaS Aferê (e vice-versa) → reclamação injusta + churn. |
| INV-FIN-GW-001 | **Webhook gateway de pagamento exige HMAC válido + idempotência por `gateway_event_id`** (ADR-0050). Replay do mesmo `gateway_event_id` retorna 200 OK sem reprocessar. Assinatura inválida retorna 401. | Auditor `auditor-idempotencia` + `auditor-seguranca` detectam endpoint de webhook sem `verify_hmac()` ou sem `INSERT ... ON CONFLICT DO NOTHING` em `gateway_events`. Teste E2E reproduz replay + assinatura forjada. | Cobrança duplicada (replay); fraude por webhook forjado; SEC-PCI-001 violada. |
| INV-FIN-GW-002 | **`Titulo.meio=pix_recorrente` exige `convenio_pix_id` NOT NULL** (BCB Resolução 1.071/2024). Adapter `PaymentGatewayProvider` valida criação do convênio antes de gerar cobranças recorrentes. | Migration linter exige CHECK constraint. Teste E2E reproduz criação de cobrança PIX recorrente sem convênio → rejeitado. | Cobrança PIX recorrente cai por falta de convênio BCB; cliente vê erro genérico do gateway; receita interrompida. |

---

## INV-SAGA-* — Invariantes de Saga cross-módulo (ADR-0034)

> Criadas em 2026-05-22 (Onda 1 saneamento projeto-inteiro). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12. **Ressalva:** `src/infrastructure/ordens_servico/sagas/sync_mobile.py` contém o arquivo de saga mas não cita `INV-SAGA-*` — família pode retornar quando saga cross-módulo real for construída.

| ID | Regra | Base normativa | Hook que valida | Escopo | Consequência de violar |
|---|---|---|---|---|---|
| INV-SAGA-001 | **Toda saga cross-módulo (≥3 módulos, ≥3 passos, compensação possível) tem tabela persistente `<dominio>_saga_<nome>` com state machine declarada em `docs/comum/sagas-cross-modulo.md`.** Coreografia pura sem orquestrador exige ADR-irmã. | ADR-0034 + ADR-0015 | `auditor-bus-integrity` §5+§6 | Absoluta | Saga muda quebra fluxo cross-módulo sem ponto único de inspeção. |
| INV-SAGA-002 | **Compensação é publicação de evento, nunca DELETE/UPDATE retroativo no passo anterior.** Preserva WORM regulatório (INV-CER-WORM-001, INV-SOFT-002). | ADR-0034 + INV-SOFT-002 + ISO 17025 cl. 8.4 | `audit-immutability-check.sh` + auditor-bus-integrity | Absoluta | Histórico regulatório apagado por compensação = fraude. |
| INV-SAGA-003 | **Compensação fora da janela (>24h) em fluxo regulatório (NF-e cancelada, cert revogado) PROIBIDA sem assinatura A3 + audit imutável + justificativa ≥30 chars.** | ADR-0034 + INV-017 + Receita Federal + ISO 17025 cl. 7.10 | Hook em endpoint compensação valida janela + A3 + audit | Absoluta | Compensação retroativa silenciosa = fraude regulatória + LGPD inauditável. |
| INV-SAGA-004 | **Saga sem terminal (`concluida`/`falhou`/`cancelada`) em 24h dispara alerta P1** (saga zumbi). | ADR-0034 | Job monitor sagas com `concluida_em IS NULL AND falhou_em IS NULL AND atualizada_em < now() - 24h` | Absoluta | Recursos travados; cliente não recebe efeito esperado. |

---

## INV-LGPD-KMS-* — Invariantes do inventário de chaves KMS

> Criadas em 2026-05-22 (Onda 1 saneamento projeto-inteiro). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-LGPD-KMS-001 | **Toda chave KMS criada para Aferê é registrada no inventário (`docs/seguranca/chaves-kms-inventario.md`) em PR.** | Hook `kms-inventario-check.sh` (Onda 4) bloqueia referência a `KMS_*` sem entrada correspondente | Crypto-shredding LGPD Zona A impossível (chave fantasma); auditor não vê propósito. |
| INV-LGPD-KMS-002 | **Rotação anual de keys versionadas é responsabilidade do job `job_kms_rotacao`** (tech-lead); falha dispara alerta P1. | Job + métrica | Rotação esquecida → comprometimento de key invalida estrutura. |
| INV-LGPD-KMS-003 | **Eliminação de tenant em Zona A executa crypto-shredding de todas as keys tenant-scoped listadas** + audit imutável + janela 7 dias de reversão (AWS KMS pending window). | Procedimento manual com aprovação Roldão | LGPD direito ao esquecimento incompleto; dados ainda decifráveis. |

---

## INV-LGPD-NOTIF-* — Invariantes de Notificação LGPD/Regulatória

> Criadas em 2026-05-22 (Onda 1 saneamento + catálogo v11). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Base normativa | Hook que valida | Escopo | Consequência de violar |
|---|---|---|---|---|---|
| INV-LGPD-NOTIF-001 | **`LGPD.IncidenteDetectado` publicado em ≤24h após detecção** (folga sobre prazo legal 3 dias úteis ANPD — Res. CD/ANPD 15/2024 art. 6º/9º/10). Consumers obrigatórios: encarregado (DPO), RT do tenant, comunicacao-omnichannel. | Res. CD/ANPD 15/2024 + INV-005 | Job monitor diff `incidente_marcado_em` vs `event_published_em` + alerta P0 se >24h | Absoluta | Multa ANPD (R-014); ATPP prazo dobrado mantido. |
| INV-LGPD-NOTIF-002 | **`Qualidade.NotificacaoCGCREDisparada` registrada em audit imutável + cópia B2 WORM em ≤5min após publicação.** Tipo: `cgcre | iaf | inmetro`. | NIT-DICLA-021 + ISO 17025 cl. 8.7 | Job monitor + audit | Absoluta em A; n/a em B/C/D | Auditor CGCRE não vê rastro de NC bloqueante → suspende acreditação. |

---

## INV-DOM-GLOSS-* — Invariantes de Glossário PT-BR Canônico (ADR-0037)

> Criadas em 2026-05-22 (Onda 1). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12. **Nota:** estas invariantes são transversais por natureza, mas ainda não têm hook mecânico (`glossario-dominio-check.sh` planejado) — retornam ao mestre quando o hook for criado.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-DOM-GLOSS-001 | **Toda classe de domínio em `src/domain/**/models.py` ou `src/domain/**/value_objects.py` cujo nome conceitual esteja no glossário deve usar o nome PT-BR canônico** (`Cliente`, não `Customer`). Adapter pode traduzir na borda EN. | Hook `glossario-dominio-check.sh` (Onda 4) | Drift conceitual; agente IA inventa nome diferente a cada Marco. |
| INV-DOM-GLOSS-002 | **Termo metrológico ISO/VIM segue VIM 4ª edição quando aplicável** (`Calibracao` não `Calibration`; PT canônico mesmo com correspondência ISO). | Hook | Drift entre PT canônico e EN adapter. |

---

## INV-BIL-* — Invariantes de Billing SaaS (Wave B `billing-saas`)

> Criadas em 2026-05-23 (Onda 10 ACL). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Veredito | Hook | Consequência |
|---|---|---|---|---|
| INV-BIL-PIX-001 | **Cobrança PIX recorrente exige `mandato_id` BCB 1.071/2024 válido, não revogado, não expirado, com `fatura.valor ≤ mandato.valor_teto`.** Validação **antes** de chamar `PaymentGatewayProvider.criar_cobranca(metodo=pix_recorrente)`. | ALTO | Hook valida na função de cobrança recorrente; bloqueia release que dispare PIX sem mandato | TED não-autorizado = passivo regulatório BCB + LGPD art. 7º |

---

## INV-BPM-* — Invariantes de Automações & BPM (Wave B/C `automacoes-bpm`)

> Criadas em 2026-05-23 (Onda 10 ACL). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Veredito | Hook | Consequência |
|---|---|---|---|---|
| INV-BPM-MIG-001 | **Migração entre versões de workflow é explícita (operador escolhe quais instâncias migrar); novas instâncias usam `v_atual`; antigas em `v_n` continuam até `CONCLUIDA` ou migração explícita.** Bloqueia se etapa atual não existe em `v_atual`. | ALTO | Hook valida modelo `WorkflowInstancia` tem `versao_origem` + `versao_atual`; trigger PG bloqueia UPDATE direto sem comando `migrar_instancia` | Instâncias em fluxo quebram silenciosamente — audit perdido + reclamação cliente |

---

## INV-BI-* — Invariantes de BI/Indicadores (Wave B/C `bi`)

> Criadas em 2026-05-23 (Onda 10 ACL). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Veredito | Hook | Consequência |
|---|---|---|---|---|
| INV-BI-MRR-001 | **Dashboard MRR/ARR/churn por componente alimentado por `MeterUsoEvent` + `BillingSaas.UsoMedido` + `BillingSaas.FaturaPaga` via outbox transacional desde dia 1** (sem depender de Debezium). Refresh ≤5min p95. Churn separa voluntário × involuntário (`motivo_churn`). | ALTO | Hook valida consumer da MV `mv_mrr_arr` registrado no outbox + teste regressão mede latência | Dono Aferê opera SaaS sem visibilidade de receita recorrente — decisão cega |

---

## INV-MKT-* — Invariantes de Marketplace de Extensões (V2/V3)

> Criadas em 2026-05-23 (Onda 10 ACL). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Veredito | Hook | Consequência |
|---|---|---|---|---|
| INV-MKT-SANDBOX-001 | **Extensão Python executa em sandbox: `RestrictedPython` (AST sanitizer) + subprocess (`firejail/nsjail`) + cgroups (CPU 500ms, RAM 128MB, disk 0, rede default-deny — só APIs Aferê via allowlist).** Hooks recebem `UntrustedInput[dict]`. | ALTO | Hook bloqueia release de extensão sem config de sandbox em `extension_manifest.yaml`; CI roda fuzz contra sandbox | Extensão maliciosa rouba dados de N tenants — Aferê responsável solidariamente (ADR-0019) |

---

## INV-SPED-* — Invariantes de Contabilidade Export (Wave A/B `contabilidade`)

> Criadas em 2026-05-23 (Onda 10 ACL). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Veredito | Hook | Consequência |
|---|---|---|---|---|
| INV-SPED-001 | **Toda fatura SaaS paga + NFS-e emitida + lançamento financeiro alimenta `PlanoContasMapeamento` por tenant; export SPED/Sage/Domínio não gera linha sem conta contábil mapeada.** | ALTO | Hook valida ao gerar export: linhas sem mapeamento → falha + lista lançamentos faltando; bloqueia release que adicione tipo de lançamento sem entry no mapeamento canônico | Contador externo recusa arquivo (linhas órfãs) — bloqueio comercial PME |

---

## INV-A3-* / INV-CER-LTV-* / INV-FIS-REGIME-* / INV-FIS-OCSP-* / INV-REG-* — Invariantes Regulatório Wave A (Onda 8)

> Criadas em 2026-05-23 (Onda 8 — auditor regulatório 7). Zero ocorrências de `INV-A3-`, `INV-CER-LTV-`, `INV-FIS-REGIME-`, `INV-FIS-OCSP-`, `INV-REG-` em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12. **Nota:** `INV-FIS-CR-001` tem referência em `src/infrastructure/audit/acoes_canonicas.py` (comentário) mas o módulo contas-receber não existe — fica aqui; retorna quando `contas-receber` tiver código.

| ID | Regra | Hook que valida | Consequência de violar |
|---|---|---|---|
| INV-FIS-CR-001 | **`Fiscal.NFSeEmitida` cria `ContasReceber.TituloEmitido` em ≤ 5s** (US-FIS-007). Fluxo correto: Certificado/OS concluído → emite NFS-e → cria CR. `ContasReceber.Pago` é evento POSTERIOR (pagamento da fatura), NÃO gatilho de emissão de NF. Inversão detectada e corrigida pela Onda 8 (C-REG-01). | Hook valida que consumer de `Fiscal.NFSeEmitida` cria CR; teste E2E mede latência ≤5s | Receita órfã (NF emitida sem título a receber); descontrole financeiro; auditoria contábil reprova. |
| INV-A3-RT-001 | **RT signatário só assina certificado RBC com e-CPF próprio vinculado ao `usuario_id` ativo**. Módulo `certificados` valida em cada assinatura: `cert.escopo == rt_signatario AND cert.usuario_id == request.usuario.id AND cert.status_local == vigente`. Cadastro do A3 (US-CER-DIG-002 em `certificados-digitais`) já valida `subject_cn.cpf == usuario.cpf`. | Hook semgrep em `assinar_certificado()` força chamada a verificação; teste E2E: técnico A tenta assinar com A3 do RT B → 403 | Fraude regulatória (qualquer A3 emprestado assinaria); NIT-DICLA-021 violada; R-039 reativa. ADR-0048. |
| INV-A3-OCSP-001 | **Cert revogado pela AC bloqueia assinatura/emissão com 409 + audit `A3.RevogacaoDetectada`**. Porta `CertificadoDigital.verificar_status()` consulta OCSP online (timeout 3s) + fallback CRL local (≤1h). Cert RBC: bloqueia hard se verificação indisponível (503). Cert não-RBC: permite com flag `verificacao_degraded=true`. Job diário varre todos certs ativos. | Hook semgrep em `assinar_certificado()` e `emitir_nf()` exige `verificar_status()` imediatamente antes; teste E2E revoga cert sandbox → próxima emissão bloqueia em <1h | Cert revogado emitindo certificado de calibração = certificado sem valor legal; R-018 reativa. ADR-0046. |
| INV-CER-LTV-001 | **Toda emissão de certificado de calibração** (US-CER-002 em `metrologia/certificados`) **gera PDF assinado em formato PAdES-LTV (perfil B-LTA)** com TSA-ITI como default e fallback ICP-Brasil. DSS embute cadeia + OCSP da hora + timestamp. Job anual re-timestamp pra estender validade além de expiração da TSA original. NF-e fiscal NÃO exige LTV. | Teste de validação PDF: emite cert → ferramenta PAdES valida B-LTA; mock expiração A3 → validação ainda passa via DSS | Validação retroativa do cert falha após 1ª expiração do A3 (~1-3 anos); retenção ISO 8.4 (25 anos) inviável. ADR-0047. |
| INV-FIS-REGIME-001 | **Enum `regime_tributario` é fechado**: `NORMAL`, `SIMPLES_NACIONAL`, `MEI`, `ST_INDICADOR`, `LUCRO_REAL`, `LUCRO_PRESUMIDO`. Migration linter rejeita valor fora do enum. | Validador de migration + teste unitário | Drift fiscal; combinatória aberta vira pesadelo. Onda 8 A-REG-04. |
| INV-REG-AMPLIACAO-001 | **Pedido de ampliação de escopo CGCRE** (US-LIC-010 + ADR-0014 Fluxo 7) **só pode ser submetido com pré-requisitos completos**: dossiê 7.11 + ART RT + padrões rastreáveis pra novas grandezas + procedimentos validados. Sistema valida AND publica `Licencas.AmpliacaoEscopoSubmetida`. | Teste E2E submete sem pré-requisitos → 422 | CGCRE devolve por documentação incompleta; cronograma atrasa. |
| INV-REG-NC-CGCRE-001 | **NC CGCRE com `severidade=maior AND escopo_afetado=X` bloqueia hard emissão no escopo X** durante o período de resposta (≤30 dias). Prazo vencido publica `Licencas.NCCgcrePrazoVencido` + escalation P1 + bloqueia emissão integral até resposta. US-LIC-011 + ADR-0014 Fluxo 8. | Hook em `certificados.emitir()` consulta NCs abertas com `bloqueia_escopo=true`; teste E2E | Supervisão CGCRE escalona pra suspensão; recall de certificados. |
| INV-REG-REVISAO-5A-001 | **Revisão CGCRE quinquenal** dispara alertas D-365/180/90/60/30 + checklist preparatório. US-LIC-012 + ADR-0014 Fluxo 9. | Job Celery + teste E2E mock data | Admin descobre 30 dias antes; dossiê incompleto; perda da acreditação. |
| INV-FIS-OCSP-CHAIN-001 | **Emissão de NF (US-FIS-001) verifica OCSP do A3 do tenant antes de chamar BaaS**. Se `revoked`, retorna 409 sem chamar BaaS; publica `A3.RevogacaoDetectada`. | Hook em `Fiscal.emitir()` chama `verificar_status()` antes; teste E2E | Tenant emite NF com cert revogado; SEFAZ rejeita; processo legal. |

---

## INV-WEBHOOK-001 — Invariante de Webhook Out (ADR-0054 — seção legada)

> INV-WEBHOOK-001 é a regra geral do sistema de webhook out. INV-WEBHOOK-OUT-001..005 (no mestre) são o detalhamento já implementado em F-C1. Esta regra geral fica aqui porque não há código que cite o ID `INV-WEBHOOK-001` diretamente (a implementação cita `INV-WEBHOOK-OUT-*`). Zero ocorrências em `src/`/`tests/`/`.claude/hooks/` em 2026-06-12.

| ID | Regra | Veredito | Hook | Consequência |
|---|---|---|---|---|
| INV-WEBHOOK-001 | **Toda entrega tem (a) `X-Afere-Signature: sha256=<HMAC(secret, body)>`; (b) `X-Afere-Idempotency-Key`; (c) timeout 10s; (d) retry exponencial 1m/5m/30m/2h/12h (5 tentativas); (e) dead letter após 5 falhas; (f) circuit breaker por endpoint (5 falhas em 10min abre, half-open após 30min); (g) SSRF guard (rejeita RFC 1918, 127.0.0.0/8, 169.254.0.0/16, loopback); (h) TLS obrigatório.** | ALTO | Hook valida código fora de `infrastructure/webhook_out/` que use `httpx`/`requests` apontando pra URL de tenant; bloqueia cliente HTTP em domínio | Replay attack, SSRF a metadata cloud, secret leak, DoS produtor |
