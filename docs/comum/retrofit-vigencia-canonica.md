---
owner: roldao
revisado-em: 2026-05-22
status: stable
finalidade: lista entidades-alvo do retrofit de vigência canônica (ADR-0030). Cada linha = status atual + ondas Wave A necessárias.
relacionados:
  - ADR-0030 (vigência temporal canônica)
  - ADR-0031 (soft-delete em 3 padrões)
  - `docs/comum/modelo-de-dominio-transversal.md` §2
---

# Retrofit de vigência canônica

> **Pra quê:** ADR-0030 cravou que toda entidade temporal regulatória tem 4 campos canônicos (`vigencia_inicio`, `vigencia_fim`, `revogado_em`, `motivo_revogacao`). Marcos anteriores criaram variantes (`encerrado_em`, `data_validade_ate`, `vence_em`, etc.). Esta doc lista as 11 entidades-alvo, status atual de cada uma e ondas de Wave A pra trazer pro canônico.

---

## Tabela de entidades-alvo

| # | Entidade | Módulo | Status atual | Campos atuais (legado) | Ação Onda Wave A | Hook detecta? |
|---|---|---|---|---|---|---|
| 1 | `ResponsavelTecnicoTenant` (RT) | `colaboradores/rt` | `parcial` | `vigencia_inicio`, `vigencia_fim`, `encerrado_em` (cravado Marco 2) — falta `revogado_em`/`motivo_revogacao` formalizados | Renomear `encerrado_em` → `revogado_em` + adicionar `motivo_revogacao` (CHECK ≥10 chars). Migration retrofit Marco 3 ondas iniciais. | sim (Onda 4) |
| 2 | `RTCompetencia` | `colaboradores/rt` | `parcial` | tstzrange `vigencia` (cravado ADR-0022) — falta `revogado_em` separado | Adicionar `revogado_em` + `motivo_revogacao`; manter `vigencia` para EXCLUDE GIST mas espelhar em `vigencia_inicio`/`vigencia_fim`. Onda Marco 3. | sim (Onda 4) |
| 3 | `Certificado` | `metrologia/certificados` | `parcial` | Marco 2 tem `emitido_em`, `validade_inicio`, `validade_fim` (uso no produto). Falta cravar 4 campos canônicos ADR-0030. | Adicionar `vigencia_inicio=emitido_em`, `vigencia_fim=validade_fim`, `revogado_em` (NULL na emissão), `motivo_revogacao`. Migration Wave A `certificados`. | sim (Onda 4) |
| 4 | `EquipamentoVersao` | `metrologia/equipamentos` | `legado` | Marco 2 tem `criada_em`, `substituida_em` | Renomear → `vigencia_inicio`/`vigencia_fim`; adicionar `revogado_em`/`motivo_revogacao` (NULL — versão raramente revogada, só substituída). Migration Marco 3 ondas iniciais. | sim |
| 5 | `FeatureFlag` (tenant_features) | `acesso-seguranca/features` | `legado` | `ativada_em`, `desativada_em` (legado F-B) | Adotar canônico `vigencia_inicio`/`vigencia_fim`; `revogado_em` para revogação forçada (suspensão tenant ADR-0035). Onda Wave A `feature-flags`. | sim |
| 6 | `AuthzPerfil` | `acesso-seguranca/authz` | `legado` | F-B tem `criado_em`, `desativado_em` | Adotar 4 campos canônicos. Perfis globais → `vigencia_fim NULL`; perfis tenant-specific (ADR-0012 / INV-AUTHZ-004) → vigência por contrato. Onda Wave A. | sim |
| 7 | `AuthzAcao` | `acesso-seguranca/authz` | `legado` | Mesma situação que AuthzPerfil | Mesma ação. Onda Wave A. | sim |
| 8 | `Procedimento` (calibração) | `metrologia/calibracao` | `inexistente` | Não existe em Marco 2 — entrará Marco 4 | Nasce já com 4 campos canônicos. ADR-0024 + ADR-0025 (validação de software) apontam pra cá. | sim |
| 9 | `Padrao` (metrológico) | `metrologia/padroes` | `inexistente` | Entrará Marco 4 | Nasce já com 4 campos canônicos + `verificacao_intermediaria_proxima_em` ortogonal (INV-CAL-VI-001). | sim |
| 10 | `Tarifa` (pricing) | `billing-saas` | `inexistente` | Wave B (pricing composicional — ADR-0013) | Nasce já com 4 campos canônicos. Tarifa imutável pós-uso (INV-026). | n/a (Wave B) |
| 11 | `MetodoCalibracao` | `metrologia/calibracao` | `inexistente` | Entrará Marco 4 | Nasce já com 4 campos canônicos + `versao_motor_calculo` (INV-CAL-VERSAO-001 + ADR-0025). | sim |

---

## Padrão de migração retrofit

Para entidades `parcial` ou `legado`:

```python
# Exemplo: Certificado (entidade #3)
operations = [
    # 1. adicionar colunas novas (compatível, default sensato)
    migrations.AddField('Certificado', 'vigencia_inicio',
        models.DateTimeField(null=True, db_index=True)),
    migrations.AddField('Certificado', 'vigencia_fim',
        models.DateTimeField(null=True, db_index=True)),
    migrations.AddField('Certificado', 'revogado_em',
        models.DateTimeField(null=True)),
    migrations.AddField('Certificado', 'motivo_revogacao',
        models.TextField(null=True)),

    # 2. backfill (data migration) — mapeia legado pra canônico
    migrations.RunPython(backfill_certificado_vigencia, reverse_code=migrations.RunPython.noop),

    # 3. NOT NULL + CHECK constraints
    migrations.AlterField('Certificado', 'vigencia_inicio',
        models.DateTimeField(null=False)),
    migrations.RunSQL("""
        ALTER TABLE certificado
        ADD CONSTRAINT chk_vigencia_canonica
        CHECK (
            vigencia_fim IS NULL OR vigencia_inicio <= vigencia_fim
        ),
        ADD CONSTRAINT chk_revogacao_canonica
        CHECK (
            revogado_em IS NULL OR (
                motivo_revogacao IS NOT NULL
                AND length(motivo_revogacao) >= 10
                AND revogado_em <= COALESCE(vigencia_fim, '9999-12-31'::timestamptz)
            )
        )
    """),
]
```

## Critério de saída

Retrofit completo para entidade quando:
1. Migration aplicada (4 campos + CHECK constraints).
2. Hook `vigencia-canonica-check.sh` passa (Onda 4).
3. Suite anti-regressão exercita: vigência válida; vigência invertida (rejeitada); revogação sem motivo (rejeitada); revogação após `vigencia_fim` (rejeitada); datetime naive em VO (rejeitado).

## Critérios de não-retrofit (entidade sai da lista)

- Entidade puramente operacional sem efeito regulatório (ex: `SessaoUsuario`) — não exige vigência canônica.
- Entidade transitória (job, cache) — não exige.

Critério **não vale** para entidade temporal regulatória: se RT, RTCompetencia, Certificado, EquipamentoVersao, FeatureFlag, AuthzPerfil/Acao, Procedimento, Padrao, Tarifa, MetodoCalibracao — **obrigatório retrofit** ou ADR formal para isentar.
