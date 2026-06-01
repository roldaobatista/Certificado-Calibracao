---
owner: roldao
revisado-em: 2026-06-01
proximo_review: 2026-08-31
status: aceito
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0078 — `metrologia/certificados`: tabela física achatada (contrato de trigger cross-app) + lógica de emissão aninhada

## Contexto

A revisão `tech-lead-saas-regulado` da spec do M8 `certificados` (2026-05-31,
`docs/faseamento/M8-certificados/reviews-consolidado.md` TL-01 ALTO) identificou que
a tabela física `certificados` (stub Marco 2, `src/infrastructure/certificados/`) é um
**contrato de schema consumido por SQL hard-coded de OUTRO módulo**:

- O trigger `equipamento_imutabilidade_pos_cert_check`
  (`src/infrastructure/certificados/migrations/0001_initial.py:73-78`) é
  `BEFORE UPDATE ON equipamentos` e executa
  `SELECT 1 FROM certificados WHERE equipamento_id = OLD.id AND status = 'emitido'
  AND revogado_em IS NULL` — nome de tabela, valor literal `'emitido'`, colunas
  `equipamento_id`/`status`/`revogado_em` todos hard-coded (INV-025).
- O hook `equipamento-imutabilidade-check.sh:67` allowlista o path
  `src/infrastructure/certificados/*`.
- `query_service.tem_emitido` + `CertificadoVigentesManager` (default manager
  filtrado) dependem da semântica `status=EMITIDO + revogado_em IS NULL`.

Renomear a tabela/app, mudar o valor `'emitido'` ou as 3 colunas do contrato quebra a
imutabilidade pós-cert de equipamentos (M2). A ADR-0072 (path aninhado) já rejeitou
"renomear módulo fechado" como risco gratuito (M4 ficou achatado por isso).

## Perfil regulatório (ADR-0067 §4)

Decisão de path/arquitetura (não-funcional, não cria feature de tema sensível). O
comportamento por perfil da emissão de certificado vive no PRD `certificados` §6.1 +
matriz-feature-perfil (templates/selos A/B/C/D, recall A-only, etc.). Esta ADR não
altera nenhuma regra perfil-aware — só decide ONDE o código mora.

## Decisão

**Caminho híbrido:**
- A **tabela física `certificados`** e o **model Django** permanecem em
  `src/infrastructure/certificados/` (app achatada Marco 2). A migration de expansão é
  **estritamente aditiva** (`ADD COLUMN`): nunca renomeia/dropa a tabela, a app, o
  valor `'emitido'`, nem as colunas `equipamento_id`/`status`/`revogado_em` do contrato.
- **Toda a lógica NOVA de emissão** (domínio puro, use cases, repositories, mappers,
  query services de emissão, sequence/NumeroReservado, REST) vai no path **aninhado**
  `src/domain/metrologia/certificados/` + `src/infrastructure/metrologia/certificados/`
  (ADR-0072, espelha M5/M6/M7).
- `query_service.tem_emitido` torna-se **explícito** (`.filter(status='emitido',
  revogado_em__isnull=True)`) em vez de confiar no default manager — robusto a
  refactors futuros que introduzam estados novos (TL-05).

Assimetria local (model num path, lógica em outro) — mesma natureza da assimetria já
aceita pela ADR-0072. Documentada aqui para que um agente futuro NÃO "conserte"
movendo a tabela (que quebraria o trigger cross-app).

## Consequências

- INV-025 (imutabilidade de equipamento pós-cert) preservada sem tocar no trigger.
- Custo: migration aditiva na app `certificados` + nova árvore aninhada. Sem renomeação.
- Drill `GATE-CER-DRILL-LOCAL` deve validar com cert REAL (`status='emitido'`
  inserido pela emissão, não stub): UPDATE de tag/NS/fabricante de equipamento
  bloqueado pelo trigger INV-025.
- `DocumentoCertificado` (PDF/A3 mutável-até-assinar — Q6) é entidade SEPARADA da
  tabela `certificados` WORM; ganha trigger próprio de imutabilidade pós-assinatura em
  Wave A (ADR-0047). Não construir agora.

## Status

✅ **Aceito** (2026-06-01 — promovido na Fatia 3 P8 do M8, T-CER-071). A migration
aditiva concretizou o contrato de trigger sem renomear/dropar a tabela `certificados`,
a app, o valor `'emitido'`, nem as colunas `equipamento_id`/`status`/`revogado_em` do
contrato INV-025 — exatamente como a decisão prescreveu. Schema entregue na Fatia 1b
(`f0cd30d` — 6 migrations aditivas, INV-025 intocado, drill `validar_certificados`
34/34); `query_service.tem_emitido` tornou-se explícito (`.filter(status='emitido',
revogado_em__isnull=True)`); lógica de emissão no path aninhado
`src/{domain,infrastructure}/metrologia/certificados/`. Depende de: ADR-0072.
Relacionada: ADR-0077 (incerteza por ponto), ADR-0076 (faixa declarada), ADR-0074
(cobertura RBC), ADR-0073 (validação no use case), ADR-0067 (perfil snapshot WORM).
