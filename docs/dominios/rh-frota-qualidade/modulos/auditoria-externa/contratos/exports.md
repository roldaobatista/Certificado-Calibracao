---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
---

# Contratos de Export — Módulo Auditoria Externa

> Exports do módulo: relatórios, matrizes, gap reports, dossiês. Não há export regulado fiscalmente.

---

## Exports

### Export 1: Relatório Final de Auditoria (PDF)
**Propósito:** consolidação completa da auditoria — entregue à diretoria e arquivado.
**Formato:** PDF.
**Regulado?:** não fiscalmente; mas é registro exigido por ISO 17025 cláusula 8.4 (controle de registros).
**Validador externo:** —
**Template/Schema:** template HTML→PDF customizável por norma.
**Campos obrigatórios:** identificação auditoria (norma, organismo, datas, escopo), responsável geral, equipe envolvida, checklist com status final, lista de apontamentos (por tipo), planos de ação (com status atual), conclusão.
**Campos opcionais:** anexos (fotos, planilhas de evidência).
**Assinatura digital:** opcional (A3 do RQ — ADR-0009 via Web PKI Lacuna).
**Imutabilidade pós-emissão:** sim — hash gravado (`INV-NNN`).
**Retenção:** ≥8 anos (ISO 17025 cláusula 8.4); ver `../../../conformidade/comum/retencao-matriz.md`.

**Exemplo (estrutura):**
```
Auditoria Externa Nº 2026-001
Norma: ABNT NBR ISO/IEC 17025:2017
Organismo: CGCRE/INMETRO
Período: 15-17/11/2026
Escopo: Calibração de balanças classe III

Checklist (143 requisitos):
  Atendidos: 139 (97.2%)
  Parciais: 3
  Não atendidos: 1

Apontamentos:
  NC Maior: 0
  NC Menor: 2
  Observações: 4
  Oportunidades: 7

Planos de Ação:
  Fechados: 0 (auditoria recém-concluída)
  Em andamento: 6

Hash: a1b2c3d4...
```

---

### Export 2: Matriz de Conformidade (PDF/CSV/XLSX)
**Propósito:** snapshot da matriz norma × status, útil pra revisão gerencial e mostrar a cliente.
**Formato:** PDF (apresentação), CSV/XLSX (análise).
**Regulado?:** não.
**Campos:** norma, cláusula, requisito, status, % conformidade, última evidência, responsável, prazo próximo doc.
**Snapshot:** sim (carimba data/hora). Snapshots diários armazenados pra rastreabilidade.

---

### Export 3: Plano de Ação (PDF por NC ou consolidado)
**Propósito:** documento formal de resposta à NC, exigido pelo organismo no follow-up.
**Formato:** PDF.
**Regulado?:** não, mas exigido por organismos certificadores.
**Campos:** identificação NC, descrição auditor, causa raiz (com 5-porquês expandidos se NC maior), ação corretiva, responsável, prazo, evidência de fechamento, status, aprovador.
**Assinatura digital:** opcional A3 do RQ.

---

### Export 4: Gap Report do Drill (PDF/XLSX)
**Propósito:** resultado da simulação interna.
**Formato:** PDF ou XLSX.
**Regulado?:** não (documento interno).
**Campos:** drill_id, auditor simulado, data, lista de gaps com criticidade, recomendações.

---

### Export 5: Dossiê CGCRE (PDF consolidado)
**Propósito:** pacote pré-auditoria entregue ao auditor CGCRE.
**Formato:** PDF (ZIP de PDFs anexos).
**Regulado?:** sim em conteúdo (cláusulas da ISO 17025) — não em formato (não há schema oficial).
**Validador externo:** auditor humano (não automatizável).
**Campos:** carta de apresentação, escopo, organograma, lista equipe + qualificações, lista equipamentos + status calibração, procedimentos vigentes, registros últimos 12 meses, planos de ação abertos.
**Assinatura digital:** A3 do RT (ADR-0009).
**Imutabilidade:** sim após entrega.

---

### Export 6: Painel de Prontidão (PDF snapshot)
**Propósito:** comprovante semanal/mensal pro Roldão arquivar.
**Formato:** PDF.
**Campos:** semáforo por norma + tendência (4 semanas) + top ações pendentes.

---

## Exports inter-módulos

- Relatório Final → arquivado em módulo Qualidade (registros controlados).
- Planos de Ação → referenciados em módulo Qualidade.
- Evidências apresentadas podem vir de qualquer módulo (Calibração, Treinamentos, Frota, etc.).
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Conteúdo segue versão da norma vigente (ex: migração ISO 17025:2017 → versão futura).
- Histórico mantém versão da norma quando auditoria ocorreu.

## Como esta lista evolui

- Export novo → adicionar.
- Mudança em template → bump CHANGELOG.
- Export `@deprecated` → janela de migração.
