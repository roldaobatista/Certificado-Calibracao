# Auditoria de decisões autônomas dos agentes

> **Lista do que os agentes decidiram SEM consultar o Roldão** (dentro dos `limites-autonomia.md`). Roldão lê pra estar informado; pode discordar (vira ADR de reversão).
>
> Auditor 2 v2 alertou: sem essa filtragem dedicada, autonomia vira caixa-preta.

---

## Formato de cada entrada

```markdown
### YYYY-MM-DD — [Resumo em PT-BR de 1 linha]
- **Decisão:** [o que foi decidido]
- **Por quê:** [razão objetiva]
- **Quem decidiu:** [agente Claude Code / Codex CLI / Auditor X]
- **Sessão:** [hash ou link pra `.agent/SESSION.md` da época]
- **Impacto:** [reversível / irreversível / parcialmente reversível]
- **Caso-limite (do limites-autonomia)?** [Caso N — sim/não] (se sim, deveria ter escalado — bug do agente)
- **Link pra ADR (se criado):** [path]
- **Roldão revisou?** ⏳ pendente / ✅ aprovou / ❌ discordou (ver ADR-NNNN de reversão)
```

---

## Entradas (cronológico reverso)

### 2026-05-16 — Roldão aprovou as 9 decisões da auditoria; aplicadas autonomamente
- **Decisão:** Roldão respondeu "ACEITO TUDO" pras 9 decisões pendentes da auditoria do batch 1. Aplicadas em sequência:
  - **D-aud-1** Pricing: R$ 300 → **R$ 500-1.000/mês** com 1 mês grátis. Faixas crescimento (R$ 1.500-3.000) e Pro (R$ 3.000-6.500) também subiram.
  - **D-aud-2** 3 fichas novas em `concorrentes.md` §14: **TOTVS Protheus** (SIGAMNT + SIGATEC + SIGAQMT/Metrologia descoberto), **Qualyteam** (Joinville/SC desde 2008, QMS BR com 400+ clientes), **SAP Business One BR** (via parceiros, R$ 50k-150k implementação).
  - **D-aud-3** Invariante #4 ("software validado") quebrado em INV-004a (deploy só com aprovação RT), INV-004b (revalidação de cálculo de incerteza), INV-004c (versão do software gravada em cada certificado).
  - **D-aud-4** INV-007 (BaaS único) movido pra ADR fiscal (não é invariante); INV-010 a INV-014 novos: retenção 17025, padrão vencido bloqueia emissão, NC bloqueia emissão, confidencialidade 4.2 com log, certificado externo sem incerteza bloqueia. **Total: 14 invariantes** (era 10).
  - **D-aud-5** Domínio Metrologia subdividido em 3: (a) Execução de calibração, (b) Padrões e rastreabilidade, (c) Garantia da validade.
  - **D-aud-6** "Gestão de Competências e Autorizações" promovido ao MVP-1 obrigatório (17025 6.2). Escopo magro: matriz competência × grandeza + validade + autorização por escopo. RH completo (folha, ponto, holerite) fica lazy.
  - **D-aud-7** Domínio "Metrologia Legal" adicionado (IPEMs/RBMLQ-I, Portarias INMETRO 157/2022 balanças + 227/2022 bombas). Confirmar se está no escopo do MVP nas entrevistas (depende se Roldão atende balança comercial / bomba combustível).
  - **D-aud-8** Padronização de IDs de risco aplicada: **R-001 a R-038** sequencial único, coluna Origem adicionada. R-021 marcado DEPRECATED (consolidado com R-033). Tabela completa de mapeamento RC-* → R-* em `riscos.md` e `concorrentes.md` §7.
  - **D-aud-9** **ADR-0000 (Uso de IA) criada** em `docs/adr/0000-uso-de-ia.md` com 5 princípios fundadores: (1) abstração obrigatória de provider, (2) dados de cliente final não vão pra API por padrão, (3) IP do output é do Roldão, (4) hard cap por tenant, (5) sanitização e segregação de input não-confiável.
- **Por quê:** Roldão deu autorização explícita ("ACEITO TUDO"). Aplicação direta sem aguardar item-a-item.
- **Quem decidiu:** Roldão (decisor) + Claude Code (executor) + 4 subagentes auditores (insumo)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16 (auditoria batch 1)
- **Impacto:** reversível (todas as edições versionadas); ADR-0000 é fundadora — reabrir só com ADR de reversão.
- **Caso-limite?** Não — todas as decisões já tinham veredito do Roldão "aceito"
- **Itens deixados em aberto pra entrevista:**
  - D-aud-7 — confirmar se Metrologia Legal está no escopo do MVP (depende se Roldão atende balança/bomba)
  - D-aud-5 — subdivisão de Metrologia em 3 sub-domínios materializa quando o módulo entrar no faseamento (até lá é só nota no mapa)
- **Roldão revisou?** ✅ aprovou em bloco

---

