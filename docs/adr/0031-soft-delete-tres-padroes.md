---
adr: 0031
titulo: Soft-delete em 3 padrões — estado-máquina / revogado_em / deletado_em
status: aceito
data: 2026-05-23
proposto-por: agente (auditoria projeto-inteiro 10 lentes — lente 10 modelo dados C-DT-03)
revisado-por: tech-lead-saas-regulado
aceito-em: 2026-05-23 (Onda 2 saneamento pré-Marco 3 OS)
bloqueia-fase: Wave A Marco 3 (`os` — Atividade cancelada) + retrofit clientes/certificados/RT
depende-de: ADR-0030 (vigência canônica)
---

# ADR-0031 — Soft-delete em 3 padrões

## Contexto

Auditoria projeto-inteiro 2026-05-23 lente 10 (modelo dados) detectou **5 variantes** de soft-delete em código já implementado:

- `clientes/models.py` + `ClienteAtivosManager` — `deletado_em` (DateTimeField nullable).
- `equipamentos/` — estado-máquina via `EquipamentoSucatamento` + `EquipamentoDevolucao`.
- `certificados/models.py:76-91` — `revogado_em` (DateTimeField nullable).
- `responsavel_tecnico/models.py:115-125` — `encerrado_em` (será renomeado em ADR-0030 → `revogado_em`).
- Marco 3 OS vai criar `cancelada_em`/`atividade.estado='cancelada'` — 5ª variante.

Sem ADR ditando padrão único, cada Marco reinventa. Hook nenhum bloqueia. Query "todas as entidades não-canceladas do tenant" tem N implementações distintas.

## Decisão

**3 padrões aceitos, escolhidos por categoria de entidade:**

### Padrão A — Estado-máquina explícita

**Usar quando:** a entidade tem máquina de estados não-trivial (transições com pré-condição, eventos, audit).

**Forma:** `status: CharField(choices=...)` + tabela auxiliar `<Entidade>EventoStatus` (audit imutável de transições).

**Exemplos:** `Equipamento` (status `ativo|sucatado|devolvido|transferido`), futuros `OS` (status `aberta|em_execucao|concluida|cancelada|faturada|paga`), `Atividade` (idem), `NaoConformidade` (ciclo CAPA).

**Soft-delete = transição** para estado terminal (`sucatado`, `cancelada`, `arquivada`). Não há flag separada.

### Padrão B — `revogado_em` (entidades imutáveis pós-emissão)

**Usar quando:** a entidade vira imutável após emissão regulatória (INV-025, INV-CER-WORM-001) e não pode ser "deletada" — só revogada com motivo.

**Forma:** campos canônicos ADR-0030 (`vigencia_inicio`, `vigencia_fim`, `revogado_em`, `motivo_revogacao`).

**Exemplos:** `Certificado`, `ResponsavelTecnicoTenant`, `RTCompetencia`, futuros `LeituraCorrecao` (rasura digital cl. 7.5), `EventoDeCalibracao` (WORM).

**Soft-delete = preencher `revogado_em` + `motivo_revogacao`** (CHECK >=10 chars). Linha física **nunca** deletada (WORM/trilha auditável).

### Padrão C — `deletado_em` (entidades de configuração mutáveis)

**Usar quando:** a entidade é configuração/cadastro mutável sem máquina de estado relevante e SEM imutabilidade regulatória.

**Forma:** `deletado_em: DateTimeField(null=True, default=None)` + manager `objects = SomenteAtivosManager()` (filtra `deletado_em IS NULL`) + `objects_all = models.Manager()` para acesso WORM.

**Exemplos:** `Cliente` (cadastro pode ser desativado), futuros `Procedimento`, `Padrao` (cadastro do lab), `Usuario` (com cuidado — ver Padrão A se houver máquina de sessão), `Telefone`/`Endereco` secundários.

**Soft-delete = preencher `deletado_em`**. Hard-delete só pela rotina LGPD art. 18 VI (anonimização ADR-0021 Zona A) ou rotina de purga após retenção expirada.

