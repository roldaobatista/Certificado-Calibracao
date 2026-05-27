---
owner: roldao
status: draft
revisado-em: 2026-05-27
proximo_review: 2026-08-27
diataxis: how-to
audiencia: dpo
tipo: runbook
origem: T-SAN-PERFIL-040 (Sprint 3 P5 ADR-0067) — anticipa AC-SAN-PERFIL-007-4 (Sprint 6 Wave A)
relacionados:
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0021-anonimizacao-vs-retencao.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - REGRAS-INEGOCIAVEIS.md
---

# Runbook DPO/Encarregado — Resposta padrão a titulares

> **PRECISA REVISÃO JURÍDICA HUMANA (OAB com LGPD) ANTES DE USO EM PRODUÇÃO.**
>
> Este documento é minuta consultiva preparada pelo subagente `advogado-saas-regulado` (sem OAB). Quando o 1º tenant externo pagante chegar, o clausulado precisa de revisão de advogado humano licenciado. Em particular: §1.B + §2 + §3.

## Por quê este documento existe

Resolução CD/ANPD 2/2022 art. 8 + LGPD art. 18 §6 exigem que o controlador **fundamente nominalmente** sua resposta a pedidos de titular. Resposta genérica "indeferido" = multa ANPD potencial.

Aferê é **operador LGPD** em relação aos tenants e **controlador** em relação aos dados próprios (logs, métricas, eventos). Para titulares vinculados a um tenant, Aferê encaminha o pedido ao tenant + responde tecnicamente com a estrutura abaixo.

## Modelos por cenário

### Cenário 1 — Titular pede eliminação de dados (LGPD art. 18 VI) em tenant **Perfil D** (comercial puro)

**Pode atender.** PII de tenant D tem retenção 5 anos (Receita, CTN art. 173). Após esse prazo, dado pessoal é anonimizável (ADR-0021 zona A).

**Resposta padrão:**

> Prezado(a) [TITULAR],
>
> Atendendo sua solicitação datada de [DATA] (protocolo ANPD/DPO interno [NN]), informamos:
>
> Seus dados pessoais vinculados a [TENANT] foram identificados em nossa base. Como [TENANT] opera no perfil **comercial-padrão** (não acreditado ISO/IEC 17025), a obrigação legal de retenção aplicável é apenas a fiscal (CTN art. 173 — 5 anos a contar do exercício seguinte).
>
> Dados com vínculo fiscal anteriores a [DATA - 5a]: **eliminados** em [DATA EXECUÇÃO].
> Dados com vínculo fiscal posteriores a [DATA - 5a]: **mantidos** com base legal LGPD art. 7º II (obrigação legal — Receita).
>
> Status final: pedido **parcialmente atendido**.
> Prazo de eliminação total: até [DATA - 5a + 5a].
>
> Canal de contestação: [DPO_EMAIL].

### Cenário 2 — Titular pede eliminação em tenant **Perfil A** (acreditado RBC)

**NÃO pode atender (recusa fundamentada).** PII de tenant A está vinculada a certificados de calibração que ISO 17025 cl. 8.4 + RBC CGCRE NIT-DICLA-016 exigem reter por ~25 anos. Negar SEM fundamentação = multa. Atender SEM consultar perfil = quebra LGPD art. 16 II.

**Resposta padrão:**

