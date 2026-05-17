---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/seguranca-dados.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/comum/isolamento-multi-tenant.md
---

# Contratos de Export — Módulo ACS

> Formatos de saída do módulo. Inclui exports REGULADOS por LGPD (Art. 18-19) e ISO 17025 (cláusula 8.4 rastreabilidade), com regras de assinatura e retenção.

---

## Convenções

- Todo export sensível é assinado digitalmente (assinatura do servidor — não A3 do usuário) com timestamp confiável (Observatório Nacional / autoridade temporal).
- Exports LGPD têm hash SHA-256 + URL pré-assinada de validade curta (24h-30d, conforme finalidade).
- Linguagem dos PDFs em PT-BR claro, sem jargão técnico.
- Toda emissão de export gera evento `acs.export.emitido` na trilha (`INV-001`).
- Tenant_id sempre presente no nome do arquivo e no conteúdo (`INV-TENANT-001`).

---

## Exports

### Export 1: Pacote LGPD do Titular (exportação de dados)

**Propósito:** atender direito de portabilidade do titular (LGPD Art. 18 II e V).
**Formato:** ZIP contendo:
- `dados-pessoais.json` (estrutura legível por humano e máquina).
- `dados-pessoais.pdf` (versão impressa amigável).
- `consentimentos-historico.pdf` (versões aceitas e revogadas).
- `documentos/` (anexos: NFs emitidas, certificados, ordens de serviço — quando aplicável).
- `manifest.json` (lista de arquivos + SHA-256 de cada um).
- `comprovante.pdf` (carta com protocolo, data, prazo cumprido, hash do pacote, assinado pelo servidor).

**Regulado?** Sim — LGPD Art. 18-19.
**Validador externo:** não aplicável (formato livre — ANPD não publicou schema).
**Template/Schema:** definido em `docs/conformidade/comum/lgpd-rat.md` (referenciado).
**Campos obrigatórios:** identificação completa do titular, lista de finalidades e bases legais, histórico de consentimentos, lista de operações registradas (acessos, vendas, atendimentos).
**Assinatura digital:** sim — assinatura do servidor (chave do tenant via KMS) + timestamp confiável.
**Imutabilidade pós-emissão:** sim — pacote vai pro Backblaze WORM (`INV-001`); URL de download invalida em 30 dias, mas o arquivo fica retido pelo período legal.
**Retenção:** ver `docs/conformidade/comum/retencao-matriz.md`.
**Acesso:** URL pré-assinada (24h após geração); titular vê link na tela do portal por 30 dias.

**Exemplo (estrutura):**
```
lgpd-export-<tenant>-<protocolo>-<data>.zip
├── manifest.json
├── dados-pessoais.json
├── dados-pessoais.pdf
├── consentimentos-historico.pdf
├── comprovante.pdf
└── documentos/
    ├── nf-2025-001.pdf
    └── certificado-RBC-2025-042.pdf
```

---

### Export 2: Comprovante de Solicitação LGPD (acionamento)

**Propósito:** dar ao titular comprovante imediato de protocolo (no ato da solicitação) e final (na conclusão).
**Formato:** PDF.
**Regulado?** Sim — LGPD Art. 18 § 5º (prazo).
**Campos obrigatórios:** protocolo, titular, tipo (exportação/anonimização/exclusão), data abertura, prazo legal (`abertura + 15 dias`), status, tenant, hash, QR code de validação.
**Assinatura digital:** sim (servidor + timestamp).
**Imutabilidade:** sim.
**Retenção:** 5 anos pós-conclusão (alinhado a Receita).

---

### Export 3: Comprovante de Anonimização

**Propósito:** evidência de que dado pessoal foi anonimizado preservando registros contábeis/fiscais.
**Formato:** PDF.
**Regulado?** Sim — LGPD Art. 5 XI + Art. 12.
**Campos obrigatórios:** titular (identificação prévia), data anonimização, escopo (campos atingidos), referência aos registros mantidos com identificador hash (NF-X, OS-Y), assinatura servidor + timestamp.
**Imutabilidade:** sim.
**Retenção:** 5 anos.

---

### Export 4: Comprovante de Exclusão

**Propósito:** evidência de exclusão definitiva quando retenção legal expira.
**Formato:** PDF + entrada permanente na trilha de auditoria (não apaga o evento de exclusão mesmo após exclusão dos dados).
**Regulado?** Sim — LGPD Art. 18 VI.
**Campos obrigatórios:** titular (hash — não nome em claro), tipo de dado excluído, data exclusão, base de retenção que expirou, assinatura servidor.

---

### Export 5: Trilha de Auditoria (CSV / PDF)

