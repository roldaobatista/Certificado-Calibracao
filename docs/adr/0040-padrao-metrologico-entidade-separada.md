---
adr: 0040
titulo: Padrão metrológico do laboratório é entidade separada (módulo `padroes`) — NÃO um `Equipamento` do cliente
status: aceito
data: 2026-05-23
aceito-em: 2026-05-25 (saneamento pré-Marco 4 — decisão Roldão)
proposto-por: agente (Onda 5 saneamento pré-Marco 3 — auditoria projeto-inteiro 10 lentes — G2 CRÍTICO)
revisado-por: consultor-rbc-iso17025 + tech-lead-saas-regulado (revisão técnica diferida pós-aceite — não bloqueante)
bloqueia-fase: Wave A Marco 4 (`calibracao` — cadeia de rastreabilidade)
depende-de: ADR-0007 (camada domínio), ADR-0002 (multi-tenancy), ADR-0022 (RT do tenant)
---

# ADR-0040 — Padrão metrológico como entidade separada

## Contexto

O módulo `equipamentos` (Wave A Marco 2 — FECHADO 2026-05-23) modela o
**equipamento físico do cliente final** que o tenant calibra (balança,
paquímetro, termômetro do cliente). NG-EQP-6 declara explicitamente:
"NÃO trata padrão metrológico do laboratório (esse fica em módulo
`padroes` separado — INV-021/022/023)".

A auditoria projeto-inteiro 10 lentes (2026-05-23) detectou o gap G2
CRÍTICO: **o módulo `padroes` está apenas declarado como non-goal —
não tem PRD, não tem modelo de domínio, não tem entidades**. Marco 4
(`calibracao`) precisa selecionar padrão metrológico na hora de
calibrar; sem entidade canônica, cada use case Wave A inventa um
schema diferente.

### Por que NÃO reusar `Equipamento` pra modelar padrão

1. **INV-025 (imutabilidade pós-cert)** trava o equipamento do
   cliente. Padrão do lab precisa de fluxo **diferente** — recal
   externo periódico atualiza atributos críticos (incerteza, validade
   do cert externo).
2. **Cliente vinculado** — `Equipamento.cliente_atual_id` aponta pra
   cliente final. Padrão pertence ao **tenant** (laboratório), não a
   um cliente.
3. **Snapshot na calibração** — padrão usado em calibração precisa
   `snapshot_padrao_json` imutável (INV-CAL-SNAP-001) capturado no
   momento da seleção. Equipamento não tem esse conceito.
4. **Estados não coincidem** — padrão tem `EM_RECAL_EXTERNO`,
   `INTERCOMPARACAO_PT_EM_CURSO`, `BAIXADO`. Equipamento tem
   `EM_CALIBRACAO_LAB`, `SUCATA`, `EXTRAVIADO`.
5. **Rastreabilidade ao SI** — padrão declara `vinculacao` à cadeia
   (BIPM, INMETRO, RBC, INTERNACIONAL). Equipamento do cliente
   nunca declara isso — ele É calibrado contra um padrão.

### Por que NÃO juntar com `Equipamento` via flag `eh_padrao_do_lab`

Foi a hipótese mais simples. Recusada porque:

- **Vazamento de superficie de ataque** — UI/API de equipamentos
  passa a ter ramificações `if eh_padrao` em vários pontos. Bug
  classe inevitável.
- **Multi-tenancy** — equipamento tem RLS por `tenant_id` apontando
  pra equipamento do cliente; padrão é "do tenant" — mesma coluna,
  semântica diferente. Confusão garantida em consultas analíticas
  cross-módulo.
- **ISO 17025 cl. 6.4 (equipamentos) vs cl. 6.5 (rastreabilidade
  metrológica)** — normativa **separa explicitamente** o controle.
  Modelar junto = drift documental contra a norma.

## Decisão

Criar módulo `metrologia/padroes` com entidade raiz
`PadraoMetrologico` separada de `Equipamento`. Marco 4 (`calibracao`)
consome via FK direta (`Calibracao.padrao_usado_id`) ou via VO
`PadraoUsado` (snapshot imutável no momento da seleção —
INV-CAL-SNAP-001).

### Atributos canônicos de `PadraoMetrologico`

- `id: UUID`
- `tenant_id: FK` (RLS)
- `numero_serie: string` (UNIQUE por tenant)
- `fabricante: string`
- `modelo: string`
- `grandezas: list[Grandeza]` (≥1 — VO em
  `src/domain/metrologia/value_objects.py`)
