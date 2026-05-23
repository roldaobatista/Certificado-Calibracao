---
adr: 0039
titulo: TipoPessoa expandido — PF, PJ, MEI, CLIENTE_EXTERIOR
status: proposto
data: 2026-05-22
proposto-por: agente (Onda 4 saneamento Marco 1 clientes — Auditor 3 ALTO A3-CLI)
revisado-por: pendente (tech-lead-saas-regulado + advogado-saas-regulado + consultor-rbc-iso17025)
bloqueia-fase: Wave A retrofit Cliente (migration `tipo` enum + campos `tax_id_estrangeiro` / `pais_origem`)
depende-de: ADR-0017 (CNPJ alfanumérico), ADR-0021 (anonimização Zona A/B/C)
---

# ADR-0039 — TipoPessoa expandido (PF, PJ, MEI, CLIENTE_EXTERIOR)

> **Status:** PROPOSTO (22/05/2026 — Onda 4 saneamento Marco 1). Pré-requisito Wave A: Cliente nascido em Marco 1 só suporta PF/PJ; produto real precisa de MEI (regime fiscal próprio) e cliente do exterior (calibração off-shore, instrumento importado pra calibrar no BR, contrato com fabricante estrangeiro).
> **Autor:** Auditor 3 (Onda 4) — gap A3-CLI.

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **MEI** | Microempreendedor Individual — pessoa física CPF que também tem CNPJ próprio (regime simplificado da Receita). Não é PJ comum (limite faturamento, sem IE de produção, NFS-e municipal). |
| **CLIENTE_EXTERIOR** | Empresa/pessoa de fora do Brasil que contrata serviço (calibração, ensaio). Não tem CNPJ. Tem **tax ID estrangeiro** (EIN nos EUA, NIF na Europa, etc.). |
| **`tax_id_estrangeiro`** | Identificador fiscal do país de origem. Texto livre normalizado por país. |
| **Enum SQL** | Lista fechada de valores válidos pra um campo (não aceita "MEU_TIPO_NOVO" sem migration). |

---

## Contexto

Marco 1 `clientes` (entregue 2026-05-20) modela `Cliente.tipo` como enum `{PF, PJ}` em `modelo-de-dominio.md` + `prd.md` §6 US-CLI-001. Cobre 80% do mercado-alvo (assistência técnica + calibração metrológica nacional).

Lacunas detectadas na auditoria Onda 4:

1. **MEI (Microempreendedor Individual)** — Balanças Solution (dogfooding) tem clientes MEI hoje (consertos pra autônomos formalizados). MEI cadastrado como PJ infla a base "PJ real" e quebra:
   - cálculo de tributo (NFS-e MEI usa código serviço próprio + alíquota fixa)
   - régua D+30/60/89 (CDC art. 6º III/IV trata MEI como vulnerável — texto deve mencionar "como microempreendedor")
   - relatório fiscal (PGDAS-D vs DASN-SIMEI vs Lucro Presumido — segregação por tipo)
2. **Cliente do exterior** — mystery shopping Calibre.Software mostra: laboratórios brasileiros em região fronteiriça (Foz, Uruguaiana, Pacaraima) recebem instrumento de cliente paraguaio/uruguaio/venezuelano pra calibrar e devolver com certificado RBC. ISO 17025 cl. 7.8 não exige cliente nacional; nada impede emissão. Hoje cadastrar exige CNPJ → cadastro fica travado.
3. **Cabeça-de-fila do tax_id estrangeiro** — KMS / WORM trilha exige PII completa pra anti-fraude; CLIENTE_EXTERIOR precisa de campo análogo a `documento` mas com regras distintas (formato livre, validação por país via tabela externa).

---

## Decisão

### 1. Expandir enum `TipoPessoa`

```
TipoPessoa = {PF, PJ, MEI, CLIENTE_EXTERIOR}
```

Default na criação = PF (preserva comportamento Marco 1 — formulário curto US-CLI-001 cria PF).

