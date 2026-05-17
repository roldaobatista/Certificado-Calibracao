---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# PRD — Módulo Equipamentos do cliente

## 1. O que este módulo é

Cadastro completo do equipamento físico do cliente final (balança, paquímetro, termômetro etc.) que o tenant calibra. Cada equipamento tem TAG única, QR Code impresso, vínculo a um cliente e histórico imutável de eventos após primeira emissão de certificado. Persona principal: metrologista de bancada (P-OP-02) e técnico de campo (P-OP-01). **Wave A** — destrava OP2 (rastreio de calibração) e OP3 (notificação de vencimento).

## 2. Por que existe (problema a resolver)

- BIG-01 (não perder info do equipamento entre OS sucessivas)
- OP17 (ficha 360° + QR Code escaneável) — *NOVA*
- Dor: cliente liga e técnico não acha histórico do instrumento.

## 3. Personas

Ver `personas.md` + `../../personas.md` (P-OP-01, P-OP-02, P-SUP-01).

## 4. Escopo (o que ESTÁ)

- CRUD de equipamento (tag, NS, fabricante, modelo, faixa, classe, vínculo a cliente)
- Geração e impressão de QR Code com link para ficha
- Ficha 360°: dados + histórico de calibração + OS abertas + próxima calibração
- Versionamento de atributos descritivos pós-emissão de certificado (INV-025)
- Transferência de equipamento entre clientes (com registro do motivo)
- Status: ativo / inativo / sucata / em calibração

## 5. Non-goals

- NÃO emite certificado (fica em Metrologia)
- NÃO calcula incerteza
- NÃO controla estoque do tenant (o equipamento é do cliente final, não do tenant)
- NÃO faz cobrança (vai pra Financeiro)

## 6. User Stories

### US-EQP-001: Cadastrar equipamento com QR Code

**Como** metrologista, **quero** cadastrar um equipamento e imprimir QR Code, **para** identificar fisicamente o ativo.

- **AC-EQP-001-1**: GIVEN tenho cliente cadastrado, WHEN preencho tag + NS + fabricante + modelo + faixa + classe, THEN equipamento é salvo e QR Code é gerado.
- **AC-EQP-001-2**: GIVEN equipamento salvo, WHEN clico "imprimir etiqueta", THEN PDF da etiqueta sai com QR + TAG + NS.

**Invariantes:** `INV-025`

### US-EQP-002: Editar equipamento com versionamento pós-emissão

**Como** metrologista, **quero** editar atributo descritivo de equipamento já com certificado emitido, **para** corrigir info sem violar imutabilidade do certificado.

- **AC-EQP-002-1**: GIVEN equipamento com ≥1 certificado emitido, WHEN edito atributo (ex: modelo), THEN sistema cria nova versão e o certificado antigo continua referenciando a versão original.
- **AC-EQP-002-2**: GIVEN tento alterar TAG ou NS de equipamento com certificado, THEN sistema bloqueia (campos imutáveis).

**Invariantes:** `INV-025`

### US-EQP-003: Escanear QR Code e abrir ficha 360°

**Como** técnico de campo, **quero** escanear QR Code, **para** ver histórico + próxima calibração no celular.

- **AC-EQP-003-1**: GIVEN QR válido, WHEN escaneio, THEN ficha 360° abre em ≤ 2s.

## 7. Métricas (ver `metricas.md`)

- Tempo médio para localizar equipamento ≤ 30s
- % equipamentos com QR impresso ≥ 90%

## 8. NFR

- Performance: ficha 360° p95 ≤ 1.5s
- Segurança: leitura do QR exige sessão autenticada do tenant
- Acessibilidade: WCAG AA

## 9. Glossário

Ver `glossario.md`.