### 2026-05-16 — Auditoria interna do batch 1 + correções factuais aplicadas
- **Decisão:** Roldão pediu "lançar 1 agente por ponto importante pra revisar". Disparei 4 auditores independentes em paralelo:
  - **Auditor 1** — concorrentes.md (achou 2 erros factuais + sugeriu 3 concorrentes ausentes + 5 frases de posicionamento frágeis)
  - **Auditor 2** — normas-e-regulacao.md (achou 4 erros factuais: NIT-DICLA-021 é Rev. 10 e não Rev. 03; DOQ-008 é jun/2020; VIM ainda é JCGM 200:2012; SVC CE/PA → SVC-RS)
  - **Auditor 3** — dominio-de-negocio.md (apontou auditoria Cgcre = 4 anos não 2; CB-25 é Qualidade e não Calibração; glossário só cobre 30%; estoque deveria ser domínio próprio)
  - **Auditor 4** — riscos.md + cross-check (apontou 10 riscos faltando; padronização de IDs; 21 documentos referenciados mas inexistentes)
- **Aplicadas autonomamente (correções factuais confirmadas por fonte):**
  - `concorrentes.md`: data Qualer/MasterControl (03/03/2025); valor Conta Azul (US$ 300 mi/~R$ 1,7 bi, não R$ 2 bi); evidência FP2 regional (4 clientes em Santa Maria/RS); RC-06, RC-07, RC-08, RC-09 adicionados; **Auvo adicionado** (indicação Roldão); **Estoque promovido a domínio próprio** (indicação Roldão + sugestão Auditor 3)
  - `normas-e-regulacao.md`: NIT-DICLA-021 Rev. 10; DOQ-008 jun/2020; VIM JCGM 200:2012; SVC CE/PA → SVC-RS; Brasília = emissor próprio ISSnet + ADN
  - `dominio-de-negocio.md`: Cgcre = ciclo 4 anos com supervisões; CB-25 corrigido (Qualidade, não Calibração) + adicionado IPEMs/RBMLQ-I; estoque promovido a domínio próprio com escopo de WMS
  - `riscos.md`: R27 (prompt injection cliente final, score 25) + R28 (soberania dados Anthropic EUA, score 16) + R29 (bus factor Roldão, score 15); top 12 reorganizado pra top 15 com R27 no #1
  - **Criado `docs/discovery/proximos-artefatos.md`** consolidando os 29 artefatos referenciados pelos 4 docs mas ainda inexistentes (inclui ADR-IA novo recomendado pelo Auditor 4)
- **NÃO aplicadas (ficam pra decisão do Roldão):**
  - Subir piso de pricing R$ 300→R$ 500-1.000 (Auditor 1)
  - Adicionar fichas TOTVS Protheus, Qualyteam, SAP B1 BR (Auditor 1) — mais 3 dossiês
  - Refinar invariante #4 em 3 sub-regras testáveis (Auditor 2)
  - Mover invariante #7 (BaaS único) pra ADR e adicionar invariantes #11-#15 (Auditor 2)
  - Subdividir domínio Metrologia em 3 sub-domínios (Auditor 3)
  - Mover Gestão de Competências pra MVP-1 (Auditor 3 — conflito real com 17025 6.2)
  - Padronizar IDs (R-001 a R-NNN sequencial) (Auditor 4)
  - Criar ADR-IA hoje (Auditor 4)
  - Substituir mitigações "monitorar" por owner + cadência + gatilho (Auditor 4)
  - Adicionar metrologia legal (IPEMs/Portarias 157/2022 e 227/2022) como sub-domínio ou flag (Auditor 3)
- **Por quê:** itens factuais são erros objetivos com fonte — aplicar não muda direção estratégica. Itens não-aplicados envolvem decisões de produto/escopo onde Roldão é o decisor.
- **Quem decidiu:** Claude Code (orquestrador) + 4 subagentes auditores (general-purpose) + Roldão (intervenções: Auvo + estoque domínio próprio)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16 (auditoria batch 1)
- **Impacto:** reversível (todas as edições versionadas no git); não toca decisões fundadoras
- **Caso-limite?** Não — correção de erro factual e adição de risco com mitigação documentada estão dentro da autonomia
- **Achados que viram entrada futura em REGRAS-INEGOCIAVEIS:**
  - R27 → INV-AGENT-001 (input não-confiável de cliente final precisa de hook)
  - R18 (já citado em entrada anterior) → INV-CALIB-001
  - Invariantes propostas em `normas-e-regulacao.md` §8.1 (10 candidatos, 5 mais sugeridos pelo Auditor 2)
- **Roldão revisou?** ⏳ pendente — Roldão precisa decidir os 9 itens não-aplicados acima

---

