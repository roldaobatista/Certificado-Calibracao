---
owner: roldao
revisado-em: 2026-05-23
proximo_review: 2026-08-23
status: draft
modulo: os
dominio: operacao
diataxis: explanation
audiencia: agente
---

# Sagas e integrações inter-modulares — Módulo OS

> Adicionado em 2026-05-23 (Onda 6 saneamento pré-Marco 3 — auditor 5).
> Documenta interações da OS com Cliente / Equipamento / Calibração /
> Financeiro / Agenda / Portal-cliente. Detalhe técnico de payloads em
> `docs/comum/integracoes-inter-modulos.md`.

---

## 1. Saga "Abrir OS a partir de orçamento aprovado"

Atores: Comercial (publica `Orcamento.Aprovado`) → OS (consumer).

1. `Orcamento.Aprovado` chega ao consumer de OS com `correlation_id`,
   `cliente_id`, `equipamento_id`, itens, valores.
2. OS valida tenant + cliente ativo + equipamento ativo (INV-OS-EQP-001
   bloqueia se BAIXADO).
3. OS cria registro RASCUNHO + N AtividadeDaOS (1 por item de serviço).
4. OS publica `OSAberta` → Mobile.sync + CRM consomem.

**Falha:** equipamento BAIXADO → 422 `EquipamentoBaixadoEmOS`;
orçamento cross-tenant → 422 `OrcamentoCrossTenant`.

---

## 2. Saga "Cancelamento parcial × Financeiro" (ADR-0042)

1. P-OP-04 chama `cancelarAtividade(atividade_id, razao)` (US-OS-008).
2. Servidor: atividade vira CANCELADA + publica `AtividadeCancelada` +
   recalcula `valor_total_pos_cancelamentos`.
3. Servidor publica `OS.EscopoAlterado` com `valor_removido` e
   `valor_total_atualizado`.
4. Consumer `financeiro/contas-receber`:
   - Se OS ainda não FATURADA → atualiza `ContasReceber.valor`.
   - Se OS já FATURADA → emite NC fiscal manual (gate
     `GATE-FIN-CR-AJUSTE-POS-FATURA` Wave B).
5. **INV-OS-FAT-001 garante:** `faturamento = sum(atividades não canceladas)`.

---

## 3. Saga "Atividade tipo=calibracao → módulo Metrologia"

1. P-OP-02 (metrologista) executa `concluirAtividade(atividade_id)`
   (US-OS-007) — atividade vira CONCLUIDA.
2. Servidor publica `AtividadeConcluida` com `tipo=calibracao` +
   `link_modulo_tecnico=null` (ainda não criada Calibracao).
3. Watchdog `os-calibracao-link-watchdog`:
   - T+24h sem `Calibracao.atividade_os_id` apontando pra essa
     atividade → alerta P2 ao RT + gerente operacional.
   - T+72h sem link → cria NC automática
     `NaoConformidade.tipo=link_calibracao_faltando` + bloqueia
     emissão de certificado.
4. INV-OS-CAL-LINK-001 garante a existência da Calibracao em ≤24h.

---

## 4. Saga "Anonimização Cliente × OS aberta" (Zona A/B ADR-0021)

1. P-CLI-DPO chama `solicitarAnonimizacao(cliente_id)` (módulo Clientes).
2. Módulo Clientes consulta OS abertas do cliente.
3. **INV-OS-ANON-001:** se existe OS em RASCUNHO / AGENDADA / EM_EXECUCAO:
   - 409 `AnonimizacaoBloqueadaPorOSAberta` + emite
     `AnonimizacaoBloqueada` com `motivo=os_aberta` +
     `os_ids_bloqueantes=[uuid...]`.
   - Cliente recebe e-mail "anonimização agendada para após conclusão
     das OS abertas" (registro ANPD).
4. Quando OS conclui (estado terminal), watchdog dispara nova
   tentativa de anonimização automaticamente (gate
   `GATE-LGPD-ART18-MODULOS`).

---

## 5. Saga "Reabertura cross-cliente em M&A" (sucessão societária)

