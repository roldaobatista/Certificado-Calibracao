---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
  - docs/conformidade/comum/retencao-matriz.md
---

# Contratos de Export — Módulo Onboarding

> Saídas do módulo de implantação. Inclui termo de aceite (juridicamente relevante, imutável).

---

## Exports

### Export 1: Termo de Aceite de Implantação (PDF)

**Propósito:** documento jurídico que marca conclusão da implantação e início da operação contratual.
**Formato:** PDF/A.
**Regulado?:** não diretamente, mas tem valor contratual.
**Validador externo:** —.
**Template/Schema:** template a definir em `docs/templates/onboarding-termo-aceite.html` (criar pós ADR-0001).
**Campos obrigatórios:** razão social do tenant, CNPJ, escopo da implantação, lista de etapas concluídas, treinamentos realizados, inconsistências aceitas/resolvidas, data de geração, nome+documento do assinante, hash do PDF.
**Campos opcionais:** observações, anexos (atas de reunião).
**Assinatura digital:** sim — A3 ICP-Brasil via Lacuna Web PKI (ADR-0009).
**Imutabilidade pós-emissão:** sim — `INV-043` (termo imutável após assinatura) + `INV-001` (WORM); armazenado em Backblaze B2 WORM.
**Retenção:** mínimo 5 anos (ver `docs/conformidade/comum/retencao-matriz.md`).

**Exemplo:**
```
TERMO DE ACEITE DE IMPLANTAÇÃO
Empresa: [Razão Social] - CNPJ [xx.xxx.xxx/xxxx-xx]
Implantação: #INC-2026-0042
Iniciada em: 2026-05-01 | Concluída em: 2026-06-15
Etapas concluídas: 12/12
Treinamentos: 3 sessões, total 6h
Inconsistências: 4 (todas resolvidas)
Validação técnica: PASSOU
Hash PDF: sha256:...
Assinado por: [Nome] | Documento: [CPF]
```

---

### Export 2: Relatório de Inconsistências de Migração (PDF / XLSX)

**Propósito:** documentar todas as inconsistências encontradas durante imports, pra revisão conjunta com o cliente.
**Formato:** PDF (resumido) + XLSX (detalhado).
**Regulado?:** não.
**Campos obrigatórios:** tipo de import, linha do arquivo, campo, severidade, descrição, dado original, status final (resolvida / aceita), justificativa.
**Assinatura digital:** opcional.
**Imutabilidade pós-emissão:** não (relatório operacional, pode ser regerado).
**Retenção:** vinculada à implantação (mesmo prazo do termo).

---

### Export 3: Checklist de Implantação Concluída (PDF)

**Propósito:** anexo do termo de aceite mostrando cada etapa com data e responsável.
**Formato:** PDF/A.
**Campos obrigatórios:** nome da etapa, data conclusão, responsável, observações.
**Imutabilidade:** sim (gerado junto com o termo).
**Retenção:** mesmo prazo do termo.

---

### Export 4: Template de importação (CSV / XLSX)

**Propósito:** modelo vazio que o cliente preenche pra importar dados iniciais.
**Formato:** CSV (UTF-8) e XLSX.
**Versionado:** sim — versão no nome do arquivo (ex: `template-clientes-v1.xlsx`).
**Campos obrigatórios:** colunas do tipo de dado correspondente + linha de header com instruções.
**Imutabilidade:** não — template evolui.

---

### Export 5: Snapshot de configuração do sandbox (JSON)

**Propósito:** registrar configuração aprovada no sandbox antes da promoção pra produção. Auditável.
**Formato:** JSON.
**Campos obrigatórios:** tenant_id, data_snapshot, configuracoes (chave/valor), hash.
**Imutabilidade:** sim após promoção.
**Retenção:** vinculada ao tenant (enquanto ativo).

---

## Exports inter-módulos

- Export 1 (Termo) consumido por: módulo financeiro (libera billing produtivo), módulo de auditoria/conformidade.
- Export 5 (Snapshot) consumido por: configurações-sistema (aplicação efetiva).

Ver `docs/comum/integracoes-inter-modulos.md`.

## Versionamento

- Templates de import versionados; ao mudar coluna, manter v anterior por 6 meses.

## Como esta lista evolui

- Export novo → adicionar + definir retenção.
- Mudança em PDF do termo → ADR (impacto jurídico).
