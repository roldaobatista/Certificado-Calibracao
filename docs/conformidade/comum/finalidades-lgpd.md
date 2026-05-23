---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/lgpd-rat.md
  - REGRAS-INEGOCIAVEIS.md
  - docs/dominios/comercial/modulos/clientes/prd.md
---

# Catálogo de finalidades LGPD (Aferê)

> **Pra quê:** centralizar as bases legais aceitas pelo produto. Toda decisão de autorização (`AuthorizationProvider.can(..., purpose=...)`) e todo registro de aceite (Cliente, futuros módulos) consulta este catálogo.
>
> **Quem mantém:** Roldão decide o que entra/sai (após parecer do subagente `advogado-saas-regulado` em cada mudança). Inclusão de finalidade nova exige PR + revisão.
>
> **Validado pelo:** subagente advogado-saas-regulado em 2026-05-18 (parecer em `docs/dominios/comercial/modulos/clientes/revisoes/US-CLI-001-advogado.md`).

---

## Catálogo (12 entradas — Wave A pós Onda 7 saneamento 2026-05-23)

### Finalidades originais (MVP-1)

| Código | Base legal | Quando usar | Coleta consentimento extra? |
|---|---|---|---|
| `execucao_contrato` | LGPD Art. 7º V | Cadastro/atendimento de cliente, OS, agendamento, financeiro do contrato comercial | Não — base autoexecutável |
| `obrigacao_legal` | LGPD Art. 7º II | NF-e, retenção fiscal, RAT trabalhista | Não |
| `interesse_legitimo` | LGPD Art. 7º IX | Anti-fraude, dedup, métricas internas anonimizadas | Não — exige LIA (`docs/conformidade/comum/lia-template.md`) |
| `consentimento` | LGPD Art. 7º I | Marketing/lembretes WhatsApp (RAT-06 opt-in), comunicação não-contratual | **SIM** — opt-in explícito separado |

### Finalidades estendidas (Onda 7 — pré-Marco 3/4/5 + Wave A regulatório)

| Código | Base legal | Quando usar | Coleta consentimento extra? |
|---|---|---|---|
| `obrigacao_regulatoria_iso17025` | LGPD Art. 7º II | RT, signatário, certificado de calibração, registros técnicos cl. 7.5, validação software cl. 7.11 | Não — base regulatória autônoma |
| `auditoria_cgcre` | LGPD Art. 7º II + Art. 11 II "a" | Acesso CGCRE/RBC durante supervisão; consultor RBC; auditor externo | Não — base regulatória |
| `signatario_a3` | LGPD Art. 7º II + MP 2.200-2/2001 | Captura/persistência de dados ICP-Brasil A3 (CPF, dados certificado, nonce, signing-time) | Não — exigência ICP-Brasil |
| `responsavel_tecnico_tenant` | LGPD Art. 7º II + NIT-DICLA-021 + ADR-0022 | RT vigente do tenant: nome, CPF, registro conselho, vigência, competências por grandeza | Não — obrigação regulatória |
| `tecnico_campo` | LGPD Art. 7º V | Técnico executor da OS: geolocalização opt-in, foto perfil, biometria touch quando exigida | **SIM para geo** — opt-in explícito (RAT-07); biometria sob art. 11 II "g" + "a" |
| `defesa_em_juizo` | LGPD Art. 7º VI | Litígio/contestação; preservação de evidências; produção de prova | Não — base autônoma |
| `cumprimento_judicial` | LGPD Art. 7º II + Art. 12 §1º | Ofício judicial; intimação; mandado | Não — obrigação legal |
| `comunicacao_servico_titular` | LGPD Art. 7º V | Notificação ao Cliente Final sobre status da OS, agendamento, recalibração, certificado emitido | Não para comunicação contratual; **SIM para WhatsApp marketing** |
| `anonimizacao_propagada` | LGPD Art. 7º II + Art. 18 VI + ADR-0021/0032 | Audit registrado por consumer cross-módulo após receber evento `Cliente.Anonimizado` | Não — propagação automática |

---

## Como usar no código

### Em `AuthorizationProvider.can()`

```python
provider.can(
    usuario_id=u.id,
    action="cliente.criar",
    resource={"tipo_pessoa": "PF"},
    tenant_id=t.id,
    purpose="execucao_contrato",  # ← string deste catálogo
)
```

A porta grava o `purpose` em `authz_decisions.purpose` (INV-AUTHZ-002). Auditoria ANPD: "quais cadastros foram feitos com base 'consentimento' em 2027?" responde com `SELECT ... WHERE purpose = 'consentimento'`.

### No aceite do cliente (`Cliente.aceite_lgpd_finalidade` — implementação opcional)

Por hora, o catálogo só vive aqui em texto. Quando Wave B (LGPD portal/DPO) precisar tabela formal, esta lista vira seed da tabela `lgpd_finalidades`.

---

## Não-finalidades (rejeitadas explicitamente)

- ~~`marketing_geral`~~ — dilui base; usar `consentimento` específico (RAT-06 WhatsApp).
- ~~`outros`~~ — sem propósito específico viola Art. 6º I (finalidade).
- ~~`pesquisa_interna`~~ — anonimizar dados (Art. 12 §1º) e reclassificar como `interesse_legitimo` se realmente preciso.

---

## Histórico

| Data | Mudança |
|------|---------|
| 2026-05-18 | Criação. 4 finalidades iniciais validadas pelo advogado. |
| 2026-05-23 | Onda 7 saneamento — 8 finalidades estendidas (obrigacao_regulatoria_iso17025, auditoria_cgcre, signatario_a3, responsavel_tecnico_tenant, tecnico_campo, defesa_em_juizo, cumprimento_judicial, comunicacao_servico_titular, anonimizacao_propagada). Trigger: auditoria projeto-inteiro lente 2 advogado-saas-regulado. Minuta — REQUER VALIDAÇÃO OAB antes do 1º tenant externo pago. |
