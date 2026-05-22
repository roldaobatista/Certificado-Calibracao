---
owner: claude-code
revisado-em: 2026-05-23
status: stable
escopo: módulo equipamentos — textos canônicos de rejeição 422 (INV-025 imutabilidade pós-certificação)
relacionados:
  - REGRAS-INEGOCIAVEIS.md (INV-025)
  - docs/faseamento/M2-equipamentos/spec.md (AC-EQP-002-2)
  - docs/faseamento/M2-equipamentos/plan.md (P-EQP-A3)
versao_canonica: 1.0.0
fundamento_legal: ISO/IEC 17025 cl. 8.4 + LGPD art. 6º V (exatidão)
---

# Textos canônicos de rejeição 422 — equipamento com certificado emitido

> **Pra quê:** quando o usuário tenta editar campo imutável de um
> equipamento que já tem certificado emitido, o sistema responde **HTTP
> 422 Unprocessable Entity** com um dos 5 textos pré-aprovados abaixo.
> O texto é **igual sempre** (não é gerado por LLM, não tem variação
> dependente de contexto) — isso permite que o agente IA, o frontend e
> a documentação de help apontem para a mesma string canônica.
>
> **Origem:** parecer `advogado-saas-regulado` (P-EQP-A3 / AC-EQP-002-2)
> + decisão em `docs/faseamento/M2-equipamentos/plan.md` (2026-05-22).
>
> **Atualização desta lista:** mudança de texto exige PR revisado pelo
> `advogado-saas-regulado` + bumping de `versao_canonica` no frontmatter.

---

## Por que texto canônico (não geração livre)

ISO/IEC 17025 cl. 8.4 exige **rastreabilidade documental imutável** de
registros técnicos pós-emissão de certificado. O CGCRE auditor lê o
texto exato exibido ao usuário pra confirmar que o tenant não pode
alterar dado de equipamento sob certificado vigente. Variação por LLM
ou por linguagem regional quebra essa rastreabilidade.

Cravado em [AC-EQP-002-2](../../faseamento/M2-equipamentos/spec.md):
"422 com texto PT-BR de 5 variantes pré-aprovadas (advogado) citando
'ISO 17025 cl. 8.4 — registros técnicos imutáveis pós-emissão'."

---

## T1 — Tentativa de alterar TAG operacional

**Quando dispara:** PATCH em `Equipamento.tag` quando existe certificado
EMITIDO (não revogado) referenciando este equipamento.

**Texto canônico (`T1`):**

```
A TAG operacional não pode ser alterada porque já existe certificado
emitido para este equipamento. A TAG aparece no documento técnico
assinado, e ISO/IEC 17025 cl. 8.4 exige imutabilidade do registro
técnico pós-emissão. Crie uma nova versão do equipamento (mudança
controlada documentada) ou registre o caso como anomalia de
identificação no recebimento.
```

---

## T2 — Tentativa de alterar número de série

**Quando dispara:** PATCH em `Equipamento.numero_serie` quando existe
certificado EMITIDO.

**Texto canônico (`T2`):**

```
O número de série não pode ser alterado porque já existe certificado
emitido referenciando este número. ISO/IEC 17025 cl. 8.4 exige que a
identificação inequívoca do equipamento no certificado seja imutável
após emissão. Se o número gravado fisicamente está incorreto e foi
descoberto agora, registre o caso como não conformidade (NC) no fluxo
do laboratório — o certificado existente seguirá referenciando o número
ANTERIOR, e o novo número entrará a partir da próxima calibração.
```

---

## T3 — Tentativa de alterar fabricante

**Quando dispara:** PATCH em `Equipamento.fabricante` quando existe
certificado EMITIDO.

**Texto canônico (`T3`):**

```
O fabricante não pode ser alterado porque já existe certificado emitido
referenciando este equipamento. O fabricante aparece no documento
técnico assinado e altera a rastreabilidade metrológica (NIT-DICLA-030).
Correção de fabricante após emissão de certificado é tratada como não
conformidade (NC) — registre no fluxo do laboratório; o certificado
existente seguirá referenciando o fabricante ANTERIOR.
```

---

## T4 — Fallback genérico (campo crítico não listado em T1-T3)

**Quando dispara:** PATCH em qualquer campo marcado como crítico pós-cert
que não seja `tag`, `numero_serie`, `fabricante` — defesa em
profundidade. Em Marco 2 a lista crítica é fechada; T4 fica pra futuros
campos que possam ser promovidos a críticos sem retroescrever T1-T3.

**Texto canônico (`T4`):**

```
Este campo do equipamento não pode ser alterado porque já existe
certificado emitido referenciando-o. ISO/IEC 17025 cl. 8.4 exige
imutabilidade do registro técnico pós-emissão. Crie uma nova versão do
equipamento (mudança controlada documentada) ou registre o caso como
não conformidade no fluxo do laboratório.
```

---

## T5 — Tentativa de DELETE de versão imutável

**Quando dispara:** DELETE em `EquipamentoVersao` (Insert-only —
INV-EQP-VERSAO-001).

**Texto canônico (`T5`):**

```
Versões de equipamento não podem ser excluídas. Cada versão registrada
em `EquipamentoVersao` representa uma mudança controlada e auditável
exigida por ISO/IEC 17025 cl. 8.4 (registros técnicos retidos). Se a
versão foi criada por engano, registre uma nova versão de
correção citando a versão errada — o histórico continua íntegro.
```

---

## Como o sistema usa estes textos

O helper Python `texto_rejeicao_422_pos_cert(campo: str)` em
`src/infrastructure/equipamentos/validators.py` retorna a string
canônica para um campo afetado. O viewset DRF chama o helper em camada
de erro 422 — não compõe texto inline, não usa LLM, não traduz.

Pa cravar a regra a nível de banco (`INV-025`), Marco 2 não tem
trigger PG ainda porque o módulo `certificados` não existe (Wave A).
O gate `GATE-EQP-INV025-TRIGGER` rastreia essa pendência em
`docs/faseamento/M2-equipamentos/tasks.md` §"GATEs Wave A".

Até lá, a defesa é:
1. Hook `equipamento-imutabilidade-check.sh` (T-EQP-071) bloqueia code
   que aceite PATCH em campos críticos sem checar certificado emitido.
2. Service Wave A `services_equipamento.atualizar` consulta porta
   stub `CertificadoQueryService.tem_emitido(equipamento_id)` e
   levanta `ImutabilidadePosCertificado(texto=T1..T5)`.
3. Quando módulo `certificados` chegar, trigger PG BEFORE UPDATE em
   `equipamentos` consulta a tabela de certificados e raiz exception
   com o texto canônico identificado pela chave T1..T5.
