---
owner: claude-code
revisado-em: 2026-05-23
status: stable
escopo: módulo equipamentos — avisos UX + cláusula contratual sobre foto de recebimento (US-EQP-006 AC-EQP-006-5 / P-EQP-A6 + P-EQP-A8 + P-EQP-S4)
relacionados:
  - docs/faseamento/M2-equipamentos/spec.md (US-EQP-006)
  - docs/faseamento/M2-equipamentos/plan.md (P-EQP-A6 + P-EQP-A8 + P-EQP-S4)
versao_canonica: v1.0-2026-05-23
fundamento_legal: LGPD art. 7º V (legítimo interesse) + ISO/IEC 17025 cl. 7.4 (rastreabilidade) + CLT art. 482 alínea "a" (improbidade) + CP art. 299 (falsidade ideológica) + CDC art. 6º III (informação clara)
---

# Aviso UX + cláusula contratual sobre foto de recebimento v1.0

> **Pra quê:** o laboratório FOTOGRAFA o equipamento no momento do
> recebimento — defesa em profundidade contra responsabilização por
> dano pré-existente (corretora RAT-EQP-FOTO + ISO/IEC 17025 cl. 7.4).
> Foto contém somente o equipamento físico — **NÃO contém face do
> cliente, dados pessoais legíveis (etiquetas com CPF/RG/nome),
> documentos ou terceiros**. Este doc define:
>
> 1. **Aviso UX** exibido ao OPERADOR antes do upload (P-EQP-A6).
> 2. **Aviso ao cliente** impresso no PDF de comprovante de entrada
>    (P-EQP-A8 — LGPD art. 7º V).
> 3. **Cláusula contratual** que dá ao laboratório direito de recusar
>    recebimento sem RC se cliente recusa fotografia (P-EQP-S4).
>
> Mudar texto exige PR + bump `versao_canonica` no frontmatter +
> revisão `advogado-saas-regulado`.

---

## 1) Aviso UX ao OPERADOR (exibido ANTES do upload da foto)

```
ANTES DE TIRAR A FOTO:

[ ] Sem face/imagem do cliente final ou de terceiros (LGPD art. 5º II).

[ ] Sem etiqueta/documento com CPF/RG/nome/e-mail/telefone visível
    (LGPD art. 5º I — dados de identificação não podem aparecer
    fotografados; reposicione o equipamento ou cubra a etiqueta).

[ ] Sem ambiente que identifique terceiros (outros equipamentos com
    TAGs visíveis pertencentes a outros clientes).

[ ] A foto será PRESERVADA por 25 anos (RBC NIT-DICLA-021 + LGPD art.
    16 retenção de evidência forense). Metadados de geolocalização e
    modelo de câmera são REMOVIDOS automaticamente pelo sistema (TL2).

[ ] Declaração: ao confirmar o upload, atesto sob as cominações dos
    arts. 299 (falsidade ideológica) e 171 (estelionato) do Código
    Penal e do art. 482 alínea "a" da CLT (justa causa por ato de
    improbidade) que a foto reflete o estado físico real do
    equipamento no momento do recebimento.

[Cancelar]              [Confirmar upload]
```

**Constantes:** `AVISO_UX_FOTO_RECEBIMENTO_VERSAO_CANONICA`,
`AVISO_UX_FOTO_RECEBIMENTO` em `validators.py`.

---

## 2) Aviso ao CLIENTE no PDF de comprovante (P-EQP-A8)

> **Marco 2 status:** texto canônico cravado; comprovante PDF fica
> em Wave A (gerador depende de `comunicacao-omnichannel`).

```
AVISO AO CLIENTE — FOTOGRAFIA DE RECEBIMENTO

Conforme ISO/IEC 17025 cl. 7.4 (manuseio de itens de ensaio) e LGPD
art. 7º V (legítimo interesse do controlador para defesa de
direitos em processo judicial, administrativo ou arbitral), o
laboratório registrou fotografia do estado físico deste
equipamento no momento do recebimento.

A fotografia tem finalidade EXCLUSIVA de:

(a) Comprovar o estado físico no momento da entrega (defesa contra
    responsabilização por dano pré-existente — corretora RAT-EQP-FOTO).

(b) Atender requisito ISO/IEC 17025 cl. 7.4 (rastreabilidade de
    manuseio).

(c) Constar como evidência em eventual processo judicial,
    administrativo ou arbitral (LGPD art. 7º V).

Política de retenção: 25 anos (RBC NIT-DICLA-021 + LGPD art. 16).

A foto NÃO contém face do cliente, dados pessoais legíveis,
documentos ou terceiros — apenas o equipamento físico.

Metadados técnicos (geolocalização, modelo de câmera, timestamp
EXIF) são removidos automaticamente pelo sistema antes do
armazenamento. Apenas o hash criptográfico SHA-256 do conteúdo
final é gravado na cadeia de auditoria imutável (defesa contra
adulteração).

Para exercer seus direitos do titular (LGPD art. 18), entre em
contato com o Encarregado de Dados (DPO) pelos canais oficiais.
```

