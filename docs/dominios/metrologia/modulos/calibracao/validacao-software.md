---
owner: Roldão
revisado_em: 2026-05-23
status: draft
---

# Validação de software — dossiê IQ/OQ/PQ

> **Pra quê:** ISO 17025 cláusula 7.11 exige que software usado em atividade laboratorial seja **validado**. Como Aferê é o vendor, **Aferê mantém o dossiê de validação** e entrega ao tenant pra anexar em auditoria CGCRE.
>
> **Padrão usado:** ILAC G8 + EURACHEM Guide + GAMP 5 (V2 quando RT aparecer).

---

## 1. Conceitos

- **URS** (User Requirements Specification): o que o usuário/lab precisa que o software faça
- **IQ** (Installation Qualification): instalação + ambiente conferem com o projetado
- **OQ** (Operational Qualification): software opera dentro de parâmetros esperados
- **PQ** (Performance Qualification): software atende necessidades reais de uso em produção

---

## 2. Estado atual (pré-código)

| Item | Status |
|------|--------|
| URS módulo Calibração | ⏳ a criar (Wave A) |
| URS módulo Financeiro/NFS-e | ⏳ a criar |
| URS módulo OS | ⏳ a criar |
| IQ ambiente Docker compose local | ⏳ a criar (Foundation F-A) |
| IQ ambiente produção (Hostinger) | ⏸️ dormente — deploy não autorizado |
| OQ cenários básicos | ⏳ a criar com pytest |
| PQ casos reais Balanças Solution | ⏳ pós-Wave A |
| Revalidação a cada release major | ⏳ política definida; primeira ainda não aconteceu |

---

## 3. URS — estrutura padrão

Cada módulo regulado tem URS com:

1. **Identificação:** nome do módulo, versão, autor, data
2. **Escopo:** o que o módulo faz (e o que NÃO faz — non-goals)
3. **Requisitos funcionais:** lista numerada (`URS-CAL-001`, etc.) com critério binário de aceitação
4. **Requisitos não-funcionais:** performance, segurança, multi-tenant, etc.
5. **Restrições regulatórias:** ISO 17025 cláusulas mapeadas
6. **Glossário:** termos do domínio
7. **Aprovação:** assinatura do Roldão + signatário técnico (V2)

---

## 4. IQ — Installation Qualification

Verifica que o ambiente onde o software roda está conforme projetado.

### Checklist IQ (ambiente local dogfooding)

- [ ] PostgreSQL 16+ instalado
- [ ] Docker compose roda sem erros
- [ ] Variáveis de ambiente (`.env`) configuradas
- [ ] Migrations rodam (tudo idempotente)
- [ ] Usuário admin criado
- [ ] Tenant Balanças Solution provisionado
- [ ] Smoke test 1: login → criar cliente → criar OS → emitir certificado
- [ ] Smoke test 2: query cross-tenant retorna 0 rows (RLS valida)
- [ ] Hooks ativos no repo
- [ ] Hash do binário/imagem Docker registrado

### Checklist IQ (produção — ⏸️ dormente)

[Detalhes ativam quando Roldão autorizar deploy]

---

## 5. OQ — Operational Qualification

Verifica que software opera dentro de parâmetros.

### Cenários OQ mínimos (módulo Calibração)

| ID | Cenário | Critério de aceitação |
|----|---------|------------------------|
| OQ-CAL-001 | Emitir certificado com dados válidos | PDF gerado em < 10s; hash registrado; audit log |
| OQ-CAL-002 | Tentar emitir sem signatário | Bloqueio + mensagem clara em PT-BR |
| OQ-CAL-003 | Cálculo de incerteza com entrada conhecida | Output bate com valor de referência ±0.0001 |
| OQ-CAL-004 | Replay determinístico (rodar mesmo cálculo 2x) | Outputs idênticos byte a byte |
| OQ-CAL-005 | Revisar certificado emitido | Nova versão criada; original preservado WORM |
| OQ-CAL-006 | Tentar deletar certificado emitido | Bloqueio + audit |
| OQ-CAL-007 | Cliente A tenta ver certificado de cliente B | Bloqueio RLS + 0 rows |
| OQ-CAL-008 | Signatário com competência X tenta assinar certificado tipo Y (fora escopo) | Bloqueio + mensagem |

