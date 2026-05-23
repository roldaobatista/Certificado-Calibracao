---
adr: 0030
titulo: Vigência temporal canônica em entidades regulatórias (VO JanelaVigencia)
status: aceito
data: 2026-05-23
proposto-por: agente (auditoria projeto-inteiro 10 lentes — lente 10 modelo dados C-DT-01)
revisado-por: tech-lead-saas-regulado + consultor-rbc-iso17025
aceito-em: 2026-05-23 (Onda 2 saneamento pré-Marco 3 OS)
bloqueia-fase: Wave A Marco 3 (`os` — Atividade temporal) + Marco 4 (`calibracao` — Procedimento/Padrão vigentes) + retrofit RT/RTCompetencia/Certificado
depende-de: ADR-0007 (camada domínio + gerador spec→código)
---

# ADR-0030 — Vigência temporal canônica

## Contexto

Auditoria projeto-inteiro 2026-05-23 lente 10 (modelo dados transversal) detectou **cacofonia de 3 nomes para 1 conceito** de vigência temporal já implementado:

- `responsavel_tecnico/models.py:115-125` — `ResponsavelTecnicoTenant`: `data_inicio_vigencia` (DateField) + `data_fim_vigencia` (DateField) + `encerrado_em` (DateTimeField).
- `responsavel_tecnico/models.py:222-228` — `RTCompetencia`: `declarado_em` (DateTimeField) + `vigente_ate` (DateField).
- `certificados/models.py:76-91` — `Certificado`: `emitido_em` (DateTimeField) + `revogado_em` (DateTimeField nullable).

AGENTS.md §3 prescreve padrão `(vigencia_inicio, vigencia_fim, revogado_em, motivo_revogacao)` mas **nenhuma entidade usa**. Marco 3 OS vai criar 4ª variante (provavelmente `iniciada_em/concluida_em/cancelada_em`); Marco 4 calibração 5ª; certificados Wave A 6ª. Cada query "qual estava vigente em T?" tem que reaprender o esquema de cada tabela.

Risco: bug de borda em "vigência expirou às 23:59:59 mas timezone do servidor estava UTC" gera certificados nulos retroativos; risco regulatório CGCRE/RBC se RT mostra vigente quando já não está.

## Decisão

**Adotar VO `JanelaVigencia` em `src/domain/shared/value_objects.py` + 4 campos canônicos em TODA entidade temporal regulatória:**

| Campo | Tipo | Nullable | Semântica |
|---|---|---|---|
| `vigencia_inicio` | `DateTimeField` (timestamptz) | NOT NULL | Quando a entidade passou a valer. |
| `vigencia_fim` | `DateTimeField` (timestamptz) | NULL = aberta | Quando a entidade deixará de valer (planejado). |
| `revogado_em` | `DateTimeField` (timestamptz) | NULL = não revogado | Quando foi revogada **antes** de `vigencia_fim`. |
| `motivo_revogacao` | `TextField` | NULL salvo se `revogado_em` not null | Texto livre auditável. |

### Regras invariantes (nova INV-VIG-001..004)

- **INV-VIG-001:** `vigencia_inicio <= vigencia_fim` quando ambas presentes — CHECK constraint na migration.
- **INV-VIG-002:** `revogado_em IS NOT NULL` exige `motivo_revogacao` com `length >= 10` — CHECK constraint.
- **INV-VIG-003:** `revogado_em <= COALESCE(vigencia_fim, '9999-12-31'::timestamptz)` — não revogar depois do fim natural.
- **INV-VIG-004:** Toda entidade que use o VO declara `tz_referencia` na docstring do modelo: "UTC" (default), "America/Sao_Paulo", ou "lab" (timezone do laboratório do tenant — cl. 7.7 ISO 17025).

### Consultas canônicas

