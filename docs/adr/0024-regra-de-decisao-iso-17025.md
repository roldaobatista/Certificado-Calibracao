---
adr: 0024
titulo: Regra de decisão ISO/IEC 17025 cl. 7.8.6 — 3 modos + 6 zonas ILAC G8 + acordo do cliente + override + lock pós-emissão
status: aceito
data: 2026-05-23
aceito-em: 2026-05-23 (Onda 6 saneamento — destravar Marco 4 calibração)
revisado-em: 2026-05-25 (P3 ritual Spec Kit M4 — absorve P-CAL-R1 + P-CAL-R3 RBC + P-CAL-A3 advogado)
proposto-por: agente (auditoria 10 lentes — TEMA-F.1)
revisado-por: consultor-rbc-iso17025 + tech-lead-saas-regulado + advogado-saas-regulado
bloqueia-fase: Wave A Marco 4 (calibracao)
depende-de: ADR-0023 (OS com Atividades)
---

# ADR-0024 — Regra de decisão ISO/IEC 17025 cl. 7.8.6

## Contexto

US-CAL-006 + AC-CAL-006-1..3 já documentam 3 regras de decisão (Aceitação Simples / Banda de Guarda 30% / Risco Compartilhado) + zona de incerteza. Mas **decisão estrutural não tem ADR** — auditor CGCRE em supervisão pede justificativa documentada de por que essas 3 + parametrização por cliente + lock após emissão.

Auditoria 10 lentes (consultor-rbc-iso17025 — TEMA-F.1) marcou como ALTO antes de Marco 4 começar.

## Decisão

**Adotar 3 modos de regra de decisão**, parametrizáveis por cliente, com lock pós-emissão:

| Modo | Quando aplicar | Como calcular | Norma de referência |
|---|---|---|---|
| **Aceitação Simples** (default) | Cliente sem requisito específico | Resultado vs especificação direta; incerteza informada mas não amplia bandas | ILAC G8 §4.2 |
| **Banda de Guarda 30%** | Cliente farma / regulatório que exige risco controlado de aceitação errada (PFA ≤ 5%) | Banda de aceitação = `[LSL + 0.3·U, USL − 0.3·U]` (k=2 → 95.45%) | ILAC G8 §4.4 |
| **Risco Compartilhado** | Cliente pede declaração de probabilidade explícita | Cálculo de PFA + PRA (false acceptance + false rejection); cliente decide threshold | ILAC G8 §4.3 + JCGM 106 |

### Override por cliente

- `Tenant` define regra padrão (`Tenant.regra_decisao_default`).
- `Cliente.regra_decisao_override` pode mudar para clientes específicos (ex: tenant default = Aceitação Simples; cliente farma X = Banda de Guarda 30%).
- Override registrado em audit + cláusula contratual obrigatória do tenant↔cliente.

### Lock pós-emissão

Após `Calibracao.status = APROVADA` + certificado EMITIDO, a regra de decisão usada fica **imutável** no snapshot do certificado. Mudar regra no `Tenant`/`Cliente` no futuro NÃO afeta certificados emitidos.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Adotar só Aceitação Simples (mais simples) | Inviabiliza cliente farma/regulatório que exige Banda de Guarda — perda de mercado |
| Permitir tenant criar regra customizada (4º modo, 5º modo) | Customização do fluxo regulatório por tenant = NC em supervisão CGCRE (ANTI-11). Reservado a ADR futura |
| Regra dinâmica por calibração (sem default tenant) | Carga cognitiva no metrologista; risco de inconsistência tenant |

## Consequências

### Positivas

- ISO 17025 §7.8.6 documentada com base normativa.
- Cliente farma / regulatório atendido sem fork de código.
- Audit trail completo da escolha + override.
- Lock pós-emissão impede fraude retroativa.

### Negativas (mitigáveis)

- Complexidade adicional no UI (P-OP-02 metrologista escolhe modo + parâmetros).
- Treinamento do tenant na escolha do modo.

## Non-goals

- NÃO permite tenant criar 4ª regra customizada.
- NÃO aplica regra retroativamente a certs emitidos.
- NÃO altera ZONA_INCERTEZA — continua exigindo decisão explícita do metrologista (AC-CAL-006-2).

## Invariantes novas

- **INV-CAL-DEC-001:** toda calibração carrega `regra_decisao` snapshot (não-FK ao Cliente — congelado).
- **INV-CAL-DEC-002:** override de cliente exige cláusula contratual ativa do tenant↔cliente (verificada via predicate `clausula_override_vigente` — hook `override-regra-decisao-contrato-check.sh`).
- **INV-CAL-DEC-003:** após `Calibracao.status = APROVADA`, `regra_decisao` é imutável (trigger PG).

