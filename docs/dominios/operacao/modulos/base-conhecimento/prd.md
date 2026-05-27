---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: base-conhecimento
dominio: operacao
diataxis: explanation
audiencia: agente
historico:
  - 2026-05-17 — versão inicial draft (repositório de conhecimento técnico)
  - 2026-05-27 — Onda 3 saneamento BATCH B2 — frontmatter canônico completo, perfil ADR-0067 declarado (BCN transversal A/B/C/D), REESCRITA COMPLETA das 10 US em BDD GIVEN-WHEN-THEN com 2-3 AC binários cada (modelo M3 OS), INV-AGENT-001 prompt injection em US texto livre (US-BCN-007), INV-TENANT-001 RLS aplicado em GIN/tsvector full-text (AC-BCN-005), vocabulário Wave A/Wave B, status STABLE.
relacionados:
  - docs/adr/0029-canonicalizacao-texto-probatorio.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0058-product-analytics-provider.md
  - docs/adr/0059-llm-provider-canonico.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/dominios/operacao/modulos/chamados/prd.md
  - docs/dominios/operacao/modulos/os/prd.md
---

# PRD — Módulo Base de Conhecimento

## 1. O que este módulo é

Repositório vivo do saber técnico da empresa: artigos, procedimentos operacionais, manuais internos, soluções de problemas comuns, FAQ, base por equipamento/marca/modelo, vídeos de treinamento e anexos técnicos. Aparece como sugestão dentro de Chamados e OS, evitando que técnico experiente seja o único ponto de conhecimento.

## 2. Por que este módulo existe

Conhecimento técnico hoje vive na cabeça de poucos. Quando técnico sai, fica doente ou está atendendo outro cliente, atendente/técnico júnior repete erro já resolvido. Módulo transforma cada solução em ativo reutilizável, com controle de versão e aprovação técnica.

## 3. Personas

**Persona dominante:** P-OP-01 (técnico criador/leitor). Detalhes em `personas.md` + `../personas.md` (P-OP-01 técnico, P-OP-03 atendente, P-OP-04 responsável técnico revisor) + `docs/comum/personas.md`.

## 4. Perfil regulatório (ADR-0067)

Base de conhecimento é **transversal a todos os perfis A/B/C/D** — todo tenant pode ter artigos. Não há gating de regulação específico, mas full-text search RESPEITA isolamento multi-tenant (RLS em GIN/tsvector):

| Feature | A — Acreditado RBC | B — Rastreável | C — Em preparação D→A | D — Comercial puro |
|---|---|---|---|---|
| **Artigo + categorização** (US-BCN-001..004) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **Aprovação técnica obrigatória pra publicar** (US-BCN-002) | ✅ OBRIGATÓRIO (RT do tenant ou suplente) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | 🟢 OPCIONAL_RECOMENDADO (qualquer admin) |
| **Sinalização de artigo desatualizado > 12 meses** (US-BCN-010) | ✅ OBRIGATÓRIO (ISO 17025 cl. 8.3) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL |
| **Full-text search com RLS aplicado** (INV-TENANT-001 — GIN/tsvector) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **Anti prompt injection em comentários** (INV-AGENT-001 — US-BCN-007) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |

Predicate `tenant_perfil_e([...])` lê `Tenant.perfil_regulatorio` no banco — NUNCA do payload.

## 5. Escopo Wave A

- CRUD de artigo (técnico, procedimento, manual, FAQ, solução-problema)
- Categorização por equipamento, marca, modelo, tipo de serviço, norma técnica
- Anexos (PDF, imagem, vídeo) e links externos
- Busca inteligente (full-text + filtros por categoria/equipamento) — RLS em GIN/tsvector (INV-TENANT-001)
- Sugestão automática de artigos dentro de Chamado (por equipamento+sintoma)
- Sugestão automática de artigos dentro de OS (por equipamento+tipo serviço)
- Controle de versão (histórico, comparar versões, rollback)
- Aprovação técnica obrigatória pra publicar (workflow rascunho→revisão→publicado)
- Comentários e sugestões de melhoria por leitor (técnico/atendente)
- Marcação "útil/não útil" pra ranquear
- Integração com Treinamentos (artigo pode ser leitura obrigatória de trilha)
- Vídeos hospedados internamente ou linkados (YouTube privado/Vimeo)
- Audit log (quem criou, quem aprovou, quem editou)
- Sinalização de artigos desatualizados (> 12 meses sem revisão)

