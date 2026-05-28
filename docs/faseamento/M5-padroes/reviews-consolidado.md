---
owner: roldao
revisado-em: 2026-05-28
status: draft
fase: M5-padroes
ritual: plan-reviews
depende-de: docs/faseamento/M5-padroes/plan.md
---

# Consolidação das revisões do plan — M5 `metrologia/padroes`

> 4 subagentes revisaram `plan.md` v1 (2026-05-28). **Nenhum BLOQUEIA total**,
> mas há correções obrigatórias antes de `/tasks`. 3 ALTO metrológicos +
> 2 bloqueantes de risco + 1 drift-docs disparam **plan v2 + 2 ADRs novas**.
> INV-RITUAL-001: itens ALTO bloqueiam fechamento.

## Vereditos

| Subagente | Veredito | Itens |
|---|---|---|
| consultor-rbc-iso17025 | AJUSTAR (5/5) | NC-1..NC-6 (3 ALTO, 3 MÉDIO) |
| tech-lead-saas-regulado | APROVA COM CORREÇÕES | P1 OK · P2 ajustar · P3 OK · P4 **reescrever (drift)** |
| advogado-saas-regulado | AJUSTAR / OK | P1 ajustar · P2 ok-redação |
| corretora-seguros-saas | AJUSTAR | 4 furos (FURO-1 e FURO-4 bloqueantes) |

## Correções obrigatórias antes de `/tasks`

### Bloqueantes ALTO (metrologia + risco)

- **C-1 (RBC NC-1 — ADR nova): Shewhart híbrido.** Read-model calculado para o
  GRÁFICO (OK), MAS toda decisão derivada de regra Western Electric → entidade
  WORM `AnaliseCartaControle` (snapshot congelado: regra_violada, FKs aos pontos,
  LC/UCL/LCL/σ/n/janela, `versao_motor_shewhart`, decisao_rt, justificativa
  canonicalizada ADR-0029, A3 quando aplicável, hash-chain). Sem isso → NC cl. 8.4
  (decisão não reconstruível: os limites mudam ao recalcular). → **ADR-00XX-A**.
- **C-2 (RBC NC-2 — ADR nova): redefinir "2º caminho de cálculo".** ADR-0025 v2
  cl. 7.11 exige 2 IMPLEMENTAÇÕES INDEPENDENTES do MESMO mensurando (provam
  ausência de bug de software), NÃO 2 estimadores de naturezas diferentes
  (média ponderada vs deriva linear → falso-positivo de investigação em deriva
  normal). Mover deriva linear para controle de estabilidade/trend (carta).
  → **ADR-00XX-B** (corrige interpretação ADR-0025 v2 no módulo padrões).
