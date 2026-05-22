---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
---

# Controle de certificado emitido — WORM + revisão como nova versão

> **Pra quê:** ISO 17025 cláusula 8.4 + INV-001 exigem que certificado emitido **não pode ser modificado**. Toda "correção" vira nova versão visível, original preservado. Sem isso, vendor é cúmplice de fraude.
>
> **Revisado em 2026-05-23 (auditoria 10 lentes — TEMA-A.4 + TEMA-B.7 + TEMA-D.6):** doc movido conceitualmente pra subordinar-se a `metrologia/certificados/` (referência cruzada explícita); adicionada §7 com 2 declarações ISO 17025 cl. 7.8.3.1.b obrigatórias no template do certificado; §8 distingue correção administrativa vs recálculo técnico (cl. 7.8.8) com matriz de aprovação.

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

## 7. Declarações obrigatórias no template (cl. 7.8.3.1.b — TEMA-B.7)

> Adicionado em 2026-05-23. ISO 17025 §7.8.3.1.b exige declarações específicas no certificado emitido — CGCRE marca como NC documental se ausentes.

Todo template de certificado emitido carrega no corpo (não pode ser omitido):

**Declaração 1 — escopo dos resultados:**
> "Os resultados deste certificado se aplicam exclusivamente ao item calibrado, tal como recebido. Recalibrações periódicas são de responsabilidade do cliente."

**Declaração 2 — reprodução:**
> "Este certificado não pode ser reproduzido, parcial ou totalmente, sem aprovação escrita do laboratório emissor. Cópias digitais autênticas devem ser verificadas no portal público em `{URL_PORTAL_VERIFICADOR}` usando o código `{TOKEN_QR}`."

**Declaração 3 (quando aplicável):** se calibração foi emitida sob exceção `executor == revisor` (cl. 6.2.5 — ver `responsabilidade-tecnica.md §3.1`):
> "Conformidade ISO/IEC 17025 §6.2.5 — exceção registrada em audit ref. NC-####"

**Validação:**

- AC-CER-001-4 (a criar no `certificados/prd.md`) garante que as 3 declarações são campos obrigatórios do template.
- Hook `cert-template-declaracoes-check.sh` (Wave A) valida que template renderiza as 3 declarações.

---

## 8. Correção administrativa vs Recálculo técnico (cl. 7.8.8 — TEMA-D.6)

> Adicionado em 2026-05-23. ISO 17025 §7.8.8 distingue 2 naturezas de retificação — hoje sistema permitia RT sozinho fazer qualquer retificação. Matriz de aprovação cravada:

| Natureza | Exemplo | Quem aprova | Exige re-executar |
|---|---|---|---|
| **Correção administrativa** | erro de digitação no nome do cliente, CEP errado, e-mail do cliente errado | RT sozinho | Não (não toca conteúdo técnico) |
| **Recálculo técnico** | erro de cálculo, padrão errado escolhido, leitura errada inserida | RT + Conferente (2ª conferência completa) | **Sim** — re-executar US-CAL-007 + US-CAL-008 |
| **Alteração de decisão de conformidade** | mudou CONFORME → NÃO CONFORME ou inverso | RT + Gestor de Qualidade + cliente notificado por escrito | **Sim** — re-executar US-CAL-006 + US-CAL-007 + US-CAL-008 |

Enum `motivo_reemissao` no modelo Certificado (`certificados/modelo-de-dominio.md`): `CORRECAO_ADMINISTRATIVA | RECALCULO_TECNICO | ALTERACAO_DECISAO_CONFORMIDADE`.

Validação:

- Pre-condição em `reemissaoCertificado(certificado_id, motivo)`: a matriz acima é aplicada — se motivo=`RECALCULO_TECNICO`, sistema obriga reexecução US-CAL-007 + US-CAL-008 antes de emitir.
- Cliente é notificado por e-mail + portal quando há `ALTERACAO_DECISAO_CONFORMIDADE` (LGPD art. 6º VI transparência + CDC).

---

## 9. Conservação

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
