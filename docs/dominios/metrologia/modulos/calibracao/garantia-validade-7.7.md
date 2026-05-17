---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Garantia da validade dos resultados (ISO 17025 cláusula 7.7)

> **Pra quê:** ISO 17025 7.7 exige que o lab "tenha um procedimento para monitorar a validade dos resultados". Em vendor de software, isso significa: **detectar se cálculo do software ficou errado** (bug, mudança de dependência, viés LLM). Sem isso, vendor é responsável por erros silenciosos que afetam decisões de clientes finais.
>
> **Origem:** INV-AGENT-001 (LLM nunca calcula valor crítico sem segundo caminho independente) + auditoria 12 agentes.

---

## 1. Princípio fundamental

**Aferê emite resultado metrológico via código testado, não via LLM.**

LLM pode aparecer no fluxo apenas pra:
- Sumarizar texto livre (observações do técnico, descrição do equipamento)
- Sugerir wording de mensagens (pra revisão humana antes de emitir)
- Classificar input
- Sugerir próxima ação

LLM **não calcula incerteza, não decide conformidade, não emite valor metrológico**. Esses fluxos passam por código determinístico testado.

---

## 2. Três defesas em série

### Defesa 1 — Replay determinístico

Toda cálculo crítico salva:
- **Hash SHA-256 das entradas** (padrão usado + leituras + condições ambientais + método)
- **Hash SHA-256 da saída** (valor + incerteza expandida + unidade)
- **Versão do código** (git tag + hash do arquivo de cálculo)

Auditor pode replay: passa as mesmas entradas, espera **byte a byte** o mesmo output. Se diverge:
- Bug introduzido em release nova
- Mudança em dependência crítica (lib de math)
- Corrupção de dado

→ Alerta SEV-1, certificado afetado fica em `REVISÃO_INTERNA`, postmortem obrigatório.

### Defesa 2 — Segundo caminho de cálculo

Pra fórmulas críticas (incerteza expandida, propagação de incerteza, conformidade):
- **Implementação primária** em Python (lib `numpy`/`scipy` ou código próprio)
- **Implementação verificadora independente** (lib alternativa, ou cálculo manual hardcoded em teste, ou comparação com tabela de referência)
- Pre-emissão: ambos rodam; se output diverge > tolerância → FAIL emissão

Implementação verificadora **não compartilha código** com a primária — propósito é detectar bug na primária.

### Defesa 3 — Tabela de referência

Pra métodos padronizados (NIT-DICLA-030 rev. 15, ILAC G8, EURACHEM):
- Conjunto de **valores de referência conhecidos** (entrada + saída esperada)
- Suite de testes roda esses valores a cada commit
- Se output diverge → FAIL build

Exemplo: pra propagação de incerteza, ter ≥ 5 casos de referência da bibliografia EURACHEM com resultado esperado documentado.

---

## 3. Quando aplica

Defesas obrigatórias em:
- Cálculo de incerteza expandida (k=2, ~95%)
- Cálculo de propagação de incerteza
- Avaliação de conformidade (LSL/USL + regra de decisão ILAC G8)
- Conversão de unidades SI ↔ proprietárias
- Cálculo de coeficiente de calibração

Defesas opcionais (boas práticas):
- Cálculo de média/desvio-padrão de série de medições
- Estatística básica de controle (cartas X-R, etc.)

---

## 4. Como LLM se encaixa

LLM **só toca em texto livre**, nunca em valor numérico crítico.

Fluxo seguro:
```
Operador faz medição → técnico digita leituras → código calcula incerteza
                                                          ↓
                                              Defesas 1+2+3 em série
                                                          ↓
                                              Resultado numérico determinístico
                                                          ↓
LLM compõe RELATÓRIO TEXTUAL (observações, recomendações)
                                                          ↓
Humano revisa antes de emitir
                                                          ↓
PDF + A3 + WORM
```

Fluxo inseguro (proibido):
```
Operador → LLM: "calcule a incerteza" → certificado
```
(Bloqueado em pre-merge pelo Auditor Segurança via INV-AGENT-001).

---

## 5. Monitoramento contínuo

Em produção (V2 quando deploy autorizado):
- Painel Grafana mostra **% de cálculos que passaram nas 3 defesas**
- Alerta SEV-1 se taxa cai < 99.5%
- Drill mensal: forçar bug em ambiente staging, conferir que defesa pega

Em ambiente local (janela atual):
- Suite de testes inclui cenários de "valor errado de propósito" — verificar que ao menos uma defesa bloqueia

---

## 6. INV-AGENT-001 — texto literal

> "Agente IA (LLM) classificado como ferramenta computacional sob supervisão humana. **Qualquer cálculo numérico que afete valor metrológico (resultado, incerteza, conformidade) DEVE passar por segundo caminho independente de cálculo** (defesa 2 acima) E ser comparado com tabela de referência (defesa 3) E ter replay determinístico habilitado (defesa 1). Falha em qualquer defesa = certificado não emitido."

Hook + Auditor Segurança enforce em pre-commit.

---

## 7. Casos limites

| Cenário | Tratamento |
|---------|-------------|
| Lib `numpy` recebe atualização que muda comportamento de função usada | Defesa 1 dispara (replay diverge); SEV-1; investiga + congela versão |
| Tabela de referência tem erro de transcrição (humano errou ao copiar) | Defesa 2 e 3 divergem ambas; humano investiga + corrige tabela; nova versão validada |
| Cálculo legítimo na fronteira da tolerância | Tolerância ajustada via ADR; teste de regressão adicionado |
| LLM consultado pelo usuário "qual é a incerteza pra esse caso?" | LLM responde "consulte o módulo de cálculo do Aferê, esta é função do software". Não calcula. |
| Cliente final pede recálculo de certificado antigo | Replay determinístico roda; output preservado em WORM bate; certificado válido |

---

## 8. Pendências

- [ ] Implementar lib primária de cálculo de incerteza (Wave A)
- [ ] Implementar lib verificadora independente (Wave A)
- [ ] Coletar tabela de referência EURACHEM/ILAC pra ≥ 5 casos
- [ ] Pytest: cenários determinísticos + cenários "valor errado"
- [ ] Hook `replay-validator.sh` em PostToolUse (a criar Wave A)
- [ ] Painel Grafana "Validade 7.7" (V2 quando deploy)

---

## 9. Referências

- ISO 17025:2017 cláusula 7.7
- INV-AGENT-001 em `REGRAS-INEGOCIAVEIS.md`
- NIT-DICLA-030 rev. 15
- EURACHEM/CITAC Guide
- ILAC G8 (regras de decisão)
- BIPM JCGM 100:2008 (GUM — Guide to the expression of uncertainty in measurement)
- `conformidade-iso-17025.md`
- `validacao-software.md`
