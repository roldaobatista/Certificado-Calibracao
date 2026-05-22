---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
relacionados:
  - docs/conformidade/comum/lgpd-rat.md
  - docs/conformidade/comum/retencao-matriz.md
  - REGRAS-INEGOCIAVEIS.md (RAT-07, INV-OS-GEO-001)
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/adr/0023-os-com-atividades.md
---

# RIPD — Geolocalização em OS de campo (RAT-07)

> **Relatório de Impacto à Proteção de Dados Pessoais** — LGPD art. 38 + Res. CD/ANPD 4/2023.
>
> **Origem:** TEMA-D.1 da auditoria 10 lentes 2026-05-23. PRD da OS cita "Geolocalização opt-in com RIPD (LGPD RAT-07)" mas RIPD não existia — bloqueio crítico pra arrancar Marco 3.
>
> **Aprovação requerida:** advogado-saas-regulado (parecer estratégico minutado por agente IA, ratificação por advogado humano com OAB antes do 1º tenant externo pago).

---

## 1. Identificação do tratamento

- **Controlador:** o tenant (laboratório/empresa de assistência técnica) — Aferê opera como operador (LGPD art. 5º VII).
- **Operador:** Aferê (vendor SaaS) — sob ADR-0019 e DPA padrão.
- **Encarregado (DPO):** publicado pelo tenant; Aferê tem DPO próprio.
- **Finalidade:** capturar lat/long no início e fim de cada `AtividadeDaOS` executada em campo (P-OP-01 técnico vai ao cliente) para (a) auditoria operacional (provar que técnico esteve no endereço declarado), (b) cálculo de tempo de deslocamento (jornada trabalhista — Lei 13.103 + CLT art. 235-C), (c) rastreabilidade da execução (ISO 17025 cl. 7.5 — registros técnicos).

## 2. Categorias de dado pessoal tratadas

| Categoria | Titular | Origem | Sensibilidade |
|---|---|---|---|
| Coordenada lat/long no início da atividade | Técnico de campo (P-OP-01) | App mobile (sensor GPS do device) | **Indireta** — pode revelar endereço de saúde/residência se atividade for em residência ou clínica |
| Coordenada lat/long no fim da atividade | Técnico de campo | App mobile | Mesma de cima |
| Coordenada do endereço do cliente final (P-OP-05) | Cliente final (quando PF) | Cadastro do cliente no tenant | **Direta** quando residencial; **indireta** quando comercial |
| Precisão em metros (`precisao_m`) | — | Sensor | Não é PII isoladamente |
| Timestamp de captura | Técnico | App mobile | Não é PII isoladamente |

**NÃO se aplica a OS de bancada** (instrumento entra no laboratório). RIPD vale para atividade com flag `requer_geo: true` no tipo (calibração in-loco, manutenção corretiva externa, instalação, verificação INMETRO externa, vistoria).

## 3. Base legal LGPD

| Titular | Base legal primária | Base legal secundária | Justificativa |
|---|---|---|---|
| Técnico (colaborador do tenant) | **art. 7º IX — legítimo interesse** (auditoria operacional do empregador) | art. 7º II — obrigação legal (jornada Lei 13.103) | Empregador pode rastrear jornada do empregado em horário de trabalho dentro do interesse legítimo de produtividade + obrigação trabalhista; **opt-in NÃO é exigido em si**, mas Aferê adiciona opt-in técnico no app pra capturar consentimento explícito (princípio da transparência LGPD art. 6º VI) |
| Cliente final | **art. 7º V — execução contrato** (instalação/calibração no endereço dele) | art. 7º IX — legítimo interesse (auditoria) | Cliente forneceu endereço ao contratar; geo do técnico no endereço dele é meio de cumprimento contratual |

## 4. Princípios LGPD aplicados (art. 6º)

| Princípio | Aplicação |
|---|---|
| **I — finalidade** | Limitada a auditoria operacional + jornada trabalhista + rastreabilidade ISO 17025. Proibido uso secundário (marketing, segmentação). |
| **II — adequação** | Coordenada captura local + tempo da atividade; nada além. |
| **III — necessidade** | INV-OS-GEO-001 limita precisão: em payload de evento publicado fora do bounded-context, precisão é arredondada (município/bairro). Coordenada exata só em `os_evento` interno. |
| **IV — livre acesso** | Técnico pode ver suas geos no app (timeline própria). Cliente pode pedir geos das atividades executadas em endereço dele. |
| **V — qualidade** | Sensor de device do técnico (Android/iOS) — precisão típica 5-30m em campo aberto; degradada em ambiente fechado. Aceita imprecisão como atributo. |
| **VI — transparência** | App mobile mostra **toast/popup** na 1ª inicialização: "Vamos capturar a localização do início e fim de cada atividade. Isso ajuda no controle de jornada e na auditoria. Toque OK pra continuar." + link pra política privacy. |
| **VII — segurança** | Geolocalização criptografada em trânsito (TLS) + em repouso (KMS tenant-key). Acesso log-ado (INV-013 AcessoDadosCliente). |
| **VIII — prevenção** | Backup com chave KMS por tenant → crypto-shredding ao fim da retenção. |
| **IX — não-discriminação** | Geo não pode ser base de decisão automatizada que afete o técnico (ex: bloquear pagamento por estar fora do endereço). LGPD art. 20 + direito à revisão humana. |
| **X — responsabilização** | Aferê + tenant ambos respondem (controladoria conjunta art. 39 LGPD). DPA padrão detalha responsabilidades. |