**Propósito:** evidência para fiscalização (RBC, ANPD, Receita) ou investigação interna.
**Formato:**
- **CSV** (estruturado, importável em planilha) — colunas: `evento_id`, `timestamp_utc`, `timestamp_local`, `tenant_id`, `usuario_id`, `usuario_nome`, `tipo_evento`, `entidade_tipo`, `entidade_id`, `acao`, `ip`, `pais`, `cidade_aprox`, `user_agent`, `correlation_id`, `hash_evento`.
- **PDF** (impresso, assinado) — sumário + tabela formatada + hash do CSV embutido.
**Regulado?** Parcial — ISO 17025 cláusula 8.4 + boas práticas ANPD.
**Validador externo:** não aplicável (formato proprietário Aferê — validação por hash).
**Campos obrigatórios:** vide colunas.
**Assinatura digital:** PDF assinado pelo servidor + timestamp.
**Imutabilidade pós-emissão:** sim — o conteúdo da trilha é WORM (`INV-001`); o export é snapshot do filtro/janela aplicado.
**Retenção:** 8 anos (ISO 17025 8.4 — registros eletrônicos da qualidade).

**Permissão:** `auditoria.exportar`.
**Limite de tamanho:** se filtro retornar > 100k linhas, gera assíncrono e notifica por email.

---

### Export 6: Histórico de um Registro Crítico

**Propósito:** mostrar versão a versão de 1 cliente/certificado/OS/lançamento para auditor.
**Formato:** PDF (impresso) + JSON (estruturado).
**Conteúdo:** linha do tempo de versões + diff campo-a-campo + identificação do usuário responsável + IP + assinatura servidor.
**Regulado?** Sim — ISO 17025 8.4 para certificados; Receita para lançamentos fiscais.
**Imutabilidade:** sim.
**Retenção:** alinhada ao tipo de registro (certificado RBC = 8 anos; NF = 5 anos).

---

### Export 7: Relatório de Acesso e Permissões (snapshot)

**Propósito:** evidência para auditor/admin ver "quem tinha acesso a quê em data X".
**Formato:** PDF + JSON.
**Conteúdo:** lista de usuários ativos no tenant na data X, perfis atribuídos, filiais vinculadas, matriz de permissão efetiva, status MFA.
**Regulado?** Boas práticas LGPD Art. 46 + ISO 27001 controles A.9.
**Assinatura digital:** sim.
**Retenção:** 5 anos.
**Permissão:** `usuario.exportar_snapshot`.

---

### Export 8: Termo de Consentimento Aceito (recibo do titular)

**Propósito:** entregar ao titular a versão exata do termo que ele aceitou.
**Formato:** PDF.
**Conteúdo:** texto integral do termo na versão aceita, finalidades selecionadas, data/hora/IP, hash, QR code de validação.
**Regulado?** Sim — LGPD Art. 8 § 1º (consentimento informado).
**Assinatura digital:** servidor + timestamp.
**Retenção:** enquanto o consentimento estiver ativo + 5 anos pós-revogação.

---

### Export 9: Relatório de Conformidade Periódico (mensal/trimestral)

**Propósito:** resumo executivo para Roldão/admin tenant sobre saúde de segurança e LGPD.
**Formato:** PDF (dashboard impresso).
**Conteúdo:**
- Métricas (cobertura MFA, solicitações LGPD no prazo, incidentes, sessões repudiadas).
- Lista de novos usuários e usuários desativados no período.
- Mudanças em perfis/permissões.
- Alertas disparados.
**Regulado?** Não — uso interno.
**Periodicidade:** mensal automático + on-demand.

---

## Exports inter-módulos

| Export deste módulo | Consumido por | Via |
|---|---|---|
| Trilha de Auditoria | conformidade (auditor RBC) | Download manual / API |
| Pacote LGPD | comum / financeiro / metrologia (precisam disponibilizar seus dados ao pacote) | Hook outbound: módulos retornam JSON parcial em `GET /v1/acs/lgpd/datasource/<modulo>` |
| Snapshot de Permissões | governanca (Família 5 auditores) | API interna |

Ver `docs/comum/integracoes-inter-modulos.md` para contrato detalhado.

---

## Versionamento de exports

- Mudança em schema do CSV de auditoria = ADR + janela de 6 meses (consumidores externos podem ter parsers).
- Mudança em template PDF (visual) = bump CHANGELOG, sem migração necessária.
- Mudança em formato regulado (se ANPD publicar schema obrigatório) = janela definida pelo regulador.

## Como esta lista evolui

- Export novo → adicionar + linkar US + validar contra schema oficial se regulado.
- Mudança em formato regulado → ADR + atualizar validador.
- Export deprecado → marcar `@deprecated` + janela de migração + comunicar consumidores.