**Constantes:** `AVISO_PDF_FOTO_RECEBIMENTO_VERSAO_CANONICA`,
`AVISO_PDF_FOTO_RECEBIMENTO` em `validators.py` (Wave A — Marco 2
expõe apenas a constante de versão).

---

## 3) Cláusula contratual — direito de recusa por recusa de foto (P-EQP-S4)

> **Para incluir** no contrato-modelo tenant↔cliente (Wave A —
> `comunicacao-contratual`).

```
CLÁUSULA — DOCUMENTAÇÃO FOTOGRÁFICA DE RECEBIMENTO

Para fins de cumprimento da ISO/IEC 17025 cl. 7.4 e de proteção
contra responsabilização por dano pré-existente, o LABORATÓRIO
registra, no momento da entrada do equipamento, fotografia do seu
estado físico — exclusivamente do equipamento, sem face do cliente,
sem dados pessoais legíveis e sem terceiros.

Caso o CLIENTE recuse, no momento do recebimento, a documentação
fotográfica do equipamento, o LABORATÓRIO terá o direito de:

(a) Recusar o recebimento do equipamento, sem qualquer ônus, multa
    ou indenização ao CLIENTE; ou

(b) Aceitar o recebimento mediante termo de RESPONSABILIDADE
    INTEGRAL do CLIENTE pelo estado físico do equipamento na
    entrega, isentando o LABORATÓRIO de qualquer pretensão futura
    de indenização por dano pré-existente, com renúncia expressa do
    CLIENTE ao direito de demandar judicialmente sobre o tema.

A escolha entre (a) e (b) cabe exclusivamente ao LABORATÓRIO, em
decisão a ser registrada no fluxo de não-conformidade interno (ISO
17025 cl. 8.7) e comunicada ao CLIENTE por escrito no mesmo ato.

Fundamento legal: ISO/IEC 17025 cl. 7.4; LGPD art. 7º V (legítimo
interesse); Código Civil arts. 421 (função social do contrato) e
462 (responsabilidade objetiva por dano pré-existente). Esta
cláusula NÃO afasta direitos básicos do CLIENTE previstos no CDC
(arts. 6º, 39 e 51), aplicando-se apenas à hipótese específica de
recusa expressa de documentação fotográfica do equipamento.
```

**Constantes:** `CLAUSULA_RECUSA_FOTO_VERSAO_CANONICA`,
`CLAUSULA_RECUSA_FOTO` em `validators.py` (Wave A).

---

## 4) Allowlist semântica — o que a foto NÃO pode conter

Operador NÃO PODE enviar foto que contenha:

- Face de cliente, técnico ou qualquer terceiro identificável.
- Etiqueta com CPF, CNPJ, RG, nome próprio completo, e-mail,
  telefone, endereço.
- Documento (RG, CNH, comprovante de residência, NF do cliente).
- Tela de computador com sistema interno (CRM, ERP, planilha) com
  dados de cliente ou terceiros.
- Outros equipamentos com TAGs visíveis pertencentes a outros
  clientes.

Defesa em camadas:
- **Camada A (UX):** aviso pré-upload (§1).
- **Camada B (técnica — Marco 2):** EXIF strip automático (geo,
  câmera, timestamp). OCR anti-CPF/CNPJ fica em Wave B+.
- **Camada C (contratual):** cláusula §3.
- **Camada D (processo):** revisão amostral periódica pelo RT do
  laboratório (NIT-DICLA-021 supervisão técnica).

---

## 5) Versionamento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| v1.0-2026-05-23 | 2026-05-23 | advogado-saas-regulado | Criação inicial. Aviso UX + aviso PDF + cláusula contratual + allowlist. |

Bump exige PR + revisão `advogado-saas-regulado` + alteração da
constante `AVISO_UX_FOTO_RECEBIMENTO_VERSAO_CANONICA` em
`validators.py` (anti-drift via teste).