## 6. Não-objetivos Wave A

- Geração automática de artigo por IA sem revisão humana (técnico sempre revisa — ADR-0059 LLM)
- Publicação pra cliente externo (módulo é interno; portal cliente fica em Atendimento)
- Wiki colaborativa estilo Confluence/Notion (edição sempre passa por aprovação)
- Tradução automática multi-idioma (Wave B)
- Pagamento por artigo / monetização externa (fora de escopo)

## 7. User Stories (BDD)

### US-BCN-001 — Técnico cria rascunho de artigo a partir de OS

**Como** técnico (P-OP-01), **quero** criar rascunho de artigo a partir de solução aplicada em OS, **para** transformar saber tácito em ativo reutilizável.

- **AC-BCN-001-1**: GIVEN técnico abre OS em estado `concluida` (ADR-0023), WHEN clica "criar artigo desta solução", THEN cria `Artigo` em estado `rascunho` + pré-preenche `titulo` (tipo do serviço) + `categorias` (equipamento + marca + modelo) + `corpo` (campos da OS + observações do técnico).
- **AC-BCN-001-2 (multi-tenant)**: GIVEN técnico salva, WHEN servidor persiste, THEN `Artigo.tenant_id = current_tenant_id` (INV-TENANT-001) + RLS aplicado em todas queries subsequentes.
- **AC-BCN-001-3 (canonicalização)**: GIVEN texto do corpo do artigo, WHEN salva, THEN aplica INV-DOC-CANON-001 (UTF-8 sem BOM + LF + NFC + sem trailing whitespace + marcadores) — ADR-0029.

**Invariantes:** `INV-TENANT-001`, `INV-DOC-CANON-001`.

---

### US-BCN-002 — Responsável técnico aprova e publica artigo

**Como** responsável técnico (P-OP-04 RT do tenant), **quero** revisar e aprovar artigo marcando versão publicada, **para** garantir qualidade técnica.

- **AC-BCN-002-1**: GIVEN artigo em `rascunho` + RT do tenant abre revisão, WHEN clica "aprovar e publicar", THEN versão é incrementada (`v1`, `v2`, ...) + artigo vira `publicado` + publica evento `Artigo.Publicado` (ADR-0033).
- **AC-BCN-002-2 (perfil A/B/C — RT obrigatório)**: GIVEN tenant em perfil A/B/C, WHEN qualquer usuário tenta aprovar, THEN sistema valida via predicate `usuario_e_rt_ativo(tenant_id)`; se falso → 403 `RT_OBRIGATORIO_PERFIL_REGULADO`.
- **AC-BCN-002-3 (perfil D)**: GIVEN tenant em perfil D, WHEN admin (não-RT) aprova, THEN sistema permite (RT opcional perfil D).
- **AC-BCN-002-4 (read perfil)**: GIVEN sistema avalia gating, WHEN lê perfil, THEN consulta `Tenant.perfil_regulatorio` do banco — NUNCA do payload.

**Invariantes:** `INV-BCN-RT-001`, `INV-TENANT-PERFIL-002`.

---

### US-BCN-003 — Atendente vê sugestão automática ao abrir chamado

**Como** atendente (P-OP-03), **quero** ver sugestão automática de artigo ao abrir chamado por equipamento X, **para** acelerar triagem.

- **AC-BCN-003-1**: GIVEN chamado novo com `equipamento_id` + `sintoma_descrito`, WHEN atendente abre tela, THEN servidor busca top-3 artigos publicados com match (`equipamento.modelo` + full-text `sintoma_descrito`) + retorna lista ranqueada por `marcacao_util / total_visualizacoes`.
- **AC-BCN-003-2 (RLS)**: GIVEN busca executa, WHEN servidor consulta full-text, THEN aplica RLS via política `artigo_tenant_isolation` sobre índice GIN/tsvector (INV-TENANT-001 anti-vazamento via search).
- **AC-BCN-003-3 (sem-resultado)**: GIVEN nenhum artigo bate, WHEN servidor responde, THEN UI oculta sugestões + atendente segue triagem normal.

