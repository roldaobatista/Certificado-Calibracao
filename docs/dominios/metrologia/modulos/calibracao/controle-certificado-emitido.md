---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Controle de certificado emitido — WORM + revisão como nova versão

> **Pra quê:** ISO 17025 cláusula 8.4 + INV-009 exigem que certificado emitido **não pode ser modificado**. Toda "correção" vira nova versão visível, original preservado. Sem isso, vendor é cúmplice de fraude.

---

## 1. Princípio

> **Certificado emitido é imutável.**

A partir do momento em que o certificado é assinado A3 + carimbo de tempo + entregue ao cliente final, o conteúdo NÃO pode ser modificado. Nem por root no banco, nem por bug, nem por má-fé.

---

## 2. Mecanismo técnico

| Camada | Como protege |
|--------|--------------|
| **WORM Backblaze B2 Object Lock** | Bucket configurado com retenção compliance mode — nem credencial AWS root consegue deletar antes do prazo |
| **Hash SHA-256 do PDF** | Calculado na emissão e registrado em audit trail; consulta posterior compara hash atual com original |
| **Assinatura PAdES-LTV** | Documento autoassinado; qualquer alteração quebra a assinatura |
| **PostgreSQL audit trail append-only** | Tabela `certificados` tem trigger `BEFORE UPDATE/DELETE` que bloqueia mudança em certificados com status `emitido` |
| **RLS + tenant_id** | Tenant A não vê nem altera certificados de tenant B (INV-TENANT) |
| **Teste automatizado de tentativa de mutação** | OQ-CAL-006 confirma que tentativa de delete/update falha |

---

## 3. Status do certificado

Máquina de estados:

```
RASCUNHO → REVISAO_INTERNA → ASSINATURA_PENDENTE → EMITIDO ↔ REVISADO
                                                       ↓
                                                  CANCELADO
```

- **RASCUNHO:** editável; sem audit relevante
- **REVISÃO_INTERNA:** revisão pelo signatário antes de assinar
- **ASSINATURA_PENDENTE:** aguardando A3 do signatário
- **EMITIDO:** imutável; WORM + hash + signed
- **REVISADO:** revisão posterior criou NOVA versão; original preservado
- **CANCELADO:** flag de cancelamento + razão; conteúdo original preservado (NÃO deletado)

---

## 4. Revisão como nova versão

Se cliente identifica erro num certificado emitido, fluxo:

1. **Identificar erro** (cliente ou lab)
2. **Nova revisão começa** (status `RASCUNHO` em registro novo; link pra certificado original)
3. **Editar dados corrigidos** + razão da revisão
4. **Revisão técnica** (signatário valida)
5. **Assinatura A3** (novo carimbo de tempo)
6. **Emissão da revisão** (status `EMITIDO`; numeração `123/2026-rev2`)
7. **Original muda status pra `REVISADO`** (mas conteúdo preservado em WORM)
8. **Audit log:** quem fez revisão, quando, qual razão, quais campos mudaram

UI deve mostrar histórico de revisões com diff visual.

---

## 5. Cancelamento

Se certificado tem erro grave e a revisão não é apropriada (e.g., calibração errada pra equipamento errado):
1. Status muda pra `CANCELADO` + razão
2. PDF do original preservado WORM
3. Audit log obrigatório
4. Cliente final é notificado
5. Se cliente final já entregou pra auditoria externa: anexar nova versão + comunicado

Cancelamento **NÃO deleta** — preserva pra rastreabilidade.

---

## 6. Numeração

Padrão: `{NN}/{AAAA}-rev{N}`
- `NN` = número sequencial do tenant no ano
- `AAAA` = ano
- `revN` = revisão (omitido se rev 1)

Exemplo: `42/2026` (original), `42/2026-rev2` (1ª revisão), `42/2026-rev3` (2ª revisão).

Numeração reservada **por tenant** (cada tenant tem seu contador). RLS garante isolamento.

---

## 7. Conservação

Ver `retencao-matriz.md`:
- **Certificado emitido:** ~25 anos (ISO 17025 8.4) — efetivamente permanente
- **Storage:** Backblaze B2 EU Central com Object Lock
- **Chave de criptografia:** AWS KMS por tenant; **NÃO** destruir antes de 25 anos
- **Crypto-shredding** só após prazo legal completo OU se tenant pede exclusão LGPD + certificado não tem mais obrigação regulatória

Conflito Receita 5 anos × ISO 25 anos × LGPD esquecimento: resolvido em `retencao-matriz.md` cenário "manter certificado, anonimizar PII do signatário após 5 anos".

---

## 8. Auditoria

Auditor Segurança verifica em pre-commit:
- Diff que adiciona `UPDATE certificados SET ...` em código sem trigger de proteção → FAIL
- Diff que deleta linha de `certificados` em código → FAIL
- Diff que muda bucket B2 sem Object Lock → FAIL

Auditor Produto verifica em pre-merge:
- AC de revisão sempre cria registro novo, não sobrescreve
- AC de cancelamento preserva original

Drill trimestral: tenta mutar certificado emitido por SQL direto + via API → ambos falham.

---

## 9. Hook específico a criar

`certificate-immutability.sh` (PostToolUse Write|Edit em código que toca `certificates/`):
- Detecta `cert.save()` em registro com `status='EMITIDO'` → FAIL
- Detecta `Certificate.objects.filter(...).update(...)` sem filtro `status__ne='EMITIDO'` → FAIL
- Detecta `.delete()` em `Certificate` → FAIL

A criar quando módulo Calibração começar.

---

## 10. Referências

- ISO 17025:2017 cláusula 8.4 (controle de registros)
- INV-009 (revisão como nova versão)
- `retencao-matriz.md` (~25 anos)
- `conformidade-iso-17025.md` (cláusulas)
- `garantia-validade-7.7.md` (hash + replay)
