---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
---

# Glossário — Módulo Clientes

> Termos específicos do módulo Clientes. Termos transversais (tenant, OS, certificado, RBC) ficam em `docs/comum/glossario-roldao.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log significa | Origem |
|---|---|---|---|---|
| Cliente PF | Pessoa física (CPF) atendida pelo tenant | "consumidor", "particular" | Cadastro com CPF + RG + dados de contato | LGPD art. 5 |
| Cliente PJ | Pessoa jurídica (CNPJ), com possíveis múltiplas unidades/filiais | "empresa cliente" | Cadastro com CNPJ + razão social + IE | Receita Federal |
| Cliente master | Entidade única que consolida cadastros duplicados em uma só visão 360° | "cadastro mestre", "registro principal" | Após dedup, é o cadastro vencedor pra onde tudo aponta | F-C (Foundation) |
| Visão 360° | Tela única com timeline cronológica de tudo que aconteceu com o cliente (OS, certificados, financeiro, contatos, NPS) | "ficha do cliente", "histórico" | Tela `/clientes/{id}` no menu Comercial | BIG-07 + JTBD-083 |
| Limite de crédito | Valor máximo de crédito comercial concedido antes de bloquear nova OS sem pré-pagamento | "limite", "alçada" | Bloqueio aparece em criação de OS/orçamento se ultrapassado | OP11 (cobrança) |
| Rating de cliente | Classificação A/B/C/D atribuída automaticamente por comportamento (pontualidade, ticket, recompra, NPS) | "score", "categoria" | Selo colorido na lista de clientes | INFERÊNCIA — confirmar com Roldão |
| Segmento | Agrupamento marketing/comercial configurável (ex: "RBC ativo", "perfil D", "indústria farma") | "tag", "categoria" | Filtro no CRM e em campanhas | OP5 + BIG-10 |
| Bloqueio comercial | Estado que impede nova OS/orçamento por inadimplência, fraude ou pedido do cliente | "suspensão", "banimento" | Selo vermelho + impedimento de operação | OP11 |
| Dedup (deduplicação) | Processo de identificar e unificar dois cadastros que representam o mesmo cliente real | "merge", "fusão" | Wizard `/clientes/dedup` ou hook no cadastro | INV-024 |
| Importação 1-clique | Upload de planilha (Cali/Bling/CSV) que cria clientes em lote com mapeamento automático | "import em massa", "carga" | Tela `/clientes/importar` | F-C (Foundation) |
| Unidade/filial | Endereço operacional adicional de um cliente PJ (não é cliente novo — é filho do cliente master) | "subsidiária", "endereço extra" | Aba "Unidades" dentro do cadastro PJ | INFERÊNCIA — confirmar com Roldão |
| Contato | Pessoa física vinculada a um cliente PJ (responsável técnico, financeiro, comercial) | "interlocutor" | Lista de pessoas dentro do PJ | — |

## Convenções

- Termos em PT-BR. Termo "lead" não vive aqui — vive no módulo `crm` (lead ≠ cliente cadastrado).
- "Cliente" sem qualificador = cliente master (entidade consolidada), nunca cadastro bruto.

## Como evolui

Termo novo → adicionar + checar não-duplicação com `docs/comum/glossario-roldao.md`.
