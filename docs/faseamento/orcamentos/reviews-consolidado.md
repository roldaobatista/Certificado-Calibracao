---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: explanation
audiencia: [agente, auditor]
frente: orcamentos
tipo: reviews-p2
relacionados:
  - docs/faseamento/orcamentos/spec.md
  - docs/faseamento/orcamentos/T-ORC-000-investigacao.md
---

# P2 — Revisões consolidadas + decisões Roldão — frente `orcamentos`

> tech-lead-saas-regulado + advogado-saas-regulado, 2026-06-13. Ambos **APROVA COM CORREÇÕES**.
> Rodada batch Roldão resolveu 2 decisões + acrescentou 1 requisito estrutural. **Resultado: a
> frente orcamentos PAUSA em P2 — surgiu uma dependência DURA (OS multi-equipamento) que precisa
> ser feita ANTES (frente própria), senão o orçamento nasce com contrato errado.**

## Decisões Roldão (rodada batch P2, 2026-06-13)

- **R-ORC-1 — Equipamento JÁ no orçamento.** Cada item de calibração do orçamento aponta para um
  equipamento (não orçamento genérico). A OS nasce com equipamento(s) identificado(s).
- **R-ORC-2 — Aprovação: lógica agora, PDF/página depois.** Vendedor aprova internamente + endpoint
  público de 1-clique entram no núcleo; PDF e a TELA HTML pública = frente de telas.
- **R-ORC-3 (NOVO, ESTRUTURAL) — N equipamentos por orçamento E por OS.** "Tanto orçamento quanto
  ordem de serviço devem permitir ter quantos equipamentos quiser, e cada um ter seus itens e ter
  itens compartilhados (sem equipamento — ex: deslocamento/taxa)." **Isto contradiz o modelo atual
  da OS (1 equipamento) e exige retrofit.**

## Achado estrutural — OS multi-equipamento é PRÉ-REQUISITO (frente própria antes de orcamentos)

Investigação tech-lead (refs no relatório do subagente):
- **OS hoje = 1 equipamento:** `OS.equipamento` FK NOT NULL PROTECT (`ordens_servico/models.py:51-56`);
  INV-OS-ATIV-002 = "atividade herda equipamento_id da OS pai"; envelope `Orcamento.Aprovado` carrega
  `equipamento_id` único no header (`consumers/orcamento.py:87,128`).
- **MAS a infra de equipamento-por-atividade já existe:** `AtividadeDaOS.equipamento_id_desnormalizado`
  (`models.py:244-252`) e o índice de concorrência metrológica INV-OS-CONC-001 **já chaveia por
  `(tenant, equipamento_id_desnormalizado)` da atividade** (`migration 0005:87-89`) — NÃO se move.
- **Abordagem recomendada (A cirúrgica):** equipamento passa a viver na atividade (coluna já existe);
  `OS.equipamento` vira nullable; envelope move `equipamento_id` do header → por item; itens
  compartilhados têm `equipamento_id=null` + `tipo_atividade_alvo=null` (linha comercial).
- **Impacto OS fechada:** migration RELAXANTE (NOT NULL→nullable, não destrutiva, reversível) +
  CREATE OR REPLACE trigger + ~5 call-sites (mapper/queries/consumer) + emenda ADR-0023 + emenda
  INV-OS-ATIV-002/INV-OS-EQP-001 + ADR nova "OS multi-equipamento". Esforço **M (médio), aditivo**.
- **Riscos:** #1 ALTO — detecção de equipamento baixado em OS multi-equipamento (`consumers/equipamento.py:40`
  filtra por `OS.equipamento_id`; precisa migrar p/ atividade + teste UNHAPPY). #2 MÉDIO — concorrência
  cross-equipamento simultânea sem falso-412 (teste de carga novo). #3 MÉDIO — `equipamento_recebimento_id`
  é 1 por OS; cl. 7.5 ISO 17025 pode exigir recebimento POR INSTRUMENTO → **acionar `consultor-rbc-iso17025`**.

**Decisão de sequenciamento (técnica, feedback_ordem_dependencia — peça compartilhada feita 1x):**
abrir frente **`os-multi-equipamento`** (ADR + retrofit cirúrgico OS + envelope header→item) ANTES de
`orcamentos` chegar em P3. A spec de orcamentos sobe para v2 já consumindo o envelope por item.

## Tech-lead — TL-ORC-01..11 (APROVA COM CORREÇÕES; 3 bloqueantes resolvidos por R-ORC-1/3 + frente OS)

- **TL-ORC-01 (crítico)** orçamento por catálogo × OS exige equipamento → resolvido por R-ORC-1 (equipamento
  no orçamento) + R-ORC-3 (N equipamentos) + frente os-multi-equipamento (envelope por item).
