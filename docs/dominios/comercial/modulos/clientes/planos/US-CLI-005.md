---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-005
---

# Plano US-CLI-005 — Dedup manual de cadastros duplicados

> Story em `docs/dominios/comercial/modulos/clientes/prd.md` §6.
>
> Texto da Story (resumo): wizard mostra 2 cadastros lado a lado; usuário escolhe campo a campo qual valor manter; histórico do perdedor migra integral pro vencedor; perdedor vira soft-delete auditável.

## ACs

- **AC-CLI-005-1**: histórico (OS, certificados, financeiro) do cadastro perdedor migra integralmente pro vencedor.
- **AC-CLI-005-2**: cadastro perdedor é soft-deleted (auditável), nunca hard-deleted (LGPD art. 16 + ISO 17025 8.4).

## Resumo

API backend (sem UI nesta fase). Endpoint POST `/api/v1/clientes/{vencedor_id}/mesclar/{perdedor_id}/` recebe um JSON com sobreposições campo-a-campo (qual valor manter por campo), aplica no vencedor + soft-deleta o perdedor + grava audit `cliente.mesclado`.

## Limites desta fase

- **Migração de histórico (AC-1)** é parcial: módulos consumidores (OS, certificados, financeiro) **não existem ainda**. Implementação atual prepara o contrato de evento `Cliente.Mesclado(vencedor_id, perdedor_id, campos_sobrescritos)` que módulos futuros consumirão. Pra MVP-1 dogfooding (sem dados em outros módulos), o AC-1 é atendido por publicação do evento + audit; quando OS/cert/financeiro existirem, eles assinam o evento e migram suas FKs.
- **Soft-delete**: campo `deletado_em: DateTimeField nullable` no Cliente. Querysets default filtram `deletado_em IS NULL`.

## Sequência de tasks

- **T-CLI-009**: migration adicionando `deletado_em` + `deletado_por_usuario_id` + `deletado_motivo` ao Cliente. Index parcial em `deletado_em IS NULL` pra performance.
- **T-CLI-010**: `Cliente.objects` filtra `deletado_em IS NULL` por default; `Cliente.all_objects` manager separado pra acesso a deletados (auditoria).
- **T-CLI-011**: endpoint `POST /api/v1/clientes/{vencedor_id}/mesclar/{perdedor_id}/` com payload `{"sobrescrever": {"nome": "valor_a_manter", "email": "...", ...}, "motivo": "..."}`. Authz: `clientes.mesclar` (perfil admin_tenant).
- **T-CLI-012**: lógica de mesclagem em `src/application/comercial/clientes/mesclar_clientes.py` (use case puro — recebe Repository protocol). Bloqueia se vencedor ou perdedor estão em tenants diferentes (impossível pela RLS mas defensivo).
- **T-CLI-013**: publicar evento `Cliente.Mesclado` via `registrar_auditoria` (interim) com payload `{vencedor_id, perdedor_id, campos_sobrescritos, motivo, usuario_id}`.
- **T-CLI-014**: adicionar `clientes.mesclar` na matriz authz_perfil_acao (migration nova).
- **T-CLI-015**: testes — 6:
  - `test_mesclar_aplica_sobrescritas_no_vencedor`
  - `test_mesclar_soft_deleta_perdedor`
  - `test_mesclar_publica_evento_cliente_mesclado`
  - `test_mesclar_cross_tenant_bloqueado` (vencedor tenant A, perdedor tenant B = 403/404)
  - `test_mesclar_exige_perfil_admin_tenant` (tecnico tenta = 403)
  - `test_mesclar_motivo_obrigatorio` (sem motivo = 400)

## Hooks ativados

- `tenant-id-validator` (queries com tenant_id)
- `authz-check` (endpoint mesclar tem `authz_action`)
- `audit-immutability-check` (audit fica imutavel)

## Non-goals deste plano

- Sem UI/wizard (só API).
- Migração de FKs em OS/certificados/financeiro — esses módulos não existem; contrato de evento publicado pra futuro.
- Restauração de soft-delete (rollback) — V2.
- Mesclagem em batch (vários pares) — V2.

## Subagentes a consultar

- `tech-lead-saas-regulado`: APROVADO COM RESSALVAS (6, todas endereçadas abaixo).
- `advogado-saas-regulado`: APROVADO COM RESSALVAS (5, todas endereçadas abaixo).

---

## Endereçamento da revisão (11 ressalvas)

