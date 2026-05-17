---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Conformidade ISO 17025:2017 — módulo Calibração

> **Pra quê:** mapear cada cláusula relevante da ISO/IEC 17025:2017 a invariante do Aferê (ID `INV-NNN` em `REGRAS-INEGOCIAVEIS.md`) + teste + hook. Sem esse mapa explícito, "conformidade ISO" vira marketing.
>
> **Escopo:** cláusulas que tocam **software de gestão laboratorial** (8.x) + emissão de certificado (7.x). Não cobre processos físicos de calibração (responsabilidade do lab usuário).

---

## 1. Cláusulas cobertas

| Cláusula | Tema | Coberta por | Verificação |
|----------|------|-------------|-------------|
| **7.7** Garantia da validade dos resultados | Replay determinístico, segundo caminho de cálculo independente da IA, hash | `garantia-validade-7.7.md` + `INV-007` | Teste automatizado: roda cálculo 2x, compara |
| **7.8** Emissão de relatórios (certificados) | Conteúdo mínimo + autenticação + cadeia de rastreabilidade | INV-002 + INV-009 + `controle-certificado-emitido.md` | Auditor Produto verifica AC; hook `INV-checker` |
| **7.10** Trabalho não-conforme | Registro de não-conformidade + ação corretiva + decisão de continuar/parar | INV-NC (a criar quando código existir) | Tela administrativa + audit log |
| **7.11** Controle de dados e gestão da informação (CRÍTICO) | Software validado + acesso controlado + backup + integridade + proteção de gravação não-autorizada + autorizações documentadas | INV-018 (dossiê) + INV-TENANT-001..004 + WORM + RBAC | `validacao-software.md` + `responsabilidade-tecnica.md` + `seguranca-dados.md` |
| **8.3** Controle de documentos | Documentos identificados, versionados, autorizados, atualizados, obsoletos retirados | Versionamento Git + `CONVENCOES-DOC.md` frontmatter `status` | Hook `paths-frontmatter-validator` + auditor produto |
| **8.4** Controle de registros | Retenção, legibilidade, integridade, proteção contra modificação | `retencao-matriz.md` + WORM + crypto-shredding por tenant | Drill DR + auditor segurança |
| **8.5** Ações para abordar riscos e oportunidades | RIPD/DPIA documentada quando aplicável | `seguranca-dados.md` §RIPD + RAT-07/09 | Roldão + DPO formal V2 |
| **8.6** Melhoria | Lições aprendidas → REGRAS-INEGOCIAVEIS atualizado; postmortem dispara regra nova | `incidente-postmortem.md` §7 | Painel-do-dono mostra postmortems abertos |
| **8.7** Ações corretivas | Causa raiz documentada + ação preventiva + verificação de eficácia | Template postmortem + entradas em `auditoria-decisoes-autonomas.md` | Auditor produto verifica fechamento |

---

## 2. Mapeamento INV → cláusula

| ID | Regra | Cláusula |
|----|-------|----------|
| INV-002 | Certificado de calibração não pode ser emitido sem cadeia rastreável completa (padrão → cadeia → unidade) | 7.8 + 7.11 |
| INV-009 | Toda revisão de certificado vira nova versão visível; original preservado em WORM | 7.8 + 8.4 |
| INV-018 | Vendor mantém dossiê de validação do software (URS/IQ/OQ/PQ) disponível pra auditoria CGCRE | 7.11 |
| INV-019 | Aplicação registra toda operação CRUD em audit trail com `user_id + tenant_id + timestamp + ação` | 7.11 + 8.4 |
| INV-020 | Lei 13.103/2015 (motorista profissional — técnico de campo): tempo de direção + descanso registrado | externo (jornada técnico, complementar) |
| INV-AGENT-001 | Agente IA classificado como "ferramenta computacional sob supervisão humana" — qualquer cálculo crítico passa por segundo caminho independente | 7.7 + 7.11 |
| SEC-003 | Input externo não-confiável não dispara ação em paths regulados (financeiro, kms, migrations, calibracao/) sem aprovação humana | 7.11 (proteção contra modificação não-autorizada) |

---

## 3. Cláusula 7.7 — detalhe especial (replay determinístico)

LLM não calcula incerteza. Aferê **emite certificados gerados deterministicamente** com:

1. **Entradas explícitas:** padrão usado + leituras + condições ambientais + método
2. **Cálculo em código testado** (não LLM): fórmulas NIT-DICLA-030 rev. 15 ou método declarado
3. **Hash de entrada:** SHA-256 do conjunto de entradas — permite replay
4. **Hash de saída:** SHA-256 do certificado emitido — permite verificação a posteriori
5. **Replay automático:** auditor de qualidade pode rodar segundo cálculo com mesma entrada e exigir output idêntico

Se LLM aparece no fluxo (sumarizar, formatar texto livre), o resultado **passa por adapter que separa "número" de "narrativa"** — número é gerado por código, narrativa é descrita pelo LLM e revista por humano antes de emissão.

Detalhe em `garantia-validade-7.7.md`.

---

