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