**Invariantes:** `INV-TENANT-001` (RLS em GIN — anti-vazamento full-text).

---

### US-BCN-004 — Técnico vê sugestão dentro da OS

**Como** técnico (P-OP-01), **quero** ver sugestão automática de artigo dentro da OS, **para** consultar enquanto executo.

- **AC-BCN-004-1**: GIVEN OS aberta com `equipamento_id` + `tipo_servico`, WHEN técnico abre detalhe, THEN exibe top-3 artigos relevantes ranqueados por utilidade.
- **AC-BCN-004-2 (mobile)**: GIVEN técnico no app (offline-first), WHEN cache local tem artigos da OS atual, THEN exibe da cache; sync atualiza no próximo conectividade.

---

### US-BCN-005 — Usuário busca por sintoma e recebe lista ranqueada

**Como** usuário (técnico/atendente), **quero** buscar por sintoma e receber lista ranqueada por utilidade, **para** encontrar solução rápida.

- **AC-BCN-005-1**: GIVEN usuário digita termo de busca, WHEN servidor processa, THEN aplica full-text search PostgreSQL (`tsvector` + `tsquery`) + ranqueia por `(marcacao_util DESC, freshness DESC)` + retorna top-20.
- **AC-BCN-005-2 (RLS em GIN/tsvector — INV-TENANT-001)**: GIVEN índice GIN sobre `tsvector_corpo_artigo`, WHEN consulta executa, THEN RLS policy `artigo_tenant_isolation` é aplicada via `tenant_id` na query (não confiar só no índice — middleware Django injeta `WHERE tenant_id = current_setting('app.tenant_id')`). Migration cria índice + política na mesma migration (hook `migration-rls-check.sh`).
- **AC-BCN-005-3 (performance)**: GIVEN tenant com até 5.000 artigos publicados, WHEN consulta full-text roda, THEN p95 ≤ 800ms (NFR).

**Invariantes:** `INV-TENANT-001`, `INV-BCN-SEARCH-RLS-001`.

---

### US-BCN-006 — Mostrar histórico de versões e comparar

**Como** RT (P-OP-04), **quero** ver histórico de versões do artigo e comparar, **para** rastrear mudanças.

- **AC-BCN-006-1**: GIVEN artigo `publicado` com `v >= 2`, WHEN RT abre histórico, THEN UI lista versões (timestamp + autor + diff em chars) + permite "comparar v1 vs v3".
- **AC-BCN-006-2 (rollback)**: GIVEN RT clica "reverter para v2", WHEN confirma, THEN cria nova versão `v(n+1) = copia v2` + audit registra revert (não destrói versões intermediárias).

**Invariantes:** `INV-BCN-WORM-001` (versões não podem ser apagadas, só revertidas via nova versão).

---

### US-BCN-007 — Leitor deixa comentário sugerindo melhoria

**Como** leitor (técnico/atendente), **quero** deixar comentário sugerindo melhoria, **para** que vire tarefa de revisão.

- **AC-BCN-007-1**: GIVEN leitor abre artigo, WHEN adiciona comentário (texto livre), THEN salva `Comentario` vinculado à versão atual + notifica RT.
- **AC-BCN-007-2 (anti prompt injection — INV-AGENT-001)**: GIVEN comentário contém texto livre, WHEN servidor processa pra LLM (sugestão automática de revisão, Wave B) ou exibe a outros usuários, THEN texto é tipado como `TextoLivreNaoConfiavel` + jamais expande variáveis/instruções; output escapado HTML (`bleach`). Hook `llm-pii-redaction-check` valida payload pré-envio LLM (ADR-0059 reservada Onda 0).
- **AC-BCN-007-3 (canonicalização)**: GIVEN comentário salvo, WHEN persiste, THEN aplica INV-DOC-CANON-001 (ADR-0029).

**Invariantes:** `INV-AGENT-001`, `INV-DOC-CANON-001`.

---

### US-BCN-008 — Leitor marca artigo útil/não útil

**Como** leitor, **quero** marcar artigo como "útil/não útil", **para** alimentar ranking de busca.

