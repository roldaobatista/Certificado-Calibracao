# PG-RIS-001 — Gestão de Riscos e Oportunidades

| Código | PG-RIS-001 | Revisão | 00 | Data | __/__/____ |
|--------|------------|---------|----|------|------------|

## 1. Objetivo
Estabelecer a sistemática para identificação, análise, avaliação, tratamento e monitoramento de riscos e oportunidades que possam afetar a validade dos resultados, a imparcialidade ou o sistema de gestão, atendendo aos itens 4.1 e 8.5 da ABNT NBR ISO/IEC 17025:2017.

## 2. Escopo
Aplica-se a todas as atividades do laboratório, contemplando:
- Riscos à imparcialidade.
- Riscos operacionais (técnicos, de pessoal, equipamento, instalação).
- Riscos contratuais e legais.
- Riscos de TI/dados.
- Oportunidades de melhoria.

## 3. Metodologia
Não há método obrigatório. Adota-se análise qualitativa simples, baseada em **probabilidade × severidade**.

### 3.1 Probabilidade (P)
| Nível | Descrição | Critério |
|-------|-----------|----------|
| 1 | Rara | < 1 % ao ano |
| 2 | Improvável | 1–10 % ao ano |
| 3 | Possível | 10–50 % ao ano |
| 4 | Provável | 50–90 % ao ano |
| 5 | Quase certa | > 90 % ao ano |

### 3.2 Severidade (S)
| Nível | Descrição |
|-------|-----------|
| 1 | Insignificante — sem impacto técnico/legal |
| 2 | Menor — impacto reversível, sem afetar resultados liberados |
| 3 | Moderada — necessidade de retrabalho ou comunicação ao cliente |
| 4 | Maior — resultado incorreto liberado; recall localizado |
| 5 | Crítica — recall amplo; perda de acreditação; impacto legal/saúde |

### 3.3 Nível de risco (NR = P × S)
| Faixa | Classificação | Tratamento |
|-------|---------------|------------|
| 1–4 | Baixo | Aceitar e monitorar |
| 5–9 | Moderado | Avaliar tratamento; planejar quando viável |
| 10–14 | Alto | Tratar com plano definido |
| 15–25 | Crítico | Tratar imediatamente; ação prioritária da direção |

## 4. Matriz de Riscos (FR-RIS-001)

| ID | Categoria | Descrição do risco | Causa | Consequência | P | S | NR | Controles atuais | Tratamento | Responsável | Prazo | Status |
|----|-----------|-------------------|-------|--------------|---|---|----|------------------|------------|-------------|-------|--------|
| R-01 | Imparcialidade | Cliente é também fornecedor | Relacionamento comercial | Pressão sobre resultado | 2 | 4 | 8 | Segregação de funções | Declaração formal | Direção | __/__/__ | Em andamento |
| R-02 | Equipamento | Falha de balança crítica | Desgaste | Atraso e retrabalho | 3 | 3 | 9 | Manutenção preventiva | Backup + plano de contingência | Gerente técnico | | |
| R-03 | Pessoal | Saída de signatário único | Rotatividade | Paralisação do escopo | 2 | 5 | 10 | Substituto qualificado | Plano de sucessão | Qualidade | | |
| R-04 | TI | Perda de dados do LIMS | Falha de hardware | Perda de registros | 2 | 5 | 10 | Backup diário | Teste de restore trimestral | TI | | |
| R-05 | Método | Mudança em norma técnica | Atualização externa | Não conformidade técnica | 3 | 4 | 12 | Monitoramento de normas | Procedimento de atualização | Qualidade | | |

## 5. Matriz de Oportunidades

| ID | Descrição | Benefício esperado | Ação | Responsável | Prazo |
|----|-----------|-------------------|------|-------------|-------|
| O-01 | Ampliar escopo X | Novo mercado | Implementar e validar método | | |
| O-02 | Automatizar planilhas | Reduzir erro humano | Avaliar LIMS | | |

## 6. Periodicidade
- Revisão **anual** mínima.
- Revisão extraordinária após: mudança organizacional, incidente, novo serviço, novo equipamento crítico, mudança normativa.

## 7. Comunicação
Resultados da análise de riscos são entradas obrigatórias da **Análise Crítica pela Direção** (item 8.9 da norma).

## 8. Histórico de revisões
| Revisão | Data | Descrição |
|---------|------|-----------|
| 00 | | Emissão inicial |