### 2. Campos novos em `Cliente`

| Campo | Tipo | Obrigatório se | Notas |
|---|---|---|---|
| `tipo` | enum TipoPessoa | sempre | Imutável após criação (mudança de regime = novo cadastro vinculado por `cliente_canonico_id` INV-CLI-001) |
| `documento` | varchar(14) | tipo ∈ {PF, PJ, MEI} | PF = CPF 11 dígitos; PJ/MEI = CNPJ ADR-0017 (`^[A-Z0-9]{12}[0-9]{2}$`) |
| `tax_id_estrangeiro` | varchar(40) | tipo = CLIENTE_EXTERIOR | Texto livre normalizado (uppercase + trim). Sem validação algorítmica no MVP — só formato presente. |
| `pais_origem` | char(2) | tipo = CLIENTE_EXTERIOR | ISO 3166-1 alpha-2 (ex: `PY`, `UY`, `US`). NUNCA `BR` (CLIENTE_EXTERIOR ⊥ tax_id BR). |
| `regime_tributario` | enum {SIMEI, SIMPLES, PRESUMIDO, REAL, ISENTO_EXTERIOR} | tipo ∈ {PJ, MEI} | MEI sempre SIMEI (CHECK constraint). Cliente PF não tem regime tributário. |

### 3. Regras de unicidade

```sql
-- PF/PJ/MEI: UNIQUE (tenant_id, documento) — INV-024 mantida
-- CLIENTE_EXTERIOR: UNIQUE (tenant_id, pais_origem, tax_id_estrangeiro)
CREATE UNIQUE INDEX uq_cliente_documento
  ON cliente (tenant_id, documento)
  WHERE tipo IN ('PF', 'PJ', 'MEI');

CREATE UNIQUE INDEX uq_cliente_tax_id_estrangeiro
  ON cliente (tenant_id, pais_origem, tax_id_estrangeiro)
  WHERE tipo = 'CLIENTE_EXTERIOR';
```

### 4. Impacto LGPD (ADR-0021)

- **CLIENTE_EXTERIOR** sai do escopo LGPD direto (titular fora do BR). Mantém-se sob jurisdição local do país de origem + cláusula contratual. **Não exigir aceite LGPD** mas exigir **aceite contratual genérico** com base legal "execução de contrato" (LGPD art. 7º V — ainda registrado, mas finalidade=`contrato_internacional`).
- **MEI** segue regras LGPD de PF (CPF é dado pessoal; CNPJ MEI é dado público mas vinculado).
- **Zona A/B/C ADR-0021:** `tax_id_estrangeiro` entra na matriz como **Zona B** (retenção fiscal Receita Federal por contrato de exportação de serviço — RFB pode auditar).

### 5. Impacto fiscal / NFS-e

- **MEI:** emissão de NFS-e usa código serviço próprio + alíquota 0 (ISS recolhido via DAS-MEI). FiscalProvider ADR-0008 precisa expor flag `e_mei` no payload de emissão. Detalhe pra Wave A — não bloqueia esta ADR.
- **CLIENTE_EXTERIOR:** emissão é exportação de serviço (RFB Lei 9.430/96 art. 24 — não há IRRF se cliente estrangeiro paga em USD/EUR via SWIFT). Campos `pais_origem` + `moeda_contrato` (campo futuro Wave A) entram no payload.

### 6. UI / formulário

- Tela US-CLI-001 ganha **seletor de tipo** com 4 opções logo no início. Mudar tipo no meio do preenchimento **redesenha o formulário** (não tenta migrar campos).
- CLIENTE_EXTERIOR tem campo "país" autocompletar (ISO 3166-1) + campo "documento fiscal local" texto livre.
- MEI mostra check "É MEI?" se usuário escolheu PJ — auto-detectar via consulta CNPJ (Wave A) opcional.

### 7. Migration Wave A