## Tabela entidade → padrão

| Entidade | Padrão | Justificativa |
|---|---|---|
| `Cliente` | C (`deletado_em`) | Cadastro mutável; anonimização LGPD Zona A separada. |
| `Equipamento` | A (estado-máquina) | Ciclo `ativo→sucatado/devolvido/transferido` com eventos. |
| `EquipamentoVersao` | B (`revogado_em`) | Histórico imutável de modificações. |
| `Certificado` | B (`revogado_em`) | Imutável pós-emissão (INV-CER-WORM-001). |
| `ResponsavelTecnicoTenant` | B (`revogado_em`) | RT vigente é estado regulatório auditável. |
| `RTCompetencia` | B (`revogado_em`) | Idem. |
| `Usuario` | C (`deletado_em`) + Padrão A se houver sessão | Conta inativa preserva audit. |
| `OS` (Marco 3) | A (estado-máquina) | Ciclo de vida complexo. |
| `Atividade` (Marco 3) | A (estado-máquina) | Ciclo de vida + transições audit. |
| `LeituraCorrecao` (Marco 4) | B (`revogado_em`) | Rasura digital ISO 17025 cl. 7.5 imutável. |
| `NaoConformidade` (Marco 4) | A (estado-máquina) | Ciclo CAPA. |
| `Procedimento` (Marco 4) | C (`deletado_em`) + vigência ADR-0030 | Cadastro do lab; vigência separada. |
| `Padrao` (Marco 4) | C (`deletado_em`) + vigência ADR-0030 | Idem. |
| `Plano`/`Tarifa` (billing-saas) | C (`deletado_em`) + vigência ADR-0030 | Snapshot por ciclo já preserva histórico. |
| `Tenant` | A (estado-máquina) | Ciclo `provisionando→ativo→suspenso→encerrado`. |

## Regras invariantes

- **INV-SOFT-001:** Toda entidade do projeto se encaixa em A, B ou C — não há 4ª variante. Nova entidade deve declarar o padrão no docstring (`# Padrão soft-delete: A|B|C — <justificativa>`).
- **INV-SOFT-002:** Padrão B + Padrão A são WORM físicos — DELETE direto bloqueado por trigger PG (`audit-immutability-check.sh` estendido em Onda 3 cobrirá os 2 padrões).
- **INV-SOFT-003:** Padrão C + manager default só lista `deletado_em IS NULL`; acesso a deletados exige `objects_all` (intencional) — viola TST-SOFT-001 se views/queries usarem `objects_all` sem comentário justificativa.

## Hook validador

`soft-delete-padrao-check.sh` (Onda 4) — bloqueia migration que cria coluna com nome `excluido_em`, `removido_em`, `arquivado_em`, `cancelado_em`, `inativo_em`, `is_deleted`, `is_active` (anti-padrão). Allow via `# soft-delete-padrao: A|B|C -- <razão>`.

## Alternativas

- **Single approach (só Padrão C — `deletado_em` universal)** — rejeitado: força entidades WORM (cert, RT) a violar imutabilidade regulatória.
- **Single approach (só Padrão A — estado-máquina universal)** — rejeitado: overhead para entidades de configuração simples (`Telefone`, `Endereco`).
- **Soft-delete via tabela `deletados` separada com FK** — rejeitado: query N+1; perde índice composto.

## Consequências

**Boas:** convenção única por categoria; hook bloqueia 4ª variante; Marco 3 OS arranca com Padrão A explícito; auditoria mecânica.

**Ruins:** retrofit migrations em `clientes` (já está em Padrão C — OK, sem mudança) e `responsavel_tecnico` (renomear via ADR-0030).

## Status

Aceita 2026-05-23 (Onda 2). Hook `soft-delete-padrao-check.sh` em Onda 4. INV-SOFT-001..003 em REGRAS-INEGOCIAVEIS.md (Onda 4).
