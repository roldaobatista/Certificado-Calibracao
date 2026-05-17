# .agent/SESSION.md — handoff entre sessões

> **Pra quê:** capturar "onde paramos / próximo passo / bloqueio" entre sessões de agente. Mais confiável que só auto-memory.
>
> **Quem mantém:** o próprio agente atualiza no final de cada sessão produtiva.
> **Hierarquia:** CURRENT.md (agora) > SESSION.md (histórico curto) > auto-memory do Claude Code (preferências do humano).

---

## Última sessão

**Data:** 2026-05-16 (sessão Rodada 0 batch 1)
**Agente:** Claude Code (Opus 4.7)
**Roldão presente:** sim, ativo (contribuiu com lista de 6 concorrentes adicionais durante a execução)

### Onde paramos
**Rodada 0 batch 1 EXECUTADA.** Os 4 artefatos que o agente faz sozinho foram preenchidos com conteúdo denso baseado em pesquisa pública (16/05/2026):

1. ✅ `docs/discovery/concorrentes.md` — 16 concorrentes BR + 8 internacionais mapeados (calibração ISO 17025) + 5 ERPs horizontais BR (Bling/Tiny/Omie/Conta Azul/Granatum). **Gap "OS + calibração + NFS-e municipal" CONFIRMADO** em 2 ondas de pesquisa independentes.
2. ✅ `docs/discovery/normas-e-regulacao.md` — 15 municípios mapeados para NFS-e, ISO 17025 cláusulas resumidas, RBC/CGCRE atualizado (NIT-DICLA-030 rev. 15), LGPD 2024-2026 (Res. 15/18/19), Bacen/PIX 2025, MOC NF-e 7.0, PCI-DSS 4.0.1. **10 invariantes candidatos identificados** pra `REGRAS-INEGOCIAVEIS.md`.
3. ✅ `docs/discovery/dominio-de-negocio.md` — visão geral do setor enriquecida + mapa preliminar de domínios → módulos prováveis (entrada pra `faseamento-modulos.md`).
4. ✅ `docs/discovery/riscos.md` — refinado com 11 riscos novos (R16–R26). Top 12 atualizado: R18 (NIT-DICLA-030 8.2.6) entrou no topo com score 25.
5. ✅ `docs/governanca/auditoria-decisoes-autonomas.md` — entrada nova com achados estratégicos da pesquisa.

### Próximo passo lógico
**Rodada 0 batch 2** — agente sozinho ainda consegue:
- `docs/discovery/personas-detalhadas.md` (6 papéis identificados em `dominio-de-negocio.md`)
- `docs/discovery/jobs-to-be-done.md`
- `docs/discovery/jornada-atual-sem-produto.md` (status quo — planilha + WhatsApp + Bling)

Depois Roldão precisa entrar em cena para:
- Revisar os 4 artefatos do batch 1 (especialmente os itens marcados `[a confirmar]` e `[Roldão validar]`)
- Receber e revisar `docs/discovery/treinamento-entrevista-roldao.md` (a criar)
- Fazer 2 entrevistas piloto (revisadas por auditor)
- Marcar onda 1: 3 entrevistas com donos de OUTRAS empresas

### Bloqueio atual
Nenhum técnico. Próxima decisão é do Roldão (autorizar batch 2 vs revisar batch 1 primeiro).

### Decisões tomadas nesta sessão
- Pesquisa via 4 subagentes paralelos (3 iniciais + 1 follow-up após lista do Roldão).
- Reconhecimento de gaps em fontes: itens `[a confirmar]` marcados explicitamente, não inventados.
- Correções factuais: SCAN morto desde 2014, RIR/99 revogado pelo RIR/2018, mito "72h GDPR" derrubado (3 dias úteis), ILAC G8 ≠ validação de software, myLIMS ≠ PerkinElmer, 3 produtos chamados "AutoLab" no Brasil.
- Estrutura de `concorrentes.md` segmentada em: internacionais → nacionais → ERPs horizontais BR → bônus do gap.

### Achados estratégicos pra Roldão olhar
- **GAP CONFIRMADO** "OS + calibração ISO 17025 + NFS-e municipal multi-prefeitura" — único player com NFS-e nativa é FP2 (regional, Santa Maria/RS). Tese central do produto sustentada.
- **R18 = risco mais grave** (score 25): NIT-DICLA-030 rev. 15 item 8.2.6 rejeita certificado sem cadeia de rastreabilidade + incerteza. Vira INV-CALIB-001.
- **Concorrente nacional mais perigoso:** Cali LAB/WEB (homologado CERTI, base RBC instalada). Vantagem: ainda é desktop-first sem fiscal.
- **Janela competitiva:** se Cali/Metroex fechar parceria com Bling/Omie pra fiscal, perdemos diferencial #1.

---

## Histórico (últimas sessões, ordem cronológica reversa)

### Sessão 2026-05-16 (Rodada 0 batch 1) — esta
4 artefatos do Discovery preenchidos. 16 concorrentes BR + 8 internacionais mapeados. 15 municípios cobertos. 11 riscos novos. Gap central do produto confirmado em 2 ondas.

### Sessão 2026-05-16 (estrutura inicial)
Criada estrutura de documentação seguindo v5: ~30 arquivos de fundação + 15 cabeçalhos de Discovery prontos pra preencher.

### Sessão 2026-05-16 (discussão de docs)
Passou por v3 → v4 → v5. Auditorias com 10 agentes (rodada 1 sobre v2 e rodada 2 sobre v4). Revelações grandes: founder is customer, N módulos a descobrir, escopo é ERP completo (não só calibração).

### Sessão 2026-05-16 (anterior, mesmo dia)
Ambiente Claude Code blindado, hooks reescritos com perl/JSON::PP + 23 testes verdes.

### Sessão 2026-04-19
Renomeação Kalibrium → Aferê.
