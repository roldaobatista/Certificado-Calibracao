---
owner: roldao + agente
revisado-em: 2026-05-20
status: stable
---

> **Histórico do ritual (P2 endurecido):** design DRAFT → review paralelo
> `advogado-saas-regulado` (primário), `tech-lead-saas-regulado`,
> `consultor-rbc-iso17025`. **16 bloqueantes absorvidos** (7 advogado +
> 6 tech-lead + 3 RBC). Pareceres em `review-advogado.md`,
> `review-tech-lead.md`, `review-rbc.md`.

# T-CLI-114..120 — design final (US-CLI-006 LGPD)

## Estratégia de implementação

Pelo volume (7 T-CLI + 16 BLOQ), implementação em **4 commits atômicos**:

| Commit | T-CLI | Tema | Risco |
|--------|-------|------|-------|
| **3a** | T-CLI-117 + T-CLI-118 | Validadores anti-PII sensível + idade <18 | baixo (serializer + CHECK) |
| **3b** | T-CLI-120 | OperacaoTratamentoCliente + trigger PG | médio (signal + trigger) |
| **3c** | T-CLI-115 + T-CLI-119 | Revogação consentimento + evento incidente | médio (campo + helper) |
| **3d** | T-CLI-114 + T-CLI-116 + ADR-0021 | 8 endpoints direitos titular + matriz eliminação×anonimização | alto (orquestração) |

## Bloqueantes absorvidos (resumo)

### Advogado (7)
- **BLOQ-A1**: `payload_resposta` **schema temático por tipo** (não ack).
- **BLOQ-A2**: mapa `finalidade × bases_legais_aceitas` em `politicas_lgpd.py` (`INV-CLI-002`).
- **BLOQ-A3**: termset PII sensível com **word-boundary `\b` + termos ≥ 5 chars**. Lista enxuta (sem `pt`/`pl`/`vot`/`trans`/`gen`).
- **BLOQ-A4**: `RequisicaoTitularLGPD.motivo_recusa` + `base_legal_recusa` (art. 18 §4º).
- **BLOQ-A5**: incidente recebe `cliente_ids: list[UUID]` ou `escopo: Literal[...]` — não `count()`.
- **BLOQ-A6**: validador idade em **CREATE e UPDATE**.
- **BLOQ-A7**: auditoria PII sensível legada = **NÃO-GOAL Marco 1** (GATE-CLI-LGPD-1 pra Wave A).

### Tech-lead (6)
- **BLOQ-TL-T2**: 2 campos — `payload_resposta_titular` (KMS Wave A — Marco 1 deixa em JSONB cifrado simples + TTL 30d) + `payload_auditoria` (sanitizado).
- **BLOQ-TL-T3**: UNIQUE `(causation_id)` (não date-bucket). 429 anti-abuse em dia/IP via rate-limit Wave A.
- **BLOQ-TL-T4**: trigger PG `AFTER INSERT/UPDATE ON cliente` grava `OperacaoTratamentoCliente` (não signal Django).
- **BLOQ-TL-T5**: outbox sempre publica revogação (consumer noop em Marco 1).
- **BLOQ-TL-T6**: `_tem_nf_emitida` / `_tem_certificado_iso` retornam `False` + comentário `GATE-CLI-M2` (registrado em `faseamento-foundation-waves.md`).
- **BLOQ-TL-TL3**: `_tem_nf_emitida` via porta (`NFGateway`) pra preservar anti-corrosion. Marco 1: stub returns False.

### RBC (3)
- **BLOQ-R1**: criar **ADR-0021 Anonimização vs retenção regulatória** — 3 zonas A/B/C de dado.
- **BLOQ-R2**: texto bloqueio `signatário humano` cita base art. 7º II Lei 9.933/99 INMETRO (dogfooding pré-RBC).
- **BLOQ-R3**: consultor humano credenciado assina antes da 1ª CGCRE real (Wave A pré-acreditação).

## Decisões finais cravadas

### A1/BLOQ-A3 — termset PII sensível (T-CLI-117)