- `faixas: list[FaixaMedicao]` (≥1 — VO existente)
- `incertezas_certificado: list[IncertezaExpandida]` (≥1 — VO
  existente; espelha o cert externo vigente)
- `vinculacao: enum {BIPM, INMETRO, RBC, INTERNACIONAL}` (cadeia de
  rastreabilidade ao SI)
- `validade_certificado_rastreabilidade: date`
- `proximo_recal: date` (computado: validade − margem segurança)
- `estado: enum {EM_USO, EM_RECAL_EXTERNO, INTERCOMPARACAO_PT_EM_CURSO,
  BAIXADO, SUCATEADO}`
- `vigencia_inicio: tstzrange` + `revogado_em` + `motivo_revogacao`
  (ADR-0030 — INV-VIG-001..004)
- `# Padrão soft-delete: B — revogado_em (WORM)` (ADR-0031 — padrões
  participam de cadeia metrológica auditável; baixa preserva
  histórico)

### Eventos publicados

- `padrao.cadastrado`
- `padrao.recal_externo_iniciado`
- `padrao.recal_externo_concluido` (novo cert → atualiza
  `incertezas_certificado` + `validade_certificado_rastreabilidade`)
- `padrao.intercomparacao_iniciada` (PT — proficiency testing,
  INV-023)
- `padrao.intercomparacao_concluida` (resultado: aprovado/rejeitado)
- `padrao.baixado` (terminal)
- `padrao.sucateado` (terminal — fim da vida útil)

### Invariantes próprias (INV-PAD-*)

- `INV-PAD-001` — `numero_serie` UNIQUE por tenant.
- `INV-PAD-002` — pelo menos 1 grandeza + 1 faixa + 1 incerteza no
  cert externo no momento do cadastro (NIT-DICLA-030 item 8.2.6).
- `INV-PAD-003` — `estado IN (EM_RECAL_EXTERNO, BAIXADO, SUCATEADO)`
  bloqueia uso em nova calibração (Marco 4 — pre-emissão valida).
- `INV-PAD-004` — `validade_certificado_rastreabilidade` no passado
  bloqueia uso (já citado em INV-011).
- `INV-PAD-005` — `vinculacao=RBC` exige tenant em perfil A;
  `vinculacao=INMETRO` aceitável em B/C; nunca aceita "rastreável a
  RBC" em D (INV-015).
- `INV-PAD-006` — alteração em `incertezas_certificado` exige
  evento `padrao.recal_externo_concluido` na transação (não
  UPDATE direto — preserva cadeia).

## Consequências

### Positivas

- Cadeia de rastreabilidade ISO 17025 cl. 6.5 fica isolada e
  auditável independentemente de equipamentos do cliente.
- Marco 4 (`calibracao`) sabe exatamente qual entidade selecionar.
- VOs metrológicos já existentes (`Grandeza`, `FaixaMedicao`,
  `IncertezaExpandida`) ganham consumidor canônico.
- NG-EQP-6 deixa de ser promessa vazia.

### Negativas

- +1 módulo na Wave A (`metrologia/padroes`). Esforço estimado:
  3-4 dias.
- Cross-módulo `calibracao → padroes` exige porta
  `PadraoMetrologicoQueryService` (ADR-0007 anti-corrosion).
- Adapter default `Empty*` em Marco 4 inicial até `padroes` ser
  cravado.

### Riscos mitigados

- **R-018 (cadeia metrológica quebrada)** — entidade canônica
  obriga snapshot na calibração.
- **Drift de schema** — código de Marco 4 não inventa estrutura
  alternativa de padrão.

## Plano de implementação

1. Wave A: criar módulo `src/domain/metrologia/padroes/` +
   migration + RLS policy.
2. Wave A: hook validador que bloqueia FK direta cross-módulo
   `calibracao → padroes` sem porta declarada.
3. Wave A: VO `PadraoUsado` (snapshot imutável) consumido por
   Marco 4 — referencia ADR-0040 + INV-CAL-SNAP-001.
4. Marco 4: PRD `calibracao` cita ADR-0040 como dependência
   bloqueante.
5. INVs `INV-PAD-001..006` cravados em `REGRAS-INEGOCIAVEIS.md`
   na Onda 5.

## Non-goals desta ADR

- NÃO define UI de cadastro de padrão (fica no PRD do módulo).
- NÃO trata calibração interna feita por outro lab do mesmo grupo
  (caso "padrão calibrado em casa" exige ADR adicional Wave B).
- NÃO trata padrão emprestado/alugado (caso de exceção — Wave B).
