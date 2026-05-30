---
owner: <DPO-ou-OnCall>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 260
proposito: runbook operacional para hard-delete de dados pessoais a pedido do titular (LGPD Art. 18 VI) — validação, exceções legais, execução, backup, registro WORM
---

<!--
template: atender-pedido-eliminacao-runbook.template.md
destino: docs/operacao/runbooks/atender-pedido-eliminacao.md
uso: runbook executado a cada pedido de eliminação (Art. 18 VI). Cobre fluxo padrão E variantes (dado em backup, dado em terceiro, dado sob exceção legal).
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6 + §C8
revisão obrigatória: 6 meses ou após qualquer pedido que tenha exposto lacuna no procedimento.
SLA legal: 15 dias corridos.
-->

# Runbook — Atender Pedido de Eliminação (LGPD Art. 18 VI)

> **Eliminação** = apagar para sempre o dado do titular, em todos os lugares onde ele existe (banco principal, réplicas, cache, backup, planilha, log, terceiros). Não é "desativar conta" nem "marcar deleted=true". É **hard-delete** verdadeiro, mantendo apenas o que a lei obriga a reter (e justificando cada item retido). Sem esse runbook executado corretamente, a empresa pode multar pela ANPD por descumprir o Art. 18.

## 0. Pré-requisitos antes de executar

- [ ] Pedido entrou pelo canal documentado (`direitos-do-titular.md` §1).
- [ ] Identidade do titular foi validada (`direitos-do-titular.md` §3).
- [ ] DPO ou pessoa autorizada está executando (não devops aleatório).
- [ ] Cofre de segredos acessível (você vai precisar de credenciais de banco e API).
- [ ] Janela de execução adequada (preferir horário de baixo tráfego).

## 1. Validação de identidade do solicitante

> Já está coberto pelo `direitos-do-titular.md §3`, mas **confirmar** antes de continuar. Eliminar a pessoa errada é incidente de segurança grave.

| Cenário | O que confirmar |
|---|---|
| Titular logado pediu pelo painel | sessão ativa + 2FA recente (≤24h) |
| Pedido por e-mail | e-mail do remetente bate com o e-mail cadastrado + código de confirmação enviado e respondido |
| Pedido com documento | foto do documento confere com cadastro; selfie com documento; sem indício de fraude |
| Pedido por advogado / representante | procuração específica para LGPD + OAB do advogado verificado |
| Titular falecido (herdeiro pedindo) | certidão de óbito + comprovante de herança / inventário |

**Se não passou:** registrar tentativa, pedir documento adicional, NÃO executar. Comunicar DPO se houver suspeita de fraude.

## 2. Levantamento de escopo (o que vai ser eliminado)

Executar query/script de "mapeamento do titular" — tabela por tabela onde o ID do titular aparece.

```sql
-- exemplo (PostgreSQL) — adaptar ao schema do projeto
SELECT 'users' AS tabela, COUNT(*) FROM users WHERE id = :titular_id
UNION ALL
SELECT 'orders', COUNT(*) FROM orders WHERE user_id = :titular_id
UNION ALL
SELECT 'audit_log', COUNT(*) FROM audit_log WHERE actor_id = :titular_id
-- ... uma linha por tabela que tem FK pro titular
;
```

> **Boa prática:** este script vive em `scripts/lgpd/map-titular.sql` e é mantido atualizado a cada migration que cria tabela com dado de titular. Auditor `auditor-lgpd` verifica que toda tabela nova entra no script.

Resultado é registrado em ticket interno (ID do pedido) para anexar à confirmação final.

## 3. Verificação de exceções legais (Art. 16)

**Crítico:** nem todo dado pode ser eliminado. A LGPD obriga a reter alguns dados mesmo após pedido. Antes de apagar, listar **o que NÃO vai ser apagado** e por qual base legal.

| Exceção | Quando aplica | O que reter | Por quanto tempo |
|---|---|---|---|
| **Art. 16 I — cumprimento de obrigação legal** | nota fiscal, contrato, comprovante de pagamento | dados mínimos da operação | conforme legislação (5 anos para fiscal; 5-10 para contratos; 5 para CDC) |
| **Art. 16 II — estudo por órgão de pesquisa** | dado anonimizado em base de pesquisa | versão anonimizada | indefinido (anonimizado não é mais dado pessoal) |
| **Art. 16 III — transferência a terceiro** | quando dado já foi compartilhado com operador sob contrato vigente | dado no terceiro segue contrato | conforme contrato + obrigação legal do terceiro |
| **Art. 16 IV — uso exclusivo do controlador, anonimizados** | métricas agregadas, modelo de ML treinado | versão anonimizada/agregada | indefinido |
| **Exercício regular de direito em processo judicial/administrativo** | litígio em curso envolvendo o titular | tudo relacionado ao processo | até trânsito em julgado + prazo prescricional |

