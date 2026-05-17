---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/conformidade/comum/lgpd-rat.md
---

# Contratos de Export — Módulo BI

> Formatos de saída do módulo BI (não-regulados; relatórios gerenciais).

---

## Exports

### Export 1: Relatório customizado em PDF

**Propósito:** versão imprimível do relatório customizado para distribuição executiva.
**Formato:** PDF.
**Regulado?:** Não (gerencial).
**Template:** template padrão Aferê + branding do tenant (logo, cores).
**Campos obrigatórios:**
- Cabeçalho: nome do relatório, período, filtros aplicados, gerado em (data/hora + usuário).
- Rodapé: paginação + selo "Aferê — visão gerencial".
- Corpo: tabela/gráficos conforme definição.
**Assinatura digital:** não.
**Imutabilidade:** não (relatório gerencial é descartável; auditoria registra geração).
**Retenção:** arquivo gerado expira em 30 dias no Backblaze B2 (configurável por tenant). Ver `../../../conformidade/comum/retencao-matriz.md`.

**Exemplo:**
```
(PDF binário; preview em wireframe a anexar)
```

---

### Export 2: Relatório customizado em XLSX

**Propósito:** análise externa em Excel.
**Formato:** XLSX (Open XML).
**Regulado?:** Não.
**Estrutura:**
- Aba "Dados" — linhas detalhadas.
- Aba "Resumo" — totais e agrupamentos.
- Aba "Metadados" — período, filtros aplicados, gerado em, usuário.
**Assinatura digital:** não.
**Imutabilidade:** não.
**Retenção:** 30 dias (mesmo que PDF).

---

### Export 3: Relatório customizado em CSV

**Propósito:** integração programática / análise em ferramenta de terceiros.
**Formato:** CSV UTF-8 com BOM, separador `;` (compatível com Excel BR).
**Regulado?:** Não.
**Estrutura:** primeira linha = cabeçalho de colunas; demais = dados.
**Retenção:** 30 dias.

---

### Export 4: Snapshot de Dashboard em PDF (envio agendado)

**Propósito:** envio agendado de "foto" do dashboard executivo por e-mail.
**Formato:** PDF.
**Regulado?:** Não.
**Conteúdo:** captura visual dos widgets do dashboard + timestamp.
**Distribuição:** anexo de e-mail OU link no Backblaze (URL temporária 7 dias).
**Imutabilidade:** snapshot é imutável (representa estado de um instante).
**Retenção:** 30 dias no storage; histórico de envios fica em `bi_agendamento_envio` indefinidamente (com link expirado após retenção).

---

### Export 5: DRE gerencial em PDF

**Propósito:** versão imprimível do DRE gerencial.
**Formato:** PDF.
**Regulado?:** Não — mas **OBRIGATORIAMENTE traz aviso** "Visão gerencial. Não substitui demonstrativo contábil oficial" em rodapé fixo.
**Assinatura digital:** não.
**Retenção:** 90 dias.

---

### Export 6: Snapshot de Link Público em PDF

**Propósito:** o cliente externo pode baixar o que está vendo no link público em PDF.
**Formato:** PDF.
**Regulado?:** Não.
**Notas LGPD:**
- Conteúdo limitado ao escopo do link público (agregado / cliente específico).
- `INV-TENANT-*` valida que não vaza dado de outro tenant nesse PDF.
- Marca d'água com data + identificador anonimizado do link.

---

## Exports inter-módulos

- **BI → Notificações:** snapshot de dashboard anexado em e-mail/WhatsApp (via Notificações).
- **BI → Auditoria:** todo export gera evento `BI.RelatorioGerado` que vai para trilha de auditoria (WORM em B2).
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export

- Mudança em template padrão → bump CHANGELOG seção "Modificado".
- Custom branding do tenant é versionado separado (não impacta template base).

## Como esta lista evolui

- Export novo → adicionar + definir retenção.
- Mudança em formato → ADR + atualizar template.
- Export deprecado → `@deprecated`.

## Notas de segurança

- Toda URL pública de export é **assinada e temporária** (Backblaze B2 + signed URL).
- Limite de tamanho por export: 50MB. Acima disso → split em múltiplos arquivos OU oferecer streaming via API.
- Arquivos contendo dado pessoal seguem `SEC-*` (criptografia em repouso + em trânsito).