## Implicações pro faseamento

- Marco 4 `calibracao` implementa as 3 regras + override + lock + 6 zonas ILAC G8 + PFA/PRA + AceiteRegraDecisao.
- Marco N `clientes` (se necessário) expõe `Cliente.regra_decisao_override` no UI.

---

## Revisão P3 ritual Spec Kit M4 (2026-05-25)

Reviews paralelos do M4 (P-CAL-R1 + P-CAL-R3 RBC + P-CAL-A3 advogado) identificaram 3 lacunas regulatórias na decisão original:

1. **Zonificação incompleta** — `decisao IN ('APROVADO', 'REPROVADO', 'CONDICIONAL')` é insuficiente para ILAC G8:09/2019 §4 tabela 1 (6 zonas). Auditor CGCRE em supervisão pede granularidade (CONDITIONAL_PASS vs CONDITIONAL_FAIL).
2. **PFA/PRA não documentados** — `BANDA_GUARDA_30` e `RISCO_COMPARTILHADO` exigem cálculo + documentação de PFA (probabilidade de aceitação falsa) e PRA (rejeição falsa) — ILAC G8 §4.4 + JCGM 106 §9.
3. **Acordo do cliente não materializado** — cl. 7.1.3 ISO 17025 exige evidência POR CALIBRAÇÃO (ou contrato vigente com aceite assinado) da regra acordada. Snapshot do `regra_decisao` na `Calibracao` é necessário mas não suficiente; CC art. 927 §único + CDC art. 25/51 invalidam exoneração unilateral via "cláusula contratual ativa" sem acordo informado.

### Decisão complementar — 6 zonas ILAC G8

`Calibracao.decisao` expande de 3 valores para enum de 7:

```
decisao ENUM(
  'PASS',                  -- valor + U totalmente dentro de [LSL, USL]
  'CONDITIONAL_PASS',      -- valor dentro, mas U cruza LSL ou USL
  'PASS_COM_RESSALVA',     -- modo Banda 30%: valor dentro de [LSL+0.3·U, USL−0.3·U]
  'CONDITIONAL_FAIL',      -- valor fora de [LSL, USL], mas U cruza fronteira
  'FAIL_COM_RESSALVA',     -- valor fora, U distante do limite mas borderline
  'FAIL',                  -- valor + U totalmente fora
  'NA'                     -- sem especificação de aceitação (calibração descritiva)
)
```

Adicionar campo `zona_ilac_g8 VARCHAR(20) NOT NULL` (snapshot da zona avaliada). Ordem semântica entre `decisao` e `zona_ilac_g8`: a zona é o resultado bruto da interseção; a decisão pode ser sugerida pela zona OU sobreposta pelo metrologista (ex: zona `CONDITIONAL_PASS` em modo `BANDA_GUARDA_30` → decisão `PASS_COM_RESSALVA`).

### Decisão complementar — PFA + PRA documentados

Adicionar à `Calibracao`:
- `pfa_calculada NUMERIC(5,4) NULL` (NOT NULL quando `regra_decisao = BANDA_GUARDA_30`)
- `pra_calculada NUMERIC(5,4) NULL` (NOT NULL quando `regra_decisao = RISCO_COMPARTILHADO`)

Motor de cálculo (ADR-0065 + spec.md §3.3) preenche os 2 campos no momento de `avaliarConformidade`. Default `nivel_confianca = 0.9545` (k=2 → 95.45%). Cálculo via JCGM 106 §9 fórmula 9.1 (PFA) + 9.2 (PRA).

### Decisão complementar — AceiteRegraDecisao (entidade nova)

Nova entidade `AceiteRegraDecisao` (Padrão B — imutável):