> **Exemplo preenchido:**
> Pedido de João Silva (id 12345). Levantamento mostrou: 47 registros em `users`, `orders`, `payments`, `addresses`, `support_tickets`, `audit_log`.
> - `payments` (12 registros) — manter pelos **5 anos** após emissão (Art. 16 I + obrigação fiscal). Cifrar com chave nova e segregar em tabela `payments_lgpd_retido`.
> - `audit_log` (3 registros referentes a alterações administrativas pelo próprio João) — manter por **5 anos** (Art. 16 I + LGPD Art. 37 / boas práticas).
> - Demais 32 registros: **hard-delete** agora.
> - `orders` com `status=concluded` há mais de 5 anos: eliminar.
> - `orders` com `status=disputed` em processo: reter até trânsito em julgado.

**Quem aprova essa lista:** DPO. Por escrito (e-mail / ticket assinado).

## 4. Execução do hard-delete

### 4.1 Ordem de execução

1. **Notificar serviços dependentes** que vão receber o evento de eliminação (ex: cache, search index, sistema externo via webhook).
2. **Cifrar com nova chave** os dados que vão para retenção legal (campo `payments_lgpd_retido` no exemplo) — ver `key-management-policy.md`.
3. **Hard-delete** das tabelas — usar transação única para garantir atomicidade.
4. **Invalidar cache** (Redis, CDN, application cache).
5. **Reindexar** mecanismos de busca (Elasticsearch, Algolia) para remover documento.
6. **Notificar operadores externos** (Stripe, SendGrid, etc.) via API de delete deles. Guardar evidência da chamada.
7. **Registrar em log WORM** (ver §6).

### 4.2 Comando SQL exemplo

```sql
BEGIN;

-- registrar pedido antes de eliminar (auditoria)
INSERT INTO lgpd_eliminacao_log (titular_id, pedido_id, executado_em, escopo_json, executor)
VALUES (:titular_id, :pedido_id, NOW(), :escopo_json, :executor);

-- cifrar e mover o que tem que ser retido (exemplo: payments para retenção fiscal)
INSERT INTO payments_lgpd_retido (id, dados_cifrados, retido_ate)
SELECT id, pgp_sym_encrypt(row_to_json(payments)::text, :chave_retencao), '<data-limite>'::date
FROM payments WHERE user_id = :titular_id;

-- hard-delete tabelas filhas primeiro (FK)
DELETE FROM support_tickets WHERE user_id = :titular_id;
DELETE FROM addresses WHERE user_id = :titular_id;
DELETE FROM orders WHERE user_id = :titular_id AND status NOT IN ('disputed');
DELETE FROM payments WHERE user_id = :titular_id; -- já replicados acima cifrados
-- ... outras tabelas filhas

-- por fim, a tabela raiz
DELETE FROM users WHERE id = :titular_id;

COMMIT;
```

> **Atenção:** não usar `TRUNCATE`. Não usar `DROP`. Não desativar a constraint de FK. Se a transação falhar, **rollback**, investigar, e tentar de novo. Nunca executar parcial.

### 4.3 Chamada a APIs de operadores

Para cada operador listado no ROPA que recebeu dado do titular:

```bash
# exemplo Stripe
curl -X DELETE "https://api.stripe.com/v1/customers/$STRIPE_CUSTOMER_ID" \
  -u "$STRIPE_SECRET_KEY:"

# exemplo SendGrid (suppression list)
curl -X DELETE "https://api.sendgrid.com/v3/asm/suppressions/global/$EMAIL" \
  -H "Authorization: Bearer $SENDGRID_API_KEY"
```

Guardar resposta HTTP + timestamp em `lgpd_eliminacao_log.evidencia_operadores`.

## 5. Backup — duas estratégias aceitas

LGPD não obriga apagar dado de backup imediatamente (é fisicamente impraticável), mas exige que o dado **não retorne à produção** quando o backup for restaurado.

Escolher uma das estratégias (documentar qual no projeto, em `backup.md`):

### 5.1 Estratégia A — Expurgo no próximo ciclo de retenção
- Manter lista de IDs eliminados em tabela `lgpd_ids_eliminados`.
- Procedimento de restore do backup roda script de purge: para cada ID na lista, eliminar do banco restaurado **antes** de promover.
- Quando backup envelhece e é descartado pelo TTL normal (ex: 90 dias), o dado deixa de existir lá também.

### 5.2 Estratégia B — Backup criptografado com chave revogável
- Backup cifrado com chave gerenciada (KMS).
- Quando titular pede eliminação, a chave do backup **não muda** (impraticável re-cifrar terabytes), mas se necessário tornar o backup totalmente inacessível (caso de comprometimento da chave), descartar a chave torna o backup inútil — **crypto-shredding** (apagamento criptográfico).
- Para titular específico: lista de IDs eliminados rege restore (igual à estratégia A).

