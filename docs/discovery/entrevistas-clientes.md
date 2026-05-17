# Discovery — Entrevistas com clientes

> **Artefato Rodada 0** (Roldão entrevista, Agente sintetiza). Conjunto de transcrições/atas + síntese cruzada. Estrutura em 3 ondas (Auditor 6 v2):

---

## Plano de amostra

| Onda | Quantas | Quem | Foco | Quando |
|---|---|---|---|---|
| **1** | 3 entrevistas | Donos de OUTRAS assistências técnicas + laboratórios RBC | Mapear PROBLEMA — não solução | Após treinamento + 2 pilotos |
| **2** | 6 entrevistas | OPERADORES (3 perfis × 2 cada): atendente, técnico de campo, financeiro | Mapear WORKFLOW REAL — dor de quem usa | Após onda 1 + síntese parcial |
| **3** | 3 entrevistas | Mix (1 dono + 1 operador + 1 metrologista) | VALIDAR solução com protótipo de papel | Após `validacao-ativa.md` ter smoke test pronto |

**Total: 12 entrevistas em 3 ciclos com aprendizado entre eles.**

---

## Critério de saída (Auditor 6 v2 alertou — travar ANTES de começar)

A onda atual termina quando:

- Atingiu o nº mínimo de entrevistas planejado.
- **Saturação documentada:** 3 entrevistas seguidas sem insight novo significativo. Se ainda surge insight, estender amostra.
- Leap-of-faith identificado em `assumption-map.md` foi validado com dado externo (não só opinião auto-reportada).
- Auditor de Produto deu OK na qualidade das atas.

**Sem critério explícito, "queremos lançar logo" vence sempre.**

---

## Estrutura desta pasta

```
discovery/
├── entrevistas-clientes.md          ← este arquivo (visão geral + síntese)
├── entrevistas/
│   ├── 001-empresa-anonima-A.md    ← ata individual
│   ├── 002-empresa-anonima-B.md
│   └── ...
└── ...
```

Cada ata segue template em `treinamento-entrevista-roldao.md` seção "Template de ata".

---

## Síntese cruzada (a preencher após cada onda)

### Onda 1 — Donos (problema)
**Status:** ⏳ não iniciada

**Top 5 dores recorrentes:**
1. (vazio)
2. (vazio)
3. (vazio)
4. (vazio)
5. (vazio)

**Convergências:** (o que apareceu em ≥2/3 entrevistas)
**Divergências:** (o que apareceu em 1 só)
**Surpresas:** (o que NÃO foi esperado)
**Validations:** (premissa confirmada)
**Invalidations:** (premissa derrubada — atualizar `assumption-map.md`)

### Onda 2 — Operadores (workflow)
**Status:** ⏳ não iniciada

(mesmo formato)

### Onda 3 — Validação de solução
**Status:** ⏳ não iniciada

(mesmo formato + reação ao protótipo)

---

## Anonimização

- Empresa: usar pseudônimo (Empresa A, B, C) em síntese cruzada e em docs públicos.
- Pessoa: usar papel + número (Dono-1, Técnico-3) em síntese; nome real só na ata individual com consentimento.
- Citação literal: ✅ ok; identificação: ❌.
- Áudio gravado: armazenamento local + B2 WORM, retenção 2 anos, criptografado.

---

## Anti-customização (founder is customer)

> ⚠️ **CRÍTICO:** Roldão é o primeiro cliente. Tentação natural: ouvir dores que coincidem com as DELE e ignorar o resto. Anti-padrão clássico.

Mitigação:
- **Cada ata tem campo** "isso bate com a dor do Roldão? Onde converge? Onde diverge?"
- **Auditor de Produto sinaliza** quando síntese reflete >70% das opiniões do próprio Roldão (provável viés de confirmação).
- Pelo menos 1 entrevista por onda deve ser com empresa de PERFIL DIFERENTE da do Roldão (porte / segmento / região).
