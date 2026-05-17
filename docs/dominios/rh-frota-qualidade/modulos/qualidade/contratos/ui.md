---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
---

# Contrato UI — Qualidade

## Telas MVP-1

### T-QUA-01 — Painel da qualidade (home P-QUA-01)
- Cards: NC abertas (por severidade), Revisões vencendo, Reclamações em triagem, NPS médio últimos 30d.
- Lista priorizada: NC Críticas abertas no topo.

### T-QUA-02 — Nova NC
- **Campos:** Descrição, Origem (dropdown), Severidade, Instrumento/OS/Certificado/Padrão afetado (busca), Evidência (anexo múltiplo), Responsável.
- **Validação:** Severidade CRITICA → painel mostra aviso vermelho "Esta NC bloqueia emissão de certificado que use o instrumento/padrão selecionado até ser fechada (regra ISO 17025)."
- **Tempo alvo:** Form submit em ≤ 2 min.

### T-QUA-03 — Detalhe NC
- **Seções:** Identificação, 5 Porquês, Plano de ação, Revisão de eficácia, Audit trail.
- **5 Porquês:** Formulário guiado com 5 perguntas "Por quê?" + campo "causa-raiz final". Bloqueio de avanço (status EM_ACAO) sem todos preenchidos em CRITICA/MAIOR.
- **Plano de ação:** Lista de tarefas com responsável + prazo + status + evidência. Botão "Concluir tarefa" exige anexo.
- **Revisão de eficácia:** Botão "Agendar revisão" exige data futura. Próximo ao prazo, alerta sobe pra painel.
- **Audit trail:** Linha do tempo de todas alterações (INV-001).

### T-QUA-04 — Reclamações (fila P-QUA-03 Andréia / P-QUA-01)
- Lista filtrada por status.
- **Cadastro rápido:** Cliente (busca), OS (link opcional), Descrição livre, Canal, Severidade percebida. Botão "Enviar pra qualidade".
- **Triagem (P-QUA-01):** botões "Abrir NC" (wizard preenche origem=RECLAMACAO), "Improcedente" (com justificativa), "Resolvida sem NC" (com texto).

### T-QUA-05 — NPS
- **Configuração:** Quando enviar (X dias após OS concluída), canal (e-mail/WhatsApp).
- **Tela do cliente:** 1 pergunta "0-10, recomendaria?" + comentário opcional. Cliente vê 1 botão grande.
- **Detrator (0-6) com comentário:** Wizard pergunta ao tenant: "Cliente foi detrator com comentário. Abrir como reclamação?" (1 clique).

### T-QUA-06 — Riscos e Oportunidades (cl. 8.5)
- Cadastro livre. MVP-1 sem matriz quantitativa.

### T-QUA-07 — Documentos da qualidade (Manual + POPs)
- Lista + upload + histórico de versões. Nova versão = novo upload (cl. 8.3).

### T-QUA-08 — Bloqueio de emissão (mostrado em outro módulo, mas regra vem daqui)
- Quando técnico tenta emitir certificado e há NC ativa, modal:
  > "Emissão bloqueada. O instrumento [X] está com Não Conformidade aberta (NC-2026-NNN, severidade Crítica). Antes de emitir, a NC precisa ser resolvida. Ver NC."
- Link direto pra T-QUA-03.

## Mensagens (linguagem sem jargão)

| Erro | Mensagem na tela |
|---|---|
| INV-012 bloqueia emissão | "Não dá pra emitir o certificado: o instrumento tem uma Não Conformidade aberta (regra de qualidade ISO). Resolva a NC antes." |
| 5 Porquês incompleto | "Pra avançar com uma NC dessa gravidade, preencha os 5 Porquês até chegar na causa-raiz." |
| Fechar NC sem eficácia agendada | "Antes de fechar, agende uma data pra verificar se a solução realmente funcionou (regra ISO)." |
| Eficácia vencida | "A verificação de eficácia da NC #NNN venceu. A NC voltou a aparecer como pendente. Realize a verificação." |

## Acessibilidade

WCAG 2.1 AA (INV-016). Formulários de 5 Porquês com labels claras, navegação por teclado, leitor de tela.

## Componentes reutilizáveis

- `<BadgeSeveridade severidade="..." />`
- `<WorkflowNc nc=... />` — visualização da máquina de estados.
- `<HistoricoAuditoria entidade="nc" id="..." />`
