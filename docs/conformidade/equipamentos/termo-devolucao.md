---
owner: claude-code
revisado-em: 2026-05-23
status: stable
escopo: módulo equipamentos — texto canônico do termo de devolução (US-EQP-006 AC-EQP-006-4 / ISO 17025 cl. 7.4.5)
relacionados:
  - docs/faseamento/M2-equipamentos/spec.md (US-EQP-006)
  - docs/conformidade/equipamentos/aviso-foto-recebimento.md (foto devolução)
versao_canonica: v1.0-2026-05-23
fundamento_legal: CPC art. 411 III (documento particular presencial) + CC art. 624 (depósito) + ISO/IEC 17025 cl. 7.4.5 + LGPD art. 7º V (legítimo interesse)
---

# Termo de devolução de equipamento — texto canônico v1.0

> **Pra quê:** quando o laboratório DEVOLVE o equipamento ao cliente
> após calibração/manutenção, o cliente DECLARA aceite do estado
> físico no momento da retirada. Documento serve de prova:
>
> 1. **Para o laboratório:** demonstrar que o equipamento foi
>    entregue íntegro/no estado documentado, blindando contra
>    pretensão posterior de dano supostamente causado durante a
>    calibração.
> 2. **Para o cliente:** registrar formalmente o recebimento +
>    eventual ressalva sobre estado físico, fixando o início da
>    responsabilidade trans-laboratório (CC art. 624 — fim do
>    depósito).
>
> Marco 2 dogfooding: aceite **presencial** (CPC art. 411 III —
> documento particular firmado pelas partes). Wave B+: aceite
> eletrônico forte via portal cliente OTP (Lei 14.063/2020 art. 4º
> + GATE-EQP-3).
>
> Mudar texto exige PR + bump `versao_canonica` no frontmatter +
> revisão `advogado-saas-regulado`.

---

## Termo canônico (4 cláusulas obrigatórias)

### Cláusula 1 — ISO/IEC 17025 cl. 7.4.5: encerramento do manuseio

```
O cliente DECLARA expressamente, sob as cominações dos arts. 299
(falsidade ideológica) e 171 (estelionato) do Código Penal e do art.
482 alínea "a" da CLT (justa causa por ato de improbidade), que está
recebendo o equipamento identificado pela TAG operacional registrada
neste termo, e que VERIFICOU presencialmente seu estado físico no
momento da retirada. A condição visual atual está registrada
expressamente neste termo (campo `condicao_visual_devolucao`) e
encerra, neste ato, o período de manuseio sob responsabilidade do
LABORATÓRIO conforme ISO/IEC 17025 cl. 7.4.5.
```

### Cláusula 2 — CC art. 624: fim do depósito

```
A devolução ora formalizada encerra, nos termos do art. 624 do
Código Civil, o regime de DEPÓSITO do equipamento sob a guarda do
LABORATÓRIO. A partir deste ato, a integridade física e operacional
do equipamento passa à responsabilidade integral do CLIENTE, salvo
defeito oculto cuja origem seja inequivocamente atribuível à
atuação do LABORATÓRIO durante o período de manuseio, hipótese em
que o CLIENTE deverá comunicar o LABORATÓRIO no prazo máximo de 30
(trinta) dias corridos contados da presente devolução, sob pena de
preclusão.
```

### Cláusula 3 — Validade técnica do certificado preservada

```
Eventual certificado de calibração emitido durante o período de
manuseio do equipamento permanece TECNICAMENTE VÁLIDO conforme
ISO/IEC 17025 §7.1.1 — o certificado atesta o estado metrológico do
equipamento no momento da calibração, independente da titularidade
ou posse subsequente. Esta cláusula NÃO ABRANGE eventual cessão de
direitos sobre dados pessoais associados ao equipamento, regulada
em termo de transferência separado (US-EQP-004).
```

### Cláusula 4 — Foto + EXIF strip + retenção 25 anos

```
O CLIENTE tem ciência de que o LABORATÓRIO registrou FOTOGRAFIA do
estado físico do equipamento neste ato de devolução, em
cumprimento à ISO/IEC 17025 cl. 7.4.5 (rastreabilidade do manuseio)
e à LGPD art. 7º V (legítimo interesse para defesa em processo
judicial, administrativo ou arbitral). A fotografia tem finalidade
EXCLUSIVA de prova do estado físico no momento da entrega. NÃO
contém face do cliente, dados pessoais legíveis, documentos ou
terceiros — apenas o equipamento.

Metadados técnicos (geolocalização, modelo de câmera, timestamp
EXIF) são removidos automaticamente pelo sistema antes do
armazenamento. Apenas o hash criptográfico SHA-256 do conteúdo
final é gravado na cadeia de auditoria imutável.

Política de retenção: 25 anos (RBC NIT-DICLA-021 + LGPD art. 16).

Para exercer direitos do titular (LGPD art. 18), entre em contato
com o Encarregado de Dados (DPO) pelos canais oficiais.
```

---

## Versionamento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| v1.0-2026-05-23 | 2026-05-23 | advogado-saas-regulado | Criação inicial. 4 cláusulas presenciais (CPC art. 411 III + CC art. 624 + ISO 17025 cl. 7.4.5 + LGPD art. 7º V). |

Bump exige PR + revisão `advogado-saas-regulado` + alteração da
constante `TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA` em `validators.py`
(anti-drift via teste `tests/test_equipamentos_devolver_t_eqp_051.py`).
