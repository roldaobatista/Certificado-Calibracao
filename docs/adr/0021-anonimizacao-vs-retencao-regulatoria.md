---
adr: 0021
titulo: Anonimização vs retenção regulatória — 3 zonas + Zona D (PF com OS em andamento)
status: aceito
data: 2026-05-20
aceito-em: 2026-05-23 (necessário pra fechar NOVO-ALTO-6 R2 — DPA cl. 4.7 referenciava ADR em proposta)
proposto-por: roldao + agente
revisado-por: advogado-saas-regulado, tech-lead-saas-regulado, consultor-rbc-iso17025
ratificacao-oab: pendente (advogado humano OAB pré-1º tenant externo pago)
bloqueia-fase: Wave A (módulo certificados ISO 17025 + módulo fiscal)
depende-de: ADR-0002 (multi-tenancy), ADR-0008 (fiscal pluggable), ADR-0017 (CNPJ alfanumérico)
---

# ADR-0021 — Anonimização vs retenção regulatória

## Contexto

US-CLI-006 (T-CLI-114..120) entrega direitos do titular LGPD em Marco 1
`clientes`. Em Wave A, módulos `operacao/certificados` (ISO 17025
§8.4 — retenção 25a) e `fiscal/nf` (CTN art. 173 — retenção 5a)
emitirão registros vinculados ao Cliente. Quando o titular invocar
direito de eliminação (LGPD art. 18 VI), há **conflito direto** entre:

- **LGPD art. 16 III**: dever de eliminar dados pessoais quando o
  tratamento cessar.
- **LGPD art. 16 IV**: permite manter dado para cumprimento de
  obrigação legal/regulatória (CTN, ISO/RBC).
- **LGPD art. 16 II**: dever só termina com anonimização.

Revisão do consultor RBC (T-CLI-114..120) cravou 3 zonas de dado;
revisão do advogado consolidou em matriz; este ADR formaliza.

## Decisão

Cliente com vínculo regulatório (NF emitida OU certificado ISO emitido)
recebe **anonimização parcial diferida** ao invocar direito de
eliminação — não eliminação efetiva. Aplica-se a seguinte
classificação por zona de dado:

### Zona A — Identificação titular (PII pura, sem valor regulatório)

| Campo | Tratamento na eliminação |
|---|---|
| CPF | Hash SHA-256 + salt por tenant (irreversível, via `hashear_pii_com_salt_tenant`) |
| RG | Hash idem |
| e-mail | `NULL` |
| telefone | `NULL` |
| data_nascimento | `NULL` |
| observacao | `NULL` |

**Base legal:** LGPD art. 16 II (anonimização permite término do
tratamento como dado pessoal).

### Zona B — Identificação fiscal/regulatória PJ (valor probatório)

| Campo | Tratamento |
|---|---|
| CNPJ | **MANTER** integral 25 anos (preserva rastreabilidade do certificado/NF) |
| Razão social | **MANTER** integral |
| Inscrição estadual | **MANTER** |
| Endereço fiscal | **MANTER** (parte da identificação fiscal) |

**Base legal:** LGPD art. 16 IV (obrigação legal — CTN 173 / Lei
9.933/99 INMETRO) + ISO/IEC 17025 §7.8.2.1 (identificação inequívoca
do cliente no certificado) + §8.4.2 (retenção do registro técnico).

### Zona C — Vínculo titular ↔ cliente PJ (pseudonimização)

| Campo | Tratamento |
|---|---|
| Nome do contato | Pseudonimizar (hash) preservando rastreabilidade interna ao tenant |
| Cargo | Pseudonimizar |
| Assinatura de aceite | Hash do CPF + traçado preservado por 25a se compõe evidência ISO |

**Base legal:** LGPD art. 11 II "a" (cumprimento de obrigação
regulatória).

### Cliente PF sem vínculo regulatório (sem NF/cert emitido)

Eliminação **efetiva** (`DELETE + cascade` preservando audit chain
via anonimização do payload das linhas históricas). LGPD art. 16 II.

## Signatário humano do certificado (ISO cl. 6.2 + NIT-DICLA-021)

Signatário **NUNCA** entra em fluxo de eliminação enquanto certificado
emitido por ele estiver dentro do prazo de 25a (LGPD art. 7º II + art. 11
II "a"). Resposta padrão ao pedido de eliminação:

> "Mantido por obrigação ISO/IEC 17025 §8.4 + NIT-DICLA-021 até
> [data emissão + 25a do último certificado assinado]. Após esse
> prazo, eliminação total será aplicada automaticamente."

**Em dogfooding pré-RBC** (ainda sem acreditação): base muda para
**Lei 9.933/99 INMETRO art. 7º II** (obrigação legal de prestar serviço
metrológico) — consultor RBC R2.

