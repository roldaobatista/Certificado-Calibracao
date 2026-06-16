---
owner: agente-ia
revisado-em: 2026-06-16
proximo-review: 2026-09-16
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: agenda
tipo: reviews-consolidado
relacionados:
  - docs/faseamento/agenda/spec.md
  - docs/faseamento/agenda/T-AGE-000-investigacao.md
---

# Reviews consolidados P2 — frente `agenda`

> 3 revisores (tech-lead + consultor-rbc + advogado). Veredito geral: **APROVA COM CORREÇÕES** —
> todas incorporadas na `spec.md`. Nenhum REPROVA travante. Achados abaixo + onde foram cravados.

## tech-lead-saas-regulado — APROVA COM CORREÇÕES

| ID | Achado | Sev | Onde cravado |
|---|---|---|---|
| TL-AGE-01 | EXCLUDE de overlap **omitia `tenant_id`** — furo de isolamento; RLS não escopa a constraint. Molde real = `excl_imposto_vigencia_sobreposta` (tenant_id 1ª coluna) | **CRÍT** | D-AGE-13 + INV-AG-OVERLAP-001 (`tenant_id WITH =, tecnico_id WITH =, tstzrange '[)' WITH &&`) |
| TL-AGE-02 | No-show: criar consumer dentro de CR (FECHADO) seria toque indevido. Espelhar D-AGE-5 → chamar `criar_titulo_manual` (use case público) via porta `AReceberPort` | ALTO | D-AGE-9 |
| TL-AGE-03 | `pendencia_cnh` JÁ legível via `PapelColaboradorOutputSerializer` (não está só no `/elegiveis`); `is_tecnico_campo` = derivado de papel — **zero extensão de colaboradores** | ALTO | D-AGE-7 + D-AGE-12 |
| TL-AGE-04 | Acoplamento app→app aceitável SE concreto fica no infra (adapter implementa `OSSchedulingPort`), não use case da agenda importando `application/operacao/os/` | MÉD | nota P3 |
| TL-AGE-05 | Não depender dos eventos locais `os_atribuida`/`atividade_reagendada` (mapeados `None`); ler via porta/repo, não SQL cru no schema da OS | MÉD | D-AGE-5 + nota P3 |
| TL-AGE-06 | Consumers `os.*`/`colaborador.*`/`tenant.rt.trocado` com `consumer_id` único, all-or-nothing; fan-out aditivo (`os.concluida` já tem 2 consumers) | MÉD | §6 + nota P3 |

Path D-AGE-1, perfil server-side, 412≠422, reuso `rt_competencia_cobre`: **APROVADOS sem ressalva.**
Sequenciamento confirmado: núcleo 1–3 construível/testável sem tocar fechados (portas com fake); fatia 4 cross-módulo por contrato público.
Honestidade (escalar): drill de concorrência do EXCLUDE em PG real; interpretação trabalhista das regras (não assina).

## consultor-rbc-iso17025 — RESSALVA

| ID | Achado | Onde cravado |
|---|---|---|
| RBC-AGE-01 | Jornada: 3→**5 regras** (faltavam teto diário + DSR 35h/6d); **espera = 1/1 não 1/3** (ADI 5322 revogou §9º); recorte **perfil-agnóstico** (CLT é ordem pública, não depende de A/B/C/D). NÃO entra na matriz-feature-perfil | D-AGE-4 + INV-AG-JORNADA-UMC-001 |
| RBC-AGE-02 | RT substituto **barra cedo demais**: agendar é planejar. Validar competência **projetada ao instante do slot**; A determinístico=412 / A incerto=warning; gate duro de NC (cl. 6.2.5/7.8) é na **emissão** (`certificados`, já existe) | D-AGE-6 + INV-AG-PERFIL-001 |
| RBC-AGE-03 | RT-só-A espelha a matriz (CONFIRMA); jornada perfil-aware REPROVA (eixo trabalhista ≠ metrológico) | §2/§5 |

## advogado-saas-regulado — minuta APROVA COM CORREÇÕES (consultiva, sem OAB)

| ID | Achado | Onde cravado |
|---|---|---|
| ADV-AGE-01 | Citações: R2 = **§5º** (não §1º) + CTB 67-C; R5 = **art. 71 §5º** (não 235-C §3º); R3 = "até 4h só c/ acordo (=12h)", 12x36 é art. 235-F distinto; nota modulação ADI 5322 **ex nunc 12/07/2023** | D-AGE-4 |
| ADV-AGE-02 | `is_tecnico_campo` mistura 2 regimes → **discriminador `regime_jornada`** (motorista_profissional 235-C × clt_geral 58/71). Enquadramento = CTPS real (RH/advogado humano). Flag em colaboradores (fechado) = ADR | D-AGE-15 |
| ADV-AGE-03 | +R6 (agenda **não é ponto** — registro de jornada é obrigação patronal, dono frota/folha); +R7 (jornada noturna 22h–5h advisory); DSR-pagamento = folha Wave C | D-AGE-4 |
| ADV-AGE-04 | PRD §4/AC-AG-002-2 contradiz a spec (gating por perfil ERRADO) → corrigir PRD; INV-020 em REGRAS desatualizado ("espera 1/3 §9") → reescrever | Ações P3 §8 |

## Ações P3 (antes de plan/tasks)

1. Corrigir **PRD** `agenda/prd.md` §4/AC-AG-002-2 — INV-020 perfil-agnóstico.
2. Reescrever **INV-020** em `REGRAS-INEGOCIAVEIS.md` (espera 1/1 ADI 5322 + R4/R5/R6/R7).
3. Rotear **`regime_jornada`** ao tech-lead (flag/ADR em colaboradores fechado — D-AGE-15).
4. **GATE-AGE-JORNADA-TRABALHISTA** registrado (advogado humano OAB pré-produção — enquadramento individual + convenção coletiva sindicato MT).

## Limites de subagente IA (escalonamento honesto)

- Jornada trabalhista (frente de maior risco): advogado humano OAB antes do 1º técnico de campo real.
- NC cl. 6.2.5 na 1ª supervisão CGCRE: consultor RBC humano credenciado (~R$5–15k pontual).
- Minutas escritas agora; revisão humana só pré-produção (decisão Roldão — `project_sem_contratacoes_externas_ate_producao`).