```
- id UUID PK
- tenant_id UUID NOT NULL (RLS)
- cliente_id UUID NOT NULL FK
- escopo VARCHAR(20) NOT NULL (POR_CONTRATO_VIGENTE | POR_CALIBRACAO_AVULSA)
- calibracao_id UUID NULL FK (NOT NULL quando escopo=POR_CALIBRACAO_AVULSA)
- contrato_clausula_id UUID NULL FK (NOT NULL quando escopo=POR_CONTRATO_VIGENTE)
- regra_decisao VARCHAR(25) NOT NULL (snapshot da regra acordada)
- texto_canonico_id UUID NOT NULL FK (→ docs/conformidade/comum/termos/aceite-regra-decisao-v1.0.md — REQUER OAB humana)
- texto_hash CHAR(80) NOT NULL (HashVersionado v<NN>$<base64> do texto exibido — ADR-0064)
- assinatura_payload_encrypted BYTEA NOT NULL (touch ou A3 cliente — INV-OS-ACEITE-BIO-001 herdado)
- assinatura_modo VARCHAR(10) NOT NULL ('TOUCH' | 'A3')
- vigencia_inicio TIMESTAMPTZ NOT NULL
- vigencia_fim TIMESTAMPTZ NULL
- concedido_em TIMESTAMPTZ NOT NULL
- correlation_id UUID NOT NULL
```

Trigger PG: UPDATE/DELETE bloqueado pós-INSERT (Padrão B WORM).

Validação no `configurarCalibracao` (US-CAL-002):

- `tipo_acreditacao = RBC` E `regra_decisao IN ('BANDA_GUARDA_30', 'RISCO_COMPARTILHADO')` → exige `AceiteRegraDecisao` vigente cobrindo o cliente.
- Predicate `regra_decisao_acordada_cobre(cliente_id, regra, em_data)` retorna `True` se: (a) `AceiteRegraDecisao` vigente com `escopo=POR_CONTRATO_VIGENTE` para o cliente, OU (b) `AceiteRegraDecisao` com `escopo=POR_CALIBRACAO_AVULSA` para a calibração específica.
- Ausente → 412 `RegraDecisaoNaoAcordadaCliente`.

Snapshot na `Calibracao`:
- `regra_decisao_acordada_em TIMESTAMPTZ NOT NULL`
- `regra_decisao_acordada_documento_id UUID NOT NULL FK` (→ `AceiteRegraDecisao.id`)
- `regra_decisao_acordada_hash CHAR(80) NOT NULL` (snapshot do `texto_hash`)

### Invariantes complementares (M4 P3)

- **INV-CAL-DEC-004:** `regra_decisao = BANDA_GUARDA_30` exige `pfa_calculada NOT NULL`; `regra_decisao = RISCO_COMPARTILHADO` exige `pra_calculada NOT NULL`. Ausente → 412 `PFA/PRA Não Calculada`.
- **INV-CAL-DEC-005:** `zona_ilac_g8` deve ser uma das 6 + `NA` (CHECK constraint DDL); outros valores rejeitados.
- **INV-CAL-DEC-006:** `tipo_acreditacao = RBC` exige `regra_decisao_acordada_documento_id NOT NULL` antes de `em_revisao_1`; ausente → 412 `RegraDecisaoNaoAcordadaCliente`. Predicate `regra_decisao_acordada_cobre` invocado em `configurarCalibracao` + `solicitarRevisao`.

### Caso narrativo CGCRE

Auditor CGCRE em supervisão pede print de 50 últimas calibrações. Agrupa por `decisao`:
- 25 PASS — sem perguntas.
- 12 CONDITIONAL_PASS — auditor pergunta: "estes 12 receberam orientação `borderline em U`?". Sistema responde com texto canônico cravado no certificado.
- 8 PASS_COM_RESSALVA — auditor confirma PFA calculada < 5% (ILAC G8 §4.4).
- 3 CONDITIONAL_FAIL — auditor pergunta: "estes 3 foram comunicados ao cliente com risco de rejeição?". Sistema mostra `EventoDeCalibracao` `ConformidadeAvaliada` com payload PRA.
- 2 FAIL — auditor confirma NC aberta + decisão `PARAR_TRABALHO`.

NC documental evitada. Cobertura ISO 17025 cl. 7.8.6 + ILAC G8 + JCGM 106.

### Limites legítimos

🔴 **REQUER OAB humana** — texto canônico `aceite-regra-decisao-v1.0.md` passa por controle CDC art. 25 + 51 (nulidade de exoneração unilateral). OAB humana redige antes de 1º tenant externo pago. Agente cria minuta preliminar com selo `REQUER VALIDAÇÃO OAB HUMANA`.

🔴 **REQUER CGCRE humano credenciado** — wording técnico das zonas + PFA/PRA por grandeza. Agente cria minuta preliminar com selo `REQUER VALIDAÇÃO CGCRE HUMANO`.

## Status

**ACEITO 2026-05-23** original (3 modos + override + lock).
**REVISADO E REACEITO 2026-05-25** (6 zonas ILAC G8 + PFA/PRA + AceiteRegraDecisao + INV-CAL-DEC-004..006).