### 2026-05-16 — Rodada 0 Discovery batch 1 executada (4 artefatos)
- **Decisão:** preencher `concorrentes.md`, `normas-e-regulacao.md`, `dominio-de-negocio.md`, `riscos.md` com conteúdo denso a partir de pesquisa pública. Disparados 3 subagentes paralelos (concorrentes ERP horizontal BR, concorrentes calibração ISO 17025, normas/regulação BR) + 1 subagente extra após Roldão acrescentar 6 nomes novos (CalibraFácil, ABC71, SoftExpert, myLIMS, AutoLab×3, ConfLab). Total: 16 concorrentes brasileiros + 8 internacionais mapeados; 15 municípios prioritários cobertos para NFS-e; 11 riscos novos adicionados (R16–R26).
- **Por quê:** Roldão autorizou início da Rodada 0 e pediu o primeiro batch (artefatos que o agente faz sozinho). Pesquisa pública sem entrevista de cliente está dentro da autonomia. Lista adicional do Roldão veio durante a execução — incorporada em append.
- **Quem decidiu:** Claude Code (Opus 4.7) — orquestrador; subagentes general-purpose pra pesquisa.
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16 (Rodada 0 batch 1)
- **Impacto:** reversível (arquivos podem ser reescritos); decisões fundadoras NÃO foram tocadas
- **Caso-limite?** Não — pesquisa secundária sem mudança de stack ou de invariante
- **Achados estratégicos que podem virar ADR/INV:**
  - **Gap "OS + calibração ISO 17025 + NFS-e municipal" confirmado** em 2 ondas de pesquisa independentes (16 nacionais + 8 internacionais). Único com NFS-e nativo é FP2 Tecnologia (Santa Maria/RS regional). Tese central do produto sustentada.
  - **NIT-DICLA-030 rev. 15 item 8.2.6:** Cgcre não aceita certificado sem resultado de medição + incerteza → vira invariante INV-CALIB-001 (bloqueio na emissão).
  - **Mito "72h GDPR" derrubado:** ANPD Res. 15/2024 é **3 dias úteis**, não 72h corridas. Toda documentação interna precisa usar o termo correto.
  - **Decreto 3000/99 (RIR/99) está REVOGADO desde 2018** (substituído pelo Decreto 9.580/2018 — RIR/2018). Draft anterior do `normas-e-regulacao.md` citava norma morta — corrigido.
  - **SCAN está morto desde 30/09/2014** — só SVC-AN/SVC-RS + EPEC. Quem cita SCAN está com base antiga.
  - **Cutover NFS-e Padrão Nacional:** MEI desde set/2023; municípios desde 01/01/2026; ME/EPP Simples obrigatório em 01/09/2026 (CGSN 189/2026). SP mantém próprio integrado ao ADN; POA desliga DANFSe local em 01/07/2026.
  - **PCI-DSS 4.0.1** vigente desde 31/03/2025 (sem carência). Recomendação: usar PSP/gateway tokenizado → SAQ A.
  - **ILAC G8 trata de regras de decisão, não validação de software** — referências corretas são WELMEC 7.2 / OIML D 31. Roldão precisa confirmar qual quer.
  - **Confusão derrubada:** myLIMS NÃO é PerkinElmer (é Confience/STG Partners); 3 produtos chamados "AutoLab" no Brasil (Arkade, Automa, MRI); ABC71 não compete com lab calibrador (compete com metrologista interno de indústria).
- **Itens [a confirmar] pra Roldão:** Brasília NFS-e modelo de adesão, NIT-DICLA-021 revisão vigente, Enunciado CD/ANPD nº 4, número da IN BCB do PIX, VIM 4ª ed., ILAC G8 vs WELMEC 7.2.
- **Roldão revisou?** ⏳ pendente — Roldão já contribuiu durante a execução com lista de 6 concorrentes adicionais; revisão final dos 4 artefatos pendente.

---

### 2026-05-16 — Estrutura inicial de documentação criada
- **Decisão:** criação de ~33 arquivos de fundação + estrutura de pastas seguindo `documentos-do-projeto.md` v5; ~100 arquivos lazy do v5 NÃO foram criados conforme regra do próprio doc.
- **Por quê:** Roldão autorizou "criar toda estrutura"; agente seguiu regra do doc "não criar template vazio pra preencher depois".
- **Quem decidiu:** Claude Code (Opus 4.7)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16
- **Impacto:** reversível (arquivos podem ser deletados)
- **Caso-limite?** Não — está dentro da autonomia
- **Link pra ADR:** N/A
- **Roldão revisou?** ⏳ pendente (este é o primeiro item da lista)

---

## Como agente atualiza esta lista

A cada decisão autônoma significativa (que valha registrar):
1. Adiciona entrada NO TOPO (cronológico reverso).
2. Atualiza `status-semanal.md` referenciando esta entrada.
3. Atualiza `trilha-auditoria-agentes.md` com detalhe técnico.

## Critério "significativa" pra registrar

- Mudança em arquivo de `REGRAS-INEGOCIAVEIS.md`, `governanca/`, `conformidade/`, `adr/`, `comum/`.
- Mudança em > 5 arquivos numa única sessão.
- Adoção/descontinuação de ferramenta, biblioteca, padrão.
- Decisão arquitetural não-trivial.
- Tudo que poderia ter escalado mas foi decidido autonomamente.

**Não registrar:** correção de typo, atualização de status, edição de comentário.