## 5. Avaliação de risco

| Risco | Probabilidade | Impacto | Severidade | Mitigação |
|---|---|---|---|---|
| **Vazamento de endereço residencial do cliente PF** (via foto + EXIF + geo) | Baixa | Alto (LGPD art. 5º X CF — privacidade do lar) | ALTO | EXIF strip on-upload (US-CER-007 atualizada — TEMA-D.7) + precisão limitada em payload publicado (INV-OS-GEO-001) |
| **Stalking de técnico via histórico de jornada vazado** | Baixa | Alto (RAT-13 trabalhista) | ALTO | Acesso a histórico só com `AcessoDadosCliente` log-ado + autorização `os.geo.ler_historico_tecnico` |
| **Decisão automatizada discriminatória** (técnico penalizado por estar fora) | Média | Médio | MÉDIO | Proibido decisão automatizada baseada em geo isolada (LGPD art. 20); revisão humana obrigatória |
| **Geo capturada sem app permissão** (bug) | Baixa | Alto | MÉDIO | OS mobile **NÃO** persiste geo se permission denied (modo offline-safe); evento publica sem `geo`, não com lat=null |
| **Cliente final PJ descobre geo de outro cliente** (cross-tenant) | Muito baixa | Crítico | CRÍTICO | RLS PostgreSQL + INV-TENANT-001; teste E2E cross-tenant |

## 6. Medidas de mitigação obrigatórias (Wave A)

1. **Opt-in técnico no app** com toast versionado (`opt_in_geo_versao: v1.0`) — registro do consentimento em `Colaborador.opt_in_geo_em` (timestamp) + `opt_in_versao`.
2. **Opt-out a qualquer momento** — técnico desativa permission no device; evento subsequente publica sem `geo`. Não retroage.
3. **EXIF strip obrigatório** em todas as fotos do app (já cravado para equipamentos T-EQP-047; estender a OS — TEMA-D.7).
4. **Precisão limitada em payload publicado** — INV-OS-GEO-001 (município/bairro fora do bounded-context).
5. **Acesso log-ado** — toda leitura de geo histórica grava `AcessoDadosCliente` antes (INV-013).
6. **Retenção 5 anos** — RAT-07 + matriz retenção; crypto-shredding ao fim.
7. **Cliente final notificado no portal** — quando OS de campo executada no endereço dele, portal mostra "técnico esteve aqui em DD/MM HH:MM" (transparência LGPD art. 6º VI).
8. **DPA padrão tenant↔Aferê** — cláusula geolocalização declarada (parágrafo dedicado).

## 7. Direitos do titular (LGPD art. 18)

| Direito | Aplicação |
|---|---|
| **I — confirmação** | Sim — técnico/cliente consultam timeline via portal/app |
| **II — acesso** | Sim — exportação em CSV das geos do titular |
| **III — correção** | Não aplicável (sensor capturou — fato técnico) |
| **IV — anonimização/bloqueio** | Bloqueio sob demanda durante investigação trabalhista/civil |
| **V — portabilidade** | CSV/JSON |
| **VI — eliminação** | Após retenção mínima (5 anos) — crypto-shredding automático |
| **VII — informação sobre uso compartilhado** | Aferê é operador, tenant é controlador — DPA expõe |
| **VIII — informação para não-fornecimento** | Técnico opt-out → não captura, atividade prossegue |
| **IX — revogação consentimento** | Toggle no app — retroativo a partir do toggle (não retroage no histórico) |

## 8. Decisão de risco residual

**Aprovado para Marco 3 mediante:**

- Implementação das 8 medidas de mitigação Wave A (Marco 3 / 4 codifica).
- Validação por advogado-saas-regulado humano antes do 1º tenant externo pago.
- Atualização do RAT-07 em `lgpd-rat.md` consolidando este RIPD.
- Hook `ripd-required-for-pii.sh` validando que módulo coleta geo só após RIPD aprovada (Wave A).

**Risco residual: BAIXO** se as 8 medidas forem aplicadas; MÉDIO/ALTO se faltar alguma.

## 9. Revisão periódica

- Toda mudança no fluxo de geo (novo tipo de atividade, mudança em payload) exige re-aprovação do RIPD por advogado.
- Anual: revisar com base em incidentes + auditoria interna.
- Próxima revisão programada: 2027-05-23.