## 4. Cláusula 7.8 — emissão de certificado

Conteúdo mínimo (ABNT NBR ISO/IEC 17025:2017 §7.8.2):
- Título: "Certificado de Calibração"
- Identificação única (número + revisão)
- Identificação do laboratório + endereço + competência (logo/acreditação RBC se aplicável)
- Identificação do cliente
- Identificação do item calibrado (descrição + número de série + observações de estado)
- Data da calibração + data de emissão
- Método utilizado (referência a norma ou procedimento interno)
- Condições ambientais (temperatura, umidade — quando aplicável)
- Resultado da calibração + unidade do SI + incerteza expandida (k=2, ~95%)
- Cadeia de rastreabilidade ao padrão nacional (INMETRO/RBC) ou internacional (BIPM)
- Identificação do signatário técnico (NIT-DICLA-021)
- Declaração de conformidade (se aplicável) com critério explícito (regra de decisão)
- Assinatura digital ICP-Brasil A3 + carimbo de tempo

**Aferê implementa:** template estruturado em Django Templates + PDF gerado via WeasyPrint + assinatura PAdES-LTV via pyhanko + A3 cliente-side via Web PKI Lacuna (ADR-0009).

---

## 5. Cláusula 7.11 — controle de dados e software (CRÍTICA)

ISO 17025 7.11.1: "O laboratório deve ter acesso aos dados e às informações necessárias para a realização das atividades laboratoriais."

ISO 17025 7.11.2: software comercial usado em atividade laboratorial **deve ser validado pelo desenvolvedor** ou **validado pelo lab** se feito in-house, e **revalidado quando houver atualização significativa**.

**Implicação operacional pro Aferê (vendor):**
- Manter **dossiê de validação do software** (URS/IQ/OQ/PQ) — ver `validacao-software.md`
- Disponibilizar dossiê pra tenant anexar em auditoria CGCRE
- Revalidação documentada a cada release major (e.g., v1.0 → v2.0)
- Acesso ao software controlado por RBAC + MFA pra papéis sensíveis (financeiro, signatário, admin)
- Backup + restore testado periodicamente (DR plan)
- Proteção contra modificação não-autorizada (RLS + WORM + hooks)

---

## 6. Cláusulas 8.3 + 8.4 — controle de docs + registros

Aferê implementa:
- **Versionamento Git** de toda documentação técnica
- **Frontmatter `status`** (draft/stable/deprecated) em todo doc
- **WORM Backblaze B2** pra audit log + certificados emitidos
- **`retencao-matriz.md`** reconciliando Receita 5 anos × ISO 25 anos × LGPD direito ao esquecimento
- **Crypto-shredding por tenant** pra exclusão segura mantendo compliance

---

## 7. Cláusula 8.5 — RIPD / DPIA

Operações de alto risco requerem RIPD documentada antes de release:
- ✅ RAT-07 (geolocalização técnico de campo) — antes do release mobile
- ✅ RAT-09 (telemetria) — antes de ligar product analytics
- ⏳ RAT condicional (LLM chatbot CS) — antes do release V2

Modelo em `docs/conformidade/comum/ripd-modelo.md` (a criar).

---

## 8. Cláusulas 8.6 + 8.7 — melhoria + ação corretiva

Todo postmortem (`incidente-postmortem.md`) gera:
- Linha do tempo
- Causa raiz (5 porquês)
- Ações de remediação com prazo + dono
- Regras novas em `REGRAS-INEGOCIAVEIS.md` (se aplicável)

Auditor de Produto verifica fechamento de cada ação no follow-up.

---

## 9. Auditoria

- **Pre-commit:** Auditor Segurança verifica violação de SEC/INV-TENANT
- **Pre-merge:** Auditor Produto verifica AC + non-goals + glossário
- **Trimestral (V2):** drill de auditoria interna (Roldão simula CGCRE)
- **Anual (V2):** revisão completa por consultor RBC credenciado (subagent `consultor-rbc-iso17025` prepara; humano contratado pontual)

---

## 10. Pendências

- [ ] Documentar URS (User Requirements Specification) do módulo Calibração
- [ ] Criar `ripd-modelo.md` (template RIPD/DPIA)
- [ ] Criar `validacao-software.md` ✅ (este lote)
- [ ] Criar `responsabilidade-tecnica.md` ✅ (este lote)
- [ ] Mapear método NIT-DICLA-030 rev. 15 em código testado (Wave A)
- [ ] Drill anual de auditoria CGCRE (V2 — quando 1º tenant RBC aparecer)

---

## 11. Referências

- ABNT NBR ISO/IEC 17025:2017
- NIT-DICLA-021 (RBC — qualificação do signatário técnico)
- NIT-DICLA-030 rev. 15 (incerteza de medição)
- ILAC P10 (rastreabilidade)
- ILAC G8 (regras de decisão)
- EURACHEM/CITAC Guide (incerteza de medição)
- `REGRAS-INEGOCIAVEIS.md` — INV-002, INV-009, INV-018, INV-019, INV-020, INV-AGENT-001, SEC-003
