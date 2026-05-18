---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
diataxis: explanation
audiencia: agente
---

# PRD — Qualidade

## Problema

Tenant ISO 17025 (e tenant que quer chegar lá) tem 3 dores:
1. **NC em Excel separado** — Responsável pela qualidade (P-RFQ-02) registra em planilha sem rastro pra OS/certificado/instrumento. Em auditoria CGCRE não consegue mostrar "causa-raiz + plano + eficácia".
2. **NC não bloqueia emissão** — Resultado: certificado sai com instrumento em NC aberta → cliente recebe certificado de padrão "rastreável mas com NC aberta" → potencial nulidade retroativa (INV-012 é exatamente isso).
3. **NPS perdido** — Cliente reclama no WhatsApp; ninguém anota; reclamação não vira NC; problema sistêmico não é detectado.

## Goals MVP-1

- CRUD de NC: origem, descrição, instrumento/OS/certificado afetado, severidade, evidência (anexo).
- **INV-012 ativa:** NC Crítica em instrumento → bloqueia emissão de certificado que use esse instrumento, até NC fechada com revisão de eficácia.
- 5 Porquês obrigatório em Crítica + Maior.
- Plano de ação: tarefas com responsável + prazo + evidência de cumprimento.
- Revisão de eficácia: após plano concluído, agendar revisão em N dias; sem revisão dentro do prazo, NC volta a "aberta-com-pendência".
- NPS pós-serviço: pergunta automática (e-mail/WhatsApp) X dias após OS concluída; resposta classificada; detrator → reclamação candidata → wizard "abrir NC?".
- Reclamações de cliente: canal único; toda reclamação vira candidata a NC.
- Registro de riscos e oportunidades (cl. 8.5): formulário livre + ligação opcional a NC.
- Upload + versionamento simples de manual da qualidade + POPs.

## Goals MVP-2

- Controle estatístico (cartas de controle Shewhart).
- Auditoria interna estruturada (cl. 8.8).
- Análise crítica pela direção (cl. 8.9).
- Matriz de risco quantitativa (probabilidade × impacto).
- Tendência de NC por causa-raiz / por instrumento / por técnico.
- Pré-dossiê de auditoria CGCRE em 1 clique.

## Non-goals MVP-1

- **Controle estatístico** — MVP-2.
- **Cartas de controle (Shewhart, CUSUM)** — MVP-2.
- **Auditoria interna estruturada** — MVP-2.
- **CAPA workflow completo estilo farma/FDA** — V2 (cliente farma TOP = V2 — INV-018).
- **Integração ANVISA/MAPA** — V2.
- **Matriz de risco quantitativa** — V2.
- **Notificação automática ANPD (LGPD)** — coberto em módulo conformidade separado (não aqui).

## Critérios de aceitação (binários)

- [ ] AC-QUA-01: Abrir NC Crítica em instrumento bloqueia emissão de certificado que use esse instrumento (INV-012 — hook).
- [ ] AC-QUA-02: Fechar NC Crítica sem 5 Porquês preenchido é bloqueado.
- [ ] AC-QUA-03: Fechar NC sem revisão de eficácia agendada é bloqueado.
- [ ] AC-QUA-04: NC com revisão de eficácia vencida (não realizada no prazo) volta automaticamente a status "aberta-com-pendência".
- [ ] AC-QUA-05: Detrator NPS abre wizard "abrir NC?" (não obrigatório, mas sugerido com 1 clique).
- [ ] AC-QUA-06: Reclamação registrada cria NC candidata (status "triagem") visível pro responsável pela qualidade.
- [ ] AC-QUA-07: Verificação intermediária de padrão fora da tolerância (INV-022) abre NC Crítica automática nesse padrão.
- [ ] AC-QUA-08: Manual da qualidade tem histórico de versões (cada upload é versão nova) — cl. 8.3 controle de documentos.
- [ ] AC-QUA-09: Conformidade WCAG 2.1 AA (INV-016).
- [ ] AC-QUA-10 (ADR-0016 INV-INT-013): **NC notifica cliente externo automaticamente** quando `entidade_origem_tipo IN ("padrao", "procedimento") AND bloqueia_emissao=true`. Sistema identifica clientes cujos equipamentos foram calibrados com esse padrão/procedimento nos últimos 12 meses, publica `Qualidade.NCNotificacaoCliente(cliente_id, nc_id, equipamentos_afetados, impacto_descricao)` por cliente. Consumer `comunicacao-omnichannel` envia WhatsApp + e-mail; consumer `portal-cliente` cria entry timeline 360°. Quando NC fechada → publica `Qualidade.NCResolucaoNotificada` similar. Payload carrega apenas dados mínimos (modelo+série, sem PII cruzado).
- [ ] AC-QUA-11 (ADR-0014 INV-INT-002): Quando RT signatário é desligado (consumir `Colaborador.Desligado` com `is_rt_signatario=true`), abrir NC sistêmica "RT desligado, designação necessária pra tipos X, Y, Z" + escalação automática pra Diretor designar substituto.
- [ ] AC-QUA-12 (ADR-0016 fluxo M4): Quando `Proficiencia.EscoreInsatisfatorio` chega, consumer `qualidade` abre NC automática vinculada a `Calibracao.NecessidadeRevisaoRetroativa(certificados=[ids])` — RT revisa lista de certs emitidos no período do PT que usam mesma grandeza + padrões.

## Discovery / referências

- INV-012, INV-022; cl. 7.9, 7.10, 8.5, 8.6, 8.7
- P-RFQ-02 responsável pela qualidade; Persona 16 Andréia CS L1
- `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md`
