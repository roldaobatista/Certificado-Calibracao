---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2027-05-23
status: stable
versao_termo: v1.0-2026-05-23
hash_canonicalizado_referencia: docs/adr/0029-canonicalizacao-texto-probatorio.md
relacionados:
  - docs/dominios/operacao/modulos/os/modelo-de-dominio.md
  - REGRAS-INEGOCIAVEIS.md (RAT-08, Lei 14.063/2020 art. 4º)
  - docs/adr/0029-canonicalizacao-texto-probatorio.md
ratificacao-oab: pendente (advogado-saas-regulado humano antes do 1º tenant externo)
---

# Termo de Aceite de Atividade — v1.0

> **Origem:** NOVO-CRIT-2 da auditoria rodada 2 (2026-05-23). `AceiteAtividade.hash_texto_termo` precisa apontar pra texto canônico versionado; sem texto, hash vira hash de nada → prova Lei 14.063/2020 art. 4º cai.
>
> **Canonicalização:** este arquivo é gravado em UTF-8 sem BOM, line-endings LF, Unicode NFC, sem trailing whitespace por linha (ADR-0029). O hash SHA-256 é calculado sobre os bytes **APENAS DO CORPO** (entre os marcadores `<<<CORPO INICIO>>>` e `<<<CORPO FIM>>>`).

---

<<<CORPO INICIO>>>

# Termo de Aceite de Atividade de Ordem de Serviço

**Versão:** v1.0-2026-05-23

## 1. Identificação

Por este termo, eu, identificado(a) pelo CPF/CNPJ informado no cadastro de cliente do laboratório [NOME_DO_TENANT], reconheço expressamente o seguinte:

## 2. Atividade executada

A atividade técnica número [ATIVIDADE_ID] da Ordem de Serviço [OS_ID], do tipo [TIPO_ATIVIDADE] (calibração, manutenção corretiva, manutenção preventiva, instalação, verificação INMETRO ou vistoria, conforme cadastrado), foi executada no instrumento [EQUIPAMENTO_IDENTIFICACAO_RESUMIDA] em [DATA_EXECUCAO_ATIVIDADE].

## 3. Manifestação de aceite

Declaro que:

- a) recebi o instrumento no estado descrito no checklist da atividade, sem reservas adicionais;
- b) tomei ciência do resultado técnico da atividade conforme registrado no sistema do laboratório [NOME_DO_TENANT];
- c) este aceite NÃO substitui o certificado oficial de calibração (quando aplicável), que é documento técnico-legal regido pela ISO/IEC 17025;
- d) este aceite NÃO transfere a titularidade do dado pessoal vinculado ao registro (LGPD art. 5º, VI/VII).

## 4. Base legal e validade

Este termo é assinatura eletrônica simples conforme **Lei 14.063/2020 art. 4º**, vinculada ao signatário por:

- IP de origem (registrado em forma de hash HMAC-SHA256 do `tenant_id` no momento da assinatura — INV-OS-AUD-001);
- Carimbo de tempo em fuso UTC;
- Hash SHA-256 deste texto canônico v1.0-2026-05-23;
- Quando aplicável, certificado A1 ou A3 ICP-Brasil (forma avançada/qualificada — Lei 14.063 art. 4º §1º).

## 5. Retenção

Este aceite é preservado em audit imutável (WORM) pelo prazo mínimo da atividade vinculada (5 a 25 anos — ver `docs/conformidade/comum/retencao-matriz.md`).

## 6. Direito de revisão humana

Cliente PF tem direito a revisar a decisão técnica por outra parte humana qualificada do laboratório [NOME_DO_TENANT] (LGPD art. 20), exercido por solicitação ao canal de privacidade do laboratório.

## 7. Foro

Eventuais controvérsias serão dirimidas no foro do domicílio do consumidor (CDC art. 101 I quando aplicável) ou no foro da sede do laboratório [NOME_DO_TENANT] nas demais relações.

<<<CORPO FIM>>>

---

## Notas operacionais (NÃO entram no hash)

- Placeholders `[NOME_DO_TENANT]`, `[ATIVIDADE_ID]`, `[OS_ID]`, `[TIPO_ATIVIDADE]`, `[EQUIPAMENTO_IDENTIFICACAO_RESUMIDA]`, `[DATA_EXECUCAO_ATIVIDADE]` são substituídos em runtime ANTES de exibição ao cliente. **O hash é do texto-template com placeholders** (não do texto interpolado) — pra que o mesmo template versionado tenha sempre o mesmo hash, independente do cliente/atividade.
- Versão `v1.0-2026-05-23` é imutável após emissão do primeiro aceite que a referencie. Mudanças no texto exigem nova versão (`v1.1`, `v2.0` etc.) — versões antigas continuam válidas para aceites já gravados.
- Variantes especiais (ex: dispensa de foto — TEMA-D.9) usam slug próprio: `aceite-atividade-dispensa-foto-v1.0.md`.
- Aprovação humana pendente: advogado-saas-regulado humano OAB pré-1º tenant externo.

## Como aplicar

1. Sistema lê arquivo em `docs/conformidade/comum/termos/aceite-atividade-vN.md`.
2. Extrai corpo entre marcadores `<<<CORPO INICIO>>>` e `<<<CORPO FIM>>>`.
3. Aplica canonicalização ADR-0029: UTF-8 sem BOM, LF, NFC, sem trailing whitespace.
4. Calcula SHA-256 dos bytes resultantes.
5. Grava em `AceiteAtividade.hash_texto_termo` (32 bytes).
6. Versão vai em `AceiteAtividade.versao_termo` (string `v1.0-2026-05-23`).