## Registro art. 37 LGPD × §8.4 ISO

**Não há conflito.** Registros independentes, compartilham trilha
imutável B2 WORM com tags distintas (`tipo: lgpd_acesso` /
`tipo: lgpd_operacao` / `tipo: iso_calibracao`). Retenção =
max(25a, prazo LGPD do tenant).

## Implementação

- **Marco 1 (dogfooding):** módulos NF/certificados ainda não existem
  → toda eliminação cai na via "PF sem vínculo regulatório" = DELETE
  efetivo. Helpers `_tem_nf_emitida` / `_tem_certificado_iso` em
  `clientes` retornam `False` (stubs).
- **Wave A:** quando módulos fiscal e certificados nascerem, stubs
  viram portas (`NFGateway`, `CertificadoGateway`) consultadas pelo
  use case `EliminarDadosDoTitular`.

## Limites honestos

- **Consultor RBC humano credenciado CGCRE** deve assinar a matriz
  antes da 1ª auditoria CGCRE real (R$ 5-10k pontual). Subagente IA é
  consultivo, não credenciado.
- **Advogado humano licenciado** valida o texto de bloqueio padrão e
  base legal final pré-1º tenant externo pago (2-4h pontual).
- Implementação real (não-stub) depende dos módulos fiscal +
  certificados Wave A.

## Zona D — Cliente PF com OS em andamento (estendida em 2026-05-23 — TEMA-D.8)

> Adicionada após auditoria 10 lentes — ADR-0021 cobria PF sem vínculo + PF com vínculo regulatório, mas não cobria **PF com OS em estado não-terminal** quando pedido de eliminação chega. CC art. 422 boa-fé contratual sugere completar; LGPD art. 18 §3º dá 15 dias úteis.

**Fluxo:**

1. Pedido de eliminação chega de cliente PF com OS em estado não-terminal (RASCUNHO/AGENDADA/EM_EXECUCAO).
2. Sistema **suspende a OS** por **15 dias corridos** (conforme LGPD art. 18 §3º — "prazo razoável" ANPD interpreta como ≤15d corridos; prorrogação justificada pelo art. 18 §4º quando necessário) + notifica cliente:

   > "Identificamos que você tem uma Ordem de Serviço em andamento (OS-####). Esta OS gera obrigação contratual (CC art. 422). Podemos: (a) concluir a OS e iniciar a eliminação após emissão de eventuais documentos legais; (b) cancelar a OS sem cobrança e eliminar imediatamente. Aguardamos sua decisão em até 15 dias corridos (LGPD art. 18 §3º). Caso precisemos de prazo adicional pra completar a OS, comunicaremos formalmente a justificativa (art. 18 §4º) antes de exceder."

3. Cliente responde:
   - **Opção A — concluir OS:** OS prossegue normalmente; quando concluir, sistema aplica matriz ADR-0021 zona A/B/C conforme cert/NF emitido.
   - **Opção B — cancelar:** sistema cancela OS sem cobrança + aplica zona A (eliminação efetiva, pois sem cert/NF).
   - **Sem resposta em 15d corridos:** sistema cancela automaticamente OS + zona A. Audit logado.

4. **Prorrogação justificada (art. 18 §4º — adicionado Onda 7C NOVO-ALTO-4 R2):** quando OS exige >15d corridos pra concluir tecnicamente (ex: cliente farma com prazo regulatório pra liberar lote), tenant notifica cliente formalmente com justificativa (texto canônico em `docs/conformidade/comum/termos/prorrogacao-prazo-eliminacao-v1.0.md` — a criar Wave A). Boa-fé contratual CC art. 422 + transparência LGPD art. 6º VI.

**Implicações:**

- Use case `EliminarDadosDoTitular` consulta `OSGateway.tem_os_em_andamento(cliente_id)` antes de aplicar matriz.
- Tenant pode definir política default (Opção A ou B) no `Tenant.politica_eliminacao_os_em_andamento`.
- Hook `dpa-zona-d-required.sh` valida que tenant tem política configurada antes de habilitar pedido de eliminação no portal.

---

## Rastreabilidade

- US-CLI-006 / AC-CLI-006-3 (`spec.md` L414-423).
- BLOQ-R1 (RBC) + BLOQ-A3 (advogado) absorvidos.
- ISO/IEC 17025 §7.8.2.1, §8.4.2; LGPD art. 7º II, art. 11 II "a",
  art. 16 II/IV; CTN art. 173; Lei 9.933/99.
- T-CLI-116 (matriz eliminação×anonimização) — implementação Wave A.
- TEMA-D.8 + TEMA-D.10 auditoria 10 lentes 2026-05-23 (Zona D + 4-party).
