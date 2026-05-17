---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
---

# Contrato Exports — Qualidade

## E-QUA-01 — Dossiê de NC (PDF — uso em auditoria CGCRE)
- **Conteúdo:** Identificação NC + descrição + evidências + 5 Porquês + plano de ação completo (tarefas + evidências) + revisão de eficácia + audit trail.
- **Formato:** PDF/UA (INV-016) — assinável digitalmente.
- **Uso:** Auditoria CGCRE (cl. 7.10, 8.7) + auditoria interna.

## E-QUA-02 — Lista de NC (Excel)
- Colunas: Nº, Data, Origem, Severidade, Status, Instrumento/Padrão, Responsável, Dias em aberto, Causa-raiz, Plano de ação resumido, Eficácia confirmada.
- Filtros: Período, Status, Severidade, Origem.
- Uso: Análise crítica pela direção (cl. 8.9 — MVP-2 estruturado; MVP-1 export ad-hoc).

## E-QUA-03 — Indicadores de qualidade (PDF/Excel — input pra análise crítica)
- Período: Mês/Trimestre/Ano.
- **Conteúdo:**
  - Nº total de NC por severidade
  - Tempo médio de resolução
  - % NC reincidente (mesma causa < 90 dias)
  - NC por origem (auditoria, reclamação, PT, verificação intermediária, etc)
  - NC por instrumento/padrão (top 10)
  - NPS médio + classificação
  - Reclamações × NC virada
- Uso: Análise crítica pela direção (cl. 8.9).

## E-QUA-04 — Reclamações (Excel)
- Colunas: Nº, Data, Cliente, OS, Canal, Descrição, Status, NC vinculada.

## E-QUA-05 — NPS detalhado (Excel + dashboard PDF)
- Colunas: Data envio, OS, Cliente, Score, Classificação, Comentário, Reclamação aberta.

## E-QUA-06 — Documentos da qualidade (manifesto + ZIP)
- Manifesto PDF lista versões vigentes (Manual + POPs) com versão + data efetivação.
- ZIP com PDFs todos.
- Uso: Auditoria.

## E-QUA-07 — Bloqueios de emissão por INV-012 (Excel)
- Auditoria: tentativas bloqueadas por mês + por instrumento + duração do bloqueio.
- Uso interno do tenant + investigação Aferê em incidente.

## Mascaramento LGPD

- Nome do cliente em E-QUA-04/05: mascarado pra papéis read-only sem necessidade (PII).
- Comentário NPS: tratamento como dado pessoal (consentimento implícito ao responder; LGPD art. 7).

## Auditoria

Todo export grava: usuário, timestamp, escopo, filtros, contagem de linhas (INV-001 + cl. 7.11 ISO 17025).

## Formatos

XLSX, CSV UTF-8 BOM, PDF/UA, ZIP.

## Não-existem MVP-1

- Cartas de controle (PNG/PDF) — MVP-2.
- Cpk/Cp por instrumento — MVP-2.
- Dossiê CGCRE pré-montado em 1 clique — V2.
- Relatório CAPA estilo FDA — V2 (cliente farma TOP).
- Matriz quantitativa de risco — V2.

## Pré-dossiê CGCRE (V2)

Em V2, agregação de:
- Manual da qualidade vigente + POPs vigentes
- Todas NC do período + status
- Plano de auditoria interna
- Análise crítica pela direção
- Resultados PT (INV-023)
- Histórico de verificações intermediárias (INV-022)

Em PDF único com índice — meta: pronto em < 1 dia (vs hoje ~ 1 semana).
