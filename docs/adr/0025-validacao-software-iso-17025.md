---
adr: 0025
titulo: Validação de software ISO/IEC 17025 cl. 7.11 — URS/IQ/OQ/PQ + replay determinístico + 2º caminho
status: aceito
data: 2026-05-23
aceito-em: 2026-05-23 (Onda 6 saneamento — destravar Marco 4 calibração)
proposto-por: agente (auditoria 10 lentes — TEMA-F.2)
revisado-por: consultor-rbc-iso17025 + tech-lead-saas-regulado
bloqueia-fase: Wave A Marco 4 (calibracao) + V2 (RT vendor)
depende-de: ADR-0007 (camada domínio + gerador spec→código)
---

# ADR-0025 — Validação de software ISO/IEC 17025 cl. 7.11

## Contexto

ISO 17025 cl. 7.11 (uso de software no laboratório) exige validação documentada: URS (User Requirements Spec), IQ (Installation Qualification), OQ (Operational Qualification), PQ (Performance Qualification), CSV (Computer System Validation). `validacao-software.md` existe mas é doc operacional — **decisão estrutural não tem ADR**.

Auditoria 10 lentes (consultor-rbc-iso17025 — TEMA-F.2) marcou como ALTO antes de Marco 4 começar.

## Decisão

**Promover `validacao-software.md` + `garantia-validade-7.7.md` a base de uma ADR estrutural**, cravando:

### 1. Dossiê de validação por release (INV-019 já existe)

Toda release pública gera:

- **URS** — requisitos do usuário (alimentado pelas US do PRD).
- **IQ** — instalação ambiente Docker compose local + verificação `verificar_objetos_seguranca`.
- **OQ** — bateria de testes operacionais (E2E + drill multi-tenant).
- **PQ** — desempenho em produção controlada (dogfooding Balanças Solution).
- **Assinatura A3 do RT-vendor** (quando contratado em V2 — INV-018).
- **Change log** + matriz de impacto.
- Disponibilizado pra tenant em até 48h.

### 2. Versionamento do motor de cálculo (INV-005 + INV-004c)

Cada `OrcamentoIncerteza` carrega `versao_motor_calculo` (texto, ex: `"motor-incerteza-v1.2.0"`). Imutável após calibração APROVADA. Permite recall de certificados por versão se erro descoberto.

### 3. Replay determinístico (Defesa 1 da garantia-validade-7.7)

- Mesma entrada → mesmo hash de saída entre 2 execuções da MESMA versão do motor.
- Diferença entre execuções = bug crítico → bloqueia release.
- Hook `replay-deterministico-check.sh` em CI roda bateria de calibrações de referência + compara hashes.

### 4. Segundo caminho de cálculo (Defesa 2 — INV-AGENT-001)

- Motor de cálculo principal (Python `motor-incerteza-v1.2.0`).
- Motor de cálculo de validação (segundo caminho — pode ser implementação independente em outra linguagem ou OSS de referência).
- Em calibrações de alta criticidade (cert RBC), AMBOS os caminhos rodam e resultado convergente é exigido.

### 5. Operações de migração de dados (cl. 7.11.3 — TEMA-M.4)

Migration Django que toca tabela de domínio metrologia (`calibracao`, `leitura`, `orcamento_incerteza`, etc.) declara em frontmatter:

```python
# metrology-affecting: yes
# impact-analysis-doc: docs/.../migration-NNNN-impacto.md
```

Hook `migration-metrology-classifier.sh` valida que migration com `metrology-affecting: yes` tem dossiê de impacto + replay determinístico em conjunto de dados pré-existentes (TEMA-M.4).

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Dossiê manual sem CI | Vira pendência crônica; INV-019 já cravou que CI bloqueia release sem dossiê |
| Sem 2º caminho de cálculo | Risco de "calibração de calibração" — não há cruz-check. Inaceitável pra RBC |
| Versionamento implícito (tag Git) | INV-005 exige campo persistido no certificado pra recall posterior |

## Consequências

### Positivas

- ISO 17025 §7.11 cravada como decisão arquitetural (não doc operacional volátil).
- CI bloqueia release sem dossiê (INV-019 já em REGRAS-INEGOCIAVEIS).
- Recall de certificados por versão do motor possível (INV-004c).
- Replay determinístico em CI detecta bug não-determinístico precocemente.

### Negativas (mitigáveis)

- Custo de construir 2º caminho de cálculo (estimado 3-6 semanas Wave A).
- Treinamento operacional Marco 4 + V2 (RT vendor).

## Non-goals

- NÃO substitui consultor RBC humano em supervisão CGCRE real (V2).
- NÃO valida software de TERCEIRO (Lacuna PKI, Backblaze) — apenas garante uso adequado.

## Invariantes novas

- **INV-CAL-VAL-001:** release pública SEM dossiê IQ/OQ/PQ assinado pelo RT-vendor (V2) BLOQUEIA deploy (INV-019 reforçada).
- **INV-CAL-VAL-002:** migration tocando entidade metrológica SEM `metrology-affecting:` declarado + impact-analysis-doc BLOQUEIA merge.
- **INV-CAL-VAL-003:** calibração RBC exige replay determinístico OK + 2º caminho convergente (delta ≤ tolerância documentada). Sem isso, emissão bloqueia.

## Implicações pro faseamento

- Marco 4 implementa motor v1 (Python) + replay determinístico em CI.
- V2 contrata RT-vendor humano → começa a assinar dossiês IQ/OQ/PQ.
- Wave B implementa 2º caminho de cálculo (3-6 semanas).

## Status

Proposta — aguarda aceite Roldão antes de Marco 4 começar. Consultor-rbc-iso17025 humano revisa antes do 1º tenant RBC acreditado (V2-V3).
