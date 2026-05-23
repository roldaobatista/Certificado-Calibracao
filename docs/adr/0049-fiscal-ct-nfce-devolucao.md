---
owner: roldao
revisado-em: 2026-05-23
status: proposta
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0008-fiscal-pluggable.md
  - docs/dominios/financeiro/modulos/fiscal/prd.md
---

# ADR-0049 — CT-e, NFC-e e fluxo de devolução: escopo Wave A vs V2

> **Status:** PROPOSTA (2026-05-23). Detectado pela auditoria Onda 8 (auditor regulatório 7): PRD do fiscal não declara explicitamente o tratamento de CT-e (transporte), NFC-e (varejo) e devolução. Sem decisão registrada, agente futuro pode inferir errado e codar fora de escopo OU bloquear cenário operacional comum (recoleta de instrumento).

## Contexto

Atividade da empresa-piloto (Balanças Solution) e tenants típicos envolve:
1. **Coleta de instrumento no cliente** pra calibrar no laboratório (movimentação de bem alheio)
2. **Recoleta/devolução** após calibração
3. **Venda de peças** durante atendimento (raro; balcão eventual)
4. **NF de serviço** (NFS-e municipal) — fluxo principal já coberto em US-FIS-001

Questões abertas:
- **CT-e (Conhecimento de Transporte Eletrônico):** obrigatório quando empresa **terceira** transporta carga; dispensado quando o próprio prestador transporta seu serviço (regulamento UF varia). Calibração tipicamente usa frota própria/parceira contratada — regulamento UF define se NF de serviço supre ou exige CT-e.
- **NFC-e (NF Consumidor Eletrônica):** modelo 65 para varejo presencial com SAT/PAF. Calibração não vende em varejo; venda eventual de peça pode usar NF-e modelo 55 normal.
- **Devolução:** cliente devolve peça defeituosa ou instrumento recolhido extemporaneamente.

## Decisão

### CT-e — NÃO-GOAL Wave A; Wave B sob demanda
- Recoleta de instrumento durante prestação de serviço de calibração é **dispensada de CT-e** quando acompanhada de NF de serviço (NFS-e) **OR** Nota Fiscal Avulsa Eletrônica (NFA-e) do prestador — regulamento ICMS UF (verificar por UF do tenant). Tenant configura no onboarding qual modelo a UF dele aceita.
- Tenant que opera transportadora terceirizada (caso raro) entra em **Wave B** com pluggable CT-e (mesma porta `FiscalProvider` da ADR-0008, novo método `emitir_cte()`).
- Documentar em `docs/conformidade/comum/fiscal.md` a matriz UF × dispensa/exigência.

### NFC-e — NÃO-GOAL Wave A
- Calibração não vende em varejo; venda eventual de peça usa NF-e modelo 55.
- Tenant que abrir varejo (raro) entra em **Wave B** sob demanda — pluggable via porta `FiscalProvider`.

### Devolução — Wave A (US-FIS-009)
- Cliente devolve peça/instrumento ou prestador estorna NF emitida.
- US-FIS-009 cobre **estorno** (cancelamento dentro do prazo via US-FIS-003) + **devolução de mercadoria** (NF de devolução do destinatário OR NF-e ajuste do emissor com CFOP de retorno).
- Cancelamento fora do prazo (>24h NFS-e, >24h NF-e — varia UF) usa **nota de ajuste extemporânea** (US-FIS-010 — novo).

### Inutilização de NFS-e municipal — NÃO-GOAL Wave A
- NFS-e municipal não tem mecanismo de inutilização padronizado (cada município define). Inutilização cobre só NF-e modelo 55 (US-FIS-005 existente).
- Município que exigir mecanismo específico entra em V2 sob demanda.

## Alternativas consideradas

1. **Cobrir tudo em Wave A (CT-e + NFC-e + devolução completa)** — REJEITADA. Escopo Wave A já é Top 3 lock (deadline 01/09/2026 CONFAZ 95/22); adicionar CT-e+NFC-e atrasa NFS-e crítico.
2. **Adiar devolução pra V2** — REJEITADA. Devolução é caso operacional comum (cliente devolve peça defeituosa); precisa do dia 0.
3. **Construir CT-e mesmo sem demanda agora** — REJEITADA. ADR-0008 já estabelece pluggable; basta criar quando primeiro tenant pedir.

## Consequências

### Positivas
- Escopo Wave A protegido (NFS-e crítica + devolução cobertas)
- ADR-0008 (`FiscalProvider`) absorve CT-e/NFC-e no futuro sem reescrita
- US-FIS-009/010 adicionadas explicitamente

### Negativas
- Tenant que vende em varejo precisa de workaround (NF-e modelo 55) — comunicação clara no onboarding
- Tenant em UF que exige CT-e mesmo com NFS-e (caso raro) bloqueia ativação Wave A — documentar matriz UF antes

## Itens a fazer

- [ ] Adicionar US-FIS-009 (devolução) + US-FIS-010 (nota de ajuste extemporânea) em `fiscal/prd.md`
- [ ] Atualizar non-goals Wave A em `fiscal/prd.md` com CT-e + NFC-e + inutilização NFS-e
- [ ] Matriz UF × dispensa CT-e em `docs/conformidade/comum/fiscal.md`
- [ ] AC US-FIS-001-X: município sem cobertura BaaS bloqueia ativação tenant
- [ ] AC US-FIS-002-3: rascunho postergado vence em 48h
- [ ] Adicionar enum `regime_tributario`: NORMAL, SIMPLES_NACIONAL, MEI, ST_INDICADOR, LUCRO_REAL, LUCRO_PRESUMIDO
- [ ] US-FIS-008: job anual atualizar_tabelas_fiscais (CFOP/CST/CSOSN/NCM/LC116)

## Aprovação

- [ ] Roldão (decisor)
- [ ] Auditor-conformidade-lgpd (devolução com PII)
- [ ] Consultor RBC (matriz UF dispensa CT-e)

## Referências

- ADR-0008 (FiscalProvider)
- Convênio ICMS 95/22
- NT 2013/007 (contingência NF-e)
- LC 116/2003 (ISS)
- IN RFB 2.229/2024 (CNPJ alfanumérico — ADR-0017)
