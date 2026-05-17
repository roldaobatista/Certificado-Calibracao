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

# Contratos de Export — Módulo Configurações do Sistema

> Saídas do módulo. Foco em snapshots auditáveis e relatórios de configuração vigente.

---

## Exports

### Export 1: Snapshot de configuração do tenant (JSON)

**Propósito:** estado completo das configurações em um momento, pra auditoria, backup ou migração.
**Formato:** JSON (estruturado por seção).
**Regulado?:** não, mas usado em auditoria.
**Campos obrigatórios:** tenant_id, data_snapshot, versao_schema, secoes (empresa, filiais, series, impostos, papeis, workflows, status, campos_obrigatorios, modelos_pdf, assinatura, integracoes (sem credenciais reais — só refs KMS), notificacoes, regras_comerciais, sla, operacional, backup, retencao, features), hash.
**Assinatura digital:** opcional (admin pode assinar A3).
**Imutabilidade pós-emissão:** sim (snapshot é imutável).
**Retenção:** vinculada ao tenant (enquanto ativo + janela legal pós-cancelamento).

---

### Export 2: Relatório de Permissões (PDF / XLSX)

**Propósito:** documentar matriz papel × módulo × ação vigente, pra revisão de segurança e LGPD.
**Formato:** PDF + XLSX.
**Campos obrigatórios:** papel, descrição, lista de permissões (módulo, recurso, ação), nº de usuários, data geração, gerador.
**Imutabilidade:** não (regerável).
**Retenção:** definida pelo tenant; recomendado ≥ 2 anos.
**Uso típico:** auditoria interna, due diligence, LGPD art. 37.

---

### Export 3: Trilha de Auditoria de Configurações (CSV / XLSX)

**Propósito:** histórico de mudanças em config sensível por período.
**Formato:** CSV (UTF-8) ou XLSX.
**Campos obrigatórios:** data, ator, ator_origem, entidade_config, entidade_id, campo, valor_antes, valor_depois, ip.
**Filtragem:** por período, ator, entidade, campo.
**Imutabilidade:** os REGISTROS são imutáveis (origem em WORM); export pode ser regerado.
**Retenção:** trilha original retida conforme LGPD + SEC-005.

---

### Export 4: Configuração Fiscal Vigente (PDF)

**Propósito:** snapshot fiscal pra contador / auditoria fiscal.
**Formato:** PDF.
**Campos obrigatórios:** empresa, filiais, regime tributário, impostos (alíquotas com vigência), séries fiscais (NF, fatura, certificado), data geração.
**Imutabilidade:** sim (snapshot).
**Retenção:** 5 anos (fiscal — ver `docs/conformidade/comum/fiscal.md`).

---

### Export 5: Workflows e Status Configurados (PDF / JSON)

**Propósito:** documentar processos modelados, pra treinamento e ISO 9001.
**Formato:** PDF (visual) + JSON (técnico).
**Campos obrigatórios:** entidade, versão, etapas em ordem, transições, status personalizados (nome, cor, ordem).
**Imutabilidade:** snapshot.
**Retenção:** definida pelo tenant.

---

### Export 6: Catálogo de Integrações Ativas (PDF)

**Propósito:** lista de integrações ativas com tipo, endpoint (sem credencial), status do último teste, data ativação. Útil pra segurança e mapeamento de dependências.
**Formato:** PDF.
**Campos:** tipo, nome, endpoint, ultimo_teste_em, ultimo_teste_status, ativada_em, ativada_por.
**Imutabilidade:** snapshot.

---

### Export 7: Configuração de Retenção vs Mínimo Legal (PDF)

**Propósito:** relatório comparativo da retenção configurada vs mínimo legal por entidade. Para DPO.
**Formato:** PDF.
**Campos:** entidade, periodo_configurado, minimo_legal, base_legal, conforme (sim/não).
**Imutabilidade:** snapshot.
**Uso:** evidência de conformidade LGPD + ISO 17025 + fiscal.

---

### Export 8: Pacote de Mudança de Plano (JSON)

**Propósito:** quando tenant muda de plano, snapshot das features ligadas atualmente vs disponíveis no novo plano. Apoia decisão do admin (o que vai deixar de funcionar).
**Formato:** JSON.
**Campos:** plano_atual, plano_novo, features_ativas_atuais, features_disponíveis_novo, features_que_serao_desligadas.
**Imutabilidade:** snapshot.

---

## Exports inter-módulos

- Export 1 (Snapshot) consumido por: auditoria global, módulo de migração tenant→tenant.
- Export 4 (Fiscal) consumido por: módulo financeiro/fiscal, contador externo.
- Export 7 (Retenção) consumido por: módulo conformidade LGPD.

Ver `docs/comum/integracoes-inter-modulos.md`.

## Versionamento

- Schema do snapshot versionado (`versao_schema` no JSON); incompatibilidade exige migração documentada.

## Como esta lista evolui

- Export novo → adicionar + definir retenção.
- Mudança em fiscal/retenção → ADR (impacto legal).
