---
owner: claude-code
revisado-em: 2026-06-12
status: stable
---

# Índice de ADRs — completo

> Fonte canônica para ADRs individuais: arquivos `docs/adr/ADR-NNNN-*.md`.
> AGENTS.md §11 lista apenas as ADRs vivas (slim). Este índice contém todas.
> "Reler quando mexer em:" = área afetada.

---

## ADRs vivas (guiam código construído hoje)

| Nº | Título curto | Módulo / área | Reler quando mexer em |
|---|---|---|---|
| ADR-0002 | Multi-tenancy schema-shared + RLS v2 | infra / todo módulo | qualquer migration ou middleware de tenant |
| ADR-0006 | Feature flags por tenant | infra / F-B | `feature_flags/`, `settings` de tenant |
| ADR-0007 | Camada domínio + spec-as-source | arquitetura | qualquer módulo novo ou porta nova |
| ADR-0008 | Fiscal pluggable FiscalProvider | fiscal / NFS-e | `src/domain/fiscal/`, adapters BaaS |
| ADR-0012 | Autorização unificada AuthorizationProvider | authz | `authz/`, `ACTION_MAP`, predicates ABAC |
| ADR-0014 | Transições regulatórias ISO 17025 (6 fluxos) | regulatório | licenças, CGCRE, perfil A→B/D→A |
| ADR-0015 | Lifecycle tenant provisioning + perfil etapa 0 | tenant / onboarding | `provisionar_tenant`, suspensão, inadimplência |
| ADR-0017 | CNPJ alfanumérico IN RFB 2.229/2024 | todo módulo com CNPJ | VO CNPJ, validadores, forms |
| ADR-0021 | Anonimização vs retenção (zonas A/B/C LGPD) | LGPD / toda entidade PII | anonimizar_cliente, hash cross-módulo |
| ADR-0022 | Gestão RT v2 (competência método+faixa) | RT / calibração | `RTCompetencia`, `rt_competencia_cobre` |
| ADR-0023 | OS com Atividades (1 OS → N AtividadeDaOS) | ordens_servico | qualquer módulo que cria/lê OS |
| ADR-0024 | Regra de decisão ISO 17025 cl. 7.8.6 | calibração | `RegraDecisao`, lock pós-emissão |
| ADR-0025 | Validação software cl. 7.11 v2 (4 módulos) | metrologia | replay fixtures, `versao_motor`, marcadores OQ |
| ADR-0026 | 2ª conferência + independência RT cl. 6.2.5 | calibração | `revisao`, `conferencia`, política exceção |
| ADR-0029 | Canonicalização texto probatório | toda entidade WORM | `<<<CORPO INICIO/FIM>>>`, UTF-8 NFC LF |
| ADR-0030 | Vigência temporal canônica (JanelaVigencia) | toda entidade temporal | `vigencia_inicio/fim`, `revogado_em` |
| ADR-0031 | Soft-delete 3 padrões | toda entidade | estado-máquina / `revogado_em` / `deletado_em` |
| ADR-0032 | FK cross-módulo + ReferenciaPIIAnonimizavel | LGPD / cross-módulo | hash_original, evento `Cliente.Anonimizado` |
| ADR-0033 | Bus idempotência consumer | filas / procrastinate | `consumer_idempotencia`, `dead_letter_events` |
| ADR-0036 | Replay determinismo schema evento `_schema_version` | bus | eventos versionados, janela 90d |
| ADR-0040 | Padrão metrológico entidade separada | metrologia/padroes | módulo `metrologia/padroes` distinto de `equipamentos` |
| ADR-0043 | Calibração faturamento + inadimplência grace perfil-aware | billing / certificados | grace A D+45 / D D+7 |
| ADR-0044 | Exportação regulatória ANVISA/INMETRO + predicate perfil A | certificados | exportação regulatória, `tenant_perfil_e({A})` |
| ADR-0045 | Certificado recall + errata perfil-aware | certificados | recall CGCRE, errata D simples |
| ADR-0054 | Webhook out provider + HMAC + SSRF guard | webhooks / F-C1 | `OutboundWebhookProvider`, hooks SSRF |
| ADR-0056 | Numeração OS sequence global + buracos aceitos | ordens_servico | `numero_os`, sequence, UNIQUE |
| ADR-0064 | Rotação HMAC anual + KMS 25a + formato `vNN$...` | criptografia / WORM | `hmac_versionado`, rotação chave anual |
| ADR-0065 | Concorrência calibração UNIQUE + CAS + advisory lock | calibração | `leitura`, `Calibracao.revision`, hash-chain |
| ADR-0067 | Perfil regulatório tenant 4 perfis A/B/C/D | tenant / todo módulo | `tenant_perfil_e`, `TenantPerfilHistorico`, WORM |
| ADR-0070 | Carta Shewhart híbrida read-model + WORM congelado | metrologia/padroes | `AnaliseCartaControle`, LC/UCL/LCL |
| ADR-0071 | 2ª implementação cl. 7.11 = mesmo mensurando independente | metrologia/padroes | anti-bug software, Welch-Satterthwaite |
| ADR-0072 | Path infra metrologia aninhado `infrastructure/metrologia/` | infra metrologia | qualquer módulo novo sob `metrologia/` |
| ADR-0073 | Validação metrológica no use case, não no DRF | metrologia / use cases | `cmc_cobre`, `procedimento_vigente_para`, 412 |
| ADR-0074 | Cobertura RBC tridimensional faixa+U≥CMC+menor-CMC | escopos-cmc | `avaliar_u_cmc`, ILAC-P14 §5.5 |
| ADR-0075 | Capacidade interna B/C/D ≠ CMC acreditada A | escopos-cmc | rótulo/badge, cl. 8.1.3 |
| ADR-0076 | Faixa DECLARADA na config vs pontos medidos na emissão | escopos-cmc / certificados | `faixa_calibrada_declarada`, CGCRE extrapolar |
| ADR-0077 | Orçamento incerteza POR PONTO retrofit M4 | calibração / certificados | `OrcamentoPorPonto`, `cadeia_pontos_hash` |
| ADR-0078 | Tabela certificados achatada + lógica aninhada | certificados | migration `certificados`, INV-025 |
| ADR-0079 | Licenca fonte rica + cache Tenant via aplicar_evento_cgcre | licencas / tenant | `aplicar_evento_cgcre`, `acreditacao_vigencia_fim` |
| ADR-0080 | Numeração SerieDocumento 2 regimes (gap-less vs buracos) | configuracoes-sistema | `SerieDocumento`, motor M8, reset anual |
| ADR-0081 | Duas fontes de preço lista×venda fail-closed | produtos-pecas-servicos | `LinhaTabelaPreco`, `PrecoResolvido`, 422 |
| ADR-0082 | OS multi-equipamento (equipamento por atividade) | ordens_servico | `AtividadeDaOS.equipamento_id`, `ItemComercialOS`, migrations 0018-0020, COALESCE trigger |

