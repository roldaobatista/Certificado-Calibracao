---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
tipo: consolidado-auditoria-10-lentes
---

# CONSOLIDADO — Auditoria 10 lentes do Marco 1 (`clientes`)

> Disparada em 2026-05-18 antes de replicar o padrão no Marco 2 (`equipamentos`). Motivo: Roldão levantou que copiar o Marco 1 cego replicaria eventual padrão ruim. **A preocupação se confirmou.**

## Veredito por lente

| # | Lente | Auditor | Veredito |
|---|---|---|---|
| 01 | Arquitetura / DDD | tech-lead | **DÉBITO ESTRUTURAL** |
| 02 | Segurança / multi-tenant | auditor-seguranca | SÓLIDO COM RESSALVAS |
| 03 | Qualidade de testes | auditor-qualidade | SÓLIDO COM RESSALVAS |
| 04 | Produto / AC | auditor-produto | ADERENTE COM RESSALVAS |
| 05 | LGPD / jurídico | advogado | CONFORME COM RESSALVAS |
| 06 | ISO 17025 | consultor-rbc | SUSTENTA COM RESSALVAS |
| 07 | Segurabilidade | corretora | SEGURÁVEL COM RESSALVAS |
| 08 | Drift doc↔código | auditor-drift | **DRIFT GRAVE** |
| 09 | Performance / banco | DBA | **DÉBITO DE PERFORMANCE** |
| 10 | Manutenibilidade | clean-code | MANUTENÍVEL COM RESSALVAS |

Nenhuma lente reprovou de forma absoluta — a base multi-tenant/RLS/audit/VOs é genuinamente forte. Mas **3 vereditos negativos** + convergência de múltiplos auditores nos mesmos bugs = copiar cego é inaceitável.

## Achados convergentes (≥2 lentes apontaram o mesmo — alta confiança)

| Achado | Lentes | Gravidade |
|---|---|---|
| Advisory lock liberado antes do trabalho real (importação sem proteção de concorrência; declarado "resolvido" sem estar) | 01 D-01 · 02 SEG-D2 · 09 P1 | **CRÍTICO** |
| Hash chain de auditoria não é cross-tenant-safe (pilar regulatório frágil por design) | 02 SEG-D1 · 07 R-CLI-02 | **CRÍTICO/sistêmico** |
| Domínio anêmico + regra LGPD copiada em 3 lugares (ADR-0007 aceita mas não cumprida) | 01 D-02/03/04 · 10 D3/D4 | **ALTO estrutural** |
| Mesclagem sem âncora de identidade canônica (certificado órfão; contamina calibração) | 06 D-01 · 08 (matriz promete o que código não tem) | **CRÍTICO regulatório** |
| Salt da importação derivável publicamente (reabre o FAIL crítico de PII já "resolvido") | 05 D1 · 07 R-CLI-05 | **ALTO** |
| God-class views.py + envelope de auditoria copiado 6x | 10 D1/D2 · 01 D-05 | **ALTO** |
| Suite não roda verde no fluxo padrão + números reportados em drift | 03 Q1/Q2 · 08 D5/D6 | **ALTO processo** |
| Controles ADR-0019 (suite anti-regressão INV + hook equipamento-imutabilidade) documentados mas inexistentes | 07 R-CLI-01/03 | **ALTO segurabilidade** |
| modelo-de-dominio.md descreve schema fantasma vs código real | 08 D1/D2 | **GRAVE drift** |
| Bug anti-injection CSV: célula com espaços ("  =cmd") ainda vira fórmula no Excel | 10 D6 | **ALTO segurança** |

## Plano de saneamento — Onda BLOQUEANTE (antes de codar `equipamentos`)

| ID | Frente | Origem | Conserto |
|---|---|---|---|
| SANEA-01 | Advisory lock dentro da transação no bulk_upsert | 01 D-01 / 02 SEG-D2 / 09 P1 | Indentar bloco 217-354 pra dentro do atomic que adquire o lock + drill 2 importações concorrentes mesmo tenant |
| SANEA-02 | Salt da importação com segredo server-side | 05 D1 / 07 R-CLI-05 | HMAC com chave KMS/SECRET_KEY, não sha256(tenant_id); remover tenant_id=None dos hashers |
| SANEA-03 | Bug anti-injection CSV com espaços | 10 D6 | Retornar "'"+sem_ws_ini; teste com célula com espaços |
| SANEA-04 | Hash chain cross-tenant-safe | 02 SEG-D1 / 07 R-CLI-02 | Cadeia por tenant OU gravar em run_as_system; gravador e verificador no mesmo escopo; teste cross-tenant de integridade |
| SANEA-05 | Âncora de identidade canônica na mesclagem | 06 D-01 | Campo cliente_canonico_id (imutável) + resolução encadeada + drill cert pré-merge→cliente pós-merge |
| SANEA-06 | Suite verde no fluxo padrão + números honestos | 03 Q1/Q2/Q3 | settings.test default no pytest OU redis no dev; smoke argon2; recontar e reescrever números |
| SANEA-07 | Extrair agregado de domínio Cliente + política LGPD única | 01 D-02/03/04 / 10 D3/D4 | Entidade de domínio com assert_invariant; política LGPD num só lar chamada pelos 3 boundaries — **molde correto pro equipamentos** |
| SANEA-08 | Helper único de evento de auditoria | 10 D2 / 01 D-05 | audit/event_helpers.py; parar de copiar 6x antes de virar N módulos |
| SANEA-09 | Materializar controles ADR-0019 | 07 R-CLI-01/03 | tests/regressao/inv_*.py + linter TST-004 + hook equipamento-imutabilidade-check.sh |
| SANEA-10 | Reconciliar doc↔código + drift de números | 08 D1-D8 / 04 D3 | modelo-de-dominio ↔ models.py; draft→stable após reconciliar; unificar contagem hooks/testes CLAUDE+AGENTS por execução real |

## Onda 2 (médios — não bloqueia dogfooding; resolver na sequência)

- Payload de mesclagem com PII além do necessário (05 D3) → remover perdedor_nome_hash/documento_hash.
- Retenção do evento cliente.mesclado → faixa 25a/WORM (06 D-02 / 05 D2).
- Timeline JSONB seq scan + batch_size + paginação (09 P2/P3/P4/P5).
- Glossário divergente (04 D2) — decidir vocabulário antes de equipamentos definir o seu.
- Refactor God-class views.py por US (10 D1).
- Limpeza: get_by_id fallback (01 D-06), política acesso Admin/suporte (02 SEG-D4), imports mortos + rodar ruff/mypy no módulo (10 D8/D9/D10).

## Conclusão

A decisão do Roldão de auditar antes de copiar **evitou propagar ≥4 bugs reais + débito estrutural** pra todos os módulos futuros. Recomendação: executar a Onda BLOQUEANTE no `clientes` antes de qualquer `/implement` do `equipamentos`; o módulo novo nasce do molde já corrigido. Onda 2 em paralelo/sequência sem travar dogfooding.