```python
import re

# Lista enxuta — só termos completos ≥ 5 chars, word boundary
# Origem: LGPD art. 5º II (taxativa) + revisão do advogado humano
# Wave A (consulta pontual antes do 1º tenant externo).
_TERMOS_PII_SENSIVEL = (
    # Saúde
    "diabet", "hipertens", "cancer", "tumor", "depres", "psiqui",
    "soropositivo", "alcool", "drogad", "vicio",
    # Biometria
    "biometr", "facial", "retina", "datilo",
    # Genética
    "geneti", "hereditari", "cromoss",
    # Política (palavras inteiras — não siglas)
    "esquerda", "direita", "comunist", "fascist",
    # Religião
    "evangelic", "catolic", "islam", "judaic", "budist", "umbanda",
    "candomble", "espirita",
    # Orientação sexual
    "lgbtq", "homosex", "bissex", "transex",
    # Origem racial/étnica (BLOQ-A1 advogado)
    "racial", "indigena", "negroide", "caucasiano",
    # Saúde reprodutiva (BLOQ-A1 advogado)
    "menstr", "gravid", "gestant", "aborto",
    # Sindicato (LGPD art. 5º II)
    "sindical", "sindicat",
)

_RE_PII_SENSIVEL = re.compile(
    r"\b(" + "|".join(_TERMOS_PII_SENSIVEL) + r")\w*\b",
    re.IGNORECASE,
)

def conter_pii_sensivel(texto: str) -> bool:
    """Detecção word-boundary case-insensitive (BLOQ-A1 + BLOQ-TL-2).
    Best-effort — NÃO substitui análise humana (controlador continua
    responsável LGPD art. 11)."""
    if not texto:
        return False
    return _RE_PII_SENSIVEL.search(texto) is not None
```

### A2/BLOQ-A2 — mapa finalidade×base legal

Adicionar a `audit/politicas_lgpd.py`:

```python
MAPA_FINALIDADE_BASE_LEGAL_ACEITA: Final[dict[str, frozenset[str]]] = {
    # finalidade -> {bases legais que continuam válidas pós-revogação consentimento}
    "cadastro_basico": frozenset({"EXECUCAO_CONTRATO"}),
    "emissao_nf": frozenset({"OBRIG_LEGAL", "EXECUCAO_CONTRATO"}),
    "emissao_certificado_iso": frozenset({"OBRIG_LEGAL"}),
    "comunicacao_marketing": frozenset({"CONSENTIMENTO"}),
    "audit_trail": frozenset({"OBRIG_LEGAL", "LEGITIMO_INTERESSE"}),
    # ...
}

def base_legal_aplicavel_pos_revogacao(
    finalidade: str, bases_disponiveis: set[str]
) -> bool:
    """True se há ao menos uma base legal aceita para a finalidade
    quando o titular revogou consentimento."""
    aceitas = MAPA_FINALIDADE_BASE_LEGAL_ACEITA.get(finalidade, frozenset())
    return bool(aceitas & bases_disponiveis - {"CONSENTIMENTO"})
```

### Schema temático de resposta (BLOQ-A1)

Por tipo, `payload_resposta_titular` segue schema fixo:

- `confirmacao`: `{confirmado: bool, bases_legais: list, finalidades: list}`
- `acesso`: dados completos + finalidades + bases + compartilhamentos + retenções
- `correcao`: `{campos_alterados: dict, timestamp}`
- `anonimizacao`: `{acao_aplicada: ANONIMIZACAO, campos_afetados: list}`
- `portabilidade`: dump JSON estruturado
- `eliminacao`: `{acao_aplicada: ELIMINACAO|ANONIMIZACAO, base_legal_eventual_recusa: str|null}`
- `informacao_compartilhamento`: lista de operadores/controladores conhecidos (Marco 1: vazia)
- `revogacao_consentimento`: `{revogado_em, bases_legais_persistentes}`

## Não-goals (cravados)

- Push real ao titular (e-mail/WhatsApp) — Wave A `comunicacao-omnichannel`.
- Processamento automático COMPLETO — DPO resolve manualmente os tipos complexos em Marco 1.
- Consumer real de incidente — módulo governança Wave A.
- Anonimização parcial de NF/cert reais — módulos Wave A.
- Cifragem KMS de `payload_resposta_titular` — Marco 1 mantém JSONB com TTL 30d.
- Auditoria PII sensível legada — GATE-CLI-LGPD-1 Wave A.
- Signatário ISO cl. 6.2 — Wave A módulo certificados.

## Rastreabilidade

- US-CLI-006 / AC-CLI-006-1..7 (`spec.md` L391-441).
- LGPD arts. 8º §5º, 11, 14, 16, 18, 37; Res. CD/ANPD 2/2022 art. 11;
  Res. ANPD 15/2024.
- `INV-CLI-002` (política LGPD canônica).
- ADR-0021 a criar (BLOQ-R1).