**Documentar no log WORM qual estratégia foi aplicada e quando o backup ficará livre do dado.**

## 6. Registro em log WORM (write-once-read-many)

Toda eliminação gera linha imutável em log de auditoria que **não pode ser editado nem apagado**. Esse log é a prova legal de que cumprimos a LGPD.

Campos obrigatórios:

| Campo | Exemplo |
|---|---|
| `id_pedido` | UUID do pedido original |
| `titular_id` (hash, não em claro depois da eliminação) | `sha256(<id-original>)` |
| `executado_em` | timestamp ISO 8601 |
| `executor` | identidade do operador (não anônimo) |
| `escopo_eliminado` | lista de tabelas + contagem de registros |
| `escopo_retido_com_base_legal` | tabelas + base legal (Art. 16 I/II/III/IV) + data limite de retenção |
| `operadores_notificados` | lista de operadores + status HTTP + timestamp |
| `estrategia_backup` | A ou B + descrição |
| `confirmacao_titular` | timestamp + canal de envio |
| `hash_encadeado` | hash do registro anterior + deste — garante integridade da cadeia |

Local físico: bucket WORM (S3 Object Lock no modo Compliance, GCS Bucket Lock, ou cofre dedicado). Retenção mínima: **10 anos** (sustentação em fiscalização).

## 7. Confirmação ao titular

Após execução, enviar e-mail (ou canal do pedido original):

```
Assunto: Confirmação — seu pedido de eliminação de dados (LGPD Art. 18 VI)

Olá <nome>,

Concluímos seu pedido de eliminação de dados pessoais em <data>.

O que foi eliminado:
- <descrição em linguagem clara — ex: "seu cadastro, endereços, histórico de pedidos
  com mais de 5 anos e todas as suas mensagens de suporte">.

O que permanece (e por quê):
- <ex: "dados de pagamento dos últimos 5 anos, mantidos por exigência fiscal — Art. 16 I LGPD.
  Esses dados estão cifrados e isolados; serão eliminados automaticamente em <data>">.

Confirmação técnica: protocolo <id-do-log-worm>.
Próximas etapas: nada — você não precisa fazer mais nada.

Encarregado (DPO): <nome>, <e-mail>.
Você sempre pode procurar a ANPD: https://www.gov.br/anpd

Atenciosamente,
<Razão social>
```

## 8. Se algo der errado

| Sintoma | Ação imediata |
|---|---|
| Transação SQL falhou no meio | rollback automático já ocorreu; investigar erro; tentar de novo após corrigir |
| API de operador retornou erro | tentar 3x com backoff; se persistir, abrir ticket no operador e registrar tentativa no log; informar DPO |
| Identificado dado em sistema fora do mapeamento | **PARAR**; atualizar `scripts/lgpd/map-titular.sql`; abrir débito de auditoria; reexecutar |
| Eliminou pessoa errada | incidente CRÍTICO; acionar `docs/operacao/runbooks/incidente-seguranca.md`; comunicar DPO em ≤1h |
| Titular reclama que ainda recebe e-mail / vê dado | verificar cache, CDN, operador não notificado; corrigir; pedir desculpas |

## 9. SLA

- **Confirmação inicial ao titular:** 48h úteis (acuse de recebimento).
- **Execução completa + confirmação final:** **15 dias corridos** (Art. 19 LGPD aplicado por analogia).
- **Em caso de complexidade (operador externo lento, processo judicial em curso):** informar titular dentro do prazo original com nova previsão.

## 10. Vinculação

- `direitos-do-titular.md` — fluxo geral que aciona este runbook (inciso VI).
- `ropa.md` — lista de operadores que precisam ser notificados.
- `retencao-dados.md` — prazos legais que justificam exceções.
- `backup.md` — estratégia adotada (A ou B) e procedimento de restore.
- `key-management-policy.md` — chaves usadas para cifrar dado retido.
- `docs/operacao/runbooks/incidente-seguranca.md` — fluxo se algo der errado.
- INV-AGENT-AUDIT-* — invariantes do log WORM.

## 11. Checklist de promoção draft → stable

- [ ] Script `scripts/lgpd/map-titular.sql` cobre todas as tabelas atuais com dado de titular.
- [ ] Estratégia de backup §5 escolhida e implementada (não só documentada).
- [ ] Log WORM §6 existe fisicamente (bucket / cofre) e foi testado.
- [ ] Pelo menos um drill (eliminação de conta de teste) foi executado dentro do SLA.
- [ ] Notificação a operadores §4.3 funciona (chamadas testadas em sandbox do operador).
- [ ] Modelo de e-mail §7 aprovado pelo jurídico.
- [ ] `revisado-em` atualizado; `status: stable`.