1. Cliente A (anonimizado) é sucedido por Cliente B (fusão/aquisição).
2. P-OP-04 chama `reabrirOS(os_id, motivo, sucessao_societaria_id)`.
3. **INV-OS-SUC-001:** OS-filha em cliente anonimizado preserva
   `cliente_id_hash` da OS-mãe (referência audit) + grava
   `sucessao_societaria_id` (FK pra registro M&A).
4. OS-filha é criada em `cliente_id=B` (sucessor).
5. Portal-cliente B recebe notificação "OS originária do cliente
   sucedido [hash]".

---

## 6. Saga "Sync mobile com fotos" (ADR-0027 + INV-OS-SYNC-001)

1. Técnico offline preenche checklist + tira fotos.
2. Device fica sem rede; quando conecta, faz POST batch.
3. Servidor: **append-only para fotos** (anexa, nunca substitui).
   Campos escalares (estado, geo, observacoes) usam LWW por
   `client_event_id` + `client_event_created_at`.
4. INV-OS-SYNC-001 garante: foto enviada nunca é descartada (mesmo
   se LWW determinar campo escalar "perdedor", a foto associada vai
   pra galeria da atividade com tag `vencedora_lww=false`).

---

## 7. Saga "Notificação ao cliente" (US-OS-004..007)

Cada transição relevante publica:

| Evento OS | Notifica portal-cliente | Notifica OmniChannel (se opt-in) |
|---|---|---|
| `OSAtribuida` | "Técnico atribuído" | WhatsApp se cliente opt-in |
| `AtividadeIniciada` | "Técnico iniciou atividade" | WhatsApp se opt-in |
| `AtividadeConcluida` | "Atividade X concluída" | WhatsApp se opt-in |
| `OSConcluida` | "OS concluída, certificado em revisão" | WhatsApp + e-mail |
| `OSCancelada` | "OS cancelada — razão: [hash texto]" | WhatsApp + e-mail |

Não publica detalhe PII no payload (INV-OS-AUD-001 + sanitização).

---

## 8. Saga "Reagendamento e troca técnico" (US-OS-011 / US-OS-012)

1. P-OP-04 chama `reagendarAtividade(atividade_id, nova_data, motivo)`
   ou `transferirTecnico(atividade_id, novo_tecnico_id, motivo)`.
2. Servidor valida agenda do novo técnico (INV-020 UMC se aplicável)
   + competência RT por grandeza (INV-CAL-RT-001 quando
   `tipo=calibracao | verificacao_inmetro`).
3. Audit: `EventoDeOS.tipo=atividade_reagendada` ou
   `atividade_tecnico_transferido` com `motivo_hash` (anti-PII).
4. Notifica cliente: "reagendamento para [data]" via portal +
   OmniChannel.

---

## 9. Saga "No-show do cliente" (US-OS-014)

1. Técnico chega no cliente, ninguém disponível.
2. App: `marcarNoShow(atividade_id, foto_evidencia, hora)`.
3. Servidor: atividade fica em PENDENTE (não inicia) + grava
   `EventoDeOS.tipo=no_show_cliente` + custo de deslocamento gerado
   em `ContasReceber` (gate `GATE-FIN-NOSHOW-COBR` Wave B).
4. Notifica cliente: "técnico esteve em [hash endereço]; reagende".

---

## 10. Saga "Dispensa de aceite cliente" (US-OS-013)

1. Cenário: cliente recusa assinatura (motivos jurídicos / cliente
   ausente após no-show / situação excepcional).
2. P-OP-04 (gerente) autoriza via `dispensarAceiteCliente(atividade_id,
   motivo, termo_pdf_id)`.
3. Servidor grava `DispensaAceiteAtividade(atividade_id, motivo,
   autorizado_por_gerente_id, termo_pdf_id)` — entidade nova.
4. Atividade pode concluir sem `AceiteAtividade`; certificado / fatura
   carrega marca "aceite dispensado por gerência (ref: [hash])".

---

## 11. Como evolui

Saga nova → adicionar seção numerada + eventos detalhados em
`docs/comum/integracoes-inter-modulos.md`. Mudança em saga
existente → versionar (v1.1) + bump CHANGELOG.