- **C-3 (RBC NC-4): Western Electric correto + trend.** Regras 2 e 3 precisam de
  "do mesmo lado" (senão falso-positivo). **Adicionar regra de tendência**
  (7 pontos monotônicos) — é o cerne da detecção de deriva (Dor #04). Versionar
  motor (`versao_motor_shewhart` — cl. 7.11).

### Bloqueantes de risco (corretora)

- **C-4 (FURO-1): bloqueio `recal_retornado_pendente_aprovacao_RT`.** Recal voltou
  e gravou valores, mas RT ainda não fez análise crítica → padrão não deve voltar
  a EM_USO utilizável. Estado/flag intermediário antes de liberar.
- **C-5 (FURO-4): bloqueio `rastreabilidade_origem_revogada`.** Lab externo perde
  acreditação OU emite recall/errata do cert de recal → rastreabilidade quebra
  retroativamente. Flag setável por evento externo (paralelo ADR-0045). Severo.

### Drift-docs (tech-lead P4 — corrigir AGORA)

- **C-6: `EmptyPadraoMetrologicoQueryService` NÃO existe no código.** Só em docs
  (spec §7/§13, plan D-PAD-5/§9, modelo-de-domínio, ADR-0040). O M4 só tem
  `padrao_id` solto (`models.py:1151` PadraoUsado, `:1006` ComponenteIncerteza) —
  sem porta plugada, sem validação. **Correção:** (a) porta como FUNÇÕES DE
  MÓDULO em `query_service.py` (estilo `certificados/query_service.py`), NÃO
  Protocol+adapter-Empty; (b) **fail-CLOSED** (padrão é barreira de segurança —
  NÃO replicar fail-open ADR-0063/0066); (c) GATE-PAD-PORTA-M4 = ADIÇÃO ao M4
  (chamar `padrao_bloqueado_para_uso` antes de gravar `PadraoUsado`) + **testes
  NOVOS** do caminho bloqueado (a suíte 629 não cobre isso hoje); (d) corrigir a
  narrativa em spec.md + plan.md (feito neste lote).

### Ajustes MÉDIO (não bloqueiam fechamento, mas entram no plan v2)

- **C-7 (RBC NC-3): k via Welch-Satterthwaite + t-Student quando ν_eff < 30**
  (≥2 recals = ν baixo; k=2 fixo subestima). Decimal puro (sem numpy).
- **C-8 (RBC NC-5): `VinculoAuxiliar` entidade temporal** (N:N, ADR-0030) com
  grandeza de influência (temp/umidade/pressão) + leitura ambiental no
  `PadraoUsadoSnapshot`; intervalos próprios do auxiliar (não herdar do principal
  — corrigir AC-PAD-007-4).
- **C-9 (RBC NC-6): NÃO cravar intervalos "OIML R111"** (R111 não define
  periodicidade). Configurável por tenant + `criterio_intervalo` justificado
  (cl. 6.4.7 + ILAC-G24). Enum `classe` mantém.
- **C-10 (tech-lead P2): GUC `app.padrao_recal_em_curso` no RESET do pool**
  (`_resetar_app_settings_na_conexao`) + `SET LOCAL`; AVALIAR eliminar o GUC
  derivando `incertezas_certificado` como READ-MODEL do último recal retornado
  (trigger bloqueia QUALQUER UPDATE direto). Decisão no plan v2.
- **C-11 (tech-lead P1): anotar** advisory-lock-por-tenant na cadeia global
  (hot path de evento de padrão é baixo — não bloqueia).
- **C-12 (tech-lead P3 — ADR curta): assimetria de path** `calibracao` (achatado)
  vs `metrologia/padroes` (aninhado). Documentar M4 como dívida; daqui pra frente
  metrologia/* aninhado. **NÃO mexer no M4.**
- **C-13 (advogado P1): PRD §8** declarar base legal (art. 7º II + V) + prazo dual
  (5a quente / 25a evidência ISO, Cenário A like M4) do executor/responsável;
  linha nova na matriz de retenção + drill análogo DRILL-RET-07.
- **C-14 (advogado P2): PRD §8** corrigir "não contém PII direta" → campos
  estruturados sem PII, MAS PDF de cert externo pode conter PII de terceiro
  (signatário do lab) — cifrar binário por chave KMS do tenant (crypto-shredding),
  art. 7º II + art. 16 I, sem anonimizar o binário probatório. Confirmar com
  tech-lead que o objeto B2 é cifrado (não só hash no evento).
- **C-15 (corretora FURO-2 — decisão arquitetura): faixa/grandeza não cobre ponto
  de uso.** Ou bloqueio na barreira OU **delegação EXPLÍCITA** a M4/escopos-cmc
  (gap não-declarado entre módulos é pior — R-042). Decidir no plan v2.
- **C-16 (corretora FURO-3): Shewhart ALERTA/tendência** (não só violação dura)
  exige aceite/justificativa registrada — liga com C-1/C-3.

## Saída

- **plan v2** incorporando C-1..C-16 (ADRs C-1/C-2 + ADR curta C-12).
- **2 ADRs novas** (Shewhart híbrido; 2º caminho = 2 implementações) + 1 ADR
  curta (assimetria de path) — escrever ANTES de `/tasks`.
- **drift-docs C-6 corrigido** em spec.md + plan.md (neste lote).
- Emendas PRD §8 (C-13/C-14) + matriz de retenção — replicam decisões M4
  (sem revisão OAB agora — pré-produção, memória `project_sem_contratacoes_externas_ate_producao`).
- **NADA de código até plan v2 + ADRs aprovados** (INV-RITUAL-001).

## Limites declarados pelos revisores

- RBC: protocolo OQ do motor de incerteza + Shewhart, em perfil A 1ª supervisão
  CGCRE, **pode exigir parecer de consultor RBC credenciado** (diferido pré-produção).
- Tech-lead: robustez do GUC sob contenção real de pool **só fecha em drill PG
  real** (GATE-PAD-DRILL-LOCAL) + pentest externo pré-1º tenant.
- Advogado: redação DPA sobre PII de terceiro embarcada → lote revisão OAB
  pré-produção.
- Corretora: contratação E&O ampliada (ADR-0028) exige corretora SUSEP — diferida.