- **TL-ORC-02** análise crítica sem dados (grandeza/faixa/executor) → grandeza/faixa vêm do EQUIPAMENTO
  (agora identificado no item, R-ORC-1); **`rt_competencia_cobre` SAI da análise do orçamento** (não há
  executor designado na fase comercial — pertence à atribuição da OS) ou vira variante "existe ALGUM RT
  competente no tenant p/ a grandeza".
- **TL-ORC-03** ninguém fecha `aprovado_pendente_os→convertido`: a OS NÃO publica `OS.Aberta` de volta hoje
  → **fatia na frente os-multi-equipamento/OS publica `OS.Aberta` (outbox)** + consumer no orçamento.
- **TL-ORC-04 (ALTO)** idempotência: NÃO é `causation_id+acao` no consumer (é `event_id` no consumer +
  `(causation_id,acao)` no outbox). Publicar com `causation_id=orcamento_id` (estável) → outbox dedup.
  Corrigir texto da spec.
- **TL-ORC-05 (ALTO)** enum `tipo_atividade_alvo` (orçamento: manutencao, OUTRO) ≠ `TipoAtividade` (OS:
  manutencao_corretiva/preventiva, sem OUTRO) → cravar tabela de tradução; manutenção default corretiva;
  remover OUTRO do enum de atividade-alvo (itens comerciais não têm tipo_atividade_alvo).
- **TL-ORC-06 (ALTO)** `calcular_precos` retorna `CalculoPrecoResultado` (cesta) com `PrecoResolvido`
  embutido em `ItemCalculado` JUNTO de margem/custo → persistir SÓ `PrecoResolvido`+`preco_final`+
  `desconto_pct`+`semaforo` no item; **NUNCA margem/custo no snapshot** (vazamento no PDF cliente).
- **TL-ORC-07 (ALTO)** endpoint público sem X-Tenant-ID: galinha-ovo (ler link precisa tenant) → token
  resolve tenant server-side (HMAC `tenant_id+orcamento_id+nonce` OU lookup token→tenant sem RLS) +
  teste cross-tenant + pentest pré-tenant-pago.
- **TL-ORC-11 (MÉDIO→ALTO)** falta entidade `AnaliseCriticaOrcamento` (gera o `analise_critica_id` que o
  envelope exige) → adicionar ao modelo (WORM: perfil_no_evento, veredito, itens_avaliados, snapshot_hash).
- Médios: TL-ORC-08 (numeração — decisão: **densa por tenant, advisory lock**, molde ADR-0080; orçamento é
  doc comercial, cliente espera sequencial limpo), TL-ORC-09 (resolver batch anti-N+1 + assertNumQueries),
  TL-ORC-10 (`padrao_disponivel` em perfil A = ressalva forte, nunca silêncio).

## Advogado — ADV-ORC-01..10 (APROVA COM CORREÇÕES; congelamento respeitado)

**Código JÁ (não espera GATE):**
- ADV-ORC-04 `Aprovacao.lgpd_aceite` grava `versao_termo`+`texto_hash` (não só boolean — prova do consentido).
- ADV-ORC-05b PII do aprovador (`nome_aprovador`/`email_aprovador`) **cifrada por KMS-tenant** (não claro/hash —
  tenant precisa exibir "quem aprovou"; crypto-shredding cobre esquecimento).
- ADV-ORC-05a teste INV-ANON-001 explícito do par `cliente_referencia_hash` (Padrão A não dispara hook auto).
- ADV-ORC-06 consumer `Cliente.Anonimizado` POR ESTADO: rascunho/enviado → cancela+revoga LinkPublico;
  aprovado+ → preserva (registro probatório). **Ciência ao Roldão:** orçamento enviado de cliente anonimizado
  some/é cancelado (correto, mas surpreende).
- ADV-ORC-08a token `secrets.token_urlsafe(32)` (≥128 bits); expiração checada no GET **e** POST.
- ADV-ORC-09 serializer público **allowlist** + teste anti-vazamento (nunca margem/comissão/custo/observacoes).
- ADV-ORC-01 apontador-PII específico na spec (não RAT — permitido).
**[OAB-PRE-PROD] (congelado, antes do 1º cliente externo):** texto do checkbox de consentimento; nível do
aceite eletrônico Lei 14.063/2020; `ip_hash` vs Marco Civil art. 15.
**JÁ correto:** envelope com `cliente_referencia_hash` (sem PII em claro); `ip_hash`; ReferenciaPIIAnonimizavel;
eventos análise crítica WORM. **GATE-LGPD-RAT-CONSOLIDACAO:** RAT aprovação · retenção orçamento · DPIA tela pública.

## Próximos passos (ordem cravada)

1. **FRENTE `os-multi-equipamento`** (ADR + retrofit cirúrgico OS + envelope header→item + `OS.Aberta` de
   volta) — ritual proporcional; acionar `consultor-rbc-iso17025` (recebimento por instrumento cl. 7.5).
2. **orcamentos spec v2** consumindo o envelope por item + todas as correções TL/ADV acima.
3. P3 plan/tasks → implementação → P9.
