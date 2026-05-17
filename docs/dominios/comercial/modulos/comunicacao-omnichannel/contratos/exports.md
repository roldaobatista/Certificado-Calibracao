---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/lgpd-rat.md
---

# Contratos de Export — Módulo Comunicação Omnichannel

> Saídas operacionais e regulatórias (LGPD).

---

## Exports

### Export 1: Trilha de consentimento (CSV/PDF)

**Propósito:** evidência LGPD em auditoria interna, ANPD, ou direito de acesso do titular.
**Formato:** CSV (granular) e PDF (apresentação ao titular).
**Regulado?:** sim — LGPD art. 9º e 18º.
**Validador externo:** N/A (auditoria humana / DPO).
**Campos obrigatórios:** cliente_id, canal_tipo, tipo (opt_in/opt_out), base_legal, texto_apresentado, texto_resposta_cliente, timestamp, referencia_mensagem_id, ator.
**Imutabilidade pós-emissão:** sim — fonte é WORM.
**Retenção:** durante a relação com o titular + 5 anos após (ver `../../../conformidade/comum/retencao-matriz.md`).

**Exemplo:**
```
cliente_id;canal;tipo;base_legal;texto_apresentado;texto_resposta;timestamp
uuid-1;whatsapp;opt_in;consentimento;"Aceita receber comunicações?";"ACEITO";2026-05-17T10:30:00-03:00
uuid-1;whatsapp;opt_out;direito_titular;"Reenvio confirmação saída";"SAIR";2026-08-01T14:22:00-03:00
```

---

### Export 2: Histórico de mensagens por cliente (PDF/CSV)

**Propósito:** atender direito de acesso LGPD (titular pede cópia dos seus dados) ou solicitação interna/jurídica.
**Formato:** PDF (apresentação) + CSV (granular).
**Regulado?:** sim — LGPD art. 18º (acesso).
**Campos:** todas as mensagens do titular, por canal, com timestamp, direção, conteúdo, anexos (links), status entrega.
**Atenção:** anexos contendo dados de terceiros precisam de mascaramento manual antes da entrega.
**Retenção do export gerado:** logado, sem retenção do PDF (regenera quando solicitado).

---

### Export 3: Relatório de atendimento (PDF/CSV)

**Propósito:** indicadores operacionais para gerência.
**Formato:** PDF + CSV + XLSX.
**Regulado?:** não.
**Campos:** período, volume por canal, TMR/TMA, % opt-in, conversões (chamado/lead), por atendente.

---

### Export 4: Lista segmentada para campanha (CSV)

**Propósito:** insumo para campanha (já filtrada por opt-in válido).
**Formato:** CSV.
**Regulado?:** não — mas USO é regulado por LGPD.
**Campos:** identificador, canal, opt-in válido (sim/não — sempre filtrado a "sim"), última interação.
**Atenção:** lista é gerada com snapshot do consentimento; se cliente fizer opt-out entre geração e disparo, a regra de envio re-verifica e bloqueia (US-COM-003).

---

### Export 5: Backup de templates aprovados (JSON)

**Propósito:** versionamento e migração entre ambientes.
**Formato:** JSON.
**Campos:** nome, versão, canal, corpo, variáveis, external_template_id, status, timestamps.

---

### Export 6: Evidência de envio (PDF por mensagem)

**Propósito:** prova de envio em disputa contratual ou jurídica.
**Formato:** PDF de 1 página.
**Campos:** destinatário, canal, conteúdo, timestamp, status entrega, hash da mensagem original.
**Assinatura digital:** opcional (via porta Signature).

---

## Exports inter-módulos

- Trilha de consentimento usada por módulo LGPD/Conformidade (`docs/conformidade/`).
- Eventos `Comunicacao.ConvertidoEmChamado`/`ConvertidoEmLead` viram criação de entidade em outros módulos (não export — integração inter-módulos).

---

## Versionamento de export

- Formatos CSV/JSON estáveis em v1.
- Mudança em layout → ADR + janela de migração para integradores externos.

---

## Como esta lista evolui

- Export novo → adicionar + (se regulado LGPD) revisar com DPO/advogado-saas-regulado.
- Mudança em formato → ADR.
- Export descontinuado → `@deprecated`.