Implementação: cada cenário OQ vira teste `pytest` cujo nome cita o ID. Hook `INV-checker` confirma cobertura.

---

## 6. PQ — Performance Qualification

Verifica que software atende necessidades reais.

PQ rodará na Balanças Solution durante dogfooding:
- 1º mês: registrar todos os usos reais + medir aderência ao OQ
- Postmortem de qualquer divergência
- Ajuste de URS/OQ se necessário (com revalidação)

---

## 7. Revalidação

Disparada por:
- **Release major** (e.g., v1.0 → v2.0): revalidação completa (URS + IQ + OQ + PQ)
- **Mudança de dependência crítica** (PostgreSQL major, Django LTS, lib de assinatura): IQ + OQ reduzido
- **Mudança regulatória** (nova versão NIT-DICLA, ISO 17025): URS revisado + OQ ajustado
- **Bug em produção que afetou certificado emitido**: postmortem + OQ ampliado

---

## 8. Dossiê — onde fica

```
docs/dominios/metrologia/modulos/calibracao/
├── validacao-software.md     ← este doc
├── urs/
│   ├── URS-CAL-001-emissao-certificado.md
│   ├── URS-CAL-002-calculo-incerteza.md
│   └── ...
├── iq/
│   ├── IQ-LOCAL.md
│   └── IQ-PROD.md             ⏸️ dormente
├── oq/
│   ├── relatorio-OQ-v1.0.md   ← gerado de pytest output + auditor produto
│   └── cenarios.md
└── pq/
    └── relatorio-PQ-balancas-solution.md  ← gerado pós-dogfooding
```

URS / IQ / OQ / PQ ficam **versionados em Git** (D2 spec-as-source). Releases assinadas com tag + hash do dossiê associado.

---

## 9. Entrega ao tenant

Quando tenant acreditado RBC pedir dossiê pra auditoria CGCRE (V2):
1. Subagent `consultor-rbc-iso17025` gera pacote consolidado (URS + IQ + OQ + PQ + cláusulas mapeadas)
2. Assinado pelo RT do vendor (humano contratado — V2)
3. Entregue em formato PDF + Git tag de referência
4. Audit log da entrega

---

## 10. Pendências

- [ ] Criar pasta `urs/`, `iq/`, `oq/`, `pq/` quando Wave A começar
- [ ] Primeira URS: módulo Calibração — emissão de certificado
- [ ] Cenários OQ-CAL-001..008 como testes pytest
- [ ] RT do vendor contratado (V2)
- [ ] Drill anual de auditoria CGCRE (V2)

---

## 12. Esqueleto URS/IQ/OQ/PQ (novo Onda 7 — A3-CAL)

> Esqueleto com IDs + responsabilidade. Detalhes preenchidos Wave A no momento de codar cada US correspondente.

### URS — User Requirements Specification (cl. 7.11.2)

| ID | Requisito | US relacionada | Responsável | Critério binário |
|---|---|---|---|---|
| URS-CAL-001 | Sistema recebe instrumento + gera etiqueta QR Code | US-CAL-001 | metrologista | etiqueta gera em ≤ 5s; QR aponta ao registro correto |
| URS-CAL-002 | Sistema configura calibração (grandeza, faixa, pontos, método) | US-CAL-002 | metrologista | configuração persiste; validação CMC bloqueia fora de escopo |
| URS-CAL-003 | Sistema valida vigência de padrão antes de selecionar | US-CAL-003 | RT | padrão vencido bloqueia seleção |
| URS-CAL-004 | Sistema registra leituras manuais e via integração | US-CAL-004 | metrologista | leitura persiste com timestamp; integração serial/USB funcional |
| URS-CAL-005 | Sistema calcula erro + incerteza GUM com orçamento ponto-a-ponto | US-CAL-005 | metrologista | resultado bate com referência ±0.0001; orçamento auditável |
| URS-CAL-006 | Sistema avalia conformidade com regra de decisão (ADR-0024) | US-CAL-006 | RT | classifica CONFORME/NÃO-CONFORME/ZONA INCERTEZA; regra documentada no cert |
| URS-CAL-007 | Sistema enforça 2ª conferência independente (ADR-0026) | US-CAL-007/008 | RT | exceção executor==revisor exige 4 condições + 5%/mês |
| URS-CAL-008 | Sistema vincula procedimento vigente na data de execução (ADR-0030) | US-CAL-016 | metrologista | predicate `procedimento_vigente_para` resolve ou bloqueia 412 |
| URS-CAL-009 | Sistema permite Recall em batch por versão de motor (ADR-0045) | US-CER-018 | gestor qualidade | notifica cliente em 24h + ANPD cond + CGCRE em 30d |
| URS-CAL-010 | Sistema preserva snapshot do cliente pós-anonimização (ADR-0021) | US-CER-002 AC-4 | sistema | `cliente_nome_snapshot` imutável em WORM |