> Prezado(a) [TITULAR],
>
> Atendendo sua solicitação datada de [DATA] (protocolo ANPD/DPO interno [NN]), informamos:
>
> Seus dados pessoais vinculados a [TENANT] foram identificados em nossa base. Esta resposta é **recusa fundamentada** de eliminação, com base nas seguintes obrigações legais:
>
> 1. **LGPD art. 16 II** (cumprimento de obrigação legal/regulatória pelo controlador).
> 2. **ISO/IEC 17025:2017 cl. 8.4.2** (controle de registros — período mínimo 1 ciclo de acreditação; prática RBC consolidada 25 anos).
> 3. **CGCRE NIT-DICLA-016 rev. atual** (rastreabilidade técnica do certificado para auditoria de supervisão).
> 4. **Acreditação CGCRE de [TENANT]:** RBC [NUMERO_RBC] vigente desde [VIGENCIA_INICIO]. Acreditação consultável em <https://www.gov.br/inmetro/pt-br>.
>
> Conforme ADR-0021 zona B do Aferê, dados são **mantidos íntegros** por **25 anos** a contar da data de emissão do último certificado vinculado a você. **Data de eliminabilidade prevista:** [HOJE + 25a do último certificado].
>
> Status final: pedido **indeferido com fundamento legal** (LGPD art. 16 II).
>
> Direito de contestação: titular pode recorrer à **ANPD** ([https://www.gov.br/anpd](https://www.gov.br/anpd)) caso entenda que a fundamentação não procede.
>
> Canal interno: [DPO_EMAIL].

### Cenário 3 — Titular pede confirmação de tratamento (LGPD art. 18 II) em qualquer perfil

**Deve atender em 15 dias úteis.** Resposta lista dados sob tratamento (sem revelar PII de outros titulares — Aferê filtra por `cliente_canonico_id` do titular requisitante).

**Resposta padrão:**

> Prezado(a) [TITULAR],
>
> Atendendo sua solicitação de confirmação de tratamento (LGPD art. 18 II) datada de [DATA]:
>
> **Tenant controlador:** [TENANT] (CNPJ [CNPJ_TENANT])
> **Perfil regulatório do tenant:** [A_ACREDITADO_RBC | B_RASTREAVEL | C_EM_PREPARACAO | D_COMERCIAL_PURO]
> **Operador:** Aferê (CNPJ [CNPJ_AFERE])
>
> **Dados tratados (categorias):**
> - Cadastrais: nome, CPF/CNPJ, contatos.
> - Operacionais: equipamentos vinculados, ordens de serviço, atividades técnicas.
> - Metrológicos (se perfil ≥ B): leituras de calibração, certificados emitidos.
>
> **Bases legais:**
> - LGPD art. 7º V (execução de contrato).
> - LGPD art. 7º II (obrigação legal — Receita, ISO 17025 cl. 8.4 quando aplicável).
>
> **Retenção esperada:**
> - Perfil A/B/C: 25 anos (ISO 17025 cl. 8.4 — registros técnicos).
> - Perfil D: 5 anos (CTN art. 173 — somente fiscal).
>
> **Compartilhamentos:**
> - Receita Federal (SPED/eSocial — perfis com fiscal habilitado).
> - CGCRE/INMETRO (auditoria — perfil A apenas, durante visita de supervisão).
> - Subprocessadores (anexo público em [DPA_URL]).
>
> **Demais direitos LGPD art. 18:** atendidos via [DPO_EMAIL].

### Cenário 4 — Titular cuja prestadora promoveu D→A (mudança de retenção 5a → 25a)

**Aviso ativo obrigatório** (AC-SAN-PERFIL-007-1..3, Sprint 6 Wave A). Aferê envia notificação 15 dias antes da promoção efetivar OU 5 dias úteis após (se promoção urgente).

**Aviso padrão:**

> Prezado(a) [TITULAR],
>
> Comunicamos atualização importante sobre o tratamento de seus dados pessoais vinculados a [TENANT]:
>
> Em [DATA_PROMOCAO], [TENANT] foi acreditado(a) pela CGCRE/INMETRO no escopo RBC [NUMERO_RBC]. Como consequência, **a retenção de seus dados de calibração passa de 5 anos para 25 anos**, com base legal LGPD art. 16 II (ISO/IEC 17025 cl. 8.4 + NIT-DICLA-016).
>
> **O que muda na prática:**
> - Certificados emitidos a partir de [DATA_PROMOCAO]: retenção 25a.
> - Certificados anteriores: mantêm retenção original (5a a contar de emissão), salvo se contiverem rastreabilidade compartilhada com pós-promoção.
>
> **Seus direitos preservados em modo restrito:**
> - Confirmação de tratamento (art. 18 II): atendido normalmente.
> - Correção (art. 18 III): atendido normalmente.
> - Portabilidade (art. 18 V): atendido normalmente.
> - Eliminação (art. 18 VI): pode ser recusada com base no art. 16 II (obrigação legal).
>
> Esta comunicação é exigência da LGPD art. 9º (informação clara) + art. 18 IX (revisão de decisões automatizadas).
>
> Canal de contestação: ANPD ou [DPO_EMAIL].

## Como o sistema apoia a resposta

| Pergunta da DPO | Como obter |
|---|---|
| Qual perfil do tenant na data X? | `SELECT perfil_no_evento FROM auditoria WHERE tenant_id=X AND timestamp <= 'data X' ORDER BY timestamp DESC LIMIT 1` (Sprint 4 — não disponível ainda) |
| Quando o tenant virou A? | `SELECT registrado_em FROM tenant_perfil_historico WHERE tenant_id=X AND direcao='promocao_regulatoria' AND perfil_novo='A'` |
| Qual o número RBC vigente? | `SELECT acreditacao_cgcre_numero FROM tenants WHERE id=X` (cache) ou módulo `licencas-acreditacoes` (Wave A — fonte da verdade granular) |
| Lista de certificados emitidos pelo tenant ao titular Y | `SELECT id, emitido_em FROM certificado WHERE tenant_id=X AND cliente_canonico_id=Y` |
| Qual a data de eliminabilidade do dado mais recente? | Última `data_servico` em `evento_de_calibracao` filtrado por cliente + 25a (se tenant A/B/C) ou 5a (se tenant D) |

## Histórico

- **2026-05-27** — Sprint 3 P5 ADR-0067: documento criado. Status `draft` até revisão jurídica humana (OAB).
- Próxima revisão prevista: pré-1º tenant externo pagante (Sprint 6 Wave A).