### Tech-lead (6)
- **TL1 (CRÍTICA — authz)**: matriz só aceita `clientes.mesclar` para `admin_tenant`. Outros perfis ficam pra Wave A se aparecer demanda.
- **TL2 (CRÍTICA — contrato evento)**: action lowercase `cliente.mesclado`. Payload completo: `{vencedor_id, perdedor_id, tenant_id, mesclado_em, campos_sobrescritos_keys (lista nomes — R1 advogado), motivo_categoria, motivo_observacao_hash, usuario_id, perdedor_documento_hash, perdedor_nome_hash}`. Sem PII cru no audit.
- **TL3 (ALTA — Manager)**: `Cliente.all_objects` (novo manager) acessa também soft-deleted; dedup no `create()` continua via `Cliente.objects` (default — só ativos) — assim documento de cliente mesclado pode ser reaproveitado se necessário (ver R4 advogado: índice único parcial cobre).
- **TL4 (ALTA — use case puro)**: `src/domain/comercial/clientes/repository.py` define Protocol `ClienteRepository`. Use case em `src/application/comercial/clientes/mesclar_clientes.py` consome o Protocol. Adapter Django em `src/infrastructure/clientes/repositories.py`.
- **TL5 (MÉDIA — cross-tenant defensivo)**: MANTÉM (defesa em profundidade — INV-AUTHZ-003 lista de tenants pode permitir leitura cross-tenant).
- **TL6 (MÉDIA — atomicidade)**: `transaction.atomic()` envolvendo sobrescrita + soft-delete + audit, nessa ordem.

### Advogado (5)
- **R1 (BLOQUEANTE — PII no audit)**: payload grava só `campos_sobrescritos_keys` (lista de nomes, ex: `["nome", "email"]`); valores ficam no estado pós-merge do Cliente (sob crypto-shredding tenant).
- **R2 (BLOQUEANTE — motivo texto livre)**: campo `motivo_categoria` (enum 5 valores) + `motivo_observacao` (CharField max 200, **rejeita CPF/CNPJ/email/telefone via regex no boundary**). Audit grava `motivo_categoria` cleartext + `motivo_observacao_hash` (SHA-256) — observação fica só no `Cliente.mesclagens` histórico no banco do tenant (criptografado em Wave B).
  Enum cravado: `duplicacao_atendimento`, `migracao_sistema_legado`, `alteracao_pf_pj`, `reorganizacao_societaria`, `outro`.
- **R3 (clareza AC-2)**: AC-2 reescrito — "soft-deleted = correção de qualidade (LGPD art. 6 V) + retenção (art. 16 II + ISO 8.4). Direito ao esquecimento (art. 18 VI) é crypto-shredding em portal-cliente Wave B — NÃO é soft-delete."
- **R4 (BLOQUEANTE — UNIQUE INDEX parcial)**: migration adiciona `CREATE UNIQUE INDEX uq_cliente_doc_ativo ON clientes (tenant_id, tipo_pessoa, documento) WHERE deletado_em IS NULL;` E remove a UniqueConstraint Django atual. Dedup INV-024 continua valendo só pra ativos; reativação de documento (raro) permitida.
- **R5 (não-notificar OK)**: documentar explicitamente que mesclagem intra-tenant não dispara notificação ao titular (LGPD art. 9º não aplica — mesma finalidade, mesmo controlador, mesma base legal).

## Sequência revisada

- **T-CLI-009**: migration adicionando `deletado_em`, `deletado_por_usuario_id`, `deletado_motivo_categoria` ao Cliente.
- **T-CLI-009b** (R4 advogado): substituir UniqueConstraint Django por UNIQUE INDEX PG parcial em `clientes(tenant_id, tipo_pessoa, documento) WHERE deletado_em IS NULL`.
- **T-CLI-010**: Manager default `Cliente.objects` filtra `deletado_em IS NULL`; `Cliente.all_objects` separado.
- **T-CLI-011**: novo enum `MotivoMesclagem` em `src/infrastructure/clientes/mesclagem.py` + regex anti-PII pra observacao.
- **T-CLI-012**: Repository protocol em `src/domain/comercial/clientes/repository.py`.
- **T-CLI-013**: use case `src/application/comercial/clientes/mesclar_clientes.py`.
- **T-CLI-014**: adapter Django `src/infrastructure/clientes/repositories.py`.
- **T-CLI-015**: endpoint POST `/api/v1/clientes/{vencedor}/mesclar/{perdedor}/` na view. Cross-tenant defensivo (TL5). Atomicidade (TL6).
- **T-CLI-016**: audit lowercase `cliente.mesclado` com payload sem PII (TL2 + R1).
- **T-CLI-017**: migration adicionando `clientes.mesclar` na matriz authz_perfil_acao (só admin_tenant — TL1).
- **T-CLI-018**: testes — 9:
  - `test_mesclar_aplica_sobrescritas_no_vencedor`
  - `test_mesclar_soft_deleta_perdedor`
  - `test_mesclar_publica_evento_sem_pii` (R1)
  - `test_mesclar_cross_tenant_bloqueado` (TL5)
  - `test_mesclar_exige_perfil_admin_tenant`
  - `test_mesclar_motivo_categoria_obrigatorio_enum`
  - `test_mesclar_observacao_com_cpf_rejeita_400` (R2)
  - `test_unique_index_parcial_permite_reativacao_de_documento` (TL3 + R4)
  - `test_mesclar_atomico_rollback_em_falha` (TL6)
