---
owner: agente-ia
revisado-em: 2026-06-10
status: aceito
relacionados:
  - docs/adr/0056-numeracao-os-buracos-aceitos.md
  - docs/faseamento/configuracoes-sistema/spec.md
  - docs/dominios/suporte-plataforma/modulos/configuracoes-sistema/prd.md
---

# ADR-0080 — Numeração de `SerieDocumento` em dois regimes por tipo

**Status:** proposta (criada na P2 da frente `configuracoes-sistema`; promover a aceito no P8)

## Contexto

O módulo `configuracoes-sistema` (frente #1 da cadeia de preço) introduz o agregado
`SerieDocumento` (US-CFG-002): numeração configurável por tipo de documento (os, orcamento,
fatura, certificado, recibo, interno) com prefixo, formato e padding.

A revisão tech-lead (TL-02) e a jurídica (ADV-07) da spec convergiram num ponto: **a exigência
de "sem buraco" na numeração NÃO é uniforme por tipo de documento**, e a spec original prometia
gap-less (INV-028 + AC-CFG-002-3 "sem gap nem duplicata") usando um mecanismo (`UPDATE ... SET
proximo_numero = proximo_numero + 1 RETURNING`) que **gera buraco em rollback** — incoerência
direta.

Fatos:
- **Documentos fiscais (`fatura`) e o certificado de calibração (`certificado` local):** buraco
  na numeração é presunção de **emissão suprimida** perante o fisco (sonegação) e de **emissão
  paralela** perante a CGCRE (ISO 17025 cl. 7.8/8.4; já cravado em INV-028/INV-034). Aqui
  gap-less é **exigência legal/regulatória**.
- **Documentos internos (`os`, `orcamento`, `recibo`, `interno`):** não há norma que proíba
  buraco. Cancelar um orçamento e pular o número não gera ilícito. "Sem gap" aqui é
  **boa-prática auditável**, não imposição fiscal.
- **NFS-e (`nf`/`nfse`):** numerada pelo **município/Ambiente Nacional** (CGSN 189/2026), nunca
  localmente (ver T-CFG-000 §2 + ADR-0008). NÃO é tipo de `SerieDocumento`.

O projeto **já tem os dois mecanismos prontos**:
- **Gap-less:** motor de reserva-TTL + confirmação one-shot + consecutividade densa de
  `metrologia/certificados` (`numero_certificado_reservado` + `src/domain/metrologia/certificados/
  numeracao.py`), construído para a numeração regulatória de certificado (NIT-DICLA-021).
- **Buracos-aceitos:** `os_numero_seq_global` da OS (ADR-0056), que documenta explicitamente
  "buraco por rollback aceito".

## Decisão

`SerieDocumento` numera em **dois regimes, escolhidos pelo `tipo`**, gravados no campo
`regime_numeracao`:

1. **`GAP_LESS`** (tipos `fatura`, `certificado`) — reusa o **motor de reserva-TTL** de
   `metrologia/certificados` (não reescrever): reserva (preview, TTL curto) → confirma one-shot
   na transação que emite o documento → reservas expiradas devolvem o número → o conjunto de
   confirmados é `{1..N}` denso. Garante ausência de buraco mesmo sob rollback/concorrência.
   Tabela WORM Padrão B no número confirmado.

2. **`BURACOS_ACEITOS`** (tipos `os`, `orcamento`, `recibo`, `interno`) — `UPDATE ... SET
   proximo_numero = proximo_numero + 1 RETURNING` (o row-lock exclusivo da linha da série basta
   para unicidade; advisory lock por `(tenant, serie_id)` mantido por consistência de molde).
   **Buraco por rollback é aceito e documentado** (estilo ADR-0056). Sem duplicata, sem
   decremento (INV-028), cancelamento não reusa número.

`AC-CFG-002-3` é reescrito: "incremento atômico **sem duplicata em nenhum tipo**; **sem gap
proposital**; nos tipos `GAP_LESS` sem gap algum (reserva-TTL); nos tipos `BURACOS_ACEITOS`
buraco por rollback é aceito".

`nf`/`nfse` **não são** `tipo` de `SerieDocumento` (BaaS/município é o dono — ADR-0008).

Reset anual (formato com `{ano}`): quando o tipo reseta o sequencial por ano, o contador é por
`(serie, ano)` (decisão do `/plan`; o motor gap-less de certificados já tem dimensão de ano).

## Consequências

**Positivas:**
- Coerência legal/regulatória: gap-less onde a lei/CGCRE exige; flexibilidade onde não exige.
- Zero código novo de numeração — reusa dois motores já validados (certificados + ADR-0056).
- INV-028 deixa de ser auto-contraditório (promessa gap-less com mecanismo gap-ful).

**Negativas / riscos:**
- Dois caminhos de código por tipo (complexidade). Mitigado por um seletor único
  (`regime_numeracao` derivado do tipo) e testes de contraste (gap-less denso vs buraco aceito).
- Gap-less real sob concorrência com rollbacks intercalados exige **drill cronometrado em PG
  real** (espelha GATE-CER-DRILL-LOCAL) antes do fechamento — não basta teste unitário.

## Non-goals

- Não numera NFS-e/NF-e localmente (BaaS/município).
- Não retrofita OS/calibração (que já têm sequence própria) para a série central agora — isso é
  refactor Wave B.
- Não define o motor de cálculo de imposto nem o de formato visual de PDF.

## Alternativas rejeitadas

- **Sequence PG dedicada por série:** não suporta prefixo/formato/padding/reset-anual por série e
  fura em rollback — rejeitada (ADR-0056 já rejeitou para OS).
- **Mecanismo único gap-less para todos os tipos:** sobre-engenharia para os/orcamento (custo de
  reserva-TTL sem exigência legal) — rejeitada.
- **Mecanismo único buracos-aceitos para todos:** viola exigência fiscal/CGCRE em fatura/
  certificado — rejeitada.
