---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: explanation
---

# PRD — Módulo Clientes

## 1. O que este módulo é

Cadastro único de clientes PF/PJ do tenant + visão 360° consolidada (timeline de OS, certificados, financeiro, contatos, NPS) + limite de crédito + segmentação + rating. **É a base de todos os outros módulos comerciais e operacionais** — sem cliente master, OS/orçamento/contrato/cobrança não existem.

## 2. Por que existe

Dor #01 (cadastro duplicado entre sistemas) + dor universal "cadê o cadastro do Sr. Silva?" + BIG-07 (Cliente 360°). Discovery: founder e validações externas confirmam que cadastro duplicado é Top 3 das dores de atendente. Foundation F-C destrava OP1, OP2, OP4, OP7, OP15.

## 3. Personas

Ver `../../personas.md` (P-COM-01 Atendente, P-COM-02 Vendedor, P-COM-05 Dono). Cliente final do tenant (P-COM-03) **não** edita seu próprio cadastro neste módulo — vai pelo portal (módulo separado).

## 4. Escopo MVP-1 (o que ESTÁ neste módulo)

- Cadastro PF (CPF + RG + telefone + e-mail + endereço + LGPD aceite)
- Cadastro PJ (CNPJ + razão + fantasia + IE + IM + endereço + contatos múltiplos + unidades/filiais)
- Validação automática CPF/CNPJ (algoritmo + opcional consulta ReceitaWS — V2)
- Dedup automático na criação (mesmo CPF/CNPJ) + wizard de dedup manual
- Visão 360° (timeline cronológica + abas: OS, Certificados, Financeiro, Contatos, NPS, Anexos)
- Limite de crédito (valor + uso atual + bloqueio quando excedido)
- Segmentação (tags configuráveis pelo tenant)
- Importação 1-clique (Cali/Bling/CSV) — Foundation F-C
- Bloqueio comercial (manual ou automático por inadimplência via régua OP11)

## 5. Non-goals (NÃO entra)

- **Equipamentos do cliente** (vai pra módulo `suporte-plataforma/equipamentos`, OP17)
- **Histórico técnico de calibração** (vai pra `operacao/certificados`)
- **Lead não-convertido** (vai pra módulo `crm/leads` — lead vira cliente só ao converter)
- **Cobrança ativa / boleto** (vai pra `financeiro/contas-receber`)
- **Rating de crédito por bureau externo** (Serasa/SPC) — fora do MVP-1
- **Cadastro próprio pelo cliente final no portal** — V2
- **CRM custom fields** com lógica condicional — Wave B no módulo crm
- **Mailing/campanha de e-mail marketing** — fora do produto

## 6. User Stories principais

### US-CLI-001: Cadastrar cliente PF em menos de 1 minuto
**Como** atendente, **quero** abrir um formulário curto e digitar CPF/nome/telefone/e-mail, **para** começar atendimento sem perder o cliente na linha.
- AC-1: GIVEN tela `/clientes/novo` WHEN preencho CPF válido THEN sistema valida algoritmo + busca duplicata + se duplicar mostra link "este cliente já existe".
- AC-2: GIVEN form preenchido WHEN salvo THEN cliente master criado com `tenant_id`, aceite LGPD registrado (RAT-03), evento `Cliente.Criado` publicado.
- **INV:** INV-024 (dedup), INV-TENANT-001, INV-TENANT-002.

### US-CLI-002: Ver visão 360° do cliente
**Como** atendente/vendedor, **quero** abrir `/clientes/{id}` e ver tudo do cliente em uma tela, **para** atender sem trocar de aba 6 vezes.
- AC-1: Timeline cronológica reversa com eventos de todos os módulos (OS criada/concluída, certificado emitido, NF-e, NPS, contato registrado).
- AC-2: Carregamento p95 < 1.5s pra clientes com até 500 eventos.

### US-CLI-003: Importar planilha de clientes (1-clique)
**Como** dono migrando de Cali/Bling, **quero** subir CSV/XLSX e ver mapeamento automático, **para** não digitar 800 cadastros.
- AC-1: GIVEN arquivo válido WHEN upload THEN preview com 10 primeiras linhas + mapeamento sugerido.
- AC-2: GIVEN confirmação WHEN executa THEN cria clientes em lote, dedup automático, relatório final (criados/atualizados/rejeitados).

### US-CLI-004: Bloquear cliente inadimplente
**Como** financeiro/dono, **quero** marcar cliente como bloqueado, **para** impedir nova OS sem quitar débito.
- AC-1: GIVEN bloqueio ativo WHEN tento criar OS THEN sistema impede + mostra motivo + sugere caminho (quitar/desbloqueio manual com justificativa).

### US-CLI-005: Dedup manual de cadastros duplicados
**Como** atendente, **quero** wizard que mostre 2 cadastros lado a lado e me deixe escolher campo a campo qual valor manter, **para** consolidar sem perder histórico.
- AC-1: Histórico (OS, certificados, financeiro) do cadastro perdedor migra integralmente pro vencedor.
- AC-2: Cadastro perdedor é soft-deleted (auditável), nunca hard-deleted (LGPD).

## 7. Métricas

Ver `metricas.md`. Resumo: taxa de duplicidade < 1%, tempo médio cadastro PF < 60s, % clientes com 360° usado/semana > 40%.

## 8. NFR

- Performance: cadastro p95 < 800ms; visão 360° p95 < 1.5s.
- Disponibilidade: 99.9% (módulo crítico).
- LGPD: RAT-03 obrigatório no cadastro; RAT-06 quando comunicação WhatsApp ativada.
- Multi-tenancy: INV-TENANT-001/002/003/004 absolutos.

## 9. Glossário

Ver `glossario.md`.
