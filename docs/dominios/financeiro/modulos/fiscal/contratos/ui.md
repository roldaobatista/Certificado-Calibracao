---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# Contrato UI — Fiscal

## Telas

### TF-01 — Lista de NFS-e / NFe

- Filtros: status, período, cliente, município, modo (normal/contingência)
- Colunas: número, cliente, valor, data, status, ações
- Status colorido: verde (emitida), vermelho (cancelada), amarelo (em contingência), cinza (rascunho)
- Ações: ver XML/PDF, cancelar, CC-e, reenviar ao cliente

### TF-02 — Emitir NFS-e

- Pré-preenchimento automático (OS + cliente + valor)
- Campo: descrição do serviço (editável)
- Campo: código LC 116 (combobox; default pré-config)
- Bloco **"Campos fiscais (preenchidos com seu contador)"** — read-only com info "Configurado em Configurações > Fiscal":
  - Regime, alíquota ISS, retenções
  - Aviso visível: "**Aferê não calcula impostos.** Os valores aqui foram configurados por você com seu contador."
- Botão "Emitir" + checkbox "Enviar pro cliente por email"

### TF-03 — Detalhe da NFS-e

- Cabeçalho: número + status + protocolo
- Linha do tempo: emitida → autorizada → enviada → vista
- Botões: cancelar (se < 24h), CC-e, reenviar 2ª via, baixar XML, baixar PDF
- Histórico de eventos (CC-e, cancelamento)
- Verificação WORM (hash do XML)

### TF-04 — CC-e (Carta de Correção)

- Texto livre (até 1000 caracteres)
- Alerta: "CC-e não corrige valor, CPF/CNPJ ou cliente — pra isso, cancele e emita nova."
- Confirmar emissão

### TF-05 — Cancelamento

- Razão (obrigatória)
- Aviso: "Cancelamento extemporâneo (> 24h) pode ter multa do município. Comunique seu contador."
- Confirmação 2 cliques

### TF-06 — Numeração / Inutilização

- Lista de buracos: "Números 102-104 ficaram em aberto desde {data}. Prazo pra inutilizar: até {data limite}."
- Botão "Inutilizar 102-104" (1 toque)

### TF-07 — Configuração fiscal

- Regime tributário
- Inscrição municipal / estadual
- Códigos LC 116 que o tenant emite
- Alíquotas (com aviso "Configure com seu contador")
- Certificado digital (upload A1 / config A3)
- BaaS provider (oculto — admin Aferê)
- Botão "Validar configuração" (sandbox test)

### TF-08 — Banner contingência (global)

- Visível em todas as telas fiscais quando ativo
- Texto: "Operando em contingência ({modo}) — autorização do {município/SEFAZ} fora. Suas NFs continuam sendo emitidas; vão regularizar quando voltar."
- Link "Saiba mais"

## Mensagens visíveis

| Contexto | Mensagem |
|---|---|
| Emissão sucesso | "NFS-e {número} emitida e enviada ao cliente." |
| SEFAZ fora | "Município está fora no momento. Vamos emitir em contingência — você continua faturando." |
| Erro dado inválido | "Falta {campo} pra emitir. Corrigir em Configuração Fiscal." |
| Certificado próximo vencer | "Seu certificado digital vence em {N} dias. Renove já pra não interromper emissão." |

## Acessibilidade + UX crítica

- Botão "Emitir" só ativo se config fiscal completa
- Não esconder erro do SEFAZ — explicar em português

## Non-goals UI

- Editor visual de cálculo de imposto (decisão fundadora — não calculamos)
- Simulador de regime tributário

## Referências

- ADR-0008, ADR-0009
- `docs/conformidade/comum/fiscal.md`