```python
# 0NNN_cliente_tipo_expandido.py
operations = [
    migrations.AddField('Cliente', 'tax_id_estrangeiro', VarChar(40, null=True)),
    migrations.AddField('Cliente', 'pais_origem', Char(2, null=True)),
    migrations.AddField('Cliente', 'regime_tributario', EnumField(null=True)),
    migrations.AlterField('Cliente', 'tipo', EnumField(choices=['PF','PJ','MEI','CLIENTE_EXTERIOR'])),
    migrations.AlterField('Cliente', 'documento', VarChar(14, null=True)),
    # CHECK constraints:
    # tipo=PF → documento NOT NULL, len=11, regime_tributario IS NULL
    # tipo=PJ → documento NOT NULL, regex CNPJ
    # tipo=MEI → documento NOT NULL, regex CNPJ, regime_tributario='SIMEI'
    # tipo=CLIENTE_EXTERIOR → tax_id_estrangeiro NOT NULL, pais_origem NOT NULL, pais_origem != 'BR', documento NULL
]
```

Retrofit dos registros existentes (Marco 1): todos PF/PJ continuam funcionando; tipo permanece. `regime_tributario` populado por job offline (Wave A) com inferência conservadora "PRESUMIDO" pra PJ que não declarar.

---

## Non-goals

- **Validação algorítmica de tax_id estrangeiro** (EIN, NIF, NIE) — fora do MVP. Texto livre normalizado.
- **Cliente exterior pessoa física** (turista estrangeiro com instrumento) — agregar como CLIENTE_EXTERIOR sem distinção PF/PJ no Marco 1. Distinção PF_EXTERIOR vs PJ_EXTERIOR fica pra V2 se demanda surgir.
- **Conversão automática PJ→MEI ou MEI→PJ** — mudança de regime cria cadastro novo com `cliente_canonico_id` apontando para o anterior (INV-CLI-001 + sucessao-societaria.md fluxo "mudança de natureza jurídica").
- **Múltiplos países de origem** — CLIENTE_EXTERIOR tem 1 país. Sede fiscal única.

---

## Consequências

### Positivas
- MEI sai do "PJ infla" — relatórios fiscais corretos.
- Cliente do exterior cadastrável no Marco 1 sem hacks (CNPJ falso = pendência hoje em laboratórios de fronteira).
- Régua D+30/60/89 ganha texto específico pra MEI (CDC vulnerável).

### Negativas
- Formulário US-CLI-001 não cabe mais em 60s pra todos os casos (CLIENTE_EXTERIOR exige país + tax ID). Aceitar: CLIENTE_EXTERIOR é <5% dos cadastros.
- Migration retrofit gera 2 índices parciais + 4 CHECK constraints — risco de deadlock em tenants com >50k clientes. Mitigação: rodar `CREATE INDEX CONCURRENTLY` + janela de manutenção.

### Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| 1 campo `documento` polimórfico vs 2 campos (`documento` + `tax_id_estrangeiro`) | 2 campos | CHECK constraints ficam legíveis; UNIQUE parcial por tipo. |
| Permitir mudar `tipo` vs imutável | Imutável | Mudança de regime é evento fiscal sério; força cadastro novo + canônico. |
| Validar tax_id estrangeiro algoritmicamente | Não | 195 países × algoritmo diferente — fora de escopo. |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita expandir TipoPessoa? — pendente
- [ ] **`tech-lead-saas-regulado`:** revisa CHECK constraints + índices parciais — pendente
- [ ] **`advogado-saas-regulado`:** confirma base legal LGPD pra CLIENTE_EXTERIOR (execução de contrato art. 7º V) — pendente
- [ ] **`consultor-rbc-iso17025`:** confirma emissão de certificado pra cliente exterior não fere ISO 17025 cl. 7.8 — pendente

---

## Referências

- ADR-0017 (CNPJ alfanumérico)
- ADR-0021 (anonimização vs retenção)
- LC 123/2006 (MEI)
- Lei 9.430/96 art. 24 (exportação de serviço)
- ISO 3166-1 alpha-2 (códigos de país)