- **AC-BCN-008-1**: GIVEN leitor abre artigo, WHEN clica "útil" ou "não útil", THEN incrementa contador em `Artigo.marcacao_util` ou `Artigo.marcacao_nao_util` + registra evento (ADR-0058 ProductAnalyticsProvider — evento de produto separado de evento de domínio).
- **AC-BCN-008-2 (LGPD analytics)**: GIVEN evento de marcação, WHEN ProductAnalyticsProvider processa, THEN aplica matriz LGPD legítimo-interesse×opt-in (ADR-0058) + payload NUNCA contém PII (hook `analytics-anti-pii-payload`).

**Invariantes:** `INV-PROD-ANALYTICS-001..003` (reservadas ADR-0058).

---

### US-BCN-009 — Marcar artigo como leitura obrigatória de trilha

**Como** RT (P-OP-04), **quero** marcar artigo como leitura obrigatória de trilha de treinamento, **para** garantir formação consistente.

- **AC-BCN-009-1**: GIVEN artigo publicado, WHEN RT marca "obrigatório em trilha X", THEN cria vínculo `TrilhaArtigo` + módulo Treinamentos passa a exigir leitura.
- **AC-BCN-009-2 (auditoria leitura)**: GIVEN técnico abre artigo obrigatório, WHEN finaliza leitura, THEN registra `LeituraConcluida` com timestamp + duração — alimenta evidência de capacitação (ISO 17025 cl. 6.2).

---

### US-BCN-010 — Sistema sinaliza artigo desatualizado > 12 meses

**Como** sistema, **quero** sinalizar artigo sem revisão > 12 meses, **para** evitar uso de informação obsoleta.

- **AC-BCN-010-1**: GIVEN artigo publicado com `ultima_revisao_em < now() - interval '12 months'`, WHEN job mensal procrastinate roda, THEN seta `Artigo.status_revisao='desatualizado'` + notifica RT.
- **AC-BCN-010-2 (perfil A/B/C — bloqueio ISO 17025 cl. 8.3)**: GIVEN tenant em perfil A/B/C + artigo `desatualizado`, WHEN sugestão automática vai aparecer em chamado/OS, THEN banner amarelo "artigo desatualizado — revisar antes de aplicar" é exibido.
- **AC-BCN-010-3 (perfil D)**: GIVEN tenant em perfil D, WHEN artigo desatualizado, THEN só notificação ao RT (sem banner — perfil D não tem ISO 17025).
- **AC-BCN-010-4 (read perfil)**: GIVEN sistema decide gating, WHEN executa, THEN lê `Tenant.perfil_regulatorio` do banco — NUNCA do payload.

**Invariantes:** `IDEMP-001` (job mensal idempotente — ADR-0033), `INV-TENANT-PERFIL-002`.

---

## 8. Métricas

Ver `metricas.md`. Primárias (mínimo 2-3): % chamados/OS com artigo sugerido aceito, tempo médio de resolução com vs sem artigo, cobertura por equipamento, % artigos desatualizados (> 12 meses).

## 9. NFR

- Busca devolve resultados em < 800ms p95
- WCAG 2.1 AA (INV-016)
- Vídeos servidos via CDN (sem bloquear app)
- Anexos > 50MB rejeitados (config tenant)
- RLS em GIN/tsvector enforced (INV-BCN-SEARCH-RLS-001)

## 10. Dependências (ADRs)

ADR-0029 (canonicalização de texto probatório), ADR-0033 (bus idempotência), ADR-0058 (ProductAnalyticsProvider — marcações útil), ADR-0059 (LLMProvider — Wave B sugestão automática de revisão), ADR-0067 (perfil regulatório — gating RT obrigatório perfil A/B/C).

## 11. Glossário

Ver `glossario.md` deste módulo + `docs/comum/glossario.md` + ADR-0037 (PT-EN canônico).

Termos centrais:
- **Artigo** — unidade de conhecimento técnico publicada (procedimento, manual, FAQ, solução).
- **Versão** — instância imutável de um artigo num momento (WORM via histórico).
- **Aprovação técnica** — autorização do RT pra publicar artigo (obrigatório perfil A/B/C).
- **Trilha** — sequência de artigos como leitura obrigatória de treinamento.

## 12. Como evolui

US nova → próximo `US-BCN-NNN`. Mudança em fluxo de aprovação exige ADR. Feature com gating por perfil → atualizar `docs/conformidade/comum/matriz-feature-perfil.md` antes do merge.