### IQ — Installation Qualification (cl. 7.11.4)

| ID | Item | Local | Critério |
|---|---|---|---|
| IQ-CAL-001 | PostgreSQL 16 + RLS ativo + roles NOBYPASSRLS | local + prod | comando `verificar_objetos_seguranca` PASS |
| IQ-CAL-002 | Docker compose roda + migrations rodam idempotente | local | `docker compose up` + `migrate` retorna 0 |
| IQ-CAL-003 | KMS Multi-Region Key configurada (sa-east-1 + us-east-1) | prod | smoke encrypt/decrypt + replica |
| IQ-CAL-004 | B2 WORM bucket `certificados-wormA` criado + retenção 25a | prod | bucket lifecycle policy PASS |
| IQ-CAL-005 | TSA-ITI alcançável (ADR-0044) | prod | round-trip carimbo < 3s |

### OQ — Operational Qualification (cl. 7.11.5)

| ID | Cenário | Critério binário |
|---|---|---|
| OQ-CAL-001 | Emitir cert com dados válidos | PDF/A-3 gerado em <3s; hash registrado; audit log; XML embedded validado |
| OQ-CAL-002 | Tentar emitir sem signatário | Bloqueio 412 + mensagem PT-BR |
| OQ-CAL-003 | Cálculo de incerteza com entrada conhecida | Output bate com valor de referência ±0.0001 |
| OQ-CAL-004 | Replay determinístico (mesmo cálculo 2x) | Outputs idênticos byte a byte (cl. 7.11 + ADR-0025) |
| OQ-CAL-005 | Reemitir cert | Nova versão criada; original SUBSTITUIDA preservado WORM |
| OQ-CAL-006 | Tentar deletar cert emitido | Bloqueio + audit (INV-001) |
| OQ-CAL-007 | Cliente A consulta cert de cliente B | 0 rows (RLS) |
| OQ-CAL-008 | Signatário sem competência tenta assinar | Bloqueio + mensagem (INV-CER-COMP-001) |
| OQ-CAL-009 | Recall em batch por `versao_motor_calculo` | Todos cert da versão buggy viram `RECALL_ATIVO` + eventos publicados |
| OQ-CAL-010 | Suspensão + levantamento preserva `dias_suspensao_acumulada` | Vigência retoma do ponto exato |

### PQ — Performance Qualification (cl. 7.11.6)

| ID | Critério | Janela | Responsável |
|---|---|---|---|
| PQ-CAL-001 | Balanças Solution opera 1 mês com cert emitidos sem NC | 30 dias pós-Wave A | Roldão + gestor qualidade |
| PQ-CAL-002 | Tempo médio recepção→aprovação ≤ 3 dias úteis | 30 dias | metrologista |
| PQ-CAL-003 | Zero gap de numeração | contínuo | sistema (`job_certificado_gap_detection`) |
| PQ-CAL-004 | Zero cert RBC emitido fora do escopo | contínuo | sistema (INV-CAL-DEC-001) |
| PQ-CAL-005 | Replay determinístico em amostra mensal de 10 cert (2º caminho ADR-0025) | mensal | gestor qualidade |

> Cada ID URS/IQ/OQ/PQ acima exige: (a) preenchimento detalhado em arquivo próprio Wave A; (b) ≥1 teste pytest cujo nome cita o ID (TST-004); (c) revalidação por release major (cl. 7.11 + GAMP 5).

---

## 11. Referências

- ISO 17025:2017 cláusula 7.11
- ILAC G8 (regras de decisão)
- EURACHEM/CITAC Guide
- GAMP 5 (Good Automated Manufacturing Practice — guideline farma)
- `conformidade-iso-17025.md`
- `responsabilidade-tecnica.md`
