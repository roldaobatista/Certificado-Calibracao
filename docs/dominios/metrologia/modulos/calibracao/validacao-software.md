---
owner: Roldão
revisado-em: 2026-05-17
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

## 11. Referências

- ISO 17025:2017 cláusula 7.11
- ILAC G8 (regras de decisão)
- EURACHEM/CITAC Guide
- GAMP 5 (Good Automated Manufacturing Practice — guideline farma)
- `conformidade-iso-17025.md`
- `responsabilidade-tecnica.md`