---

## ADRs frias (Wave B/C/V2, superadas, exauridas ou reservadas)

> Não guiam código hoje. Ler se a área específica for construída.

| Nº | Título curto | Quando ler |
|---|---|---|
| ADR-0000 | Uso de IA no projeto | contexto histórico |
| ADR-0001 | Stack Django+Flutter+PG — 3 portões | Portão 2/3 da ADR-0001 |
| ADR-0003 | Mobile Flutter offline-first técnico campo | app-tecnico Wave A |
| ADR-0004 | Sync mobile offline-first — refined-by 0027 | app-tecnico Wave A |
| ADR-0005 | Engine de automações BPM | Wave B automacoes-bpm |
| ADR-0009 | A3 assina client-side via Lacuna | Wave A certificados digitais |
| ADR-0010 | Estratégia tela HTMX + 5 SPAs | Wave A UI |
| ADR-0011 | Banco analítico BI separado | Wave B BI |
| ADR-0013 | Pricing composicional billing-saas | Wave B billing-saas full |
| ADR-0016 | Operação consistente desligamento síncrono | Wave A operação |
| ADR-0018 | Scanner QR em PWA BarcodeDetector | Wave A US-EQP-003 |
| ADR-0019 | RC + segurabilidade código IA — superseded-by 0028 | contexto histórico |
| ADR-0020 | REGRAS > orçamento; CODEOWNERS expandido | contexto histórico |
| ADR-0027 | Sync mobile merge por atividade (LWW) | app-tecnico Wave A |
| ADR-0028 | Mapa coberturas seguro Wave A (5 modalidades) | 1º tenant externo pago |
| ADR-0034 | Saga compensação cross-módulo | Wave A M3+M4 |
| ADR-0035 | Tenant suspenso modo read-only perfil-aware | Wave A billing-saas suspensão |
| ADR-0037 | Glossário PT-EN canônico | contexto histórico / transversal |
| ADR-0038 | INV-AUTH lockout+senha+sessão | Wave A F-B retrofit |
| ADR-0039 | Cliente exterior + MEI TipoPessoa | Wave A retrofit Marco 1 |
| ADR-0041 | OS concorrência atividades | Wave A Marco 3 |
| ADR-0042 | OS cancelamento parcial × faturamento | Wave A Marco 3 |
| ADR-0046 | OCSP/CRL revogação online 3s fallback | Wave A A3 digital |
| ADR-0047 | Carimbo TSA-ITI PAdES-LTV 25a | Wave A certificados digitais |
| ADR-0048 | A3 e-CPF RT 3 cadastros | Wave A A3 digital |
| ADR-0049 | Fiscal CT-e+NFC-e+devolução non-goal Wave A | Wave A fiscal |
| ADR-0050 | Gateway pagamento PaymentGatewayProvider | Wave A financeiro |
| ADR-0051 | Propagação ADR-0023 em módulos Wave A | Wave A 5 módulos operacionais |
| ADR-0052 | PIX recorrente BCB 1.071/2024 | Wave A billing-saas |
| ADR-0053 | Export SPED ECF+EFD Contribuições | Wave A |
| ADR-0055 | Marketplace sandbox revenue share | V2/V3 marketplace |
| ADR-0057 | Acessibilidade WCAG 2.1 AA | Wave A toda tela nova |
| ADR-0058 | ProductAnalyticsProvider 19ª porta | Wave A analytics |
| ADR-0059 | LLMProvider canônica + INV-LLM-001..010 | reservada — antes 1ª feature LLM Wave B |
| ADR-0060 | EmailTemplateProvider + dedup hash | reservada — antes comunicacao-omnichannel |
| ADR-0061 | Canal titular + DPO LGPD art. 41 | reservada — antes 1º dogfooding real |
| ADR-0062 | Devcontainer canônico sandbox | F-C2 network allowlist |
| ADR-0063 | RT competência diferida Marco 4 fail-open | contexto histórico (porta já real) |
| ADR-0066 | Predicates cmc_cobre+procedimento fail-open | contexto histórico (fail-open resolvido) |
| ADR-0068 | Sucessão RT NIT-DICLA-016 | Wave A agenda+app-tecnico+certificados |
| ADR-0069 | Bypass competência cl. 6.2 4 condições | Wave A rh-frota-qualidade/treinamentos |
