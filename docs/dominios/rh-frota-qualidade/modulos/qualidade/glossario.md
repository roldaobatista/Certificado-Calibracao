---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
---

# Glossário — Qualidade

| Termo | Definição |
|---|---|
| **NC (Não Conformidade)** | Desvio detectado em processo, produto ou serviço (ISO 17025 cl. 7.10). Toda NC tem origem, descrição, severidade, status e responsável. **NC aberta em instrumento bloqueia emissão (INV-012).** |
| **Origem da NC** | De onde a NC veio: auditoria interna, reclamação de cliente (NPS), inspeção de padrão, falha em PT (proficiency testing — INV-023), retorno de calibração, autoavaliação. |
| **Severidade** | Crítica (bloqueia emissão), Maior (afeta resultado mas contornável), Menor (cosmética/processual). |
| **5 Porquês** | Técnica de análise de causa-raiz: perguntar "por quê?" 5x até chegar à causa estrutural. Obrigatório em NC Crítica e Maior. |
| **Plano de ação** | Conjunto de ações com responsável + prazo + evidência pra eliminar causa-raiz da NC (cl. 8.7). |
| **Ação corretiva** | Ação tomada pra eliminar a causa da NC já ocorrida (cl. 8.7). |
| **Ação preventiva** | Ação pra reduzir risco de NC futura. Em ISO 17025:2017 foi absorvida em "ações pra abordar riscos e oportunidades" (cl. 8.5). |
| **Revisão de eficácia** | Após X dias da ação corretiva, verificar se NC realmente foi eliminada (cl. 8.7 item 8.7.3). Sem revisão, NC permanece "fechada-com-pendência". |
| **Auditoria interna** | Avaliação periódica do sistema de gestão (cl. 8.8 — embora MVP-1 só cobre NC; auditoria interna completa = V2). |
| **NPS (Net Promoter Score)** | Métrica de satisfação pós-serviço (pergunta "0-10, recomendaria?"). MVP-1 = pergunta + classificação detrator/neutro/promotor. |
| **Reclamação** | NPS detrator + texto OU canal dedicado. Toda reclamação vira NC candidata (cl. 7.9 ISO 17025). |
| **Riscos e oportunidades (cl. 8.5)** | Registro de riscos identificados + tratamento. MVP-1 = registro livre; matriz de risco completa = V2. |
| **CAPA** | Corrective And Preventive Action (terminologia FDA/farma — equivalente a ações corretivas + ações pra abordar riscos). |
| **Controle estatístico / cartas de controle** | Análise estatística de tendência de resultados de medição (Shewhart, CUSUM). **NON-GOAL MVP-1.** MVP-2. |
| **Verificação intermediária** | Conferência periódica de padrão entre calibrações (INV-022). Resultado fora do esperado abre NC automaticamente. |
| **Manual da qualidade** | Documento mestre que descreve o sistema. MVP-1 = upload de PDF + versionamento simples. |
| **Procedimento (POP)** | Documento operacional. MVP-1 = upload + versionamento. |

## Referências

- ISO/IEC 17025:2017 cl. 7.9 (reclamações), 7.10 (NC), 8.5 (riscos), 8.6 (melhoria), 8.7 (ações corretivas), 8.8 (auditoria interna), 8.9 (análise crítica)
- `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md`
- INV-012 (NC bloqueia emissão); INV-022 (verificação intermediária)
- P-RFQ-02 responsável pela qualidade