```python
# Em src/domain/shared/value_objects.py
@dataclass(frozen=True)
class JanelaVigencia:
    inicio: datetime
    fim: datetime | None
    revogado_em: datetime | None = None
    motivo_revogacao: str | None = None

    def __post_init__(self) -> None:
        if self.fim is not None and self.inicio > self.fim:
            raise ValueError(f"vigencia_inicio {self.inicio} > vigencia_fim {self.fim}")
        if self.revogado_em is not None:
            if not self.motivo_revogacao or len(self.motivo_revogacao) < 10:
                raise ValueError("revogado_em exige motivo_revogacao >=10 chars (INV-VIG-002)")
            limite = self.fim or datetime.max.replace(tzinfo=UTC)
            if self.revogado_em > limite:
                raise ValueError("revogado_em > vigencia_fim (INV-VIG-003)")

    def vigente_em(self, momento: datetime) -> bool:
        """True se a janela cobre o instante (independente de timezone — comparação UTC-aware)."""
        if self.revogado_em is not None and momento >= self.revogado_em:
            return False
        if momento < self.inicio:
            return False
        if self.fim is not None and momento >= self.fim:
            return False
        return True

    def vigente_agora(self) -> bool:
        return self.vigente_em(datetime.now(UTC))
```

### Retrofit obrigatório

Migrations criadas em Onda 2:
- `responsavel_tecnico/migrations/00XX_canonizar_vigencia.py` — rename `data_inicio_vigencia → vigencia_inicio`, `data_fim_vigencia → vigencia_fim`, `encerrado_em → revogado_em`; converter DateField→DateTimeField (UTC midnight); adicionar `motivo_revogacao` NOT NULL DEFAULT '' (depois CHECK).
- `responsavel_tecnico/migrations/00XX_canonizar_rtcompetencia.py` — rename `declarado_em → vigencia_inicio`, `vigente_ate → vigencia_fim`; adicionar `revogado_em` + `motivo_revogacao`.
- `certificados/migrations/00XX_canonizar_vigencia.py` — rename `emitido_em → vigencia_inicio`; manter `revogado_em`; adicionar `vigencia_fim` (NULL = válido até revogação ou recalibração).

### Aliases compatíveis (período de migração)

Cada modelo retém propriedade `@property` deprecada (1 release):
```python
@property
def emitido_em(self) -> datetime:
    """DEPRECATED ADR-0030. Use vigencia_inicio."""
    return self.vigencia_inicio
```

Removidos após Marco 4 fechar.

## Alternativas consideradas

- **Manter cada modelo com seu próprio esquema** — rejeitado: drift garantido a cada Marco; bug de borda timezone difícil de detectar; viola "Negócio vence conveniência" (cada agente reinventa).
- **VO sem ALTER nas tabelas existentes** — rejeitado: drift de leitura permanece; testes UNHAPPY "vigente_em" ficam com 3 caminhos por entidade.
- **Tabela `vigencias` separada com FK** — rejeitado: query N+1 garantida; perde índice composto em consultas comuns.

## Consequências

**Boas:**
- Marco 3 OS, Marco 4 calibração, certificados Wave A nascem com VO único.
- Query padrão "o que estava vigente em T?" é mecânica em qualquer tabela.
- CHECK constraints no banco garantem invariantes (sem só confiar em código Python).
- Auditoria CGCRE/RBC consegue rastrear vigência de RT/procedimento/padrão por timestamp.

**Ruins:**
- 3 migrations de retrofit Onda 2 + ajuste de testes existentes.
- 1 release com propriedades deprecated (`emitido_em`, `declarado_em`, etc.) — limpar em Marco 4 P1.

## Non-goals

- Versionamento temporal de entidade inteira (event sourcing) — fora de escopo; `EquipamentoVersao` continua sendo a abordagem para histórico de modificação.
- Vigência em entidades não-regulatórias (configurações UI, preferências usuário) — VO opcional, não obrigatório.

## Hook validador

`vigencia-canonica-check.sh` (Onda 4) — bloqueia migration que cria coluna `data_inicio_vigencia | data_fim_vigencia | iniciada_em | concluida_em | declarado_em | vigente_ate | encerrado_em` em entidade regulatória (allow via comentário `# vigencia-canonica: skip -- <razão ≥10 chars>`).

## Status / próximo passo

Aceita 2026-05-23 (Onda 2 saneamento). Implementação VO + retrofit migrations entra em Onda 2 imediatamente; teste regressão `test_inv_vig_001..004.py` em Onda 4.
